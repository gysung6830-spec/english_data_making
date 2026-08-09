// ai.js — 추출된 영어 문장을 Claude 로 "교재 데이터(categories)" 로 구조화한다.
//
// 입력: PDF 에서 뽑은 영어 문장 배열
// 출력: data.js 와 같은 스키마의 categories 배열
//        (문법 챕터 분류 + 끊어읽기·어휘·캐치·뼈대 생성)
//
// 규칙(README '콘텐츠 작성 가이드라인' 반영):
//   · chunks(끊어읽기)  = 앞에서부터 순서대로 직독직해([영어조각, 한글조각])
//   · catch            = 이 문장의 핵심 뜻 한 줄(20~45자, 반말, 문법 용어 금지)
//   · vocab            = 지문에 나온 단어·뜻
//   · steps(worked만)  = 뼈대(진짜 주어+동사)·괄호(수식어) 분석
//
// 환경변수:
//   ANTHROPIC_API_KEY  — 실제 Claude 호출 (없으면 MOCK 로 폴백)
//   ANTHROPIC_MODEL    — 기본 'claude-opus-5'
//   ANTHROPIC_MOCK=1   — 키가 있어도 강제로 MOCK (로컬 파이프라인 테스트용)

const { makeTip } = require('./tip'); // (참고용, 렌더 단계에서 사용)

const DEFAULT_MODEL = process.env.ANTHROPIC_MODEL || 'claude-opus-5';

// 우리가 다루는 문법 챕터(순서 = 목차 번호 ①~⑦). AI 가 문장을 이 중 하나로 분류.
const CHAPTERS = [
  { key: '전치사구', title: "① 전치사구 — '전치사 + 명사' 덩어리로 읽기" },
  { key: '수동태', title: '② 수동태 — be + p.p. 로 "당하다"' },
  { key: 'to부정사', title: '③ to부정사 — to + 동사원형의 세 가지 얼굴' },
  { key: '동명사', title: '④ 동명사 — 동사에 -ing 를 붙여 명사로' },
  { key: '관계사', title: '⑤ 관계사 — 명사를 문장으로 꾸미기' },
  { key: '분사', title: '⑥ 분사 — -ing/-ed 로 명사 꾸미기' },
  { key: '분사구문', title: '⑦ 분사구문 — 접속사+주어를 지운 -ing 덩어리' },
];

// ── AI 출력 JSON 스키마 (객체 형태 → normalize 에서 튜플로 변환) ──
const OUTPUT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['categories'],
  properties: {
    categories: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['key', 'title', 'intro', 'signal', 'method', 'worked', 'practice'],
        properties: {
          key: { type: 'string' },
          title: { type: 'string' },
          intro: { type: 'array', items: { type: 'string' }, minItems: 1 },
          signal: { type: 'array', items: { type: 'string' }, minItems: 1 },
          method: {
            type: 'array', minItems: 1,
            items: {
              type: 'object', additionalProperties: false,
              required: ['label', 'text'],
              properties: { label: { type: 'string' }, text: { type: 'string' } },
            },
          },
          traps: { type: 'array', items: { type: 'string' } },
          worked: { type: 'array', minItems: 2, items: sentenceSchema() },
          practice: { type: 'array', items: sentenceSchema() },
        },
      },
    },
  },
};

function sentenceSchema() {
  const props = {
    src: { type: 'string' },
    en: { type: 'string' },
    chunks: {
      type: 'array', minItems: 1,
      items: {
        type: 'object', additionalProperties: false,
        required: ['en', 'kor'],
        properties: { en: { type: 'string' }, kor: { type: 'string' } },
      },
    },
    vocab: {
      type: 'array', minItems: 1,
      items: {
        type: 'object', additionalProperties: false,
        required: ['word', 'mean'],
        properties: { word: { type: 'string' }, mean: { type: 'string' } },
      },
    },
    catch: { type: 'string' },
    // trap: 이 문장에서 자주 틀리는 해석 포인트 경고(문장별 맞춤)
    trap: { type: 'string' },
  };
  const required = ['src', 'en', 'chunks', 'vocab', 'catch', 'trap'];
  return { type: 'object', additionalProperties: false, required, properties: props };
}

// ── AI 출력(객체) → 내부 스키마(튜플) 변환 ──
function normalize(aiData) {
  const cats = (aiData.categories || []).filter((c) => c && c.key);
  return cats.map((c) => ({
    key: c.key,
    title: c.title,
    intro: c.intro || [],
    signal: c.signal || [],
    method: (c.method || []).map((m) => [m.label, m.text]),
    traps: Array.isArray(c.traps) ? c.traps : undefined,
    worked: (c.worked || []).map(normSentence),
    practice: (c.practice || []).map(normSentence),
  }));
}
function normSentence(s) {
  return {
    src: String(s.src || ''),
    en: s.en || '',
    chunks: (s.chunks || []).map((c) => [c.en, c.kor]),
    catch: s.catch || '',
    vocab: (s.vocab || []).map((v) => [v.word, v.mean]),
    trap: s.trap || '',
  };
}

const SYSTEM_PROMPT = `너는 한국 수능/평가원 영어 지문을 '구문해석 교재' 데이터로 가공하는 편집자야.
학생에게 반말로 친근하게 설명하는 과외 선생님 톤을 유지해.

주어진 영어 문장들을 아래 문법 챕터로 분류하고, 각 문장을 교재용으로 가공해:
${CHAPTERS.map((c) => `- ${c.key}`).join('\n')}

각 문장 가공 규칙:
- chunks(끊어읽기): 문장을 앞에서부터 순서대로 의미 덩어리로 끊고, 각 덩어리를 직독직해해.
  (en=영어 덩어리, kor=그 덩어리의 우리말). 이어 붙이면 자연스러운 전체 번역이 되게.
- vocab: 그 문장에서 학생이 모를 만한 단어 3~6개와 뜻.
- catch: 이 문장에서 딱 이것만 이해하면 통과인 '핵심 뜻 한 줄'. 20~45자, 반말("~는 거야!"),
  문법 용어 쓰지 말고 내용 요약만. 세부(연도·기관명 등)는 압축.
- trap: 이 문장에서 학생이 '자주 틀리는 해석 포인트' 경고 한 줄(반말, "~하지 마 — ~로 읽어야 해").
  반드시 그 문장에 실제로 있는 요소만 지적해(문장에 없는 단어를 예로 들지 마).

챕터 규칙:
- 각 챕터는 worked(같이 풀어보기) 2문장 이상 + practice(혼자 풀어보기) 나머지.
- worked·practice 모든 문장에 catch 와 trap 을 넣어.
- traps: 그 챕터 문법에서 공통으로 조심할 함정 2~3개(문장 특정 단어에 얽매이지 않는 일반 주의)도 채워.
- 문장이 하나도 없는 챕터는 categories 에서 빼.
- title 은 원문자 번호(①②③…)를 문법 순서대로 유지해.
- src 는 원문 문항 번호를 알 수 있으면 그 번호, 모르면 일련번호 문자열.
- intro(무엇인가요), signal(신호), method(해석법)도 학생 눈높이 반말로 새로 써.`;

function userPrompt(sentences) {
  const list = sentences.map((s, i) => `${i + 1}. ${s}`).join('\n');
  return `다음은 업로드된 PDF 에서 추출한 영어 문장들이야. 이걸 문법 챕터별 교재 데이터로 만들어줘.\n\n${list}`;
}

// ── 실제 Claude 호출 ──
async function callClaude(sentences) {
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic(); // ANTHROPIC_API_KEY 를 env 에서 읽음

  const stream = client.messages.stream({
    model: DEFAULT_MODEL,
    max_tokens: 32000,
    thinking: { type: 'adaptive' },
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: userPrompt(sentences) }],
    output_config: { format: { type: 'json_schema', schema: OUTPUT_SCHEMA } },
  });
  const final = await stream.finalMessage();
  const text = final.content
    .filter((b) => b.type === 'text')
    .map((b) => b.text)
    .join('');
  return JSON.parse(text);
}

// ── MOCK: 키 없이 파이프라인 테스트. 추출 문장을 규칙 기반으로 대충 분류/가공. ──
function mockStructure(sentences) {
  const pick = (s) => {
    const t = s.toLowerCase();
    if (/\b(was|were|is|are|been|being)\b.*\b(ed|en)\b/.test(t) || /\bby\b/.test(t)) return '수동태';
    if (/\bto\s+[a-z]+/.test(t)) return 'to부정사';
    if (/[a-z]+ing\b/.test(t) && /\b(by|after|before|while|when)\b/.test(t)) return '분사구문';
    if (/[a-z]+ing\b/.test(t)) return '동명사';
    if (/\b(who|which|that|whose|where|whom)\b/.test(t)) return '관계사';
    if (/[a-z]+ing\b|[a-z]+ed\b/.test(t)) return '분사';
    return '전치사구';
  };
  const buckets = {};
  sentences.forEach((en, i) => {
    const key = pick(en);
    (buckets[key] = buckets[key] || []).push({ en, idx: i + 1 });
  });

  const mkSentence = (o, withSteps) => {
    const words = o.en.split(/\s+/);
    const mid = Math.max(2, Math.floor(words.length / 2));
    const chunks = [
      [words.slice(0, mid).join(' '), '(앞 덩어리 해석)'],
      [words.slice(mid).join(' '), '(뒤 덩어리 해석)'],
    ];
    return {
      src: String(o.idx),
      en: o.en,
      chunks,
      catch: '이 문장의 핵심을 한 줄로 잡아보는 거야!',
      vocab: [[words[0] || 'word', '(뜻)'], [words[mid] || 'word', '(뜻)']],
      trap: '진짜 주어·동사를 먼저 찾고, 나머지는 꾸밈말로 걸러 읽어.',
    };
  };

  const categories = [];
  CHAPTERS.forEach((ch) => {
    const items = buckets[ch.key];
    if (!items || items.length < 2) return; // worked 2개 확보 안 되면 스킵
    categories.push({
      key: ch.key,
      title: ch.title,
      intro: [`'${ch.key}'가 뭔지 예문으로 감을 잡아보자.`, '겁먹지 말고 순서대로 따라와.'],
      signal: [`${ch.key}의 신호를 문장에서 찾아봐.`],
      method: [['1단계', '덩어리로 끊는다.'], ['2단계', '앞에서부터 해석한다.'], ['한 단계 위', '진짜 동사와 꾸밈말을 구분한다.']],
      traps: [`'${ch.key}' 신호를 놓치지 마.`, '진짜 주어·동사를 먼저 찾고 나머지는 꾸밈말로 걸러.'],
      worked: items.slice(0, 2).map((o) => mkSentence(o)),
      practice: items.slice(2).map((o) => mkSentence(o)),
    });
  });
  return { categories };
}

// title 의 앞머리 원문자 번호(①~⑳)를 최종 순서에 맞게 다시 매긴다.
// (챕터 일부만 생성되면 원래 번호와 위치가 어긋나므로 검증 경고가 뜨는 걸 방지)
const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫'];
function renumberTitles(categories) {
  return categories.map((c, i) => {
    const num = CIRCLED[i] || `${i + 1}`;
    const stripped = String(c.title || c.key).replace(/^\s*[①-⑳]\s*/, '');
    return { ...c, title: `${num} ${stripped}` };
  });
}

// ── 진입점 ──
// sentences: string[] → Promise<{ categories, mode }>
async function structureSentences(sentences, opts = {}) {
  const useMock = opts.mock || process.env.ANTHROPIC_MOCK === '1' || !process.env.ANTHROPIC_API_KEY;
  if (useMock) {
    // mockStructure 는 이미 내부(튜플) 스키마로 만들므로 normalize 를 거치지 않는다.
    return { categories: renumberTitles(mockStructure(sentences).categories), mode: 'mock' };
  }
  const aiData = await callClaude(sentences);
  return { categories: renumberTitles(normalize(aiData)), mode: 'ai' };
}

// ─────────────────────────────────────────────────────────────
// 지문(passage) 모드 — 목차를 구문(문법)이 아니라 '지문 단위'로.
//   문장은 원문 순서 그대로, 문장별 구문해석 도움은 유지(문법은 point 태그),
//   지문 맨 위 topic('이 지문 뭐야') + 지문 요지 catch('이 정도는 캐치').
// ─────────────────────────────────────────────────────────────

function passageSentenceSchema() {
  return {
    type: 'object', additionalProperties: false,
    required: ['src', 'en', 'point', 'chunks', 'vocab', 'catch', 'trap'],
    properties: {
      src: { type: 'string' },
      en: { type: 'string' },
      // point: 이 문장의 핵심 구문/문법 짧은 태그 (예: '수동태','관계사절','분사구문')
      point: { type: 'string' },
      chunks: {
        type: 'array', minItems: 1,
        items: {
          type: 'object', additionalProperties: false, required: ['en', 'kor'],
          properties: { en: { type: 'string' }, kor: { type: 'string' } },
        },
      },
      vocab: {
        type: 'array', minItems: 1,
        items: {
          type: 'object', additionalProperties: false, required: ['word', 'mean'],
          properties: { word: { type: 'string' }, mean: { type: 'string' } },
        },
      },
      catch: { type: 'string' },
      trap: { type: 'string' },
    },
  };
}

const PASSAGE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['passages'],
  properties: {
    passages: {
      type: 'array', minItems: 1,
      items: {
        type: 'object', additionalProperties: false,
        required: ['title', 'source', 'topic', 'catch', 'claim', 'structure', 'paraphrases', 'sentences'],
        properties: {
          title: { type: 'string' },   // 지문 주제 한 줄
          source: { type: 'string' },  // 출처/문항번호 (알면)
          topic: { type: 'string' },   // 소재 = "이 지문 뭐에 관한 거야" 1~2문장
          catch: { type: 'string' },   // 지문 전체 요지 "이 정도는 캐치" 1~2문장
          claim: {                     // 필자 주장(정답) — 입장 + 근거
            type: 'object', additionalProperties: false,
            required: ['stance', 'why'],
            properties: {
              stance: { type: 'string', description: "필자 입장: '긍정적' / '부정적·비판적' / '중립적' 중 하나에 짧은 설명을 덧붙여" },
              why: { type: 'string' },
            },
          },
          structure: {                 // 글의 구조(정답) — 유형 + 근거
            type: 'object', additionalProperties: false,
            required: ['type', 'why'],
            properties: {
              type: { type: 'string', description: "통념→반박(반전) / 주장→근거·예시 / 문제→해결(방안) / 비교·대조 / 시간·순서(나열) / 예시→일반화(결론) 중 하나(또는 근접한 표현)" },
              why: { type: 'string' },
            },
          },
          paraphrases: {               // 재진술 '사슬' 0~3개 (핵심어가 지문에서 반복 재진술되는 흐름)
            type: 'array',
            items: {
              type: 'object', additionalProperties: false,
              required: ['keyword', 'links', 'why'],
              properties: {
                keyword: {
                  type: 'string',
                  description: "이 사슬의 핵심 개념/소재 짧은 이름(2~10자). 비교·대조로 소재가 2개면 각각 다르게(예: '전통 의학').",
                },
                links: {
                  type: 'array', minItems: 2, maxItems: 5, items: { type: 'string' },
                  description: "지문에 나온 순서대로, 같은 개념을 재진술한 표현들 A→A′→A″… (지문 속 실제 표현, 2개 이상).",
                },
                why: {
                  type: 'string',
                  description: "이 사슬이 어떻게 변주됐는지 한 줄(반말). 예: '소유 부정 → 관리인 비유로 같은 뜻을 바꿔 말해'.",
                },
              },
            },
          },
          sentences: { type: 'array', minItems: 1, items: passageSentenceSchema() },
        },
      },
    },
  },
};

const PASSAGE_SYSTEM_PROMPT = `너는 한국 수능/평가원 영어 지문을 '구문해석 교재'로 가공하는 편집자야.
학생에게 반말로 친근하게 설명하는 과외 선생님 톤을 유지해.

주어진 영어 문장들은 '지문(passage)'의 원문 순서 그대로야.
목표는 '한 지문을 온전히 이해'하게 하는 것 — 문법별로 쪼개지 말고 지문 흐름 그대로 구성해.

지문 단위 규칙:
- 문장은 원문 순서를 절대 바꾸지 마(재배열 금지).
- 내용 흐름상 여러 지문이 섞여 있으면 지문 단위로 나눠. 한 지문이면 passages 는 1개.
- title: 그 지문의 주제 한 줄. source: 출처/문항번호를 알면(모르면 빈 문자열 대신 '지문').
- topic: "이 지문 뭐에 관한 거야?" 1~2문장(반말).
- catch: 이 지문에서 반드시 잡아야 할 핵심 내용 = 지문 요지 1~2문장(반말, "~라는 거야!").
  '이 정도는 캐치해야 한다'는 걸 알 수 있게 — 세부보다 전체 메시지.
- claim: 필자 주장(입장). stance 는 '긍정적'/'부정적·비판적'/'중립적' 중 하나.
  ★판단 기준★ 필자가 대상을 두고 쓴 '평가 어휘'와 마지막·전환(But/However) 문장을 봐:
    · 긍정 신호: benefit·beneficial·valuable·crucial·essential·effective·advantage·merit·
      improve·enhance·support·in favor of 같은 칭찬·권장 → 그 대상에 긍정.
    · 부정 신호: drawback·flaw·weakness·problem·harmful·worthless·misleading·fail·lack·
      neglect·ignore·overlook·criticize·doubt·mere·side effect·myth 같은 비판·경계 → 부정.
    · 중립: 긍정·부정 평가어가 뚜렷이 '없고', ⑴ 유보·추측(may·might·tend to·seem·some·often),
      ⑵ 양쪽 균형 제시(on one hand…on the other·both A and B·it depends),
      ⑶ 평가 없는 객관 서술(describe·explain·report·according to)일 때만 중립. 한쪽으로 몰면 중립 아님.
  이런 어휘가 지문에 있으면 그걸 근거로 입장을 정하고, why 에 '어떤 평가 어휘/문장을 보고
  그렇게 판단했는지'를 한 줄로 짚어줘(예: "'valuable·should'로 권장하니 긍정").
- structure: 이 글의 구조. type 은 [통념→반박(반전) / 주장→근거·예시 / 문제→해결(방안) /
  비교·대조 / 시간·순서(나열) / 예시→일반화(결론)] 중 가장 알맞은 하나(또는 근접 표현),
  why 는 그렇게 본 근거(전환어 But/However, 예시, 시간표현 등)를 한 줄로.
- paraphrases: 재진술 '사슬' 0~3개. 재진술은 보통 '핵심 키워드 하나가 지문에서 표현만 바꿔
  반복'되는 사슬이야 — A(첫 등장) → A′(동의어로) → A″(구체 예시로) → A‴(결론에서 다시).
  이 사슬을 잡는 훈련이 빈칸·함의·요지의 뿌리야. 아래 원리를 지켜:
  1) ★기준★ '필자 주장·핵심 소재'가 되는 키워드의 사슬만 뽑아. 곁가지·사소한 세부의
     반복은 넣지 마. 한 사슬 = 같은 개념 하나.
  2) links: 그 키워드를 지문에서 다시 말한 표현들을 '나온 순서대로' 2~5개.
     ★반드시 지문 문장에 있는 어구를 '그대로(verbatim) 복사'해서 넣어★ — 요약하거나 단어를
     바꾸지 마(학생이 지문에서 찾아 써야 하므로 글자 그대로여야 함). 표면 어휘는 서로 다르되
     뜻은 같은 어구들이어야 해. 변주 장치: 동의어 / 추상↔구체 / 명사화↔동사화 / 능동↔수동 /
     긍정↔이중부정 / 비유↔직설.
  3) keyword: 그 사슬의 핵심 개념을 짧은 이름으로. 비교·대조로 소재가 2개면 사슬을 2개로
     나눠 각각 keyword 를 다르게(예: '전통 의학' 사슬, '현대 의학' 사슬) — 두 소재가 각각
     어떻게 재진술되는지 보이게.
  4) why: 이 사슬이 어떻게 변주됐는지 한 줄(반말). 예: '소유 부정 → 관리인 비유로 바꿔 말해'.
  5) ★가장 중요★ 이런 사슬이 뚜렷하지 않으면 '절대' 억지로 넣지 마 — 빈 배열([])이 정답이야.
     서사문(이야기)·편지/안내문·대화문·단순 시간순 나열 지문은 대개 사슬이 없어 → [] 로.
     확신이 서는 '진짜' 사슬만. 품질 > 개수.

각 문장 가공(구문해석 도움은 그대로 유지):
- chunks(끊어읽기): 앞에서부터 순서대로 의미 덩어리로 끊고 직독직해(en=영어조각, kor=우리말).
- vocab: 그 문장에서 모를 만한 단어 3~6개와 뜻.
- catch: 이 문장 핵심 뜻 한 줄(20~45자, 반말, 문법 용어 금지).
- trap: 이 문장에서 **오역하기 쉬운 부분을 미리** 짚어줘. "A로 잘못 읽기 쉬운데, 실제론 B야" 형식으로,
  그 문장에 실제 있는 요소만(없는 단어 지어내지 마).
- point: 이 문장의 핵심 구문/문법을 짧은 태그로(예: '수동태','관계사절','분사구문','to부정사','전치사구').`;

function passageUserPrompt(sentences) {
  const list = sentences.map((s, i) => `${i + 1}. ${s}`).join('\n');
  return `다음은 업로드된 지문에서 추출한 영어 문장들이야(원문 순서 그대로). `
    + `지문 단위로, 한 지문을 온전히 이해하는 교재로 만들어줘.\n\n${list}`;
}

function normalizePassages(aiData) {
  const list = (aiData.passages || []).filter((p) => p && Array.isArray(p.sentences));
  return list.map((p) => ({
    title: p.title || '지문',
    source: p.source || '지문',
    topic: p.topic || '',
    catch: p.catch || '',
    claim: p.claim && p.claim.stance
      ? { stance: p.claim.stance, why: p.claim.why || '' } : undefined,
    structure: p.structure && p.structure.type
      ? { type: p.structure.type, why: p.structure.why || '' } : undefined,
    paraphrases: Array.isArray(p.paraphrases)
      ? p.paraphrases.map((x) => ({
        keyword: x.keyword || '',
        links: Array.isArray(x.links) ? x.links.slice() : [],
        why: x.why || '',
      })) : undefined,
    sentences: p.sentences.map((s) => ({
      src: String(s.src || ''),
      en: s.en || '',
      point: s.point || '',
      chunks: (s.chunks || []).map((c) => [c.en, c.kor]),
      vocab: (s.vocab || []).map((v) => [v.word, v.mean]),
      catch: s.catch || '',
      trap: s.trap || '',
    })),
  }));
}

// AI 출력의 사소한 흠(빈 끊어읽기 조각/어휘, 빈 src·catch 등)을 자동 보정해
// 검증(불변식)을 통과하도록 정리한다. 못 살리는 문장·지문은 조용히 버린다.
function sanitizePassages(passages) {
  const ne = (v) => typeof v === 'string' && v.trim().length > 0;
  // 영어여야 하는 필드(en·끊어읽기 영어쪽·단어)에 섞인 한글은 제거(방어).
  const deK = (v) => String(v == null ? '' : v).replace(/[가-힣ㄱ-ㅎㅏ-ㅣ]+/g, ' ')
    .replace(/[（(]\s*[)）]|\[\s*\]|【\s*】/g, ' ')  // 남은 빈 괄호 제거
    .replace(/\s+([,.;:!?)\]}])/g, '$1').replace(/([([{])\s+/g, '$1')
    .replace(/\s{2,}/g, ' ').trim();
  return passages.map((p) => {
    const sentences = (p.sentences || []).map((s, i) => {
      const chunks = (s.chunks || [])
        .map((c) => (Array.isArray(c) ? [deK(c[0]), c[1]] : c))   // 영어쪽만 한글 제거
        .filter((c) => Array.isArray(c) && ne(c[0]) && ne(c[1]));
      const vocab = (s.vocab || [])
        .map((v) => (Array.isArray(v) ? [deK(v[0]), v[1]] : v))
        .filter((v) => Array.isArray(v) && ne(v[0]) && ne(v[1]));
      return {
        src: ne(s.src) ? s.src : String(i + 1),
        en: deK(s.en || ''),
        point: s.point || '',
        chunks,
        vocab: vocab.length ? vocab : [[(deK(s.en || '').split(/\s+/)[0] || 'word'), '뜻']],
        catch: ne(s.catch) ? s.catch : '이 문장의 핵심을 한 줄로 잡아보자.',
        trap: s.trap || '',
      };
    }).filter((s) => ne(s.en) && s.chunks.length > 0);
    // 재진술 사슬: 링크를 정리한다.
    //   1) 빈 값·중복 제거,  2) '지문에 실제로 있는' 표현만 남김(못 찾는 빈칸·틀린 답 방지),
    //   3) 지문 등장 순서로 정렬(첫 표현=실제 첫 등장, 화살표 A→A′→A″ 방향 보장).
    //   정리 후 링크가 2개 미만인 사슬은 버림(없으면 렌더에서 미출력).
    const passageNorm = sentences.map((s) => s.en).join(' ').toLowerCase().replace(/[^a-z0-9]/g, '');
    const norm = (v) => String(v).toLowerCase().replace(/[^a-z0-9]/g, '');
    const paraphrases = (Array.isArray(p.paraphrases) ? p.paraphrases : [])
      .map((ch) => {
        const seen = new Set();
        const links = [];
        (ch && Array.isArray(ch.links) ? ch.links : []).forEach((v) => {
          if (!ne(v)) return;
          const t = v.trim(); const k = t.toLowerCase();
          if (seen.has(k)) return;
          const pos = passageNorm.indexOf(norm(t));
          if (pos < 0) return;               // 지문에 없는 표현 → 못 찾는 빈칸이 되므로 제거
          seen.add(k); links.push({ t, pos });
        });
        links.sort((a, b) => (a.pos === b.pos ? 0 : a.pos - b.pos));  // 지문 등장 순서
        return {
          keyword: ne(ch && ch.keyword) ? ch.keyword.trim() : '',
          links: links.map((x) => x.t),
          why: ne(ch && ch.why) ? ch.why.trim() : '',
        };
      })
      .filter((ch) => ch.links.length >= 2);
    return { ...p, paraphrases, sentences };
  }).filter((p) => p.sentences.length > 0);
}

async function callClaudePassages(sentences, apiKey) {
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic(apiKey ? { apiKey } : undefined);
  const stream = client.messages.stream({
    model: DEFAULT_MODEL,
    max_tokens: 32000,
    thinking: { type: 'adaptive' },
    system: PASSAGE_SYSTEM_PROMPT,
    messages: [{ role: 'user', content: passageUserPrompt(sentences) }],
    output_config: { format: { type: 'json_schema', schema: PASSAGE_SCHEMA } },
  });
  const final = await stream.finalMessage();
  const text = final.content.filter((b) => b.type === 'text').map((b) => b.text).join('');
  return JSON.parse(text);
}

// ── 대량 처리: 한 번에 다 보내면 출력이 토큰 한도를 넘어 JSON 이 잘린다.
//    그래서 (1) 지문 경계만 싸게 나누고 (2) 지문별로 따로 생성해 합친다. ──
const MAX_PER_CALL = 12; // 한 생성 호출이 다루는 최대 문장 수(잘림 방지 안전선)
const GEN_CONCURRENCY = 3; // 동시 생성 호출 수(레이트리밋 여유)

// 지정 동시성으로 순서를 보존하며 매핑
async function mapLimit(items, limit, fn) {
  const out = new Array(items.length);
  let i = 0;
  const worker = async () => {
    while (i < items.length) { const idx = i; i += 1; out[idx] = await fn(items[idx], idx); }
  };
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return out;
}

// [start,end](1-based) 그룹이 MAX_PER_CALL 을 넘으면 잘게 쪼갠다.
function splitLargeGroups(groups) {
  const out = [];
  groups.forEach(([a, b]) => {
    for (let s = a; s <= b; s += MAX_PER_CALL) out.push([s, Math.min(b, s + MAX_PER_CALL - 1)]);
  });
  return out;
}

// 문장이 적으면 통짜, 실패 시 폴백용 균등 분할
function evenGroups(n, size) {
  const g = [];
  for (let s = 1; s <= n; s += size) g.push([s, Math.min(n, s + size - 1)]);
  return g;
}

// Phase 1: 지문 경계 나누기 (작은 출력 → 잘리지 않음)
async function segmentPassages(sentences, apiKey) {
  if (sentences.length <= MAX_PER_CALL) return [[1, sentences.length]];
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic(apiKey ? { apiKey } : undefined);
  const N = sentences.length;
  const list = sentences.map((s, i) => `${i + 1}. ${s}`).join('\n');
  const schema = {
    type: 'object', additionalProperties: false, required: ['starts'],
    properties: { starts: { type: 'array', items: { type: 'integer' } } },
  };
  const sys = '너는 영어 문장 목록을 원래 지문(passage) 단위로 나누는 편집자야. '
    + '문장은 원문 순서야. 내용 흐름(주제 전환, 편지/이야기/설명문 등)을 보고 '
    + '각 지문이 "시작하는 문장 번호"만 오름차순으로 돌려줘(첫 지문은 1). 한 지문은 보통 4~10문장이야.';
  const stream = client.messages.stream({
    model: DEFAULT_MODEL, max_tokens: 2000, system: sys,
    messages: [{ role: 'user', content: `다음 문장들을 지문 단위로 나눠, 각 지문 시작 문장 번호를 starts 로 줘.\n\n${list}` }],
    output_config: { format: { type: 'json_schema', schema } },
  });
  const final = await stream.finalMessage();
  const text = final.content.filter((b) => b.type === 'text').map((b) => b.text).join('');
  let starts = [];
  try { starts = (JSON.parse(text).starts || []).filter((x) => Number.isInteger(x) && x >= 1 && x <= N); } catch (_) { /* 폴백 */ }
  starts = [...new Set([1, ...starts])].sort((a, b) => a - b);
  if (starts.length < 1) return evenGroups(N, 8);
  // 시작번호만으로 [1..N] 을 빈틈없이 타일링
  return starts.map((s, i) => [s, i + 1 < starts.length ? starts[i + 1] - 1 : N]);
}

// MOCK: 원문 순서를 지문 단위로 (문장 많으면 ~8개씩 분할). 문법은 point 태그로.
function mockPassages(sentences) {
  const pointOf = (s) => {
    const t = s.toLowerCase();
    if (/\bby\b/.test(t) || /\b(was|were|been)\b/.test(t)) return '수동태';
    if (/\b(who|which|that|whose|where|whom)\b/.test(t)) return '관계사절';
    if (/\bto\s+[a-z]+/.test(t)) return 'to부정사';
    if (/[a-z]+ing\b/.test(t)) return '분사/동명사';
    return '전치사구';
  };
  const mk = (en, i) => {
    const words = en.split(/\s+/);
    const mid = Math.max(2, Math.floor(words.length / 2));
    return {
      src: String(i + 1),
      en,
      point: pointOf(en),
      chunks: [[words.slice(0, mid).join(' '), '(앞 덩어리 해석)'], [words.slice(mid).join(' '), '(뒤 덩어리 해석)']],
      vocab: [[words[0] || 'word', '(뜻)'], [words[mid] || 'word', '(뜻)']],
      catch: '이 문장의 핵심을 한 줄로 잡아보는 거야!',
      trap: '수식어를 주어로 잘못 읽기 쉬운데, 진짜 주어·동사부터 찾아 읽어야 해.',
    };
  };
  const passages = [];
  const SIZE = 8;
  for (let g = 0; g < sentences.length; g += SIZE) {
    const chunk = sentences.slice(g, g + SIZE);
    passages.push({
      title: `지문 ${passages.length + 1}`,
      source: '지문',
      topic: '이 지문이 무엇에 관한 내용인지 전체 흐름을 잡아보자.',
      catch: '이 지문에서 반드시 잡아야 할 핵심 메시지를 한두 줄로 정리하는 거야!',
      claim: { stance: '중립적', why: '(MOCK: 실제로는 필자 입장을 긍정/부정/중립으로 판단)' },
      structure: { type: '주장 → 근거·예시', why: '(MOCK: 실제로는 전환어·예시·시간표현을 보고 판단)' },
      paraphrases: [],
      sentences: chunk.map((en, i) => mk(en, g + i)),
    });
  }
  return { passages };
}

// 진입점: sentences(원문 순서) → { passages, mode }
async function structurePassages(sentences, opts = {}) {
  // 웹에서 넘어온 키(opts.apiKey) 우선, 없으면 환경변수.
  const apiKey = opts.apiKey || process.env.ANTHROPIC_API_KEY;
  const useMock = opts.mock || process.env.ANTHROPIC_MOCK === '1' || !apiKey;
  // mockPassages 는 이미 내부(튜플) 스키마이므로 normalize 를 거치지 않는다.
  if (useMock) return { passages: mockPassages(sentences).passages, mode: 'mock' };

  const onProgress = typeof opts.onProgress === 'function' ? opts.onProgress : () => {};

  // 1) 지문 경계 나누기 (작은 출력) → 각 그룹이 너무 크면 잘게 쪼갠다(잘림 방지)
  let groups = await segmentPassages(sentences, apiKey);
  groups = splitLargeGroups(groups).filter(([a, b]) => a <= b);
  onProgress(`지문 ${groups.length}개로 나눔 — 지문별로 생성 시작`);

  // 2) 지문별 생성(동시성 제한). 한 지문이 실패해도 나머지는 살린다.
  let done = 0;
  const results = await mapLimit(groups, GEN_CONCURRENCY, async ([a, b]) => {
    const sub = sentences.slice(a - 1, b);
    try {
      const aiData = await callClaudePassages(sub, apiKey);
      const norm = normalizePassages(aiData);
      done += 1; onProgress(`지문 생성 ${done}/${groups.length} 완료`);
      return norm;
    } catch (e) {
      // 키·모델·권한 문제(401/403/404)는 전체 공통 원인 → 건너뛰지 말고 바로 알림
      const st = e.status || e.statusCode;
      if (st === 401 || st === 403 || st === 404) throw e;
      done += 1; onProgress(`지문 ${done}/${groups.length} 생성 실패(건너뜀): ${e.message}`);
      return [];
    }
  });

  const passages = sanitizePassages(results.flat());
  if (!passages.length) throw new Error('모든 지문 생성이 실패했어요. (키·모델 권한·네트워크 확인)');
  return { passages, mode: 'ai' };
}

module.exports = {
  structureSentences, normalize, OUTPUT_SCHEMA, CHAPTERS, DEFAULT_MODEL,
  structurePassages, normalizePassages, sanitizePassages, PASSAGE_SCHEMA,
};

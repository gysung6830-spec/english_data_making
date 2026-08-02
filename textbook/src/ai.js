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
        required: ['title', 'source', 'topic', 'catch', 'sentences'],
        properties: {
          title: { type: 'string' },   // 지문 주제 한 줄
          source: { type: 'string' },  // 출처/문항번호 (알면)
          topic: { type: 'string' },   // "이 지문 뭐에 관한 거야" 1~2문장
          catch: { type: 'string' },   // 지문 전체 요지 "이 정도는 캐치" 1~2문장
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

각 문장 가공(구문해석 도움은 그대로 유지):
- chunks(끊어읽기): 앞에서부터 순서대로 의미 덩어리로 끊고 직독직해(en=영어조각, kor=우리말).
- vocab: 그 문장에서 모를 만한 단어 3~6개와 뜻.
- catch: 이 문장 핵심 뜻 한 줄(20~45자, 반말, 문법 용어 금지).
- trap: 자주 틀리는 해석 경고 한 줄(그 문장에 실제 있는 요소만).
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

async function callClaudePassages(sentences) {
  const Anthropic = require('@anthropic-ai/sdk');
  const client = new Anthropic();
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
      trap: '진짜 주어·동사를 먼저 찾고, 나머지는 꾸밈말로 걸러 읽어.',
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
      sentences: chunk.map((en, i) => mk(en, g + i)),
    });
  }
  return { passages };
}

// 진입점: sentences(원문 순서) → { passages, mode }
async function structurePassages(sentences, opts = {}) {
  const useMock = opts.mock || process.env.ANTHROPIC_MOCK === '1' || !process.env.ANTHROPIC_API_KEY;
  // mockPassages 는 이미 내부(튜플) 스키마이므로 normalize 를 거치지 않는다.
  if (useMock) return { passages: mockPassages(sentences).passages, mode: 'mock' };
  const aiData = await callClaudePassages(sentences);
  return { passages: normalizePassages(aiData), mode: 'ai' };
}

module.exports = {
  structureSentences, normalize, OUTPUT_SCHEMA, CHAPTERS, DEFAULT_MODEL,
  structurePassages, normalizePassages, PASSAGE_SCHEMA,
};

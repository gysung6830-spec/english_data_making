// document.js — 문서 조립 (명세 §5.1 문서 구조)
//
// 1. 표지 (제목/부제/출처/사용법 — "쌤이 알려주는 사용법", 반말 지도 톤)
// 2. 챕터마다: 제목 → 무엇인가요 → 신호 → 해석법 → 같이 풀어보기(2) → 혼자 풀어보기(나머지) → 페이지브레이크
// 3. 맨 뒤: 정답 섹션 (챕터별 그룹핑, practice 만 — chunks 를 이어붙인 한글)

const {
  Document, Paragraph, TextRun, AlignmentType, ShadingType,
} = require('docx');
const S = require('./styles');
const B = require('./boxes');
const { makeTip } = require('./tip');

// 각 챕터의 worked 를 앞 2문장만 "같이 풀어보기" 로 쓰고, 나머지는 steps 를
// 떼어 "혼자 풀어보기(practice)" 앞쪽으로 이동시킨다(명세 §4). 원본은 건드리지 않음.
function splitWorked(categories) {
  return categories.map((cat) => {
    const keepWorked = cat.worked.slice(0, 2);
    const moved = cat.worked.slice(2).map((w) => ({
      src: w.src, en: w.en, chunks: w.chunks, catch: w.catch, vocab: w.vocab, trap: w.trap,
    }));
    return { ...cat, worked: keepWorked, practice: [...moved, ...cat.practice] };
  });
}

// 문장별 함정 문구 선택: 문장에 trap 이 있으면 그걸, 없으면 챕터 traps 를 순환.
function pickTrap(cat, s, i) {
  if (s && s.trap) return s.trap;
  const arr = cat && cat.traps;
  return Array.isArray(arr) && arr.length ? arr[i % arr.length] : '';
}

// ── 표지 ─────────────────────────────────────────────
function coverParagraphs() {
  const center = (children, after) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children });
  return [
    center([new TextRun({ text: '문법으로 뚫는 영어 해석 교재', bold: true, size: 44, color: S.NAVY, font: S.FONT })], 200),
    // 부제는 실제 챕터 순서(수동태→…→분사구문)에 맞춰 표기
    center([new TextRun({ text: '전치사구 · 수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문', size: 26, color: S.BRASS, bold: true, font: S.FONT })], 100),
    center([new TextRun({ text: '자료 출처: 2023학년도 수능 · 2024년 9월 평가원 모의평가(고3) 기출', size: 20, italics: true, font: S.FONT })], 100),
    center([new TextRun({ text: '기초 문법 학습용 · 과외 교재', size: 18, color: '666666', font: S.FONT })], 700),

    new Paragraph({
      spacing: { before: 200, after: 100 },
      shading: { type: ShadingType.CLEAR, fill: S.LIGHTGRAY },
      children: [new TextRun({ text: '  📌 쌤이 알려주는 사용법', bold: true, size: 22, color: S.NAVY, font: S.FONT })],
    }),
    B.p('문법 용어가 낯설어도 괜찮아. 이 교재는 그런 너를 위해 만든 거야 — 순서대로만 따라오면 돼.'),
    B.bullet('챕터마다 순서는 이래: ① 이게 뭔지 쌤이 설명 → ② 어떻게 알아채는지(신호) → ③ 쌤이랑 같이 풀기(2문장) → ④ 너 혼자 풀어보기(나머지 전부)'),
    B.bullet('문장마다 박스 순서는 이래: 어휘 → 끊어읽기 팁 → 끊어읽기(영어→한글) → ⚠️ 이거 조심(함정) → 이 정도는 캐치.'),
    B.bullet('끊어읽기는 앞에서부터만 읽어, 뒤로 돌아가지 말고 — 그게 진짜 독해야. 영어 원문은 볼드로 크게 표시해뒀어.'),
    B.bullet('⚠️ 이거 조심 박스는 자주 틀리는 함정을 미리 알려줘 — 읽기 전에 꼭 체크해. 연습문제는 답 쓰는 칸이 비어있으니 직접 써보고, 정답은 맨 뒤에서 확인해.'),
    B.pageBreak(),
  ];
}

// ── 설명 섹션 ────────────────────────────────────────
function introSection(cat) {
  const out = [B.h1(cat.title)];
  out.push(B.h2('무엇인가요?'));
  cat.intro.forEach((t) => out.push(B.p(t)));
  out.push(B.h2('어떻게 찾나요? (신호)'));
  cat.signal.forEach((t) => out.push(B.bullet(t)));
  out.push(B.h2('어떻게 해석하나요?'));
  cat.method.forEach(([l, t]) => out.push(new Paragraph({
    spacing: { after: 50 },
    indent: { left: 300 },
    children: [
      new TextRun({ text: l + '  ', bold: true, color: S.NAVY, size: 20, font: S.FONT }),
      new TextRun({ text: t, size: 20, font: S.FONT }),
    ],
  })));
  return out;
}

// ── 문장 렌더 ────────────────────────────────────────
// 순서: 어휘 → 끊어읽기 팁(어디서 끊을지) → 끊어읽기 → 함정 주의 → (내 해석) → 캐치
function renderWorked(w, trap) {
  return [
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.tipBox(makeTip(w.chunks)),
    ...B.chunkBox(w.chunks),
    ...B.trapBox(trap),
    ...B.catchBox(w.catch),
  ];
}
// 연습문제: 초록 끊어읽기 카드는 빼고, 학생이 직접 끊어 읽고 해석을 쓰는 칸을 준다.
// (끊어읽기 정답·캐치는 맨 뒤 정답·해설 섹션에서 확인)
function renderPractice(w, idx, trap) {
  return [
    B.h3(`연습 ${idx + 1}`),
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.tipBox(makeTip(w.chunks)),
    ...B.trapBox(trap),
    ...B.answerWriteBox(),
  ];
}

// ── 챕터 ─────────────────────────────────────────────
function chapterParagraphs(cat) {
  const out = [...introSection(cat)];
  // 같이 풀어보기 · 혼자 풀어보기는 각각 새 페이지에서 시작
  out.push(B.pageBreak());
  out.push(B.h2('같이 풀어보기'));
  cat.worked.forEach((w, i) => out.push(...renderWorked(w, pickTrap(cat, w, i))));
  out.push(B.pageBreak());
  out.push(B.h2('혼자 풀어보기 (연습문제)'));
  cat.practice.forEach((w, i) => out.push(...renderPractice(w, i, pickTrap(cat, w, i))));
  out.push(B.pageBreak());
  return out;
}

// ── 정답·해설 섹션 (맨 뒤, practice 만) ────────────────
//    문제마다 끊어읽기 정답(영어/한글) + 핵심(캐치)을 실어 해설로 제공.
function answerParagraphs(categories) {
  const out = [B.pageBreak(), B.h1('정답 · 해설 — 혼자 풀어보기')];
  out.push(B.p('직접 푼 걸 여기서 맞춰보자. 끊어읽기 정답과 이 문장에서 붙잡을 핵심을 정리했어.'));
  categories.forEach((cat) => {
    if (!cat.practice || cat.practice.length === 0) return;
    out.push(B.h2(cat.key));
    cat.practice.forEach((w, i) => {
      out.push(B.h3(`${i + 1}. ${w.en}  [${w.src}]`));
      out.push(...B.chunkBox(w.chunks));   // 끊어읽기 정답(영어/한글)
      out.push(...B.catchBox(w.catch));    // 핵심
    });
  });
  return out;
}

// ── 지문(passage) 모드 docx ─────────────────────────
// 목차=지문, 문장 원문 순서, 문법은 '구문 포인트' 표기, 지문 요지 캐치.
function passageSentenceParas(s, idx) {
  const out = [
    new Paragraph({
      spacing: { before: 200, after: 40 },
      children: [
        new TextRun({ text: `${idx}. `, bold: true, size: 22, color: S.NAVY, font: S.FONT }),
        new TextRun({ text: s.en, bold: true, size: 24, font: S.FONT_EN, color: '111111' }),
      ],
    }),
  ];
  if (s.point) {
    out.push(new Paragraph({
      spacing: { after: 80 },
      children: [new TextRun({ text: `구문 포인트 — ${s.point}`, bold: true, size: 18, color: S.BRASS, font: S.FONT })],
    }));
  }
  // 순서: 어휘 → 해석(쓰기) → 캐치(쓰기) → 이거 조심(오역 주의)
  //   (끊어읽기 원리는 책 앞 '끊어읽기 팁 — 어디서 끊을까?' 페이지에 한 번)
  out.push(...B.vocabBox(s.vocab));
  out.push(...B.interpretWriteBox());
  out.push(...B.catchWriteBox());
  out.push(...B.trapBox(s.trap));
  return out;
}

// 책 앞 '끊어읽기 팁 — 어디서 끊을까?' 페이지 (목차 항목 1회)
const CUT_SIGNALS_DOCX = [
  ['① 전치사 앞 (in/on/at/of/with/for…)', "전치사구(전치사+명사)는 한 덩어리 — 예) in 1937 → ‘1937년에’"],
  ['② to부정사 앞 (to+동사원형)', "‘~하는 것/~할/~하기 위해’ 덩어리 — 예) to house his works → ‘작품을 소장하기 위한’"],
  ['③ 접속사 앞 (and/but/that/because/when…)', '뒤에 새 절(주어+동사)이 붙어 — 예) …, and he started teaching → 새 사건 시작'],
  ['④ 관계사 앞 (who/which/that/where…)', '앞 명사를 꾸미는 절의 시작 — 예) the man who lives … → ‘…하는 그 남자’'],
  ['⑤ 분사 · 콤마 (-ing/-ed 수식, ,)', '새 수식 덩어리 시작·이미 찍힌 경계 — 예) …, was established → 콤마·수동에서 끊기'],
];
function principlePageParas() {
  const out = [B.h1('끊어읽기 팁 — 어디서 끊을까?')];
  out.push(B.p('핵심 원리: 진짜 주어+동사(뼈대)를 먼저 잡고, 나머지 수식 덩어리는 신호어 앞에서 끊어 앞에서부터 붙여 읽어 — 되돌아가지 않기!', { bold: true }));
  out.push(B.h2('끊는 신호 5가지'));
  CUT_SIGNALS_DOCX.forEach(([name, rule]) => {
    out.push(new Paragraph({
      spacing: { after: 40 }, indent: { left: 200 },
      children: [
        new TextRun({ text: `${name}  `, bold: true, size: 21, color: S.NAVY, font: S.FONT }),
        new TextRun({ text: rule, size: 20, font: S.FONT }),
      ],
    }));
  });
  out.push(B.p('끊는 자리는 늘 ‘새 덩어리가 시작되는 신호어 앞’ — 지문에서 이 5개만 찾으면 문장이 저절로 끊긴다.'));
  out.push(B.pageBreak());
  return out;
}

// 책 앞 '글의 구조 — 어떤 짜임이 있나?' 페이지 (목차 항목 1회, 모의고사 지문 기준)
const STRUCTURE_GUIDE_DOCX = [
  ['① 통념 → 반박(반전)',
    '통념: many people think/believe · it is widely believed · traditionally · most people assume  →  반전: But · However · Yet · In fact · Contrary to',
    '흔한 생각(통념)을 깔아둔 뒤 뒤집어 필자 주장을 편다'],
  ['② 주장 → 근거·예시',
    '주장: should · must · it is important that  →  근거·예시: because · for example · research shows · therefore',
    '주장을 먼저 내세우고 이유·연구·예시로 뒷받침'],
  ['③ 문제 → 해결(방안)',
    '문제: problem · challenge · issue · concern  →  해결: solution · solve · address · one way to · need to',
    '문제를 제기하고 해결책·방안을 제시'],
  ['④ 비교 · 대조',
    '대조: while · whereas · unlike · in contrast · on the other hand  ·  비교: similarly · likewise · just as · both',
    'A와 B의 공통점·차이점을 견줌'],
  ['⑤ 시간 · 순서(나열)',
    '순서: first · second · then · next · later · after · finally  ·  시간: in 1937 · meanwhile · over time',
    '사건·과정을 시간·순서대로(전기·실험·역사)'],
  ['⑥ 예시 → 일반화(결론)',
    '예시: for example · for instance · such as · consider  →  결론: thus · therefore · in short · this suggests · overall',
    '구체 사례들을 든 뒤 일반 원리·결론으로 묶음'],
];
function structureTypesPageParas() {
  const out = [B.h1('글의 구조 — 어떤 짜임이 있나?')];
  out.push(B.p('글의 구조 = 필자가 생각을 배치한 ‘틀’. 전환어(But/However…)와 연결어를 신호로 잡으면 구조가 보이고, 구조가 보이면 요지·필자 주장이 빨리 잡힌다. (모의고사·수능 독해 지문 기준 6가지)', { bold: true }));
  STRUCTURE_GUIDE_DOCX.forEach(([name, sig, flow]) => {
    out.push(new Paragraph({
      spacing: { after: 20 }, indent: { left: 200 },
      children: [new TextRun({ text: `${name}  —  ${flow}`, bold: true, size: 21, color: S.NAVY, font: S.FONT })],
    }));
    out.push(new Paragraph({
      spacing: { after: 90 }, indent: { left: 360 },
      children: [new TextRun({ text: `🔎 ${sig}`, size: 18, italics: true, color: '6A57B0', font: S.FONT })],
    }));
  });
  out.push(B.p('지문마다 ‘글의 구조 — 해석 전에 예측!’에서 이 6개 중 하나를 골라 보고, 지문 끝에서 정답과 맞춰본다.'));
  out.push(B.pageBreak());
  return out;
}

// 지문 끝 답지 — 문장별 모범 해석(끊어읽기) + 모범 캐치
function passageAnswerParas(p) {
  const out = [B.pageBreak(), B.h1('답지 — 해석 · 캐치'), B.p('위에서 직접 쓴 걸 여기서 맞춰보자.')];
  (p.sentences || []).forEach((s, i) => {
    // src(문항번호)가 짧은 라벨일 때만 표시. AI 가 문장 전체를 넣는 경우는 생략.
    const tag = s.src && String(s.src).length <= 10 ? `  [${s.src}]` : '';
    out.push(B.h3(`${i + 1}. ${s.en}${tag}`));
    out.push(...B.chunkBox(s.chunks));
    if (s.catch) out.push(...B.catchBox(s.catch));
  });
  return out;
}

// 🧩 글의 구조 고르기 (해석 전에) — 체크 목록
const STRUCTURE_TYPES = [
  '통념 → 반박(반전)', '주장 → 근거·예시', '문제 → 해결(방안)',
  '비교 · 대조', '시간 · 순서(나열)', '예시 → 일반화(결론)',
];
// 해석 전 예측 4코너(소재·필자주장·구조·재진술) — 직접 쓰는 체크 목록
function predictChoiceParas(p) {
  const out = [];
  out.push(B.p('통째로 읽고, 해석 들어가기 전에 먼저 예측해봐! (정답은 지문 끝)', { bold: true }));
  out.push(B.p('🔎 소재 — 이 지문, 뭐에 관한 글이야? (한 줄):  ______________________________________'));
  out.push(B.p('🗣️ 필자 주장 — 필자 입장은?   ☐ 긍정적   ☐ 부정적·비판적   ☐ 중립적'));
  out.push(B.p('     한 줄 요약: ____________________________   ·   근거 문장 번호: __________'));
  out.push(B.p('🧩 이 글, 어떤 구조야? (하나 ✓ · 앞 “글의 구조” 페이지 참고)'));
  STRUCTURE_TYPES.forEach((t) => out.push(new Paragraph({
    spacing: { after: 30 }, indent: { left: 240 },
    children: [new TextRun({ text: `☐  ${t}`, size: 21, font: S.FONT })],
  })));
  out.push(B.p('     근거(전환·연결 표현이나 문장 번호): ____________________________'));
  const paraQ = (p.paraphrases || []).filter((x) => Array.isArray(x) && String(x[0] == null ? '' : x[0]).trim());
  if (paraQ.length) {
    out.push(B.p('🔗 재진술(같은 말) 찾기 — 아래 표현과 같은 뜻으로 바꿔 쓴 말을 지문에서 찾아 써봐:'));
    paraQ.forEach(([a]) => out.push(new Paragraph({
      spacing: { after: 30 }, indent: { left: 240 },
      children: [new TextRun({ text: `${a}  ≈  ______________________________`, size: 21, font: S.FONT })],
    })));
  }
  return out;
}
// 지문 끝: 해석 전 예측 정답 공개 — 별도 페이지 + 항목별 카드(가독성↑)
const GRAM = '6A57B0'; const GRAMBG = 'F0EDF9'; const GRAMLINE = 'DDD4F2';
function revealItem(label, main, why) {
  const kids = [new Paragraph({
    spacing: { after: why ? 50 : 0 },
    children: [
      new TextRun({ text: `${label}  `, bold: true, size: 22, color: GRAM, font: S.FONT }),
      new TextRun({ text: main, bold: true, size: 22, font: S.FONT }),
    ],
  })];
  if (why) kids.push(new Paragraph({ children: [new TextRun({ text: why, size: 20, color: '4B4B57', font: S.FONT })] }));
  return B.makeBox(GRAMBG, GRAMLINE, kids);
}
function predictRevealParas(p) {
  // 재진술: 양쪽 값이 모두 있는 짝만
  const pairs = (p.paraphrases || []).filter((x) => Array.isArray(x)
    && String(x[0] == null ? '' : x[0]).trim() && String(x[1] == null ? '' : x[1]).trim());
  const out = [B.pageBreak(), B.h2('✅ 해석 전 예측 — 정답 확인  ·  소재 · 필자 주장 · 글의 구조 · 재진술')];
  if (p.topic) { out.push(revealItem('🔎 소재', p.topic, '')); out.push(B.spacer()); }
  if (p.claim && p.claim.stance) { out.push(revealItem('🗣️ 필자 주장', p.claim.stance, p.claim.why || '')); out.push(B.spacer()); }
  if (p.structure && p.structure.type) { out.push(revealItem('🧩 글의 구조', p.structure.type, p.structure.why || '')); out.push(B.spacer()); }
  if (pairs.length) {
    const kids = [new Paragraph({
      spacing: { after: 70 },
      children: [new TextRun({ text: '🔗 재진술 (같은 말)', bold: true, size: 22, color: GRAM, font: S.FONT })],
    })];
    pairs.forEach(([a, b]) => kids.push(new Paragraph({
      spacing: { after: 50 },
      children: [
        new TextRun({ text: a, bold: true, size: 20, font: S.FONT }),
        new TextRun({ text: '  ≈  ', bold: true, size: 20, color: GRAM, font: S.FONT }),
        new TextRun({ text: b, size: 20, color: '4B4B57', font: S.FONT }),
      ],
    })));
    out.push(B.makeBox(GRAMBG, GRAMLINE, kids)); out.push(B.spacer());
  }
  return out;
}

function passageParagraphs(p, idx) {
  const out = [B.h1(p.title || `지문 ${idx + 1}`)];
  out.push(B.p(`출처: ${p.source || '지문'}`, { italics: true, color: '666666' }));
  out.push(B.h2('지문 통째로 읽기'));
  out.push(new Paragraph({
    spacing: { after: 160 },
    children: (p.sentences || []).flatMap((s, i) => [
      new TextRun({ text: `${i + 1} `, bold: true, color: S.NAVY, size: 20, font: S.FONT }),
      new TextRun({ text: `${s.en} `, size: 22, font: S.FONT_EN }),
    ]),
  }));
  out.push(B.h2('해석 전 예측 — 소재·주장·구조·재진술'));
  out.push(...predictChoiceParas(p));
  out.push(B.pageBreak());
  out.push(B.h2('한 문장씩 직접 풀기'));
  (p.sentences || []).forEach((s, i) => out.push(...passageSentenceParas(s, i + 1)));
  // 지문 끝: 답지(해석·캐치) → 해석 전 예측 정답 → 지문 전체 요지
  out.push(...passageAnswerParas(p));
  out.push(...predictRevealParas(p));
  if (p.catch) { out.push(B.h2('이 지문, 이 정도는 캐치! (전체 요지)')); out.push(...B.catchBox(p.catch)); }
  out.push(B.pageBreak());
  return out;
}

function passageCoverParagraphs(meta = {}) {
  const center = (children, after) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children });
  return [
    center([new TextRun({ text: meta.title || '필생보', bold: true, size: 52, color: S.NAVY, font: S.FONT })], 120),
    center([new TextRun({ text: '필자의 생각이 보이는 영어독해', bold: true, size: 28, color: S.NAVY, font: S.FONT })], 160),
    center([new TextRun({ text: '소재 → 필자 주장(긍정·부정) → 글 구조 → 재진술(같은 말)', size: 22, color: S.BRASS, bold: true, font: S.FONT })], 100),
    center([new TextRun({ text: '업로드한 지문 기반 · 자동 생성', size: 18, color: '666666', font: S.FONT })], 700),
    new Paragraph({
      spacing: { before: 200, after: 100 }, shading: { type: ShadingType.CLEAR, fill: S.LIGHTGRAY },
      children: [new TextRun({ text: '  📌 이렇게 써', bold: true, size: 22, color: S.NAVY, font: S.FONT })],
    }),
    B.bullet('지문마다: ① 통째로 쭉 읽고 → ② 한 문장씩 [어휘·팁·이거조심] 보고 해석과 캐치를 직접 써 → ③ 지문 끝 "답지"에서 해석·캐치 맞춰보고 → ④ "이 지문 이 정도는 캐치"로 전체 요지 확인.'),
    B.bullet('캐치는 매 문장 한 줄로 줄여 쓰는 연습이야 — 누가/무엇이 → 어쨌다만 남기고 곁가지는 버려.'),
    B.bullet('문법은 문장마다 "구문 포인트"로 콕 짚어 줘 — 목차는 문법이 아니라 지문 순서야.'),
    B.pageBreak(),
  ];
}

function buildPassageDocument(passages, meta = {}) {
  const children = [
    ...passageCoverParagraphs(meta),
    ...principlePageParas(),
    ...structureTypesPageParas(),
    ...passages.flatMap((p, i) => passageParagraphs(p, i)),
  ];
  return new Document({
    styles: { default: { document: { run: { font: S.FONT, size: 22 } } } },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } } },
      children,
    }],
  });
}

// ── 최상위 조립 ──────────────────────────────────────
function buildDocument(rawCategories) {
  const categories = splitWorked(rawCategories);
  const children = [
    ...coverParagraphs(),
    ...categories.flatMap(chapterParagraphs),
    ...answerParagraphs(categories),
  ];

  return new Document({
    styles: { default: { document: { run: { font: S.FONT, size: 22 } } } },
    sections: [{
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } },
      },
      children,
    }],
  });
}

module.exports = {
  buildDocument, splitWorked, coverParagraphs, chapterParagraphs, answerParagraphs,
  buildPassageDocument, passageParagraphs,
};

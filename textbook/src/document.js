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
      src: w.src, en: w.en, chunks: w.chunks, catch: w.catch, vocab: w.vocab,
    }));
    return { ...cat, worked: keepWorked, practice: [...moved, ...cat.practice] };
  });
}

// ── 표지 ─────────────────────────────────────────────
function coverParagraphs() {
  const center = (children, after) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children });
  return [
    center([new TextRun({ text: '문법으로 뚫는 영어 해석 교재', bold: true, size: 44, color: S.NAVY, font: S.FONT })], 200),
    // 부제는 실제 챕터 순서(수동태→…→분사구문)에 맞춰 표기
    center([new TextRun({ text: '수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문', size: 26, color: S.BRASS, bold: true, font: S.FONT })], 100),
    center([new TextRun({ text: '자료 출처: 2023학년도 대학수학능력시험 20~24 · 31 · 32 · 35 · 40 · 41-42번', size: 20, italics: true, font: S.FONT })], 100),
    center([new TextRun({ text: '기초 문법 학습용 · 과외 교재', size: 18, color: '666666', font: S.FONT })], 700),

    new Paragraph({
      spacing: { before: 200, after: 100 },
      shading: { type: ShadingType.CLEAR, fill: S.LIGHTGRAY },
      children: [new TextRun({ text: '  📌 쌤이 알려주는 사용법', bold: true, size: 22, color: S.NAVY, font: S.FONT })],
    }),
    B.p('문법 용어가 낯설어도 괜찮아. 이 교재는 그런 너를 위해 만든 거야 — 순서대로만 따라오면 돼.'),
    B.bullet('챕터마다 순서는 이래: ① 이게 뭔지 쌤이 설명 → ② 어떻게 알아채는지(신호) → ③ 쌤이랑 같이 풀기(2문장) → ④ 너 혼자 풀어보기(나머지 전부)'),
    B.bullet('문장마다 박스 순서는 이래: 어휘 → 끊어읽기(영어→한글) → 뼈대·괄호 → 이 정도는 캐치 → 왜 여기서 끊었는지 팁.'),
    B.bullet('끊어읽기는 앞에서부터만 읽어, 뒤로 돌아가지 말고 — 그게 진짜 독해야. 영어 원문은 볼드로 크게 표시해뒀어.'),
    B.bullet('연습문제는 뼈대·괄호 박스와 답 쓰는 칸이 비어있어. 직접 표시하고 써본 다음, 정답은 맨 뒤에서 확인해.'),
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
function renderWorked(w) {
  return [
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.chunkBox(w.chunks),
    ...B.skeletonBox(w.steps),
    ...B.catchBox(w.catch),
    ...B.tipBox(makeTip(w.chunks)),
  ];
}
function renderPractice(w, idx) {
  return [
    B.h3(`연습 ${idx + 1}`),
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.chunkBox(w.chunks),
    ...B.skeletonBoxBlank(),
    ...B.answerWriteBox(),
    ...B.catchBox(w.catch),
    ...B.tipBox(makeTip(w.chunks)),
  ];
}

// ── 챕터 ─────────────────────────────────────────────
function chapterParagraphs(cat) {
  const out = [...introSection(cat)];
  out.push(B.h2('같이 풀어보기'));
  cat.worked.forEach((w) => out.push(...renderWorked(w)));
  out.push(B.h2('혼자 풀어보기 (연습문제)'));
  cat.practice.forEach((w, i) => out.push(...renderPractice(w, i)));
  out.push(B.pageBreak());
  return out;
}

// ── 정답 섹션 ────────────────────────────────────────
function answerParagraphs(categories) {
  const out = [B.h1('정답 (혼자 풀어보기 · 참고용 해석)')];
  categories.forEach((cat) => {
    if (!cat.practice || cat.practice.length === 0) return;
    out.push(B.h2(cat.key));
    cat.practice.forEach((w, i) => {
      const kor = w.chunks.map((c) => c[1]).join(' ');
      out.push(B.p(`${i + 1}) ${kor}`));
    });
  });
  return out;
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

module.exports = { buildDocument, splitWorked, coverParagraphs, chapterParagraphs, answerParagraphs };

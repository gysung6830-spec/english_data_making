// document.js — 문서 조립 (명세 §5.1 문서 구조)
//
// 1. 표지
// 2. 챕터마다: 제목 → 무엇인가요 → 신호 → 해석법 → 같이 풀어보기(2) → 혼자 풀어보기(나머지) → 페이지브레이크
// 3. 맨 뒤: 정답 섹션 (챕터별 그룹핑, practice 만)

const {
  Document, Paragraph, TextRun, HeadingLevel, PageBreak, AlignmentType,
} = require('docx');
const { FONT, INK, SIZE } = require('./styles');
const {
  run, para, spacer,
  header, vocabBox, chunkBox, skeletonBox, writeBox, catchBox, tipBox,
} = require('./boxes');

// ── 표지 ─────────────────────────────────────────────
function coverParagraphs() {
  const center = (runs, after = 120) =>
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children: runs });

  return [
    new Paragraph({ spacing: { before: 1200 }, children: [] }),
    center([run('문법으로 뚫는 영어 해석', { bold: true, size: 56 })], 80),
    center([run('수능 기출로 배우는 구문해석 워크북', { bold: true, size: 28, color: INK.muted })], 200),
    center([run('2023학년도 대학수학능력시험 지문 기반', { size: 22, color: INK.muted })], 600),

    para(run('쌤이 알려주는 사용법', { bold: true, size: 26 }), { after: 100 }),
    para(run('자, 이 교재는 이렇게 쓰는 거야.', { size: SIZE.body }), { after: 60 }),
    para(run('① 먼저 챕터 맨 앞 설명을 읽고, "이 문법은 이런 표시를 찾으면 되는구나" 감을 잡자.', { size: SIZE.body }), { after: 40 }),
    para(run('② "같이 풀어보기" 두 문장은 쌤이 뼈대·괄호까지 다 풀어놨어. 소리 내서 따라 읽어봐.', { size: SIZE.body }), { after: 40 }),
    para(run('③ "혼자 풀어보기"는 네가 직접 끊어 읽고, 뼈대·괄호를 채우고, 해석을 써보는 칸이야.', { size: SIZE.body }), { after: 40 }),
    para(run('④ 다 풀고 나서 맨 뒤 정답과 맞춰보자. 틀려도 괜찮아 — 왜 그렇게 끊는지가 더 중요해!', { size: SIZE.body }), { after: 40 }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

// ── 설명 섹션 (무엇인가요 / 신호 / 해석법) ─────────────
function introSection(cat) {
  const out = [];
  out.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 160, before: 80 },
    children: [run(cat.title, { bold: true, size: 34 })],
  }));

  out.push(para(run('무엇인가요?', { bold: true, size: 26, color: INK.brass }), { after: 60 }));
  (cat.intro || []).forEach((line) => out.push(para(run(line, { size: SIZE.body }), { after: 40 })));
  out.push(spacer());

  out.push(para(run('어떻게 찾나요? (신호)', { bold: true, size: 26, color: INK.brass }), { after: 60 }));
  (cat.signal || []).forEach((line) => out.push(para([
    run('▸ ', { size: SIZE.body, color: INK.brass }), run(line, { size: SIZE.body }),
  ], { after: 30 })));
  out.push(spacer());

  out.push(para(run('어떻게 해석하나요?', { bold: true, size: 26, color: INK.brass }), { after: 60 }));
  (cat.method || []).forEach(([label, text], i) => out.push(para([
    run(`${i + 1}. `, { bold: true, size: SIZE.body }),
    run(label + ' ', { bold: true, size: SIZE.body, color: INK.brass }),
    run('— ' + text, { size: SIZE.body }),
  ], { after: 40 })));
  out.push(spacer());
  return out;
}

// ── 문장 하나 렌더 (worked / practice 공통, 명세 §5.2 순서) ──
function renderSentence(s, { isWorked }) {
  const out = [];
  out.push(header(s));                       // 1
  out.push(vocabBox(s.vocab)); out.push(spacer()); // 2
  out.push(chunkBox(s.chunks)); out.push(spacer()); // 3
  out.push(skeletonBox(isWorked ? s.steps : null)); out.push(spacer()); // 4
  if (!isWorked) { out.push(writeBox()); out.push(spacer()); }           // 5 (practice 만)
  out.push(catchBox(s.catch)); out.push(spacer());  // 6
  out.push(tipBox(s.chunks)); out.push(spacer());   // 7
  return out;
}

// ── 챕터 하나 ────────────────────────────────────────
function chapterParagraphs(cat) {
  const out = [...introSection(cat)];

  out.push(para(run('✎ 같이 풀어보기', { bold: true, size: 28 }), { after: 100 }));
  cat.worked.forEach((s) => out.push(...renderSentence(s, { isWorked: true })));

  out.push(para(run('✐ 혼자 풀어보기', { bold: true, size: 28 }), { after: 100 }));
  cat.practice.forEach((s) => out.push(...renderSentence(s, { isWorked: false })));

  out.push(new Paragraph({ children: [new PageBreak()] }));
  return out;
}

// ── 정답 섹션 (맨 뒤, practice 만) ────────────────────
function answerParagraphs(categories) {
  const out = [];
  out.push(new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { after: 160 },
    children: [run('정답 — 혼자 풀어보기', { bold: true, size: 34 })],
  }));
  out.push(para(run('끊어 읽은 덩어리를 순서대로 이어 읽으면 이런 뜻이 돼. 네 해석이랑 맞춰보자!', { size: SIZE.body }), { after: 120 }));

  categories.forEach((cat) => {
    if (!cat.practice || cat.practice.length === 0) return;
    out.push(para(run(cat.title, { bold: true, size: 26, color: INK.brass }), { after: 80, before: 120 }));
    cat.practice.forEach((s) => {
      const answer = (s.chunks || []).map((c) => c[1]).join(' ');
      out.push(para([
        run(`[${s.src}] `, { bold: true, size: SIZE.body, color: INK.brass }),
        run(s.en, { bold: true, size: SIZE.body }),
      ], { after: 20 }));
      out.push(para(run('→ ' + answer, { size: SIZE.body, color: INK.muted }), { after: 100 }));
    });
  });
  return out;
}

// ── 최상위: Document 조립 ─────────────────────────────
function buildDocument(categories) {
  const children = [
    ...coverParagraphs(),
    ...categories.flatMap(chapterParagraphs),
    ...answerParagraphs(categories),
  ];

  return new Document({
    styles: {
      default: {
        document: { run: { font: FONT, size: SIZE.body, color: INK.default } },
      },
    },
    sections: [{
      properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
      children,
    }],
  });
}

module.exports = { buildDocument, coverParagraphs, chapterParagraphs, answerParagraphs };

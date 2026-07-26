// boxes.js — 재사용 가능한 박스/문단 빌더 (명세 §5.2 박스 순서 · §5.4 스타일)
//
// docx 라이브러리는 여러 문단을 하나의 테두리로 묶는 기능이 없어서,
// 모든 박스를 1×1 표(Table) 로 구현한다. 셀 하나에 여러 Paragraph 를 넣고
// 셀 테두리 + 배경색으로 박스처럼 보이게 함(명세 §5.2). 각 박스 뒤에는
// spacer() 로 여백을 준다.

const {
  Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, AlignmentType,
} = require('docx');
const { FONT, COLORS, INK, SIZE } = require('./styles');
const { makeTip } = require('./tip');

// ── 저수준 헬퍼 ─────────────────────────────────────────────

// TextRun 하나. 기본 폰트/색 적용.
function run(text, opts = {}) {
  return new TextRun({
    text: String(text),
    font: FONT,
    bold: opts.bold || false,
    size: opts.size || SIZE.body,
    color: opts.color || INK.default,
  });
}

// Paragraph 하나. runs 는 TextRun 배열.
function para(runs, opts = {}) {
  return new Paragraph({
    children: Array.isArray(runs) ? runs : [runs],
    spacing: { after: opts.after != null ? opts.after : 40, line: opts.line || 288 },
    alignment: opts.alignment,
  });
}

// 박스 사이 여백용 빈 문단
function spacer() {
  return new Paragraph({ children: [], spacing: { after: 80 } });
}

// 셀 테두리 한 벌(모든 변 동일 색/두께)
function allBorders(color) {
  const side = { style: BorderStyle.SINGLE, size: 6, color };
  return { top: side, bottom: side, left: side, right: side };
}

// 1×1 박스 표. colorKey 는 COLORS 의 키(vocab/chunk/…). paragraphs 는 문단 배열.
function box(colorKey, paragraphs) {
  const { fill, border } = COLORS[colorKey];
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: 100, type: WidthType.PERCENTAGE },
            shading: { type: ShadingType.CLEAR, fill, color: 'auto' },
            borders: allBorders(border),
            margins: { top: 120, bottom: 120, left: 160, right: 160 },
            children: paragraphs,
          }),
        ],
      }),
    ],
  });
}

// 박스 제목 줄(이모지 + 라벨)
function boxLabel(emoji, label, color) {
  return para([
    run(emoji + ' ', { size: SIZE.label }),
    run(label, { bold: true, size: SIZE.label, color: color || INK.default }),
  ], { after: 60 });
}

// ── 문장 단위 빌더 (명세 §5.2 순서) ──────────────────────────

// 1. 영어 원문 헤더 — bold, size 27, 문항번호 태그
function header(sentence) {
  return new Paragraph({
    spacing: { after: 100, before: 120, line: 300 },
    children: [
      run(`[${sentence.src}] `, { bold: true, size: SIZE.body, color: INK.brass }),
      run(sentence.en, { bold: true, size: SIZE.headerEn }),
    ],
  });
}

// 2. 📘 어휘 박스
function vocabBox(vocab) {
  const rows = (vocab || []).map(([w, m]) =>
    para([
      run('• ', { size: SIZE.body, color: INK.muted }),
      run(w, { bold: true, size: SIZE.body }),
      run('  —  ' + m, { size: SIZE.body }),
    ], { after: 30 }),
  );
  return box('vocab', [boxLabel('📘', '어휘', COLORS.vocab.border), ...rows]);
}

// 3. ✂ 끊어읽기 박스 — 청크마다 영어(bold, size 22) → 한글(size 19)
function chunkBox(chunks) {
  const lines = [];
  (chunks || []).forEach(([en, kor]) => {
    lines.push(para(run(en, { bold: true, size: SIZE.chunkEn }), { after: 10 }));
    lines.push(para(run(kor, { size: SIZE.chunkKor, color: INK.muted }), { after: 70 }));
  });
  return box('chunk', [boxLabel('✂', '끊어읽기', COLORS.chunk.border), ...lines]);
}

// 4. 🦴 뼈대·괄호 박스
//    worked  : steps 를 그대로 표시
//    practice: 빈 밑줄 두 칸(학생이 직접 작성)
function skeletonBox(steps) {
  const body = [];
  if (steps && steps.length) {
    steps.forEach(([label, text]) => {
      body.push(para([
        run(label + ' : ', { bold: true, size: SIZE.body, color: COLORS.skeleton.border }),
        run(text, { size: SIZE.body }),
      ], { after: 40 }));
    });
  } else {
    body.push(para([run('뼈대(진짜 주어+동사) : ', { bold: true, size: SIZE.body }),
      run('______________________________', { color: INK.muted })], { after: 60 }));
    body.push(para([run('괄호(수식어) : ', { bold: true, size: SIZE.body }),
      run('______________________________', { color: INK.muted })], { after: 40 }));
  }
  return box('skeleton', [boxLabel('🦴', '뼈대·괄호', COLORS.skeleton.border), ...body]);
}

// 5. ✏️ 내 해석 써보기 박스 (practice 만) — 밑줄 두 줄
function writeBox() {
  const line = () => para(run('__________________________________________________', { color: INK.muted }), { after: 90 });
  return box('write', [boxLabel('✏️', '내 해석 써보기', INK.muted), line(), line()]);
}

// 6. ✅ 이 정도는 캐치! 박스
function catchBox(text) {
  return box('catch', [
    boxLabel('✅', '이 정도는 캐치!', COLORS.catch.border),
    para(run(text, { size: SIZE.body }), { after: 20 }),
  ]);
}

// 7. 💡 팁 박스 — "왜 여기서 끊었을까?" 자동 생성
function tipBox(chunks) {
  return box('tip', [
    boxLabel('💡', '왜 여기서 끊었을까?', INK.muted),
    para(run(makeTip(chunks), { size: SIZE.small, color: INK.muted }), { after: 20 }),
  ]);
}

module.exports = {
  run, para, spacer, box, boxLabel,
  header, vocabBox, chunkBox, skeletonBox, writeBox, catchBox, tipBox,
  AlignmentType,
};

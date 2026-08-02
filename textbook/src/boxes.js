// boxes.js — 재사용 가능한 박스/문단 빌더 (명세 §5.2 박스 순서 · §5.4 스타일)
//
// docx 라이브러리는 여러 문단을 하나의 테두리로 묶는 기능이 없어서,
// 모든 박스를 1×1 표(Table) 로 구현한다. 셀 하나에 여러 Paragraph 를 넣고
// 셀 테두리 + 배경색으로 박스처럼 보이게 함(명세 §5.2). 각 박스 함수는
// [표, spacer()] 배열을 돌려주므로 호출부에서 그대로 펼쳐(spread) 넣으면 된다.

const {
  Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType,
} = require('docx');
const S = require('./styles');

// ── 공통 문단/여백 ─────────────────────────────────────
function pageBreak() {
  const { PageBreak } = require('docx');
  return new Paragraph({ children: [new PageBreak()] });
}
function spacer() {
  return new Paragraph({ spacing: { after: 160 }, children: [new TextRun({ text: '' })] });
}
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text, size: 22, font: S.FONT, ...opts })] });
}
function bullet(text, opts = {}) {
  return new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: '• ' + text, size: 22, font: S.FONT, ...opts })] });
}

// ── 제목류 ─────────────────────────────────────────────
function h1(text) {
  return new Paragraph({
    spacing: { before: 480, after: 200 },
    border: { bottom: { color: S.NAVY, space: 4, style: BorderStyle.SINGLE, size: 12 } },
    children: [new TextRun({ text, bold: true, color: S.NAVY, size: 32, font: S.FONT })],
  });
}
function h2(text) {
  return new Paragraph({
    spacing: { before: 260, after: 120 },
    children: [new TextRun({ text, bold: true, color: S.BRASS, size: 24, font: S.FONT })],
  });
}
function h3(text) {
  return new Paragraph({
    spacing: { before: 220, after: 80 },
    children: [new TextRun({ text, bold: true, color: S.NAVY, size: 21, font: S.FONT })],
  });
}

// ── 박스 기본 ──────────────────────────────────────────
function makeBox(bgColor, borderColor, paragraphs) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: bgColor },
            borders: {
              top: { style: BorderStyle.SINGLE, size: 6, color: borderColor },
              bottom: { style: BorderStyle.SINGLE, size: 6, color: borderColor },
              left: { style: BorderStyle.SINGLE, size: 6, color: borderColor },
              right: { style: BorderStyle.SINGLE, size: 6, color: borderColor },
            },
            margins: { top: 100, bottom: 100, left: 150, right: 150 },
            children: paragraphs,
          }),
        ],
      }),
    ],
  });
}
function boxLabel(text, color) {
  return new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text, bold: true, size: 19, color, font: S.FONT })] });
}
function underlineRow(after) {
  return new Paragraph({
    border: { bottom: { color: S.UNDERLINE, space: 1, style: BorderStyle.SINGLE, size: 4 } },
    spacing: { after },
    children: [new TextRun({ text: ' ', size: 19 })],
  });
}

// ── 문장 단위 빌더 (명세 §5.2 순서) ─────────────────────

// 1. 영어 원문 헤더 — bold, size 27 + 문항번호 태그
function engHeader(text, src) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [
      new TextRun({ text, bold: true, size: 27, font: S.FONT_EN, color: '111111' }),
      new TextRun({ text: `  [${src}번]`, size: 16, color: '888888', italics: true, font: S.FONT }),
    ],
  });
}

// 2. 📘 어휘 박스 (한 줄에 " / " 로 연결)
function vocabBox(pairs) {
  const text = pairs.map(([w, m]) => `${w} – ${m}`).join('   /   ');
  return [
    makeBox(S.VOCAB.bg, S.VOCAB.border, [
      boxLabel('📘 어휘', S.VOCAB.txt),
      new Paragraph({ children: [new TextRun({ text, size: 19, color: S.VOCAB.txt, font: S.FONT })] }),
    ]),
    spacer(),
  ];
}

// 3. ✂ 끊어읽기 박스 — 영어(bold, size 22) → 한글(size 19)
//    showKor=false 면 한글은 빈 밑줄(연습문제: 학생이 직접 작성)
function chunkBox(chunks, showKor = true) {
  const lines = chunks.map(([en, kor]) =>
    new Paragraph({
      spacing: { after: 70 },
      children: [
        new TextRun({ text: en, bold: true, size: 22, font: S.FONT_EN, color: S.CHUNK.txt }),
        new TextRun({ text: '  →  ', bold: true, size: 19, color: S.SLASH, font: S.FONT }),
        showKor
          ? new TextRun({ text: kor, size: 19, color: S.CHUNK.txt, font: S.FONT })
          : new TextRun({ text: '________________', size: 19, color: S.UNDERLINE, font: S.FONT }),
      ],
    }),
  );
  return [
    makeBox(S.CHUNK.bg, S.CHUNK.border, [boxLabel('✂ 끊어읽기 (영어 → 한글)', S.CHUNK.txt), ...lines]),
    spacer(),
  ];
}

// 4. ⚠️ 함정 주의 박스 — 이 문장에서 자주 틀리는 해석 경고 (worked·practice 공통)
function trapBox(text) {
  if (!text) return [];
  return [
    makeBox(S.TRAP.bg, S.TRAP.border, [
      new Paragraph({
        children: [
          new TextRun({ text: '⚠️ 이거 조심!  ', bold: true, size: 19, color: S.TRAP.label, font: S.FONT }),
          new TextRun({ text, size: 19, color: S.TRAP.txt, font: S.FONT }),
        ],
      }),
    ]),
    spacer(),
  ];
}

// 5. ✏️ 내 해석 써보기 박스 (practice 만) — 빈 밑줄 두 줄
function answerWriteBox() {
  return [
    makeBox(S.WRITE.bg, S.WRITE.border, [
      boxLabel('✏️ 이 문장이 무슨 내용인 것 같아?', S.WRITE.border),
      underlineRow(220),
      underlineRow(40),
    ]),
    spacer(),
  ];
}

// 6. ✅ 이 정도는 캐치! 박스
function catchBox(text) {
  return [
    makeBox(S.CATCHBG, S.CATCH.border, [
      new Paragraph({
        children: [
          new TextRun({ text: '✅ 이 정도는 캐치!  ', bold: true, size: 19, color: S.CATCH.label, font: S.FONT }),
          new TextRun({ text, size: 19, color: S.CATCH.txt, font: S.FONT }),
        ],
      }),
    ]),
    spacer(),
  ];
}

// ✂ 끊어읽기 팁 박스 — "어디서 끊을까?" (자동 생성 문구를 인자로 받음)
function tipBox(text) {
  return [
    makeBox(S.TIP.bg, S.TIP.border, [
      new Paragraph({
        children: [
          new TextRun({ text: '✂ 끊어읽기 팁 — 어디서 끊을까?  ', bold: true, size: 18, color: '333333', font: S.FONT }),
          new TextRun({ text, size: 18, color: S.TIP.txt, font: S.FONT }),
        ],
      }),
    ]),
    spacer(),
  ];
}

module.exports = {
  pageBreak, spacer, p, bullet, h1, h2, h3,
  makeBox, boxLabel,
  engHeader, vocabBox, chunkBox, trapBox, answerWriteBox, catchBox, tipBox,
};

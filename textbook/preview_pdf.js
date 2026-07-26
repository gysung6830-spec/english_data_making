#!/usr/bin/env node
// preview_pdf.js — 미리보기 PDF 생성기 (Chromium 인쇄)
//
// 정식 산출물은 build_v4.js 의 docx → LibreOffice(soffice) → pdf 파이프라인이다.
// 하지만 일부 환경(현재 개발 샌드박스)에서는 LibreOffice 가 문서를 못 열어
// pdf 변환이 안 된다. 그래서 "지금 눈으로 확인용" 미리보기 PDF 를 만들기 위해,
// 같은 data.js / splitWorked / makeTip 을 써서 HTML 로 렌더링한 뒤 Chromium 으로
// 인쇄한다. 디자인(박스 색·순서)은 docx 와 최대한 맞췄다.
//
// ⚠️ 서체는 NanumSquareRound 가 이 환경에 없어 대체 폰트로 보인다(선생님 PC 의
//    docx 와 동일한 제약). 색/레이아웃/내용 확인용으로만 쓰면 된다.
//
// 사용법: node preview_pdf.js  →  output/output_v4_preview.pdf

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');

const categories = require('./data');
const { splitWorked } = require('./src/document');
const { makeTip } = require('./src/tip');
const S = require('./src/styles');

// Chromium 실행 파일 경로 탐색 (핀 버전이 환경마다 달라 동적으로 찾음)
function findChrome() {
  const candidates = [];
  try {
    candidates.push(...execSync('ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null')
      .toString().trim().split('\n').filter(Boolean));
  } catch (_) { /* ignore */ }
  candidates.push('/opt/pw-browsers/chromium/chrome-linux/chrome');
  return candidates.find((p) => p && fs.existsSync(p)) || undefined;
}

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ── HTML 조각 빌더 ─────────────────────────────────────
function box(cls, inner) { return `<div class="box ${cls}">${inner}</div>`; }
function label(text) { return `<div class="boxlabel">${esc(text)}</div>`; }

function vocabHtml(vocab) {
  const line = vocab.map(([w, m]) => `${esc(w)} – ${esc(m)}`).join('   /   ');
  return box('vocab', label('📘 어휘') + `<div class="vline">${line}</div>`);
}
function chunkHtml(chunks) {
  const lines = chunks.map(([en, kor]) =>
    `<div class="cline"><span class="cen">${esc(en)}</span><span class="arrow"> → </span><span class="ckor">${esc(kor)}</span></div>`).join('');
  return box('chunk', label('✂ 끊어읽기 (영어 → 한글)') + lines);
}
function skeletonHtml(steps) {
  const lines = steps.map(([l, t]) => `<div class="sline"><b>${esc(l)}</b>  ${esc(t)}</div>`).join('');
  return box('skel', label('🦴 뼈대 · 괄호') + lines);
}
function skeletonBlankHtml() {
  return box('skel', label('🦴 뼈대 · 괄호 — 직접 표시해봐!')
    + '<div class="sline">뼈대(진짜 주어+동사):</div><div class="ul"></div>'
    + '<div class="sline">괄호(수식어):</div><div class="ul"></div>');
}
function writeHtml() {
  return box('write', label('✏️ 내 해석 써보기') + '<div class="ul"></div><div class="ul"></div>');
}
function catchHtml(text) {
  return box('catch', `<span class="catchlabel">✅ 이 정도는 캐치!  </span>${esc(text)}`);
}
function tipHtml(text) {
  return box('tip', `<span class="tiplabel">💡 왜 여기서 끊었을까?  </span>${esc(text)}`);
}
function headerHtml(s) {
  return `<div class="enh">${esc(s.en)}<span class="srctag">  [${esc(s.src)}번]</span></div>`;
}

function workedHtml(w) {
  return headerHtml(w) + vocabHtml(w.vocab) + chunkHtml(w.chunks)
    + skeletonHtml(w.steps) + catchHtml(w.catch) + tipHtml(makeTip(w.chunks));
}
function practiceHtml(w, i) {
  return `<div class="h3">연습 ${i + 1}</div>` + headerHtml(w) + vocabHtml(w.vocab)
    + chunkHtml(w.chunks) + skeletonBlankHtml() + writeHtml()
    + catchHtml(w.catch) + tipHtml(makeTip(w.chunks));
}

function chapterHtml(cat) {
  let h = `<h1>${esc(cat.title)}</h1>`;
  h += '<div class="h2">무엇인가요?</div>' + cat.intro.map((t) => `<p>${esc(t)}</p>`).join('');
  h += '<div class="h2">어떻게 찾나요? (신호)</div>' + cat.signal.map((t) => `<p class="bl">▸ ${esc(t)}</p>`).join('');
  h += '<div class="h2">어떻게 해석하나요?</div>' + cat.method.map(([l, t]) => `<p class="mth"><b>${esc(l)}</b> — ${esc(t)}</p>`).join('');
  h += '<div class="h2">같이 풀어보기</div>' + cat.worked.map(workedHtml).join('');
  h += '<div class="h2">혼자 풀어보기 (연습문제)</div>' + cat.practice.map(practiceHtml).join('');
  return `<section>${h}</section>`;
}

function answerHtml(cats) {
  let h = '<h1>정답 (혼자 풀어보기 · 참고용 해석)</h1>';
  cats.forEach((cat) => {
    if (!cat.practice.length) return;
    h += `<div class="h2">${esc(cat.key)}</div>`;
    cat.practice.forEach((w, i) => {
      h += `<p>${i + 1}) ${esc(cat.practice[i].chunks.map((c) => c[1]).join(' '))}</p>`;
    });
  });
  return `<section>${h}</section>`;
}

function coverHtml() {
  return `<section class="cover">
    <div class="ctitle">문법으로 뚫는 영어 해석 교재</div>
    <div class="csub">전치사구 · 수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문</div>
    <div class="csrc">자료 출처: 2023학년도 수능 · 2024년 9월 평가원 모의평가(고3) 기출</div>
    <div class="cnote">기초 문법 학습용 · 과외 교재</div>
    <div class="usebox">
      <div class="useh">📌 쌤이 알려주는 사용법</div>
      <p>문법 용어가 낯설어도 괜찮아. 이 교재는 그런 너를 위해 만든 거야 — 순서대로만 따라오면 돼.</p>
      <p class="bl">• 챕터마다: ① 쌤 설명 → ② 신호 → ③ 같이 풀기(2문장) → ④ 혼자 풀기(나머지 전부)</p>
      <p class="bl">• 문장마다: 어휘 → 끊어읽기 → 뼈대·괄호 → 이 정도는 캐치 → 왜 여기서 끊었는지 팁.</p>
      <p class="bl">• 끊어읽기는 앞에서부터만, 뒤로 돌아가지 말고. 영어 원문은 크게 볼드로 표시했어.</p>
      <p class="bl">• 연습문제는 뼈대·괄호와 답 칸이 비어있어. 직접 쓰고 맨 뒤 정답과 맞춰봐.</p>
    </div>
  </section>`;
}

function css() {
  return `
  * { box-sizing: border-box; }
  body { font-family: "NanumSquareRound","Noto Sans KR","Malgun Gothic",sans-serif; color:#1a1a1a; font-size:12.5px; line-height:1.55; margin:0; }
  section { page-break-after: always; padding: 4px 2px; }
  h1 { color:#${S.NAVY}; font-size:20px; border-bottom:2px solid #${S.NAVY}; padding-bottom:6px; margin:6px 0 12px; }
  .h2 { color:#${S.BRASS}; font-weight:bold; font-size:15px; margin:16px 0 7px; }
  .h3 { color:#${S.NAVY}; font-weight:bold; font-size:13.5px; margin:14px 0 5px; }
  p { margin:4px 0; }
  p.bl { margin:2px 0; }
  p.mth { margin:3px 0 3px 14px; }
  .enh { font-weight:bold; font-size:16px; color:#111; margin:14px 0 6px; }
  .srctag { font-size:10px; color:#888; font-style:italic; font-weight:normal; }
  .box { border-radius:3px; padding:8px 11px; margin:5px 0 9px; }
  .boxlabel { font-weight:bold; font-size:12px; margin-bottom:4px; }
  .vocab { background:#${S.VOCAB.bg}; border:1px solid #${S.VOCAB.border}; }
  .vocab, .vocab .boxlabel { color:#${S.VOCAB.txt}; }
  .vline { font-size:12px; }
  .chunk { background:#${S.CHUNK.bg}; border:1px solid #${S.CHUNK.border}; color:#${S.CHUNK.txt}; }
  .chunk .boxlabel { color:#${S.CHUNK.txt}; }
  .cline { margin:2px 0 6px; }
  .cen { font-weight:bold; font-size:14px; }
  .arrow { color:#${S.SLASH}; font-weight:bold; }
  .ckor { font-size:12.5px; }
  .skel { background:#${S.SKEL.bg}; border:1px solid #${S.SKEL.border}; color:#${S.SKEL.txt}; }
  .skel .boxlabel { color:#${S.SKEL.txt}; }
  .sline { margin:3px 0; }
  .ul { border-bottom:1px solid #aaa; height:15px; margin:4px 0 10px; }
  .write { background:#fff; border:1px solid #333; }
  .write .boxlabel { color:#333; }
  .catch { background:#${S.CATCHBG}; border:1px solid #${S.CATCH.border}; color:#${S.CATCH.txt}; }
  .catchlabel { font-weight:bold; color:#${S.CATCH.label}; }
  .tip { background:#${S.TIP.bg}; border:1px solid #${S.TIP.border}; color:#${S.TIP.txt}; font-size:11.5px; }
  .tiplabel { font-weight:bold; color:#333; }
  .cover { text-align:center; padding-top:120px; }
  .ctitle { color:#${S.NAVY}; font-weight:bold; font-size:30px; margin-bottom:14px; }
  .csub { color:#${S.BRASS}; font-weight:bold; font-size:16px; margin-bottom:16px; }
  .csrc { font-style:italic; font-size:12px; margin-bottom:6px; }
  .cnote { color:#666; font-size:11px; margin-bottom:40px; }
  .usebox { text-align:left; background:#${S.LIGHTGRAY}; border-radius:4px; padding:14px 18px; margin:0 30px; }
  .useh { color:#${S.NAVY}; font-weight:bold; font-size:14px; margin-bottom:8px; }
  `;
}

async function main() {
  const cats = splitWorked(categories);
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css()}</style></head>
    <body>${coverHtml()}${cats.map(chapterHtml).join('')}${answerHtml(cats)}</body></html>`;

  const outDir = path.join(__dirname, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  const htmlPath = path.join(outDir, 'output_v4_preview.html');
  const pdfPath = path.join(outDir, 'output_v4_preview.pdf');
  fs.writeFileSync(htmlPath, html);

  const browser = await chromium.launch({ executablePath: findChrome() });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'load' });
  await page.pdf({
    path: pdfPath, format: 'A4', printBackground: true,
    margin: { top: '14mm', bottom: '14mm', left: '14mm', right: '14mm' },
  });
  await browser.close();
  console.log('✓ 미리보기 PDF 생성:', path.relative(process.cwd(), pdfPath));
}

main().catch((e) => { console.error(e); process.exit(1); });

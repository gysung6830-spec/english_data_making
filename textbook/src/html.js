// html.js — 디자인 PDF용 HTML 렌더러 (재사용 모듈)
//
// 참고 교재(김은아영어연구소 스타일) 디자인을 HTML/CSS 로 구현하고,
// Chromium 으로 인쇄해 PDF 를 만든다. preview_pdf.js(CLI)와 webapp 이 공유한다.
//   - buildHtml(categories)  → 전체 HTML 문자열
//   - renderPdf(html, pdfPath) → Chromium 으로 PDF 저장
//   - findChrome()           → Chromium 실행 파일 경로

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { splitWorked } = require('./document');
const { makeTip } = require('./tip');

const FONTS_DIR = path.join(__dirname, '..', 'fonts');
const FOOTER_BRAND = '©2026. 김은아영어연구소. All rights reserved.';

// ── 팔레트 (참고 교재 색 추출값: 리프 그린 계열) ──
const C = {
  ink: '#232323', sub: '#6b7280',
  teal: '#279A52', tealDark: '#1E7A40', mint: '#EAF6EC',
  green: '#279A52', greenHdr: '#279A52', zebra: '#F1F8EF',
  key: '#C5533F', keyBg: '#FBECEA',
  gram: '#6A57B0', gramBg: '#F0EDF9',
  plus: '#C0821F', plusBg: '#FBF3E0',
  goalBg: '#F7EED6', goalBar: '#D9A24A',
  tipBg: '#F2F3F4', tipBar: '#9aa0a6',
  line: '#e5e7eb', greenLine: '#CDE8CF',
};

function findChrome() {
  const list = [];
  try {
    list.push(...execSync('ls -d /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null')
      .toString().trim().split('\n').filter(Boolean));
  } catch (_) { /* noop */ }
  list.push('/opt/pw-browsers/chromium/chrome-linux/chrome');
  return list.find((p) => p && fs.existsSync(p)) || undefined;
}

const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

function fontFaces() {
  const defs = [
    ['NanumSquareRoundL.woff2', 300], ['NanumSquareRoundR.woff2', 400],
    ['NanumSquareRoundB.woff2', 700], ['NanumSquareRoundEB.woff2', 800],
  ];
  return defs.map(([file, weight]) => {
    const fp = path.join(FONTS_DIR, file);
    if (!fs.existsSync(fp)) return '';
    const b64 = fs.readFileSync(fp).toString('base64');
    return `@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:${weight};`
      + `src:url(data:font/woff2;base64,${b64}) format('woff2');}`;
  }).join('\n');
}

function secHead(num, title, hint, tone = 'teal', brk = false) {
  return `<div class="sechead${brk ? ' brk' : ''}">
    <span class="secnum ${tone}">${num}</span>
    <span class="sectitle">${esc(title)}</span>
    ${hint ? `<span class="sechint">${esc(hint)}</span>` : ''}
  </div>`;
}

function gramCard(pillText, tone, bodyHtml) {
  return `<div class="gcard ${tone}"><span class="pill ${tone}">${esc(pillText)}</span>
    <div class="gbody">${bodyHtml}</div></div>`;
}

function vocabTable(cat) {
  const seen = new Set(); const rows = [];
  [...cat.worked, ...cat.practice].forEach((s) => (s.vocab || []).forEach(([w, m]) => {
    const k = String(w).toLowerCase();
    if (!seen.has(k)) { seen.add(k); rows.push([w, m]); }
  }));
  const body = rows.map(([w, m], i) => `<tr class="${i % 2 ? 'z' : ''}">
    <td class="n">${i + 1}</td><td class="w">${esc(w)}</td><td>${esc(m)}</td></tr>`).join('');
  return `<table class="vtab"><thead><tr><th class="n">#</th><th class="w">단어</th><th>뜻</th></tr></thead><tbody>${body}</tbody></table>`;
}

function chunkLines(chunks, showKor) {
  const sep = ' <span class="sl">/</span> ';
  const en = chunks.map((c) => esc(c[0])).join(sep);
  const ko = chunks.map((c) => esc(c[1])).join(sep);
  return `<div class="chbox">
    <div class="chrow"><span class="chtag en">영어</span><span class="chtxt cen">${en}</span></div>
    <div class="chrow"><span class="chtag ko">한글</span>${showKor
      ? `<span class="chtxt ckor">${ko}</span>` : '<span class="chblank"></span>'}</div>
  </div>`;
}

function sentHead(s, idx) {
  return `<div class="senth"><span class="sbadge">${idx}</span>
    <span class="sen">${esc(s.en)}</span><span class="stag">[${esc(s.src)}]</span></div>`;
}
function skeletonCard(steps) {
  const body = (steps || []).map(([l, t]) => `<div class="sk"><b>${esc(l)}</b> ${esc(t)}</div>`).join('');
  return gramCard('뼈대·괄호 분석', 'gram', body);
}
function skeletonBlank() {
  return gramCard('뼈대·괄호 — 직접!', 'gram',
    '<div class="sk">뼈대(진짜 주어+동사):</div><div class="ul"></div>'
    + '<div class="sk">괄호(수식어):</div><div class="ul"></div>');
}
function writeCard() {
  return `<div class="gcard plus"><span class="pill plus">이 문장이 무슨 내용인 것 같아?</span>
    <div class="gbody"><div class="ul"></div><div class="ul"></div></div></div>`;
}
function catchCard(text) {
  return `<div class="callout catch"><span class="co-ic">✅ 이 정도는 캐치!</span> ${esc(text)}</div>`;
}
function tipCard(text) {
  return `<div class="callout tip"><span class="co-ic">✂ 끊어읽기 팁 — 어디서 끊을까?</span> ${esc(text)}</div>`;
}

// 문장별 어휘 리스트 — 끊어읽기 팁 바로 앞에 표시(그 문장에 나온 단어·뜻).
function vocabInline(vocab) {
  if (!vocab || !vocab.length) return '';
  const items = vocab.map(([w, m]) =>
    `<span class="vw">${esc(w)}</span> <span class="vm">${esc(m)}</span>`).join('<span class="vd">·</span>');
  return `<div class="vinline"><span class="vic">📘 어휘</span>${items}</div>`;
}

function workedBlock(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${vocabInline(s.vocab)}
    ${tipCard(makeTip(s.chunks))}
    ${chunkLines(s.chunks, true)}
    ${skeletonCard(s.steps)}
    ${catchCard(s.catch)}</div>`;
}
function practiceBlock(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${vocabInline(s.vocab)}
    ${tipCard(makeTip(s.chunks))}
    ${chunkLines(s.chunks, false)}
    ${skeletonBlank()}${writeCard()}</div>`;
}

function chapterHtml(cat, chIndex) {
  const intro = cat.intro || [];
  const goal = intro.length > 1 ? intro[0]
    : `'${cat.key}'의 신호를 찾아 덩어리로 끊어 읽는 법을 익혀보자!`;
  const introBody = (intro.length > 1 ? intro.slice(1) : intro).map((t) => `<p>${esc(t)}</p>`).join('');

  let h = '<section class="chapter">';
  h += `<div class="chhead"><span class="daypill">Chapter ${chIndex + 1}</span>
    <span class="tagpill">구문해석 · 기초</span></div>`;
  h += `<h1>${esc(cat.title)}</h1>`;
  h += '<div class="chsub">문법으로 뚫는 영어 해석 · 수능/평가원 기출 기반 · 기초 문법 학습용</div>';
  h += `<div class="goal"><span class="goal-ic">오늘의 목표</span> ${esc(goal)}</div>`;
  h += secHead(CIRCLED[0], '이 문법, 뭐야?', '겁먹지 말고 편하게 읽어보기', 'green');
  h += `<div class="plaincard">${introBody}</div>`;
  h += secHead(CIRCLED[1], '이렇게 찾아 (신호)', '이 표시만 보이면 바로 이거!', 'green');
  h += `<div class="signals">${(cat.signal || []).map((t) => `<div class="sig"><span class="chk">✓</span>${esc(t)}</div>`).join('')}</div>`;
  h += secHead(CIRCLED[2], '해석하는 법', '순서대로 따라만 오면 돼', 'gram');
  h += (cat.method || []).map(([l, t], i) => gramCard(l, i === (cat.method.length - 1) ? 'plus' : 'key', esc(t))).join('');
  h += secHead(CIRCLED[3], '단어 완전정복', '지문에 나온 단어 · 뜻', 'green');
  h += vocabTable(cat);
  h += secHead(CIRCLED[4], '같이 풀어보기', '쌤이랑 뼈대까지 같이 풀어보자', 'teal', true);
  h += cat.worked.map((s, i) => workedBlock(s, i + 1)).join('');
  h += secHead(CIRCLED[5], '혼자 풀어보기', '직접 끊고, 뼈대 찾고, 해석 써보기 · 정답은 맨 뒤', 'key', true);
  h += cat.practice.map((s, i) => practiceBlock(s, i + 1)).join('');
  h += '</section>';
  return h;
}

function answerHtml(cats) {
  let h = `<section class="chapter answers"><div class="chhead"><span class="daypill">정답 · 해설</span></div>
    <h1>정답 · 해설 — 혼자 풀어보기</h1>
    <div class="chsub">직접 푼 걸 여기서 맞춰보자. 끊어읽기 정답과 이 문장에서 붙잡을 핵심을 정리했어.</div>`;
  cats.forEach((cat, ci) => {
    if (!cat.practice.length) return;
    h += secHead(CIRCLED[ci] || (ci + 1), cat.key, null, 'teal');
    h += cat.practice.map((s, i) => `<div class="sblock">
      <div class="senth"><span class="sbadge">${i + 1}</span><span class="sen">${esc(s.en)}</span><span class="stag">[${esc(s.src)}]</span></div>
      ${chunkLines(s.chunks, true)}${catchCard(s.catch)}</div>`).join('');
  });
  h += '</section>';
  return h;
}

function coverHtml(meta = {}) {
  const subtitle = meta.subtitle || '전치사구 · 수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문';
  const source = meta.source || '2023학년도 수능 · 2024년 9월 평가원 모의평가(고3) 기출 기반';
  return `<section class="cover">
    <div class="cov-badges"><span class="daypill">문법으로 뚫는 영어 해석</span></div>
    <div class="ctitle">${esc(meta.title || '영어 해석 구문 워크북')}</div>
    <div class="csub">${esc(subtitle)}</div>
    <div class="csrc">${esc(source)}</div>
    <div class="usebox">
      <div class="useh">📌 쌤이 알려주는 사용법</div>
      <p>문법 용어가 낯설어도 괜찮아. 순서대로만 따라오면 돼.</p>
      <div class="usesteps">
        <div class="ustep"><b>①</b> 이 문법이 뭔지 읽고</div>
        <div class="ustep"><b>②</b> 찾는 신호를 익히고</div>
        <div class="ustep"><b>③</b> 해석하는 법을 보고</div>
        <div class="ustep"><b>④</b> 같이 풀고 → 혼자 풀기!</div>
      </div>
      <p class="fine">끊어읽기는 앞에서부터만, 뒤로 돌아가지 말고. 정답은 맨 뒤에서 확인해.</p>
    </div>
  </section>`;
}

function css() {
  return `
  * { box-sizing: border-box; }
  html,body { margin:0; }
  body { font-family:"NanumSquareRound","Noto Sans KR","Malgun Gothic",sans-serif;
    color:${C.ink}; font-size:11.5px; line-height:1.5; }
  .chapter { break-before: page; page-break-before: always; padding: 2px; }
  .cover { text-align:center; padding-top:90px; }
  .chhead { margin-bottom:6px; }
  .daypill { display:inline-block; background:${C.teal}; color:#fff; font-weight:700;
    font-size:11px; padding:3px 12px; border-radius:20px; }
  .tagpill { display:inline-block; border:1px solid ${C.line}; color:${C.sub};
    font-size:10px; padding:2px 10px; border-radius:20px; margin-left:6px; }
  h1 { font-size:20px; font-weight:800; margin:4px 0 3px; color:${C.ink}; }
  .chsub { color:${C.sub}; font-size:10.5px; margin-bottom:10px;
    border-bottom:2px solid ${C.teal}; padding-bottom:9px; }
  .goal { background:${C.goalBg}; border-left:5px solid ${C.goalBar}; border-radius:5px;
    padding:9px 13px; margin:11px 0; font-size:11px; }
  .goal-ic { display:inline-block; background:${C.goalBar}; color:#fff; font-weight:700;
    font-size:10px; padding:2px 9px; border-radius:12px; margin-right:7px; }
  .sechead { display:flex; align-items:center; margin:20px 0 9px; }
  .sechead.brk { break-before: page; page-break-before: always; margin-top: 2px; }
  .secnum { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px;
    border-radius:50%; color:#fff; font-size:12px; font-weight:800; margin-right:8px; }
  .secnum.teal{background:${C.teal};} .secnum.green{background:${C.green};} .secnum.gram{background:${C.gram};} .secnum.key{background:${C.key};}
  .sectitle { font-size:15px; font-weight:800; }
  .sechint { color:${C.sub}; font-size:10px; margin-left:9px; }
  .plaincard { background:#fafafa; border:1px solid ${C.line}; border-radius:6px; padding:10px 13px; }
  .plaincard p { margin:3px 0; }
  .signals { display:flex; flex-direction:column; gap:5px; }
  .sig { background:${C.mint}; border:1px solid ${C.greenLine}; border-radius:6px; padding:7px 11px; font-size:11px; }
  .chk { color:${C.teal}; font-weight:800; margin-right:7px; }
  .gcard { border:1px solid ${C.line}; border-left-width:5px; border-radius:6px;
    padding:9px 12px 10px; margin:8px 0; break-inside:avoid; }
  .gcard.key { border-left-color:${C.key}; background:${C.keyBg}; }
  .gcard.gram { border-left-color:${C.gram}; background:${C.gramBg}; }
  .gcard.plus { border-left-color:${C.plus}; background:${C.plusBg}; }
  .pill { display:inline-block; color:#fff; font-weight:700; font-size:10px;
    padding:2px 10px; border-radius:12px; margin-bottom:6px; }
  .pill.key{background:${C.key};} .pill.gram{background:${C.gram};} .pill.plus{background:${C.plus};}
  .gbody { font-size:11px; }
  .sk { margin:3px 0; }
  .ul { border-bottom:1px solid #b9b9b9; height:15px; margin:5px 0 9px; }
  table { border-collapse:collapse; width:100%; font-size:10.8px; }
  .vtab { margin:4px 0 6px; border:1px solid ${C.line}; table-layout:fixed; }
  .vtab th { background:${C.greenHdr}; color:#fff; text-align:left; padding:6px 9px; font-weight:700; }
  .vtab td { padding:5px 9px; border-top:1px solid ${C.line}; }
  .vtab td.n, .vtab th.n { width:32px; text-align:center; color:${C.teal}; font-weight:700; }
  .vtab td.w, .vtab th.w { width:140px; font-weight:700; }
  .vtab tr.z td { background:${C.zebra}; }
  .sblock { break-inside:avoid; margin:12px 0 16px; }
  .senth { display:flex; align-items:flex-start; margin:6px 0 5px; }
  .sbadge { flex:none; display:inline-flex; align-items:center; justify-content:center;
    width:20px; height:20px; border-radius:50%; background:${C.teal}; color:#fff;
    font-size:11px; font-weight:800; margin-right:8px; margin-top:1px; }
  .sen { font-weight:800; font-size:13px; }
  .stag { color:${C.sub}; font-size:10px; font-style:italic; margin-left:6px; align-self:center; }
  .vinline { background:#fff; border:1px solid ${C.greenLine}; border-left:4px solid ${C.green};
    border-radius:6px; padding:7px 11px; margin:4px 0 7px; font-size:10.6px; }
  .vinline .vic { font-weight:800; color:${C.tealDark}; margin-right:9px; }
  .vw { font-weight:700; }
  .vm { color:#555; }
  .vd { color:#c3ccc6; margin:0 8px; }
  .chbox { border:1px solid ${C.line}; border-left:4px solid ${C.green}; border-radius:6px;
    padding:8px 12px; margin:4px 0 9px; background:${C.zebra}; }
  .chrow { display:flex; align-items:baseline; margin:4px 0; }
  .chtag { flex:none; font-size:9px; font-weight:800; color:#fff; border-radius:9px;
    padding:1px 8px; margin-right:9px; line-height:1.5; }
  .chtag.en { background:${C.green}; }
  .chtag.ko { background:#8a8f98; }
  .chtxt { flex:1; }
  .chtxt.cen { font-weight:700; font-size:13px; }
  .chtxt.ckor { font-size:12px; color:#333; }
  .sl { color:${C.green}; font-weight:800; padding:0 3px; }
  .chblank { flex:1; border-bottom:1px dashed #c3ccc6; height:15px; }
  .callout { border-radius:6px; padding:8px 12px; margin:7px 0; font-size:10.8px; break-inside:avoid; }
  .callout.catch { background:${C.mint}; border:1px solid ${C.greenLine}; }
  .callout.tip { background:${C.tipBg}; border-left:4px solid ${C.tipBar}; color:#555; }
  .co-ic { font-weight:800; margin-right:6px; }
  .callout.catch .co-ic { color:${C.tealDark}; }
  .cov-badges { margin-bottom:20px; }
  .ctitle { font-size:34px; font-weight:800; color:${C.ink}; margin-bottom:14px; }
  .csub { color:${C.teal}; font-weight:700; font-size:15px; margin-bottom:12px; }
  .csrc { color:${C.sub}; font-size:11.5px; font-style:italic; margin-bottom:40px; }
  .usebox { text-align:left; background:${C.mint}; border:1px solid ${C.greenLine}; border-radius:10px;
    padding:16px 20px; margin:0 40px; }
  .useh { color:${C.tealDark}; font-weight:800; font-size:14px; margin-bottom:8px; }
  .usesteps { display:flex; flex-wrap:wrap; gap:6px 14px; margin:8px 0; }
  .ustep { font-size:11px; } .ustep b { color:${C.teal}; }
  .fine { color:${C.sub}; font-size:10.5px; margin-top:6px; }
  `;
}

// 전체 HTML 문서. rawCategories 는 splitWorked 전(worked 2개 초과 허용) 데이터.
function buildHtml(rawCategories, meta = {}) {
  const cats = splitWorked(rawCategories);
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${fontFaces()}\n${css()}</style></head>`
    + `<body>${coverHtml(meta)}${cats.map((c, i) => chapterHtml(c, i)).join('')}${answerHtml(cats)}</body></html>`;
}

// HTML → PDF (Chromium 인쇄). playwright 가 없으면 명확한 에러.
async function renderPdf(html, pdfPath) {
  // eslint-disable-next-line global-require
  const { chromium } = require('playwright');
  const browser = await chromium.launch({ executablePath: findChrome() });
  try {
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'load' });
    await page.pdf({
      path: pdfPath, format: 'A4', printBackground: true,
      margin: { top: '13mm', bottom: '15mm', left: '13mm', right: '13mm' },
      displayHeaderFooter: true,
      headerTemplate: '<div></div>',
      footerTemplate: `<div style="width:100%; font-size:8px; color:#9aa0a6;
        padding:0 13mm; display:flex; justify-content:space-between;">
        <span>${FOOTER_BRAND}</span>
        <span>페이지 <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
    });
  } finally {
    await browser.close();
  }
}

module.exports = { buildHtml, renderPdf, findChrome };

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
  trapBg: '#FEF3E2', trapLine: '#F5D9AE', trapBar: '#E08A1E',
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

// @font-face 를 만든다. base64 는 코드에 박힌 src/fonts-embedded.js 에서 가져오므로
// fonts/ 폴더 유무·실행 경로·환경과 무관하게 항상 NanumSquareRound 가 임베드된다.
// (혹시 임베드 모듈이 비어 있으면 fonts/ 의 woff2 를 읽어 보는 안전장치만 둔다.)
function fontFaces() {
  const face = (weight, b64) =>
    `@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:${weight};`
    + `src:url(data:font/woff2;base64,${b64}) format('woff2');}`;

  let embedded = [];
  try { embedded = require('./fonts-embedded').FONTS || []; } catch (_) { /* 아래 폴백 */ }
  if (embedded.length) return embedded.map((f) => face(f.weight, f.b64)).join('\n');

  // 폴백: 임베드 모듈이 없을 때만 파일에서 읽음(개발 중 폰트 교체 직후 등).
  const defs = [
    ['NanumSquareRoundL.woff2', 300], ['NanumSquareRoundR.woff2', 400],
    ['NanumSquareRoundB.woff2', 700], ['NanumSquareRoundEB.woff2', 800],
  ];
  return defs.map(([file, weight]) => {
    const fp = path.join(FONTS_DIR, file);
    if (!fs.existsSync(fp)) return '';
    return face(weight, fs.readFileSync(fp).toString('base64'));
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
// ✏️ 직접 끊어 읽고 해석 쓰는 칸 (혼자 풀어보기 문제 쪽 — 초록 카드 대신)
function answerWriteCard() {
  return `<div class="writecard">
    <div class="wc-h">✏️ 직접 ' / ' 로 끊고, 그 아래에 뜻을 적어봐</div>
    <div class="wl"></div><div class="wl"></div></div>`;
}
// 해설 쪽 끊어읽기 — 초록 '문제' 카드가 아니라 담백한 해설 스타일(영어/한글).
function chunkExplain(chunks) {
  const rows = chunks.map((c) =>
    `<div class="exrow"><span class="exen">${esc(c[0])}</span><span class="exko">${esc(c[1])}</span></div>`).join('');
  return `<div class="excard"><div class="ex-h">끊어읽기 해석 (모범답안)</div>${rows}</div>`;
}
function catchCard(text) {
  return `<div class="callout catch"><span class="co-ic">✅ 이 정도는 캐치!</span> ${esc(text)}</div>`;
}
function tipCard(text) {
  return `<div class="callout tip"><span class="co-ic">✂ 끊어읽기 팁 — 어디서 끊을까?</span> ${esc(text)}</div>`;
}
// ⚠️ 함정 주의 — 이 문장에서 자주 틀리는 해석 포인트 경고.
function trapCard(text) {
  if (!text) return '';
  return `<div class="callout trap"><span class="co-ic">⚠️ 이거 조심!</span> ${esc(text)}</div>`;
}
// 문장별 함정 문구 선택: 문장에 trap 이 있으면 그걸, 없으면 챕터 traps 를 순서대로 순환.
function pickTrap(cat, s, i) {
  if (s && s.trap) return s.trap;
  const arr = cat && cat.traps;
  return Array.isArray(arr) && arr.length ? arr[i % arr.length] : '';
}

// 문장별 어휘 리스트 — 끊어읽기 팁 바로 앞에 표시(그 문장에 나온 단어·뜻).
function vocabInline(vocab) {
  if (!vocab || !vocab.length) return '';
  const items = vocab.map(([w, m]) =>
    `<span class="vw">${esc(w)}</span> <span class="vm">${esc(m)}</span>`).join('<span class="vd">·</span>');
  return `<div class="vinline"><span class="vic">📘 어휘</span>${items}</div>`;
}

function workedBlock(s, idx, trap) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${vocabInline(s.vocab)}
    ${tipCard(makeTip(s.chunks))}
    ${chunkLines(s.chunks, true)}
    ${trapCard(trap)}
    ${catchCard(s.catch)}</div>`;
}
// 혼자 풀어보기 — 문제 쪽(왼쪽 페이지): 영어 + 어휘 + 팁 + 함정 + 직접 쓰는 칸 (초록 카드 없음)
function practiceProblem(s, idx, trap) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${vocabInline(s.vocab)}
    ${tipCard(makeTip(s.chunks))}
    ${trapCard(trap)}
    ${answerWriteCard()}</div>`;
}
// 혼자 풀어보기 — 해설 쪽(오른쪽 페이지): 영어 + 모범 끊어읽기 + 캐치
function practiceExplain(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${chunkExplain(s.chunks)}
    ${catchCard(s.catch)}</div>`;
}

// 혼자 풀어보기를 '왼쪽=문제 / 오른쪽=해설' 펼침면으로 묶는다.
// 한 펼침에 SPREAD_N 문제씩 — 양쪽이 각각 한 페이지에 넘치지 않고 들어가도록.
const SPREAD_N = 3;
function practiceSpreads(cat) {
  const items = cat.practice || [];
  let h = '';
  for (let g = 0; g < items.length; g += SPREAD_N) {
    const group = items.slice(g, g + SPREAD_N);
    const from = g + 1; const to = g + group.length;
    // 왼쪽(짝수/좌측 페이지): 문제
    h += `<section class="probpage"><div class="pp-head"><span class="pp-badge">혼자 풀어보기 · 문제</span>
      <span class="pp-range">${cat.key} ${from}–${to}번</span>
      <span class="pp-hint">직접 끊어 읽고 해석을 써봐 · 오른쪽 페이지에서 맞춰보기</span></div>`;
    group.forEach((s, k) => { h += practiceProblem(s, g + k + 1, pickTrap(cat, s, g + k)); });
    h += '</section>';
    // 오른쪽(홀수/우측 페이지): 해설
    h += `<section class="solpage"><div class="sp-head"><span class="sp-badge">해설</span>
      <span class="pp-range">${cat.key} ${from}–${to}번</span>
      <span class="pp-hint">왼쪽 문제의 모범 끊어읽기와 핵심</span></div>`;
    group.forEach((s, k) => { h += practiceExplain(s, g + k + 1); });
    h += '</section>';
  }
  return h;
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
  h += secHead(CIRCLED[4], '같이 풀어보기', '쌤이랑 함정까지 같이 짚어보자', 'teal', true);
  h += cat.worked.map((s, i) => workedBlock(s, i + 1, pickTrap(cat, s, i))).join('');
  h += '</section>';
  // 혼자 풀어보기는 챕터 섹션 밖에서 '왼쪽 문제 / 오른쪽 해설' 펼침면으로.
  h += practiceSpreads(cat);
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
      <p class="fine">끊어읽기는 앞에서부터만, 뒤로 돌아가지 말고. 혼자 풀어보기는 <b>왼쪽에서 직접 풀고, 오른쪽 페이지 해설</b>로 바로 맞춰봐.</p>
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
  /* 혼자 풀어보기 — 문제 3개 페이지 / 해설 3개 페이지를 그냥 번갈아 출력.
     (좌/우 짝·홀 강제는 하지 않음 — 빈 페이지가 끼지 않도록 단순 페이지 나눔) */
  .probpage { break-before: page; page-break-before: always; padding:2px; }
  .solpage { break-before: page; page-break-before: always; padding:2px; }
  .pp-head, .sp-head { display:flex; align-items:center; flex-wrap:wrap; gap:5px 10px;
    margin-bottom:12px; padding-bottom:9px; border-bottom:2px solid ${C.teal}; }
  .pp-badge { background:${C.key}; color:#fff; font-weight:800; font-size:11px; padding:3px 12px; border-radius:20px; }
  .sp-badge { background:${C.tealDark}; color:#fff; font-weight:800; font-size:11px; padding:3px 12px; border-radius:20px; }
  .pp-range { font-weight:800; font-size:15px; }
  .pp-hint { color:${C.sub}; font-size:10px; }
  /* 직접 쓰는 칸 */
  .writecard { border:1px dashed #bcc6bf; border-radius:6px; padding:9px 12px 12px; margin:4px 0 10px; background:#fcfdfc; }
  .wc-h { font-size:10.3px; color:${C.sub}; font-weight:700; margin-bottom:6px; }
  .wl { border-bottom:1px solid #cacaca; height:18px; margin:10px 0; }
  /* 해설 끊어읽기 (담백한 스타일 — 초록 '문제' 카드 아님) */
  .excard { border:1px solid ${C.greenLine}; border-left:4px solid ${C.tealDark}; border-radius:6px;
    padding:8px 12px; margin:4px 0 8px; background:#fbfdfb; }
  .ex-h { font-size:9.5px; font-weight:800; color:${C.tealDark}; margin-bottom:6px; text-transform:none; }
  .exrow { display:flex; gap:10px; padding:3px 0; border-top:1px dotted #e3ece4; }
  .exrow:first-of-type { border-top:0; }
  .exen { flex:1; font-weight:700; font-size:11.3px; }
  .exko { flex:1; font-size:11px; color:#333; }
  .callout { border-radius:6px; padding:8px 12px; margin:7px 0; font-size:10.8px; break-inside:avoid; }
  .callout.catch { background:${C.mint}; border:1px solid ${C.greenLine}; }
  .callout.tip { background:${C.tipBg}; border-left:4px solid ${C.tipBar}; color:#555; }
  .callout.trap { background:${C.trapBg}; border:1px solid ${C.trapLine}; border-left:4px solid ${C.trapBar}; color:#7a4a12; }
  .co-ic { font-weight:800; margin-right:6px; }
  .callout.catch .co-ic { color:${C.tealDark}; }
  .callout.trap .co-ic { color:${C.trapBar}; }
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
  /* 지문 모드 */
  .ptag { flex:none; align-self:center; margin-left:8px; background:${C.gramBg}; color:${C.gram};
    border:1px solid #ddd4f2; font-size:9px; font-weight:800; padding:1px 8px; border-radius:10px; }
  .fulltext { background:#fafafa; border:1px solid ${C.line}; border-radius:8px; padding:12px 15px;
    margin:6px 0 4px; font-size:12px; line-height:1.75; }
  .fulltext .fn { color:${C.teal}; font-weight:800; margin-right:3px; }
  .pcatch { background:${C.mint}; border:1px solid ${C.greenLine}; border-left:5px solid ${C.teal};
    border-radius:8px; padding:12px 15px; margin:14px 0 4px; font-size:12px; break-inside:avoid; }
  .pcatch-h { display:block; color:${C.tealDark}; font-weight:800; font-size:13px; margin-bottom:5px; }
  .catchwrite { background:${C.mint}; border:1px solid ${C.greenLine}; border-radius:6px;
    padding:8px 12px 10px; margin:7px 0; break-inside:avoid; }
  .cw-h { font-size:11px; font-weight:800; color:${C.tealDark}; margin-bottom:4px; }
  .cw-hint { font-weight:600; color:${C.sub}; font-size:9.5px; margin-left:4px; }
  `;
}

// ── 지문(passage) 모드 렌더 — 목차=지문, 문장 원문 순서, 문법은 point 태그 ──
function pointTag(point) {
  return point ? `<span class="ptag">${esc(point)}</span>` : '';
}
// 지문 통째로 먼저 읽기(영어 원문 나열)
function fullTextBlock(sentences) {
  const body = sentences.map((s, i) =>
    `<span class="fn">${i + 1}</span>${esc(s.en)} `).join('');
  return `<div class="fulltext">${body}</div>`;
}
// 해석 직접 쓰는 칸 (정답은 지문 끝 답지)
function interpretWriteCard() {
  return `<div class="writecard">
    <div class="wc-h">✏️ 해석 — 직접 우리말로 써봐 (정답은 지문 끝 '답지'에서 확인)</div>
    <div class="wl"></div><div class="wl"></div></div>`;
}
// 캐치 직접 쓰는 칸 + '잘하는 법' 가이드. 학생이 매 문장 한 줄로 줄여보는 연습.
function catchWriteCard() {
  return `<div class="catchwrite">
    <div class="cw-h">✅ 이 정도는 캐치! <span class="cw-hint">핵심만 한 줄 — 누가/무엇이 → 어쨌다? (곁가지·수식은 버려)</span></div>
    <div class="wl"></div></div>`;
}
// 문장 하나(문제 쪽): 영어+포인트태그 → 어휘 → 팁 → 이거 조심 → 해석(쓰기) → 캐치(쓰기)
function passageSentence(s, idx) {
  return `<div class="sblock">
    <div class="senth"><span class="sbadge">${idx}</span><span class="sen">${esc(s.en)}</span>${pointTag(s.point)}</div>
    ${vocabInline(s.vocab)}
    ${tipCard(makeTip(s.chunks))}
    ${trapCard(s.trap)}
    ${interpretWriteCard()}
    ${catchWriteCard()}</div>`;
}
// 지문 끝 답지: 문장별 모범 해석(끊어읽기) + 모범 캐치
function passageAnswerKey(p) {
  let h = secHead(CIRCLED[2], '답지 — 해석 · 캐치', '위에서 직접 푼 걸 여기서 맞춰봐', 'key', true);
  h += (p.sentences || []).map((s, i) => `<div class="sblock">
    <div class="senth"><span class="sbadge">${i + 1}</span><span class="sen">${esc(s.en)}</span>${pointTag(s.point)}</div>
    ${chunkExplain(s.chunks)}
    ${s.catch ? catchCard(s.catch) : ''}</div>`).join('');
  return h;
}
function passageHtml(p, idx) {
  let h = '<section class="chapter">';
  h += `<div class="chhead"><span class="daypill">지문 ${idx + 1}</span>
    <span class="tagpill">${esc(p.source || '구문해석')}</span></div>`;
  h += `<h1>${esc(p.title || `지문 ${idx + 1}`)}</h1>`;
  h += '<div class="chsub">문법으로 뚫는 영어 해석 · 지문 한 편을 온전히 이해하기</div>';
  if (p.topic) h += `<div class="goal"><span class="goal-ic">이 지문, 뭐야?</span> ${esc(p.topic)}</div>`;
  h += secHead(CIRCLED[0], '지문 통째로 읽기', '먼저 전체 흐름을 쭉 훑어봐', 'green');
  h += fullTextBlock(p.sentences);
  h += secHead(CIRCLED[1], '한 문장씩 직접 풀기', '어휘·팁·이거조심 보고 → 해석·캐치는 직접', 'teal');
  h += (p.sentences || []).map((s, i) => passageSentence(s, i + 1)).join('');
  h += passageAnswerKey(p);
  if (p.catch) {
    h += `<div class="pcatch"><span class="pcatch-h">✅ 이 지문, 이 정도는 캐치! (전체 요지)</span>${esc(p.catch)}</div>`;
  }
  h += '</section>';
  return h;
}

// 지문 모드 전체 HTML. passages 는 normalizePassages 결과.
function buildHtmlPassages(passages, meta = {}) {
  const cover = coverHtml({
    title: meta.title || '지문 구문독해 워크북',
    subtitle: meta.subtitle || '지문 한 편을 온전히 — 끊어읽기로 구문까지',
    source: meta.source || '업로드한 지문 기반 · 자동 생성',
  });
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${fontFaces()}\n${css()}</style></head>`
    + `<body>${cover}${passages.map((p, i) => passageHtml(p, i)).join('')}</body></html>`;
}

// 전체 HTML 문서. rawCategories 는 splitWorked 전(worked 2개 초과 허용) 데이터.
function buildHtml(rawCategories, meta = {}) {
  const cats = splitWorked(rawCategories);
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${fontFaces()}\n${css()}</style></head>`
    + `<body>${coverHtml(meta)}${cats.map((c, i) => chapterHtml(c, i)).join('')}</body></html>`;
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

module.exports = { buildHtml, buildHtmlPassages, renderPdf, findChrome };

#!/usr/bin/env node
// preview_pdf.js — 디자인 적용 PDF 생성기 (Chromium 인쇄)
//
// 참고 교재(김은아영어연구소 스타일)의 디자인 언어를 반영한다:
//   · 청록/그린 강조색, 라운드 배지(일차·태그)
//   · 번호 원형 배지 + 제목 + 회색 힌트로 섹션 헤더
//   · 문법 설명은 컬러 필(핵심/문법/한 단계 위) + 왼쪽 컬러 보더 카드
//   · 끊어읽기 직독직해는 2단(영어 끊어읽기 | 우리말) 청록 헤더 표
//   · 단어 완전정복은 그린 헤더 + 얼룩(zebra) 표
//   · 하단 저작권 + 페이지 번호
//
// 정식 편집본은 build_v4.js 의 docx. 이 스크립트는 같은 data.js/splitWorked/
// makeTip 을 써서 HTML→Chromium 으로 "배포용 예쁜 PDF" 를 만든다.
// ⚠️ NanumSquareRound 가 이 환경엔 없어 대체 폰트로 보인다(선생님 PC docx 와 동일 제약).
//
// 사용법: node preview_pdf.js  →  output/output_v4_preview.pdf

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');

const categories = require('./data');
const { splitWorked } = require('./src/document');
const { makeTip } = require('./src/tip');

const FOOTER_BRAND = '©2026. 김은아영어연구소. All rights reserved.';

// ── 팔레트 ────────────────────────────────────────────
const C = {
  ink: '#232323', sub: '#6b7280',
  teal: '#2E9B87', tealDark: '#217a6b', mint: '#E9F7F1',
  green: '#35A47E', greenHdr: '#2E9B87', zebra: '#F3FAF7',
  key: '#D9663A', keyBg: '#FBEDE7',        // 오늘의 핵심(주황)
  gram: '#6B4FA0', gramBg: '#F1EEF9',       // 문법(보라)
  plus: '#B0824F', plusBg: '#FBF3E4',       // 한 단계 위(골드)
  goalBg: '#FFF6E4', goalBar: '#E0A73C',
  tipBg: '#F2F3F4', tipBar: '#9aa0a6',
  line: '#e5e7eb',
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

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

// NanumSquareRound 를 base64 woff2 로 임베드해서 PDF 가 항상 이 서체로 렌더되게 함.
// (fonts/ 의 woff2 는 OFL-1.1, 임베드 허용) — 폰트가 없으면 대체 폰트로 폴백.
function fontFaces() {
  const dir = path.join(__dirname, 'fonts');
  const defs = [
    ['NanumSquareRoundL.woff2', 300],
    ['NanumSquareRoundR.woff2', 400],
    ['NanumSquareRoundB.woff2', 700],
    ['NanumSquareRoundEB.woff2', 800],
  ];
  return defs.map(([file, weight]) => {
    const fp = path.join(dir, file);
    if (!fs.existsSync(fp)) return '';
    const b64 = fs.readFileSync(fp).toString('base64');
    return `@font-face{font-family:'NanumSquareRound';font-style:normal;font-weight:${weight};`
      + `src:url(data:font/woff2;base64,${b64}) format('woff2');}`;
  }).join('\n');
}

// ── 조각 빌더 ─────────────────────────────────────────
function secHead(num, title, hint, tone = 'teal') {
  return `<div class="sechead">
    <span class="secnum ${tone}">${num}</span>
    <span class="sectitle">${esc(title)}</span>
    ${hint ? `<span class="sechint">${esc(hint)}</span>` : ''}
  </div>`;
}

// 문법 카드(핵심/문법/한 단계 위)
function gramCard(pillText, tone, bodyHtml) {
  return `<div class="gcard ${tone}">
    <span class="pill ${tone}">${esc(pillText)}</span>
    <div class="gbody">${bodyHtml}</div>
  </div>`;
}

// 단어 완전정복: 챕터 어휘 합쳐 dedup
function vocabTable(cat) {
  const seen = new Set(); const rows = [];
  [...cat.worked, ...cat.practice].forEach((s) => (s.vocab || []).forEach(([w, m]) => {
    const k = w.toLowerCase();
    if (!seen.has(k)) { seen.add(k); rows.push([w, m]); }
  }));
  const body = rows.map(([w, m], i) => `<tr class="${i % 2 ? 'z' : ''}">
    <td class="n">${i + 1}</td><td class="w">${esc(w)}</td><td>${esc(m)}</td></tr>`).join('');
  return `<table class="vtab"><thead><tr><th class="n">#</th><th>단어</th><th>뜻</th></tr></thead><tbody>${body}</tbody></table>`;
}

// 끊어읽기 직독직해 2단 표 (showKor=false 면 우리말 칸은 빈칸)
function chunkTable(chunks, showKor) {
  const rows = chunks.map(([en, kor], i) => `<tr class="${i % 2 ? 'z' : ''}">
    <td class="cn">${i + 1}</td>
    <td class="cen">${esc(en)}</td>
    <td class="ckor">${showKor ? esc(kor) : '<span class="blankcell"></span>'}</td></tr>`).join('');
  return `<table class="ctab"><thead><tr>
    <th class="cn">#</th><th>영어 (끊어읽기)</th><th>우리말 (직독직해)</th>
  </tr></thead><tbody>${rows}</tbody></table>`;
}

function sentHead(s, idx) {
  return `<div class="senth"><span class="sbadge">${idx}</span>
    <span class="sen">${esc(s.en)}</span><span class="stag">[${esc(s.src)}]</span></div>`;
}

function skeletonCard(steps) {
  const body = steps.map(([l, t]) => `<div class="sk"><b>${esc(l)}</b> ${esc(t)}</div>`).join('');
  return gramCard('뼈대·괄호 분석', 'gram', body);
}
function skeletonBlank() {
  return gramCard('뼈대·괄호 — 직접!', 'gram',
    '<div class="sk">뼈대(진짜 주어+동사):</div><div class="ul"></div>'
    + '<div class="sk">괄호(수식어):</div><div class="ul"></div>');
}
function writeCard() {
  return `<div class="gcard plus"><span class="pill plus">내 해석 써보기</span>
    <div class="gbody"><div class="ul"></div><div class="ul"></div></div></div>`;
}
function catchCard(text) {
  return `<div class="callout catch"><span class="co-ic">✅ 이 정도는 캐치!</span> ${esc(text)}</div>`;
}
function tipCard(text) {
  return `<div class="callout tip"><span class="co-ic">💡 왜 여기서 끊었을까?</span> ${esc(text)}</div>`;
}

function workedBlock(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${chunkTable(s.chunks, true)}
    ${skeletonCard(s.steps)}
    ${catchCard(s.catch)}${tipCard(makeTip(s.chunks))}</div>`;
}
function practiceBlock(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${chunkTable(s.chunks, false)}
    ${skeletonBlank()}${writeCard()}
    ${catchCard(s.catch)}${tipCard(makeTip(s.chunks))}</div>`;
}

function chapterHtml(cat, chIndex) {
  const goal = cat.intro.length > 1 ? cat.intro[0]
    : `'${cat.key}'의 신호를 찾아 덩어리로 끊어 읽는 법을 익혀보자!`;
  const introBody = (cat.intro.length > 1 ? cat.intro.slice(1) : cat.intro)
    .map((t) => `<p>${esc(t)}</p>`).join('');

  let h = `<section class="chapter">`;
  h += `<div class="chhead">
    <span class="daypill">Chapter ${chIndex + 1}</span>
    <span class="tagpill">구문해석 · 기초</span>
  </div>`;
  h += `<h1>${esc(cat.title)}</h1>`;
  h += `<div class="chsub">문법으로 뚫는 영어 해석 · 수능/평가원 기출 기반 · 기초 문법 학습용</div>`;
  h += `<div class="goal"><span class="goal-ic">오늘의 목표</span> ${esc(goal)}</div>`;

  h += secHead(CIRCLED[0], '이 문법, 뭐야?', '겁먹지 말고 편하게 읽어보기', 'green');
  h += `<div class="plaincard">${introBody}</div>`;

  h += secHead(CIRCLED[1], '이렇게 찾아 (신호)', '이 표시만 보이면 바로 이거!', 'green');
  h += `<div class="signals">${cat.signal.map((t) => `<div class="sig"><span class="chk">✓</span>${esc(t)}</div>`).join('')}</div>`;

  h += secHead(CIRCLED[2], '해석하는 법', '순서대로 따라만 오면 돼', 'gram');
  h += cat.method.map(([l, t], i) => gramCard(l, i === cat.method.length - 1 ? 'plus' : 'key', esc(t))).join('');

  h += secHead(CIRCLED[3], '단어 완전정복', '지문에 나온 단어 · 뜻', 'green');
  h += vocabTable(cat);

  h += secHead(CIRCLED[4], '같이 풀어보기', '쌤이랑 뼈대까지 같이 풀어보자', 'teal');
  h += cat.worked.map((s, i) => workedBlock(s, i + 1)).join('');

  h += secHead(CIRCLED[5], '혼자 풀어보기', '직접 끊고, 뼈대 찾고, 해석 써보기 · 정답은 맨 뒤', 'key');
  h += cat.practice.map((s, i) => practiceBlock(s, i + 1)).join('');

  h += `</section>`;
  return h;
}

function answerHtml(cats) {
  let h = `<section class="chapter answers"><div class="chhead"><span class="daypill">Answers</span></div>
    <h1>정답 — 혼자 풀어보기 (참고용 해석)</h1>
    <div class="chsub">끊어 읽은 덩어리를 순서대로 이어 읽으면 이런 뜻이야. 네 해석과 맞춰보자!</div>`;
  cats.forEach((cat, ci) => {
    if (!cat.practice.length) return;
    h += secHead(CIRCLED[ci] || (ci + 1), cat.key, null, 'teal');
    h += '<div class="anslist">' + cat.practice.map((s, i) =>
      `<div class="ans"><span class="ansn">${i + 1}</span>
        <span class="anskor">${esc(s.chunks.map((c) => c[1]).join(' '))}</span></div>`).join('') + '</div>';
  });
  h += `</section>`;
  return h;
}

function coverHtml() {
  return `<section class="cover">
    <div class="cov-badges"><span class="daypill">문법으로 뚫는 영어 해석</span></div>
    <div class="ctitle">영어 해석 구문 워크북</div>
    <div class="csub">전치사구 · 수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문</div>
    <div class="csrc">2023학년도 수능 · 2024년 9월 평가원 모의평가(고3) 기출 기반</div>
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
  /* 목차(챕터)마다 반드시 새 페이지에서 시작 */
  .chapter { break-before: page; page-break-before: always; padding: 2px; }
  .cover { text-align:center; padding-top:90px; }

  /* 챕터 헤더 */
  .chhead { margin-bottom:6px; }
  .daypill { display:inline-block; background:${C.teal}; color:#fff; font-weight:700;
    font-size:11px; padding:3px 12px; border-radius:20px; }
  .tagpill { display:inline-block; border:1px solid ${C.line}; color:${C.sub};
    font-size:10px; padding:2px 10px; border-radius:20px; margin-left:6px; }
  h1 { font-size:20px; font-weight:800; margin:4px 0 3px; color:${C.ink}; }
  .chsub { color:${C.sub}; font-size:10.5px; margin-bottom:10px;
    border-bottom:2px solid ${C.teal}; padding-bottom:9px; }

  /* 오늘의 목표 */
  .goal { background:${C.goalBg}; border-left:5px solid ${C.goalBar}; border-radius:5px;
    padding:9px 13px; margin:11px 0; font-size:11px; }
  .goal-ic { display:inline-block; background:${C.goalBar}; color:#fff; font-weight:700;
    font-size:10px; padding:2px 9px; border-radius:12px; margin-right:7px; }

  /* 섹션 헤더 */
  .sechead { display:flex; align-items:center; margin:20px 0 9px; }
  .secnum { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px;
    border-radius:50%; color:#fff; font-size:12px; font-weight:800; margin-right:8px; }
  .secnum.teal{background:${C.teal};} .secnum.green{background:${C.green};} .secnum.gram{background:${C.gram};} .secnum.key{background:${C.key};}
  .sectitle { font-size:15px; font-weight:800; }
  .sechint { color:${C.sub}; font-size:10px; margin-left:9px; }

  .plaincard { background:#fafafa; border:1px solid ${C.line}; border-radius:6px; padding:10px 13px; }
  .plaincard p { margin:3px 0; }

  /* 신호 체크리스트 */
  .signals { display:flex; flex-direction:column; gap:5px; }
  .sig { background:${C.mint}; border:1px solid #cfe9e1; border-radius:6px; padding:7px 11px; font-size:11px; }
  .chk { color:${C.teal}; font-weight:800; margin-right:7px; }

  /* 문법 카드 (핵심/문법/한 단계 위) */
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

  /* 단어 표 */
  table { border-collapse:collapse; width:100%; font-size:10.8px; }
  .vtab { margin:4px 0 6px; border:1px solid ${C.line}; }
  .vtab th { background:${C.greenHdr}; color:#fff; text-align:left; padding:6px 9px; font-weight:700; }
  .vtab td { padding:5px 9px; border-top:1px solid ${C.line}; }
  .vtab td.n, .vtab th.n { width:34px; text-align:center; color:${C.teal}; font-weight:700; }
  .vtab td.w { font-weight:700; }
  .vtab tr.z td { background:${C.zebra}; }

  /* 끊어읽기 직독직해 표 */
  .sblock { break-inside:avoid; margin:12px 0 16px; }
  .senth { display:flex; align-items:flex-start; margin:6px 0 5px; }
  .sbadge { flex:none; display:inline-flex; align-items:center; justify-content:center;
    width:20px; height:20px; border-radius:50%; background:${C.teal}; color:#fff;
    font-size:11px; font-weight:800; margin-right:8px; margin-top:1px; }
  .sen { font-weight:800; font-size:13px; }
  .stag { color:${C.sub}; font-size:10px; font-style:italic; margin-left:6px; align-self:center; }
  .ctab { border:1px solid ${C.line}; margin:3px 0 8px; }
  .ctab th { background:${C.greenHdr}; color:#fff; text-align:left; padding:5px 9px; font-weight:700; }
  .ctab td { padding:5px 9px; border-top:1px solid ${C.line}; vertical-align:top; }
  .ctab td.cn, .ctab th.cn { width:26px; text-align:center; color:${C.teal}; font-weight:700; }
  .ctab td.cen { width:52%; font-weight:700; }
  .ctab td.ckor { color:#333; }
  .ctab tr.z td { background:${C.zebra}; }
  .blankcell { display:block; min-height:13px; border-bottom:1px dashed #cbd5d1; }

  /* 콜아웃 */
  .callout { border-radius:6px; padding:8px 12px; margin:7px 0; font-size:10.8px; break-inside:avoid; }
  .callout.catch { background:${C.mint}; border:1px solid #bfe6da; }
  .callout.tip { background:${C.tipBg}; border-left:4px solid ${C.tipBar}; color:#555; }
  .co-ic { font-weight:800; margin-right:6px; }
  .callout.catch .co-ic { color:${C.tealDark}; }

  /* 정답 */
  .anslist { display:flex; flex-direction:column; gap:4px; }
  .ans { display:flex; align-items:flex-start; }
  .ansn { flex:none; width:20px; height:20px; border-radius:50%; background:${C.green}; color:#fff;
    font-size:10px; font-weight:800; display:inline-flex; align-items:center; justify-content:center; margin-right:8px; }
  .anskor { font-size:11px; }

  /* 표지 */
  .cov-badges { margin-bottom:20px; }
  .ctitle { font-size:34px; font-weight:800; color:${C.ink}; margin-bottom:14px; }
  .csub { color:${C.teal}; font-weight:700; font-size:15px; margin-bottom:12px; }
  .csrc { color:${C.sub}; font-size:11.5px; font-style:italic; margin-bottom:40px; }
  .usebox { text-align:left; background:${C.mint}; border:1px solid #cfe9e1; border-radius:10px;
    padding:16px 20px; margin:0 40px; }
  .useh { color:${C.tealDark}; font-weight:800; font-size:14px; margin-bottom:8px; }
  .usesteps { display:flex; flex-wrap:wrap; gap:6px 14px; margin:8px 0; }
  .ustep { font-size:11px; } .ustep b { color:${C.teal}; }
  .fine { color:${C.sub}; font-size:10.5px; margin-top:6px; }
  `;
}

async function main() {
  const cats = splitWorked(categories);
  const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${fontFaces()}\n${css()}</style></head>
    <body>${coverHtml()}${cats.map((c, i) => chapterHtml(c, i)).join('')}${answerHtml(cats)}</body></html>`;

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
    margin: { top: '13mm', bottom: '15mm', left: '13mm', right: '13mm' },
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `<div style="width:100%; font-size:8px; color:#9aa0a6;
      padding:0 13mm; display:flex; justify-content:space-between;">
      <span>${FOOTER_BRAND}</span>
      <span>페이지 <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
  });
  await browser.close();
  console.log('✓ 디자인 PDF 생성:', path.relative(process.cwd(), pdfPath));
}

main().catch((e) => { console.error(e); process.exit(1); });

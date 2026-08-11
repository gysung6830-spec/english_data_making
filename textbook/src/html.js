// html.js — 디자인 PDF용 HTML 렌더러 (재사용 모듈)
//
// 참고 교재(Ortica 영어 스타일) 디자인을 HTML/CSS 로 구현하고,
// Chromium 으로 인쇄해 PDF 를 만든다. preview_pdf.js(CLI)와 webapp 이 공유한다.
//   - buildHtml(categories)  → 전체 HTML 문자열
//   - renderPdf(html, pdfPath) → Chromium 으로 PDF 저장
//   - findChrome()           → Chromium 실행 파일 경로

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { splitWorked } = require('./document');
const { makeTip, PRINCIPLES } = require('./tip');

const FONTS_DIR = path.join(__dirname, '..', 'fonts');
const FOOTER_BRAND = '©2026. Ortica 영어. All rights reserved.';

// ── 팔레트 (필생보 딥그린 테마) ──
const C = {
  ink: '#1c2620', sub: '#5f6b64',
  teal: '#14603A', tealDark: '#0C3F26', mint: '#E6F1EA',
  green: '#14603A', greenHdr: '#14603A', zebra: '#EEF5F0',
  key: '#B24A38', keyBg: '#FBECEA',
  gram: '#5E4C9E', gramBg: '#EFEDF8',
  plus: '#B07A1C', plusBg: '#FBF3E0',
  goalBg: '#E6F1EA', goalBar: '#14603A',
  tipBg: '#F2F3F4', tipBar: '#9aa0a6',
  trapBg: '#FEF3E2', trapLine: '#F5D9AE', trapBar: '#C77A17',
  line: '#dfe6e1', greenLine: '#BAD5C2',
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
function catchCard(text) {
  return `<div class="callout catch"><span class="co-ic">✅ 이 정도는 캐치!</span> ${esc(text)}</div>`;
}
function tipCard(text) {
  return `<div class="callout tip"><span class="co-ic">✂ 끊어읽기 팁 — 어디서 끊을까?</span> ${esc(text)}</div>`;
}
// ✂ 끊어읽기 팁 — 어디서 끊을까? (책 앞쪽 별도 페이지, 목차 항목 1회)
const CUT_SIGNALS = [
  ['전치사 앞', 'in / on / at / of / with / for …', '전치사구(전치사+명사)는 한 덩어리', "in 1937 → “1937년에”"],
  ['to부정사 앞', 'to + 동사원형', "‘~하는 것 / ~할 / ~하기 위해’ 덩어리", "to house his works → “작품을 소장하기 위한”"],
  ['접속사 앞', 'and / but / that / because / when …', '뒤에 새 절(주어+동사)이 붙어', "…, and he started teaching → 새 사건 시작"],
  ['관계사 앞', 'who / which / that / where …', '앞 명사를 꾸미는 절의 시작', "the man who lives … → “…하는 그 남자”"],
  ['분사 · 콤마', '-ing / -ed 수식, 그리고 ,', '새 수식 덩어리 시작 · 이미 찍힌 경계', "…, was established → 콤마·수동에서 끊기"],
];
function principlePageHtml() {
  const cards = CUT_SIGNALS.map(([name, trig, rule, ex], i) => `<div class="cutcard">
    <div class="cut-top"><span class="cut-n">${CIRCLED[i]}</span><span class="cut-name">${esc(name)}</span>
      <span class="cut-trig">${esc(trig)}</span></div>
    <div class="cut-rule">${esc(rule)}</div>
    <div class="cut-ex">예) ${esc(ex)}</div>
  </div>`).join('');
  return `<section class="chapter">
    <div class="chhead"><span class="daypill">끊어읽기 원리</span><span class="tagpill">한 번만 익히면 끝</span></div>
    <h1>끊어읽기 팁 — 어디서 끊을까?</h1>
    <div class="chsub">필생보 · 필자의 생각이 보이는 영어독해 — 모든 지문에 이 원리를 그대로 써먹어</div>
    <div class="goal"><span class="goal-ic">핵심 원리</span> 뼈대(진짜 <b>주어+동사</b>)를 먼저 잡고, 나머지 수식 덩어리는 <b>신호어 앞</b>에서 끊어 <b>앞에서부터</b> 붙여 읽어 — 되돌아가지 않기!</div>
    <div class="cutgrid">${cards}</div>
    <div class="pcatch"><span class="pcatch-h">✅ 이 페이지만 기억해!</span>끊는 자리는 늘 <b>‘새 덩어리가 시작되는 신호어 앞’</b>이야. 지문에서 이 5개만 찾으면 문장이 저절로 끊겨.</div>
  </section>`;
}

// ══════════════════════════════════════════════════════════════════════════
//  PART 0 · 독해의 원리 — Ortica 영어 '형광펜 독해' 원리 총론(전 12면) 재현
//  (업로드 PART0 지면을 필생보 딥그린으로 1:1 재구성)
// ══════════════════════════════════════════════════════════════════════════
const PART0_PILL = 'PART 0 · 독해의 원리';
// 공용 스캐폴드: 좌측 알약 + 제목 + 우측 페이지번호 + 초록 룰 + 히어로 박스
function ppage(no, h1, hero, body) {
  return `<section class="chapter part0">
    <div class="phead"><span class="ppill">${PART0_PILL}</span><span class="ph-title">${h1}</span>${no ? `<span class="ph-no">${no} / 11</span>` : ''}</div>
    <div class="phrule"></div>
    ${hero ? `<div class="phero">${hero}</div>` : ''}
    ${body}
    <div class="pfoot">© 2026. Ortica 영어 · 형광펜 독해 — 독해의 원리</div>
  </section>`;
}
// 초록 세로바 소제목
function psec(t) { return `<div class="psec">${t}</div>`; }
// 불릿 리스트(› 마커)
function pbul(items) { return `<ul class="pbul">${items.map((x) => `<li>${x}</li>`).join('')}</ul>`; }
// 표
function ptable(headers, rows) {
  const th = headers.map((h) => `<th>${h}</th>`).join('');
  const tb = rows.map((r) => `<tr>${r.map((c, i) => `<td class="${i === 0 ? 'k' : ''}">${c}</td>`).join('')}</tr>`).join('');
  return `<table class="ptable"><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table>`;
}
// 기출 예시 인용 박스 (라벨 + 회차 + 영문[하이라이트 가능] + 해설)
function qbox(lab, cite, en, note, cls) {
  return `<div class="qbox ${cls || ''}"><div class="q-top"><span class="q-lab">${lab}</span>${cite ? `<span class="q-cite">${cite}</span>` : ''}<span class="q-en">${en}</span></div>${note ? `<div class="q-note">${note}</div>` : ''}</div>`;
}
// A/B 배지 칩 — 'A lead to B' 처럼 A·B 를 배지로 렌더
function abChips(list) {
  const one = (s) => {
    const parts = esc(s).split(/\b(A|B)\b/);
    const html = parts.map((p) => (p === 'A' ? '<span class="ab-badge ab-a">A</span>' : p === 'B' ? '<span class="ab-badge ab-b">B</span>' : p)).join('');
    return `<span class="abchip">${html}</span>`;
  };
  return `<div class="abchips">${list.map(one).join('')}</div>`;
}

// ── P1 (01/11) · 독해 태도 ─────────────────────────────────────────────
function attitudePageHtml() {
  return ppage('01', '모의고사 점수는 ‘태도’에서 나온다',
    '“정확하게 모든 문장을 해석하는 것” 과 “좋은 점수” 는 비례하지 않는다. 점수는 <b>구문을 완벽히 분석한 사람</b>이 아니라 <b>글의 중심 내용을 잘 파악한 사람</b>에게 간다.',
    `<div class="tgrid">
       <div class="tcard"><span class="tbadge co">공부할 때</span><div class="tcard-t">걸어다니는 사전</div><div class="tcard-d">단어·구문을 끝까지 정확히. 실력의 바탕을 쌓는 시간.</div></div>
       <div class="tcard"><span class="tbadge co">시험 칠 때</span><div class="tcard-t">모르는 건 추론</div><div class="tcard-d">모르는 단어에 멈추지 말고 <b>문맥으로 추론</b>. “무슨 말을 하려는가”만 고민.</div></div>
     </div>`
    + psec('“무슨 글이지?” 의문을 가지며 읽기')
    + pbul([
      '하나의 영어 단락은 결국 <b>하나의 주제</b>로 귀결된다. 다양한 정보는 그 주제를 설명하려는 것일 뿐 — <b>장황한 표현에 속지 말 것</b>.',
      '주어진 정보를 다 소화하며 읽으면 지친다. <b>무엇을 부각하는지</b> 찾으며 읽자.',
      '<b>(what)</b> 이 글이 무엇에 대한 글인가? → <b>(기준)</b> ‘A에 대한 글이구나’ 잡고 <b>필자의 의견</b>(키워드의 개념·주장)을 생각하며 읽기.',
    ])
    + psec('HOW — 초반에 멈춰 ‘관통 키워드’를 잡는다')
    + pbul([
      '글의 초반 3문장쯤 읽고 <b>멈춰서</b> 생각한다: 세 문장을 <b>관통하는 하나의 키워드</b>는? <b>반복되는 말</b>을 찾아라.',
      '잘 안 보이면 잠시 멈춘다. 예시가 있으면 앞 문장과 어떻게 같은지 생각한다. (앞 문장 <span class="ktag g">General</span> → for example <span class="ktag o">Specific</span>)',
      '주제 문제는 키워드가 <b>반드시 선지에 담긴다</b> — 같은 용어를 쓰지 않더라도.',
    ])
    + `<div class="pcatch"><span class="pcatch-h">✅ 주제 선지</span> 편견 없는 실험(본문) → <b>객관적인 실험의 중요성</b>(선지) ✔<br><span class="pc-warn">주의 — 가장 많이 쓰인 단어가 선지에 있다고 해서 답인 것은 아니다.</span></div>`);
}

// ── P2 (02/11) · 완급조절 ──────────────────────────────────────────────
function pacePageHtml() {
  const flow = `<div class="flow3">
    <div class="fl old"><div class="fl-h">OLD (배경·통념)</div><div class="fl-b">도입부 / 마이너스<br>약하게 “음~ 그렇구나”</div></div>
    <div class="fl-arw">→</div>
    <div class="fl new"><div class="fl-h">NEW · MAIN (주제)</div><div class="fl-b">필자가 진짜 하고 싶은 말<br><b>가장 강하게</b></div></div>
    <div class="fl-arw">→</div>
    <div class="fl sup"><div class="fl-h">SUPPORT (부연)</div><div class="fl-b">예시·상술<br>선명하면 약하게</div></div>
  </div>`;
  return ppage('02', '완급조절 — OLD / NEW·MAIN / SUPPORT',
    '모든 문장을 똑같이 강하게 읽을 필요는 없다. 한 단락엔 주제가 <b>하나뿐</b>. 강·약을 조절하는 <b>능동적 독해</b>를 하자. 완급 없이 직독직해만 하면 남는 정보가 없다.',
    flow
    + psec('OLD를 알아채는 신호 — 컴마(,)가 붙은 앞자리')
    + pbul([
      '문두에서 <b>컴마로 끊기는 부사절·분사구문·전치사구</b>가 흔히 배경(OLD) 신호. (컴마가 없으면 주절 핵심 정보일 때가 많다.)',
      'OLD는 <b>약하게</b>(해석을 하지 말라는 게 아니다). 진부한 통념(~)을 던져 <b>뒤 내용을 강조</b>하는 <b>대비 효과(contrast effect)</b>다.',
    ])
    + qbox('OLD → NEW', '2023 6월 37번', '<span class="ol">Although</span> this is true, <span class="q-hl">it has also become a tired and played-out argument.</span>', '‘맞는 말이다’(양보·OLD) → 하지만 ‘진부한 주장’(NEW·핵심). 양보절은 약하게, 주절이 진짜 하고 싶은 말.')
    + psec('SUPPORT — 선명함으로 완급을 정한다')
    + pbul([
      '선명함 <b>높음</b>(MAIN이 이해됨) → SUPPORT는 <b>약하게</b> 대충. support로 MAIN을 확인.',
      '선명함 <b>낮음</b>(이해 안 됨) → SUPPORT를 <b>강하게</b> 천천히. 단, MAIN과 SUPPORT 정보가 충돌하면 안 된다.',
      '「<b>, 관계사,</b>」는 약하게(독자가 모를 것 같아 덧붙인 정보). 관계사만 있으면 필요한 정보이니 챙긴다.',
    ])
    + qbox(', 관계사', '2024 9월 33번', '… three different scientists each independently rediscovered Mendel’s forgotten work, <span class="q-hl">which</span> of course had been there all along.', '「, which」이하는 부연(비제한) — 핵심은 ‘세 과학자가 멘델의 연구를 재발견’.'));
}

// ── P3 (03/11) · 추론(어순·구두점) ─────────────────────────────────────
function inferPageHtml() {
  return ppage('03', '모르는 것은 ‘추론’한다 — 어순·구두점',
    '영어는 흔히 <b>General → Specific</b> 순서. 추상적인 말이 앞에 오면 대개 뒤에 구체적인 정보가 따라온다. 모르는 단어에 멈추지 말고 <b>‘뒤가 알려줄 것’</b>이라 믿고 읽어라.',
    psec('정의를 여는 신호 — BE동사 (A = B)')
    + qbox('A = B', '2023 9월 22번', '<b>Tax is</b> the application of a society’s theories of distributive justice.', '모르는 말도 be동사 뒤에서 정의됨 — ‘Tax = 분배 정의 이론의 적용’. ‘뒤가 알려줄 것’이라 믿고 읽는다.')
    + psec('구두점 — 필자가 남긴 독해 신호')
    + pbul([
      '<b>세미콜론 ;</b> = 두 문장을 잇는 <b>연결(and·but·so 역할)</b>. ‘내용상 관련 있구나’만 생각하고 넘긴다.',
      '<b>콜론 :</b> = 부연·재진술·열거. 실전에선 <b>A : B</b> 에서 A가 이해되면 B는 읽을 필요 없다.',
      '<b>대쉬 –</b> = 콜론과 유사(상술). 부연을 중간에 넣을 땐 대쉬, 끝에 넣을 땐 콜론.',
      '<b>따옴표 “ ” ‘ ’</b> = 인용·강조, 또는 단어의 본래 의미를 <b>비틀어 쓸 때</b>(필자의 의도).',
    ])
    + `<div class="qcols">
        ${qbox('콜론 :', '2022 6월 36번', 'This isn’t really a paradox: landmarks are themselves, but they also define neighborhoods around themselves.', '콜론 앞(‘역설이 아니다’)이 이해되면 뒤(부연)는 확인만 — B 약하게.')}
        ${qbox('대쉬 —', '2023 6월 20번', 'What can make the difference is drive — utilizing the mental gear to maximize gains made in the technical and physical areas.', '대쉬 이하는 ‘drive’를 상술 — 앞이 이해되면 약하게.')}
      </div>`
    + psec('병렬·나열 [and / or] — 하나만 알면 된다')
    + pbul(['<b>A, B and C / A, B or C</b> 에서 셋 중 <b>하나라도 이해되면</b> 나머지는 ‘비슷한 문맥’으로 넘긴다.'])
    + qbox('나열', '2023 9월 24번', '… a wide potential of variations in tempo, volume, tonal quality and intonation.', '‘tempo’ 하나만 알아도 ‘여러 변주 요소’ 나열임을 안다 — 나머지는 넘겨도 됨.'));
}

// ── P4 (04/11) · 연결사 지도 ───────────────────────────────────────────
function connectivePageHtml() {
  return ppage('04', '연결사 = “어디가 중요한지 알려줄게”',
    '연결사(접속부사)는 문장과 문장의 <b>관계</b>를 알려주는 표지다. 문장 어디에 있든 <b>앞 문장과 뒷 문장 ‘사이’</b>에 놓고 읽어라. 특히 <b>역접</b>은 완급의 분기점이다.',
    psec('역접 — Switching vs Contrast')
    + `<div class="tgrid">
        <div class="tcard sw"><span class="tbadge sw">Switching</span><div class="tcard-t">A ‹ B · 뒤가 중요</div><div class="tcard-d">‘그러나·대신에’. 앞을 뒤집고 <b>뒷 내용이 핵심</b>. 앞은 약하게.</div></div>
        <div class="tcard co"><span class="tbadge co">Contrast</span><div class="tcard-t">A = B · 둘 다 중요</div><div class="tcard-d">‘반면에’. 두 대상을 <b>비교·대조</b> — 양쪽 다 챙긴다.</div></div>
      </div>`
    + `<div class="qcols">
        ${qbox('Switching', '2023 6월 23번', '<b>However,</b> the emotional states themselves are likely to be quite invariant across cultures.', '앞 통념을 <b>뒤집어</b> 필자 주장으로 — 뒷내용이 핵심.')}
        ${qbox('Contrast', '2024 6월 33번', 'The artist, <b>on the other hand,</b> relies on the strength of her artistry to effect a marriage between subjectivities.', '앞 대상 ↔ ‘the artist’를 <b>대조</b> — 양쪽 다 중요.')}
      </div>`
    + ptable(['묶음', '뜻', '대표 연결사'], [
      ['반대·전환', '그러나', 'however, but, still, though, nevertheless, nonetheless, even so'],
      ['대체·대신', '대신에', 'instead, rather'],
      ['대조·대비', '반면에', 'on the other hand, by contrast, conversely, but, however'],
    ])
    + pbul(['<b>그러나</b> = 앞 내용 <b>전체</b>를 뒤집음.&nbsp;&nbsp;<b>대신에</b> = 앞 내용 <b>일부</b>를 대체(‘대신’을 ‘그러나’로 못 바꿈).'])
    + `<div class="qcols">
        ${qbox('그러나', '2022 6월 22번', 'It does, <b>however,</b> greatly improve its chances.', 'however가 문장 중간에 있어도 앞뒤 사이에 놓고 역접으로 읽는다.')}
        ${qbox('대신에', '2022 6월 23번', '<b>Instead,</b> the bases and interests of this activity change and develop to playing and watching sports.', '앞 내용의 <b>대체</b>로 전개 — ‘그러나’로 바꾸면 어색.')}
      </div>`
    + psec('헷갈리는 다의어 — 2순위 해석까지 챙기기')
    + ptable(['표현', '1순위', '2순위'], [
      ['but / however', '그러나(Switching) / 반면에(Contrast)', '역접 아닐 땐 <b>강조</b>(Emphasis)'],
      ['In fact', '사실상·실제로 (순접)', '하지만 사실은 (역접)'],
      ['on the contrary', '오히려·도리어 (앞 진술을 부정·강조)', '≠ on the other hand(반면에)와 혼동 주의'],
      ['on the other hand', '반면에 (by contrast)', '다른 한편으로는 (첨가)'],
    ])
    + `<div class="qcols">
        ${qbox('In fact', '2025 6월 32번', '<b>In fact,</b> the ability to generate creative ideas is essentially useless if these ideas subsequently die.', '여기선 <b>순접</b>(사실상) — 앞을 강조·부연(‘역접’ 아님).')}
        ${qbox('다른 한편', '2026 9월 40번', '<b>On the other hand,</b> if characters are the work of several hands over decades, they may change considerably.', '역접이 아니라 <b>다른 경우를 첨가</b> — ‘다른 한편으로는’.')}
      </div>`);
}

// ── P5 (05/11) · 재진술 원리 ───────────────────────────────────────────
function restatePrinciplePageHtml() {
  return ppage('05', '재진술(Paraphrasing) — 같은 말을 알아채기',
    '독해의 최종 기술은 <b>재진술</b> — 명시적 단서 없이도 “앞의 그 말을 <b>바꿔 한 거구나</b>”를 느끼는 것. 필자는 핵심 주장·소재를 한 번만 말하지 않고 <b>표현을 바꿔 되풀이</b>하고, 정답 선지는 그 되풀이의 <b>마지막 한 번</b>이다.',
    `<div class="pnote"><span class="pnote-ic">🔁</span>PART 1에는 재진술이 뚜렷한 문항마다 「재진술 연결 문제」가 붙어 있다 — 소재가 하나면 A → A′ → A″ …로, 비교 지문이면 A → A′ … · B → B′ …로 두 소재를 나란히, <b>지문에 실제로 되풀이된 만큼</b> 이어 본다(억지로 만들지 않는다). <b>마지막 재진술이 곧 정답 선지</b>임을 지문을 풀며 확인한다.</div>`
    + psec('순접 연결사 — 소재는 달라도 주제는 같다')
    + ptable(['기능', '방향', '대표 연결사'], [
      ['재진술', 'G/S → 다시 말하면 → G/S', 'that is, in other words, in effect, indeed'],
      ['예시·요약', '일반 ↔ 구체', 'for example, for instance / in short, in conclusion'],
      ['나열·첨가', '같은 주제에 항목을 더함', 'similarly, likewise, also, moreover, furthermore'],
      ['인과', '결과 ← 원인', 'as a result, therefore, thus, hence, so'],
    ])
    + qbox('재진술', '2022 수능 40번', '<b>That is,</b> the explanation of scientific generalizations comes from the causal mechanisms that produce the regularities.', '앞 문장을 같은 뜻으로 다시 말함 — that is가 없어도 이 관계를 느끼는 것이 재진술 독해.')
    + psec('재진술 독해 = G(일반화) ↔ S(구체화)를 오간다')
    + pbul([
      '표현이 달라도 <b>문맥상 하나의 범주</b>면 같은 말이다 — 둘 중 하나만 이해되면 나머지는 약하게.',
      '까다로운 순서·삽입도 명시적 단서가 아니라 <b>재진술(소재 동일)</b>을 답의 근거로 낸다.',
    ])
    + qbox('범주 묶기', '', '서울 = 대한민국의 수도 = 한국에서 천만이 사는 곳', '표현은 달라도 <b>하나의 범주</b>임을 느끼는 것 — 정답 선지는 지문을 이렇게 바꿔 말한다.'));
}

// ── P6 (06/11) · 재진술 5변환·함정 ─────────────────────────────────────
function transformPageHtml() {
  return ppage('06', '재진술로 정답을 만든다 — 5변환 · 함정',
    '정답 = 뜻은 그대로, <b>단어만 바꾼다</b>. 오답 = 단어는 그대로 두고, <b>뜻을 왜곡한다</b>. 그래서 <b>지문 단어가 그대로 보이는 선지부터 의심</b>하고, 표현이 바뀌어 낯선 선지를 정답 후보로 본다.',
    psec('평가원 단골 변환 5패턴 — 지문 → 정답 선지')
    + ptable(['변환', '지문 표현 → 정답 선지'], [
      ['① 동의어 치환', 'proper · forces · detailed → careful · drives · thorough'],
      ['② 구체 → 추상', 'a songwriter · a boundary → creative people · locality'],
      ['③ 품사 전환', 'decide(동사) → decision-making(명사)'],
      ['④ 반대구조(부정↔긍정)', 'does not shrink → expands'],
      ['⑤ 비유 → 직설', 'a window to other worlds → unfamiliar perspectives'],
    ])
    + psec('오답은 이 4잣대로 소거한다')
    + ptable(['3초 잣대', '이럴 때 소거', '확인법'], [
      ['copy · 복사', '지문 단어가 그대로 보여 익숙하다', '그 단어의 <b>논리·관계</b>가 지문과 같은지 재확인'],
      ['reverse · 반대', '단어는 비슷한데 방향이 반대다', '<b>부정어·인과 방향</b>을 대조'],
      ['distort · 왜곡', '90%는 맞는데 한 군데가 어긋난다', '<b>대상·조건·정도</b>를 하나씩 대조'],
      ['off · 이탈', '그럴듯하지만 지문에서 본 적 없다', '<b>근거 문장</b>을 못 짚으면 소거(상식 ≠ 근거)'],
    ])
    + `<div class="pnote"><span class="pnote-ic">⚠️ 흔한 오해</span>“all·always·only 같은 극단어가 있으면 오답” — 사설·토익식 요령. 실제 평가원 오답에서 극단어는 드물다. 평가원은 극단어가 아니라 <b>‘지문 근거와의 관계’</b>로 오답을 만든다.</div>`
    + `<div class="pnote"><span class="pnote-ic">🔁</span>PART 1에서 이렇게 훈련한다 — 각 문항 STEP 1의 「재진술 미션」에서 필자 주장·소재를 먼저 잡고, STEP 3의 「재진술 지도」에서 그것이 어떻게 되풀이되어 정답이 됐는지 확인한다.</div>`);
}

// ── P7 (07/11) · 글의 구조 6가지 ───────────────────────────────────────
const STRUCTURE_GUIDE = [
  ['통념 → 반박(반전)', 'many people think · it is widely believed · traditionally · we tend to think', 'But · However · Yet · In fact · In reality · Contrary to', '흔한 생각(통념)을 깔아둔 뒤 뒤집어 필자 주장을 편다.', '“Many people believe X. But in fact, Y.”'],
  ['주장 → 근거·예시', 'should · must · it is important that · I argue', 'because · since · for example · research shows · therefore', '주장을 먼저 내세우고 이유·연구·예시로 뒷받침.', '“X가 중요하다. 예를 들어 …, 연구에 따르면 …”'],
  ['문제 → 해결(방안)', 'problem · challenge · issue · difficulty · concern', 'solution · solve · address · one way to · need to', '문제를 제기하고 해결책·방안을 제시.', '“이런 문제가 있다. 이를 해결하려면 …”'],
  ['비교 · 대조', 'while · whereas · unlike · in contrast · on the other hand', 'similarly · likewise · just as · like · both … and', 'A와 B의 공통점·차이점을 견줌.', '“A는 …인 반면, B는 …이다.”'],
  ['시간 · 순서(나열)', 'first · second · next · then · later · finally', 'in 1937 · meanwhile · over time · eventually · subsequently', '사건·과정을 시간·순서대로(전기·실험·역사).', '“먼저 …, 그다음 …, 마침내 …”'],
  ['예시 → 일반화(결론)', 'for example · such as · consider · take … as an example', 'thus · therefore · in short · this suggests · overall', '구체 사례를 든 뒤 일반 원리·결론으로 묶음.', '“예: …. 이런 사례들은 결국 …임을 보여준다.”'],
];
function structurePageHtml() {
  const cards = STRUCTURE_GUIDE.map((r, i) => `<div class="scard">
    <div class="sc-top"><span class="sc-n">${CIRCLED[i]}</span><span class="sc-name">${esc(r[0])}</span></div>
    <div class="sc-sig"><span class="sc-mag">🔎 통념/앞</span> ${esc(r[1])}</div>
    <div class="sc-sig"><span class="sc-arw">↳ 반전/뒤</span> ${esc(r[2])}</div>
    <div class="sc-flow">${esc(r[3])}</div>
    <div class="sc-ex">예) ${esc(r[4])}</div>
  </div>`).join('');
  return ppage('07', '글의 구조 — 어떤 짜임이 있나?',
    '글의 구조 = 필자가 생각을 배치한 ‘틀’. <b>전환어(But/However…)와 연결어</b>를 신호로 잡으면 구조가 보이고, 구조가 보이면 <b>요지·필자 주장</b>이 빨리 잡힌다. 아래 <b>6가지 틀</b> 중 하나를 예측하며 읽자.',
    `<div class="scardgrid">${cards}</div>`
    + psec('이렇게 써먹어')
    + pbul([
      '지문마다 <b>‘해석 전에’</b> 이 6개 중 하나를 예측하고, 지문 끝에서 맞았는지 확인한다.',
      '전환어(But·However)가 보이면 <b>①통념→반박</b>, 대조어가 보이면 <b>④비교·대조</b> — 신호가 곧 구조다.',
    ]));
}

// ── P8 (08/11) · 긍정/부정(±) 어휘 사전 ① ──────────────────────────────
const STANCE_POS = [
  '중요·필수', 'critical · crucial · essential · vital · key · fundamental · indispensable · integral · significant · substantial · principal · prime · core · necessary',
  '이익·가치', 'benefit · beneficial · valuable · priceless · fruitful · merit · desirable · relevant · work(효과 있다)',
  '강조·강화', 'emphasize · stress · enhance · reinforce · prioritize · matter · count · be of importance',
  '집중·추구·선호', 'focus on · concentrate on · center on · attend to · seek to V · in favor of · need · require · fond of',
  '강조 구문·부사', 'only · invariably · substantially · nothing but · not just A but also B · It is … that · win out',
];
const STANCE_NEG = [
  '버림·제거', 'abandon · discard · scrap · drop · remove · eliminate · discharge · leave out · rule out · removal',
  '무시·간과', 'disregard · ignore · overlook · neglect · dismiss · of little account',
  '부족·부재·결핍', 'lack · shortage · absence · absent from · free from · incapable of · drawback · flaw · downside · side effect',
  '거부·반대·금지', 'refuse · reject · resist · exclude · deny · disapprove · discourage · forbid · say no to',
  '방해·차단·약화·실패', 'interfere with · stand in the way of · cut off · displace · prevent[keep/stop] A from Ving · diminish · obscure · fail · lose out',
  '비판·의심·무가치', 'criticize · question · doubt · challenge · myth · misleading · worthless · irrelevant · unnecessary · costly',
];
function stanceChips(arr, cls) {
  let h = '';
  for (let i = 0; i < arr.length; i += 2) {
    const words = arr[i + 1].split(' · ')
      .map((x) => `<span class="chip ${cls}">${esc(x)}</span>`).join('');
    h += `<tr><td class="k">${esc(arr[i])}</td><td><span class="chips">${words}</span></td></tr>`;
  }
  return h;
}
function stanceVocabPageHtml() {
  return ppage('08', '긍정/부정(±) 어휘 사전 ①',
    '필자는 무엇을 <b>지지(＋)</b>하고 무엇을 <b>버리는지(−)</b>로 글을 끌고 간다. 그래서 문장 뜻을 다 몰라도 핵심어의 <b>± 방향</b>만 잡으면 요지·함축·정답 선지가 보인다. 아래 어휘는 “이 단어가 나오면 필자 태도가 어느 쪽인지”를 알려주는 <b>방향 표지</b>다.',
    `<div class="dirgrid">
       <div class="dircard pos"><div class="dir-h">＋ 긍정 방향</div><div class="dir-d">중요하다·이익이다·강조한다 → 필자가 <b>부각·지지</b>. 대개 노랑(핵심)·정답 쪽.</div></div>
       <div class="dircard neg"><div class="dir-h">− 부정 방향</div><div class="dir-d">버린다·부족하다·무시한다 → 필자가 <b>비판·배제</b>. 통념(OLD)이나 반대 대상일 때가 많다.</div></div>
     </div>`
    + `<div class="voca-h pos"><span class="voca-badge pos">＋</span> 필자가 중시·지지하는 어휘</div>`
    + `<table class="ptable voca"><thead><tr><th>갈래</th><th>대표 어휘</th></tr></thead><tbody>${stanceChips(STANCE_POS, 'pos')}</tbody></table>`
    + `<div class="voca-h neg"><span class="voca-badge neg">−</span> 필자가 버리거나 부정하는 어휘</div>`
    + `<table class="ptable voca neg"><thead><tr><th>갈래</th><th>대표 어휘</th></tr></thead><tbody>${stanceChips(STANCE_NEG, 'neg')}</tbody></table>`);
}

// ── P9 (09/11) · 긍정/부정(±) 어휘 사전 ② — 방향 전환·적용 ───────────────
function stancePolarityPageHtml() {
  return ppage('09', '긍정/부정(±) 어휘 사전 ② — 방향 전환·적용',
    '가장 중요한 건 방향을 <b>‘뒤집는’ 표현</b>이다. 긍정 대상 앞에 부정어가 붙으면 순식간에 −가 된다. 이 <b>극성 전환</b>을 놓치면 정반대로 읽는다 — 평가원 오답의 단골(<b>반대구조</b>)이 바로 이 지점이다.',
    psec('극성을 뒤집는 신호 — ±를 반대로')
    + `<div class="pnote flip"><b>부정어 · 결어 · 분리</b><br>not, no, never, no longer, hardly, rarely, by no means / free from, absent from, immune to, independent of, apart from, other than / far from, cease, stop</div>`
    + ptable(['원래 방향', '전환 표현이 붙으면'], [
      ['shrink <span class="dim">(−, 줄다)</span>', '<b>does not</b> shrink = <span class="pchip">＋</span> expands (늘다)'],
      ['bias <span class="dim">(−, 편향)</span>', '<b>free from</b> bias = <span class="pchip">＋</span> 객관적'],
      ['affect <span class="dim">(영향)</span>', '<b>immune to</b> = <span class="nchip">−</span> 영향받지 않음'],
      ['necessary <span class="dim">(＋)</span>', '<b>not</b> necessarily = 반드시 ~는 아님(약화)'],
    ])
    + psec('독해에 이렇게 적용한다')
    + ptable(['유형', '± 어휘로 푸는 법'], [
      ['함축 (21)', '밑줄 표현이 ＋인지 −인지만 판정 → 방향이 다른 선지 절반을 먼저 소거. (어휘 뜻 몰라도 됨)'],
      ['패러프레이징 함정', '정답의 ± 방향이 지문과 <b>반대면 오답</b>(반대구조). 예: 지문 −인데 선지 ＋.'],
      ['완급조절', '도입 통념(OLD)=− → 역접 뒤 주제(NEW)=＋ 전환을 ± 어휘로 감지.'],
      ['무관·빈칸', '주제의 ± 방향과 <b>어긋나는</b> 문장·선지를 배제.'],
    ])
    + qbox('+/− 판정', '2022 6월 21번', 'abandon your dreams for an empty inbox <span class="nchip">−</span>', '‘꿈을 버린다’(−)를 잡으면, 밑줄이 부정적임을 즉시 판정 → ＋방향 선지 소거.')
    + `<div class="pnote"><span class="pnote-ic">✏️</span>워크북 STEP 2에서 바로 쓴다 — 함축·무관·빈칸의 ±(긍정/부정) 판정과 반대구조 함정 소거에서 이 표를 근거로 삼는다.</div>`);
}

// ── P10 (10/11) · 논리관계 구문 ① 인과·등호 ────────────────────────────
function logicCausePageHtml() {
  return ppage('10', '논리 관계 구문 사전 ① — 인과·등호',
    '독해는 결국 문장들의 <b>‘관계’</b>를 잡는 일이다. 관계는 넷뿐 — <b>인과(→) · 등호(=) · 대조(↔) · 비교(&gt;)</b>. 이 표현들이 보이면 <b>구조가 즉시 드러난다</b>. 연결사·구두점이 없어도 이 구문이 같은 신호 역할을 한다.',
    `<div class="rel-sec"><span class="rel-ic cause">→</span> <b>인과 — A가 B를 낳거나(→) B에서 비롯(←)</b></div>`
    + `<div class="ab-leg"><span class="ab-badge ab-a">A</span>=원인(cause) &nbsp; <span class="ab-badge ab-b">B</span>=결과(effect) — 색으로 어느 쪽이 원인·결과인지 바로 보인다.</div>`
    + `<div class="abgrp-lab">원인 → 결과 <span class="sub">A가 B를 일으킨다</span></div>`
    + abChips(['A result in B', 'A lead to B', 'A cause B', 'A bring about B', 'A bring on B', 'A trigger B', 'A prompt B', 'A give rise to B', 'A contribute to B', 'A be the source of B', 'A influence B', 'A have an effect on B', 'A be a basis for B'])
    + `<div class="abgrp-lab">결과 ← 원인 <span class="sub">A가 B에서 비롯·근거한다</span></div>`
    + abChips(['A result from B', 'A stem from B', 'A arise from B', 'A derive from B', 'A spring from B', 'A originate in B', 'A be rooted in B', 'A be based on B', 'A be anchored in B', 'A be induced by B', 'attribute A to B', 'A due to B'])
    + `<div class="ab-note">결과를 여는 신호(절 단위) — so ~ that / such ~ that / it follows that S V / insofar as. &nbsp;명사 — outcome(결과) · rationale · justification(근거).</div>`
    + `<div class="pnote"><span class="pnote-ic">🔗 연계</span>연결사 지도의 인과(therefore·thus) · 글의 구조 ③문제→해결·⑥예시→일반화. 인과 구문이 보이면 ‘결과=필자 결론(＋)’에 형광펜.</div>`
    + `<div class="rel-sec"><span class="rel-ic eq">=</span> <b>등호·정의 — A = B (같다·라 부른다·상징한다)</b></div>`
    + `<div class="abgrp-lab">A를 B라 하거나 A=B로 놓는다 <span class="sub">정의·명명·상징·간주·동일시</span></div>`
    + abChips(['A is B', 'A be called B', 'A be termed B', 'define A as B', 'refer to A as B', 'A reflect B', 'A mirror B', 'A represent B', 'A embody B', 'A illustrate B', 'regard A as B', 'see A as B', 'view A as B', 'treat A as B', 'recognize A as B', 'describe A as B', 'identify A with B', 'A be equivalent to B', 'A amount to B'])
    + `<div class="ab-note">A=B를 여는 신호 — that is · i.e. · in short / such as · like · including · e.g. (재진술·예시)</div>`
    + `<div class="pnote"><span class="pnote-ic">🔗 연계</span>추론 페이지의 BE동사 정의(A=B)·콜론(:) · 재진술(A=A′). ‘A=B’가 보이면 한쪽만 이해하면 나머지는 약하게.</div>`);
}

// ── P11 (11/11) · 논리관계 구문 ② 대조·비교 ────────────────────────────
function relGroup(labCls, lab, sub, list) {
  return `<div class="relgrp"><span class="rel-lab ${labCls}">${lab}<span class="rel-sub">${sub}</span></span>${abChips(list)}</div>`;
}
function logicContrastPageHtml() {
  return ppage('11', '논리 관계 구문 사전 ② — 대조·비교',
    '이 표현들이 보이면 = 글에 <b>소재가 둘(A·B)</b>이라는 신호다. 뜻을 하나하나 외우지 말고, <b>두 소재의 관계를 기호로</b> 잡아라 — A&gt;B · A&lt;B · A↔B · A⇒B. 재진술의 <b>비교 지문(A·B 추적)</b>과 바로 연결된다.',
    relGroup('rel-gt', 'A &gt; B', 'A가 B보다 우위', ['more A than B', 'A outweigh B', 'A surpass B', 'A exceed B', 'A prevail over B', 'A outperform B', 'A outnumber B', 'A outshine B', 'A outlive B', 'A beat B', 'A trump B', 'A precede B', 'A superior to B', 'prefer A to B', 'favor A over B', 'choose A over B', 'A rather than B', 'A instead of B'])
    + relGroup('rel-lt', 'A &lt; B', 'A가 B에 밀림', ['less A than B', 'A inferior to B', 'A be overwhelmed by B', 'A be overcome by B', 'A be overshadowed by B', 'A be dwarfed by B', 'A is weakened by B', 'A be sacrificed for B'])
    + relGroup('rel-diff', 'A ↔ B', 'A와 B가 다름·대조', ['A differ from B', 'distinguish A from B', 'separate A from B', 'set A apart from B', 'boundary between A and B', 'A contrast with B', 'unlike', 'whereas', 'on the other hand', 'opposed to', 'contrary to', 'the former', 'the latter', 'vice versa'])
    + relGroup('rel-sub2', 'A ⇒ B', 'A가 B로 대체·전환', ['A replace B', 'A displace B', 'A be substituted by B', 'A be supplanted by B', 'A give way to B', 'switch to B', 'shift from A to B', 'transition from A to B', 'move from A to B'])
    + relGroup('rel-focus', '→ B', 'not A but B — B가 초점, A는 버림', ['not A but B', 'not so much A as B', 'far from A'])
    + `<div class="pnote"><span class="pnote-ic">🔗 연계</span>연결사 대조(whereas·on the other hand) · 글의 구조 ④비교·대조 · 재진술 비교 지문(A·B 두 소재). 필자가 미는 쪽(&gt;·B)이 곧 주제.</div>`
    + qbox('초점 못박기', '비교·대체 구문', '<b>not</b> the technology <b>but</b> the way we use it', '‘A가 아니라 B’ — B(우리가 쓰는 방식)가 필자의 초점. A는 버리는 미끼(−).')
    + `<div class="pnote"><span class="pnote-ic">✏️</span>워크북에서 바로 쓴다 — 이 네 관계(→ = ↔ &gt;)는 STEP 2에서 노랑 문장을 잡는 신호이자 순서·삽입의 연결고리다.</div>`);
}

// ── P12 (요약) · 형광펜 신호 사전 포스터 ───────────────────────────────
// [번호/제목, 신호어(italic), → 의미, 예시 en, 예시 해설]
const HIGHLIGHT_SIGNALS = [
  ['① 역접·대조', 'However · But · Yet · Nevertheless · In contrast · By contrast · On the contrary · Instead · Conversely · Unlike · Whereas · Rather(than) · Still · No longer · not A but B', '앞 내용을 뒤집는다 = 필자의 진짜 주장', 'It looks simple. However, it often fails.', 'However 뒤가 정답'],
  ['② 결론·귀결', 'Thus · Therefore · Hence · So · Consequently · As a result · In conclusion · In short · In sum · Ultimately · That is why', '글을 닫는 문장 = 주제', 'Therefore, planning matters most.', '결론=주제'],
  ['③ 인과', 'because · since · due to · owing to · lead to · result in · give rise to · thereby · in order to · this is because', '논리의 뼈대(원인 → 결과)', 'It grew because demand rose.', '원인이 논리 핵심'],
  ['④ 강조·주장', 'should · must · ought to · need to / important · essential · crucial · vital · key / In fact · Indeed · Above all · especially · notably · clearly', '필자가 대놓고 미는 문장', 'You must plan first.', '당위=주제'],
  ['⑤ 최상·유일·한정', 'the most · the best · the only · the single · first / only · only when · only if · unless · except · as long as', '정답이 숨는 단골 자리', 'It works only when cold.', '조건이 정답 근거'],
  ['⑥ 통념·반전', 'Many believe · It is (often) thought · Traditionally · Contrary to popular belief · Surprisingly · Paradoxically · Ironically', '통념을 깨는 곳 = 주제', 'Many believe X. But actually Y.', 'Y가 주제'],
  ['⑦ 정의·재정의', 'is defined as · means · refers to · that is · in other words / 콜론( : ) · 대시( — ) 뒤', '개념을 못박는 문장', 'Freedom means real choice.', '정의=핵심'],
  ['⑧ 태도·평가어(±)', '＋ benefit · advantage · valuable · effective · promising ↔ − problem · risk · illusion · myth · fail · drawback', '대의·함축·정답의 방향(＋/−)', 'an illusion, not a real gain', '필자 태도는 (−)'],
  ['⑨ 예시 후 일반화', 'In each case · In general · Overall · This suggests / shows / means', '예시를 접고 결론으로 복귀', 'In each case, limits helped.', '예시 끝, 결론 복귀'],
  ['⑩ 위치', '글 첫 문장 · 각 단락 첫 문장 · 마지막 문장 · 빈칸/밑줄 문장 + 바로 앞뒤', '신호어 없어도 무조건 읽는 자리', '빈칸 문장과 그 앞뒤는 항상 노랑', ''],
  ['⑪ 지시·연결(대용어)', 'this · these · that · those · such (a) · one · another · its · the former · the latter', '순서·삽입(35~38)의 핵심 — 앞 문장을 가리킨다', 'This problem… / Such a view…', '앞에 그 대상이 있어야 함'],
  ['⑫ 첨가·병렬', 'not only ~ but also · moreover · furthermore · in addition · as well as · besides / (비교) similarly · likewise · just as', '같은 방향 추가·강조(주제 강화)', 'Not only A but also B', 'B에 방점'],
];
const HIGHLIGHT_SKIP = [
  ['스킵 · 예시', 'For example · For instance · such as · like · e.g. · to illustrate · including · namely / take · consider · imagine · suppose', '주장의 근거일 뿐, 주장 자체가 아님', 'Take/Consider/Imagine ~', '예시 도입, 통째 스킵'],
  ['스킵 · 부연/양보', '숫자·연도·인명·지명 나열 · 재진술 반복 · Although · Though · Despite · In spite of / 딸린 절 · 긴 관계절( , which ~ )', '양보절은 스킵, 주절이 핵심', 'Despite the noise, it worked.', '주절(worked)만'],
];
function sigCard(s, skip) {
  return `<div class="sig"><span class="sig-h${skip ? ' skip' : ''}">${esc(s[0])}</span>
    <div class="sig-w">${esc(s[1])}</div>
    <div class="sig-m">→ ${esc(s[2])}</div>
    ${s[3] ? `<div class="sig-ex"><b>${esc(s[3])}</b>${s[4] ? ` → ${esc(s[4])}` : ''}</div>` : ''}</div>`;
}
function highlightPosterPageHtml() {
  const left = [0, 2, 4, 6, 8, 10];
  const right = [1, 3, 5, 7, 9, 11];
  const col = (idxs, extra) => idxs.map((i) => sigCard(HIGHLIGHT_SIGNALS[i])).join('') + (extra ? sigCard(extra, true) : '');
  return `<section class="chapter part0 poster-page">
    <div class="poster-title">형광펜 독해 — 수능 영어, ‘칠하는 법’을 배운다</div>
    <div class="poster-sub">노란색 ‘신호’로 무엇을 읽고 무엇을 버릴까 — 이 표 한 장이 출발점</div>
    <div class="poster">
      <div class="poster-h">🖍️ 신호 사전 — 노란색은 ‘신호’로 찾는다</div>
      <div class="poster-lead">정답을 몰라도 아래 신호가 보이면 🟡 무조건 읽는다. 이 표가 눈에 익으면 어떤 지문이든 읽을 문장이 먼저 보인다.</div>
      <div class="poster-cols">
        <div class="poster-col">${col(left, HIGHLIGHT_SKIP[0])}</div>
        <div class="poster-col">${col(right, HIGHLIGHT_SKIP[1])}</div>
      </div>
      <div class="poster-steps">
        <div class="pstep"><div><span class="pstep-n">1</span><span class="pstep-t">훑기</span></div><div class="pstep-d">첫 문장·빈칸/밑줄 문장 먼저 → ‘무엇을 묻나’ 파악</div></div>
        <div class="pstep"><div><span class="pstep-n">2</span><span class="pstep-t">칠하기</span></div><div class="pstep-d">①~⑫ 신호가 보이는 문장만 🟡 형광펜, 예시·양보는 ⬜ 스킵</div></div>
        <div class="pstep"><div><span class="pstep-n">3</span><span class="pstep-t">찍기</span></div><div class="pstep-d">노랑 문장으로 정답 근거 → 패러프레이즈로 선지 확정</div></div>
      </div>
    </div>
    <div class="pfoot">© 2026. Ortica 영어 · 형광펜 독해 — 독해의 원리</div>
  </section>`;
}

// 원리 페이지 묶음(지문 앞) — 업로드 PART0 순서 그대로 12면
function principlesSectionHtml() {
  return attitudePageHtml() + pacePageHtml() + inferPageHtml() + connectivePageHtml()
    + restatePrinciplePageHtml() + transformPageHtml() + structurePageHtml()
    + stanceVocabPageHtml() + stancePolarityPageHtml()
    + logicCausePageHtml() + logicContrastPageHtml() + highlightPosterPageHtml();
}

// ⚠️ 이거 조심 — 이 문장에서 '오역하기 쉬운 부분'을 미리 경고(오역 주의).
function trapCard(text) {
  if (!text) return '';
  return `<div class="callout trap"><span class="co-ic">⚠️ 이거 조심! (오역 주의)</span> ${esc(text)}</div>`;
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
// 혼자 풀어보기 — 해설 쪽(오른쪽 페이지): 영어 + 모범 끊어읽기(영어/한글 · / 구분) + 캐치
function practiceExplain(s, idx) {
  return `<div class="sblock">${sentHead(s, idx)}
    ${chunkLines(s.chunks, true)}
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
  const edition = meta.edition || meta.brand || '수능·평가원 독해 훈련';
  const mark = meta.mark || meta.brand || '';                 // 큰 표제(예: 필생보)
  const expandHtml = meta.expandHtml || '';                   // 마크 풀이(예: 필자의 생각이 보이는)
  const main = meta.title || '영어 독해';                      // 메인 타이틀
  const source = meta.source || '';
  const pillars = meta.pillars || ['소재', '필자 주장', '글 구조', '재진술'];
  const heroMark = mark
    ? `<div class="cov-mark">${esc(mark)}</div>${expandHtml ? `<div class="cov-expand">${expandHtml}</div>` : ''}`
    : '';
  const pillarRow = pillars.length
    ? `<div class="cov-pillars">${pillars.map((t) => `<span class="cov-pill">${esc(t)}</span>`).join('<span class="cov-arw">›</span>')}</div>`
    : '';
  const showUse = meta.showUse !== false; // 표지에 사용법 노출 여부(지문 모드는 false → 목차 페이지로)
  return `<section class="cover">
    <div class="cov-deco"></div>
    <div class="cov-top"><span class="cov-edition">${esc(edition)}</span></div>
    <div class="cov-hero">
      ${heroMark}
      <div class="cov-main">${esc(main)}</div>
      <div class="cov-rule"></div>
      ${pillarRow}
    </div>
    ${source ? `<div class="cov-src">${esc(source)}</div>` : ''}
    ${showUse ? useboxHtml(meta) : ''}
  </section>`;
}

// 📌 쌤이 알려주는 사용법 박스(표지 또는 목차 페이지에서 재사용)
function useboxHtml(meta = {}) {
  const steps = meta.useSteps || ['지문 통째로 읽고', '한 문장씩 어휘·팁·이거조심 보고', '해석·캐치 직접 쓰고', '지문 끝 답지로 맞춰보기!'];
  return `<div class="usebox">
    <div class="useh">📌 쌤이 알려주는 사용법</div>
    <p>${esc(meta.useIntro || '지문 한 편을 통째로 이해하는 훈련이야. 순서대로만 따라와.')}</p>
    <div class="usesteps">
      ${steps.map((t, i) => `<div class="ustep"><b>${CIRCLED[i]}</b> ${esc(t)}</div>`).join('')}
    </div>
    <p class="fine">${meta.useFine || '캐치는 매 문장 <b>한 줄</b>로 — 누가/무엇이 → 어쨌다. 이렇게 <b>소재·필자 주장·글 구조·재진술</b>을 잡는 게 목표야.'}</p>
  </div>`;
}

// 목차 + 사용법 페이지 (표지 다음). 목차는 STEP 1(원리) / STEP 2(지문)로 구성.
function tocPageHtml(passages, meta = {}) {
  const guideRows = [
    ['🎯', '독해 태도', '점수는 태도에서 나온다'],
    ['🎚️', '완급조절', 'OLD / NEW·MAIN / SUPPORT'],
    ['🧩', '추론 — 어순·구두점', '모르는 건 추론한다'],
    ['🔗', '연결사 지도', 'Switching vs Contrast'],
    ['🔁', '재진술', '같은 말을 알아채기'],
    ['🔄', '재진술 5변환·함정', '정답이 만들어지는 법'],
    ['🏗️', '글의 구조', '6가지 글의 틀'],
    ['🗣️', '±어휘 사전 ①', '긍정·부정 어휘'],
    ['🔀', '±어휘 사전 ②', '방향 전환·적용'],
    ['➡️', '논리관계 구문 ①', '인과 · 등호'],
    ['⚖️', '논리관계 구문 ②', '대조 · 비교'],
    ['🖍️', '형광펜 신호 사전', '무엇을 읽고 버릴까'],
  ].map((r, i) => `<div class="mg-row"><span class="mg-n">${String(i + 1).padStart(2, '0')}</span><span class="mg-name">${esc(r[1])}</span><span class="mg-tag">${esc(r[2])}</span></div>`).join('');
  const passRows = (passages || []).map((p, i) => `<div class="mg-row alt"><span class="mg-n">${i + 1}</span><span class="mg-name">${esc(p.title || `지문 ${i + 1}`)}</span><span class="mg-tag">${esc(p.source || '지문')}</span></div>`).join('');
  return `<section class="chapter tocpage">
    <div class="chhead"><span class="daypill">${esc(meta.mark || '필생보')}</span><span class="tagpill">이 책 사용법 &amp; 목차</span></div>
    <h1>목차 · Contents</h1>
    <div class="chsub">먼저 독해 원리를 익히고 → 지문으로 훈련하는 순서야</div>
    <div class="mg-step">STEP 1 — 먼저 익히는 독해 원리</div>
    ${guideRows}
    <div class="mg-step alt">STEP 2 — 지문으로 훈련 · 지문 ${(passages || []).length}편</div>
    ${passRows}
    ${useboxHtml(meta)}
  </section>`;
}

function css() {
  return `
  * { box-sizing: border-box; }
  html,body { margin:0; }
  body { font-family:"NanumSquareRound","Noto Sans KR","Malgun Gothic",sans-serif;
    color:${C.ink}; font-size:11.5px; line-height:1.5; }
  .chapter { break-before: page; page-break-before: always; padding: 2px; }
  .cover { text-align:center; position:relative; padding-top:70px; overflow:hidden; }
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
  .callout { border-radius:6px; padding:8px 12px; margin:7px 0; font-size:10.8px; break-inside:avoid; }
  .callout.catch { background:${C.mint}; border:1px solid ${C.greenLine}; }
  .callout.tip { background:${C.tipBg}; border-left:4px solid ${C.tipBar}; color:#555; }
  .callout.trap { background:${C.trapBg}; border:1px solid ${C.trapLine}; border-left:4px solid ${C.trapBar}; color:#7a4a12; }
  .co-ic { font-weight:800; margin-right:6px; }
  .callout.catch .co-ic { color:${C.tealDark}; }
  .callout.trap .co-ic { color:${C.trapBar}; }
  /* ── 표지(프리미엄) ── */
  .cov-deco { position:absolute; top:-160px; left:50%; transform:translateX(-50%);
    width:520px; height:520px; border-radius:50%;
    background:radial-gradient(circle at 50% 40%, ${C.mint} 0%, rgba(234,246,236,.35) 55%, rgba(234,246,236,0) 72%); z-index:0; }
  .cov-top { position:relative; z-index:1; margin-bottom:26px; }
  .cov-edition { display:inline-block; letter-spacing:3px; font-size:11px; font-weight:800; color:${C.tealDark};
    border:1.5px solid ${C.teal}; border-radius:20px; padding:5px 18px; background:#fff; }
  .cov-hero { position:relative; z-index:1; }
  .cov-mark { font-size:76px; font-weight:800; letter-spacing:6px; color:${C.teal}; line-height:1.05;
    text-shadow:0 2px 0 rgba(30,122,64,.12); }
  .cov-expand { font-size:15px; font-weight:700; color:${C.sub}; letter-spacing:2px; margin-top:6px; }
  .cov-expand .cov-hl { color:${C.teal}; font-weight:800; }
  .cov-main { font-size:30px; font-weight:800; color:${C.ink}; letter-spacing:8px; margin-top:12px; }
  .cov-rule { width:64px; height:4px; border-radius:3px; background:${C.teal}; margin:16px auto 14px; }
  .cov-pillars { display:flex; align-items:center; justify-content:center; gap:8px; flex-wrap:wrap; }
  .cov-pill { font-size:12px; font-weight:800; color:${C.tealDark}; background:${C.mint};
    border:1px solid ${C.greenLine}; border-radius:20px; padding:4px 14px; }
  .cov-arw { color:${C.teal}; font-weight:800; font-size:13px; }
  .cov-src { position:relative; z-index:1; color:${C.sub}; font-size:11.5px; font-style:italic; margin:22px 0 40px; }
  /* ── 목차 페이지 ── */
  /* 목차 — 매거진 인덱스(큰 번호) */
  .mg-step { font-weight:800; font-size:13px; color:${C.teal}; letter-spacing:.5px; margin:16px 0 4px; }
  .mg-step.alt { color:${C.gram}; margin-top:22px; }
  .mg-row { display:flex; align-items:baseline; gap:14px; padding:9px 4px; border-bottom:1px solid #eef2ee; }
  .mg-n { flex:none; width:40px; font-size:22px; font-weight:800; color:${C.teal}; line-height:1; }
  .mg-row.alt .mg-n { color:${C.gram}; }
  .mg-name { flex:1; font-size:13.5px; font-weight:800; color:${C.ink}; }
  .mg-tag { flex:none; font-size:10.5px; font-weight:600; color:${C.sub}; }
  .tocpage .usebox { margin:20px 0 0; }
  .usebox { position:relative; z-index:1; text-align:left; background:${C.mint}; border:1px solid ${C.greenLine}; border-radius:10px;
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
  .cutgrid { display:flex; flex-direction:column; gap:8px; margin:10px 0; }
  .cutcard { border:1px solid ${C.line}; border-left:5px solid ${C.teal}; border-radius:7px;
    padding:9px 13px; background:#fbfdfb; break-inside:avoid; }
  .cut-top { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
  .cut-n { display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px;
    border-radius:50%; background:${C.teal}; color:#fff; font-size:11px; font-weight:800; }
  .cut-name { font-weight:800; font-size:13px; }
  .cut-trig { color:${C.tealDark}; font-size:10.5px; font-weight:700; background:${C.mint};
    border:1px solid ${C.greenLine}; border-radius:10px; padding:1px 9px; }
  .cut-rule { font-size:11px; color:#333; }
  .cut-ex { font-size:10.8px; line-height:1.5; color:${C.sub}; margin-top:2px; }
  .cutcard.gram { border-left-color:${C.gram}; background:${C.gramBg}; }
  .cut-n.gram { background:${C.gram}; }
  .cutcard.pos { border-left-color:${C.teal}; background:${C.mint}; }
  .cutcard.neg { border-left-color:${C.key}; background:${C.keyBg}; }
  .cut-n.pos { background:${C.teal}; } .cut-n.neg { background:${C.key}; } .cut-n.neu { background:${C.sub}; }
  /* 독해 원리(PART0) 페이지 공용 — 가독성 위주(넉넉한 글자·여백) */
  .ptable { border:1px solid ${C.line}; margin:11px 0; font-size:11.5px; border-radius:6px; overflow:hidden; }
  .ptable th { background:${C.teal}; color:#fff; text-align:left; padding:7px 11px; font-weight:800; font-size:11.5px; }
  .ptable td { padding:8px 11px; border-top:1px solid ${C.line}; vertical-align:top; line-height:1.7; }
  .ptable td.k { font-weight:800; color:${C.ink}; white-space:nowrap; width:1%; }
  .ptable tr:nth-child(even) td { background:${C.zebra}; }
  .pex { background:#fff; border:1px solid ${C.line}; border-left:4px solid ${C.teal}; border-radius:6px; padding:9px 12px; margin:8px 0 3px; }
  .pex-lab { font-size:10px; font-weight:800; color:#fff; background:${C.tealDark}; border-radius:9px; padding:2px 9px; margin-right:7px; }
  .pex-en { font-size:12.5px; font-weight:700; font-style:italic; color:#222; }
  .pex-note { font-size:11px; color:#555; margin-top:5px; line-height:1.6; }
  .flow3 { display:flex; align-items:stretch; gap:8px; margin:14px 0; }
  .fl { flex:1; border-radius:9px; padding:12px 13px; text-align:center; }
  .fl .fl-h { font-weight:800; font-size:13px; margin-bottom:6px; }
  .fl .fl-b { font-size:11.3px; line-height:1.6; }
  .fl.old { background:#f4f5f6; border:1px solid #d6d8dc; } .fl.old .fl-h { color:${C.sub}; }
  .fl.new { background:${C.mint}; border:1px solid ${C.greenLine}; } .fl.new .fl-h { color:${C.tealDark}; }
  .fl.sup { background:${C.plusBg}; border:1px solid ${C.trapLine}; } .fl.sup .fl-h { color:${C.plus}; }
  .fl-arw { align-self:center; color:${C.teal}; font-weight:800; font-size:18px; }
  /* 완급조절 워크드 예시 — 문장별 OLD/MAIN/SUPPORT 분해 */
  .wex { border:1px solid ${C.greenLine}; border-radius:10px; padding:4px 0 10px; margin:12px 0; overflow:hidden; }
  .wex-h { background:${C.teal}; color:#fff; font-weight:800; font-size:12.5px; padding:8px 14px; margin-bottom:8px; }
  .wex-row { display:flex; align-items:center; gap:11px; padding:8px 14px; }
  .wex-row + .wex-row { border-top:1px solid #eef1ee; }
  .wex-row.old { background:#f6f7f8; } .wex-row.main { background:${C.mint}; } .wex-row.sup { background:${C.plusBg}; }
  .wex-tag { flex:none; width:96px; text-align:center; font-size:10px; font-weight:800; color:#fff; border-radius:11px; padding:3px 0; }
  .wex-tag.old { background:${C.sub}; } .wex-tag.main { background:${C.teal}; } .wex-tag.sup { background:${C.plus}; }
  .wex-s { flex:1; font-size:12.5px; color:#1a1a1a; line-height:1.5; }
  .wex-s u { text-decoration-color:${C.key}; text-underline-offset:2px; font-weight:800; }
  .wex-k { flex:none; width:190px; font-size:10px; color:#555; line-height:1.45; }
  .wex-note { font-size:11px; color:#444; padding:8px 14px 0; line-height:1.6; }
  .flipbox { background:${C.trapBg}; border:1px solid ${C.trapLine}; border-left:5px solid ${C.trapBar}; border-radius:8px; padding:11px 14px; margin:12px 0 4px; }
  .flip-h { font-weight:800; font-size:12.5px; color:${C.trapBar}; margin-bottom:7px; }
  .flip-row { font-size:11.3px; line-height:1.85; margin:4px 0; } .flip-row b { color:${C.ink}; }
  .flip-row .pp { color:${C.teal}; } .flip-row .nn { color:${C.key}; }
  .hs-grid { display:flex; flex-direction:column; gap:6px; margin:11px 0; }
  .hs-row { display:grid; grid-template-columns:104px 1fr 154px; gap:11px; align-items:baseline;
    background:#fff; border:1px solid ${C.line}; border-left:4px solid ${C.plus}; border-radius:7px; padding:8px 12px; }
  .hs-h { font-weight:800; font-size:11.8px; color:${C.ink}; }
  .hs-w { font-size:10.8px; font-weight:600; color:#333; line-height:1.65; }
  .hs-m { font-size:10.5px; font-weight:700; color:${C.tealDark}; line-height:1.4; }
  /* 필자 입장 신호어 — 칩(태그) 그리드. 칩 글씨는 검은색, 카테고리는 테두리색으로 구분 */
  .b-block { border-radius:10px; padding:0 0 10px; margin:11px 0; overflow:hidden; }
  .b-block.pos { background:#EFF6F1; border:1px solid ${C.greenLine}; }
  .b-block.neg { background:#FDF3F1; border:1px solid ${C.trapLine}; }
  .b-block.neu { background:#f6f7f8; border:1px solid #d6d8dc; }
  .b-head { font-weight:800; font-size:12.5px; color:#fff; padding:8px 13px; margin-bottom:8px; }
  .b-block.pos .b-head { background:${C.teal}; }
  .b-block.neg .b-head { background:${C.key}; }
  .b-block.neu .b-head { background:${C.sub}; }
  .b-note { font-size:10.3px; color:#555; padding:0 13px 6px; }
  .chgrp { display:flex; gap:9px; padding:4px 13px; align-items:baseline; }
  .chgrp-lab { flex:none; width:82px; font-weight:800; font-size:10.5px; color:#444; padding-top:3px; }
  .chips { flex:1; display:flex; flex-wrap:wrap; gap:4px; }
  .chip { font-size:10.6px; font-weight:700; color:${C.ink}; background:#fff; border-radius:11px; padding:3px 10px; }
  .chip.pos { border:1px solid #93c7a6; }
  .chip.neg { border:1px solid #eeb98f; }
  .chip.neu { border:1px solid #cfd3d8; }
  .st-sig { font-size:10px; color:${C.gram}; font-weight:700; margin:2px 0; line-height:1.45; }
  .daypill.gram { background:${C.gram}; }
  .goal.gram { background:${C.gramBg}; border-left-color:${C.gram}; }
  .goal-ic.gram { background:${C.gram}; }
  .structbox { background:${C.gramBg}; border:1px solid #ddd4f2; border-left:5px solid ${C.gram};
    border-radius:8px; padding:11px 14px; margin:6px 0 12px; break-inside:avoid; }
  .st-h { font-weight:800; font-size:13px; color:${C.gram}; margin-bottom:8px; }
  .st-hint { font-weight:600; color:${C.sub}; font-size:9.7px; margin-left:5px; }
  .st-opts { display:flex; flex-wrap:wrap; gap:7px 14px; margin-bottom:9px; }
  .st-opt { display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:700; color:#333; }
  .st-box { width:13px; height:13px; border:1.6px solid ${C.gram}; border-radius:3px; background:#fff; display:inline-block; }
  .st-why { font-size:10.3px; color:${C.sub}; }
  .st-line { display:inline-block; border-bottom:1px solid #b9b1d6; min-width:210px; vertical-align:bottom; }
  .st-line.long { min-width:340px; }
  .stance-tip { margin-top:8px; padding:8px 11px; background:#faf9fe; border:1px dashed #d6cdf0;
    border-radius:7px; display:flex; flex-direction:column; gap:4px; }
  .stance-row { font-size:10.4px; color:#4b4b57; line-height:1.5; }
  .stag { display:inline-block; color:#fff; font-weight:800; font-size:9.5px; padding:1px 8px;
    border-radius:9px; margin-right:6px; }
  .stag.pos { background:${C.teal}; } .stag.neg { background:${C.key}; } .stag.neu { background:${C.sub}; }
  .structbox + .structbox { margin-top:-4px; }
  .para-q { font-size:11.3px; margin:5px 0; }
  .para-eq { color:${C.gram}; font-weight:800; margin:0 4px; }
  /* 재진술 '사슬' 잇기 — 첫 표현 + 빈칸(A→A′→A″) */
  .ch-row { margin:8px 0; padding:8px 11px; background:#fff; border:1px solid #e4ddf5; border-radius:7px; }
  .ch-kw { display:inline-block; background:${C.gram}; color:#fff; font-size:10px; font-weight:800;
    padding:1px 9px; border-radius:10px; margin-bottom:6px; }
  .ch-flow { display:flex; flex-wrap:wrap; align-items:center; gap:6px; }
  .ch-first { font-weight:800; color:${C.ink}; font-size:11.4px; background:${C.mint};
    border:1px solid ${C.greenLine}; border-radius:6px; padding:3px 9px; }
  .ch-arrow { color:${C.gram}; font-weight:800; }
  .ch-blank { flex:1; min-width:120px; border-bottom:1px dashed #b9b1d6; height:18px; }
  /* 재진술 사슬 정답(해설) */
  .rv-chain { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:3px 0 2px; }
  .rv-link { font-size:11.3px; font-weight:700; color:${C.ink}; background:#fff;
    border:1px solid #e4ddf5; border-radius:6px; padding:3px 9px; }
  .rv-arrow { color:${C.gram}; font-weight:800; }
  .struct-reveal { background:${C.gramBg}; border:1px solid #ddd4f2; border-left:5px solid ${C.gram};
    border-radius:8px; padding:10px 14px; margin:12px 0 4px; font-size:11.3px; break-inside:avoid; }
  .sr-h { display:block; font-weight:800; color:${C.gram}; margin-bottom:5px; font-size:12.5px; }
  .pr-line { margin:3px 0; }
  .pr-lab { font-weight:800; color:${C.gram}; margin-right:6px; }
  /* 해석 전 예측 — 정답 해설지 (별도 페이지 · 항목별 카드로 가독성↑) */
  .revealpage { break-before: page; page-break-before: always; padding:2px; }
  .rv-head { display:flex; align-items:center; flex-wrap:wrap; gap:5px 10px;
    margin-bottom:14px; padding-bottom:9px; border-bottom:2px solid ${C.gram}; }
  .rv-badge { background:${C.gram}; color:#fff; font-weight:800; font-size:12px; padding:4px 13px; border-radius:20px; }
  .rv-htitle { font-weight:800; font-size:15px; color:${C.ink}; }
  .rv-hint { color:${C.sub}; font-size:10px; }
  .rv-item { background:${C.gramBg}; border:1px solid #ddd4f2; border-left:5px solid ${C.gram};
    border-radius:9px; padding:11px 15px 12px; margin:10px 0; break-inside:avoid; }
  .rv-top { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
  .rv-ic { font-size:15px; }
  .rv-lab { font-weight:800; font-size:13.5px; color:${C.gram}; letter-spacing:.2px; }
  .rv-main { font-size:12.5px; line-height:1.65; color:${C.ink}; }
  .rv-stance { display:inline-block; background:${C.gram}; color:#fff; font-size:11.5px;
    font-weight:800; padding:2px 11px; border-radius:12px; }
  .rv-why { font-size:11.5px; line-height:1.65; color:#4b4b57; margin-top:6px;
    padding-top:6px; border-top:1px dashed #d6cdf0; }
  .rv-paras { display:flex; flex-direction:column; gap:6px; margin-top:2px; }
  .rv-para { display:flex; align-items:baseline; gap:8px; background:#fff;
    border:1px solid #e4ddf5; border-radius:6px; padding:6px 10px; font-size:11.5px; line-height:1.6; }
  .rv-a { flex:1; font-weight:700; color:${C.ink}; }
  .rv-eq { flex:none; color:${C.gram}; font-weight:800; }
  .rv-b { flex:1; color:#4b4b57; }
  .rv-why-para { margin:1px 0 3px; padding:4px 10px 5px; font-size:10.6px; line-height:1.55;
    color:#5b5b66; background:#faf9fe; border:1px dashed #d6cdf0; border-radius:6px; }
  .rv-why-ic { font-weight:800; color:${C.gram}; margin-right:4px; }
  .rv-theme { margin:8px 0 3px; font-size:11.5px; font-weight:800; color:#fff;
    background:${C.gram}; display:inline-block; padding:2px 12px; border-radius:11px; }

  /* ══ PART 0 · 독해의 원리(업로드 PART0 1:1 재현) ══ */
  .part0 h1 { display:none; }
  .phead { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .ppill { flex:none; background:${C.tealDark}; color:#fff; font-weight:800; font-size:10.5px;
    letter-spacing:.3px; padding:5px 12px; border-radius:6px; }
  .ph-title { flex:1; font-size:18px; font-weight:800; color:${C.tealDark}; line-height:1.2; }
  .ph-no { flex:none; font-size:10.5px; font-weight:700; color:#b7c1ba; }
  .phrule { height:3px; background:${C.teal}; border-radius:2px; margin:0 0 12px; }
  .phero { background:${C.mint}; border-left:5px solid ${C.teal}; border-radius:6px;
    padding:11px 15px; font-size:11.6px; line-height:1.72; color:${C.ink}; margin-bottom:4px; }
  .phero b { color:${C.tealDark}; }
  .pfoot { text-align:center; font-size:8.5px; color:#c2cbc4; margin-top:16px; }
  .psec { border-left:5px solid ${C.teal}; padding-left:10px; margin:15px 0 7px;
    font-weight:800; font-size:13.5px; color:${C.tealDark}; }
  .pbul { list-style:none; margin:5px 0 4px; padding:0; }
  .pbul li { position:relative; padding:3px 0 3px 17px; font-size:11.4px; line-height:1.7; color:${C.ink}; }
  .pbul li::before { content:'›'; position:absolute; left:2px; top:3px; color:${C.teal}; font-weight:800; }
  .ktag { display:inline-block; color:#fff; font-size:9px; font-weight:800; padding:1px 7px; border-radius:9px; vertical-align:1px; }
  .ktag.g { background:${C.teal}; } .ktag.o { background:${C.plus}; }
  .pcatch .pc-warn { display:block; margin-top:4px; font-size:10.4px; color:${C.key}; font-weight:700; }
  /* 기출 예시 인용 박스 */
  .qbox { background:${C.mint}; border:1px solid ${C.greenLine}; border-radius:8px; padding:8px 12px; margin:8px 0; }
  .qbox .q-top { line-height:1.55; }
  .q-lab { display:inline-block; font-size:9px; font-weight:800; color:#fff; background:${C.tealDark};
    border-radius:9px; padding:1px 8px; margin-right:5px; white-space:nowrap; }
  .q-cite { font-size:9px; font-weight:800; color:${C.gram}; margin-right:5px; white-space:nowrap; }
  .q-en { font-size:11.6px; color:#1a1a1a; }
  .q-en .ol { background:#eef0f1; padding:0 3px; border-radius:3px; color:${C.sub}; font-weight:700; }
  .q-hl { background:#FFF0A6; padding:0 2px; border-radius:3px; }
  .q-note { font-size:10.3px; color:#555; margin-top:4px; line-height:1.55; }
  .qcols { display:flex; gap:10px; align-items:stretch; }
  .qcols .qbox { flex:1; margin:8px 0 0; }
  /* 태도/연결사 상단 컬러 카드 */
  .tgrid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:11px 0 4px; }
  .tcard { border:1px solid ${C.line}; border-top:4px solid ${C.teal}; border-radius:8px; padding:11px 13px; background:#fff; }
  .tcard.sw { border-top-color:${C.key}; } .tcard.co { border-top-color:#3B6BB0; }
  .tbadge { display:inline-block; font-size:9.5px; font-weight:800; color:#fff; border-radius:11px; padding:2px 11px; margin-bottom:6px; }
  .tbadge.sw { background:${C.key}; } .tbadge.co { background:#3B6BB0; }
  .tcard-t { font-weight:800; font-size:12.5px; color:${C.ink}; margin-bottom:3px; }
  .tcard-d { font-size:10.6px; color:#444; line-height:1.6; }
  /* 완급조절 흐름 3박스(OLD/NEW·MAIN/SUPPORT) — .flow3 재사용, old 배경 회색 */
  .flow3 .fl.old { background:#f4f5f6; border:1px solid #e2e5e3; } .flow3 .fl.old .fl-h { color:${C.sub}; }
  /* +/- 어휘 방향 헤더 카드 */
  .dirgrid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:11px 0 6px; }
  .dircard { border-radius:8px; padding:10px 13px; }
  .dircard.pos { background:#EFF6F1; border:1px solid ${C.greenLine}; }
  .dircard.neg { background:#FDF3F1; border:1px solid ${C.trapLine}; }
  .dir-h { font-weight:800; font-size:12.5px; margin-bottom:4px; }
  .dircard.pos .dir-h { color:${C.teal}; } .dircard.neg .dir-h { color:${C.key}; }
  .dir-d { font-size:10.5px; color:#444; line-height:1.55; }
  .voca-h { font-weight:800; font-size:12.5px; margin:12px 0 5px; }
  .voca-h.pos { color:${C.teal}; } .voca-h.neg { color:${C.key}; }
  .voca-badge { display:inline-block; width:17px; height:17px; line-height:17px; text-align:center;
    color:#fff; border-radius:50%; font-size:10px; font-weight:800; margin-right:4px; }
  .voca-badge.pos { background:${C.teal}; } .voca-badge.neg { background:${C.key}; }
  .ptable.voca td.k { color:${C.tealDark}; }
  .ptable.voca.neg th { background:${C.key}; } .ptable.voca.neg td.k { color:${C.key}; }
  .ptable .chips { display:flex; flex-wrap:wrap; gap:4px; }
  /* 극성/판정 칩 */
  .pchip { display:inline-block; background:${C.teal}; color:#fff; font-weight:800; font-size:9.5px; padding:0 6px; border-radius:9px; }
  .nchip { display:inline-block; background:${C.key}; color:#fff; font-weight:800; font-size:9.5px; padding:0 6px; border-radius:9px; }
  .dim { color:${C.sub}; font-weight:600; font-size:10px; }
  .pnote.flip { background:${C.trapBg}; }
  /* 오렌지 노트 박스 */
  .pnote { background:${C.trapBg}; border:1px solid ${C.trapLine}; border-radius:8px;
    padding:9px 13px; margin:10px 0; font-size:10.8px; line-height:1.65; color:#6a4d12; }
  .pnote-ic { font-weight:800; color:${C.trapBar}; margin-right:5px; white-space:nowrap; }
  /* 글의 구조 6카드 */
  .scardgrid { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin:11px 0 4px; }
  .scard { border:1px solid ${C.line}; border-left:4px solid ${C.teal}; border-radius:8px; padding:9px 12px; background:#fff; break-inside:avoid; }
  .sc-top { display:flex; align-items:center; gap:7px; margin-bottom:5px; }
  .sc-n { flex:none; width:19px; height:19px; line-height:19px; text-align:center; background:${C.teal}; color:#fff; border-radius:50%; font-size:11px; font-weight:800; }
  .sc-name { font-weight:800; font-size:12px; color:${C.ink}; }
  .sc-sig { font-size:9.8px; color:#3a4640; line-height:1.55; margin:1px 0; }
  .sc-mag { color:${C.teal}; font-weight:800; } .sc-arw { color:${C.key}; font-weight:800; }
  .sc-flow { font-size:10.5px; color:${C.ink}; font-weight:700; margin:4px 0 2px; }
  .sc-ex { font-size:9.6px; color:${C.sub}; font-style:italic; }
  /* A/B 배지 칩 (논리관계) */
  .abchips { display:flex; flex-wrap:wrap; gap:5px; margin:2px 0 4px; }
  .abchip { display:inline-flex; align-items:center; gap:4px; font-size:10.3px; font-weight:600;
    color:${C.ink}; background:#fff; border:1px solid ${C.line}; border-radius:7px; padding:3px 8px; }
  .ab-badge { display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center;
    color:#fff; font-size:9px; font-weight:800; border-radius:4px; padding:0 2px; }
  .ab-a { background:${C.teal}; } .ab-b { background:${C.plus}; }
  .abgrp-lab { font-size:11px; font-weight:800; color:${C.tealDark}; margin:9px 0 4px; }
  .abgrp-lab .sub { font-weight:600; color:${C.sub}; font-size:9.6px; margin-left:5px; }
  .ab-leg { font-size:10px; color:#444; margin:3px 0 2px; }
  .ab-note { font-size:9.8px; color:${C.sub}; margin:4px 0 2px; line-height:1.5; }
  .rel-sec { font-size:13px; color:${C.tealDark}; margin:13px 0 5px; }
  .rel-ic { display:inline-block; width:20px; height:20px; line-height:20px; text-align:center;
    color:#fff; border-radius:5px; font-weight:800; font-size:12px; margin-right:5px; vertical-align:2px; }
  .rel-ic.cause { background:${C.teal}; } .rel-ic.eq { background:#3B6BB0; }
  /* 대조·비교 관계 그룹 */
  .relgrp { margin:8px 0; break-inside:avoid; }
  .rel-lab { display:inline-block; font-size:11px; font-weight:800; color:#fff; border-radius:6px; padding:3px 11px; margin-bottom:5px; }
  .rel-lab .rel-sub { font-weight:600; opacity:.92; margin-left:7px; font-size:9.6px; }
  .rel-gt { background:${C.plus}; } .rel-lt { background:${C.tealDark}; } .rel-diff { background:${C.key}; }
  .rel-sub2 { background:#3B6BB0; } .rel-focus { background:${C.teal}; }
  /* 형광펜 포스터(요약면) */
  .poster-page { padding:2px; }
  .poster-title { text-align:center; font-weight:800; font-size:17px; color:${C.tealDark}; margin:2px 0 3px; }
  .poster-sub { text-align:center; font-size:10.3px; color:${C.sub}; margin-bottom:11px; }
  .poster { border:2px solid ${C.teal}; border-radius:12px; padding:13px 16px; }
  .poster-h { font-weight:800; font-size:14px; color:${C.tealDark}; margin-bottom:3px; }
  .poster-lead { font-size:10px; color:${C.sub}; margin-bottom:10px; }
  .poster-cols { display:grid; grid-template-columns:1fr 1fr; gap:9px 18px; }
  .poster-col { display:flex; flex-direction:column; gap:9px; }
  .sig { break-inside:avoid; }
  .sig-h { display:inline-block; font-size:10.3px; font-weight:800; color:#fff; background:${C.teal}; border-radius:10px; padding:1px 9px; margin-bottom:2px; }
  .sig-h.skip { background:${C.sub}; }
  .sig-w { font-size:9.3px; font-style:italic; color:#333; line-height:1.5; }
  .sig-m { font-size:9.4px; font-weight:700; color:${C.tealDark}; margin:1px 0; }
  .sig-ex { font-size:9.1px; color:#2a5c40; background:${C.mint}; border-radius:5px; padding:3px 7px; margin-top:2px; line-height:1.45; }
  .poster-steps { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-top:12px; }
  .pstep { border:1px solid ${C.greenLine}; border-radius:8px; padding:9px 11px; background:${C.mint}; }
  .pstep-n { display:inline-block; width:17px; height:17px; line-height:17px; text-align:center; background:${C.teal}; color:#fff; border-radius:50%; font-size:9.5px; font-weight:800; margin-right:5px; }
  .pstep-t { font-weight:800; font-size:11px; color:${C.tealDark}; }
  .pstep-d { font-size:9.6px; color:#444; margin-top:3px; line-height:1.5; }
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
    ${interpretWriteCard()}
    ${catchWriteCard()}
    ${trapCard(s.trap)}</div>`;
}
// 글의 구조 유형(학생이 해석 전에 하나 고름)
const STRUCTURE_TYPES = [
  '통념 → 반박(반전)',
  '주장 → 근거·예시',
  '문제 → 해결(방안)',
  '비교 · 대조',
  '시간 · 순서(나열)',
  '예시 → 일반화(결론)',
];
// 🔎 소재 — 이 지문 뭐에 관한 글인지 한 줄로(직접)
function subjectCard() {
  return `<div class="structbox">
    <div class="st-h">🔎 소재 — 이 지문, 뭐에 관한 글이야? <span class="st-hint">한 줄로 써봐 · 정답은 지문 끝</span></div>
    <div class="wl"></div></div>`;
}
// 🗣️ 필자 주장 — 필자 입장(긍정/부정/중립) 고르기 + 판별 힌트(평가어·마지막 문장)
function claimCard() {
  const opts = ['긍정적', '부정적·비판적', '중립적'].map((t) => `<label class="st-opt"><span class="st-box"></span>${esc(t)}</label>`).join('');
  return `<div class="structbox">
    <div class="st-h">🗣️ 필자 주장 — 긍정 · 부정 · 중립? <span class="st-hint">평가어(형용사)와 마지막 문장으로 판단 · 정답은 지문 끝</span></div>
    <div class="st-opts">${opts}</div>
    <div class="stance-tip">
      <div class="stance-row"><span class="stag pos">긍정</span> 좋다·이롭다·중요하다 / should · thanks to · valuable·effective 같은 <b>칭찬·권장</b></div>
      <div class="stance-row"><span class="stag neg">부정</span> 문제·해롭다 / But·However 로 뒤집기 · overlook·fail · should not 같은 <b>비판·경고</b></div>
      <div class="stance-row"><span class="stag neu">중립</span> 사실을 설명하거나 양쪽을 비교(on the other hand)만 하고 <b>편들지 않음</b></div>
    </div>
  </div>`;
}
// 🧩 글의 구조 고르기 — 해석 전에 전체 흐름 보고 예측(직접 ✓)
function structureChoiceCard() {
  const opts = STRUCTURE_TYPES.map((t) => `<label class="st-opt"><span class="st-box"></span>${esc(t)}</label>`).join('');
  return `<div class="structbox">
    <div class="st-h">🧩 이 글, 어떤 구조야? <span class="st-hint">전체 흐름을 보고 하나에 ✓ (앞 '글의 구조' 페이지 참고)</span></div>
    <div class="st-opts">${opts}</div>
    <div class="st-why">그렇게 본 근거(전환·연결 표현이나 문장 번호): <span class="st-line"></span></div>
  </div>`;
}
// 🔗 재진술 '사슬' — 핵심어 하나가 A→A′→A″ 로 반복 재진술되는 흐름.
//   links 가 2개 이상인 사슬만 남기고, 링크 문자열을 정리한다.
function validChains(p) {
  return (p && Array.isArray(p.paraphrases) ? p.paraphrases : [])
    .map((ch) => ({
      keyword: ch && ch.keyword ? String(ch.keyword) : '',
      why: ch && ch.why ? String(ch.why) : '',
      links: (ch && Array.isArray(ch.links) ? ch.links : [])
        .filter((v) => v && String(v).trim()).map((v) => String(v).trim()),
    }))
    .filter((ch) => ch.links.length >= 2);
}
// 🔗 재진술 사슬 찾기 — 첫 표현(A)만 주고, 나머지를 지문에서 순서대로 찾아 쓰는 잇기 문제.
function paraphraseCard(p) {
  const chains = validChains(p);
  if (!chains.length) return ''; // 사슬이 없으면 아예 출력하지 않음
  const rows = chains.map((ch) => {
    const kw = ch.keyword ? `<span class="ch-kw">${esc(ch.keyword)}</span>` : '';
    const first = `<span class="ch-first">${esc(ch.links[0])}</span>`;
    const blanks = ch.links.slice(1).map(() =>
      '<span class="ch-arrow">→</span><span class="ch-blank"></span>').join('');
    return `<div class="ch-row">${kw}<div class="ch-flow">${first}${blanks}</div></div>`;
  }).join('');
  return `<div class="structbox">
    <div class="st-h">🔗 재진술 사슬 찾기 <span class="st-hint">첫 표현이 지문에서 같은 뜻으로 어떻게 다시 나오는지 순서대로 찾아 써봐 (정답은 지문 끝)</span></div>
    ${rows}</div>`;
}
// 지문 끝: 해석 전 예측(소재·주장·구조·재진술) 정답 — 별도 페이지, 항목별 카드로 가독성↑
function predictReveal(p) {
  const cards = [];
  const card = (ic, lab, main, why) => `<div class="rv-item">
    <div class="rv-top"><span class="rv-ic">${ic}</span><span class="rv-lab">${esc(lab)}</span></div>
    <div class="rv-main">${main}</div>${why ? `<div class="rv-why">${esc(why)}</div>` : ''}</div>`;

  if (p.topic) cards.push(card('🔎', '소재', esc(p.topic), ''));
  if (p.claim && p.claim.stance) cards.push(card('🗣️', '필자 주장', `<b class="rv-stance">${esc(p.claim.stance)}</b>`, p.claim.why || ''));
  if (p.structure && p.structure.type) cards.push(card('🧩', '글의 구조', `<b class="rv-stance">${esc(p.structure.type)}</b>`, p.structure.why || ''));

  // 재진술 사슬: 있을 때만 출력. 핵심어별로 A→A′→A″ 전체 사슬을 보여줌.
  const chains = validChains(p);
  if (chains.length) {
    const items = chains.map((ch) => {
      const kw = ch.keyword ? `<div class="rv-theme">📂 ${esc(ch.keyword)}</div>` : '';
      const flow = ch.links.map((l, i) =>
        `${i ? '<span class="rv-arrow">→</span>' : ''}<span class="rv-link">${esc(l)}</span>`).join('');
      const whyRow = ch.why ? `<div class="rv-why-para"><span class="rv-why-ic">↳ 변주</span> ${esc(ch.why)}</div>` : '';
      return `${kw}<div class="rv-chain">${flow}</div>${whyRow}`;
    }).join('');
    cards.push(`<div class="rv-item">
      <div class="rv-top"><span class="rv-ic">🔗</span><span class="rv-lab">재진술 사슬 (같은 말)</span></div>
      ${items}</div>`);
  }

  if (!cards.length) return '';
  return `<section class="revealpage">
    <div class="rv-head"><span class="rv-badge">해석 전 예측 · 정답</span>
      <span class="rv-htitle">소재 · 필자 주장 · 글의 구조 · 재진술</span>
      <span class="rv-hint">앞에서 예측한 걸 여기서 맞춰봐</span></div>
    ${cards.join('')}</section>`;
}
// 지문 끝 답지: 문장별 모범 해석(끊어읽기) + 모범 캐치
function passageAnswerKey(p) {
  let h = secHead(CIRCLED[3], '답지 — 해석 · 캐치', '위에서 직접 푼 걸 여기서 맞춰봐', 'key', true);
  h += (p.sentences || []).map((s, i) => {
    const tag = s.src && String(s.src).length <= 10 ? `<span class="stag">[${esc(s.src)}]</span>` : '';
    return `<div class="sblock">
    <div class="senth"><span class="sbadge">${i + 1}</span><span class="sen">${esc(s.en)}</span>${pointTag(s.point)}${tag}</div>
    ${chunkLines(s.chunks, true)}
    ${s.catch ? catchCard(s.catch) : ''}</div>`;
  }).join('');
  return h;
}
function passageHtml(p, idx) {
  let h = '<section class="chapter">';
  h += `<div class="chhead"><span class="daypill">지문 ${idx + 1}</span>
    <span class="tagpill">${esc(p.source || '구문해석')}</span></div>`;
  h += `<h1>${esc(p.title || `지문 ${idx + 1}`)}</h1>`;
  h += '<div class="chsub">필생보 · 필자의 생각이 보이는 영어독해 — 소재·주장·구조·재진술</div>';
  h += secHead(CIRCLED[0], '지문 통째로 읽기', '먼저 전체 흐름을 쭉 훑어봐', 'green');
  h += fullTextBlock(p.sentences);
  h += secHead(CIRCLED[1], '해석 전 예측 — 소재·주장·구조·재진술', '통째로 읽고, 해석 들어가기 전에 먼저 예측해봐! (정답은 지문 끝)', 'gram');
  h += subjectCard() + claimCard() + structureChoiceCard() + paraphraseCard(p);
  h += secHead(CIRCLED[2], '한 문장씩 직접 풀기', '어휘 보고 → 해석·캐치 직접 쓰고 → 오역 주의로 점검 (끊어읽기 원리는 앞 페이지)', 'teal', true);
  h += (p.sentences || []).map((s, i) => passageSentence(s, i + 1)).join('');
  h += passageAnswerKey(p);
  h += predictReveal(p);
  if (p.catch) {
    h += `<div class="pcatch"><span class="pcatch-h">✅ 이 지문, 이 정도는 캐치! (전체 요지)</span>${esc(p.catch)}</div>`;
  }
  h += '</section>';
  return h;
}

// 지문 모드 전체 HTML. passages 는 normalizePassages 결과.
function buildHtmlPassages(passages, meta = {}) {
  const cover = coverHtml({
    edition: meta.edition || '수능·평가원 독해 훈련',
    mark: meta.mark || '필생보',
    // 필·생·보 = 필자의 생각이 보이는 (앞 글자를 브랜드색으로 강조)
    expandHtml: meta.expandHtml || '<b class="cov-hl">필</b>자의 <b class="cov-hl">생</b>각이 <b class="cov-hl">보</b>이는',
    title: meta.title || '영어 독해',
    source: meta.source || '',
    pillars: meta.pillars || ['소재', '필자 주장', '글 구조', '재진술'],
    showUse: false, // 사용법은 표지 다음 '목차 페이지'로
  });
  const uses = {
    mark: meta.mark || '필생보',
    useIntro: '지문 한 편을 통째로 이해하는 훈련이야. 순서대로만 따라와.',
    useSteps: ['지문 통째로 읽고', '한 문장씩 어휘·팁·이거조심 보고', '해석·캐치 직접 쓰고', '지문 끝 답지로 맞춰보기!'],
    useFine: '캐치는 매 문장 <b>한 줄</b>로 — 누가/무엇이 → 어쨌다. 이렇게 <b>소재·필자 주장·글 구조·재진술</b>을 잡는 게 목표야.',
  };
  const front = principlesSectionHtml();
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${fontFaces()}\n${css()}</style></head>`
    + `<body>${cover}${tocPageHtml(passages, uses)}${front}${passages.map((p, i) => passageHtml(p, i)).join('')}</body></html>`;
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

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

// 글의 구조 안내 페이지 (책 앞쪽 별도 페이지, 목차 항목 1회) — 모의고사 지문 기준
// [유형, 통념/앞단계 신호, 반전/뒷단계 신호, 흐름, 예]
const STRUCTURE_GUIDE = [
  ['통념 → 반박(반전)',
    '통념 세팅: many people think/believe · it is widely[commonly] believed · traditionally · we tend to think · most people assume · at first glance',
    '반전: But · However · Yet · In fact · In reality · Contrary to · Nevertheless',
    '흔한 생각(통념)을 깔아둔 뒤 뒤집어 필자 주장을 편다', '“Many people believe X. But in fact, Y.”'],
  ['주장 → 근거·예시',
    '주장: should · must · it is important that · I argue',
    '근거·예시: because · since · for example · for instance · research[studies] show · therefore',
    '주장을 먼저 내세우고 이유·연구·예시로 뒷받침', '“X가 중요하다. 예를 들어 …, 연구에 따르면 …”'],
  ['문제 → 해결(방안)',
    '문제: problem · challenge · issue · difficulty · concern',
    '해결: solution · solve · address · one way to · need to · should',
    '문제를 제기하고 해결책·방안을 제시', '“이런 문제가 있다. 이를 해결하려면 …”'],
  ['비교 · 대조',
    '대조: while · whereas · unlike · in contrast · on the other hand · by contrast',
    '비교: similarly · likewise · just as · like · both … and',
    'A와 B의 공통점·차이점을 견줌', '“A는 …인 반면, B는 …이다.”'],
  ['시간 · 순서(나열)',
    '순서: first · second · next · then · later · after · before · finally',
    '시간: in 1937 · meanwhile · over time · eventually · subsequently',
    '사건·과정을 시간·순서대로(전기·실험·역사)', '“먼저 …, 그다음 …, 마침내 …”'],
  ['예시 → 일반화(결론)',
    '예시: for example · for instance · such as · consider · take … as an example',
    '일반화·결론: thus · therefore · in short · in conclusion · this suggests[shows] · overall',
    '구체 사례들을 든 뒤 일반 원리·결론으로 묶음', '“예: …. 이런 사례들은 결국 …임을 보여준다.”'],
];
function structurePageHtml() {
  const cards = STRUCTURE_GUIDE.map(([name, sig1, sig2, flow, ex], i) => `<div class="cutcard gram">
    <div class="cut-top"><span class="cut-n gram">${CIRCLED[i]}</span><span class="cut-name">${esc(name)}</span></div>
    <div class="st-sig">🔎 ${esc(sig1)}</div>
    <div class="st-sig">↳ ${esc(sig2)}</div>
    <div class="cut-rule">${esc(flow)}</div>
    <div class="cut-ex">예) ${esc(ex)}</div>
  </div>`).join('');
  return `<section class="chapter">
    <div class="chhead"><span class="daypill gram">글의 구조</span><span class="tagpill">모의고사 지문 기준</span></div>
    <h1>글의 구조 — 어떤 짜임이 있나?</h1>
    <div class="chsub">필생보 · 모의고사·수능 독해 지문에 자주 나오는 6가지 글의 틀</div>
    <div class="goal gram"><span class="goal-ic gram">핵심</span> 글의 구조 = 필자가 생각을 배치한 ‘틀’. <b>전환어(But/However…)와 연결어</b>를 신호로 잡으면 구조가 보이고, 구조가 보이면 <b>요지·필자 주장</b>이 빨리 잡혀.</div>
    <div class="cutgrid">${cards}</div>
    <div class="struct-reveal"><span class="sr-h">🧩 이렇게 써먹어</span> 지문마다 ‘글의 구조 — 해석 전에 예측!’에서 이 6개 중 하나를 골라 보고, 지문 끝에서 정답과 맞춰봐.</div>
  </section>`;
}
// 필자 입장 신호 어휘 — Ortica 영어 VOCA(DAY 31 긍정·중요 / DAY 32·33 부정) 전량을
// 뉘앙스별로 묶어 수록. 중립은 '평가어 없음 + 유보/양면'을 명확한 예로 제시.
const STANCE_POS = ['이익·유익', 'benefit · beneficial · fruitful · merit · valuable · priceless · work(효과가 있다)',
  '중요·핵심·필수', 'core · key · point · critical · crucial · essential · integral · indispensable · necessary · fundamental · vital · significant · substantial · prime · principal · prevailing · matter · count · be of importance · relevant',
  '집중·주목', 'center on · concentrate on · focus on · attend to',
  '강조·강화·향상', 'emphasize · stress · enhance · reinforce · prioritize',
  '필요·추구·선호', 'need · require · seek to V · fond of · desirable · in favor of',
  '강조 구문·부사', 'only · invariably · substantially · nothing but · not just A but also B · without A · It is … that V · win out'];
const STANCE_NEG = ['버리다·제거', 'abandon · discard · scrap · drop · remove · eliminate · discharge · leave out · rule out · removal',
  '무시·간과', 'disregard · ignore · overlook · neglect · dismiss',
  '부족·부재·결핍', 'lack · shortage · absence · absent from · free from · incapable of · of little account',
  '제한·회피·벗어남', 'restrict · limit · avoid · sidestep · bypass · shy away from · deviate from · break away from · move away from · disengage from · apart from · aside from · departure from · quit · detach',
  '거절·거부·금지', 'refuse · reject · resist · exclude · deny · say no to · disapprove · discourage · forbid',
  '방해·차단·단절', 'interfere with · stand in the way of · cut off · break with · displace · stop/prevent/keep A from Ving',
  '실패·상실·약화', 'fail · lose out · diminish',
  '비판·의심·이의', 'criticize · question · doubt · obscure · challenge',
  '무가치·문제·결함', 'drawback · downside · side effect · flaw · myth · misleading · worthless · irrelevant · unnecessary · poor · costly · challenging · mere',
  '무관·독립', 'have nothing to do with · have no bearing on · have no idea of · independent of A · independently · immune to · isolation',
  '부정 부사·구문', "hardly · rarely · by no means · don't bother · unlikely to V · allergic to · erroneously · other than · at the price[expense] of · It is of no use to V · It's not so much … but ~ · strip[free] A of B · reluctance · exception"];
const STANCE_NEU = ['유보·추측(단정 회피)', 'may · might · can · tend to · seem · appear · suggest · some · often · in some cases · not necessarily',
  '양면·균형 제시', 'on one hand … on the other hand · while ~ · both A and B · it depends · vary',
  '객관 서술(관찰·보고)', 'describe · explain · report · note · observe · according to · studies show (해석 없이 나열만)'];
// 어휘를 칩(태그)으로 렌더. 칩 안 글씨는 검은색(색은 테두리로만 구분).
function stanceChips(arr, cls) {
  let h = '';
  for (let i = 0; i < arr.length; i += 2) {
    const words = arr[i + 1].split(' · ')
      .map((x) => `<span class="chip ${cls}">${esc(x)}</span>`).join('');
    h += `<div class="chgrp"><span class="chgrp-lab">${esc(arr[i])}</span><span class="chips">${words}</span></div>`;
  }
  return h;
}
function stancePageHtml() {
  return `<section class="chapter">
    <div class="chhead"><span class="daypill key">필자 입장 신호</span><span class="tagpill">긍정·부정 어휘로 태도 읽기</span></div>
    <h1>필자의 입장 — 어떤 어휘로 드러나나?</h1>
    <div class="chsub">필생보 · Ortica 영어 VOCA 기반 · 필자가 대상을 '좋게 / 나쁘게' 보는지는 평가 어휘에서 새어 나온다</div>
    <div class="goal"><span class="goal-ic">핵심</span> 필자가 대상을 두고 쓴 <b>평가 어휘</b>를 잡으면 입장이 보여. 진짜 주장은 보통 <b>마지막 문장</b>(therefore · in conclusion)이나 <b>But · However 뒤</b>, <b>should · must</b> 에서 터져 나와.</div>
    <div class="b-block pos"><div class="b-head">👍 긍정 · 중요 — 필자가 좋게·중요하게 봄</div>${stanceChips(STANCE_POS, 'pos')}</div>
    <div class="b-block neg"><div class="b-head">👎 부정 — 필자가 비판·경계·배제·부정</div>${stanceChips(STANCE_NEG, 'neg')}</div>
    <div class="b-block neu"><div class="b-head">🤔 중립 — 좋다·나쁘다 평가가 없을 때</div>
      <div class="b-note">긍정·부정 평가어가 <b>뚜렷이 없고</b>, 아래처럼 <b>판단을 유보</b>하거나 <b>양쪽을 균형 있게</b> 보여주면 중립이야. (한쪽으로 몰지 않음)</div>
      ${stanceChips(STANCE_NEU, 'neu')}</div>
    <div class="flipbox">
      <div class="flip-h">🔄 ± 방향을 뒤집는 신호 — 놓치면 정반대로 읽는다 (평가원 오답 단골 '반대구조')</div>
      <div class="flip-row"><b>부정·결여·분리</b> not · no · never · no longer · hardly · rarely · by no means · free from · absent from · immune to · independent of · apart from · far from · cease · stop</div>
      <div class="flip-row"><b>전환 예</b> does not shrink = <b class="pp">＋</b>expands · free from bias = <b class="pp">＋</b>객관적 · immune to = <b class="nn">−</b>영향 안 받음 · not necessarily = 약화(반드시 ~는 아님)</div>
    </div>
    <div class="pcatch"><span class="pcatch-h">✅ 이렇게 써먹어</span> 문장 뜻을 다 몰라도 핵심어의 <b>± 방향</b>만 잡으면 요지·함축·정답 선지가 보여. 지문마다 ‘필자 주장’에서 이 방향으로 예측해봐.</div>
  </section>`;
}
// ── 독해의 원리(PART0) — Ortica 영어 '형광펜 독해' 원리 총론을 필생보 스타일로 수록 ──
// 공용 스캐폴드/헬퍼
function ppage(pill, tag, h1, sub, goal, body) {
  return `<section class="chapter">
    <div class="chhead"><span class="daypill key">${esc(pill)}</span><span class="tagpill">${esc(tag)}</span></div>
    <h1>${esc(h1)}</h1>
    <div class="chsub">${esc(sub)}</div>
    ${goal ? `<div class="goal"><span class="goal-ic">핵심</span> ${goal}</div>` : ''}
    ${body}</section>`;
}
function ptable(headers, rows) {
  const th = headers.map((h) => `<th>${esc(h)}</th>`).join('');
  const tb = rows.map((r) => `<tr>${r.map((c, i) => `<td class="${i === 0 ? 'k' : ''}">${c}</td>`).join('')}</tr>`).join('');
  return `<table class="ptable"><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table>`;
}
function pcard(ic, name, body, cls) {
  return `<div class="cutcard ${cls || ''}"><div class="cut-top"><span class="cut-n ${cls || ''}">${ic}</span><span class="cut-name">${esc(name)}</span></div>${body}</div>`;
}
function pex(label, en, note) {
  return `<div class="pex"><span class="pex-lab">${esc(label)}</span> <span class="pex-en">${esc(en)}</span>${note ? `<div class="pex-note">${esc(note)}</div>` : ''}</div>`;
}

// P1 · 독해 태도
function attitudePageHtml() {
  return ppage('독해의 원리 ①', '태도', '모의고사 점수는 ‘태도’에서 나온다',
    '“정확하게 모든 문장을 해석하는 것” ≠ “좋은 점수” — 점수는 글의 중심 내용을 잡은 사람에게 간다',
    '구문을 완벽히 분석한 사람이 아니라, <b>글이 무슨 말을 하려는가</b>를 잡은 사람이 점수를 가져가.',
    pcard('📖', '공부할 때 — 걸어다니는 사전', '<div class="cut-rule">단어·구문을 끝까지 정확히. 실력의 바탕을 쌓는 시간.</div>', 'pos')
    + pcard('✍', '시험 칠 때 — 모르는 건 추론', '<div class="cut-rule">모르는 단어에 멈추지 말고 문맥으로 추론. “무슨 말을 하려는가”만 고민.</div>', 'neg')
    + pcard('🔑', 'HOW — 초반에 멈춰 ‘관통 키워드’를 잡는다', '<div class="cut-rule">글 초반 3문장쯤 읽고 멈춰: <b>세 문장을 관통하는 하나의 키워드</b>는? 반복되는 말을 찾아라. 예시가 있으면 앞 문장과 어떻게 같은지 생각(General → for example Specific).</div>', 'gram')
    + '<div class="pcatch"><span class="pcatch-h">✅ 주제 문제의 정답 원리</span> 키워드는 반드시 선지에 담긴다 — 같은 용어를 쓰지 않더라도. (단, 가장 많이 쓰인 단어가 곧 답인 건 아님)</div>');
}

// P2 · 완급조절 — 한 문장을 OLD(문두 부사절·전치사구) / MAIN(주절) / SUPPORT(분사구문·관계사)로 쪼갠다
function pacePageHtml() {
  const worked = `<div class="wex">
    <div class="wex-h">📖 예시로 나눠보기 — 한 문장을 세 역할로 쪼개봐</div>
    <div class="wex-row old"><span class="wex-tag old">OLD · 부사절</span><span class="wex-s"><u>Although the plan looks simple,</u></span><span class="wex-k">문두 배경(부사절·전치사구) — <b>약하게</b></span></div>
    <div class="wex-row main"><span class="wex-tag main">MAIN · 주절</span><span class="wex-s">it often fails in practice,</span><span class="wex-k">진짜 하고 싶은 말(주절) — <b>가장 강하게</b></span></div>
    <div class="wex-row sup"><span class="wex-tag sup">SUPPORT · 분사구문</span><span class="wex-s"><u>leaving many beginners confused.</u></span><span class="wex-k">뒤에 덧붙인 부연(분사구문·관계사) — <b>약하게</b></span></div>
    <div class="wex-note">▶ 문두 <b>부사절·전치사구</b>(OLD)와 뒤의 <b>분사구문·「,which」관계사</b>(SUPPORT)는 약하게, 가운데 <b>주절(MAIN)</b>에 힘줘 — 이게 완급조절이야.</div>
  </div>`;
  const flow = `<div class="flow3">
    <div class="fl old"><div class="fl-h">OLD (배경)</div><div class="fl-b">문두 <b>부사절·전치사구</b><br>(Although/When/In…) · <b>약하게</b></div></div>
    <div class="fl-arw">→</div>
    <div class="fl new"><div class="fl-h">MAIN (주제)</div><div class="fl-b"><b>주절</b> — 진짜 하고 싶은 말<br><b>가장 강하게</b></div></div>
    <div class="fl-arw">→</div>
    <div class="fl sup"><div class="fl-h">SUPPORT (부연)</div><div class="fl-b">뒤의 <b>분사구문·관계사</b><br>(, -ing/-ed · , which) · <b>약하게</b></div></div>
  </div>`;
  return ppage('독해의 원리 ②', '완급조절', '완급조절 — OLD / MAIN / SUPPORT로 나눠 읽기',
    '모든 문장을 똑같이 강하게 읽을 필요는 없다 · 문장은 주절(MAIN)에 힘이 실린다',
    '문두 배경과 뒤 부연은 약하게, <b>주절</b>에 힘주는 <b>능동적 독해</b>를 하자. 아래처럼 세 역할로 쪼개봐.',
    worked + flow
    + '<div class="cutgrid">'
    + pcard('🔎', 'OLD 신호 — 컴마(,)가 붙은 앞자리', '<div class="cut-rule">문두에서 컴마로 끊기는 <b>부사절(Although~)·전치사구(In~)</b>가 배경(OLD). 컴마가 없으면 주절 핵심일 때가 많다.</div>', 'neg')
    + pcard('✅', 'SUPPORT 신호 — 뒤에 붙는 분사·관계사', '<div class="cut-rule"><b>분사구문(, -ing/-ed)</b>과 <b>「,which」비제한 관계사</b>는 부연 — 약하게. (관계사만 있으면 필요한 정보이니 챙긴다.)</div>', 'pos')
    + '</div>');
}

// P3 · 추론(어순·구두점)
function inferPageHtml() {
  return ppage('독해의 원리 ③', '추론', '모르는 것은 ‘추론’한다 — 어순·구두점',
    '영어는 흔히 General → Specific · 추상적인 말이 앞에 오면 대개 뒤에 구체 정보가 따라온다',
    '모르는 단어에 멈추지 말고 <b>‘뒤가 알려줄 것’</b>이라 믿고 읽어라.',
    pcard('=', '정의를 여는 신호 — BE동사 (A=B)', pex('A=B', 'Tax is the application of a society’s theories of distributive justice.', 'be동사 뒤에서 정의됨 → ‘Tax = 분배 정의 이론의 적용’. 뒤가 알려줄 거라 믿고 읽는다.'), 'gram')
    + '<div class="cutgrid">'
    + pcard(':', '콜론 — 부연·재진술·열거', '<div class="cut-rule">A : B 에서 A가 이해되면 B는 읽을 필요 없이 확인만.</div>')
    + pcard('—', '대쉬 — 상술', '<div class="cut-rule">대쉬 이하는 앞을 상술. 앞이 이해되면 약하게. (중간 삽입=대쉬, 끝=콜론)</div>')
    + pcard(';', '세미콜론 — 두 문장 연결', '<div class="cut-rule">and·but·so 역할. ‘내용상 관련 있구나’만 생각하고 넘긴다.</div>')
    + pcard('“”', '따옴표 — 인용·강조', '<div class="cut-rule">인용·강조, 또는 단어의 본래 의미를 비틀어 쓸 때(필자의 의도).</div>')
    + '</div>'
    + pcard('·', '병렬·나열 [and / or] — 하나만 알면 된다', pex('나열', '…variations in tempo, volume, tonal quality and intonation.', '‘tempo’ 하나만 알아도 ‘여러 변주 요소’ 나열임을 안다 — 나머지는 넘겨도 됨.'), 'pos'));
}

// P4 · 연결사 지도
function connectivePageHtml() {
  return ppage('독해의 원리 ④', '연결사', '연결사 = “어디가 중요한지 알려줄게”',
    '연결사는 문장과 문장의 관계 표지 · 문장 어디에 있든 앞뒤 ‘사이’에 놓고 읽어라',
    '특히 <b>역접</b>은 완급의 분기점이야.',
    '<div class="cutgrid">'
    + pcard('↔', 'Switching — 앞을 뒤집고 뒤가 핵심', '<div class="cut-rule">‘그러나·대신에’ · <b>A ‹ B</b> 뒤가 중요, 앞은 약하게.</div><div class="cut-ex">however · but · still · nevertheless · instead · rather</div>', 'neg')
    + pcard('=', 'Contrast — 두 대상 다 중요', '<div class="cut-rule">‘반면에’ · <b>A = B</b> 비교·대조, 양쪽 다 챙긴다.</div><div class="cut-ex">on the other hand · by contrast · conversely</div>', 'gram')
    + '</div>'
    + ptable(['표현', '1순위', '2순위(놓치기 쉬움)'], [
      ['but / however', '그러나(Switching) / 반면에(Contrast)', '역접 아닐 땐 <b>강조</b>(Emphasis)'],
      ['In fact', '사실상·실제로(순접·강조)', '하지만 사실은(역접)'],
      ['on the contrary', '오히려·도리어(앞 진술 부정·강조)', '≠ on the other hand(반면에)와 혼동 주의'],
      ['on the other hand', '반면에(by contrast)', '다른 한편으로는(첨가)'],
    ]));
}

// P5 · 재진술 원리
function restatePrinciplePageHtml() {
  return ppage('독해의 원리 ⑤', '재진술', '재진술(Paraphrasing) — 같은 말을 알아채기',
    '독해의 최종 기술 = 재진술 · 명시적 단서 없이도 “앞의 그 말을 바꿔 한 거구나”를 느끼는 것',
    '필자는 핵심을 <b>한 번만 말하지 않고</b> 표현을 바꿔 되풀이하고, <b>정답 선지는 그 되풀이의 마지막 한 번</b>이야.',
    '<div class="pcatch" style="margin-top:2px"><span class="pcatch-h">🔁 이 교재에선</span> 지문마다 「재진술 사슬」 문제로 훈련해 — 소재가 하나면 A→A′→A″…, 비교 지문이면 A→A′… · B→B′… 로 두 소재를 나란히. (지문에 실제 되풀이된 만큼만, 억지로 만들지 않음)</div>'
    + ptable(['기능', '방향', '대표 연결사'], [
      ['재진술', 'G/S → 다시 말하면 → G/S', 'that is · in other words · in effect · indeed'],
      ['예시·요약', '일반 ↔ 구체', 'for example · for instance / in short · in conclusion'],
      ['나열·첨가', '같은 주제에 항목을 더함', 'similarly · likewise · also · moreover · furthermore'],
      ['인과', '결과 ← 원인', 'as a result · therefore · thus · hence · so'],
    ])
    + pcard('🧠', '재진술 독해 = G(일반화) ↔ S(구체화)를 오간다', '<div class="cut-rule">서울 = 대한민국의 수도 = 한국에서 천만이 사는 곳 — 표현은 달라도 <b>하나의 범주</b>임을 느끼는 것. 정답 선지는 지문을 이렇게 바꿔 말한다.</div>', 'gram'));
}

// P6 · 재진술 5변환·함정
function transformPageHtml() {
  return ppage('독해의 원리 ⑥', '5변환·함정', '재진술로 정답을 만든다 — 5변환 · 오답 함정',
    '정답 = 뜻은 그대로, 단어만 바꾼다 · 오답 = 단어는 그대로, 뜻을 왜곡한다',
    '그래서 <b>지문 단어가 그대로 보이는 선지부터 의심</b>하고, 표현이 바뀌어 낯선 선지를 정답 후보로 봐.',
    ptable(['평가원 단골 5변환', '지문 표현 → 정답 선지'], [
      ['① 동의어 치환', 'proper · forces · detailed → careful · drives · thorough'],
      ['② 구체 → 추상', 'a songwriter · a boundary → creative people · locality'],
      ['③ 품사 전환', 'decide(동사) → decision-making(명사)'],
      ['④ 반대구조(부정↔긍정)', 'does not shrink → expands'],
      ['⑤ 비유 → 직설', 'a window to other worlds → unfamiliar perspectives'],
    ])
    + ptable(['오답 3초 잣대', '이럴 때 소거'], [
      ['copy · 복사', '지문 단어가 그대로 보여 익숙하다 → 논리·관계가 같은지 재확인'],
      ['reverse · 반대', '단어는 비슷한데 방향이 반대다 → 부정어·인과 방향 대조'],
      ['distort · 왜곡', '90%는 맞는데 한 군데가 어긋난다 → 대상·조건·정도 대조'],
      ['off · 이탈', '그럴듯한데 지문에서 본 적 없다 → 근거 문장 못 짚으면 소거(상식 ≠ 근거)'],
    ])
    + '<div class="pcatch"><span class="pcatch-h">⚠️ 흔한 오해</span> “all·always·only 같은 극단어가 있으면 오답” = 사설·토익식 요령. 평가원은 극단어가 아니라 <b>‘지문 근거와의 관계’</b>로 오답을 만든다.</div>');
}

// P10 · 논리관계 구문 ① 인과·등호
function logicCausePageHtml() {
  return ppage('독해의 원리 ⑦', '논리관계 ①', '논리관계 구문 — 인과(→) · 등호(=)',
    '독해는 결국 문장들의 ‘관계’를 잡는 일 · 관계는 넷뿐 — 인과(→) · 등호(=) · 대조(↔) · 비교(>)',
    '연결사·구두점이 없어도 이 구문들이 같은 <b>신호 역할</b>을 해.',
    pcard('→', '인과 — 원인 → 결과 / 결과 ← 원인', '<div class="cut-rule"><b>원인→결과</b>: A cause / lead to / result in / bring about / give rise to / trigger / contribute to / be the source of B</div><div class="cut-rule"><b>결과←원인</b>: A result from / stem from / arise from / derive from / be based on / be rooted in / attribute A to B · A due to B</div><div class="cut-ex">결과 신호(절): so~that · such~that · it follows that · 명사 outcome · rationale · justification</div>', 'neg')
    + pcard('=', '등호·정의 — A = B (같다·라 부른다·상징한다)', '<div class="cut-rule">A is B · be called / be termed / define A as / refer to A as / represent / embody / illustrate / regard[see·view·treat] A as / identify A with B · be equivalent to</div><div class="cut-ex">여는 신호: that is · i.e. · in short / such as · like · including · e.g. — 한쪽만 이해하면 나머지는 약하게</div>', 'gram'));
}

// P11 · 논리관계 구문 ② 대조·비교
function logicContrastPageHtml() {
  return ppage('독해의 원리 ⑧', '논리관계 ②', '논리관계 구문 — 대조(↔) · 비교(>)',
    '이 표현이 보이면 = 글에 소재가 둘(A·B)이라는 신호 · 뜻을 외우지 말고 관계를 기호로 잡아라',
    '재진술의 <b>비교 지문(A·B 추적)</b>과 바로 연결돼. 필자가 미는 쪽(&gt; · B)이 곧 주제야.',
    '<div class="cutgrid">'
    + pcard('&gt;', 'A &gt; B — A가 우위', '<div class="cut-ex">more A than B · outweigh · surpass · exceed · prevail over · outperform · prefer A to B · A rather than B · A instead of B</div>', 'pos')
    + pcard('&lt;', 'A &lt; B — A가 밀림', '<div class="cut-ex">less A than B · inferior to · be overwhelmed[overcome·overshadowed·dwarfed] by · be sacrificed for</div>', 'neg')
    + pcard('↔', 'A ↔ B — 다름·대조', '<div class="cut-ex">differ from · distinguish[separate·set apart] A from B · contrast with · unlike · whereas · on the other hand · contrary to · the former · the latter</div>', 'gram')
    + pcard('⇒', 'A ⇒ B — 대체·전환', '<div class="cut-ex">replace · displace · be substituted[supplanted] by · give way to · switch to · shift[transition·move] from A to B</div>')
    + '</div>'
    + '<div class="pcatch"><span class="pcatch-h">🎯 초점 못 박기</span> <b>not A but B</b> (not so much A as B / far from A) — B가 필자의 초점, A는 버리는 미끼(−). 예) not the technology but the way we use it.</div>');
}

// P12 · 형광펜 신호 사전
const HIGHLIGHT_SIGNALS = [
  ['① 역접·대조', 'However · But · Yet · Nevertheless · In contrast · On the contrary · Instead · Conversely · Unlike · Whereas · Rather(than) · Still · No longer · not A but B', '앞을 뒤집는다 = 필자의 진짜 주장'],
  ['② 결론·귀결', 'Thus · Therefore · Hence · So · Consequently · As a result · In conclusion · In short · Ultimately · That is why', '글을 닫는 문장 = 주제'],
  ['③ 인과', 'because · since · due to · owing to · lead to · result in · give rise to · thereby · in order to · this is because', '논리의 뼈대(원인 → 결과)'],
  ['④ 강조·주장', 'should · must · ought to · need to · important · essential · crucial · vital · key · In fact · Indeed · above all · especially · notably · clearly', '필자가 대놓고 미는 문장'],
  ['⑤ 최상·유일·한정', 'the most · the best · the only · first · only when · only if · unless · except · as long as', '정답이 숨는 단골 자리'],
  ['⑥ 통념·반전', 'Many believe · It is (often) thought · Traditionally · Contrary to popular belief · Surprisingly · Paradoxically · Ironically', '통념을 깨는 곳 = 주제'],
  ['⑦ 정의·재정의', 'is defined as · means · refers to · that is · in other words · 콜론( : ) · 대시( — ) 뒤', '개념을 못 박는 문장'],
  ['⑧ 태도·평가어(±)', '＋ benefit · advantage · valuable · effective · promising  ↔  − problem · risk · illusion · myth · fail · drawback', '대의·함축·정답의 방향(＋/−)'],
  ['⑨ 예시 후 일반화', 'In each case · In general · Overall · This suggests / shows / means', '예시를 접고 결론으로 복귀'],
  ['⑩ 위치', '글 첫 문장 · 각 단락 첫 문장 · 마지막 문장 · 빈칸/밑줄 문장 + 바로 앞뒤', '신호어 없어도 무조건 읽는 자리'],
  ['⑪ 지시·연결(대용어)', 'this · these · that · those · such (a) · one · another · the former · the latter', '순서·삽입의 핵심 — 앞 문장을 가리킨다'],
  ['⑫ 첨가·병렬', 'not only ~ but also · moreover · furthermore · in addition · as well as · similarly · likewise · just as', '같은 방향 추가·강조(주제 강화)'],
];
function highlightSignalPageHtml() {
  const rows = HIGHLIGHT_SIGNALS.map((s) => `<div class="hs-row"><div class="hs-h">${esc(s[0])}</div><div class="hs-w">${esc(s[1])}</div><div class="hs-m">→ ${esc(s[2])}</div></div>`).join('');
  return ppage('독해의 원리 ⑨', '형광펜 신호 사전', '형광펜 독해 — 무엇을 읽고 무엇을 버릴까',
    '정답을 몰라도 아래 신호가 보이면 🟡 무조건 읽는다 · 이 표가 눈에 익으면 읽을 문장이 먼저 보인다',
    '<b>훑기</b>(첫 문장·빈칸/밑줄로 ‘무엇을 묻나’) → <b>칠하기</b>(①~⑫ 신호만 🟡, 예시·양보는 스킵) → <b>찍기</b>(노랑 문장으로 근거 → 재진술로 선지 확정)',
    `<div class="hs-grid">${rows}</div>`
    + '<div class="pcatch"><span class="pcatch-h">⬜ 스킵해도 되는 곳</span> for example · such as · take/consider/imagine(예시 도입) · 숫자·연도·인명 나열 · Although·Despite 딸린 양보절 · 긴 관계절(, which ~) — 주절·주장만 챙기면 돼.</div>');
}

// 원리 페이지 묶음(끊어읽기 원리 다음, 지문 앞)
function principlesSectionHtml() {
  return attitudePageHtml() + pacePageHtml() + inferPageHtml() + connectivePageHtml()
    + restatePrinciplePageHtml() + transformPageHtml()
    + logicCausePageHtml() + logicContrastPageHtml() + highlightSignalPageHtml();
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
    ['✂', '끊어읽기 원리', '어디서 끊을까 — 5가지 신호'],
    ['🎯', '독해 태도', '점수는 태도에서 나온다'],
    ['🎚️', '완급조절', 'OLD / NEW·MAIN / SUPPORT'],
    ['🧩', '추론 — 어순·구두점', '모르는 건 추론한다'],
    ['🔗', '연결사 지도', 'Switching vs Contrast'],
    ['🔁', '재진술', '같은 말을 알아채기'],
    ['🔄', '재진술 5변환·함정', '정답이 만들어지는 법'],
    ['🏗️', '글의 구조', '6가지 글의 틀'],
    ['🗣️', '필자 입장 신호', '긍정·부정(±) 어휘'],
    ['➡️', '논리관계 구문 ①', '인과 · 등호'],
    ['⚖️', '논리관계 구문 ②', '대조 · 비교'],
    ['🖍️', '형광펜 신호 사전', '무엇을 읽고 버릴까'],
  ].map((r) => `<div class="toc-row"><span class="toc-ic">${r[0]}</span><span class="toc-name">${esc(r[1])}</span><span class="toc-dot"></span><span class="toc-tag">${esc(r[2])}</span></div>`).join('');
  const passRows = (passages || []).map((p, i) => `<div class="toc-row">
    <span class="toc-num">${i + 1}</span><span class="toc-name">${esc(p.title || `지문 ${i + 1}`)}</span>
    <span class="toc-dot"></span><span class="toc-tag">${esc(p.source || '지문')}</span></div>`).join('');
  return `<section class="chapter tocpage">
    <div class="chhead"><span class="daypill">${esc(meta.mark || '필생보')}</span><span class="tagpill">이 책 사용법 &amp; 목차</span></div>
    <h1>목차 · Contents</h1>
    <div class="chsub">먼저 독해 원리를 익히고 → 지문으로 훈련하는 순서야</div>
    <div class="toc-part">
      <div class="toc-part-h"><span class="tp-step">STEP 1</span> 먼저 익히는 독해 원리</div>
      ${guideRows}
    </div>
    <div class="toc-part">
      <div class="toc-part-h alt"><span class="tp-step alt">STEP 2</span> 지문으로 훈련 · 지문 ${(passages || []).length}편</div>
      ${passRows}
    </div>
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
  .toc-part { margin:12px 0 16px; }
  .toc-part-h { display:flex; align-items:center; gap:8px; font-size:14px; font-weight:800; color:${C.ink};
    padding-bottom:7px; margin-bottom:8px; border-bottom:2px solid ${C.teal}; }
  .toc-part-h.alt { border-bottom-color:${C.gram}; }
  .tp-step { font-size:10px; font-weight:800; color:#fff; background:${C.teal}; border-radius:12px; padding:2px 10px; letter-spacing:1px; }
  .tp-step.alt { background:${C.gram}; }
  .toc-row { display:flex; align-items:center; gap:9px; padding:7px 6px; }
  .toc-row + .toc-row { border-top:1px solid #f0f1f2; }
  .toc-ic { flex:none; width:24px; text-align:center; font-size:14px; }
  .toc-num { flex:none; display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px;
    border-radius:7px; background:${C.gramBg}; color:${C.gram}; font-size:11px; font-weight:800; border:1px solid #ddd4f2; }
  .toc-name { flex:none; font-size:12.5px; font-weight:800; color:${C.ink}; }
  .toc-dot { flex:1; border-bottom:2px dotted #d6d9dd; margin:0 4px; transform:translateY(-3px); }
  .toc-tag { flex:none; font-size:10px; font-weight:700; color:${C.sub}; }
  .tocpage .usebox { margin:18px 0 0; }
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
  const front = principlePageHtml()
    + attitudePageHtml() + pacePageHtml() + inferPageHtml() + connectivePageHtml()
    + restatePrinciplePageHtml() + transformPageHtml()
    + structurePageHtml() + stancePageHtml()
    + logicCausePageHtml() + logicContrastPageHtml() + highlightSignalPageHtml();
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

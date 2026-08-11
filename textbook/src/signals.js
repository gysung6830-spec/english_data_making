// signals.js — PART 0 '형광펜 독해' 신호를 실제 지문에 자동 표시하기 위한 사전.
// 지문 문장(en)을 카테고리별로 토큰화해서, PDF(html.js)·DOCX(document.js)가 같은
// 규칙으로 형광펜을 칠한다. (연결사·신호=노랑 / 예시·양보=회색 스킵 / ±어휘=초록·빨강)
//
// 오탐이 큰 지나치게 흔한 단어(so, but, still, as, key, matter …)는 일부러 제외.

const HL = {
  // 연결사·신호 (노랑)
  sig: [
    'on the other hand', 'on the contrary', 'contrary to popular belief', 'as a result',
    'in conclusion', 'in contrast', 'by contrast', 'in short', 'in fact', 'in addition',
    'as well as', 'that is why', 'not only', 'but also', 'give rise to', 'result in', 'results in',
    'resulted in', 'lead to', 'leads to', 'led to', 'due to', 'owing to', 'in order to',
    'ought to', 'need to', 'the most', 'the best', 'the only', 'only when', 'only if',
    'as long as', 'is defined as', 'refers to', 'in other words', 'just as', 'above all',
    'however', 'nevertheless', 'nonetheless', 'conversely', 'instead', 'whereas', 'unlike', 'but', 'yet',
    'therefore', 'thus', 'hence', 'consequently', 'ultimately', 'because', 'since', 'thereby',
    'should', 'must', 'indeed', 'especially', 'particularly', 'notably', 'clearly', 'unless',
    'traditionally', 'surprisingly', 'paradoxically', 'ironically', 'moreover', 'furthermore',
    'besides', 'similarly', 'likewise',
  ],
  // 예시·양보 (회색 — 스킵)
  skip: [
    'for example', 'for instance', 'such as', 'even though', 'in spite of', 'including',
    'namely', 'although', 'though', 'despite',
  ],
  // 긍정 ± (초록)
  pos: [
    'beneficial', 'benefit', 'valuable', 'priceless', 'fruitful', 'desirable', 'crucial',
    'critical', 'essential', 'vital', 'fundamental', 'indispensable', 'integral', 'significant',
    'substantial', 'important', 'advantage', 'effective', 'emphasize', 'enhance', 'reinforce',
    'prioritize', 'improve', 'improves', 'dominant',
  ],
  // 부정 ± (빨강)
  neg: [
    'abandon', 'discard', 'eliminate', 'shortage', 'absence', 'drawback', 'downside',
    'disregard', 'overlook', 'neglect', 'dismiss', 'refuse', 'reject', 'resist', 'diminish',
    'problem', 'risk', 'illusion', 'worthless', 'misleading', 'criticize', 'threat', 'negative',
    'wrong', 'danger', 'alarm', 'conceal', 'failed', 'fails', 'fail', 'lack',
  ],
};

function buildRe() {
  const map = new Map();
  ['skip', 'sig', 'pos', 'neg'].forEach((cat) => {
    HL[cat].forEach((w) => { if (!map.has(w.toLowerCase())) map.set(w.toLowerCase(), cat); });
  });
  const phrases = [...map.keys()].sort((a, b) => b.length - a.length)
    .map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  // 앞뒤에 '글자·하이픈'이 붙은 경우는 제외 → 하이픈 합성어(self-enhance, worn-out,
  // non-verbal 등)의 '일부'가 잘려 형광펜 칠해지는 것을 막는다.
  return { re: new RegExp('(?<![A-Za-z-])(' + phrases.join('|') + ')(?![A-Za-z-])', 'gi'), map };
}
const { re, map } = buildRe();

// 지문 문장 → [{t:'조각', cls:'sig'|'skip'|'pos'|'neg'|undefined}] 토큰 배열
function tokenizeSignals(en) {
  const s = String(en == null ? '' : en);
  const out = [];
  let last = 0; let m;
  re.lastIndex = 0;
  // eslint-disable-next-line no-cond-assign
  while ((m = re.exec(s))) {
    if (m.index > last) out.push({ t: s.slice(last, m.index) });
    out.push({ t: m[0], cls: map.get(m[0].toLowerCase()) });
    last = m.index + m[0].length;
    re.lastIndex = last;
  }
  if (last < s.length) out.push({ t: s.slice(last) });
  return out;
}

module.exports = { tokenizeSignals, HL };

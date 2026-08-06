// tip.js — "어디서 끊을까?" 팁 문구 자동 생성 (명세 §5.3)
//
// chunks 배열의 각 끊어읽기 경계(두 번째 청크부터)의 첫 단어를 보고
// 어떤 신호 때문에 끊었는지 추정하고, "왜 거기서 끊는지" 원리(규칙)까지 붙인다.
// 순수 문자열 매칭이라 오탐 가능성이 있고(정확성보다 "그럴듯한 학습 힌트"가 목적),
// 향후 품사 태깅으로 정교화할 여지가 있음 — 명세 §5.3 참고.

const RELATIVES = ['who', 'whom', 'whose', 'which', 'that', 'where', 'when'];
const PREPS = ['in', 'on', 'at', 'to', 'of', 'with', 'by', 'for', 'from', 'about',
  'into', 'through', 'against', 'without', 'under', 'after', 'before',
  'during', 'upon', 'as'];
const CONJ = ['and', 'or', 'but', 'when', 'while', 'if', 'because', 'so', 'then', 'yet'];

// 신호 유형별 '원리(왜 그 앞에서 끊나)'
const RULE = {
  prep: "전치사구(전치사+명사)는 한 덩어리",
  inf: "to+동사원형은 '~하는 것/~할/~위해' 덩어리",
  conj: "접속사 뒤엔 새 절이 붙어",
  rel: "관계사는 앞 명사를 꾸미는 절의 시작",
  part: "-ing/-ed 수식은 새 덩어리 시작",
};

// 끊어읽기 5원칙 요약(지문마다 한 번 보여주는 원리 박스용)
const PRINCIPLES = [
  '전치사(in/on/at/of/with/for…) 앞',
  'to부정사(to+동사원형) 앞',
  '접속사(and/but/that/because/when…) 앞',
  '관계사(who/which/that/where…) 앞',
  '분사(-ing/-ed 수식)·콤마(,)',
];

function classify(chunks) {
  const types = [];
  const words = [];
  for (let i = 1; i < chunks.length; i += 1) {
    const raw = chunks[i][0].replace(/^[—\-"'(]+/, '').trim();
    const first = raw.split(/\s+/)[0].toLowerCase().replace(/[^a-z]/g, '');
    if (RELATIVES.includes(first)) { types.push('rel'); words.push(`관계사 '${first}'`); }
    else if (first === 'to' && /^to\s+[a-z]+ing?\b/i.test(raw) === false) { types.push('inf'); words.push("to부정사 'to'"); }
    else if (PREPS.includes(first)) { types.push('prep'); words.push(`전치사 '${first}'`); }
    else if (CONJ.includes(first)) { types.push('conj'); words.push(`접속사 '${first}'`); }
    else if (/ing[.,;]?$/i.test(raw.split(/\s+/)[0])) { types.push('part'); words.push('분사/동명사(-ing)'); }
  }
  return { types, words };
}

// 한 문장의 끊어읽기 팁 — 어디서(신호어) + 왜(원리)
function makeTip(chunks) {
  const { types, words } = classify(chunks);
  const uniqWords = [...new Set(words)].slice(0, 3);
  if (uniqWords.length === 0) {
    return '진짜 주어+동사(뼈대)를 먼저 잡고, 나머지 수식 덩어리는 앞에서 끊어 하나씩 붙여. 되돌아가지 말고 앞에서부터.';
  }
  const rules = [...new Set(types)].map((t) => RULE[t]).filter(Boolean);
  return `${uniqWords.join(', ')} 앞에서 끊어. 원리 — ${rules.join(' · ')}라서 그 앞이 새 덩어리 경계야. 앞에서부터 끊어 붙여 읽어.`;
}

module.exports = { makeTip, PRINCIPLES };

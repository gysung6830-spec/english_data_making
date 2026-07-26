// tip.js — "왜 여기서 끊었을까?" 팁 문구 자동 생성 (명세 §5.3)
//
// chunks 배열의 각 끊어읽기 경계(두 번째 청크부터)의 첫 단어를 보고
// 어떤 문법 신호 때문에 끊었는지 추정한다. 순수 문자열 매칭이라 오탐 가능성이
// 있고(정확성보다 "그럴듯한 학습 힌트" 제공이 목적), 향후 품사 태깅으로
// 정교화할 여지가 있음 — 명세 §5.3 참고.

const RELATIVES = ['who', 'whom', 'whose', 'which', 'that', 'where', 'when'];
const PREPS = ['in', 'on', 'at', 'to', 'of', 'with', 'by', 'for', 'from', 'about',
  'into', 'through', 'against', 'without', 'under', 'after', 'before',
  'during', 'upon', 'as'];
const CONJ = ['and', 'or', 'but', 'when', 'while', 'if', 'because', 'so', 'then', 'yet'];

function makeTip(chunks) {
  const triggers = [];
  for (let i = 1; i < chunks.length; i += 1) {
    const raw = chunks[i][0].replace(/^[—\-"'(]+/, '').trim();
    const first = raw.split(/\s+/)[0].toLowerCase().replace(/[^a-z]/g, '');
    if (RELATIVES.includes(first)) triggers.push(`관계사 '${first}'`);
    else if (first === 'to' && /^to\s+[a-z]+ing?\b/i.test(raw) === false) triggers.push("to부정사 'to'");
    else if (PREPS.includes(first)) triggers.push(`전치사 '${first}'`);
    else if (CONJ.includes(first)) triggers.push(`접속사 '${first}'`);
    else if (/ing[.,;]?$/i.test(raw.split(/\s+/)[0])) triggers.push('분사/동명사(-ing)');
  }
  const uniq = [...new Set(triggers)].slice(0, 3);
  if (uniq.length === 0) {
    return '의미가 한 덩어리로 끝나는 지점(주어+동사 뼈대, 수식어 경계)마다 끊어 봐. 그 덩어리 안에서만 뜻을 붙이면 훨씬 쉬워.';
  }
  return `${uniq.join(', ')} 앞에서 끊어 봐 — 새로운 의미 덩어리가 시작되는 신호야. 이 지점마다 숨 한 번 쉬고 다음 덩어리로 넘어가면 돼.`;
}

module.exports = { makeTip };

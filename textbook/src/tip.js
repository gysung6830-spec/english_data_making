// tip.js — "왜 여기서 끊었을까?" 팁 문구 자동 생성 (명세 §5.3)
//
// chunks 배열의 각 끊어읽기 경계(두 번째 청크부터)의 첫 단어를 보고
// 어떤 문법 신호 때문에 끊었는지 추정한다. 순수 문자열 매칭이라 오탐 가능성이
// 있고(정확성보다 "그럴듯한 학습 힌트" 제공이 목적), 향후 품사 태깅으로
// 정교화할 여지가 있음 — 명세 §5.3 참고.

const RELATIVES = new Set([
  'who', 'whom', 'whose', 'which', 'that', 'where', 'when',
]);

const PREPOSITIONS = new Set([
  'in', 'on', 'at', 'to', 'of', 'with', 'by', 'for', 'from', 'about',
  'into', 'through', 'against', 'without', 'under', 'after', 'before',
  'during', 'upon', 'as',
]);

const CONJUNCTIONS = new Set([
  'and', 'or', 'but', 'when', 'while', 'if', 'because', 'so', 'then', 'yet',
]);

// 청크 첫 단어를 소문자·문장부호 제거해 반환
function firstWord(chunkEn) {
  const m = String(chunkEn).trim().toLowerCase().match(/[a-z][a-z'-]*/);
  return m ? m[0] : '';
}

// 한 경계(첫 단어)에 대한 트리거 종류를 추정. 없으면 null.
function classify(word) {
  if (!word) return null;
  const isIng = word.endsWith('ing');
  if (RELATIVES.has(word)) return { kind: 'relative', word };
  if (word === 'to') return { kind: 'infinitive', word }; // to부정사
  // 분사/동명사: -ing 로 끝나는 첫 단어 (to 예외는 위에서 이미 처리)
  if (isIng) return { kind: 'ing', word };
  if (CONJUNCTIONS.has(word)) return { kind: 'conjunction', word };
  if (PREPOSITIONS.has(word)) return { kind: 'preposition', word };
  return null;
}

const PHRASE = {
  relative:    (w) => `'${w}' 는 앞의 명사를 꾸며 주는 신호야 — 여기서 한 번 끊고 "어떤 명사?" 하고 뒤를 이어 읽자.`,
  infinitive:  ()  => `'to + 동사' 가 나오면 '~하기 위해 / ~하는 것' 처럼 새 덩어리가 시작돼. 그래서 여기서 끊었어.`,
  ing:         (w) => `'${w}' 처럼 -ing 로 시작하면 '~하면서 / ~하는' 덩어리라 앞과 나눠 읽는 게 편해.`,
  conjunction: (w) => `'${w}' 는 두 덩어리를 이어 주는 말이라, 앞뒤를 나눠서 각각 해석하면 돼.`,
  preposition: (w) => `'${w}' 같은 전치사 앞에서 끊으면 '어디/무엇에 대해' 인지 덩어리로 잡기 쉬워.`,
};

// chunks -> 팁 문구(문자열). 트리거가 하나도 없으면 기본 폴백.
function makeTip(chunks) {
  if (!Array.isArray(chunks) || chunks.length < 2) {
    return '의미가 한 덩어리로 뭉치는 곳에서 끊어 읽으면 긴 문장도 안 헷갈려!';
  }

  const triggers = [];
  const seen = new Set();
  // 두 번째 청크부터가 "끊은 경계"
  for (let i = 1; i < chunks.length; i += 1) {
    const t = classify(firstWord(chunks[i][0]));
    if (t && !seen.has(t.kind + ':' + t.word)) {
      seen.add(t.kind + ':' + t.word);
      triggers.push(t);
    }
    if (triggers.length >= 3) break; // 최대 3개
  }

  if (triggers.length === 0) {
    return '의미가 한 덩어리로 뭉치는 곳에서 끊어 읽으면 긴 문장도 안 헷갈려!';
  }

  return triggers.map((t) => PHRASE[t.kind](t.word)).join(' ');
}

module.exports = { makeTip, classify, firstWord };

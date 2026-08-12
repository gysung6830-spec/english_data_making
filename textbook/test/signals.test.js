// signals.test.js — 형광펜 신호 토큰화 회귀 테스트 (비용 0)
//
// 고정 대상: 하이픈 합성어(self-enhance)의 '일부'가 잘려 형광펜 칠해지는 버그 방지.

const { test } = require('node:test');
const assert = require('node:assert');
const { tokenizeSignals } = require('../src/signals');

function classesFor(text, word) {
  return tokenizeSignals(text)
    .filter((t) => t.t.trim().toLowerCase() === word.toLowerCase() && t.cls)
    .map((t) => t.cls);
}

test('하이픈 합성어(self-enhance) 안의 "enhance" 는 형광펜 대상이 아니어야 함', () => {
  const toks = tokenizeSignals('This self-enhance trick is nice.');
  const highlighted = toks.filter((t) => t.cls).map((t) => t.t);
  assert.deepStrictEqual(highlighted, [], `unexpected highlight: ${JSON.stringify(highlighted)}`);
});

test('단독 "enhance" 는 긍정(pos) 형광펜', () => {
  assert.deepStrictEqual(classesFor('This will enhance results.', 'enhance'), ['pos']);
});

test('연결사 "however" 는 신호(sig) 형광펜', () => {
  assert.deepStrictEqual(classesFor('However, it failed.', 'however'), ['sig']);
});

test('예시 표현 "for example" 은 회색(skip)', () => {
  const toks = tokenizeSignals('For example, this works.');
  const hit = toks.find((t) => t.cls === 'skip');
  assert.ok(hit && /for example/i.test(hit.t));
});

test('부정 어휘 "problem" 은 부정(neg) 형광펜', () => {
  assert.deepStrictEqual(classesFor('This is a problem.', 'problem'), ['neg']);
});

test('토큰을 이어붙이면 원문이 복원된다 (손실 없음)', () => {
  const s = 'However, self-enhance may cause a problem for example.';
  assert.strictEqual(tokenizeSignals(s).map((t) => t.t).join(''), s);
});

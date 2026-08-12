// validate.test.js — 지문 데이터 불변식 검증 회귀 테스트 (비용 0)

const { test } = require('node:test');
const assert = require('node:assert');
const { validatePassages } = require('../src/validate');

function goodPassage() {
  return {
    title: 'T', source: 'S', topic: 'to', catch: 'ca',
    sentences: [{
      src: '1', en: 'Hello world here.',
      chunks: [['Hello', '안녕'], ['world here', '여기 세계']],
      vocab: [['world', '세계']], catch: 'c',
    }],
  };
}

test('validatePassages: 정상 데이터는 에러 없음', () => {
  const { errors } = validatePassages([goodPassage()]);
  assert.deepStrictEqual(errors, []);
});

test('validatePassages: en 이 비면 에러', () => {
  const p = goodPassage();
  p.sentences[0].en = '';
  const { errors } = validatePassages([p]);
  assert.ok(errors.some((e) => /en 이 비어있음/.test(e)));
});

test('validatePassages: chunks 가 비면 에러', () => {
  const p = goodPassage();
  p.sentences[0].chunks = [];
  const { errors } = validatePassages([p]);
  assert.ok(errors.some((e) => /chunks 가 비어있음/.test(e)));
});

test('validatePassages: 반쪽 끊어읽기 조각([영어]만)은 에러', () => {
  const p = goodPassage();
  p.sentences[0].chunks = [['Hello', '']];
  const { errors } = validatePassages([p]);
  assert.ok(errors.some((e) => /chunks\[0\]/.test(e)));
});

test('validatePassages: sentences 가 비면 에러', () => {
  const p = goodPassage();
  p.sentences = [];
  const { errors } = validatePassages([p]);
  assert.ok(errors.some((e) => /sentences 가 비어있음/.test(e)));
});

test('validatePassages: 빈 배열은 에러', () => {
  const { errors } = validatePassages([]);
  assert.ok(errors.length >= 1);
});

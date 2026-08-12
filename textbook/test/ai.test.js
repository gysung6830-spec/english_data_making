// ai.test.js — AI 구조화 단계의 '결정적 로직' 회귀 테스트 (실제 Claude 호출 없음 · 비용 0)
//
// 고정 대상:
//   1) 스키마에 array minItems > 1 또는 maxItems 가 없어야 함 (400 에러 재발 방지)
//   2) sanitizePassages — 재진술 링크: 지문에 없는 표현 제거 · 등장순 정렬 · 2개 미만 사슬 제거
//   3) sanitizePassages — 영어 필드(en/끊어읽기 en)에 섞인 한글 제거
//   4) normalizePassages — 객체 → 내부 튜플 스키마 변환

const { test } = require('node:test');
const assert = require('node:assert');
const {
  PASSAGE_SCHEMA, OUTPUT_SCHEMA, sanitizePassages, normalizePassages,
} = require('../src/ai');

function collectSchemaViolations(node, path, acc) {
  if (node && typeof node === 'object') {
    if ('minItems' in node && node.minItems > 1) acc.push(`${path}.minItems=${node.minItems}`);
    if ('maxItems' in node) acc.push(`${path}.maxItems=${node.maxItems}`);
    Object.keys(node).forEach((k) => collectSchemaViolations(node[k], `${path}.${k}`, acc));
  }
  return acc;
}

test('스키마: array minItems 는 0/1 만 (structured outputs 400 방지)', () => {
  assert.deepStrictEqual(collectSchemaViolations(PASSAGE_SCHEMA, 'PASSAGE', []), []);
  assert.deepStrictEqual(collectSchemaViolations(OUTPUT_SCHEMA, 'OUTPUT', []), []);
});

function samplePassage() {
  return {
    title: 't', source: 's', topic: '', catch: 'c',
    sentences: [{
      src: '1', en: 'The market is efficient and fair here.', point: '',
      chunks: [['The market', '시장은'], ['is efficient', '효율적']],
      vocab: [['market', '시장']], catch: 'x', ex: '', trap: '',
    }],
    paraphrases: [
      // 링크가 지문 등장 순서와 다르게 들어오고, 하나는 지문에 없는 표현
      { keyword: 'k', links: ['is efficient', 'The market', 'not in passage at all'], why: 'w' },
      // 정리 후 링크 1개 → 사슬 제거 대상
      { keyword: 'drop', links: ['The market'], why: 'only one' },
    ],
  };
}

test('sanitizePassages: 지문에 없는 링크 제거 + 2개 미만 사슬 제거', () => {
  const out = sanitizePassages([samplePassage()]);
  assert.strictEqual(out[0].paraphrases.length, 1);
});

test('sanitizePassages: 링크를 지문 등장 순서로 정렬 (A→A′ 방향 보장)', () => {
  const out = sanitizePassages([samplePassage()]);
  // 지문에서 "The market" 이 "is efficient" 보다 먼저 나오므로 그 순서로 재정렬
  assert.deepStrictEqual(out[0].paraphrases[0].links, ['The market', 'is efficient']);
});

test('sanitizePassages: 영어 끊어읽기 조각에 섞인 한글 제거', () => {
  const p = samplePassage();
  p.sentences[0].chunks = [['The market 시장', '시장은'], ['is efficient', '효율적']];
  const out = sanitizePassages([p]);
  assert.strictEqual(out[0].sentences[0].chunks[0][0], 'The market');
});

test('sanitizePassages: 어휘가 비면 기본값을 채워 검증 통과시킴', () => {
  const p = samplePassage();
  p.sentences[0].vocab = [];
  const out = sanitizePassages([p]);
  assert.ok(out[0].sentences[0].vocab.length >= 1);
});

test('normalizePassages: 객체 형태를 내부 튜플 스키마로 변환', () => {
  const ai = {
    passages: [{
      title: 'T', source: 'S', topic: 'to', catch: 'ca',
      claim: { stance: '긍정적', why: 'w' },
      structure: { type: '주장→근거', why: 'w' },
      paraphrases: [{ keyword: 'k', links: ['a', 'b'], why: 'w' }],
      sentences: [{
        src: '1', en: 'Hello world.', point: '전치사구',
        chunks: [{ en: 'Hello', kor: '안녕' }, { en: 'world', kor: '세계' }],
        vocab: [{ word: 'world', mean: '세계' }],
        catch: 'c', ex: '', trap: '',
      }],
    }],
  };
  const out = normalizePassages(ai);
  assert.strictEqual(out.length, 1);
  assert.deepStrictEqual(out[0].sentences[0].chunks[0], ['Hello', '안녕']);
  assert.deepStrictEqual(out[0].sentences[0].vocab[0], ['world', '세계']);
  assert.strictEqual(out[0].claim.stance, '긍정적');
});

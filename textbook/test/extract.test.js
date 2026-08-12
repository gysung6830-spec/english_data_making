// extract.test.js — 추출 단계 회귀 테스트 (API 비용 0 · 오프라인)
//
// 이번 세션에 고친 두 버그를 고정한다:
//   1) 공백이 제어문자(U+0001)로 추출되어 단어가 붙는 인코딩 깨짐
//   2) 짧은 대사 문장("Wrong again.")·문장 끝 꼬리 유실
// 및 looksEnglish/stripHangul/joinAndSplit 의 핵심 불변식.

const { test } = require('node:test');
const assert = require('node:assert');
const {
  looksEnglish, stripHangul, joinAndSplit, normalizePdfText,
} = require('../src/extract');

const SOH = String.fromCharCode(1);   // U+0001
const NBSP = String.fromCharCode(0xA0);
const BOM = String.fromCharCode(0xFEFF);

test('normalizePdfText: 제어문자 U+0001 을 공백으로 정규화 (단어 붙음 방지)', () => {
  const glued = `Many${SOH}developmental${SOH}theorists`;
  assert.strictEqual(normalizePdfText(glued), 'Many developmental theorists');
});

test('normalizePdfText: NBSP·BOM 등 유니코드 공백도 일반 공백으로', () => {
  assert.strictEqual(normalizePdfText(`a${NBSP}b${BOM}c`), 'a b c');
});

test('normalizePdfText: 줄바꿈·탭은 보존', () => {
  assert.strictEqual(normalizePdfText('a\nb\tc'), 'a\nb\tc');
});

test('looksEnglish: 짧은 대사 문장도 통과 ("Wrong again.")', () => {
  assert.strictEqual(looksEnglish('Wrong again.'), true);
});

test('looksEnglish: 일반 문장 통과', () => {
  assert.strictEqual(looksEnglish('The cat sat on the mat quietly.'), true);
});

test('looksEnglish: 저작권 푸터 배제', () => {
  assert.strictEqual(looksEnglish('©2026. Ortica. All rights reserved.'), false);
});

test('looksEnglish: 답지 재진술 화살표(→) 배제', () => {
  assert.strictEqual(looksEnglish('A → B → C transformation.'), false);
});

test('looksEnglish: URL/사이트 푸터 배제', () => {
  assert.strictEqual(looksEnglish('www.flowedu.tistory.com!'), false);
});

test('looksEnglish: 한글 위주 줄 배제', () => {
  assert.strictEqual(looksEnglish('이 문장은 한글이야.'), false);
});

test('stripHangul: 영어 문장 속 한글 병기·빈 괄호 제거', () => {
  assert.strictEqual(stripHangul('The word (단어) means something.'), 'The word means something.');
});

test('joinAndSplit: 여러 줄에 걸친 영어 문장을 한 문장으로 합침', () => {
  const out = joinAndSplit('The quick brown fox\njumps over the lazy dog.');
  assert.ok(out.some((s) => /quick brown fox jumps over the lazy dog\./.test(s)),
    `joined sentence missing: ${JSON.stringify(out)}`);
});

test('joinAndSplit: 짧은 영어 꼬리 줄도 앞 문장에 이어붙임 (문장 끝 유실 방지)', () => {
  // 문장 끝 "own?" 이 다음 줄로 넘어간 경우
  const out = joinAndSplit('Do you really understand it on your\nown?');
  assert.ok(out.some((s) => /on your own\?/.test(s)),
    `tail not merged: ${JSON.stringify(out)}`);
});

// prune.test.js — 산출물 정리(pruneOutputs) 회귀 테스트 (비용 0 · 오프라인)
//
// 규칙: 같은 stamp(book_xxx)의 docx/pdf/html 은 한 세트. 48시간 초과 또는
//   최신 30세트를 벗어난 오래된 세트를 삭제, 최신 30세트·48시간 이내는 보존.

const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pruneOutputs } = require('../webapp/server');

function mkSet(dir, stamp, ageMs) {
  const t = Date.now() - ageMs;
  ['docx', 'pdf', 'html'].forEach((ext) => {
    const f = path.join(dir, `${stamp}.${ext}`);
    fs.writeFileSync(f, 'x');
    fs.utimesSync(f, t / 1000, t / 1000);
  });
}
function tmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'prune-'));
}

test('48시간 초과 세트는 삭제된다', () => {
  const d = tmpDir();
  mkSet(d, 'book_fresh', 1 * 60 * 60 * 1000);        // 1시간 전 → 보존
  mkSet(d, 'book_old', 49 * 60 * 60 * 1000);         // 49시간 전 → 삭제
  pruneOutputs(d);
  assert.ok(fs.existsSync(path.join(d, 'book_fresh.pdf')), 'fresh 세트가 남아야 함');
  assert.ok(!fs.existsSync(path.join(d, 'book_old.pdf')), 'old 세트가 지워져야 함');
  assert.ok(!fs.existsSync(path.join(d, 'book_old.docx')));
  assert.ok(!fs.existsSync(path.join(d, 'book_old.html')));
});

test('최신 30세트만 남기고 초과분은 삭제된다', () => {
  const d = tmpDir();
  // 35세트를 서로 다른 나이(모두 48시간 이내)로 생성 — i가 클수록 오래됨
  for (let i = 0; i < 35; i += 1) mkSet(d, `book_${String(i).padStart(2, '0')}`, i * 60 * 1000);
  pruneOutputs(d);
  const remaining = new Set(fs.readdirSync(d).map((n) => n.replace(/\.[^.]+$/, '')));
  assert.strictEqual(remaining.size, 30, `30세트만 남아야 함 (현재 ${remaining.size})`);
  assert.ok(remaining.has('book_00'), '가장 최신은 보존');
  assert.ok(!remaining.has('book_34'), '가장 오래된 초과분은 삭제');
});

test('30세트 이하·48시간 이내는 모두 보존', () => {
  const d = tmpDir();
  for (let i = 0; i < 10; i += 1) mkSet(d, `book_${i}`, i * 60 * 1000);
  pruneOutputs(d);
  assert.strictEqual(fs.readdirSync(d).length, 30, '10세트×3파일 = 30개 모두 보존');
});

test('없는 디렉터리에도 안전하게 동작(예외 없음)', () => {
  assert.doesNotThrow(() => pruneOutputs(path.join(os.tmpdir(), 'no-such-dir-xyz-123')));
});

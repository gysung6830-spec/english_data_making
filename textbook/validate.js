#!/usr/bin/env node
// validate.js — 데이터 검증만 단독 실행 (빌드 없이 CI/사전 점검용)
//   node validate.js
// 오류가 있으면 종료 코드 1, 없으면 0.

const categories = require('./data');
const { validateData } = require('./src/validate');

const { errors, warnings } = validateData(categories);

warnings.forEach((w) => console.warn('경고:', w));

if (errors.length) {
  console.error(`\n❌ 검증 실패 (${errors.length}건):`);
  errors.forEach((e) => console.error('  •', e));
  process.exit(1);
}

console.log(`✓ 검증 통과 — 챕터 ${categories.length}개, 문제 없음.`);
process.exit(0);

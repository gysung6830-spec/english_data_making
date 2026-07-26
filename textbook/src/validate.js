// validate.js — 데이터 불변식 검증 (명세 §4 invariant, 우선순위 작업 #3)
//
// 빌드 전에 data.js 를 검사해, 구조 오류를 조기에 잡는다.
//  - worked.length === 2 (챕터당 정확히 2문장)
//  - 모든 문장에 en / chunks / vocab / catch 가 비어있지 않아야 함
//  - worked 문장은 steps 가 있어야 하고, practice 문장은 steps 가 없어야 함
//  - title 에 원문자 번호(①~⑥ …)가 챕터 순서와 맞는지 경고
//  - 초록 계열 색상 하드코딩 여부는 styles 에서 관리하므로 여기서는 다루지 않음

const CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

function nonEmptyStr(v) {
  return typeof v === 'string' && v.trim().length > 0;
}

function checkSentence(s, where, { requireSteps }) {
  const errs = [];
  if (!nonEmptyStr(s.src)) errs.push(`${where}: src 가 비어있음`);
  if (!nonEmptyStr(s.en)) errs.push(`${where}: en 이 비어있음`);

  if (!Array.isArray(s.chunks) || s.chunks.length === 0) {
    errs.push(`${where}: chunks 가 비어있음`);
  } else {
    s.chunks.forEach((c, i) => {
      if (!Array.isArray(c) || !nonEmptyStr(c[0]) || !nonEmptyStr(c[1])) {
        errs.push(`${where}: chunks[${i}] 는 [영어, 한글] 두 값이 모두 필요함`);
      }
    });
  }

  if (!Array.isArray(s.vocab) || s.vocab.length === 0) {
    errs.push(`${where}: vocab 가 비어있음`);
  } else {
    s.vocab.forEach((v, i) => {
      if (!Array.isArray(v) || !nonEmptyStr(v[0]) || !nonEmptyStr(v[1])) {
        errs.push(`${where}: vocab[${i}] 는 [단어, 뜻] 두 값이 모두 필요함`);
      }
    });
  }

  if (!nonEmptyStr(s.catch)) errs.push(`${where}: catch 문구가 비어있음`);

  if (requireSteps) {
    if (!Array.isArray(s.steps) || s.steps.length === 0) {
      errs.push(`${where}: worked 문장인데 steps 가 없음`);
    }
  } else if (Array.isArray(s.steps) && s.steps.length > 0) {
    errs.push(`${where}: practice 문장에는 steps 가 없어야 함(학생이 직접 채우는 칸)`);
  }
  return errs;
}

// categories 배열 검증 -> { errors: string[], warnings: string[] }
function validateData(categories) {
  const errors = [];
  const warnings = [];

  if (!Array.isArray(categories) || categories.length === 0) {
    return { errors: ['data 가 비어있거나 배열이 아님'], warnings };
  }

  categories.forEach((cat, idx) => {
    const tag = cat.key || `#${idx + 1}`;
    if (!nonEmptyStr(cat.key)) errors.push(`카테고리 #${idx + 1}: key 가 비어있음`);
    if (!nonEmptyStr(cat.title)) errors.push(`[${tag}] title 이 비어있음`);
    ['intro', 'signal', 'method'].forEach((f) => {
      if (!Array.isArray(cat[f]) || cat[f].length === 0) {
        errors.push(`[${tag}] ${f} 가 비어있음`);
      }
    });

    // title 의 원문자 번호가 챕터 순서와 일치하는지 (경고)
    const expected = CIRCLED[idx];
    if (nonEmptyStr(cat.title) && !cat.title.includes(expected)) {
      warnings.push(`[${tag}] title 에 순서 번호 '${expected}' 가 없음 — 목차 재배열 시 번호 갱신 필요(명세 §2)`);
    }

    // worked.length === 2 (핵심 불변식)
    if (!Array.isArray(cat.worked) || cat.worked.length !== 2) {
      errors.push(`[${tag}] worked.length === 2 여야 함 (현재 ${Array.isArray(cat.worked) ? cat.worked.length : 'N/A'})`);
    }
    (cat.worked || []).forEach((s, i) =>
      errors.push(...checkSentence(s, `[${tag}] worked[${i}]`, { requireSteps: true })));

    if (!Array.isArray(cat.practice) || cat.practice.length === 0) {
      warnings.push(`[${tag}] practice 가 비어있음 — 정말 나머지 문장이 하나도 없는지 확인`);
    }
    (cat.practice || []).forEach((s, i) =>
      errors.push(...checkSentence(s, `[${tag}] practice[${i}]`, { requireSteps: false })));
  });

  return { errors, warnings };
}

module.exports = { validateData };

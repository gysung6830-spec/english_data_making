#!/usr/bin/env node
// gen-fonts-embed.js — fonts/*.woff2 를 base64 로 인코딩해 src/fonts-embedded.js 를 생성.
//
// 목적: 디자인 PDF/HTML 이 파일시스템의 fonts/ 폴더에 의존하지 않고도(경로·환경 무관)
//       항상 NanumSquareRound 로 렌더되도록, 폰트 base64 를 코드에 그대로 박아 넣는다.
//
// 폰트를 교체/업데이트하면 이 스크립트를 다시 돌려 src/fonts-embedded.js 를 갱신한다:
//   node scripts/gen-fonts-embed.js
//
// NanumSquareRound 는 OFL-1.1 (fonts/LICENSE.txt) — 임베드/재배포 허용.

const fs = require('fs');
const path = require('path');

const FONTS_DIR = path.join(__dirname, '..', 'fonts');
const OUT = path.join(__dirname, '..', 'src', 'fonts-embedded.js');

// [상수 이름, 파일명, font-weight]
const DEFS = [
  ['NanumSquareRoundL', 'NanumSquareRoundL.woff2', 300],
  ['NanumSquareRoundR', 'NanumSquareRoundR.woff2', 400],
  ['NanumSquareRoundB', 'NanumSquareRoundB.woff2', 700],
  ['NanumSquareRoundEB', 'NanumSquareRoundEB.woff2', 800],
];

const entries = DEFS.map(([name, file, weight]) => {
  const fp = path.join(FONTS_DIR, file);
  const b64 = fs.readFileSync(fp).toString('base64');
  return { name, weight, b64 };
});

const header = `// fonts-embedded.js — 자동 생성 파일 (scripts/gen-fonts-embed.js).\n`
  + `// NanumSquareRound(OFL-1.1) woff2 를 base64 로 인라인. 직접 수정하지 말 것 —\n`
  + `// 폰트를 바꾸려면 fonts/ 를 교체하고 'node scripts/gen-fonts-embed.js' 재실행.\n`
  + `/* eslint-disable */\n`;

const body = 'module.exports = {\n'
  + '  // { weight, woff2(base64) }\n'
  + '  FONTS: [\n'
  + entries.map((e) => `    { weight: ${e.weight}, b64: '${e.b64}' },`).join('\n')
  + '\n  ],\n};\n';

fs.writeFileSync(OUT, header + body);
const kb = (fs.statSync(OUT).size / 1024).toFixed(0);
console.log(`✓ 생성: ${path.relative(process.cwd(), OUT)} (${kb}KB, 폰트 ${entries.length}개)`);

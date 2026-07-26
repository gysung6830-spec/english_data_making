#!/usr/bin/env node
// preview_pdf.js — 디자인 적용 PDF 생성기 (CLI 얇은 래퍼)
//
// 실제 렌더링(HTML/CSS·Chromium 인쇄)은 src/html.js 로 옮겼다.
// 이 CLI 와 webapp 이 같은 렌더러를 공유한다.
//   · buildHtml(categories) → 디자인 HTML
//   · renderPdf(html, pdf)  → Chromium 으로 PDF 저장
//
// 사용법: node preview_pdf.js  →  output/output_v4_preview.pdf

const fs = require('fs');
const path = require('path');
const categories = require('./data');
const { buildHtml, renderPdf } = require('./src/html');

async function main() {
  const html = buildHtml(categories);

  const outDir = path.join(__dirname, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  const htmlPath = path.join(outDir, 'output_v4_preview.html');
  const pdfPath = path.join(outDir, 'output_v4_preview.pdf');
  fs.writeFileSync(htmlPath, html);

  await renderPdf(html, pdfPath);
  console.log('✓ 디자인 PDF 생성:', path.relative(process.cwd(), pdfPath));
}

main().catch((e) => { console.error(e); process.exit(1); });

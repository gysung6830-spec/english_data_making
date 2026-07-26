#!/usr/bin/env node
// build_v4.js — 교재 빌드 진입점 (명세 §5.5 출력 파이프라인)
//
//   1. data.js 로드 → 검증(validate)
//   2. docx 로 .docx 바이너리 생성 (Packer.toBuffer)
//   3. LibreOffice headless 로 .pdf 변환 (soffice --headless --convert-to pdf)
//
// 사용법:
//   node build_v4.js                 # output/output_v4.docx + .pdf 생성
//   node build_v4.js --no-pdf        # docx 만 (LibreOffice 없을 때)
//   node build_v4.js --out mybook    # output/mybook.docx / .pdf
//
// 리팩터링 메모(명세 우선순위 #2): 예전 단일 파일 build_v4.js 를
// src/{styles,tip,boxes,document,validate}.js 모듈로 분리했다.

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { Packer } = require('docx');

const categories = require('./data');
const { buildDocument } = require('./src/document');
const { validateData } = require('./src/validate');

function parseArgs(argv) {
  const opts = { pdf: true, out: 'output_v4' };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--no-pdf') opts.pdf = false;
    else if (a === '--out') { opts.out = argv[i + 1]; i += 1; }
  }
  return opts;
}

function convertToPdf(docxPath, outDir) {
  const pdfPath = path.join(outDir, `${path.basename(docxPath, '.docx')}.pdf`);
  // soffice 는 변환에 실패해도 종료 코드 0 을 반환하는 경우가 있어(예: 문서 로드 실패),
  // 종료 코드만 믿지 말고 실제로 pdf 파일이 새로 생겼는지 확인한다.
  const before = fs.existsSync(pdfPath) ? fs.statSync(pdfPath).mtimeMs : 0;
  let out = '';
  try {
    out = execFileSync('soffice', [
      '--headless', '--convert-to', 'pdf', '--outdir', outDir, docxPath,
    ], { stdio: 'pipe' }).toString();
  } catch (err) {
    console.warn('⚠️  PDF 변환 실패(LibreOffice 없음/오류) — docx 는 생성됨:',
      (err.stderr && err.stderr.toString().trim()) || err.message);
    return false;
  }
  const ok = fs.existsSync(pdfPath) && fs.statSync(pdfPath).mtimeMs > before;
  if (!ok) {
    console.warn('⚠️  PDF 변환이 완료되지 않음(soffice 는 오류에도 종료코드 0 을 반환) — docx 는 생성됨.');
    if (out.trim()) console.warn('   soffice:', out.trim());
    console.warn('   → LibreOffice 가 정상 설치된 PC 에서 아래 명령으로 변환하세요:');
    console.warn(`   soffice --headless --convert-to pdf --outdir "${outDir}" "${docxPath}"`);
  }
  return ok;
}

async function main() {
  const opts = parseArgs(process.argv);

  // 1) 검증
  const { errors, warnings } = validateData(categories);
  warnings.forEach((w) => console.warn('경고:', w));
  if (errors.length) {
    console.error(`\n❌ 데이터 검증 실패 (${errors.length}건) — 빌드를 중단합니다:`);
    errors.forEach((e) => console.error('  •', e));
    process.exit(1);
  }
  console.log(`✓ 데이터 검증 통과 (챕터 ${categories.length}개)`);

  // 2) docx 생성
  const outDir = path.join(__dirname, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  const docxPath = path.join(outDir, `${opts.out}.docx`);

  const doc = buildDocument(categories);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(docxPath, buffer);
  console.log('✓ docx 생성:', path.relative(process.cwd(), docxPath));

  // 3) pdf 변환
  if (opts.pdf) {
    if (convertToPdf(docxPath, outDir)) {
      console.log('✓ pdf 생성:', path.relative(process.cwd(), path.join(outDir, `${opts.out}.pdf`)));
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

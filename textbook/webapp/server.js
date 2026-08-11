#!/usr/bin/env node
// server.js — PDF 업로드 → AI 구조화 → 교재(docx + 디자인 PDF) 생성 웹앱
//
// 흐름:
//   1) 사용자가 수능/평가원 WORKBOOK PDF 업로드
//   2) src/extract.js 가 영어 문장 후보 추출
//   3) src/ai.js 가 Claude(claude-opus-5) 로 문법 챕터별 교재 데이터 생성
//        (ANTHROPIC_API_KEY 없으면 MOCK 로 폴백 — 파이프라인만 확인용)
//   4) src/validate.js 로 불변식 검증
//   5) src/document.js → docx, src/html.js → 디자인 PDF 렌더
//   6) 다운로드 링크 반환
//
// 실행:  ANTHROPIC_API_KEY=sk-... node webapp/server.js   (또는 npm run web)
//        http://localhost:3000

require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });

const fs = require('fs');
const path = require('path');
const express = require('express');
const multer = require('multer');
const { Packer } = require('docx');

const { extractSentences } = require('../src/extract');
const { structurePassages } = require('../src/ai');
const { validatePassages } = require('../src/validate');
const { buildPassageDocument, packDocx } = require('../src/document');
const { buildHtmlPassages, renderPdf } = require('../src/html');

const PORT = process.env.PORT || 3000;
const OUT_DIR = path.join(__dirname, '..', 'output', 'web');
fs.mkdirSync(OUT_DIR, { recursive: true });

const app = express();
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 30 * 1024 * 1024 }, // 30MB
  fileFilter: (req, file, cb) => {
    const ok = /pdf$/i.test(file.originalname) || file.mimetype === 'application/pdf';
    cb(ok ? null : new Error('PDF 파일만 업로드할 수 있어요.'), ok);
  },
});

app.use(express.static(path.join(__dirname, 'public')));
app.use('/download', express.static(OUT_DIR));

// 진행 상태를 담아 JSON 으로 응답
app.post('/api/generate', upload.single('pdf'), async (req, res) => {
  const steps = [];
  const log = (m) => { steps.push(m); console.log('•', m); };
  try {
    if (!req.file) return res.status(400).json({ ok: false, error: 'PDF 파일이 없어요.' });

    // 한글 파일명이 latin1 로 들어오는 경우 복원
    let fileName = req.file.originalname;
    try { fileName = Buffer.from(fileName, 'latin1').toString('utf8'); } catch (_) { /* 그대로 */ }
    log(`업로드 받음: ${fileName} (${(req.file.size / 1024).toFixed(0)}KB)`);

    // 2) 문장 추출
    const { sentences } = await extractSentences(req.file.buffer);
    log(`영어 문장 ${sentences.length}개 추출`);
    if (sentences.length < 2) {
      return res.status(422).json({ ok: false, error: '영어 문장을 충분히 찾지 못했어요. 텍스트가 들어있는 PDF 인지 확인해 주세요.', steps });
    }

    // 3) AI 구조화 — 지문(passage) 단위. 대량이면 지문별로 나눠 생성(잘림 방지).
    //    웹에서 입력한 API 키(있으면)를 그 요청에만 사용. (로그·저장 안 함)
    const apiKey = (req.body && req.body.apiKey ? String(req.body.apiKey).trim() : '') || undefined;
    if (apiKey) log('API 키 확인 — 실제 AI 로 생성 (지문이 많으면 몇 분 걸릴 수 있어요)');
    const { passages, mode } = await structurePassages(sentences, { apiKey, onProgress: log });
    log(`지문 데이터 생성 (${mode === 'mock' ? 'MOCK — API 키 없음' : 'Claude AI'}) · 지문 ${passages.length}개`);
    if (!passages.length) {
      return res.status(422).json({ ok: false, error: '지문으로 구성할 문장이 부족했어요.', steps });
    }

    // 4) 검증 (에러는 중단, 경고는 통과)
    const { errors, warnings } = validatePassages(passages);
    warnings.forEach((w) => log(`경고: ${w}`));
    if (errors.length) {
      return res.status(422).json({ ok: false, error: `데이터 검증 실패 (${errors.length}건)`, detail: errors, steps });
    }
    log('데이터 검증 통과');

    // 5) 렌더 — 파일명은 요청별 고유값
    const stamp = `book_${Date.now().toString(36)}`;
    const docxPath = path.join(OUT_DIR, `${stamp}.docx`);
    const pdfPath = path.join(OUT_DIR, `${stamp}.pdf`);
    const htmlPath = path.join(OUT_DIR, `${stamp}.html`);

    const buffer = await packDocx(buildPassageDocument(passages));
    fs.writeFileSync(docxPath, buffer);
    log('docx 생성 완료');

    const html = buildHtmlPassages(passages);
    fs.writeFileSync(htmlPath, html);
    await renderPdfEnsuringBrowser(html, pdfPath, log);

    const files = [{ label: 'docx (편집용)', url: `/download/${path.basename(docxPath)}` }];
    if (fs.existsSync(pdfPath)) files.unshift({ label: 'PDF (배포용)', url: `/download/${path.basename(pdfPath)}` });

    return res.json({ ok: true, mode, passages: passages.length, sentences: sentences.length, steps, files });
  } catch (err) {
    console.error(err);
    let msg = err.message || '서버 오류';
    const status = err.status || err.statusCode;
    if (status === 401) msg = 'Claude API 키가 올바르지 않아요. 키를 다시 확인해 주세요.';
    else if (status === 403) msg = '이 키로는 접근 권한이 없어요. (결제/권한 확인)';
    else if (status === 404) msg = '모델을 찾을 수 없어요. 키에 해당 모델(claude-opus-5) 권한이 있는지 확인해 주세요.';
    else if (status === 429) msg = '요청이 많아 잠시 후 다시 시도해 주세요 (rate limit).';
    else if (status === 529) msg = 'AI 서버가 혼잡해요. 잠시 후 다시 시도해 주세요.';
    else if (/Unexpected end of JSON|Unexpected token|JSON/i.test(msg)) msg = 'AI 응답이 잘렸어요. 다시 시도하거나 더 짧은 PDF 로 나눠서 올려 주세요.';
    return res.status(500).json({ ok: false, error: msg, steps });
  }
});

// 미들웨어(multer 등) 에러를 JSON 으로 — 프런트가 이유를 볼 수 있게
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  if (res.headersSent) return next(err);
  let msg = err.message || '요청 오류';
  if (err.code === 'LIMIT_FILE_SIZE') msg = 'PDF 가 너무 커요 (최대 30MB).';
  return res.status(400).json({ ok: false, error: msg });
});

app.get('/api/health', (req, res) => {
  res.json({ ok: true, hasKey: !!process.env.ANTHROPIC_API_KEY, model: process.env.ANTHROPIC_MODEL || 'claude-opus-5' });
});

// PDF 렌더. 브라우저(Chromium)가 없으면 최초 1회 자동 설치 후 재시도해 PDF 도 꼭 나오게 한다.
let browserInstallTried = false;
async function renderPdfEnsuringBrowser(html, pdfPath, log) {
  try {
    await renderPdf(html, pdfPath);
    log('디자인 PDF 생성 완료');
    return true;
  } catch (e1) {
    if (!browserInstallTried) {
      browserInstallTried = true;
      log('PDF용 브라우저(Chromium)가 없어 설치를 시도합니다 (최초 1회, 1~2분 걸려요)…');
      try {
        require('child_process').execSync('npx playwright install chromium', {
          cwd: path.join(__dirname, '..'), stdio: 'ignore',
        });
        await renderPdf(html, pdfPath);
        log('브라우저 설치 완료 · 디자인 PDF 생성 완료');
        return true;
      } catch (e2) {
        log(`PDF 생성 실패 — 터미널에서  npx playwright install chromium  실행 후 다시 시도해 주세요. (docx 는 정상)`);
        return false;
      }
    }
    log('PDF 생성 실패 — 브라우저 미설치 (docx 는 정상). npx playwright install chromium 후 재시도.');
    return false;
  }
}

// 서버가 준비되면 기본 브라우저를 자동으로 연다(더블클릭 실행 편의). NO_OPEN=1 이면 끔.
function openBrowser(url) {
  if (process.env.NO_OPEN) return;
  try {
    const { exec } = require('child_process');
    const cmd = process.platform === 'win32' ? `start "" "${url}"`
      : process.platform === 'darwin' ? `open "${url}"` : `xdg-open "${url}"`;
    exec(cmd, () => {});
  } catch (_) { /* 무시 */ }
}

app.listen(PORT, () => {
  const url = `http://localhost:${PORT}`;
  console.log(`\n📘 필생보 교재 생성 웹앱이 켜졌어요 → ${url}`);
  console.log('   브라우저가 자동으로 열립니다. (안 열리면 위 주소를 직접 입력)');
  console.log('   이 창을 닫으면 웹앱도 꺼집니다. 끄려면 Ctrl + C.\n');
  console.log('   API 키: 웹 화면의 입력칸에 붙여넣으면 실제 AI 로 생성 (비우면 MOCK).\n');
  openBrowser(url);
});

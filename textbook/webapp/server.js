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
const { buildPassageDocument } = require('../src/document');
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

    log(`업로드 받음: ${req.file.originalname} (${(req.file.size / 1024).toFixed(0)}KB)`);

    // 2) 문장 추출
    const { sentences } = await extractSentences(req.file.buffer);
    log(`영어 문장 ${sentences.length}개 추출`);
    if (sentences.length < 2) {
      return res.status(422).json({ ok: false, error: '영어 문장을 충분히 찾지 못했어요. 텍스트가 들어있는 PDF 인지 확인해 주세요.', steps });
    }

    // 3) AI 구조화 — 지문(passage) 단위. 문장 원문 순서 유지 + 지문 요지.
    const { passages, mode } = await structurePassages(sentences);
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

    const buffer = await Packer.toBuffer(buildPassageDocument(passages));
    fs.writeFileSync(docxPath, buffer);
    log('docx 생성 완료');

    const html = buildHtmlPassages(passages, { title: '지문 구문독해 워크북 (자동 생성)' });
    fs.writeFileSync(htmlPath, html);
    try {
      await renderPdf(html, pdfPath);
      log('디자인 PDF 생성 완료');
    } catch (e) {
      log(`PDF 렌더 건너뜀(playwright/Chromium 없음): ${e.message}`);
    }

    const files = [{ label: 'docx (편집용)', url: `/download/${path.basename(docxPath)}` }];
    if (fs.existsSync(pdfPath)) files.unshift({ label: 'PDF (배포용)', url: `/download/${path.basename(pdfPath)}` });

    return res.json({ ok: true, mode, passages: passages.length, sentences: sentences.length, steps, files });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ ok: false, error: err.message || '서버 오류', steps });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ ok: true, hasKey: !!process.env.ANTHROPIC_API_KEY, model: process.env.ANTHROPIC_MODEL || 'claude-opus-5' });
});

app.listen(PORT, () => {
  const key = process.env.ANTHROPIC_API_KEY ? '있음(실 AI)' : '없음(MOCK 폴백)';
  console.log(`\n📘 필생보 교재 생성 웹앱: http://localhost:${PORT}`);
  console.log(`   ANTHROPIC_API_KEY: ${key} · 모델: ${process.env.ANTHROPIC_MODEL || 'claude-opus-5'}\n`);
});

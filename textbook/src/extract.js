// extract.js — 업로드된 PDF 에서 영어 문장 후보를 뽑아낸다.
//
// WORKBOOK/모의고사 PDF 는 영어 지문 + 문항 번호 + (때로) 한글 해설이 섞여 있다.
// 여기서는 pdf-parse 로 순수 텍스트를 얻고, "영어 문장" 만 후보로 정리한다.
// 문장을 문법 챕터로 분류하고 chunks/vocab/catch 를 만드는 건 src/ai.js 의 몫.
//
//   extractSentences(buffer) → Promise<{ raw: string, sentences: string[] }>

// pdf-parse v2 는 { PDFParse } 클래스를 export 한다.
//   new PDFParse({ data: buffer }).getText() → { text, ... }
async function pdfToText(buffer) {
  const mod = require('pdf-parse');
  const PDFParse = mod.PDFParse || mod.default || mod;
  if (typeof PDFParse === 'function' && PDFParse.prototype && PDFParse.prototype.getText) {
    const parser = new PDFParse({ data: buffer });
    const res = await parser.getText();
    return res.text || '';
  }
  // 구버전 fallback: pdf-parse 를 함수로 직접 호출
  const res = await PDFParse(buffer);
  return res.text || '';
}

// 한 줄이 "영어 문장 후보" 인지 판별.
//  - 알파벳이 충분히 많고(영어 위주), 한글이 거의 없어야 함
//  - 문장부호로 끝나고, 너무 짧지 않아야 함
function looksEnglish(line) {
  const s = line.trim();
  if (s.length < 25) return false;                    // 너무 짧은 조각 제외
  const hangul = (s.match(/[가-힣]/g) || []).length;
  const latin = (s.match(/[A-Za-z]/g) || []).length;
  if (latin < 15) return false;                       // 영어 글자가 너무 적음
  if (hangul > latin * 0.15) return false;            // 한글이 섞이면 지문 아님(해설/보기)
  const words = s.split(/\s+/).filter(Boolean);
  if (words.length < 5) return false;                 // 최소 5단어
  return /[.!?]["')\]]?\s*$/.test(s);                 // 문장부호로 끝남
}

// 문항 번호("20.", "[41~42]", "32번" 등)와 페이지 머리말 제거
function stripNoise(text) {
  return text
    .replace(/\r/g, '')
    .replace(/[ \t]+/g, ' ')
    // 약어의 마침표를 없애 문장 분리 오작동 방지 (5 p.m. → 5 pm, e.g. → eg …)
    .replace(/\b([ap])\.\s*m\./gi, '$1m ')
    .replace(/\b(Mr|Mrs|Ms|Dr|St|vs|etc|Inc|Jr|Sr|Prof|No)\./g, '$1')
    .replace(/\be\.g\./gi, 'eg').replace(/\bi\.e\./gi, 'ie').replace(/\bU\.S\./g, 'US')
    // 각주 번호 제거 (문장 끝의 1) 2) … — 단, (1937) 같은 연도·괄호는 보존)
    .replace(/(?<![\d(])\d{1,3}\)/g, ' ')
    // 줄 앞의 문항 번호/불릿 제거
    .replace(/^\s*\(?\d{1,2}\)?[.)]\s*/gm, '')
    .replace(/^\s*[①-⑳]\s*/gm, '');
}

// 여러 줄에 걸쳐 끊긴 영어 문장을 이어 붙인 뒤, 문장 단위로 분리.
function joinAndSplit(text) {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const paras = [];
  let buf = '';
  for (const line of lines) {
    const hangul = (line.match(/[가-힣]/g) || []).length;
    const latin = (line.match(/[A-Za-z]/g) || []).length;
    // 영어 위주 줄만 이어붙임. 짧은 제목(예: 'WORKBOOK')이 지문에 섞이지 않도록
    // 최소 영문 글자 수(10)와 한글 대비 우세를 함께 요구.
    const isEngLine = latin >= 10 && latin > hangul;
    if (!isEngLine) { if (buf) { paras.push(buf); buf = ''; } continue; }
    buf = buf ? `${buf} ${line}` : line;
    if (/[.!?]["')\]]?$/.test(line)) { paras.push(buf); buf = ''; }
  }
  if (buf) paras.push(buf);

  // 문단을 문장 단위(.!? 기준)로 다시 쪼갬. 약어(Mr. U.S. 등)는 러프하게 허용.
  const out = [];
  for (const para of paras) {
    const parts = para.match(/[^.!?]+[.!?]+["')\]]?/g) || [para];
    parts.forEach((p) => out.push(p.trim()));
  }
  return out;
}

async function extractSentences(buffer) {
  const raw = await pdfToText(buffer);
  const cleaned = stripNoise(raw);
  const candidates = joinAndSplit(cleaned);

  const seen = new Set();
  const sentences = [];
  for (const c of candidates) {
    if (!looksEnglish(c)) continue;
    const key = c.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (seen.has(key)) continue;                      // 중복 문장 제거
    seen.add(key);
    sentences.push(c);
  }
  return { raw, sentences };
}

module.exports = { extractSentences, looksEnglish };

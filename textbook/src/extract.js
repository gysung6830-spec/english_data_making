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
    // 1) 각주 번호 먼저 제거 (문장 끝 1) 2) … — 단, (1937) 같은 연도·괄호는 보존).
    //    p.m. 뒤에 각주가 붙는 경우가 있어(예: "7 p.m.5)"), p.m. 처리보다 먼저 한다.
    .replace(/(?<![\d(])\d{1,3}\)/g, ' ')
    .replace(/^\s*\(?\d{1,2}\)?[.)]\s*/gm, '')  // 줄 앞 문항 번호/불릿
    .replace(/^\s*[①-⑳]\s*/gm, '')
    // 2) p.m./a.m.: 문장 끝(뒤에 대문자로 새 문장 시작)이면 마침표 1개 보존해 문장 분리 유지,
    //    그 외(뒤에 콤마·소문자 등 문장 중간)면 마침표를 없애 오분리 방지.
    .replace(/\b([ap])\.\s*m\.(\s+)(?=["'(]?[A-Z])/gi, '$1m.$2')
    .replace(/\b([ap])\.\s*m\./gi, '$1m ')
    .replace(/\b(Mr|Mrs|Ms|Dr|St|vs|etc|Inc|Jr|Sr|Prof|No)\./g, '$1')
    .replace(/\be\.g\./gi, 'eg').replace(/\bi\.e\./gi, 'ie').replace(/\bU\.S\./g, 'US');
}

// 여러 줄에 걸쳐 끊긴 영어 문장을 이어 붙인 뒤, 문장 단위로 분리.
function joinAndSplit(text) {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
  const paras = [];
  let buf = '';
  for (const line of lines) {
    const hangul = (line.match(/[가-힣]/g) || []).length;
    const latin = (line.match(/[A-Za-z]/g) || []).length;
    const lower = (line.match(/[a-z]/g) || []).length;
    // 영어 위주 줄만 이어붙임. 짧은 제목(예: 'WORKBOOK')이 지문에 섞이지 않도록
    // 최소 영문 글자 수(10)와 한글 대비 우세를 함께 요구.
    // 예외: 대사/서사에서 한 줄로 쪼개진 짧은 문장 조각("That was 처럼 10자 미만)도
    //   한글이 전혀 없고 소문자가 있는 '진짜 문장' 조각이면 이어붙인다.
    //   (대문자만인 헤더 'WORKBOOK'·'SINCERELY' 등은 소문자 조건으로 계속 배제)
    const isEngLine = (latin >= 10 && latin > hangul)
      || (hangul === 0 && lower >= 2 && latin >= 5);
    if (!isEngLine) { if (buf) { paras.push(buf); buf = ''; } continue; }
    buf = buf ? `${buf} ${line}` : line;
    if (/[.!?]["')\]]?$/.test(line)) { paras.push(buf); buf = ''; }
  }
  if (buf) paras.push(buf);

  // 문단을 문장 단위(.!? 기준)로 다시 쪼갬. 약어(Mr. U.S. 등)는 러프하게 허용.
  const out = [];
  for (const para of paras) {
    const parts = para.match(/[^.!?]+[.!?]+["')\]]?/g) || [para];
    // 문장 분리 후 남는 '온전한 문장이 못 되는 짧은 조각'(뒤 looksEnglish 의 25자·5단어
    //   기준 미달)은 버리지 말고 이웃 문장에 도로 붙여 원문을 보존한다.
    //   - 꼬리 조각("I'll let her know ...", "10:00.")은 앞 문장에 붙임
    //   - 선두 조각("Finally, the telephone rang.")은 다음 문장 앞에 붙임(carry)
    //   설명문 지문은 이런 조각이 없어 영향이 없다.
    const isShort = (s) => s.length < 25 || s.split(/\s+/).filter(Boolean).length < 5;
    const merged = [];
    let carry = '';
    for (const raw of parts) {
      const t = raw.trim();
      if (!t) continue;
      const piece = carry ? `${carry} ${t}` : t;
      carry = '';
      if (isShort(piece)) {
        if (merged.length) merged[merged.length - 1] += ` ${piece}`;
        else carry = piece;
      } else {
        merged.push(piece);
      }
    }
    if (carry) {
      if (merged.length) merged[merged.length - 1] += ` ${carry}`;
      else merged.push(carry);
    }
    merged.forEach((p) => out.push(p));
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

module.exports = { extractSentences, looksEnglish, stripNoise, joinAndSplit };

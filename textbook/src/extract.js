// extract.js — 업로드된 PDF 에서 영어 문장 후보를 뽑아낸다.
//
// WORKBOOK/모의고사 PDF 는 영어 지문 + 문항 번호 + (때로) 한글 해설이 섞여 있다.
// 여기서는 pdf-parse 로 순수 텍스트를 얻고, "영어 문장" 만 후보로 정리한다.
// 문장을 문법 챕터로 분류하고 chunks/vocab/catch 를 만드는 건 src/ai.js 의 몫.
//
//   extractSentences(buffer) → Promise<{ raw: string, sentences: string[] }>

// pdf-parse v2 는 { PDFParse } 클래스를 export 한다.
//   new PDFParse({ data: buffer }).getText() → { text, ... }
// 일부 PDF 는 폰트 인코딩 때문에 '공백'을 제어문자(U+0001 등)로 추출한다
// (space 글리프가 glyph #1 에 매핑되고 ToUnicode 가 U+0001 을 돌려주는 경우).
// 그대로 두면 단어가 "Many␁developmental␁theorists" 처럼 붙어 AI 입력이 깨진다.
//  → 제어문자·이색 공백을 일반 공백으로 정규화한다(줄바꿈·탭은 보존).
function normalizePdfText(t) {
  return String(t == null ? '' : t)
    // 제어문자(U+0000–U+0008, U+000B, U+000C, U+000E–U+001F) → 공백. \n(0A)·\t(09) 보존.
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, ' ')
    // 각종 유니코드 공백(NBSP·엇은공백·전각공백·BOM 등) → 공백
    .replace(/[\u00A0\u2000-\u200B\u202F\u205F\u3000\uFEFF]/g, ' ');
}

async function pdfToText(buffer) {
  const mod = require('pdf-parse');
  const PDFParse = mod.PDFParse || mod.default || mod;
  if (typeof PDFParse === 'function' && PDFParse.prototype && PDFParse.prototype.getText) {
    const parser = new PDFParse({ data: buffer });
    const res = await parser.getText();
    return normalizePdfText(res.text || '');
  }
  // 구버전 fallback: pdf-parse 를 함수로 직접 호출
  const res = await PDFParse(buffer);
  return normalizePdfText(res.text || '');
}

// 한 줄이 "영어 문장 후보" 인지 판별.
//  - 알파벳이 충분히 많고(영어 위주), 한글이 거의 없어야 함
//  - 문장부호로 끝나고, 너무 짧지 않아야 함
function looksEnglish(line) {
  const s = line.trim();
  if (s.length < 10) return false;                    // 너무 짧은 조각 제외(짧은 문장은 허용)
  const hangul = (s.match(/[가-힣]/g) || []).length;
  const latin = (s.match(/[A-Za-z]/g) || []).length;
  if (latin < 8) return false;                        // 영어 글자가 너무 적음
  if (hangul > latin * 0.15) return false;            // 한글이 섞이면 지문 아님(해설/보기)
  const words = s.split(/\s+/).filter(Boolean);
  if (words.length < 2) return false;                 // 최소 2단어("Wrong again." 같은 짧은 문장 허용)
  // URL/사이트 푸터 조각 배제(예: "flowedu. tistory. com!")
  if (/tistory|flowedu|https?:|www\./i.test(s)) return false;
  // 저작권 푸터·답지(재진술 사슬 화살표) 잡음 배제 — 실제 지문 문장엔 없음
  if (/all rights reserved|©|→/i.test(s)) return false;
  return /[.!?]["')\]]?\s*$/.test(s);                 // 문장부호로 끝남
}

// 영어 문장 안에 잘못 섞인 한글(및 그로 인해 남는 빈 괄호·중복 공백)을 제거.
function stripHangul(s) {
  return String(s)
    .replace(/[가-힣ㄱ-ㅎㅏ-ㅣ]+/g, ' ')       // 한글 음절/자모 제거
    .replace(/[（(]\s*[)）]|\[\s*\]|【\s*】/g, ' ') // 남은 빈 괄호 제거
    .replace(/\s+([,.;:!?)\]}])/g, '$1')          // 구두점 앞 공백 정리
    .replace(/([([{])\s+/g, '$1')                 // 여는 괄호 뒤 공백 정리
    .replace(/\s{2,}/g, ' ')
    .trim();
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
// 문장이 '인용부호가 열린 채' 끝나는지 판정(인용 안 닫힘 → 다음 문장이 같은 인용의 연속).
// 큰따옴표는 짝(홀수=열림), 작은따옴표는 '축약형 아포스트로피'를 빼고 여닫기만 센다.
function quoteOpen(s) {
  const sdq = (s.match(/"/g) || []).length;              // 곧은 큰따옴표
  const cdo = (s.match(/“/g) || []).length;          // 여는 큰따옴표 “
  const cdc = (s.match(/”/g) || []).length;          // 닫는 큰따옴표 ”
  if (sdq % 2 === 1) return true;
  if (cdo > cdc) return true;
  const so = (s.match(/(^|[\s(\[])['‘]/g) || []).length;         // 인용 여는 작은따옴표
  const sc = (s.match(/['’]([\s).,!?;:\]]|$)/g) || []).length;   // 인용 닫는 작은따옴표
  return so > sc;
}
// 인용부호가 문장 경계를 넘어 열린 채면(예: "…the end will come. And by …humanity.'")
// 다음 문장과 합쳐 한 문장으로 — 인용문 내부의 마침표에서 잘못 쪼개지는 것을 복원.
function mergeQuoted(arr) {
  const out = [];
  for (const s of arr) {
    if (out.length && quoteOpen(out[out.length - 1])) out[out.length - 1] += ` ${s}`;
    else out.push(s);
  }
  return out;
}
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
    // ★ 버퍼가 열려 있으면(문장 진행 중) '짧은 영어 꼬리 줄'(줄바꿈으로 넘어간 마지막
    //   한두 단어, 예: "own?" · "them." · "provide.")도 한글만 없으면 이어붙인다.
    //   → 문장 끝(구두점)이 다음 줄로 넘어가 통째로 버려지던 문제 방지.
    const isEngTail = buf && hangul === 0 && latin >= 1;
    if (!isEngLine && !isEngTail) { if (buf) { paras.push(buf); buf = ''; } continue; }
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
  return mergeQuoted(out);
}

async function extractSentences(buffer) {
  const raw = await pdfToText(buffer);
  const cleaned = stripNoise(raw);
  const candidates = joinAndSplit(cleaned);

  const seen = new Set();
  const sentences = [];
  for (const c of candidates) {
    if (!looksEnglish(c)) continue;
    // 영어 문장으로 통과했더라도 안에 섞인 한글(고유명사 옆 주석·병기 해석 등)은 지운다.
    // 영어 지문 문장은 원래 한글이 없으므로, 남은 한글은 잘못 붙은 것 → 제거 후 공백 정리.
    const clean = stripHangul(c);
    // 한글 제거 후에도 영어가 최소치 미만이면 버림. 짧은 대사 문장("Wrong again."=10자)도
    // 살리도록 8자로 낮춤 — URL/푸터 잡음은 이미 looksEnglish 에서 배제됨.
    if (clean.replace(/[^A-Za-z]/g, '').length < 8) continue;
    const key = clean.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (seen.has(key)) continue;                      // 중복 문장 제거
    seen.add(key);
    sentences.push(clean);
  }
  return { raw, sentences };
}

module.exports = {
  extractSentences, looksEnglish, stripNoise, joinAndSplit, stripHangul, normalizePdfText,
};

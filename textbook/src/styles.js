// styles.js — 문서 전역 스타일 상수 (색상 / 폰트 / 크기)
//
// 명세 §5.4 스타일 규칙을 한곳에 모아둔 모듈.
//  - 폰트는 문서 전체가 NanumSquareRound (영어 포함 동일 패밀리).
//  - 초록 계열 색상 사용 금지(명세 §5.4). 새 배색에도 초록을 넣지 말 것.
//  - docx 라이브러리의 size 값은 half-point 단위지만, 명세가 부르는 숫자
//    (27 / 22 / 19 …)를 그대로 size 로 넘겨 기존 build_v4 동작과 일치시킨다.

const FONT = 'NanumSquareRound';
const FONT_EN = 'NanumSquareRound'; // 영어도 동일 폰트, 볼드+확대로 강조

// 문서 공통 색
const NAVY = '1F3864';       // 제목/소제목
const BRASS = 'B08D57';      // 강조(초록 대체), 박스 테두리
const LIGHTGRAY = 'F2F2F2';  // 사용법 안내 배경
const CATCHBG = 'FFF3D6';    // 캐치 박스 배경
const SLASH = 'C0392B';      // 끊어읽기 화살표(→) — 붉은 계열

// 박스별 배경(fill) / 테두리(border) / 글자(txt) — 명세 §5.2
const VOCAB = { bg: 'EAF1FB', border: '5B7FA6', txt: '2C4A6E' }; // 📘 어휘
const CHUNK = { bg: 'FBEFE0', border: BRASS, txt: '6B4A1E' };    // ✂ 끊어읽기
const TRAP = { bg: 'FEF3E2', border: 'E08A1E', label: 'B5651D', txt: '7A4A12' }; // ⚠️ 이거 조심(함정)
const CATCH = { border: BRASS, txt: '5C3D00', label: '8A5A00' }; // ✅ 캐치
const TIP = { bg: 'F0F0F0', border: '999999', txt: '555555' };   // 💡 팁
const WRITE = { bg: 'FFFFFF', border: '333333' };                // ✏️ 내 해석 써보기
const UNDERLINE = 'AAAAAA';  // 빈 밑줄 색

module.exports = {
  FONT, FONT_EN,
  NAVY, BRASS, LIGHTGRAY, CATCHBG, SLASH,
  VOCAB, CHUNK, TRAP, CATCH, TIP, WRITE, UNDERLINE,
};

// styles.js — 문서 전역 스타일 상수 (색상 / 폰트 / 크기)
//
// 명세 §5.4 스타일 규칙을 한곳에 모아둔 모듈.
//  - 폰트는 문서 전체가 NanumSquareRound (영어 포함 동일 패밀리).
//  - 초록 계열 색상 사용 금지(명세 §5.4). 새 배색에도 초록을 넣지 말 것.
//  - docx 라이브러리의 size 값은 half-point 단위지만, 명세가 부르는 숫자
//    (27 / 22 / 19 …)를 그대로 size 로 넘겨 기존 build_v4 동작과 일치시킨다.

const FONT = 'NanumSquareRound';

// 박스별 배경(fill) / 테두리(border) 색 — 명세 §5.2
const COLORS = {
  vocab:    { fill: 'EAF1FB', border: '5B7FA6' }, // 📘 어휘 박스
  chunk:    { fill: 'FBEFE0', border: 'B08D57' }, // ✂ 끊어읽기 박스 (테두리 브라스)
  skeleton: { fill: 'ECEAF6', border: '7A5FA6' }, // 🦴 뼈대·괄호 박스
  write:    { fill: 'FFFFFF', border: '595959' }, // ✏️ 내 해석 써보기 박스 (흰 배경/짙은 회색)
  catch:    { fill: 'FFF3D6', border: 'B08D57' }, // ✅ 이 정도는 캐치! 박스 (테두리 브라스)
  tip:      { fill: 'F0F0F0', border: '999999' }, // 💡 팁 박스
};

// 텍스트 색상 (본문/헤더) — 초록 금지 규칙 준수
const INK = {
  default:  '1A1A1A', // 기본 검정 계열
  muted:    '595959', // 옅은 회색(밑줄/보조 라벨)
  brass:    '8A6D3B', // 브라스 계열 강조(초록 대체)
};

// 크기 (명세가 부르는 숫자를 그대로 사용 — docx size 필드에 전달)
const SIZE = {
  headerEn:   27, // 영어 원문 헤더 (bold)
  chunkEn:    22, // 끊어읽기 영어 (bold)
  chunkKor:   19, // 끊어읽기 한글
  body:       20, // 일반 본문
  label:      20, // 박스 라벨(이모지 제목)
  small:      18, // 보조 문구(팁 등)
};

module.exports = { FONT, COLORS, INK, SIZE };

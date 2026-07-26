# 수능 구문해석 교재 자동 생성기 (Node.js)

"문법으로 뚫는 영어 해석" 워크북을 코드로 생성하는 도구.
수능 기출 문장을 문법 챕터별로 **[설명 → 같이 풀어보기(2문장) → 혼자 풀어보기(나머지 전부)]**
구성의 `.docx` / `.pdf` 로 만들어 준다.

`data.js` 에는 2023학년도 수능(20~24 · 31 · 32 · 35 · 40 · 41-42번) 기출 문장이
들어 있다. 챕터를 추가하거나 문장을 바꿀 때는 §"데이터 스키마"의 불변식만 지키면 된다.

## 목차 순서 (확정)

```
① 수동태 → ② to부정사 → ③ 동명사 → ④ 관계사 → ⑤ 분사 → ⑥ 분사구문
```

챕터를 추가/재배열하면 `title` 의 원문자 번호(①~⑥)도 함께 갱신해야 한다.
(`validate.js` 가 순서 번호 누락을 경고로 잡아 준다.)

## 실행

```bash
npm install          # docx 설치 (최초 1회)
npm run validate     # 데이터 불변식 검사만
npm run build        # output/output_v4.docx + .pdf 생성
npm run build:docx   # docx 만 (LibreOffice 없을 때)
```

또는 직접:

```bash
node build_v4.js                 # docx + pdf
node build_v4.js --no-pdf        # docx 만
node build_v4.js --out mybook    # output/mybook.docx / .pdf
```

### PDF 변환

`build_v4.js` 는 LibreOffice(`soffice`)를 headless 로 불러 docx → pdf 변환한다.

```
soffice --headless --convert-to pdf --outdir output output/output_v4.docx
```

soffice 는 변환에 실패해도 종료 코드 0 을 반환하는 버릇이 있어서, 빌드 스크립트는
**실제 pdf 파일이 새로 생겼는지** 확인한 뒤에만 성공으로 처리한다. 변환이 안 되면
docx 만 만들고, 위 수동 변환 명령을 안내한다.

## 폴더 구조 (리팩터링 후)

```
textbook/
  data.js              교재 데이터 (6챕터, 명세 §4 스키마)
  build_v4.js          빌드 진입점: 검증 → docx → pdf (명세 §5.5)
  validate.js          데이터 검증만 단독 실행 (CI/사전 점검)
  src/
    styles.js          색상·폰트·크기 상수 (명세 §5.4)
    tip.js             "왜 여기서 끊었을까?" 팁 자동 생성 (명세 §5.3)
    boxes.js           재사용 박스/문단 빌더 (명세 §5.2)
    document.js        표지·챕터·정답 조립 (명세 §5.1)
    validate.js        불변식 검증 로직
  output/              생성물(.docx/.pdf) — git 에는 올리지 않음
```

예전 단일 파일이던 렌더러를 위 모듈로 분리했다(명세 우선순위 #2).

## 데이터 스키마 (`data.js`)

```ts
type Chunk = [en: string, kor: string];    // 끊어읽기 한 덩어리(영어, 한글)
type Step  = [label: string, text: string];

type Sentence = {
  src: string;            // 문항 번호 ("21", "41-42" …)
  en: string;             // 원문 전체
  chunks: Chunk[];         // 순서대로 이어붙이면 전체 번역이 되도록
  catch: string;           // "이 정도는 캐치!" — 강사 반말 지도 톤
  vocab: [string, string][];
  steps?: Step[];          // worked 에만 있음 (practice 는 없음)
};

type Category = {
  key: string;             // "수동태" 등
  title: string;            // "① 수동태 — …" (원문자 번호 포함)
  intro: string[];          // "무엇인가요?"
  signal: string[];         // "어떻게 찾나요? (신호)"
  method: Step[];           // "어떻게 해석하나요?"
  worked: Sentence[];       // 정확히 2개 (steps 포함)
  practice: Sentence[];     // 나머지 전부 (steps 없음)
};
```

### worked / practice 자동 분배

데이터의 `worked` 에는 **2문장을 초과해 넣어도 된다.** 빌드 시 `src/document.js`
의 `splitWorked()` 가 각 챕터의 `worked` 앞 2문장만 "같이 풀어보기" 로 쓰고,
나머지는 `steps` 를 떼어 "혼자 풀어보기(practice)" 앞쪽으로 옮긴다. 따라서
**최종 산출물의 `worked` 는 항상 정확히 2문장**이 된다(명세 §4 불변식은 빌드 결과 기준).

### 불변식 (`validate.js` 가 검사)

- `worked.length >= 2` (앞 2개만 같이 풀어보기로 사용, 나머지는 practice 로 이동)
- 모든 문장에 `src`/`en`/`chunks`/`vocab`/`catch` 가 비어있지 않음
- worked 는 `steps` 가 **있어야** 하고, practice 는 `steps` 가 **없어야** 함
- `title` 의 원문자 번호가 챕터 순서와 일치 (불일치 시 경고)
- `chunks` 를 순서대로 이어 붙인 한글이 정답 섹션에 그대로 쓰이므로,
  이어 읽었을 때 자연스러운 문장이 되도록 작성

## 스타일 규칙 (`src/styles.js`)

- 폰트: `NanumSquareRound` (문서 전체 기본값, 영어 포함). 선생님 PC 에 이 폰트가
  설치돼 있어야 docx 가 의도대로 렌더링된다.
- **초록 계열 색상 사용 금지** (명세 §5.4). 새 박스 배색에도 초록을 넣지 말 것.
- 말투: 모든 설명·박스 문구는 강사가 학생에게 말하는 **반말 지도 톤**.
- 영어 강조: 문장 헤더·끊어읽기 박스의 영어는 항상 bold + 확대. 한글은 강조 안 함.

## 박스 순서 (문장 하나당, 고정 — 명세 §5.2)

1. 영어 원문 헤더 (bold, size 27, 문항번호 태그)
2. 📘 어휘 박스
3. ✂ 끊어읽기 박스 (영어 bold size 22 → 한글 size 19)
4. 🦴 뼈대·괄호 박스 (worked=steps 표시 / practice=빈 밑줄)
5. ✏️ 내 해석 써보기 박스 (practice 만)
6. ✅ 이 정도는 캐치! 박스
7. 💡 팁 박스 ("왜 여기서 끊었을까?" 자동 생성)

각 박스는 docx 에 여러 문단을 하나의 테두리로 묶는 기능이 없어 **1×1 표**로 구현했다.

## 남은 작업 (명세 §7)

- [x] 목차 순서 확정 + `title` 번호 (우선순위 #1)
- [x] 렌더러 모듈 분리 (우선순위 #2)
- [x] 데이터 검증 스크립트 (우선순위 #3)
- [x] 실제 2023 수능 기출 문장으로 `data.js` 채움
- [ ] (선택) NanumSquareRound 폰트 파일 포함 + 로컬 폰트 등록 스크립트 (우선순위 #4)
- [ ] (선택) 나머지 문법 챕터(동격/비교·도치/간접의문문·명사절/강조구문) 추가 (우선순위 #5)
- [ ] (선택) WORKBOOK PDF → 문장 후보 추출 파서 (우선순위 #6)

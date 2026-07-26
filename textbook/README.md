# 수능 구문해석 교재 자동 생성기 (Node.js)

"문법으로 뚫는 영어 해석" 워크북을 코드로 생성하는 도구.
수능 기출 문장을 문법 챕터별로 **[설명 → 같이 풀어보기(2문장) → 혼자 풀어보기(나머지 전부)]**
구성의 `.docx` / `.pdf` 로 만들어 준다.

`data.js` 에는 2023학년도 수능(20~24 · 31 · 32 · 35 · 40 · 41-42번) 기출 문장이
들어 있다. 챕터를 추가하거나 문장을 바꿀 때는 §"데이터 스키마"의 불변식만 지키면 된다.

## 목차 순서 (확정)

```
① 전치사구 → ② 수동태 → ③ to부정사 → ④ 동명사 → ⑤ 관계사 → ⑥ 분사 → ⑦ 분사구문
```

챕터를 추가/재배열하면 `title` 의 원문자 번호(①~⑦)도 함께 갱신해야 한다.
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

### 디자인 PDF (`npm run preview`) — 배포용 예쁜 버전

참고 교재(김은아영어연구소) 스타일의 디자인을 적용한 **배포용 PDF** 를 만든다:

```bash
npm run preview   # output/output_v4_preview.pdf (Chromium 인쇄)
```

디자인 언어(청록/그린 강조, 라운드 배지, 번호 원형 섹션 헤더, 컬러 필 문법 카드,
끊어읽기(영어 한 줄+한글 한 줄, / 구분), 그린 헤더 zebra 단어표, 하단 저작권/페이지)는
`preview_pdf.js` 의 HTML/CSS 에 있고, 내용은 `build_v4.js` 와 **같은**
`data.js` / `splitWorked` / `makeTip` 을 공유한다.

- **`build_v4.js` → docx**: 텍스트 편집용(선생님이 문구 수정). LibreOffice 로 pdf 변환도 가능.
- **`preview_pdf.js` → pdf**: 위 디자인이 입혀진 배포용. 편집은 `data.js` 에서.
  각 챕터(목차)는 항상 **새 페이지에서 시작**하고, 하단에 저작권+페이지 번호가 붙는다.

(`playwright` 는 optionalDependencies — 디자인 PDF 를 만들 때만 설치.)

### 폰트 — NanumSquareRound (나눔스퀘어라운드)

`fonts/` 에 NanumSquareRound(L/R/B/EB, OFL-1.1)를 포함한다.

- **디자인 PDF(`preview_pdf.js`)**: `fonts/*.woff2` 를 base64 로 **임베드**하므로,
  별도 설치 없이 어디서 만들어도 나눔스퀘어라운드로 렌더된다.
- **docx→LibreOffice PDF(`build_v4.js`)**: docx 는 폰트를 이름으로만 참조하므로,
  변환 PC 에 폰트가 설치돼 있어야 정확히 렌더된다. 아래로 설치:

```bash
bash setup_fonts.sh   # fonts/*.ttf → ~/.local/share/fonts + fc-cache
# Windows: fonts/*.ttf 더블클릭 → '설치'
```

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

## 박스 순서 (문장 하나당, 고정)

1. 영어 원문 헤더 (bold, 문항번호 태그 — 2024 9월 모평 추가분은 `[9월 N번]`)
2. 📘 어휘 — docx 는 문장별 박스, 디자인 PDF 는 챕터 상단 **단어 완전정복** 표로 모아 표시
3. ✂ **끊어읽기 팁 — 어디서 끊을까?** (자동 생성, 읽기 전 안내)
4. ✂ 끊어읽기 (영어 한 줄 → 한글 한 줄, `/` 로 청크 구분)
5. 🦴 뼈대·괄호 (worked = steps 표시 / practice = 빈칸)
6. ✏️ 내 해석 써보기 (practice 만)
7. ✅ **이 정도는 캐치!** (이 문장의 핵심 뜻 — 아래 가이드라인 참고)
   - **같이 풀어보기**: 문제 밑에 그대로 표시(쌤이 풀어주는 예시)
   - **혼자 풀어보기**: 문제 밑에는 두지 않고 **맨 뒤 '정답·해설' 섹션**에 표시(스포일러 방지).
     연습문제는 한글 끊어읽기도 빈칸이라 학생이 직접 채운다.

docx 는 각 박스를 여러 문단을 하나의 테두리로 묶을 수 없어 **1×1 표**로 구현했다.

### 정답·해설 (맨 뒤, 혼자 풀어보기)

모든 문제가 끝난 뒤 맨 뒤 **정답·해설** 섹션에서, 연습문제마다
**끊어읽기 정답(영어 / 한글) + 핵심(캐치)** 을 챕터별로 정리해 보여 준다.
(상세 뼈대·괄호 분석은 '같이 풀어보기'가 모델을 제시하므로 해설에는 넣지 않음.)

## 콘텐츠 작성 가이드라인

### ✅ "이 정도는 캐치" 에 담는 핵심 내용 (분량 기준)

**한 줄 정의**: *"이 문장에서 딱 이것만 이해하면 통과"* — 그 문장의 요지 한 줄.
세부는 버리고 **핵심 메시지 하나**만 담는다.

| 항목 | 기준 |
|---|---|
| **분량** | 한 문장(한 줄), 대략 20~45자. 두 줄 넘어가면 캐치가 아님 |
| **범위** | "누가/무엇이 → 어쨌다"는 **주 메시지 1개**. 곁가지 수식·부연은 압축하거나 생략 |
| **말투** | "~는 거예요!" 친근한 반말 지도 톤(학생 격려조) |
| **문법 용어** | **쓰지 않는다** — 전치사구·분사 등 용어 설명은 ③ 끊어읽기 팁·해석법이 담당 |
| **형태** | 청크별 직역이 아니라 자연스러운 우리말 **요약** |

**역할 분담(겹치지 않게):**
- 끊어읽기(한글 줄) = 청크별 직독직해(문장 전체를 순서대로)
- 정답 섹션(맨 뒤) = 청크를 이어 붙인 전체 해석
- **이 정도는 캐치 = 위 둘을 다 못 외워도 이 한 줄만은 붙잡아라 하는 요지**

**예시** — *He went to the United States in 1937, and about a decade later, he started teaching visual design at MIT.*
- ✅ 적정: `"그는 1937년에 미국으로 가서, 약 10년 뒤 MIT에서 시각 디자인을 가르치기 시작했다는 거예요!"` (두 핵심 사건만 압축)
- ❌ 너무 많음: 연도·기관·과목을 다 나열해 직역에 가까워짐 → 그건 '정답 해석'이지 캐치가 아님
- ❌ 너무 적음: `"그가 미국에 갔대!"` → 문장 절반(MIT 강의)을 빠뜨림

즉 **직역(정답)과 뼈만 남긴 요약의 중간** — "이 문장이 결국 무슨 말이야?"에 한 문장으로 답하는 수준.

## 남은 작업 (명세 §7)

- [x] 목차 순서 확정 + `title` 번호 (우선순위 #1)
- [x] 렌더러 모듈 분리 (우선순위 #2)
- [x] 데이터 검증 스크립트 (우선순위 #3)
- [x] 실제 2023 수능 기출 문장으로 `data.js` 채움
- [x] NanumSquareRound 폰트 포함(PDF 임베드) + 로컬 폰트 등록 스크립트 (우선순위 #4)
- [ ] (선택) 나머지 문법 챕터(동격/비교·도치/간접의문문·명사절/강조구문) 추가 (우선순위 #5)
- [ ] (선택) WORKBOOK PDF → 문장 후보 추출 파서 (우선순위 #6)

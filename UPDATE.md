# 🔄 더블클릭으로 실행·업데이트하기 (윈도우)

한 번만 세팅해두면, 그다음부터는 **파일 더블클릭**만으로
- `start.bat` → 웹앱 실행
- `update.bat` → 최신 코드로 업데이트

가 됩니다. (매번 ZIP 다시 받을 필요 없어요.)

---

## ① 최초 1회 세팅 (Git 설치 + 코드 받기)

### 1. Git 설치
1. 브라우저에서 **git-scm.com** 접속 → **Download for Windows** 클릭
2. 받은 설치 파일 실행 → 계속 **Next** (기본값 그대로) → **Install**
   (뭘 고를지 모르면 전부 기본값으로 두면 됩니다)

### 2. 코드를 받을 위치 정하기
- 예: `문서(Documents)` 폴더를 쓸게요.
- 파일 탐색기로 **문서 폴더**에 들어가서 → 주소 표시줄에 **`cmd`** 입력 → Enter (까만 창 열림)

### 3. 코드 내려받기 (딱 한 줄)
까만 창에 아래를 **그대로 복사해서 붙여넣고** Enter:
```
git clone -b claude/english-passage-analysis-tool-giy07l https://github.com/gysung6830-spec/english_data_making.git
```
- 처음엔 **GitHub 로그인 창(브라우저)** 이 뜰 수 있어요 → 로그인하면 됩니다. (한 번만)
- 끝나면 `english_data_making` 폴더가 생겨요.

### 4. 부품(라이브러리) 설치 (최초 1회)
```
cd english_data_making
pip install -r requirements.txt
```
- (GTK3(PDF 엔진)를 아직 안 깔았다면, README의 5단계대로 한 번 설치)

---

## ② 매일 쓰기 — `start.bat` 더블클릭
- `english_data_making` 폴더 안의 **`start.bat`** 파일을 **더블클릭**
- 잠시 후 브라우저가 자동으로 `localhost:5000` 을 엽니다.
- 종료할 땐 까만 창에서 **Ctrl + C**.

> 주소는 항상 `localhost:5000` 로 똑같아요.

---

## ③ 수정사항 반영 — `update.bat` 더블클릭
- 제가 코드를 고쳤다는 얘기를 들으면, **`update.bat`** 파일을 **더블클릭**
- "업데이트 완료!" 가 뜨면 → 다시 `start.bat` 으로 실행
- 끝이에요. (ZIP 다시 받을 필요 없음)

---

## 자주 묻는 것
- **`update.bat` 이 "Git 이 없어요" 라고 나와요** → ①-1의 Git 설치를 안 한 거예요. 설치 후 다시.
- **더블클릭했더니 까만 창이 잠깐 떴다 사라져요** → 폴더 위치가 맞는지 확인하세요. `start.bat`/`update.bat` 은 반드시 `webapp.py` 가 같이 있는 폴더 안에서 실행돼야 해요.
- **API 키** → 코드가 아니라 웹 화면에 입력하므로, 업데이트해도 그대로예요.

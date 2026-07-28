# 은아T 클래스 앱 — 1단계 스타터

## 여기 들어있는 것
- 로그인 화면
- 학생 홈 화면 + 은아T comment 목록 (Supabase에서 실제로 불러옴)

## 시작하는 법 (순서대로)

### 1. Supabase 프로젝트 만들기
supabase.com → 가입 → New Project 생성

### 2. config.js에 키 채워넣기
Supabase 대시보드 → Settings → API 에서
- Project URL
- anon public key
이 두 개를 복사해서 `config.js` 파일 안에 붙여넣으세요.

### 3. 테이블 만들기
Supabase 대시보드 → SQL Editor → 아래 SQL 실행:

```sql
create table comments (
  id uuid default gen_random_uuid() primary key,
  class_name text,
  title text not null,
  created_at timestamp with time zone default now()
);

-- 로그인한 사람만 읽을 수 있게 설정
alter table comments enable row level security;
create policy "로그인한 사용자는 읽기 가능"
  on comments for select
  using (auth.role() = 'authenticated');
```

### 4. 테스트용 계정 + 데이터 만들기
- Authentication → Users → Add user 로 학생 테스트 계정 하나 생성 (이메일/비번)
- Table Editor → comments → 행 추가로 은아T comment 샘플 하나 입력

### 5. 로컬에서 확인하기
`index.html` 파일을 더블클릭해서 브라우저로 열면 바로 확인 가능
(로그인 화면에서 3번에서 만든 테스트 계정으로 로그인)

### 6. 인터넷에 배포하기 (무료, 링크로 학부모님께 공유)
1. netlify.com 가입 (무료)
2. 이 폴더 전체를 그대로 드래그해서 업로드 ("Deploy manually")
3. 몇 초 후 `https://무작위이름.netlify.app` 같은 링크 생성됨
4. 이 링크를 학생/학부모님께 보내면 됨 — 아이폰에서는 Safari로 열고
   공유 버튼 → "홈 화면에 추가" 하면 앱처럼 아이콘이 생김

## 다음 단계
이 스타터가 잘 작동하면, 다음 화면들을 순서대로 추가해나가면 돼요:
1. 오답노트 제출 (사진 업로드)
2. 영작 Quiz
3. 강사(관리자) 화면
4. 학부모 화면

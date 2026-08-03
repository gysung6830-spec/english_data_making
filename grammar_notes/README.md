# 특강용 문법 필기 교재 (빈칸 채우기형)

원본 교재 목차(UNIT 01~10, 각 Point 4개 + Unit Practice + Wrap Up)를 바탕으로
**특강 板書·필기용 빈칸 교재**를 PDF로 생성합니다. UNIT마다 두 가지 PDF가 나옵니다.

- **학생용(필기본)** — 핵심 개념·예문 일부가 빈칸으로 비어 있어 강의를 들으며 채웁니다.
- **교사용(정답본)** — 같은 레이아웃에 정답이 형광 표시되어 있습니다.

## 생성 방법

```bash
pip install weasyprint pyyaml   # 최초 1회 (setup.sh로도 설치됨)
python -m grammar_notes.build 01   # UNIT 01 → output/ 에 학생용·교사용 PDF 2종
```

결과물:
- `output/특강문법_UNIT01_주어의 형태_학생용.pdf`
- `output/특강문법_UNIT01_주어의 형태_교사용_정답.pdf`

## 폴더 구조

```
grammar_notes/
  generator.py       빈칸 파서 + HTML/CSS + PDF 렌더링(WeasyPrint)
  build.py           빌드 진입점 (python -m grammar_notes.build <UNIT번호>)
  units/
    unit01.py        UNIT 01 콘텐츠 (현재 샘플)
    unit02.py ~       ← 이 형식대로 추가하면 나머지 UNIT도 동일 디자인으로 생성
```

## 콘텐츠 작성 규칙 (units/unitXX.py)

빈칸/강조는 텍스트 안에 마크업으로 표기합니다.

| 표기 | 학생용 | 교사용 |
|---|---|---|
| `{{정답}}` | 밑줄 빈칸 | 형광 정답 |
| `{{정답\|\|힌트}}` | 빈칸 + 작은 힌트 | 형광 정답 |
| `**굵게**` | 굵은 글씨(빈칸 아님) | 동일 |
| `__밑줄__` | 밑줄(구문 표시용) | 동일 |

`**{{정답}}**` 처럼 빈칸을 굵게 감싸도 정상 처리됩니다.

## 디자인

원본 교재의 **초록 테마**(UNIT 배지=진초록, Point=초록, Tip 박스, 지브라 표)를 따르며,
한글은 NanumSquareRound 폰트를 PDF에 임베드해 어느 환경에서도 동일하게 보입니다.

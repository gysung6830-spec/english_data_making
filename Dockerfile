# 영어 지문 분석 웹앱 - 인터넷 배포용 이미지
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# WeasyPrint(6개 분석 자료 렌더) 시스템 라이브러리
#  + 폰트: 한글=나눔고딕(fonts-nanum), 영어 세리프=Liberation Serif(fonts-liberation)
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
      libffi-dev shared-mime-info fonts-nanum fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# 통합 워크북(--workbook) PDF 렌더용 Chromium + 그 시스템 의존성 설치
RUN python -m playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*

COPY . .

# 대량/사진 처리는 시간이 걸리므로 타임아웃을 넉넉히(10분) 준다.
CMD gunicorn -w 2 -k gthread --threads 4 --timeout 600 -b 0.0.0.0:${PORT} webapp:app

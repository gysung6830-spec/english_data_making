# 영어 지문 분석 웹앱 - 인터넷 배포용 이미지
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# WeasyPrint(PDF 렌더) 시스템 라이브러리 + 한글 폰트(나눔고딕)
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
      libffi-dev shared-mime-info fonts-nanum \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 대량/사진 처리는 시간이 걸리므로 타임아웃을 넉넉히(10분) 준다.
CMD gunicorn -w 2 -k gthread --threads 4 --timeout 600 -b 0.0.0.0:${PORT} webapp:app

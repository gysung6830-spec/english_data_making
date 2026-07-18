"""영어 시험지 자동 생성 — 웹앱 (Flask).

지문을 붙여넣고 옵션을 고르면 브라우저에서 바로 시험지 PDF를 미리보기/다운로드한다.
- API 키가 없으면 '데모' 모드로 내장 지문(DNA·star manager)을 사용해 미리볼 수 있다.
- API 키가 있으면 입력한 지문으로 Claude가 7종 문항을 생성한다.

실행: python webapp.py  (기본 http://127.0.0.1:5000)
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from exam import renderer, validator
from exam.demo_data import demo_passages
from src.config import load_config

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "web"
OUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

_FID_RE = re.compile(r"^[0-9a-f]{6,32}$")
_SEP_RE = re.compile(r"(?m)^\s*-{3,}\s*$")   # 지문 구분: --- 한 줄


def split_passages(text: str) -> list[str]:
    """'---' 한 줄로 구분된 여러 지문을 나눈다(구분선이 없으면 전체를 지문 1개로)."""
    blocks = _SEP_RE.split(text or "")
    return [b.strip() for b in blocks if b.strip()]


def _pdf_path(fid: str) -> Path:
    if not _FID_RE.match(fid):
        abort(404)
    return OUT / f"exam_{fid}.pdf"


@app.get("/")
def index():
    cfg = load_config()
    return render_template("index.html", has_api_key=cfg.has_api_key, error=None)


@app.post("/generate")
def generate():
    cfg = load_config()
    # 'demo' 버튼을 눌렀을 때만 데모. '시험지 생성'은 항상 입력 지문을 사용한다.
    demo = request.form.get("action") == "demo"
    header = (request.form.get("header") or "").strip()
    vocab_method = request.form.get("vocab_method", "synonym")
    content_difficulty = request.form.get("content_difficulty", "hard")

    fid = uuid.uuid4().hex[:12]
    out = _pdf_path(fid)

    def fail(msg: str, code: int = 400):
        return render_template("index.html", has_api_key=cfg.has_api_key, error=msg), code

    uploads = [f for f in request.files.getlist("files") if f and f.filename]

    try:
        if demo:
            passages = demo_passages()
            validator.validate_passages(passages)
            validator.validate_numbering(passages, start=1)
            renderer.render_pdf(passages, out, header_note=header)
            n = len(passages)
        else:
            pasted = split_passages(request.form.get("passages", ""))
            if not uploads and not pasted:
                return fail("지문을 붙여넣거나 파일(PDF·사진)을 올리거나 '데모'를 선택하세요.")
            if not cfg.has_api_key:
                return fail("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env에 키를 넣거나 "
                            "'API 없이 데모'를 사용하세요.")
            from exam import ingest
            from exam.llm import ClaudeClient
            from exam.pipeline import build_exam
            client = ClaudeClient(cfg.api_key, cfg.model)

            if uploads:
                # 업로드 파일 저장(PDF/사진) → 지문 추출(사진은 비전으로 읽음)
                updir = OUT / "uploads" / fid
                updir.mkdir(parents=True, exist_ok=True)
                paths = []
                for i, f in enumerate(uploads, 1):
                    ext = Path(f.filename).suffix.lower()
                    if not ingest.is_supported(f"x{ext}"):
                        return fail(f"지원하지 않는 형식입니다: {f.filename} "
                                    "(.txt/.pdf/.jpg/.png/.webp)")
                    dest = updir / f"upload_{i}{ext}"
                    f.save(dest)
                    paths.append(dest)
                bodies = [b for _, b in ingest.load_bodies(paths, client=client)]
            else:
                bodies = pasted

            if not bodies:
                return fail("지문을 추출하지 못했습니다. 파일 내용을 확인해 주세요.")
            build_exam(client, bodies, out, header_note=header,
                       max_retries=cfg.processing.max_retries,
                       vocab_method=vocab_method,
                       content_difficulty=content_difficulty)
            n = len(bodies)
    except Exception as e:  # noqa: BLE001 — 사용자에게 원인 표시
        return fail(f"생성 실패: {e}", 500)

    return render_template("result.html", fid=fid, count=n,
                           demo=demo, header=header)


@app.get("/pdf/<fid>")
def pdf(fid: str):
    p = _pdf_path(fid)
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="application/pdf")   # 브라우저 인라인 미리보기


@app.get("/download/<fid>")
def download(fid: str):
    p = _pdf_path(fid)
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="application/pdf", as_attachment=True,
                     download_name="영어시험지.pdf")

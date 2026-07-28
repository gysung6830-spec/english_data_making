"""영어 시험지 자동 생성 — 웹앱 (Flask).

지문을 붙여넣고 옵션을 고르면 브라우저에서 바로 시험지 PDF를 미리보기/다운로드한다.
- API 키가 없으면 '데모' 모드로 내장 지문(DNA·star manager)을 사용해 미리볼 수 있다.
- API 키가 있으면 입력한 지문으로 Claude가 7종 문항을 생성한다.

실행: python webapp.py  (기본 http://127.0.0.1:5000)
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from exam import renderer, validator
from exam.demo_data import demo_passages
from exam.demo2 import demo_passages_2
from exam.set2 import TYPE_LABELS2, TYPE_ORDER2, TYPE_PROMPTS2
from src.config import load_config

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "web"
OUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)


def _api_available(cfg) -> bool:
    """API 키가 있고, '미리보기 전용 모드'가 아니면 True.

    PREVIEW_ONLY(웹앱 --preview 또는 EXAM_PREVIEW_ONLY=1)면 키가 있어도 안 쓴다.
    """
    if app.config.get("PREVIEW_ONLY") or os.environ.get("EXAM_PREVIEW_ONLY"):
        return False
    return cfg.has_api_key

_FID_RE = re.compile(r"^[0-9a-f]{6,32}$")
_SEP_RE = re.compile(r"(?m)^\s*-{3,}\s*$")   # 지문 구분: --- 한 줄
_ILLEGAL_NAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')   # 파일명 금지문자


def safe_name(raw: str) -> str:
    """사용자가 입력한 지문명을 안전한 파일명 조각으로 정리."""
    s = _ILLEGAL_NAME.sub("", raw or "").strip().strip(".")
    s = re.sub(r"\s+", " ", s)
    return s[:80]


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
    return render_template("index.html", has_api_key=_api_available(cfg), error=None)


@app.post("/generate")
def generate():
    cfg = load_config()
    # 'demo' 버튼을 눌렀을 때만 데모. '시험지 생성'은 항상 입력 지문을 사용한다.
    demo = request.form.get("action") == "demo"
    header = (request.form.get("header") or "").strip()
    vocab_method = request.form.get("vocab_method", "synonym")
    from exam import difficulty as _diff
    level = _diff.normalize(request.form.get("level"))   # 상/중/하 (기본 중)
    content_difficulty = _diff.content_difficulty(level)

    # 출력할 세트: 1회/2회 체크박스(없으면 1회 기본)
    sets = [s for s in request.form.getlist("sets") if s in ("1", "2")] or ["1"]
    uploads = [f for f in request.files.getlist("files") if f and f.filename]
    doc_name = safe_name(request.form.get("doc_name", ""))

    def fail(msg: str, code: int = 400):
        return render_template("index.html", has_api_key=_api_available(cfg), error=msg), code

    # 실제 모드: 지문을 한 번만 확보(두 세트가 같은 지문 공유)
    bodies = None
    client = None
    if not demo:
        pasted = split_passages(request.form.get("passages", ""))
        if not uploads and not pasted:
            return fail("지문을 붙여넣거나 파일(PDF·사진)을 올리거나 '무료 미리보기'를 선택하세요.")
        if not _api_available(cfg):
            return fail("실제 생성에는 API 키가 필요합니다. (미리보기 전용 모드이거나 키가 "
                        "없습니다.) 비용 없이 보려면 '무료 미리보기' 버튼을 누르세요.")
        from exam import ingest
        from exam.llm import ClaudeClient
        client = ClaudeClient(cfg.api_key, cfg.model)
        try:
            if uploads:
                updir = OUT / "uploads" / uuid.uuid4().hex[:12]
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
        except Exception as e:  # noqa: BLE001
            return fail(f"지문 처리 실패: {e}", 500)
        if not bodies:
            return fail("지문을 추출하지 못했습니다. 파일 내용을 확인해 주세요.")

    # 기본 파일명
    if not doc_name:
        if demo:
            doc_name = "데모지문"
        elif uploads:
            doc_name = safe_name(Path(uploads[0].filename).stem)
        else:
            doc_name = "영어지문"
    doc_name = doc_name or "영어지문"

    outputs = []
    try:
        # 실제 모드에서 두 세트가 같은 지문을 쓰면 분석을 '한 번만' 돌려 공유한다(속도·비용).
        analyses = None
        if not demo:
            from exam.pipeline import analyze_bodies
            analyses = analyze_bodies(client, bodies,
                                      max_retries=cfg.processing.max_retries)
        for sid in sets:
            f2 = uuid.uuid4().hex[:12]
            out = _pdf_path(f2)
            if sid == "1":
                if demo:
                    ps = demo_passages()
                    validator.validate_passages(ps)
                    validator.validate_numbering(ps, start=1)
                    renderer.render_pdf(ps, out, header_note=header)
                    n = len(ps)
                else:
                    from exam.pipeline import build_exam
                    build_exam(client, bodies, out, header_note=header,
                               max_retries=cfg.processing.max_retries,
                               vocab_method=vocab_method,
                               content_difficulty=content_difficulty,
                               analyses=analyses, level=level)
                    n = len(bodies)
                outputs.append({"fid": f2, "label": "변형문제 1회", "count": n,
                                "name": f"{doc_name}_변형문제_1회"})
            else:
                if demo:
                    ps = demo_passages_2()
                    validator.validate_passages(ps, TYPE_ORDER2)
                    validator.validate_numbering(ps, 1, TYPE_ORDER2)
                    renderer.render_pdf(ps, out, header_note=header,
                                        type_order=TYPE_ORDER2, prompts=TYPE_PROMPTS2,
                                        labels=TYPE_LABELS2)
                    n = len(ps)
                else:
                    from exam.gen2 import build_exam2
                    build_exam2(client, bodies, out, header_note=header,
                                max_retries=cfg.processing.max_retries,
                                analyses=analyses, level=level)
                    n = len(bodies)
                outputs.append({"fid": f2, "label": "변형문제 2회", "count": n,
                                "name": f"{doc_name}_변형문제_2회"})
    except Exception as e:  # noqa: BLE001 — 사용자에게 원인 표시
        return fail(f"생성 실패: {e}", 500)

    return render_template("result.html", outputs=outputs, demo=demo, header=header)


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
    base = safe_name(request.args.get("name", "")) or "영어지문_변형문제"
    return send_file(p, mimetype="application/pdf", as_attachment=True,
                     download_name=f"{base}.pdf")

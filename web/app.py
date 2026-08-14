"""영어 시험지 자동 생성 — 웹앱 (Flask).

지문을 붙여넣고 옵션을 고르면 브라우저에서 바로 시험지 PDF를 미리보기/다운로드한다.
- API 키가 없으면 '데모' 모드로 내장 지문(DNA·star manager)을 사용해 미리볼 수 있다.
- API 키가 있으면 입력한 지문으로 Claude가 7종 문항을 생성한다.

실행: python webapp.py  (기본 http://127.0.0.1:5000)
"""
from __future__ import annotations

import json
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


def _json_path(fid: str) -> Path:
    if not _FID_RE.match(fid):
        abort(404)
    return OUT / f"exam_{fid}.json"


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

    # 난이도: 체크박스(상/중/하 다중). 없으면 중 하나. 표시 순서는 하<중<상.
    LEVEL_ORDER = ["하", "중", "상"]
    chosen = set(l for l in request.form.getlist("levels") if l in ("상", "중", "하"))
    levels = [l for l in LEVEL_ORDER if l in chosen] or ["중"]

    # 출력할 세트: 1회/2회 체크박스(없으면 1회 기본)
    sets = [s for s in request.form.getlist("sets") if s in ("1", "2")] or ["1"]
    # 출력할 섹션(없으면 4개 모두)
    valid_sec = ("student", "teacher", "quick", "answers")
    sections = [s for s in request.form.getlist("sections") if s in valid_sec] or list(valid_sec)
    uploads = [f for f in request.files.getlist("files") if f and f.filename]
    doc_name = safe_name(request.form.get("doc_name", ""))

    def fail(msg: str, code: int = 400):
        return render_template("index.html", has_api_key=_api_available(cfg), error=msg), code

    # 실제 모드: 지문을 한 번만 확보(두 세트가 같은 지문 공유)
    bodies = None
    src_labels: list[str] | None = None   # 원본 PDF의 영어지문 문항번호(있으면)
    client = None
    if not demo:
        pasted = split_passages(request.form.get("passages", ""))
        if not uploads and not pasted:
            return fail("지문을 붙여넣거나 파일(PDF·사진)을 올리거나 '무료 미리보기'를 선택하세요.")
        # API 키: 브라우저에서 붙여넣은 키(우선) → 없으면 .env 키. (미리보기 전용 모드는 키 무시)
        preview_only = bool(app.config.get("PREVIEW_ONLY")
                            or os.environ.get("EXAM_PREVIEW_ONLY"))
        form_key = (request.form.get("api_key") or "").strip()
        eff_key = None if preview_only else (form_key or cfg.api_key)
        if not eff_key:
            if preview_only:
                return fail("미리보기 전용 모드입니다. '무료 미리보기'를 사용하세요.")
            return fail("실제 생성에는 API 키가 필요합니다. 위 '🔑 API 키' 칸에 키를 붙여넣거나 "
                        "(.env 에 설정해도 됩니다). 비용 없이 보려면 '무료 미리보기' 버튼을 누르세요.")
        from exam import ingest
        from exam.llm import ClaudeClient
        client = ClaudeClient(eff_key, cfg.model,
                              thinking=cfg.processing.thinking,
                              effort=cfg.processing.effort)
        try:
            if uploads:
                updir = OUT / "uploads" / uuid.uuid4().hex[:12]
                updir.mkdir(parents=True, exist_ok=True)
                paths = []
                for i, f in enumerate(uploads, 1):
                    ext = Path(f.filename).suffix.lower()
                    if not ingest.is_supported(f"x{ext}"):
                        return fail(f"지원하지 않는 형식입니다: {f.filename} "
                                    "(.txt/.pdf/.hwp/.hwpx/.jpg/.png/.webp)")
                    dest = updir / f"upload_{i}{ext}"
                    f.save(dest)
                    paths.append(dest)
                pairs = ingest.load_bodies(
                    paths, client=client,
                    vision_fallback=cfg.processing.pdf_vision_fallback)
                bodies = [b for _, b in pairs]
                # 원본 PDF의 '영어지문 문항번호'(예: 31번)가 있으면 지문 라벨로 쓴다.
                src_labels = [lbl for lbl, _ in pairs]
            else:
                bodies = pasted
        except Exception as e:  # noqa: BLE001
            return fail(f"지문 처리 실패: {e}", 500)
        if not bodies:
            return fail("지문을 추출하지 못했습니다. 파일 내용을 확인해 주세요.")

        # 시작 문항번호(수동): 입력하면 지문 라벨을 이 번호부터 지문마다 1씩 증가시킨다
        # (원본 PDF 문항번호/자동 표기를 덮어씀). 비우면 기존 방식 유지.
        start_raw = (request.form.get("start_no") or "").strip()
        if start_raw:
            try:
                start_n = int(start_raw)
            except ValueError:
                return fail("시작 문항번호는 숫자로 입력하세요.")
            if start_n < 1:
                return fail("시작 문항번호는 1 이상이어야 합니다.")
            src_labels = [f"{start_n + i}번" for i in range(len(bodies))]

    # 기본 파일명
    if not doc_name:
        if demo:
            doc_name = "데모지문"
        elif uploads:
            doc_name = safe_name(Path(uploads[0].filename).stem)
        else:
            doc_name = "영어지문"
    doc_name = doc_name or "영어지문"

    def part_tag(sid: str, lv: str | None) -> str:
        """머리글(header)을 뺀 파트 제목 — JSON 저장·복원 시 새 머리글과 다시 합쳐진다."""
        tag = f"변형문제 {sid}회"
        if lv:
            tag += f" · 난이도 {lv}"
        if demo:
            tag += " (데모)"
        return tag

    def part_header(sid: str, lv: str | None) -> str:
        tag = part_tag(sid, lv)
        return f"{tag} — {header}" if header else tag

    try:
        # 실제 모드: 분석을 '한 번만' 돌려 모든 세트·난이도 조합이 공유한다(속도·비용).
        analyses = None
        if not demo:
            from exam.pipeline import analyze_bodies
            analyses = analyze_bodies(client, bodies,
                                      max_retries=cfg.processing.max_retries)

        # 선택한 (세트 × 난이도) 조합을 모두 만들어 한 PDF로 합본한다.
        # 데모는 난이도 변형이 없으므로 세트당 1개만.
        combo_levels = [None] if demo else levels
        parts = []
        part_meta = []      # JSON 저장용(재분석·재생성 없이 제목만 바꿔 재출력)
        labels = []
        for sid in sets:
            for lv in combo_levels:
                if sid == "1":
                    if demo:
                        ps = demo_passages()
                        validator.validate_passages(ps)
                        validator.validate_numbering(ps, start=1)
                    else:
                        from exam.pipeline import build_passages
                        ps = build_passages(client, bodies,
                                            max_retries=cfg.processing.max_retries,
                                            analyses=analyses, level=lv,
                                            labels=src_labels)
                    parts.append({"passages": ps, "header_note": part_header(sid, lv),
                                  "sections": sections})
                else:
                    if demo:
                        ps = demo_passages_2()
                        validator.validate_passages(ps, TYPE_ORDER2)
                        validator.validate_numbering(ps, 1, TYPE_ORDER2)
                    else:
                        from exam.gen2 import build_passages2
                        ps = build_passages2(client, bodies,
                                             max_retries=cfg.processing.max_retries,
                                             analyses=analyses, level=lv,
                                             labels=src_labels)
                    parts.append({"passages": ps, "header_note": part_header(sid, lv),
                                  "sections": sections, "type_order": TYPE_ORDER2,
                                  "prompts": TYPE_PROMPTS2, "labels": TYPE_LABELS2})
                part_meta.append({"set": sid, "tag": part_tag(sid, lv),
                                  "sections": sections, "passages": ps})
                labels.append(part_header(sid, lv))

        fid = uuid.uuid4().hex[:12]
        out = _pdf_path(fid)
        renderer.render_pdf_multi(parts, out)
        # 실제 생성 결과는 JSON 으로도 저장 → 다음에 제목만 바꿔 재출력(무료).
        has_json = False
        if not demo:
            from exam import serialize
            payload = serialize.dump_parts(part_meta, header=header, doc_name=doc_name)
            _json_path(fid).write_text(
                json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            has_json = True
        outputs = [{"fid": fid, "label": "합본 (" + " · ".join(labels) + ")",
                    "count": len(parts), "name": f"{doc_name}_변형문제_합본",
                    "has_json": has_json}]
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


@app.get("/json/<fid>")
def result_json(fid: str):
    """분석·문항 결과(JSON) 다운로드 — 나중에 제목만 바꿔 재출력할 때 다시 넣는다."""
    p = _json_path(fid)
    if not p.exists():
        abort(404)
    base = safe_name(request.args.get("name", "")) or "영어지문_변형문제"
    return send_file(p, mimetype="application/json", as_attachment=True,
                     download_name=f"{base}.json")


@app.post("/rerender")
def rerender():
    """분석 결과 JSON 을 다시 받아, 제목(머리글)만 바꿔 재출력한다(API 미사용·무료)."""
    cfg = load_config()

    def fail(msg: str, code: int = 400):
        return render_template("index.html", has_api_key=_api_available(cfg), error=msg), code

    up = request.files.get("analysis_json")
    if not up or not up.filename:
        return fail("분석 결과 JSON 파일(.json)을 올려 주세요.")
    if Path(up.filename).suffix.lower() != ".json":
        return fail("확장자가 .json 인 분석 결과 파일을 올려 주세요.")
    try:
        data = json.loads(up.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return fail(f"JSON 을 읽지 못했습니다: {e}")

    # 새 머리글: 입력하면 교체, 비우면 JSON 에 저장된 머리글 유지.
    new_header_raw = request.form.get("header", "")
    header_override = new_header_raw.strip() if new_header_raw.strip() else None
    new_doc = safe_name(request.form.get("doc_name", ""))

    from exam import serialize
    try:
        parts, meta = serialize.load_parts(data, header_override=header_override)
    except Exception as e:  # noqa: BLE001
        return fail(f"분석 결과를 재구성하지 못했습니다: {e}")

    doc_name = new_doc or meta.get("doc_name") or "영어지문"
    header = header_override if header_override is not None else meta.get("header", "")
    try:
        fid = uuid.uuid4().hex[:12]
        renderer.render_pdf_multi(parts, _pdf_path(fid))
        # 재출력분도 (바뀐 제목 반영해) JSON 다시 저장 → 계속 재활용 가능.
        _json_path(fid).write_text(
            json.dumps({**data, "header": header, "doc_name": doc_name},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        outputs = [{"fid": fid, "label": f"재출력 · {meta['n_parts']}개 파트",
                    "count": meta["n_parts"], "name": f"{doc_name}_변형문제_합본",
                    "has_json": True}]
    except Exception as e:  # noqa: BLE001
        return fail(f"재출력 실패: {e}", 500)

    return render_template("result.html", outputs=outputs, demo=False, header=header)

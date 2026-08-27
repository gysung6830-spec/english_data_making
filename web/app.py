"""영어 시험지 자동 생성 — 웹앱 (Flask).

지문을 붙여넣고 옵션을 고르면 브라우저에서 바로 시험지 PDF를 미리보기/다운로드한다.
- API 키가 없으면 '데모' 모드로 내장 지문(DNA·star manager)을 사용해 미리볼 수 있다.
- API 키가 있으면 입력한 지문으로 Claude가 통합 17문항을 생성한다.

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
from exam.merged import (
    MERGED_LABELS,
    MERGED_ORDER,
    MERGED_PROMPTS,
    build_passages_merged,
    demo_passages_merged,
)
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


def parse_labels(raw: str) -> list[str]:
    """사용자가 입력한 지문 번호 목록을 파싱한다.

    '10-A, 10-1, … 논술형' 또는 '[10-A, 10-1, …]', 줄바꿈 구분 모두 허용.
    바깥 대괄호를 벗기고 쉼표/줄바꿈으로 나눈 뒤, 각 항목의 공백·대괄호를 정리해
    빈 항목은 버린다.
    """
    s = (raw or "").strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    toks = re.split(r"[,\n]", s)
    return [t.strip().strip("[]").strip() for t in toks if t.strip().strip("[]").strip()]


def _apply_passage_field(data: dict, values: list[str], field: str, kr: str) -> str | None:
    """지문별 필드(source_label·title 등)를 입력값으로 '지문 순서대로' 덮어쓴다
    (JSON dict 직접 수정). 모든 파트는 같은 지문 집합을 공유하므로, 각 파트의 i번째
    지문에 values[i]를 넣는다. 입력 개수와 지문 수가 다르면 친절한 오류를 돌려준다(수정 안 함)."""
    parts = data.get("parts") or []
    for pm in parts:
        n = len(pm.get("passages") or [])
        if n != len(values):
            return (f"{kr} {len(values)}개를 입력했는데, 이 자료의 지문은 {n}개입니다. "
                    f"지문 수({n}개)에 맞춰 순서대로 구분해 입력해 주세요.")
    for pm in parts:
        for i, pd in enumerate(pm.get("passages") or []):
            pd[field] = values[i]
    return None


def apply_labels(data: dict, labels: list[str]) -> str | None:
    """지문 번호(source_label)를 지문 순서대로 덮어쓴다."""
    return _apply_passage_field(data, labels, "source_label", "지문 번호")


# 결과물 종류 → 파일명 접미사 (""=합본). 개별 산출물은 섹션 이름을 그대로 쓴다.
_KIND_SUFFIX = {
    "": "", "review": "_검토메모",
    "student": "_학생용", "teacher": "_교사용",
    "quick": "_빠른정답", "answers": "_해설지",
}
# 개별 파일 표시용: 섹션 → (파일명 조각, 화면 라벨)
SECTION_NAMES = {
    "student": ("학생용", "학생용 (문제)"),
    "teacher": ("교사용", "교사용 (문제+해설)"),
    "quick": ("빠른정답", "빠른 정답"),
    "answers": ("해설지", "해설지 (정답 및 해설)"),
}


# 문항별 한 줄 설명 — 화면에 '몇 번이 무엇인지'를 번호 순으로 보여 준다.
# MERGED_ORDER 가 바뀌면 번호도 자동으로 따라가므로 설명이 어긋날 일이 없다.
TYPE_NOTES = {
    "topic": "글 전체가 무엇을 다루는가 (영어 선지)",
    "title": "비유·대구 또는 의문형으로 압축 — 다섯 선지를 한 갈래로 통일",
    "B": "밑줄 어구의 문맥적 의미 (축자 해석이 함정)",
    "content": "한글 진술 10개를 각각 O/X — O 는 늘 2개, 나머지는 모두 X",
    "content_2": "영어 진술 10개를 각각 O/X — 한글판과 '다른 사실'을 묻는다 "
                 "(문장 5개 이하 지문은 8개)",
    "grammar": "틀린 것을 모두 고르기 — 원문 지문 그대로, 몇 개인지 알려주지 않음",
    "grammar_fix": "밑줄 ①~⑥ 중 틀린 4개를 찾아 번호와 고친 형태를 쓰는 서술형 "
                   "— ⚠ 지문을 다시 써서 출제",
    "pair_odd": "밑줄 ⓐ~ⓔ 중 어법 오류 1개 + 어휘 오류 1개를 짝으로",
    "vocab_2": "원문단어형 — 4개는 원문 그대로, 어색한 하나 찾기",
    "vocab": "유의어형 — 5개가 다 바뀌어 하나하나 대조",
    "vocab_3": "부정어형 — 낱말은 멀쩡하고 문장이 글 흐름과 모순",
    "F": "정답은 지문에 없던 표현(패러프레이즈)이어야 한다",
    "linker": "(A)(B) 두 자리의 연결어를 짝으로 — 글의 뼈대(대조·예시·인과)를 읽는다",
    "order": "(A)(B)(C)(D) 네 덩어리를 제 순서로",
    "insert": "지시어·연결사로 들어갈 자리가 한 곳으로 굳는다",
    "E": "한 문장 요약문의 (A)(B)에 들어갈 낱말쌍",
    "D": "낱개 단어를 배열해 문장 완성 (동사는 원형 제시)",
}


def type_rows() -> list[tuple[int, str, str]]:
    """출제 유형을 (문항 번호, 유형 이름, 한 줄 설명)으로. MERGED_ORDER 와 늘 일치한다."""
    return [(i, MERGED_LABELS[t], TYPE_NOTES.get(t, ""))
            for i, t in enumerate(MERGED_ORDER, 1)]


@app.context_processor
def _inject_types():
    """모든 화면에서 문항별 목록을 쓸 수 있게 한다(따로 넘기지 않아도 됨)."""
    return {"type_rows": type_rows(), "n_types": len(MERGED_ORDER)}


def _pdf_path(fid: str, kind: str = "") -> Path:
    if not _FID_RE.match(fid) or kind not in _KIND_SUFFIX:
        abort(404)
    return OUT / f"exam_{fid}{_KIND_SUFFIX[kind]}.pdf"


def _stash_path(token: str) -> Path:
    """사전 점검 경고 후 '그래도 생성'할 때 쓸, 추출해 둔 지문 임시 저장 경로."""
    if not _FID_RE.match(token):
        abort(404)
    p = OUT / "precheck"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{token}.json"


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

    # 출력할 섹션(없으면 4개 모두)
    valid_sec = ("student", "teacher", "quick", "answers")
    sections = [s for s in request.form.getlist("sections") if s in valid_sec] or list(valid_sec)
    # 문항 배치: 지문별(기본) 또는 문제유형별
    group_by = request.form.get("group_by")
    group_by = group_by if group_by in ("passage", "type") else renderer.DEFAULT_GROUP_BY
    # 출력 방식: 합본(기본) / 개별(구성별 파일) / 합본 및 개별
    out_mode = request.form.get("out_mode")
    out_mode = out_mode if out_mode in ("merged", "each", "both") else "merged"
    uploads = [f for f in request.files.getlist("files") if f and f.filename]
    doc_name = safe_name(request.form.get("doc_name", ""))

    def fail(msg: str, code: int = 400):
        return render_template("index.html", has_api_key=_api_available(cfg), error=msg), code

    # 실제 모드: 지문을 한 번만 확보한다
    bodies = None
    src_labels: list[str] | None = None   # 원본 PDF의 영어지문 문항번호(있으면)
    client = None
    if not demo:
        pasted = split_passages(request.form.get("passages", ""))
        # 사전 점검 경고 후 '그래도 생성': 앞서 추출해 둔 지문을 재사용(재업로드 불필요)
        ack_token = request.form.get("precheck_ack", "")
        ack_stash = _stash_path(ack_token) if ack_token else None
        if not uploads and not pasted and not (ack_stash and ack_stash.exists()):
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
        from exam import _concurrent, ingest
        from exam.llm import ClaudeClient
        # 처리 방식: 폼 선택 > 설정파일. batch 면 요청을 모아 보내 비용이 절반이 된다.
        run_mode = request.form.get("run_mode")
        if run_mode not in ("fast", "batch"):
            run_mode = cfg.processing.mode if cfg.processing.mode in ("fast", "batch") else "fast"

        def _make_client(model_id: str):
            kw = dict(thinking=cfg.processing.thinking, effort=cfg.processing.effort)
            if run_mode == "batch":
                from exam.batch_client import BatchingClaudeClient
                return BatchingClaudeClient(eff_key, model_id, **kw)
            return ClaudeClient(eff_key, model_id, **kw)

        if run_mode == "batch":
            # 배치는 '많이 모을수록' 이득이라 동시 대기 수를 넉넉히 둔다(실제 호출은 배치 1건).
            _concurrent.set_concurrency(max(cfg.processing.concurrency, 64))
        else:
            # 동시 호출 상한을 설정값으로 맞춘다(환경변수가 있으면 그쪽이 우선).
            _concurrent.set_concurrency(cfg.processing.concurrency)
        client = _make_client(cfg.model)
        # 검수에 걸린 문항만 다시 만들 상위 모델(설정에서 비우면 승격하지 않음).
        strong = (_make_client(cfg.model_review)
                  if cfg.model_review and cfg.model_review != cfg.model else None)
        try:
            if ack_stash is not None and ack_stash.exists():
                data = json.loads(ack_stash.read_text(encoding="utf-8"))
                bodies = data["bodies"]
                src_labels = data.get("labels") or None
            elif uploads:
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

        # 사전 점검(API 미사용): 추출·정제가 깨끗한지 먼저 보고, 문제가 있으면 생성 전에
        # 알려 준다. '그래도 생성'을 누르면(precheck_ack) 저장해 둔 지문으로 그대로 진행한다.
        if not ack_token:
            from exam import precheck as _pc
            rep = _pc.precheck(bodies, src_labels)
            if not rep.ok:      # 생성(=API 비용) 전에 알리고, 진행 여부는 사용자가 고른다
                token = uuid.uuid4().hex[:12]
                _stash_path(token).write_text(
                    json.dumps({"bodies": bodies, "labels": src_labels}, ensure_ascii=False),
                    encoding="utf-8")
                keep = [(k, v) for k, v in request.form.items(multi=True)
                        if k != "precheck_ack"]
                return render_template(
                    "index.html", has_api_key=_api_available(cfg),
                    precheck_issues=[str(i) for i in rep.issues],
                    precheck_summary=rep.summary(),
                    precheck_token=token, precheck_form=keep), 200

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

    # 머리글(header)을 뺀 파트 제목 — JSON 저장·복원 시 새 머리글과 다시 합쳐진다.
    part_tag = "변형문제 (데모)" if demo else "변형문제"
    part_header = f"{part_tag} — {header}" if header else part_tag

    try:
        # 진행 상황을 웹앱을 띄운 터미널에 한 줄씩 표시(브라우저는 기다리기만 하므로).
        from exam.progress import NullProgress, Progress
        prog = NullProgress() if demo else Progress(len(bodies))
        if client is not None and hasattr(client, "_progress"):
            client._progress = prog          # 배치 제출·완료도 터미널에 표시
        # 지문 분석은 한 번만 돌린다(모든 유형이 같은 분석을 공유한다).
        analyses = None
        if not demo:
            prog.note(f"지문 {len(bodies)}개 분석 중 …")
            from exam.pipeline import analyze_bodies
            analyses = analyze_bodies(client, bodies,
                                      max_retries=cfg.processing.max_retries)
            prog.note(f"분석 완료 · 이제 지문 {len(bodies)}개의 문항 생성을 시작합니다")

        if demo:
            ps = demo_passages_merged()
            validator.validate_passages(ps, MERGED_ORDER)
            validator.validate_numbering(ps, 1, MERGED_ORDER)
        else:
            ps = build_passages_merged(client, bodies,
                                       max_retries=cfg.processing.max_retries,
                                       analyses=analyses,
                                       labels=src_labels, progress=prog,
                                       part_label=part_tag, strong_client=strong)
        parts = [{"passages": ps, "header_note": part_header,
                  "sections": sections, "type_order": MERGED_ORDER,
                  "prompts": MERGED_PROMPTS, "labels": MERGED_LABELS,
                  "group_by": group_by}]
        # JSON 저장용(재분석·재생성 없이 제목만 바꿔 재출력)
        part_meta = [{"set": "M", "tag": part_tag, "sections": sections,
                      "passages": ps, "group_by": group_by}]
        labels = [part_header]

        prog.note("문항 생성 완료 · PDF 조판 중 …")
        fid = uuid.uuid4().hex[:12]
        out = _pdf_path(fid)
        # 출력 방식: 합본(기본) / 개별 / 합본 및 개별.
        # ※ 어느 쪽이든 '이미 생성된 문항'을 다시 조판할 뿐이라 API 비용은 같다(추가 호출 없음).
        want_merged = out_mode in ("merged", "both")
        want_each = out_mode in ("each", "both")
        review_path = None
        if want_merged:
            # 검토 메모(확인 권장 문항)는 '별도 파일'로 저장한다.
            review_path = renderer.render_pdf_multi(parts, out, review_out=_pdf_path(fid, "review"))
        each_made: list[str] = []
        if want_each:
            for sec in sections:                    # 선택한 구성만, 각각 한 파일로
                one = [{**p, "sections": [sec]} for p in parts]
                renderer.render_pdf_multi(one, _pdf_path(fid, sec),
                                          review_out=_pdf_path(fid, "review"))
                each_made.append(sec)
        if review_path is None:                     # 개별만 뽑은 경우에도 검토 메모는 남긴다
            review_path = renderer.render_review_pdf(parts, _pdf_path(fid, "review"))
        # 실제 생성 결과는 JSON 으로도 저장 → 다음에 제목만 바꿔 재출력(무료).
        has_json = False
        if not demo:
            from exam import serialize
            payload = serialize.dump_parts(part_meta, header=header, doc_name=doc_name)
            _json_path(fid).write_text(
                json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            has_json = True
        outputs = []
        if want_merged:
            outputs.append({"fid": fid, "kind": "",
                            "label": "📚 합본 — " + " · ".join(labels),
                            "count": len(parts), "name": f"{doc_name}_변형문제",
                            "has_json": has_json})
        for sec in each_made:                # 개별 파일(선택한 구성 순서대로)
            fname, disp = SECTION_NAMES[sec]
            outputs.append({"fid": fid, "kind": sec, "label": f"📄 {disp}",
                            "count": len(parts), "name": f"{doc_name}_{fname}",
                            "has_json": has_json and not want_merged and sec == each_made[0]})
        if review_path:      # 검토 메모가 있으면 별도 결과물로 추가
            outputs.append({"fid": fid, "kind": "review",
                            "label": "📋 검토 메모 (확인 권장 문항)",
                            "count": len(parts), "name": f"{doc_name}_검토메모",
                            "has_json": False})
    except Exception as e:  # noqa: BLE001 — 사용자에게 원인 표시
        return fail(_readable_error(e), 500)

    return render_template("result.html", outputs=outputs, demo=demo, header=header)


# 내부 라이브러리가 던지는 원문(pydantic 검증문·스택 용어)은 사용자가 읽을 말이 아니다.
# 지금까지 화면에 이런 것이 그대로 찍혔다:
#   "1 validation error for Analysis sentences Value error, 문장이 4개 미만입니다
#    [type=value_error, input_value=[], ...] https://errors.pydantic.dev/..."
_ERROR_HINTS = (
    (("지문이 너무 짧", "문장이 4개 미만", "문장이 0개", "지문이 비어"),
     "지문이 너무 짧거나 제대로 읽히지 않았습니다. 원문 파일에서 영어 지문이 온전히 "
     "뽑혔는지, 한 지문이 여러 개로 쪼개지지 않았는지 확인해 주세요."),
    (("rate_limit", "rate limit", "429"),
     "요청이 잠시 몰렸습니다. 1~2분 뒤에 다시 시도해 주세요."),
    (("overloaded", "529"),
     "AI 서버가 혼잡합니다. 잠시 뒤에 다시 시도해 주세요."),
    (("timeout", "timed out"),
     "응답이 너무 오래 걸렸습니다. 지문 수를 줄여 다시 시도해 주세요."),
    (("credit", "quota", "billing", "insufficient"),
     "API 사용 한도에 걸렸습니다. 결제·한도 설정을 확인해 주세요."),
    (("authentication", "api_key", "api key", "unauthorized", "401"),
     "API 키가 올바르지 않습니다. 키를 다시 확인해 주세요."),
    (("connection", "network", "unreachable", "dns"),
     "AI 서버에 연결하지 못했습니다. 인터넷 연결을 확인한 뒤 다시 시도해 주세요."),
)


def _readable_error(e: Exception) -> str:
    """생성 실패를 사람이 읽을 수 있는 한 문장으로 바꾼다(원인 실마리는 남긴다)."""
    raw = str(e)
    low = raw.lower()
    for keys, msg in _ERROR_HINTS:
        if any(k in low for k in keys):
            return f"생성 실패 — {msg}"
    # 짚이는 데가 없으면 원문을 보여 주되, 스택·URL 같은 군더더기는 잘라 낸다.
    first = raw.split("\n")[0].split("For further information")[0].strip()
    return f"생성 실패: {first[:300]}"


@app.get("/pdf/<fid>")
def pdf(fid: str):
    p = _pdf_path(fid, request.args.get("kind", ""))
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="application/pdf")   # 브라우저 인라인 미리보기


@app.get("/download/<fid>")
def download(fid: str):
    p = _pdf_path(fid, request.args.get("kind", ""))
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

    # 지문 번호 다시 넣기: 입력하면 '지문 순서대로' 라벨을 덮어쓴다(비우면 기존 유지).
    labels = parse_labels(request.form.get("labels", ""))
    if labels:
        err = apply_labels(data, labels)   # data(JSON) 직접 수정 → PDF·재저장 JSON 모두 반영
        if err:
            return fail(err)

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

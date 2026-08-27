#!/usr/bin/env python3
"""구문 분석 학습지(본 코딩) - 웹앱(브라우저) 버전.

지문을 문장 단위로 쪼개 '구문 태깅 + 해석 + 포인트 박스(포인트박스형)' 학습지를
만드는 전용 앱입니다. 6섹션 분석 도구(webapp.py)와 화면이 분리돼 있습니다.

실행:
    python worksheet_app.py     →  http://localhost:5001
"""
from __future__ import annotations

import os
import traceback
import uuid
from pathlib import Path

from flask import render_template_string, request

from src import extract
from src.client import ClaudeClient
from src.worksheet import pipeline as ws_pipeline
from src.worksheet import quality as ws_quality
from src.worksheet import serialize as ws_serialize
from src.worksheet.pipeline import Header as WsHeader
from web_common import (ALLOWED, BASE_CSS, UPLOAD_DIR, OUTPUT_DIR, _safe_name,
                        cfg, make_app, render_result)

app = make_app(__name__)

# 학습지 앱은 한글(HWP/HWPX) 문서도 지원(6섹션 앱과 달리 텍스트 추출 경로 있음).
ALLOWED_WS = ALLOWED | extract.HWP_EXTS


WORKSHEET_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>구문 분석 학습지 만들기</title><style>""" + BASE_CSS + """
  fieldset{border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:14px;}
  legend{font-weight:800;font-size:13px;padding:0 6px;}
</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✏️ 구문 분석 학습지</h1>
    <div class=sub>지문을 문장 단위로 쪼개 <b>구문 태깅 + 해석 + 포인트 박스</b> 학습지를 만듭니다.</div>
    <div class=hint style="margin:-8px 0 8px">이미 분석한 결과의 <b>제목만</b> 바꾸려면 →
      <a class=dl href="{{ url_for('retitle') }}">🧩 분석 데이터(JSON)로 제목 수정 (API 재분석 없음)</a></div>
    <form id=f method=post action="{{ url_for('build') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF·HWP, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF · HWP</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png,.hwp,.hwpx" hidden>
      </div>
      <div class=files id=filelist></div>

      <fieldset><legend>② 미리보기 <span class=hint>(만들어질 학습지 모양)</span></legend>
        <img src="{{ url_for('static', filename='layout_a.png') }}" alt="학습지 예시"
             style="width:100%;border:1px solid var(--line);border-radius:8px;display:block;">
        <div class=hint style="margin-top:6px">리본 + 구문 분석 + 포인트 박스 · 한 지문을 최대한 1페이지로 자동 압축</div>
      </fieldset>

      <fieldset><legend>③ 문항 번호 · 저장 파일명</legend>
        <label>시작 문항 번호 <span class=hint>(리본에 표시 · 지문마다 +1 자동 증가)</span></label>
        <input type=text name=start_no inputmode=numeric pattern="[0-9]*" placeholder="예: 30  →  30, 31, 32 …">
        <div class=hint>비우면 PDF 머리글의 ‘N번’을 <b>자동 인식</b>하고, 그것도 없으면 ★로 둡니다.</div>
        <label style="margin-top:10px">저장 파일명 (지문명) <span class=hint>(비우면 올린 파일 이름)</span></label>
        <input type=text name=basename placeholder="예: 2027수능특강_30번">
        <div class=hint>저장 이름: <b>(지문명)_포인트박스</b> · 영문 제목과 한글 부제는 지문 내용을 보고 <b>자동으로</b> 붙습니다.</div>
      </fieldset>

      <label>④ Anthropic API 키
        <span class=hint>(미리보기만 할 거면 비워두고 아래 '샘플 미리보기' 체크)</span></label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}" {{ 'readonly' if has_key else '' }}>

      <label class=chk style="margin-top:12px"><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>학습지 만들기</button>
        <span class=hint>여러 지문은 지문마다 새 페이지로 나옵니다.</span>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">만드는 중입니다… 잠시만요</p></div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),
       list=document.getElementById('filelist'),f=document.getElementById('f'),ov=document.getElementById('overlay');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{file.files=ev.dataTransfer.files;show();});
 file.onchange=show;
 function show(){list.innerHTML=[...file.files].map(x=>'📄 '+x.name).join('<br>')||'';}
 f.onsubmit=()=>{if(!file.files.length){alert('파일을 먼저 올려주세요.');return false;} ov.style.display='flex';};
</script>
</body></html>
"""


@app.route("/")
def index():
    return render_template_string(WORKSHEET_HTML, has_key=cfg.has_api_key)


# ---------------------------------------------------------------------------
# 제목(헤더)만 수정 — 이미 분석한 결과(JSON)를 다시 넣어 API 없이 재출력
# ---------------------------------------------------------------------------
RETITLE_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>제목 수정 (분석 데이터 불러오기)</title><style>""" + BASE_CSS + """
</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>🧩 제목만 수정하기</h1>
    <div class=sub>이미 분석한 결과(<b>분석 데이터 JSON</b>)를 올리면, <b>재분석(API 비용) 없이</b>
      제목·주제·문항번호만 고쳐 학습지를 다시 뽑습니다.</div>
    {% if err %}<div class=err>{{ err }}</div>{% endif %}
    <form id=f method=post action="{{ url_for('retitle_load') }}" enctype=multipart/form-data>
      <label>분석 데이터 파일 (…_분석데이터.json)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 JSON 파일을 끌어다 놓으세요</p>
        <p>학습지를 만들 때 함께 저장된 <b>…_분석데이터.json</b></p>
        <input id=file type=file name=jsonfile accept=".json,application/json" hidden>
      </div>
      <div class=files id=filelist></div>
      <div class=row>
        <button class=btn type=submit>불러오기</button>
        <a class="btn gray" href="{{ url_for('index') }}">← 처음으로</a>
      </div>
    </form>
  </div>
</div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),
       list=document.getElementById('filelist');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{file.files=ev.dataTransfer.files;show();});
 file.onchange=show;
 function show(){list.innerHTML=[...file.files].map(x=>'📄 '+x.name).join('<br>')||'';}
</script>
</body></html>
"""

RETITLE_EDIT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>제목 수정</title><style>""" + BASE_CSS + """
  fieldset{border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:14px;}
  legend{font-weight:800;font-size:13px;padding:0 6px;}
  .num{width:120px;}
</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>🧩 제목·헤더 수정</h1>
    <div class=sub>고칠 곳만 바꾸고 <b>‘다시 만들기’</b>를 누르세요. (분석 내용·해석·어법은 그대로 유지됩니다.)</div>
    <form id=f method=post action="{{ url_for('retitle_build') }}">
      <input type=hidden name=raw_json value="{{ raw_json_attr }}">
      {% for i, a in items %}
      <fieldset>
        <legend>지문 {{ i + 1 }}{% if a.source_name %} · {{ a.source_name }}{% endif %}</legend>
        <label>문항 번호 <span class=hint>(리본에 표시 · 비우면 ★)</span></label>
        <input class=num type=text name="lecture_{{ i }}" value="{{ a.lecture_label }}"
               inputmode=numeric placeholder="예: 30">
        <label>영문 제목</label>
        <input type=text name="title_en_{{ i }}" value="{{ a.title_en }}">
        <label>한글 제목(부제)</label>
        <input type=text name="title_ko_{{ i }}" value="{{ a.title_ko }}">
        <label>주제 <span class=hint>(상단 요약 박스 첫 줄)</span></label>
        <input type=text name="summary_{{ i }}" value="{{ a.summary }}">
        <label>쉽게 말하면 <span class=hint>(상단 요약 박스 둘째 줄)</span></label>
        <input type=text name="summary_easy_{{ i }}" value="{{ a.summary_easy }}">
      </fieldset>
      {% endfor %}
      <label style="margin-top:14px">저장 파일명 <span class=hint>(비우면 기존 이름)</span></label>
      <input type=text name=basename value="{{ basename }}" placeholder="예: 2027수능특강_30번">
      <div class=row>
        <button class=btn id=go type=submit>다시 만들기 (API 없음)</button>
        <a class="btn gray" href="{{ url_for('retitle') }}">← 다른 파일</a>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">만드는 중입니다… 잠시만요</p></div>
<script>
 const f=document.getElementById('f'),ov=document.getElementById('overlay');
 f.onsubmit=()=>{ov.style.display='flex';};
</script>
</body></html>
"""


@app.route("/retitle")
def retitle():
    return render_template_string(RETITLE_HTML, err="")


@app.route("/retitle/load", methods=["POST"], endpoint="retitle_load")
def retitle_load_route():
    f = request.files.get("jsonfile")
    if not f or not f.filename:
        return render_template_string(RETITLE_HTML, err="JSON 파일을 올려주세요.")
    try:
        text = f.read().decode("utf-8")
        analyses = ws_serialize.analyses_from_json(text)
    except Exception:
        return render_template_string(RETITLE_HTML,
            err="분석 데이터(JSON)를 읽지 못했습니다. 학습지와 함께 저장된 ‘…_분석데이터.json’ 인지 확인하세요.")
    if not analyses:
        return render_template_string(RETITLE_HTML, err="JSON 안에 지문 데이터가 없습니다.")
    base = _safe_name(Path(f.filename).stem.replace("_분석데이터", ""))
    # 히든 입력(value=) 에 담을 한 줄(compact) JSON. Jinja 자동 이스케이프가 속성 안전 처리를
    # 하므로 여기서 따로 이스케이프하지 않는다(중복 이스케이프 방지).
    compact = ws_serialize.analyses_to_json(analyses, indent=None)
    return render_template_string(RETITLE_EDIT_HTML, items=list(enumerate(analyses)),
                                  raw_json_attr=compact, basename=base)


@app.route("/retitle/build", methods=["POST"], endpoint="retitle_build")
def retitle_build_route():
    raw = request.form.get("raw_json") or ""
    try:
        analyses = ws_serialize.analyses_from_json(raw)
    except Exception:
        return render_template_string(RETITLE_HTML, err="데이터를 다시 불러와 주세요(세션 만료 가능).")
    if not analyses:
        return render_template_string(RETITLE_HTML, err="지문 데이터가 없습니다.")
    # 편집한 헤더 필드 반영(있는 값만 덮어씀)
    for i, a in enumerate(analyses):
        for field in ("title_en", "title_ko", "summary", "summary_easy"):
            v = request.form.get(f"{field}_{i}")
            if v is not None:
                setattr(a, field, v.strip())
        lec = request.form.get(f"lecture_{i}")
        if lec is not None:
            a.lecture_label = lec.strip()

    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""
    if raw_name:
        for a in analyses:
            a.source_name = raw_name
    stem = custom_base or _safe_name(analyses[0].source_name or "passage")

    footer = cfg.design.footer_note or "(C)2026.Ortica영어.All rights reserved"
    make_student = getattr(cfg.design, "make_student", True)
    out = OUTPUT_DIR / f"{stem}_포인트박스.pdf"
    try:
        ws_pipeline.render_worksheet_pair(
            analyses, out, layout="A", footer_note=footer, density="auto",
            make_student=make_student,
            slevel=getattr(cfg.design, "student_level", "blank"),
            boxmode=getattr(cfg.design, "box_align", "even"),
            bw=getattr(cfg.design, "print_mode", True))   # 웹앱 기본=인쇄용(흑백 친화)
    except Exception as e:
        traceback.print_exc()
        return render_result([{"name": stem, "ok": False, "error": str(e)}])
    # 수정본도 JSON 재저장(다음 수정에 이어서 쓸 수 있게)
    outfiles = [{"label": "✏️ 교사용+학생용(합본)" if make_student else "✏️ 교사용", "out": out.name}]
    try:
        json_name = f"{stem}_분석데이터.json"
        (OUTPUT_DIR / json_name).write_text(
            ws_serialize.analyses_to_json(analyses), encoding="utf-8")
        outfiles.append({"label": "🧩 분석 데이터(JSON · 제목 재수정용)", "out": json_name})
    except Exception:
        traceback.print_exc()
    note = f" (지문 {len(analyses)}개 · 제목 수정 · API 미사용)"
    return render_result([{"name": stem + note, "ok": True, "flag": False,
                           "reasons": [], "files": outfiles}])


@app.route("/build", methods=["POST"], endpoint="build")
def build_route():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    form_key = (request.form.get("api_key") or "").strip()
    key = (None if "설정됨" in form_key else (form_key or None)) or cfg.api_key

    layout = "A"       # 학습지는 포인트박스형 한 종류(직독직해 B형은 미노출)
    density = "auto"   # 한 지문을 최대한 1페이지로 자동 압축
    kind = "포인트박스"   # 저장 파일명: (지문명)_포인트박스.pdf
    strength = "full"    # 태깅 강도는 항상 '전체'로 고정

    # 시작 문항 번호(수동): 있으면 지문마다 start, start+1, … 로 리본 라벨을 자동 증가.
    # 비우면 base_header.lecture_label 은 빈 값 → 파이프라인이 PDF 머리글의 'N번'을 자동 인식.
    start_raw = (request.form.get("start_no") or "").strip()
    start_no = int(start_raw) if start_raw.isdigit() else None

    # 영문 제목·한글 부제는 지문 내용에서 자동 생성(사용자 입력 아님). 날짜는 사용하지 않음.
    base_header = WsHeader(lecture_label="", strength=strength)
    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    if not files:
        return render_template_string(WORKSHEET_HTML, has_key=cfg.has_api_key)
    if not mock and not key:
        html = WORKSHEET_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key)

    client = None if mock else ClaudeClient(key, cfg.model)
    footer = cfg.design.footer_note or "(C)2026.Ortica영어.All rights reserved"

    results = []
    counter = start_no          # 파일·지문을 가로질러 이어서 증가(수동 시작번호일 때만)
    for idx, f in enumerate(files, start=1):
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_WS:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(JPG·PNG·PDF·HWP만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        try:
            if mock:
                analyses = ws_pipeline.mock_analyses_for_file(tmp, base_header)
            else:
                analyses = ws_pipeline.build_analyses_for_file(
                    client, cfg, tmp, base_header,
                    max_retries=cfg.processing.max_retries, layout=layout)
            # 수동 시작 문항 번호: 지문마다 start, start+1, … 로 리본 라벨을 덮어씀(자동 증가).
            if start_no is not None:
                for a in analyses:
                    a.lecture_label = str(counter)
                    counter += 1
            # 뱃지 '파일명+지문번호'용 파일명: 지문명(basename) 있으면 그걸, 없으면 올린 파일 이름.
            src_label = raw_name or Path(f.filename).stem
            for a in analyses:
                a.source_name = src_label
            if custom_base:
                stem = custom_base if len(files) == 1 else f"{custom_base}_{idx}"
            else:
                stem = _safe_name(Path(f.filename).stem)
            out = OUTPUT_DIR / f"{stem}_{kind}.pdf"
            make_student = getattr(cfg.design, "make_student", True)
            # 합본 1개 PDF: 교사용 전체 지문 → 학생용 전체 지문(설정 make_student).
            ws_pipeline.render_worksheet_pair(
                analyses, out, layout=layout, footer_note=footer, density=density,
                make_student=make_student,
                slevel=getattr(cfg.design, "student_level", "blank"),
                boxmode=getattr(cfg.design, "box_align", "even"),
                bw=getattr(cfg.design, "print_mode", True))   # 웹앱 기본=인쇄용(흑백 친화)
            label = "✏️ 교사용+학생용(합본)" if make_student else "✏️ 교사용"
            outfiles = [{"label": label, "out": out.name}]
            # 분석 데이터(JSON) 저장 — 나중에 제목·헤더만 고쳐 재출력할 때 재분석(API) 없이 씀.
            try:
                json_name = f"{stem}_분석데이터.json"
                (OUTPUT_DIR / json_name).write_text(
                    ws_serialize.analyses_to_json(analyses), encoding="utf-8")
                outfiles.append({"label": "🧩 분석 데이터(JSON · 제목 재수정용)",
                                 "out": json_name})
            except Exception:
                traceback.print_exc()
            note = f" (지문 {len(analyses)}개)" if len(analyses) > 1 else ""
            # 무인 품질 게이트: 자동 복구까지 끝난 결과가 미심쩍으면 '검수 권장'으로 표시
            # (목 미리보기·auto_flag 꺼짐이면 생략). 사람은 flag 된 것만 확인하면 된다.
            flag, reasons = False, []
            if not mock and getattr(cfg.quality, "auto_flag", True):
                verdict = ws_quality.assess(analyses, min_sentences=cfg.quality.min_sentences)
                flag, reasons = (not verdict["ok"]), verdict["reasons"]
            results.append({"name": f.filename + note, "ok": True,
                            "flag": flag, "reasons": reasons, "files": outfiles})
        except Exception as e:  # 개별 실패가 전체를 멈추지 않음
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": str(e)})
        finally:
            tmp.unlink(missing_ok=True)

    return render_result(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print("=" * 56)
    print("  [구문 분석 학습지] 웹앱이 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (6섹션 분석 도구는 webapp.py 를 실행하세요)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

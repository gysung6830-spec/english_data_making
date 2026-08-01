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

      <fieldset><legend>③ 강 번호 · 저장 파일명</legend>
        <label>강 번호</label><input type=text name=lecture_label placeholder="예: 20 / 14강">
        <label>저장 파일명 (지문명) <span class=hint>(비우면 올린 파일 이름)</span></label>
        <input type=text name=basename placeholder="예: 2027수능특강_20강">
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

    # 영문 제목·한글 부제는 지문 내용에서 자동 생성(사용자 입력 아님). 날짜는 사용하지 않음.
    base_header = WsHeader(
        lecture_label=(request.form.get("lecture_label") or "").strip(),
        strength=strength,
    )
    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    if not files:
        return render_template_string(WORKSHEET_HTML, has_key=cfg.has_api_key)
    if not mock and not key:
        html = WORKSHEET_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key)

    client = None if mock else ClaudeClient(key, cfg.model)
    footer = cfg.design.footer_note or "(C)2026.김은아영어연구소.All rights reserved"

    results = []
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
                boxmode=getattr(cfg.design, "box_align", "even"))
            label = "✏️ 교사용+학생용(합본)" if make_student else "✏️ 교사용"
            outfiles = [{"label": label, "out": out.name}]
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

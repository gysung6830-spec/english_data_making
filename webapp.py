#!/usr/bin/env python3
"""6섹션 영어 지문 분석 도구 - 웹앱(브라우저) 버전.

※ 이 앱은 '구문 분석 학습지(본 코딩)'와 별개의 도구입니다.
   구문 분석 학습지 웹앱은 worksheet_app.py 를 실행하세요.

실행:
    python webapp.py     →  http://localhost:5000
"""
from __future__ import annotations

import os
import traceback
import uuid
from pathlib import Path

from flask import render_template_string, request

from src import pipeline
from src.client import ClaudeClient
from src.config import OutputsCfg
from web_common import (ALLOWED, BASE_CSS, UPLOAD_DIR, _safe_name, cfg,
                        make_app, render_result)

app = make_app(__name__)


INDEX_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>영어 지문 분석 도구</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>📘 영어 지문 자동 분석</h1>
    <div class=sub>지문 사진(JPG/PNG)이나 PDF를 올리면, 분석지·어휘 리스트·영단어 시험지를 만들어 드립니다.</div>
    <form id=f method=post action="{{ url_for('analyze') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png" hidden>
      </div>
      <div class=files id=filelist></div>

      <label>② Anthropic API 키
        <span class=hint>(console.anthropic.com 에서 발급 · 미리보기만 할 거면 비워도 됨)</span>
      </label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}"
             {{ 'readonly' if has_key else '' }}>
      {% if has_key %}<div class=hint>.env에 저장된 키가 있어 자동으로 사용됩니다.</div>{% endif %}

      <label>③ 저장 파일명 (지문명) <span class=hint>(비우면 올린 파일 이름 사용)</span></label>
      <input type=text name=basename placeholder="예: 2027수능특강_16강">
      <div class=hint>저장 이름: <b>(지문명)_지문분석</b> · <b>(지문명)_어휘리스트</b> · <b>(지문명)_어휘test</b></div>

      <label>④ 만들 자료 선택 <span class=hint>(직독직해 핵심 어휘로 리스트·시험지도 함께)</span></label>
      <label class=chk><input type=checkbox name=out_analysis value=1 checked> 📘 지문 분석지 (6개 섹션)</label>
      <label class=chk><input type=checkbox name=out_wordlist value=1 checked> 📝 어휘 리스트 (단어+뜻 정리)</label>
      <label class=chk><input type=checkbox name=out_quiz value=1 checked> ✏️ 영단어 시험지 (뜻 맞히기·정답 포함)</label>

      <label class=chk><input type=checkbox name=brand value=1 checked> 🖋️ 분석지에 '은아 T' 문구 넣기 <span class=hint>(직독직해 made by · 출제표 tip · 하단 저작권은 항상 유지)</span></label>

      <label class=chk style="margin-top:16px"><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>분석 시작</button>
        <span class=hint>파일이 많으면 몇 분 걸릴 수 있어요. 창을 닫지 마세요.</span>
      </div>
    </form>
  </div>
</div>

<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">분석 중입니다… 잠시만요</p></div>
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
    return render_template_string(INDEX_HTML, has_key=cfg.has_api_key)


@app.route("/analyze", methods=["POST"], endpoint="analyze")
def analyze_route():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or cfg.api_key

    # 만들 자료 선택 (아무것도 안 고르면 분석지만)
    which = OutputsCfg(
        analysis=bool(request.form.get("out_analysis")),
        wordlist=bool(request.form.get("out_wordlist")),
        quiz=bool(request.form.get("out_quiz")),
    )
    if not (which.analysis or which.wordlist or which.quiz):
        which = OutputsCfg(analysis=True, wordlist=False, quiz=False)

    # '은아 T' 문구 넣기 체크박스 (하단 저작권은 항상 유지)
    brand = cfg.design.brand if request.form.get("brand") else ""

    # 저장 파일명(지문명) — 비우면 올린 파일 이름 사용
    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key)
    if not mock and not key:
        # 키 없고 미리보기도 아님 → 안내
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key)

    client = None if mock else ClaudeClient(key, cfg.model)

    results = []
    for idx, f in enumerate(files, start=1):
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(JPG·PNG·PDF만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        try:
            if mock:
                reports = pipeline._mock_reports_for_pdf(cfg, tmp)
            else:
                reports = pipeline.build_reports_for_pdf(client, cfg, tmp)
            if custom_base:
                # 지문명을 지정한 경우: 파일이 여러 개면 뒤에 번호를 붙여 충돌 방지
                stem = custom_base if len(files) == 1 else f"{custom_base}_{idx}"
            else:
                stem = _safe_name(Path(f.filename).stem)
            outs = pipeline.render_outputs(cfg, reports, stem, which=which, brand=brand)
            labels = {"analysis": "📘 분석지", "wordlist": "📝 어휘 리스트", "quiz": "✏️ 시험지"}
            fitems = [{"label": labels[k], "out": p.name} for k, p in outs.items()]
            note = f" (지문 {len(reports)}개)" if len(reports) > 1 else ""
            results.append({"name": f.filename + note, "ok": True, "files": fitems})
        except Exception as e:  # 개별 실패가 전체를 멈추지 않음
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": str(e)})
        finally:
            tmp.unlink(missing_ok=True)

    return render_result(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 56)
    print("  [6섹션 분석 도구] 웹앱이 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (구문 분석 학습지는 worksheet_app.py 를 실행하세요)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

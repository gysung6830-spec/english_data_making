"""Flask 웹앱: 업로드 → 형식 선택 → 파일명 입력 → 다운로드.

실행:
    python webapp.py        # http://localhost:5000
"""
from __future__ import annotations

import io
import os
import tempfile
import traceback
import zipfile
from pathlib import Path

from flask import (Flask, flash, redirect, render_template_string, request,
                   send_file, url_for)

try:
    from .main import (FORMATS, extract_passages, html_to_pdf, safe_filename)
    from .renderer import render_format_a, render_format_b, render_format_c
    from .translator import translate_missing
except ImportError:  # python webapp.py 로 직접 실행할 때
    from main import (FORMATS, extract_passages, html_to_pdf, safe_filename)
    from renderer import render_format_a, render_format_b, render_format_c
    from translator import translate_missing

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "passage3-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60MB

ALLOWED = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# 형식 표시 순서/이름
FORMAT_ORDER = [
    ("a", "한줄해석", "영어 문장 + 바로 아래 회색박스 한글해석"),
    ("c", "한줄영어", "영어 문장만 (해석 없음)"),
    ("b", "좌지문우해석", "좌 영어 / 우 한글 2단 표"),
]

PAGE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>영어 지문 → 3형식 PDF 생성기</title>
<style>
  /* 다크모드 기기에서도 항상 밝은 문서 UI로 고정 (입력 글자 흰색 방지) */
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { font-family: 'Noto Sans KR','Malgun Gothic',sans-serif; max-width: 640px;
         margin: 0 auto; padding: 24px 18px 60px; color:#1c1c1e; background:#fafafa; }
  h1 { font-size: 20px; margin: 8px 0 4px; color:#1c1c1e; }
  p.sub { color:#6e6e73; font-size:13px; margin:0 0 20px; }
  .card { background:#fff; border:1px solid #ececee; border-radius:12px;
          padding:18px; margin-bottom:16px; }
  label.field { display:block; font-weight:600; font-size:13.5px; margin-bottom:6px; color:#1c1c1e; }
  input[type=text], input[type=file] { width:100%; padding:9px 11px; font-size:14px;
          border:1px solid #d6d6da; border-radius:8px; background:#fff; color:#1c1c1e; }
  input[type=text]::placeholder { color:#9a9a9f; }
  .fmt { display:flex; align-items:flex-start; gap:10px; padding:10px;
         border:1px solid #ececee; border-radius:8px; margin-bottom:8px; cursor:pointer; }
  .fmt input { margin-top:3px; }
  .fmt b { display:block; font-size:14px; }
  .fmt span { font-size:12px; color:#6e6e73; }
  .preview { font-size:13px; color:#48484a; margin-top:8px; }
  .preview code { background:#f2f2f4; padding:2px 6px; border-radius:4px; }
  button { width:100%; padding:13px; font-size:15px; font-weight:700; color:#fff;
           background:#1c1c1e; border:none; border-radius:10px; cursor:pointer; }
  button:hover { background:#000; }
  .flash { background:#fde8e8; color:#a12626; border:1px solid #f5c2c2;
           border-radius:8px; padding:10px 12px; font-size:13.5px; margin-bottom:14px; }
  .hint { font-size:12px; color:#8a8a8e; margin-top:6px; }
</style>
</head>
<body>
  <h1>영어 지문 → 3형식 PDF 생성기</h1>
  <p class="sub">지문 파일(PDF·이미지·txt)을 올리면 한줄해석 · 한줄영어 · 좌지문우해석 PDF를 만들어 드립니다.</p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
    {% endif %}
  {% endwith %}

  <form method="post" action="{{ url_for('generate') }}" enctype="multipart/form-data">
    <div class="card">
      <label class="field" for="file">1. 지문 파일</label>
      <input type="file" id="file" name="file"
             accept=".pdf,.txt,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff" required>
      <div class="hint">PDF · 사진(JPG/PNG 등) · txt 지원. 스캔/사진은 자동 OCR.</div>
    </div>

    <div class="card">
      <label class="field">2. 출력 형식 (하나 이상 선택)</label>
      {% for key, name, desc in formats %}
      <label class="fmt">
        <input type="checkbox" name="fmt" value="{{ key }}" {% if key=='a' %}checked{% endif %}
               onchange="updatePreview()">
        <span><b>{{ name }}</b><span>{{ desc }}</span></span>
      </label>
      {% endfor %}
    </div>

    <div class="card">
      <label class="field" for="docname">3. PDF 파일명 (지문명)</label>
      <input type="text" id="docname" name="docname" placeholder="예: 2026년 5월 모의고사"
             oninput="updatePreview()" required>
      <div class="preview" id="preview"></div>
    </div>

    <div class="card">
      <label class="field" for="header">4. 상단 머리글 (선택)</label>
      <input type="text" id="header" name="header" placeholder="예: OO영어학원 · 지문 자료">
      <div class="hint">각 페이지 <b>오른쪽 위</b>에 표시됩니다(학원명·자료명 등). 비우면 표시 안 함.</div>
    </div>

    <div class="card">
      <label class="field" for="apikey">5. AI 번역 키 (선택)</label>
      <input type="password" id="apikey" name="apikey" placeholder="sk-ant-... (해석 없는 자료를 자동 번역)"
             autocomplete="off">
      <div class="hint">
        <b>영어만 있는 자료</b>에 한글 해석을 자동으로 채우려면 Claude API 키를 넣으세요.
        비우면 해석칸은 빈 채로 나옵니다. (해석이 이미 있는 자료는 키 없이 그대로 사용)
        키는 이번 생성에만 쓰이며 저장되지 않습니다.
      </div>
    </div>

    <button type="submit">PDF 생성 · 다운로드</button>
  </form>

<script>
  const SUFFIX = { a: "한줄해석", c: "한줄영어", b: "좌지문우해석" };
  function updatePreview() {
    const name = (document.getElementById('docname').value || '지문').trim() || '지문';
    const checked = Array.from(document.querySelectorAll('input[name=fmt]:checked')).map(x=>x.value);
    const box = document.getElementById('preview');
    if (checked.length === 0) { box.innerHTML = '형식을 하나 이상 선택하세요.'; return; }
    if (checked.length === 1) {
      box.innerHTML = '생성 파일: <code>' + name + '_' + SUFFIX[checked[0]] + '.pdf</code>';
    } else {
      const files = checked.map(k => name + '_' + SUFFIX[k] + '.pdf');
      box.innerHTML = '생성 파일(zip): <code>' + name + '_PDF.zip</code><br>&nbsp;└ ' +
                      files.map(f => '<code>'+f+'</code>').join(', ');
    }
  }
  updatePreview();
</script>
</body>
</html>
"""


def _ext_ok(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE, formats=FORMAT_ORDER)


@app.route("/generate", methods=["POST"])
def generate():
    file = request.files.get("file")
    docname = request.form.get("docname", "").strip()
    header = request.form.get("header", "").strip()
    formats = request.form.getlist("fmt")
    api_key = request.form.get("apikey", "").strip() or None

    if not file or not file.filename:
        flash("지문 파일을 선택하세요.")
        return redirect(url_for("index"))
    if not _ext_ok(file.filename):
        flash("지원하지 않는 파일 형식입니다. (PDF·이미지·txt)")
        return redirect(url_for("index"))
    if not formats:
        flash("출력 형식을 하나 이상 선택하세요.")
        return redirect(url_for("index"))

    doc = safe_filename(docname or Path(file.filename).stem)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        in_path = tmp_path / file.filename
        file.save(str(in_path))

        try:
            passages = extract_passages(in_path, api_key=api_key)
        except Exception:
            traceback.print_exc()
            flash("파일을 처리하는 중 오류가 발생했습니다.")
            return redirect(url_for("index"))

        if not passages:
            flash("지문을 찾지 못했습니다. 헤더 형식(…N번: 제목)과 원문자(①②)를 확인하세요.")
            return redirect(url_for("index"))

        # 한줄영어(c)만 선택하면 번역 불필요
        if any(f in formats for f in ("a", "b")):
            try:
                passages = translate_missing(passages, api_key=api_key)
            except Exception:
                traceback.print_exc()  # 번역 실패는 치명적이지 않음

        renderers = {
            "a": render_format_a,
            "c": render_format_c,
            "b": render_format_b,
        }

        produced = []  # (파일명, bytes)
        for key in [k for k, _, _ in FORMAT_ORDER if k in formats]:
            render_fn = renderers[key]
            suffix = FORMATS[key][1]
            html_str = render_fn(passages, header_text=header)
            out_pdf = tmp_path / f"{doc}_{suffix}.pdf"
            try:
                html_to_pdf(html_str, out_pdf, autofit=True)
            except Exception:
                traceback.print_exc()
                flash("PDF 렌더링 중 오류가 발생했습니다. (Playwright/Chromium 설치 확인)")
                return redirect(url_for("index"))
            produced.append((out_pdf.name, out_pdf.read_bytes()))

        if len(produced) == 1:
            name, data = produced[0]
            return send_file(io.BytesIO(data), mimetype="application/pdf",
                             as_attachment=True, download_name=name)

        # 여러 개 → zip
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in produced:
                zf.writestr(name, data)
        buf.seek(0)
        return send_file(buf, mimetype="application/zip", as_attachment=True,
                         download_name=f"{doc}_PDF.zip")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

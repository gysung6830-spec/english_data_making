"""Flask 웹앱: 업로드 → 형식 선택 → 파일명 입력 → 다운로드.

실행:
    python webapp.py        # http://localhost:5000
"""
from __future__ import annotations

import io
import os
import tempfile
import time
import traceback
import zipfile
from pathlib import Path


def _log(msg: str = "") -> None:
    """터미널(웹앱 창)에 진행 상황을 즉시 출력."""
    print(msg, flush=True)


def _fmt_dur(sec: float) -> str:
    """초 → '1분 5.2초' / '3.4초' 형태."""
    if sec >= 60:
        return f"{int(sec // 60)}분 {sec % 60:.0f}초"
    return f"{sec:.1f}초"


def _progress(label: str):
    """AI 단계 진행률을 한 줄에서 갱신(\\r)하는 콜백."""
    def cb(done: int, total: int) -> None:
        end = "\n" if done >= total else ""
        print(f"\r    {label} {done}/{total}", end=end, flush=True)
    return cb

from flask import (Flask, flash, redirect, render_template_string, request,
                   send_file, url_for)

try:
    from .chunker import chunk_sentences, any_needs_chunks
    from .main import (FORMATS, extract_passages, html_to_pdf,
                       renumber_passages, drop_practical_items, is_mock_exam,
                       safe_filename)
    from .renderer import (render_format_a, render_format_b, render_format_c,
                           render_format_d)
    from .segmenter import segment_passages
    from .serialize import passages_to_json
    from .translator import translate_missing
    from .vocab import extract_vocab
except ImportError:  # python webapp.py 로 직접 실행할 때
    from chunker import chunk_sentences, any_needs_chunks
    from main import (FORMATS, extract_passages, html_to_pdf,
                      renumber_passages, drop_practical_items, is_mock_exam,
                      safe_filename)
    from renderer import (render_format_a, render_format_b, render_format_c,
                          render_format_d)
    from segmenter import segment_passages
    from serialize import passages_to_json
    from translator import translate_missing
    from vocab import extract_vocab

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "passage3-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60MB

ALLOWED = {".pdf", ".txt", ".hwp", ".hwpx", ".json",
           ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

# 형식 표시 순서/이름
FORMAT_ORDER = [
    ("a", "한줄해석", "영어 문장 + 바로 아래 회색박스 한글해석"),
    ("c", "한줄영어", "영어 문장만 (해석 없음)"),
    ("b", "좌지문우해석", "좌 영어 / 우 한글 2단 표"),
    ("d", "직독직해", "한줄해석 + 영어 문장에 ' / '로 의미 단위 표시 (AI, 키 필요)"),
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
  /* 드래그앤드롭 파일 영역 */
  .dropzone { position:relative; border:2px dashed #c4dccd; border-radius:10px;
              background:#f4f9f6; padding:24px 14px; text-align:center; cursor:pointer;
              transition:border-color .15s, background .15s; }
  .dropzone.dragover { border-color:#14532d; background:#e7f0ea; }
  .dropzone .file-input { position:absolute; inset:0; width:100%; height:100%;
              opacity:0; cursor:pointer; }
  .dz-inner { pointer-events:none; color:#4b5563; font-size:13.5px; line-height:1.5; }
  .dz-inner b { color:#14532d; }
  .dz-icon { font-size:22px; color:#14532d; margin-bottom:4px; }
  .dz-name { display:inline-block; margin-top:2px; font-size:13px; color:#14532d; font-weight:700; }
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
  <p class="sub">지문 파일(PDF·HWP·이미지·txt)을 올리면 한줄해석 · 한줄영어 · 좌지문우해석 PDF를 만들어 드립니다.
    <br>이미 만든 <b>분석 JSON</b>을 다시 넣으면 <b>제목만 바꿔 재생성</b>(재분석·API 비용 없음)됩니다.</p>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
    {% endif %}
  {% endwith %}

  <form method="post" action="{{ url_for('generate') }}" enctype="multipart/form-data">
    <div class="card">
      <label class="field">1. 지문 파일</label>
      <div id="dropzone" class="dropzone">
        <input type="file" id="file" name="file" class="file-input"
               accept=".pdf,.txt,.hwp,.hwpx,.json,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff" required>
        <div class="dz-inner" id="dzText">
          <div class="dz-icon">⬆</div>
          <div><b>파일을 여기로 끌어다 놓거나</b> 클릭해서 선택</div>
        </div>
      </div>
      <div class="hint">PDF · HWP(한글) · 사진(JPG/PNG 등) · txt · <b>분석 JSON</b> 지원. 스캔/사진은 자동 OCR.
        분석 JSON을 넣으면 재분석 없이 바로 재생성됩니다.</div>
    </div>

    <div class="card">
      <label class="field">2. 출력 형식 (하나 이상 선택)</label>
      {% for key, name, desc in formats %}
      <label class="fmt">
        <input type="checkbox" name="fmt" value="{{ key }}" {% if key in ['a','d'] %}checked{% endif %}
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
      <label class="field" for="startno">4. 문항 시작 번호 (선택)</label>
      <input type="number" id="startno" name="startno" min="1" step="1"
             placeholder="예: 26  →  지문마다 26번, 27번, 28번 …">
      <div class="hint">입력하면 각 지문 제목이 <b>시작번호부터 1씩 증가</b>하는 문항번호로 표시됩니다.
        비우면 파일에서 인식한 번호를 그대로 사용합니다.</div>
      <label class="fmt" style="margin-top:10px;margin-bottom:0">
        <input type="checkbox" name="drop2728" value="1" checked>
        <span><b>모의고사 27·28번(실용문) 제외</b>
          <span><b>모의고사로 판별될 때만</b> 27·28번(안내문·광고)을 자동 제외합니다.
            교재 등 다른 자료는 그대로 둡니다. 포함하려면 체크 해제.</span></span>
      </label>
      <label class="fmt" style="margin-top:10px;margin-bottom:0">
        <input type="checkbox" name="fillpage" value="1">
        <span><b>페이지 꽉 채우기</b>
          <span>지문마다 남는 세로 여백을 문장 간격에 나눠 페이지를 아래까지 채웁니다.
            <b>기본은 꺼짐</b>(문장은 기본 간격, 하단 여백 유지). 한 페이지 압축은
            항상 적용됩니다. ※ 좌지문우해석(b)은 표 구조라 이 옵션과 무관합니다.</span></span>
      </label>
    </div>

    <div class="card">
      <label class="field" for="header">5. 상단 머리글 (선택)</label>
      <input type="text" id="header" name="header" placeholder="예: OO영어학원 · 지문 자료">
      <div class="hint">각 페이지 <b>오른쪽 위</b>에 표시됩니다(학원명·자료명 등). 비우면 표시 안 함.</div>
    </div>

    <div class="card">
      <label class="field" for="apikey">6. AI 번역 키 (선택)</label>
      <input type="password" id="apikey" name="apikey" placeholder="sk-ant-... (해석 없는 자료를 자동 번역)"
             autocomplete="off">
      <div class="hint">
        <b>영어만 있는 자료</b>에 한글 해석을 자동으로 채우려면 Claude API 키를 넣으세요.
        비우면 해석칸은 빈 채로 나옵니다. (해석이 이미 있는 자료는 키 없이 그대로 사용)
        키는 이번 생성에만 쓰이며 저장되지 않습니다.
      </div>
    </div>

    <div class="card">
      <label class="fmt" style="margin-bottom:0">
        <input type="checkbox" name="savejson" value="1" checked>
        <span><b>7. 분석 데이터(JSON) 함께 받기</b>
          <span>나중에 <b>제목만 바꿔 재생성</b>할 때 이 JSON을 다시 넣으면 API 비용 없이 즉시 생성됩니다.</span></span>
      </label>
    </div>

    <button type="submit">PDF 생성 · 다운로드</button>
  </form>

<script>
  const SUFFIX = { a: "한줄해석", c: "한줄영어", b: "좌지문우해석", d: "직독직해" };
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

  // 드래그앤드롭 파일 선택
  (function(){
    const dz = document.getElementById('dropzone');
    const fileInput = document.getElementById('file');
    const dzText = document.getElementById('dzText');
    function showName(){
      if (fileInput.files && fileInput.files.length){
        var fn = fileInput.files[0].name;
        var isJson = /\.json$/i.test(fn);
        var extra = isJson
          ? '<div style="font-size:12px;color:#14532d;margin-top:3px;font-weight:700">분석 JSON 재입력 — 제목만 바꿔 재분석 없이 재생성됩니다</div>'
          : '<div style="font-size:12px;color:#6b7280;margin-top:3px">다른 파일을 끌어다 놓거나 클릭해 변경</div>';
        dzText.innerHTML = '<div class="dz-icon">' + (isJson ? '🔄' : '📄') + '</div>'
          + '선택된 파일: <span class="dz-name">' + fn + '</span>' + extra;
      }
    }
    fileInput.addEventListener('change', showName);
    ['dragenter','dragover'].forEach(function(ev){
      dz.addEventListener(ev, function(e){ e.preventDefault(); e.stopPropagation(); dz.classList.add('dragover'); });
    });
    ['dragleave','dragend','drop'].forEach(function(ev){
      dz.addEventListener(ev, function(e){ e.preventDefault(); e.stopPropagation(); dz.classList.remove('dragover'); });
    });
    dz.addEventListener('drop', function(e){
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length){
        try { fileInput.files = files; } catch(_) {}
        showName();
      }
    });
  })();
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
    start_no = request.form.get("startno", "").strip() or None
    save_json = request.form.get("savejson") == "1"
    drop_2728 = request.form.get("drop2728") == "1"
    fill_page = request.form.get("fillpage") == "1"

    if not file or not file.filename:
        flash("지문 파일을 선택하세요.")
        return redirect(url_for("index"))
    if not _ext_ok(file.filename):
        flash("지원하지 않는 파일 형식입니다. (PDF·HWP·이미지·txt)")
        return redirect(url_for("index"))
    if not formats:
        flash("출력 형식을 하나 이상 선택하세요.")
        return redirect(url_for("index"))

    doc = safe_filename(docname or Path(file.filename).stem)
    t0 = time.perf_counter()
    fmt_names = ", ".join(FORMATS[k][1] for k, _, _ in FORMAT_ORDER if k in formats)
    _log("")
    _log("=" * 60)
    _log(f"[생성 시작] {docname or Path(file.filename).stem}  "
         f"({time.strftime('%Y-%m-%d %H:%M:%S')})")
    _log(f"  파일: {file.filename} | 형식: {fmt_names}"
         f"{' | AI 키 사용' if api_key else ' | 키 없음'}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        in_path = tmp_path / file.filename
        file.save(str(in_path))

        try:
            t = time.perf_counter()
            passages = extract_passages(in_path, api_key=api_key)
        except Exception:
            traceback.print_exc()
            flash("파일을 처리하는 중 오류가 발생했습니다.")
            return redirect(url_for("index"))

        if not passages:
            _log("[중단] 지문을 찾지 못했습니다.")
            flash("지문을 찾지 못했습니다. 헤더 형식(…N번: 제목)과 원문자(①②)를 확인하세요.")
            return redirect(url_for("index"))

        # 문항 시작 번호 지정 시 라벨 재부여
        passages = renumber_passages(passages, start_no)
        # 모의고사일 때만 실용문(27·28번) 제외
        if drop_2728 and is_mock_exam(passages, docname):
            before = len(passages)
            passages = drop_practical_items(passages)
            if len(passages) < before:
                _log(f"    모의고사 판정 · 27·28번(실용문) 제외: {before} → {len(passages)}개")
        elif drop_2728:
            _log("    모의고사 아님 → 27·28번 유지")
        n_sent = sum(len(p.sentences) for p in passages)
        _log(f"[1] 입력 파싱 완료 — 지문 {len(passages)}개, 문장 {n_sent}개  "
             f"({_fmt_dur(time.perf_counter() - t)})")

        # 분석 단계는 '이미 있는 항목은 건너뛴다'(idempotent). JSON 재입력이라도
        # 누락분(예: 새로 분리된 장문 문장의 청크)은 키가 있으면 채운다.
        #   - 완성된 자료 + 키 없음 → 모두 no-op(비용 0)
        #   - 일부 누락 + 키 있음 → 누락분만 생성
        is_json_input = Path(file.filename).suffix.lower() == ".json"
        if is_json_input:
            _log("[2] JSON 재입력 — 이미 분석된 항목 재사용, 누락분만 채움(키 있을 때)")
        # 번호 없는 통짜 지문을 AI로 문장 분리(키 있으면)
        n_raw = sum(1 for p in passages if not p.sentences and p.raw)
        if n_raw:
            if api_key:
                _log(f"[2] 번호 없는 지문 {n_raw}개 AI 문장 분리 중…")
                t = time.perf_counter()
                try:
                    passages = segment_passages(passages, api_key=api_key,
                                                progress=_progress("지문"))
                    _log(f"    → 문장 분리 완료, 총 문장 "
                         f"{sum(len(p.sentences) for p in passages)}개  "
                         f"({_fmt_dur(time.perf_counter() - t)})")
                except Exception:
                    traceback.print_exc()
            else:
                _log(f"[2] 번호 없는 지문 {n_raw}개 발견 — 키가 없어 건너뜀"
                     "(빈 지문으로 나옴)")
        # 한줄영어(c)만 선택하면 번역 불필요
        if any(f in formats for f in ("a", "b", "d")):
            miss = sum(1 for p in passages for s in p.sentences if s.en and not s.ko)
            if miss and api_key:
                _log(f"[3] 해석 없는 문장 {miss}개 번역 중…")
                t = time.perf_counter()
                try:
                    passages = translate_missing(passages, api_key=api_key)
                    _log(f"    → 번역 완료  ({_fmt_dur(time.perf_counter() - t)})")
                except Exception:
                    traceback.print_exc()
        # 하단 어휘 리스트(키 있으면, 어휘 없는 지문만 자동 추출)
        if api_key and any(not p.vocab and any(s.en for s in p.sentences)
                           for p in passages):
            _log("[4] 핵심 어휘 추출 중(AI, 누락 지문만)…")
            t = time.perf_counter()
            try:
                passages = extract_vocab(passages, api_key=api_key,
                                         progress=_progress("어휘"))
                _log(f"    → 어휘 추출 완료  ({_fmt_dur(time.perf_counter() - t)})")
            except Exception:
                traceback.print_exc()
        # 직독직해 청크(키 있으면, 청크가 없거나 뜻이 비어 미완성인 문장만)
        if "d" in formats and api_key and any_needs_chunks(passages):
            _log("[5] 직독직해 청크 생성 중(AI, 누락 문장만)…")
            t = time.perf_counter()
            try:
                passages = chunk_sentences(passages, api_key=api_key,
                                           progress=_progress("직독직해"))
                _log(f"    → 직독직해 청크 완료  ({_fmt_dur(time.perf_counter() - t)})")
            except Exception:
                traceback.print_exc()

        renderers = {
            "a": render_format_a,
            "c": render_format_c,
            "b": render_format_b,
            "d": render_format_d,
        }

        disp_name = (docname or Path(file.filename).stem).strip()  # 뱃지 표시용
        produced = []  # (파일명, bytes)
        _log("[6] PDF 렌더링…")
        for key in [k for k, _, _ in FORMAT_ORDER if k in formats]:
            render_fn = renderers[key]
            suffix = FORMATS[key][1]
            t = time.perf_counter()
            html_str = render_fn(passages, header_text=header, doc_name=disp_name)
            out_pdf = tmp_path / f"{doc}_{suffix}.pdf"
            try:
                html_to_pdf(html_str, out_pdf, autofit=True,
                            fill_page=fill_page)
            except Exception:
                traceback.print_exc()
                flash("PDF 렌더링 중 오류가 발생했습니다. (Playwright/Chromium 설치 확인)")
                return redirect(url_for("index"))
            produced.append((out_pdf.name, out_pdf.read_bytes()))
            _log(f"    · {out_pdf.name}  ({_fmt_dur(time.perf_counter() - t)})")

        # 재사용용 분석 JSON (제목만 바꿔 재생성할 때 다시 입력)
        json_bytes = None
        if save_json:
            json_bytes = passages_to_json(passages, docname=disp_name).encode("utf-8")

        _log(f"[완료] PDF {len(produced)}개"
             f"{' + 분석 JSON' if json_bytes else ''} 생성 — "
             f"총 {_fmt_dur(time.perf_counter() - t0)}")
        _log("=" * 60)

        # 형식 1개 + JSON 미포함 → PDF 그대로
        if len(produced) == 1 and not json_bytes:
            name, data = produced[0]
            return send_file(io.BytesIO(data), mimetype="application/pdf",
                             as_attachment=True, download_name=name)

        # 그 외 → zip (PDF들 + 분석 JSON)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in produced:
                zf.writestr(name, data)
            if json_bytes:
                zf.writestr(f"{doc}_ORTICA.json", json_bytes)
        buf.seek(0)
        return send_file(buf, mimetype="application/zip", as_attachment=True,
                         download_name=f"{doc}_PDF.zip")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

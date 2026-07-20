#!/usr/bin/env python3
"""영어 지문 분석 도구 - 웹앱(브라우저) 버전.

실행:
    python webapp.py
그다음 브라우저에서  http://localhost:5000  접속.

터미널을 몰라도, 브라우저에서 파일을 올리고 버튼만 누르면
분석 PDF가 만들어집니다.
"""
from __future__ import annotations

import os
import re
import secrets
import traceback
import uuid
from pathlib import Path

from flask import (Flask, abort, redirect, render_template_string, request,
                   session, send_from_directory, url_for)

from src import extract, pipeline, render
from src.client import ClaudeClient
from src.config import ROOT, OutputsCfg, load_config
from src.worksheet import pipeline as ws_pipeline
from src.worksheet.pipeline import Header as WsHeader

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60MB 업로드 제한
app.secret_key = os.environ.get("APP_SECRET") or secrets.token_hex(16)

# 인터넷에 올릴 때 접속 비밀번호 (환경변수 APP_PASSWORD). 없으면 잠금 없음(로컬용).
APP_PASSWORD = os.environ.get("APP_PASSWORD")

cfg = load_config()
UPLOAD_DIR = ROOT / "web_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = cfg.output_dir

ALLOWED = {".pdf"} | extract.IMAGE_EXTS


# ---------------------------------------------------------------------------
# HTML 템플릿 (한 파일로 관리)
# ---------------------------------------------------------------------------
BASE_CSS = """
  :root{--ink:#23272e;--accent:#1d4ed8;--green:#15803d;--muted:#6b7280;--line:#e5e7eb;}
  *{box-sizing:border-box;}
  body{font-family:'Nanum Gothic','NanumGothic',system-ui,sans-serif;color:var(--ink);
       background:#f6f7f9;margin:0;padding:24px;line-height:1.55;}
  .wrap{max-width:720px;margin:0 auto;}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;
        box-shadow:0 1px 3px rgba(0,0,0,.05);margin-bottom:18px;}
  h1{font-size:22px;margin:0 0 4px;}
  .sub{color:var(--muted);font-size:13px;margin-bottom:18px;}
  label{font-weight:700;font-size:14px;display:block;margin:14px 0 6px;}
  input[type=text],input[type=password]{width:100%;padding:10px 12px;border:1px solid var(--line);
        border-radius:8px;font-size:14px;}
  .drop{border:2px dashed #c7cdd6;border-radius:12px;padding:26px;text-align:center;
        background:#fafbfc;cursor:pointer;transition:.15s;}
  .drop.hl{border-color:var(--accent);background:#eff4ff;}
  .drop p{margin:6px 0;color:var(--muted);font-size:13px;}
  .files{margin-top:10px;font-size:13px;color:var(--ink);}
  .btn{display:inline-block;background:var(--accent);color:#fff;border:none;border-radius:9px;
       padding:12px 22px;font-size:15px;font-weight:700;cursor:pointer;}
  .btn:disabled{opacity:.5;cursor:not-allowed;}
  .btn.gray{background:#374151;}
  .chk{display:flex;align-items:center;gap:8px;font-size:14px;margin-top:12px;font-weight:600;}
  .hint{font-size:12px;color:var(--muted);margin-top:6px;}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px;}
  .layouts{display:flex;gap:12px;margin-top:8px;}
  .lay{flex:1;border:1.5px solid var(--line);border-radius:12px;padding:9px;margin:0;cursor:pointer;
       display:block;font-weight:400;}
  .lay .lh{font-size:14px;display:flex;align-items:center;gap:6px;font-weight:700;}
  .lay img{width:100%;border:1px solid var(--line);border-radius:6px;margin:6px 0;display:block;}
  .lay .ld{font-size:11px;color:var(--muted);line-height:1.4;}
  .lay:has(input:checked){border-color:var(--accent);background:#f2f6ff;}
  table{width:100%;border-collapse:collapse;margin-top:6px;font-size:14px;}
  td,th{padding:9px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle;}
  .ok{color:var(--green);font-weight:700;}
  .fail{color:#be123c;font-weight:700;}
  a.dl{color:var(--accent);font-weight:700;text-decoration:none;margin-right:12px;}
  .err{background:#fff1f3;border:1px solid #fecdd3;color:#9f1239;padding:10px 12px;border-radius:8px;
       font-size:13px;margin-top:10px;}
  #overlay{position:fixed;inset:0;background:rgba(255,255,255,.85);display:none;
           align-items:center;justify-content:center;flex-direction:column;z-index:10;}
  .spin{width:44px;height:44px;border:5px solid #d1d5db;border-top-color:var(--accent);
        border-radius:50%;animation:sp 1s linear infinite;}
  @keyframes sp{to{transform:rotate(360deg);}}
"""

INDEX_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>영어 지문 분석 도구</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>📘 영어 지문 자동 분석</h1>
    <div class=sub>지문 사진(JPG/PNG)이나 PDF를 올리면, 분석지·어휘 리스트·영단어 시험지를 만들어 드립니다.</div>
    <div style="margin:-6px 0 14px"><a class=dl href="{{ url_for('worksheet') }}">✏️ 구문 분석 학습지(직독직해 + 태깅) 만들러 가기 →</a></div>
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

RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>분석 결과</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✅ 분석 결과</h1>
    <div class=sub>성공 {{ n_ok }}개 · 실패 {{ n_fail }}개 (총 {{ results|length }}개)</div>
    <table>
      <tr><th>파일</th><th>상태</th><th>결과 PDF</th></tr>
      {% for r in results %}
      <tr>
        <td>{{ r.name }}</td>
        <td>{% if r.ok %}<span class=ok>완료</span>{% else %}<span class=fail>실패</span>{% endif %}</td>
        <td>
          {% if r.ok %}
            {% for fitem in r.files %}
            <div style="margin-bottom:5px">
              <b style="font-size:12px">{{ fitem.label }}</b>&nbsp;
              <a class=dl href="{{ url_for('view', fname=fitem.out) }}" target=_blank>미리보기</a>
              <a class=dl href="{{ url_for('download', fname=fitem.out) }}">다운로드</a>
            </div>
            {% endfor %}
          {% else %}<span class=hint>{{ r.error }}</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
    </table>
    <div class=row><a class="btn gray" href="{{ url_for('index') }}">← 다른 파일 분석하기</a></div>
  </div>
</div></body></html>
"""


LOGIN_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>로그인</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap><div class=card style="max-width:420px;margin:60px auto;">
  <h1>🔒 로그인</h1>
  <div class=sub>이 도구를 사용하려면 비밀번호를 입력하세요.</div>
  {% if err %}<div class=err>{{ err }}</div>{% endif %}
  <form method=post>
    <label>비밀번호</label>
    <input type=password name=password autofocus>
    <div class=row><button class=btn type=submit>들어가기</button></div>
  </form>
</div></div></body></html>
"""


# ---------------------------------------------------------------------------
# 접속 잠금 (인터넷 배포 시)
# ---------------------------------------------------------------------------
@app.before_request
def _auth_gate():
    if not APP_PASSWORD:
        return  # 비밀번호 미설정 → 잠금 없음(내 컴퓨터 로컬 사용용)
    if request.endpoint in ("login", "static"):
        return
    if session.get("auth"):
        return
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["auth"] = True
            return redirect(url_for("index"))
        err = "비밀번호가 틀렸습니다."
    return render_template_string(LOGIN_HTML, err=err)


# ---------------------------------------------------------------------------
# 라우트
# ---------------------------------------------------------------------------
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

    n_ok = sum(1 for r in results if r["ok"])
    return render_template_string(RESULT_HTML, results=results,
                                  n_ok=n_ok, n_fail=len(results) - n_ok)


def _safe_name(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", stem).strip() or "passage"


def _safe_output(fname: str) -> Path:
    """다운로드 경로 검증(디렉터리 탈출 방지)."""
    p = (OUTPUT_DIR / fname).resolve()
    if not str(p).startswith(str(OUTPUT_DIR.resolve())) or not p.is_file():
        abort(404)
    return p


@app.route("/download/<path:fname>")
def download(fname):
    _safe_output(fname)
    return send_from_directory(OUTPUT_DIR, fname, as_attachment=True)


@app.route("/view/<path:fname>")
def view(fname):
    _safe_output(fname)
    return send_from_directory(OUTPUT_DIR, fname, as_attachment=False)


# ---------------------------------------------------------------------------
# 구문 분석 학습지 (레이아웃 A/B)
# ---------------------------------------------------------------------------
WORKSHEET_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>구문 분석 학습지 만들기</title><style>""" + BASE_CSS + """
  fieldset{border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:14px;}
  legend{font-weight:800;font-size:13px;padding:0 6px;}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
  .radio{display:flex;gap:16px;flex-wrap:wrap;margin-top:6px;}
  .radio label{font-weight:600;display:flex;align-items:center;gap:6px;margin:0;}
  select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:8px;font-size:14px;}
</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✏️ 구문 분석 학습지</h1>
    <div class=sub>지문을 문장 단위로 쪼개 <b>직독직해 + 구문 태깅 + 포인트 박스</b> 학습지를 만듭니다.</div>
    <div style="margin:-6px 0 12px"><a class=dl href="{{ url_for('index') }}">← 6개 섹션 분석 도구로 돌아가기</a></div>
    <form id=f method=post action="{{ url_for('worksheet_build') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png" hidden>
      </div>
      <div class=files id=filelist></div>

      <fieldset><legend>② 레이아웃 <span class=hint>(예시 사진 참고)</span></legend>
        <div class=layouts>
          <label class=lay>
            <span class=lh><input type=radio name=layout value=A checked> A. 포인트박스형</span>
            <img src="{{ url_for('static', filename='layout_a.png') }}" alt="A형 예시">
            <span class=ld>리본 + 구문 분석 + 포인트 박스<br>(한 지문을 최대한 1페이지로 자동 압축)</span>
          </label>
          <label class=lay>
            <span class=lh><input type=radio name=layout value=B> B. 직독직해형</span>
            <img src="{{ url_for('static', filename='layout_b.png') }}" alt="B형 예시">
            <span class=ld>영어 원문 + 문법 태그 / 직독직해 + 핵심 단어</span>
          </label>
        </div>
      </fieldset>

      <fieldset><legend>③ 태깅 강도</legend>
        <div class=radio>
          <label><input type=radio name=strength value=full checked> 전체</label>
          <label><input type=radio name=strength value=key> 핵심만</label>
          <label><input type=radio name=strength value=none> 없음(원문+해석)</label>
        </div>
      </fieldset>

      <fieldset><legend>④ 강 번호 · 저장 파일명</legend>
        <label>강 번호</label><input type=text name=lecture_label placeholder="예: 20 / 14강">
        <label>저장 파일명 (지문명) <span class=hint>(비우면 올린 파일 이름)</span></label>
        <input type=text name=basename placeholder="예: 2027수능특강_20강">
        <div class=hint>영문 제목과 한글 부제는 지문 내용을 보고 <b>자동으로</b> 붙습니다.</div>
      </fieldset>

      <label>⑤ Anthropic API 키
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


@app.route("/worksheet")
def worksheet():
    return render_template_string(WORKSHEET_HTML, has_key=cfg.has_api_key)


@app.route("/worksheet/build", methods=["POST"], endpoint="worksheet_build")
def worksheet_build_route():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    form_key = (request.form.get("api_key") or "").strip()
    key = (None if "설정됨" in form_key else (form_key or None)) or cfg.api_key

    layout = "B" if (request.form.get("layout") == "B") else "A"
    density = "auto"   # A형은 항상 자동 압축(한 지문 최대한 1페이지)
    brand = cfg.design.brand or "은아 T"   # 직독직해 헤더 'made by …'
    kind = "포인트박스형" if layout == "A" else "직독직해형"
    strength = request.form.get("strength") or "full"
    if strength not in ("full", "key", "none"):
        strength = "full"

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
        if ext not in ALLOWED:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(JPG·PNG·PDF만 가능)"})
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
            ws_pipeline.render_worksheet(analyses, out, layout=layout, brand=brand,
                                         footer_note=footer, density=density)
            note = f" (지문 {len(analyses)}개)" if len(analyses) > 1 else ""
            results.append({"name": f.filename + note, "ok": True,
                            "files": [{"label": f"✏️ {kind}", "out": out.name}]})
        except Exception as e:  # 개별 실패가 전체를 멈추지 않음
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": str(e)})
        finally:
            tmp.unlink(missing_ok=True)

    n_ok = sum(1 for r in results if r["ok"])
    return render_template_string(RESULT_HTML, results=results,
                                  n_ok=n_ok, n_fail=len(results) - n_ok)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 56)
    print("  영어 지문 분석 웹앱이 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

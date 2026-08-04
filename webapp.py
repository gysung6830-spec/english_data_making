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

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60MB 업로드 제한
app.secret_key = os.environ.get("APP_SECRET") or secrets.token_hex(16)

# 인터넷에 올릴 때 접속 비밀번호 (환경변수 APP_PASSWORD). 없으면 잠금 없음(로컬용).
APP_PASSWORD = os.environ.get("APP_PASSWORD")

cfg = load_config()
UPLOAD_DIR = ROOT / "web_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = cfg.output_dir

ALLOWED = {".pdf", ".json"} | extract.IMAGE_EXTS | extract.HWP_EXTS


# ---------------------------------------------------------------------------
# HTML 템플릿 (한 파일로 관리)
# ---------------------------------------------------------------------------
BASE_CSS = """
  @font-face{font-family:'NanumSquareRound';font-weight:400;
    src:url('/fonts/NanumSquareRoundR.woff2') format('woff2');}
  @font-face{font-family:'NanumSquareRound';font-weight:700;
    src:url('/fonts/NanumSquareRoundB.woff2') format('woff2');}
  @font-face{font-family:'NanumSquareRound';font-weight:800;
    src:url('/fonts/NanumSquareRoundEB.woff2') format('woff2');}
  :root{--ink:#23272e;--accent:#0e7c74;--green:#15803d;--muted:#6b7280;--line:#e5e7eb;}
  *{box-sizing:border-box;}
  body{font-family:'NanumSquareRound','Nanum Gothic','NanumGothic',system-ui,sans-serif;color:var(--ink);
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
  table{width:100%;border-collapse:collapse;margin-top:6px;font-size:14px;}
  td,th{padding:9px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle;}
  .ok{color:var(--green);font-weight:700;}
  .fail{color:#be123c;font-weight:700;}
  .warn{color:#b45309;font-weight:700;}
  .warnbox{background:#fffbeb;border:1px solid #fde68a;color:#92400e;font-size:12px;
           padding:5px 8px;border-radius:6px;margin-top:5px;}
  .remode{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;font-size:13px;
          padding:9px 12px;border-radius:8px;margin-top:10px;}
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
    <h1>🖊️ 내신 서술형 대비 교재 만들기</h1>
    <div class=sub>지문 사진(JPG/PNG)·PDF·한글(HWP/HWPX)을 올리면, <b>내신 서술형 대비 교재</b>를 만들어 드립니다.</div>
    <form id=f method=post action="{{ url_for('analyze') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF·HWP, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF · HWP · HWPX · <b>JSON(재편집)</b></p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png,.hwp,.hwpx,.json" hidden>
      </div>
      <div class=files id=filelist></div>
      <div class=hint>💾 이미 뽑은 결과의 <b>재편집용 데이터(JSON)</b>를 <b>끌어다 놓거나</b> 선택하면 <b>API 없이</b> 제목·번호만 바꿔 다시 뽑습니다.</div>
      <div id=remode class=remode style="display:none">🔁 <b>재편집 모드</b> — API를 사용하지 않고 제목·번호만 바꿔 다시 뽑습니다. 아래 <b>③ 저장 파일명</b>에 새 제목을 입력하세요.</div>

      <label>② Anthropic API 키
        <span class=hint>(console.anthropic.com 에서 발급 · 미리보기만 할 거면 비워도 됨)</span>
      </label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}"
             {{ 'readonly' if has_key else '' }}>
      {% if has_key %}<div class=hint>.env에 저장된 키가 있어 자동으로 사용됩니다.</div>{% endif %}

      <label>③ 저장 파일명 <span class=hint>(비우면 올린 파일 이름 사용)</span></label>
      <input type=text name=basename placeholder="예: 공통영어2 1과">
      <div class=hint><b>(입력)_서술형대비.pdf</b> 로 저장되고, 입력한 이름이 <b>교재 제목</b>으로 쓰입니다.</div>

      <label>④ 시작 문항번호 <span class=hint>(이 번호부터 1씩 자동 증가)</span></label>
      <input type=number name=start_no min=1 step=1 value=1 style="width:120px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px;">
      <div class=hint>예: <b>5</b> 를 넣으면 첫 문항이 5번, 그다음 6·7…로 매겨집니다. (여러 지문이면 유형별로 이어서 증가)</div>

      <label>⑤ 지문 번호 <span class=hint>(배지 '파일명-지문번호'에 표시 · 여러 지문이면 1씩 증가)</span></label>
      <input type=number name=passage_start_no min=1 step=1 value=1 style="width:120px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px;">
      <div class=hint>예: 파일명 <b>올림포스 7강</b>, 지문 번호 <b>3</b> → 배지가 <b>올림포스 7강-3</b> 으로 표시됩니다.</div>

      <div class=hint style="margin-top:14px">📄 결과물: <b>내신 서술형 대비 교재</b> (7개 유형 · 학생용 / 교사용 / 빠른 정답 / 정답 및 해설)</div>

      <label class=chk style="margin-top:12px"><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

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
 const remode=document.getElementById('remode'),go=document.getElementById('go');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{ev.preventDefault();file.files=ev.dataTransfer.files;show();});
 file.onchange=show;
 function isJson(n){return n.toLowerCase().endsWith('.json');}
 function show(){
   const fs=[...file.files];
   list.innerHTML=fs.map(x=>(isJson(x.name)?'💾 ':'📄 ')+x.name).join('<br>')||'';
   const reedit=fs.length>0 && fs.every(x=>isJson(x.name));
   remode.style.display=reedit?'block':'none';
   go.textContent=reedit?'제목 바꿔 다시 뽑기':'분석 시작';
 }
 f.onsubmit=()=>{
   if(!file.files.length){alert('파일을 먼저 올려주세요.');return false;}
   const fs=[...file.files], reedit=fs.every(x=>isJson(x.name));
   ov.querySelector('p').textContent=reedit?'제목을 바꿔 다시 만드는 중입니다…':'분석 중입니다… 잠시만요';
   ov.style.display='flex';
 };
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
        <td>{% if r.ok %}{% if r.warn %}<span class=warn>확인 필요</span>{% else %}<span class=ok>완료</span>{% endif %}{% else %}<span class=fail>실패</span>{% endif %}</td>
        <td>
          {% if r.ok %}
            {% for fitem in r.files %}
            <div style="margin-bottom:5px">
              <b style="font-size:12px">{{ fitem.label }}</b>&nbsp;
              {% if fitem.pdf %}<a class=dl href="{{ url_for('view', fname=fitem.out) }}" target=_blank>미리보기</a>{% endif %}
              <a class=dl href="{{ url_for('download', fname=fitem.out) }}">다운로드</a>
            </div>
            {% endfor %}
            {% for w in r.warn %}<div class=warnbox>⚠ {{ w }}</div>{% endfor %}
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
    if request.endpoint in ("login", "static", "fonts"):
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

    # 이 웹앱은 '서술형 대비 교재'만 산출한다(다른 자료는 만들지 않음).
    which = OutputsCfg(analysis=False, wordlist=False, quiz=False, worksheet=True)
    brand = cfg.design.brand

    # 저장 파일명(지문명) — 비우면 올린 파일 이름 사용
    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    # 시작 문항번호(사용자 지정) — 이 번호부터 1씩 자동 증가. 기본 1.
    try:
        start_no = max(1, int(request.form.get("start_no") or 1))
    except (TypeError, ValueError):
        start_no = 1
    # 지문 시작 번호(사용자 지정) — 배지 '파일명-지문번호'에 반영. 기본 1.
    try:
        passage_start_no = max(1, int(request.form.get("passage_start_no") or 1))
    except (TypeError, ValueError):
        passage_start_no = 1

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key)
    # JSON(재편집용 데이터)만 올린 경우는 분석이 없으므로 API 키가 필요 없다.
    json_only = all(Path(f.filename).suffix.lower() == ".json" for f in files)
    if not mock and not key and not json_only:
        # 키 없고 미리보기도 아니고 JSON 재편집도 아님 → 안내
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요."
            " (재편집용 JSON만 올릴 때는 키가 필요 없습니다.)</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key)

    client = None if (mock or not key) else ClaudeClient(key, cfg.model)

    results = []
    for idx, f in enumerate(files, start=1):
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(PDF·JPG·PNG·HWP·HWPX만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        try:
            reports = []
            if ext == ".json":
                # 재편집용 데이터: API 없이 제목·번호만 바꿔 재렌더
                worksheets, meta = pipeline.load_worksheets_json(tmp)
            elif mock:
                reports = (pipeline._mock_reports_for_pdf(cfg, tmp)
                           if which.needs_report else [])
                worksheets = (pipeline._mock_worksheets_for_pdf(cfg, tmp)
                              if which.worksheet else [])
            elif client is None:
                results.append({"name": f.filename, "ok": False,
                                "error": "API 키가 필요합니다(이 파일은 분석이 필요함)."})
                continue
            else:
                reports, worksheets = pipeline.build_all_for_pdf(client, cfg, tmp, which=which)
            if custom_base:
                # 지문명을 지정한 경우: 파일이 여러 개면 뒤에 번호를 붙여 충돌 방지
                stem = custom_base if len(files) == 1 else f"{custom_base}_{idx}"
            elif ext == ".json":
                # 파일명 미입력 시 원래 이름에서 '_서술형대비' 접미사를 떼어 기본값으로
                stem = _safe_name(re.sub(r"_서술형대비$", "", Path(f.filename).stem))
            else:
                stem = _safe_name(Path(f.filename).stem)
            recs = pipeline.render_outputs(cfg, reports, stem, which=which, brand=brand,
                                           worksheets=worksheets, ws_start_no=start_no,
                                           ws_passage_start_no=passage_start_no)
            fitems = [{"label": r["label"], "out": r["path"].name,
                       "pdf": r["path"].suffix.lower() == ".pdf"} for r in recs]
            n_passages = max(len(reports), len(worksheets))
            note = f" (지문 {n_passages}개)" if n_passages > 1 else ""
            if ext == ".json":
                note += " · 🔁 재편집(API 미사용)"
            results.append({"name": f.filename + note, "ok": True, "files": fitems,
                            "warn": _ws_warnings(worksheets)})
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


_WS_TYPE_LABELS = [("summary", "요약문"), ("paraphrase", "문장변형"),
                   ("arrange", "배열영작"), ("compose", "조건영작"),
                   ("choice", "보기어휘"), ("error", "어법오류"), ("qa", "문답")]


def _ws_warnings(worksheets) -> list:
    """생성 실패로 '누락된 유형'을 파일별로 표시(무검수 운영 triage용)."""
    warns = []
    for i, ws in enumerate(worksheets, 1):
        missing = [label for field, label in _WS_TYPE_LABELS
                   if getattr(ws, field, None) is None]
        if missing:
            tag = f"지문 {i} · " if len(worksheets) > 1 else ""
            warns.append(f"{tag}누락 유형: {', '.join(missing)}")
    return warns


def _safe_output(fname: str) -> Path:
    """다운로드 경로 검증(디렉터리 탈출 방지)."""
    p = (OUTPUT_DIR / fname).resolve()
    if not str(p).startswith(str(OUTPUT_DIR.resolve())) or not p.is_file():
        abort(404)
    return p


FONT_DIR = ROOT / "templates" / "fonts"


@app.route("/fonts/<path:fname>")
def fonts(fname):
    """웹 UI 용 나눔스퀘어라운드 웹폰트 제공."""
    p = (FONT_DIR / fname).resolve()
    if not str(p).startswith(str(FONT_DIR.resolve())) or not p.is_file():
        abort(404)
    return send_from_directory(FONT_DIR, fname)


@app.route("/download/<path:fname>")
def download(fname):
    _safe_output(fname)
    return send_from_directory(OUTPUT_DIR, fname, as_attachment=True)


@app.route("/view/<path:fname>")
def view(fname):
    _safe_output(fname)
    return send_from_directory(OUTPUT_DIR, fname, as_attachment=False)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 56)
    print("  영어 지문 분석 웹앱이 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

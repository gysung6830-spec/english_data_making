#!/usr/bin/env python3
"""기초 브릿지 교재 생성기 — 독립 웹앱(브라우저) 버전.

문법을 모르는 학생용 '기초 브릿지 교재'를 지문에서 난이도 맞춤으로 자동 생성한다.
(지문 분석지·어휘·시험지를 만드는 webapp.py 와는 별개의 앱)

실행:
    python bridge_webapp.py          # 기본 포트 5002
    PORT=5005 python bridge_webapp.py
그다음 브라우저에서  http://localhost:5002  접속.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import traceback
import uuid
from pathlib import Path

from flask import (Flask, abort, redirect, render_template_string, request,
                   session, send_from_directory, url_for)

from src import bridge, extract, pipeline
from src.client import ClaudeClient
from src.config import ROOT, load_config

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
app.secret_key = os.environ.get("APP_SECRET") or secrets.token_hex(16)

APP_PASSWORD = os.environ.get("APP_PASSWORD")  # 배포 시 접속 잠금(없으면 로컬용)

cfg = load_config()
UPLOAD_DIR = ROOT / "web_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = cfg.output_dir
ALLOWED = {".pdf"} | extract.IMAGE_EXTS


def _levels_json() -> str:
    return json.dumps({str(k): {"key": v["key"], "desc": v["desc"]}
                       for k, v in bridge.LEVELS.items()}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# HTML (초록 톤 — 브릿지 교재 브랜드)
# ---------------------------------------------------------------------------
BASE_CSS = """
  :root{--ink:#23272e;--green:#1f7a48;--green2:#2f9e5f;--muted:#6b7280;--line:#e5e7eb;}
  *{box-sizing:border-box;}
  body{font-family:'Nanum Gothic','NanumGothic',system-ui,sans-serif;color:var(--ink);
       background:#f3f7f4;margin:0;padding:24px;line-height:1.55;}
  .wrap{max-width:720px;margin:0 auto;}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;
        box-shadow:0 1px 3px rgba(0,0,0,.05);margin-bottom:18px;}
  h1{font-size:22px;margin:0 0 4px;}
  .sub{color:var(--muted);font-size:13px;margin-bottom:18px;}
  label{font-weight:700;font-size:14px;display:block;margin:14px 0 6px;}
  input[type=text],input[type=password]{width:100%;padding:10px 12px;border:1px solid var(--line);
        border-radius:8px;font-size:14px;}
  .drop{border:2px dashed #b9d6c4;border-radius:12px;padding:26px;text-align:center;
        background:#fafdfb;cursor:pointer;transition:.15s;}
  .drop.hl{border-color:var(--green2);background:#eef7f1;}
  .drop p{margin:6px 0;color:var(--muted);font-size:13px;}
  .files{margin-top:10px;font-size:13px;color:var(--ink);}
  .btn{display:inline-block;background:var(--green);color:#fff;border:none;border-radius:9px;
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
  a.dl{color:var(--green);font-weight:700;text-decoration:none;margin-right:12px;}
  .err{background:#fff1f3;border:1px solid #fecdd3;color:#9f1239;padding:10px 12px;border-radius:8px;
       font-size:13px;margin-top:10px;}
  .lvbox{background:#eef7f1;border:1px solid #cfe6d8;border-radius:10px;padding:16px;margin-top:10px;}
  input[type=range]{width:100%;accent-color:var(--green2);}
  .lvscale{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:2px;}
  .lvkey{font-weight:800;color:var(--green);margin-top:8px;font-size:16px;}
  .lvdesc{font-size:13px;color:#374151;margin-top:2px;}
  #overlay{position:fixed;inset:0;background:rgba(255,255,255,.85);display:none;
           align-items:center;justify-content:center;flex-direction:column;z-index:10;}
  .spin{width:44px;height:44px;border:5px solid #d1d5db;border-top-color:var(--green2);
        border-radius:50%;animation:sp 1s linear infinite;}
  @keyframes sp{to{transform:rotate(360deg);}}
"""

INDEX_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>기초 브릿지 교재 생성기</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>📗 기초 브릿지 교재 생성기</h1>
    <div class=sub>문법을 모르는 학생용! 지문을 올리고 <b>난이도만 고르면</b> 표지·요약·학습지(단어·기초문법·끊어읽기·문제)를 만들어 드립니다.</div>
    <form id=f method=post action="{{ url_for('generate') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png" hidden>
      </div>
      <div class=files id=filelist></div>

      <label>② 학습자 난이도 <span class=hint>(슬라이더를 옮기면 설명이 바뀝니다)</span></label>
      <div class=lvbox>
        <input type=range name=bridge_level id=blevel min=1 max=5 step=1 value=1>
        <div class=lvscale><span>1 쉬움</span><span>2</span><span>3</span><span>4</span><span>5 어려움</span></div>
        <div class=lvkey id=blevel_key></div>
        <div class=lvdesc id=blevel_desc></div>
      </div>

      <label>③ Anthropic API 키
        <span class=hint>(console.anthropic.com 에서 발급 · 미리보기만 할 거면 비워도 됨)</span>
      </label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}"
             {{ 'readonly' if has_key else '' }}>
      {% if has_key %}<div class=hint>.env에 저장된 키가 있어 자동으로 사용됩니다.</div>{% endif %}

      <label>④ 저장 파일명 (지문명) <span class=hint>(비우면 올린 파일 이름 사용)</span></label>
      <input type=text name=basename placeholder="예: 천재L1_모기">

      <label class=chk style="margin-top:16px"><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>교재 만들기</button>
        <span class=hint>지문당 1회 생성 요청이 있어 몇 분 걸릴 수 있어요. 창을 닫지 마세요.</span>
      </div>
    </form>
  </div>
</div>

<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">교재를 만들고 있어요… 잠시만요</p></div>
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
 // 난이도 슬라이더
 const LV={{ levels_json|safe }};
 const bl=document.getElementById('blevel'),bk=document.getElementById('blevel_key'),bd=document.getElementById('blevel_desc');
 function upLv(){bk.textContent=bl.value+'단계 · '+LV[bl.value].key; bd.textContent=LV[bl.value].desc;}
 bl.addEventListener('input',upLv); upLv();
</script>
</body></html>
"""

RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>생성 결과</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✅ 교재 생성 결과</h1>
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
    <div class=row><a class="btn gray" href="{{ url_for('index') }}">← 다른 지문으로 만들기</a></div>
  </div>
</div></body></html>
"""

LOGIN_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>로그인</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap><div class=card style="max-width:420px;margin:60px auto;">
  <h1>🔒 로그인</h1><div class=sub>이 도구를 사용하려면 비밀번호를 입력하세요.</div>
  {% if err %}<div class=err>{{ err }}</div>{% endif %}
  <form method=post><label>비밀번호</label><input type=password name=password autofocus>
    <div class=row><button class=btn type=submit>들어가기</button></div></form>
</div></div></body></html>
"""


@app.before_request
def _auth_gate():
    if not APP_PASSWORD:
        return
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


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, has_key=cfg.has_api_key,
                                  levels_json=_levels_json())


@app.route("/generate", methods=["POST"], endpoint="generate")
def generate_route():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or cfg.api_key
    try:
        level = max(1, min(5, int(request.form.get("bridge_level", 1))))
    except (TypeError, ValueError):
        level = 1

    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key,
                                      levels_json=_levels_json())
    if not mock and not key:
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key,
                                      levels_json=_levels_json())

    client = None if mock else ClaudeClient(key, cfg.model)
    lv_key = bridge.level_meta(level)["key"]

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
            stem = (custom_base if len(files) == 1 else f"{custom_base}_{idx}") \
                if custom_base else _safe_name(Path(f.filename).stem)

            extractions = [None] if mock else pipeline.build_extractions_for_pdf(client, cfg, tmp)
            fitems = []
            for j, ex in enumerate(extractions, start=1):
                suffix = "" if len(extractions) == 1 else f"_{j}"
                if mock:
                    gen = bridge.mock_gen(level=level)
                    src = f"{f.filename} · 샘플 미리보기"
                else:
                    gen = bridge.generate(client, cfg, ex, level)
                    src = getattr(ex, "source", "") or f.filename
                out = OUTPUT_DIR / f"{stem}{suffix}_브릿지교재_{lv_key}.pdf"
                bridge.render_pdf(gen, out, level, source=src)
                fitems.append({"label": f"📗 브릿지 교재({level}·{lv_key})", "out": out.name})

            note = f" (지문 {len(extractions)}개)" if len(extractions) > 1 else ""
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    print("=" * 56)
    print("  📗 기초 브릿지 교재 생성기(웹앱)가 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

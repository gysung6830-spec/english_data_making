#!/usr/bin/env python3
"""두 웹앱(6섹션 분석 도구 · 구문 분석 학습지)이 공유하는 최소 웹 유틸.

⚠️ 경계 안내
  - '구문 분석 학습지(본 코딩)' 웹앱  : worksheet_app.py
  - '6섹션 분석 도구(별개 도구)' 웹앱 : webapp.py
  둘은 화면(라우트/폼)이 서로 분리돼 있으며, 여기 있는 공통 코드(접속 잠금·
  파일 다운로드·업로드 경로·기본 CSS·결과 화면)만 함께 쓴다. 지문 추출/LLM
  클라이언트/설정 같은 '분석 코어'는 src/ 를 공유한다.
"""
from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

from flask import (Flask, abort, redirect, render_template_string, request,
                   send_from_directory, session, url_for)

from src import extract
from src.config import ROOT, load_config

cfg = load_config()
UPLOAD_DIR = ROOT / "web_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = cfg.output_dir
STATIC_DIR = ROOT / "static"

ALLOWED = {".pdf"} | extract.IMAGE_EXTS

# 인터넷에 올릴 때 접속 비밀번호 (환경변수 APP_PASSWORD). 없으면 잠금 없음(로컬용).
APP_PASSWORD = os.environ.get("APP_PASSWORD")


# ---------------------------------------------------------------------------
# 공통 CSS / 결과·로그인 화면
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

RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>결과</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✅ 완료</h1>
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
    <div class=row><a class="btn gray" href="{{ url_for('index') }}">← 다시 만들기</a></div>
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


def _safe_name(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", stem).strip() or "passage"


def _safe_output(fname: str) -> Path:
    """다운로드 경로 검증(디렉터리 탈출 방지)."""
    p = (OUTPUT_DIR / fname).resolve()
    if not str(p).startswith(str(OUTPUT_DIR.resolve())) or not p.is_file():
        abort(404)
    return p


def render_result(results: list[dict]):
    n_ok = sum(1 for r in results if r["ok"])
    return render_template_string(RESULT_HTML, results=results,
                                  n_ok=n_ok, n_fail=len(results) - n_ok)


def make_app(import_name: str) -> Flask:
    """접속 잠금·로그인·파일 다운로드/미리보기가 이미 붙은 Flask 앱을 만든다.

    각 앱(webapp.py / worksheet_app.py)은 여기에 'index'와 자기 라우트만 더한다.
    """
    app = Flask(import_name, static_folder=str(STATIC_DIR))
    app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024  # 60MB 업로드 제한
    app.secret_key = os.environ.get("APP_SECRET") or secrets.token_hex(16)

    @app.before_request
    def _auth_gate():
        if not APP_PASSWORD:
            return  # 비밀번호 미설정 → 잠금 없음(로컬 사용용)
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

    @app.route("/download/<path:fname>")
    def download(fname):
        _safe_output(fname)
        return send_from_directory(OUTPUT_DIR, fname, as_attachment=True)

    @app.route("/view/<path:fname>")
    def view(fname):
        _safe_output(fname)
        return send_from_directory(OUTPUT_DIR, fname, as_attachment=False)

    return app

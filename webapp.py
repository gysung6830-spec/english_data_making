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

from src import extract, pipeline, workbook_render, blanks_render, blanks_schemas
from src.client import ClaudeClient
from src.config import ROOT, load_config

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
  .kinds{display:flex;gap:10px;flex-wrap:wrap;}
  .kind{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:600;
        border:1px solid var(--line);border-radius:9px;padding:9px 12px;cursor:pointer;flex:1;}
  .hint{font-size:12px;color:var(--muted);margin-top:6px;}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px;}
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
    <div class=sub>지문 사진(JPG/PNG)이나 PDF를 올리면, 통합 워크북·빈칸 채우기 워크북 PDF를 만들어 드립니다.</div>
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

      <label>③ 산출물 종류 <span class=hint>(원하는 것을 모두 선택)</span></label>
      <div class=kinds>
        <label class=kind><input type=checkbox name=kinds value=workbook checked> 통합 워크북</label>
        <label class=kind><input type=checkbox name=kinds value=blanks> 빈칸 채우기 워크북</label>
      </div>

      <label>④ 저장할 PDF 파일명
        <span class=hint>(비우면 자동: <b>지문명_워크북</b>)</span>
      </label>
      <input type=text name=outname placeholder="예: 올림포스_Unit10_워크북">
      <div class=hint>여러 지문을 올리면 파일명 뒤에 지문 이름이 붙습니다.</div>

      <label class=chk><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

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
            <a class=dl href="{{ url_for('view', fname=r.out) }}" target=_blank>미리보기</a>
            <a class=dl href="{{ url_for('download', fname=r.out) }}">다운로드</a>
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
    kinds = request.form.getlist("kinds") or ["workbook"]   # 체크박스(복수 선택). 기본: 통합 워크북
    custom = _safe_name((request.form.get("outname") or "").strip()) if (request.form.get("outname") or "").strip() else ""
    single = len(files) == 1
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or cfg.api_key

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key)
    if not mock and not key:
        # 키 없고 미리보기도 아님 → 안내
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key)

    client = None if mock else ClaudeClient(key, cfg.model)

    do_workbook = "workbook" in kinds
    do_blanks = "blanks" in kinds
    multi_types = (do_workbook + do_blanks) >= 2

    def out_name(stem, type_suffix, default_suffix):
        """사용자 지정명(custom) 우선, 없으면 지문명+기본접미사.
        여러 산출물 유형을 함께 뽑을 땐 custom 뒤에 유형 접미사로 구분."""
        if custom:
            b = custom if single else f"{custom}_{stem}"
            return f"{b}{type_suffix if multi_types else ''}"
        return f"{stem}{default_suffix}"

    results = []
    wb_books = []       # 통합 워크북 파일간 합본용
    blank_sets = []     # 빈칸형 파일간 합본용
    n_files_ok = 0      # 산출물을 낸 파일 수(파일간 합본 여부 판단용)
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(JPG·PNG·PDF만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        stem = _safe_name(Path(f.filename).stem)
        try:
            if do_workbook:
                # 한 파일에 여러 지문이 있으면 지문별 워크북을 모두 만든다.
                wbs = ([pipeline._mock_workbook_for_pdf(cfg, tmp)] if mock
                       else pipeline.build_workbooks_for_pdf(client, cfg, tmp))
                out = OUTPUT_DIR / f"{out_name(stem, '_통합', '_워크북')}.pdf"
                workbook_render.render_workbooks_pdf(wbs, out, footer_note=cfg.design.footer_note)
                wb_books.extend(wbs)
                results.append({"name": f"{f.filename} · 통합 워크북 (지문 {len(wbs)}편)",
                                "ok": True, "out": out.name})
            if do_blanks:
                file_sets = ([pipeline._mock_blank_set_for_pdf(cfg, tmp, 1)] if mock
                             else pipeline.build_blank_sets_for_pdf(client, cfg, tmp))
                for idx, st in enumerate(file_sets, start=1):
                    st.no = idx
                bwb = blanks_schemas.build_blank_workbook(
                    blanks_schemas.LLMBlankWorkbook(sets=file_sets),
                    title=file_sets[0].title, subtitle=file_sets[0].subtitle)
                out = OUTPUT_DIR / f"{out_name(stem, '_빈칸', '_빈칸워크북')}.pdf"
                blanks_render.render_blanks_pdf(bwb, out, footer_note=cfg.design.footer_note)
                blank_sets.extend(file_sets)
                results.append({"name": f"{f.filename} · 빈칸형 (지문 {len(file_sets)}편)",
                                "ok": True, "out": out.name})
            n_files_ok += 1
        except Exception as e:  # 개별 실패가 전체를 멈추지 않음
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": str(e)})
        finally:
            tmp.unlink(missing_ok=True)

    # 파일이 '2개 이상'일 때만 파일들을 하나로 합친 합본 추가(단일 파일은 이미 지문별로 다 들어감)
    if do_workbook and n_files_ok >= 2 and len(wb_books) >= 2:
        try:
            combined = OUTPUT_DIR / f"{(custom + '_통합합본') if custom else '통합워크북_합본'}.pdf"
            workbook_render.render_workbooks_pdf(wb_books, combined, footer_note=cfg.design.footer_note)
            results.append({"name": "📚 통합 워크북 합본", "ok": True, "out": combined.name})
        except Exception as e:
            traceback.print_exc()
            results.append({"name": "📚 통합 합본", "ok": False, "error": str(e)})

    # 빈칸형: 파일 2개 이상일 때만 파일간 합본 추가
    if do_blanks and n_files_ok >= 2 and len(blank_sets) >= 2:
        try:
            for idx, st in enumerate(blank_sets, start=1):
                st.no = idx
            bwb = blanks_schemas.build_blank_workbook(
                blanks_schemas.LLMBlankWorkbook(sets=blank_sets),
                title="빈칸 워크북", subtitle="유형 B 지문 빈칸 · 유형 A 요약문 빈칸")
            combined = OUTPUT_DIR / f"{(custom + '_빈칸합본') if custom else '빈칸워크북_합본'}.pdf"
            blanks_render.render_blanks_pdf(bwb, combined, footer_note=cfg.design.footer_note)
            results.append({"name": "📚 빈칸형 합본", "ok": True, "out": combined.name})
        except Exception as e:
            traceback.print_exc()
            results.append({"name": "📚 빈칸 합본", "ok": False, "error": str(e)})

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 56)
    print("  영어 지문 분석 웹앱이 실행되었습니다.")
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

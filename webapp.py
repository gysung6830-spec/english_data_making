#!/usr/bin/env python3
"""영어 지문 분석 도구 - 웹앱(브라우저) 버전.

실행:
    python webapp.py
그다음 브라우저에서  http://localhost:5000  접속.

터미널을 몰라도, 브라우저에서 파일을 올리고 버튼만 누르면
분석 PDF가 만들어집니다.
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

from src import extract, hwp, pipeline, render, schemas
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

ALLOWED = {".pdf"} | extract.IMAGE_EXTS | hwp.HWP_EXTS


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
    <div class=sub>지문 사진(JPG/PNG)·PDF·HWP를 올리면, 분석지·어휘 리스트·영단어 시험지를 만들어 드립니다.</div>
    <form id=f method=post action="{{ url_for('analyze') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (사진·PDF·HWP, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>JPG · PNG · PDF · HWP · HWPX</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png,.hwp,.hwpx" hidden>
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

      <label>④ 시작 문항번호 <span class=hint>(예: 31 — 지문마다 1씩 자동 증가. 비우면 원본 번호/순번 사용)</span></label>
      <input type=text name=start_no placeholder="예: 31" inputmode=numeric>
      <div class=hint>제목이 <b>31. 주제</b> → <b>32. 주제</b> → <b>33. 주제</b> … 순으로 매겨집니다.</div>

      <label>⑤ 만들 자료 선택 <span class=hint>(직독직해 핵심 어휘로 리스트·시험지도 함께)</span></label>
      <label class=chk><input type=checkbox name=out_analysis value=1 checked> 📘 지문 분석지 (교사용·정답 포함)</label>
      <label class=chk><input type=checkbox name=out_student value=1> 📗 지문 분석지 (학생용·정답 빈칸)</label>
      <label class=chk><input type=checkbox name=out_wordlist value=1 checked> 📝 어휘 리스트 (직독직해 단어+뜻)</label>
      <label class=chk><input type=checkbox name=out_quiz value=1 checked> ✏️ 영단어 시험지 (뜻 맞히기·정답 포함)</label>
      <label class=chk><input type=checkbox name=out_vocablist value=1 checked> 📚 핵심 어휘 리스트 (유의어·반의어)</label>
      <label class=chk><input type=checkbox name=out_vocabtest value=1 checked> 🧩 핵심 어휘 시험지 (뜻쓰기+유의어/반의어 줄긋기)</label>

      <label class=chk style="margin-top:16px"><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>분석 시작</button>
        <span class=hint>파일이 많으면 몇 분 걸릴 수 있어요. 창을 닫지 마세요.</span>
      </div>
    </form>
  </div>

  <div class=card>
    <h1 style="font-size:19px">🔁 제목만 수정 (재분석 없음 · API 비용 X)</h1>
    <div class=sub>이미 분석한 결과와 함께 받은 <b>제목수정용 데이터(.json)</b>를 올리고, 지문명·시작번호만 바꿔 다시 뽑습니다.</div>
    <form id=f2 method=post action="{{ url_for('reedit') }}" enctype=multipart/form-data>
      <label>① 제목수정용 데이터 (.json)</label>
      <div class=drop id=drop2>
        <div style="font-size:22px">🔁</div>
        <p><b>여기를 클릭</b>해 .json 파일을 올리세요</p>
        <p>결과와 함께 받은 ‘🔁 제목수정용 데이터(.json)’</p>
        <input id=file2 type=file name=bundles multiple accept=".json" hidden>
      </div>
      <div class=files id=filelist2></div>

      <label>② 새 지문명 <span class=hint>(제목 뱃지·저장 파일명에 사용)</span></label>
      <input type=text name=re_basename placeholder="예: 2022올림포스_Ch04">

      <label>③ 시작 문항번호 <span class=hint>(비우면 기존 번호 유지)</span></label>
      <input type=text name=re_start_no placeholder="예: 11" inputmode=numeric>

      <label>④ 만들 자료</label>
      <label class=chk><input type=checkbox name=re_analysis value=1 checked> 📘 지문 분석지(교사용)</label>
      <label class=chk><input type=checkbox name=re_student value=1> 📗 지문 분석지(학생용)</label>
      <label class=chk><input type=checkbox name=re_wordlist value=1 checked> 📝 어휘 리스트</label>
      <label class=chk><input type=checkbox name=re_quiz value=1 checked> ✏️ 영단어 시험지</label>
      <label class=chk><input type=checkbox name=re_vocablist value=1 checked> 📚 핵심 어휘 리스트</label>
      <label class=chk><input type=checkbox name=re_vocabtest value=1 checked> 🧩 핵심 어휘 시험지</label>

      <div class=row>
        <button class="btn gray" id=go2 type=submit>제목 바꿔 다시 뽑기</button>
        <span class=hint>API 재호출 없이 즉시 생성됩니다.</span>
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

 // 🔁 제목만 수정 폼
 const drop2=document.getElementById('drop2'),file2=document.getElementById('file2'),
       list2=document.getElementById('filelist2'),f2=document.getElementById('f2');
 drop2.onclick=()=>file2.click();
 ['dragover','dragenter'].forEach(e=>drop2.addEventListener(e,ev=>{ev.preventDefault();drop2.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop2.addEventListener(e,ev=>{ev.preventDefault();drop2.classList.remove('hl');}));
 drop2.addEventListener('drop',ev=>{file2.files=ev.dataTransfer.files;show2();});
 file2.onchange=show2;
 function show2(){list2.innerHTML=[...file2.files].map(x=>'📄 '+x.name).join('<br>')||'';}
 f2.onsubmit=()=>{if(!file2.files.length){alert('제목수정용 데이터(.json)를 올려주세요.');return false;} ov.style.display='flex';};
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
              {% if not fitem.dl_only %}<a class=dl href="{{ url_for('view', fname=fitem.out) }}" target=_blank>미리보기</a>{% endif %}
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
        student=bool(request.form.get("out_student")),
        wordlist=bool(request.form.get("out_wordlist")),
        quiz=bool(request.form.get("out_quiz")),
        vocablist=bool(request.form.get("out_vocablist")),
        vocabtest=bool(request.form.get("out_vocabtest")),
    )
    if not (which.analysis or which.student or which.wordlist or which.quiz
            or which.vocablist or which.vocabtest):
        which = OutputsCfg(analysis=True, wordlist=False, quiz=False,
                           vocablist=False, vocabtest=False)

    # 브랜드 문구(직독직해 made by ~). config 값 사용(기본 비어 있음).
    brand = cfg.design.brand

    # 저장 파일명(지문명) — 비우면 올린 파일 이름 사용
    raw_name = (request.form.get("basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""

    # 시작 문항번호 — 입력 시 지문마다 1씩 자동 증가(비우면 원본 번호/순번 사용)
    raw_start = (request.form.get("start_no") or "").strip()
    try:
        running_no = int(raw_start) if raw_start else None
    except ValueError:
        running_no = None

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
                            "error": "지원하지 않는 형식(JPG·PNG·PDF·HWP·HWPX만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        try:
            if mock:
                reports = pipeline._mock_reports_for_pdf(cfg, tmp)
            else:
                reports = pipeline.build_reports_for_pdf(client, cfg, tmp)
            # 시작 문항번호가 지정되면 지문마다 번호를 1씩 올려 부여(파일 간에도 연속)
            if running_no is not None:
                for rep in reports:
                    rep.item_no = str(running_no)
                    running_no += 1
            if custom_base:
                # 지문명을 지정한 경우: 파일이 여러 개면 뒤에 번호를 붙여 충돌 방지
                stem = custom_base if len(files) == 1 else f"{custom_base}_{idx}"
            else:
                stem = _safe_name(Path(f.filename).stem)
            # 지문 번호 뱃지에 쓸 '파일명' — 지문명(입력) 또는 업로드 파일 이름(깔끔한 형태)
            file_label = custom_base or _safe_name(Path(f.filename).stem)
            recs = pipeline.render_outputs(cfg, reports, stem, which=which, brand=brand,
                                           source_label=file_label)
            fitems = [{"label": r["label"], "out": r["path"].name} for r in recs]
            # 제목만 바꿔 재출력할 수 있게 분석 데이터(JSON) 저장 → 다운로드 제공
            bundle = _save_bundle(stem, reports, brand)
            fitems.append({"label": "🔁 제목수정용 데이터(.json)", "out": bundle.name, "dl_only": True})
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


@app.route("/reedit", methods=["POST"], endpoint="reedit")
def reedit_route():
    """이미 분석한 결과(제목수정용 .json)를 다시 넣어 제목·번호만 바꿔 재출력(API 미사용)."""
    files = [f for f in request.files.getlist("bundles") if f and f.filename]
    which = OutputsCfg(
        analysis=bool(request.form.get("re_analysis")),
        student=bool(request.form.get("re_student")),
        wordlist=bool(request.form.get("re_wordlist")),
        quiz=bool(request.form.get("re_quiz")),
        vocablist=bool(request.form.get("re_vocablist")),
        vocabtest=bool(request.form.get("re_vocabtest")),
    )
    if not (which.analysis or which.student or which.wordlist or which.quiz
            or which.vocablist or which.vocabtest):
        which = OutputsCfg(analysis=True, wordlist=False, quiz=False,
                           vocablist=False, vocabtest=False)
    brand = cfg.design.brand

    raw_name = (request.form.get("re_basename") or "").strip()
    custom_base = _safe_name(raw_name) if raw_name else ""
    raw_start = (request.form.get("re_start_no") or "").strip()
    try:
        running_no = int(raw_start) if raw_start else None
    except ValueError:
        running_no = None

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key)

    results = []
    for idx, f in enumerate(files, start=1):
        try:
            if Path(f.filename).suffix.lower() != ".json":
                raise ValueError(
                    "‘제목수정용 데이터(.json)’ 파일만 올릴 수 있습니다. "
                    "결과 PDF가 아니라, 분석 결과와 함께 받은 .json 파일을 올려 주세요."
                )
            raw = f.stream.read()
            try:
                text = raw.decode("utf-8-sig")  # BOM 있어도 처리
            except UnicodeDecodeError:
                raise ValueError(
                    "이 파일은 텍스트(.json)가 아닙니다(PDF·이미지 등으로 보임). "
                    "분석 결과와 함께 받은 ‘🔁 제목수정용 데이터(.json)’를 올려 주세요."
                )
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                raise ValueError("제목수정용 데이터(.json)를 읽을 수 없습니다(형식 오류).")
            reports = [schemas.Report.model_validate(d) for d in data.get("reports", [])]
            if not reports:
                raise ValueError("제목수정용 데이터에 분석 결과가 없습니다(.json 파일이 맞는지 확인).")
            # 시작 문항번호 지정 시 지문마다 1씩 증가
            if running_no is not None:
                for rp in reports:
                    rp.item_no = str(running_no)
                    running_no += 1
            base_from_file = _safe_name(Path(f.filename).stem.replace("_편집데이터", ""))
            stem = custom_base or base_from_file
            if custom_base and len(files) > 1:
                stem = f"{custom_base}_{idx}"
            label = custom_base or base_from_file
            recs = pipeline.render_outputs(cfg, reports, stem, which=which, brand=brand,
                                           source_label=label)
            fitems = [{"label": r["label"], "out": r["path"].name} for r in recs]
            bundle = _save_bundle(stem, reports, brand)
            fitems.append({"label": "🔁 제목수정용 데이터(.json)", "out": bundle.name, "dl_only": True})
            results.append({"name": f.filename + " → 제목 수정", "ok": True, "files": fitems})
        except Exception as e:
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": str(e)})

    n_ok = sum(1 for r in results if r["ok"])
    return render_template_string(RESULT_HTML, results=results,
                                  n_ok=n_ok, n_fail=len(results) - n_ok)


def _safe_name(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", stem).strip() or "passage"


def _save_bundle(stem: str, reports, brand: str) -> Path:
    """분석 결과(Report들)를 JSON 으로 저장 → 나중에 제목만 바꿔 재출력(무 API)."""
    bundle = {"meta": {"brand": brand},
              "reports": [rp.model_dump(mode="json") for rp in reports]}
    p = OUTPUT_DIR / f"{stem}_편집데이터.json"
    p.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    return p


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

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

from src import extract, pipeline, envcheck, bundle
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

ALLOWED = {".pdf"} | extract.IMAGE_EXTS | extract.HWP_EXTS


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
    <div class=sub>지문 사진(JPG/PNG)·PDF·HWP를 올리면, 통합 워크북·빈칸 채우기 워크북 PDF를 만들어 드립니다.</div>
    {{ env_banner|safe }}
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

      <label>③ 산출물 <span class=hint>(자동 생성)</span></label>
      <div class=kinds>
        <label class=kind><input type=checkbox name=kinds value=workbook checked> 통합 워크북 <span class=hint>(단일유형·빈칸 포함)</span></label>
      </div>
      <div class=hint>※ 한 파일에 <b>통합 카드 → 단일 유형 → 빈칸 워크북</b> 순서로 모두 담깁니다.</div>

      <label>④ 저장할 PDF 파일명
        <span class=hint>(비우면 자동: <b>지문명_워크북</b>)</span>
      </label>
      <input type=text name=outname placeholder="예: 올림포스_Unit10_워크북">
      <div class=hint>여러 지문을 올리면 파일명 뒤에 지문 이름이 붙습니다.</div>

      <label>⑤ 시작 문항번호 <span class=hint>(선택 — 비우면 자동 추출)</span></label>
      <input type=number name=start_no min=1 max=200 placeholder="예: 30">
      <div class=hint>입력하면 <b>첫 지문 = 그 번호</b>, 이후 지문마다 <b>1씩 자동 증가</b>합니다(30 → 31 → 32 …). 뱃지 오류를 없애는 가장 확실한 방법이에요.</div>

      <label class=chk><input type=checkbox name=verify_vocab value=1 checked> 어휘(상) 자동 교차검증 <span class=hint>(정답이 정확히 2개인지 저비용 AI가 재검토 · 지문당 비용 +1~2%)</span></label>
      <label class=chk><input type=checkbox name=mock value=1> 샘플 미리보기 (API 키 없이 디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>분석 시작</button>
        <span class=hint>파일이 많으면 몇 분 걸릴 수 있어요. 창을 닫지 마세요.</span>
      </div>
    </form>
  </div>

  <div class=card>
    <h1>✏️ 제목만 바꾸기 <span class=hint style="font-weight:400">(API 재분석 없이 · 무료)</span></h1>
    <div class=sub>이미 분석해서 받은 <b>분석데이터(JSON)</b> 파일을 올리면, 분석은 그대로 두고 <b>제목만</b> 고쳐 다시 뽑습니다.</div>
    <form method=post action="{{ url_for('retitle') }}" enctype=multipart/form-data>
      <label>분석데이터(JSON) 파일 <span class=hint>(결과 표의 «💾 분석데이터(JSON)» 로 받은 파일)</span></label>
      <input type=file name=bundle accept=".json" required>
      <div class=row><button class="btn gray" type=submit>제목 수정하러 가기 →</button></div>
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
            {% if r.json %}<a class=dl href="{{ url_for('download', fname=r.json) }}" title="제목만 바꿔 다시 뽑을 때 이 파일을 올리세요">💾 분석데이터(JSON)</a>{% endif %}
          {% else %}<span class=hint>{{ r.error }}</span>{% endif %}
        </td>
      </tr>
      {% endfor %}
    </table>
    <div class=row><a class="btn gray" href="{{ url_for('index') }}">← 다른 파일 분석하기</a></div>
  </div>
</div></body></html>
"""


RETITLE_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>제목 수정</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✏️ 제목 수정</h1>
    <div class=sub>분석 내용은 그대로 두고 제목만 바꿉니다. (API 재분석 없음 · 무료)</div>
    {% if err %}<div class=err>{{ err }}</div>{% endif %}
    <form id=f method=post action="{{ url_for('retitle_apply') }}" enctype=multipart/form-data>
      <input type=hidden name=token value="{{ token }}">
      {% for t in titles %}
      <label>지문 {{ loop.index }} 제목</label>
      <input type=text name="title_{{ loop.index0 }}" value="{{ t }}">
      {% endfor %}
      <label>저장할 PDF 파일명 <span class=hint>(비우면 원래 이름 유지)</span></label>
      <input type=text name=outname value="{{ outname }}" placeholder="예: 올림포스_Unit10_워크북">
      <div class=row>
        <button class=btn id=go type=submit>제목 바꿔 다시 뽑기</button>
        <a class="btn gray" href="{{ url_for('index') }}">← 취소</a>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">다시 뽑는 중입니다…</p></div>
<script>
 const f=document.getElementById('f'),ov=document.getElementById('overlay');
 f.onsubmit=()=>{ov.style.display='flex';};
</script>
</body></html>
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
def _env_banner_html() -> str:
    """환경 자가진단 결과를 배너 HTML 로. 문제 없으면 빈 문자열."""
    result = envcheck.check_environment(cfg)
    bad = [it for it in result["items"] if not it["ok"]]
    if not bad:
        return ""
    rows = "".join(f"<li><b>{it['name']}</b> — {it['detail']}</li>" for it in bad)
    return (
        '<div class=err style="background:#fff8e1;border-color:#f5d78a;color:#7a5b00">'
        '<b>⚠️ 실행 환경 점검</b> — 아래 항목을 해결해야 정상 동작합니다.'
        f'<ul style="margin:6px 0 0 18px;padding:0">{rows}</ul></div>'
    )


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, has_key=cfg.has_api_key,
                                  env_banner=_env_banner_html())


@app.route("/health")
def health():
    """환경 자가진단 결과(JSON). 문제 유무를 프로그램적으로 확인할 때."""
    from flask import jsonify
    return jsonify(envcheck.check_environment(cfg))


@app.route("/analyze", methods=["POST"], endpoint="analyze")
def analyze_route():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    # 어휘(상) 자동 교차검증 토글(기본 켜짐). 이번 요청에만 반영.
    cfg.processing.verify_vocab = bool(request.form.get("verify_vocab"))
    custom = _safe_name((request.form.get("outname") or "").strip()) if (request.form.get("outname") or "").strip() else ""
    single = len(files) == 1
    # 수동 문항번호(시작번호) — 있으면 자동 추출보다 우선, 지문마다 1씩 증가
    try:
        q_counter = int((request.form.get("start_no") or "").strip())
        if q_counter < 1:
            q_counter = None
    except (TypeError, ValueError):
        q_counter = None
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or cfg.api_key

    if not files:
        return render_template_string(INDEX_HTML, has_key=cfg.has_api_key, env_banner="")
    if not mock and not key:
        # 키 없고 미리보기도 아님 → 안내
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '샘플 미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, has_key=cfg.has_api_key, env_banner="")

    client = None if mock else ClaudeClient(key, cfg.model)

    # 산출물은 통합 워크북 하나로 통일(단일 유형·빈칸 워크북 포함). 항상 생성.
    def out_name(stem, type_suffix, default_suffix):
        """사용자 지정명(custom) 우선, 없으면 지문명+기본접미사."""
        if custom:
            return custom if single else f"{custom}_{stem}"
        return f"{stem}{default_suffix}"

    results = []
    wb_books = []       # 통합 워크북 파일간 합본용
    wb_packs = []       # 단일 유형 산문 워크시트 파일간 합본용
    wb_bsets = []       # 통합 워크북에 포함되는 빈칸형(맨 뒤) 파일간 합본용
    wb_wpacks = []      # 통합 워크북에 포함되는 영작(가장 마지막) 파일간 합본용
    n_files_ok = 0      # 산출물을 낸 파일 수(파일간 합본 여부 판단용)
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            results.append({"name": f.filename, "ok": False,
                            "error": "지원하지 않는 형식(JPG·PNG·PDF·HWP·HWPX만 가능)"})
            continue
        tmp = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(tmp))
        stem = _safe_name(Path(f.filename).stem)
        warn_note = ""
        try:
            # ── 추출 품질 자가진단 (API 호출 전, 비용 0) ──
            # 텍스트 파일(PDF/HWP)만 사전 점검. 심각하면 API 를 부르지 않고 건너뛴다(비용 절약).
            if not mock and not extract.is_image(tmp):
                try:
                    diag = extract.diagnose_extraction(extract.extract_passage_text(tmp))
                except Exception:
                    diag = {"level": "ok", "ok": True, "messages": []}
                if not diag["ok"]:
                    results.append({"name": f.filename, "ok": False,
                                    "error": "⚠️ " + " ".join(diag["messages"])
                                             + " · AI를 호출하지 않았습니다(비용 절약)."})
                    continue
                if diag["level"] == "warn":
                    warn_note = " ⚠️ " + " ".join(diag["messages"])
            # 한 파일에 여러 지문이 있으면 지문별로 통합 워크북 + 단일 유형 + 빈칸형을 만든다.
            if mock:
                wbs = [pipeline._mock_workbook_for_pdf(cfg, tmp)]
                packs = [pipeline._mock_prose_pack_for_pdf(cfg, tmp)]
                file_bsets = [pipeline._mock_blank_set_for_pdf(cfg, tmp, 1)]
                file_wpacks = [pipeline._mock_writing_pack_for_pdf(cfg, tmp)]
            else:
                wbs, packs, file_bsets, file_wpacks = pipeline.build_workbook_bundle_for_pdf(
                    client, cfg, tmp)
            # 뱃지를 '파일명 · 지문번호'로 통일. 수동 시작번호가 있으면 지문마다 +1(파일 간 누적),
            # 없으면 자동 추출/지문 순서 번호를 그대로 쓰고 파일명만 앞에 붙인다.
            from src.textutil import file_tag
            nxt = pipeline.apply_q_numbers(wbs, packs, file_bsets, file_wpacks,
                                           start=q_counter, tag=file_tag(f.filename))
            if q_counter is not None:
                q_counter = nxt
            base = out_name(stem, '_통합', '_워크북')
            # 유형 순서(통합→어형→어법→어휘→영작→해석→빈칸)로 '한글 포함'·'한글 제외' 2개 PDF
            outs = pipeline.render_workbook_two_versions(
                wbs, packs, OUTPUT_DIR, base, footer_note=cfg.design.footer_note,
                scratch=OUTPUT_DIR, blank_wb=pipeline._build_blank_workbook(file_bsets),
                writing_packs=file_wpacks, source_name=f.filename)
            # 분석 결과(JSON) 저장 — 나중에 '제목만' 바꿔 재렌더링(API 재호출 없이)할 때 쓴다.
            json_name = f"{base}_분석데이터.json"
            try:
                bundle.save_json(
                    bundle.dump_bundle(wbs, packs, file_bsets, file_wpacks, source_name=f.filename),
                    OUTPUT_DIR / json_name)
            except Exception:
                json_name = ""
            wb_books.extend(wbs)
            wb_packs.extend(packs)
            wb_bsets.extend(file_bsets)
            wb_wpacks.extend(file_wpacks)
            for idx, o in enumerate(outs):
                tag = "한글 포함" if o.name.endswith("_한글포함.pdf") else "한글 제외"
                results.append({"name": f"{f.filename} · 통합 워크북 [{tag}] (지문 {len(wbs)}편){warn_note}",
                                "ok": True, "out": o.name,
                                "json": json_name if idx == 0 else ""})
            n_files_ok += 1
        except Exception as e:  # 개별 실패가 전체를 멈추지 않음
            traceback.print_exc()
            results.append({"name": f.filename, "ok": False, "error": _friendly_error(e)})
        finally:
            tmp.unlink(missing_ok=True)

    # 파일이 '2개 이상'일 때만 파일들을 하나로 합친 합본 추가(단일 파일은 이미 지문별로 다 들어감)
    if n_files_ok >= 2 and len(wb_books) >= 2:
        try:
            base = f"{(custom + '_통합합본') if custom else '통합워크북_합본'}"
            outs = pipeline.render_workbook_two_versions(
                wb_books, wb_packs, OUTPUT_DIR, base, footer_note=cfg.design.footer_note,
                scratch=OUTPUT_DIR, blank_wb=pipeline._build_blank_workbook(wb_bsets),
                writing_packs=wb_wpacks)
            for o in outs:
                tag = "한글 포함" if o.name.endswith("_한글포함.pdf") else "한글 제외"
                results.append({"name": f"📚 통합 워크북 합본 [{tag}]", "ok": True, "out": o.name})
        except Exception as e:
            traceback.print_exc()
            results.append({"name": "📚 통합 합본", "ok": False, "error": str(e)})

    n_ok = sum(1 for r in results if r["ok"])
    return render_template_string(RESULT_HTML, results=results,
                                  n_ok=n_ok, n_fail=len(results) - n_ok)


# ---------------------------------------------------------------------------
# 제목만 수정 (분석 JSON 재사용 · API 재호출 없음)
# ---------------------------------------------------------------------------
@app.route("/retitle", methods=["POST"])
def retitle():
    """분석데이터(JSON) 업로드 → 임시 저장 후 제목 편집 폼을 보여준다."""
    up = request.files.get("bundle")
    if not up or not up.filename:
        return render_template_string(RETITLE_HTML, err="JSON 파일을 올려주세요.",
                                      token="", titles=[], outname="")
    try:
        data = json.loads(up.read().decode("utf-8"))
        wbs, packs, bsets, wpacks, source = bundle.load_bundle(data)
        titles = bundle.passage_titles(wbs, packs, wpacks, bsets)
    except Exception as e:
        return render_template_string(
            RETITLE_HTML, err="올바른 ORTICA 분석데이터(JSON)가 아닙니다: " + str(e),
            token="", titles=[], outname="")
    token = uuid.uuid4().hex
    (UPLOAD_DIR / f"{token}.json").write_text(json.dumps(data, ensure_ascii=False),
                                              encoding="utf-8")
    outname = _safe_name(Path(source).stem) if source else ""
    return render_template_string(RETITLE_HTML, err="", token=token, titles=titles,
                                  outname=outname)


@app.route("/retitle_apply", methods=["POST"])
def retitle_apply():
    """편집한 제목을 반영해 다시 렌더링(분석은 저장된 JSON 그대로 재사용)."""
    token = re.sub(r"[^0-9a-f]", "", (request.form.get("token") or ""))[:32]
    tmp = UPLOAD_DIR / f"{token}.json"
    if not token or not tmp.is_file():
        return render_template_string(RETITLE_HTML, err="세션이 만료되었습니다. 다시 올려주세요.",
                                      token="", titles=[], outname="")
    try:
        data = json.loads(tmp.read_text(encoding="utf-8"))
        wbs, packs, bsets, wpacks, source = bundle.load_bundle(data)
        for i in range(len(bundle.passage_titles(wbs, packs, wpacks, bsets))):
            new_t = (request.form.get(f"title_{i}") or "").strip()
            if new_t:
                bundle.set_passage_title(wbs, packs, wpacks, bsets, i, new_t)
        base = _safe_name((request.form.get("outname") or "").strip()) \
            or (_safe_name(Path(source).stem) if source else "통합워크북")
        outs = pipeline.render_workbook_two_versions(
            wbs, packs, OUTPUT_DIR, base, footer_note=cfg.design.footer_note,
            scratch=OUTPUT_DIR, blank_wb=pipeline._build_blank_workbook(bsets),
            writing_packs=wpacks, source_name=source)
        json_name = f"{base}_분석데이터.json"
        bundle.save_json(bundle.dump_bundle(wbs, packs, bsets, wpacks, source_name=source),
                         OUTPUT_DIR / json_name)
    except Exception as e:
        traceback.print_exc()
        return render_template_string(RETITLE_HTML, err="다시 뽑기 실패: " + _friendly_error(e),
                                      token=token, titles=[], outname="")
    finally:
        tmp.unlink(missing_ok=True)

    results = []
    for idx, o in enumerate(outs):
        tag = "한글 포함" if o.name.endswith("_한글포함.pdf") else "한글 제외"
        results.append({"name": f"✏️ 제목 수정본 · 통합 워크북 [{tag}]", "ok": True,
                        "out": o.name, "json": json_name if idx == 0 else ""})
    return render_template_string(RESULT_HTML, results=results, n_ok=len(results), n_fail=0)


def _safe_name(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", stem).strip() or "passage"


def _friendly_error(e: Exception) -> str:
    """API·네트워크 오류를 '무엇을 해야 하는지'까지 담은 한국어 안내로 바꾼다."""
    name = type(e).__name__
    msg = str(e)
    low = (name + " " + msg).lower()
    if "authentication" in low or "invalid x-api-key" in low or "401" in low:
        return "API 키가 올바르지 않습니다. console.anthropic.com 에서 키를 다시 확인해 입력하세요."
    if "permission" in low or "403" in low:
        return "이 API 키로는 접근 권한이 없습니다. 키/결제 상태를 확인하세요."
    if "rate" in low and "limit" in low or "429" in low:
        return "요청이 너무 많습니다(사용량 한도). 잠시 후 다시 시도하거나 파일 수를 줄여 주세요."
    if "credit" in low or "billing" in low or "quota" in low or "insufficient" in low:
        return "API 사용 크레딧이 부족합니다. console.anthropic.com 결제에서 크레딧을 충전하세요."
    if "overloaded" in low or "529" in low:
        return "AI 서버가 일시적으로 혼잡합니다(overloaded). 잠시 후 다시 시도하세요."
    if "connection" in low or "timeout" in low or "network" in low:
        return "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인하고 다시 시도하세요."
    if "검증 실패" in msg:
        return msg + " (지문 형식이 특이하면 발생할 수 있습니다. 다른 파일로도 시도해 보세요.)"
    return msg


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
    # 실행 환경 자가진단 (무엇이 빠졌는지 즉시 표시)
    print("  " + envcheck.format_report(envcheck.check_environment(cfg)).replace("\n", "\n  "))
    print("-" * 56)
    print("  브라우저에서 아래 주소로 접속하세요:")
    print(f"      http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

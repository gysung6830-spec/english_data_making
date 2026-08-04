#!/usr/bin/env python3
"""동형모의고사 자동생성 - 웹앱(브라우저) 버전.

실행:
    python webapp.py
그다음 브라우저에서  http://localhost:5000  접속.

지문 파일을 올리고 → 학교·학년·난이도·파일명을 고르고 → 버튼만 누르면
동형모의고사(문제지+정답해설)가 만들어집니다. API 키가 없으면 '미리보기'로
디자인·배치·검증까지 확인할 수 있습니다.
"""
from __future__ import annotations

import os
import re
import secrets
import traceback
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import (Flask, abort, redirect, render_template_string, request,
                   send_from_directory, session, url_for)

from mockexam.ingest.loader import IMAGE_EXTS
from mockexam.pipeline import generate_mock
from mockexam.render.exam import TYPE_LABEL_KO, render_exam
from mockexam.school import load_schools_index

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
app.secret_key = os.environ.get("APP_SECRET") or secrets.token_hex(16)
APP_PASSWORD = os.environ.get("APP_PASSWORD")

UPLOAD_DIR = ROOT / "web_uploads"
OUTPUT_DIR = ROOT / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
# 생성 모델은 Sonnet 고정(빠르고 우수·합리적 비용). 바꾸려면 MOCK_MODEL 환경변수만.
MODEL = os.environ.get("MOCK_MODEL", "claude-sonnet-5")

ALLOWED = {".pdf", ".txt", ".md", ".hwp", ".hwpx"} | IMAGE_EXTS


def _has_key() -> bool:
    k = os.environ.get("ANTHROPIC_API_KEY")
    return bool(k and "여기에" not in k)


BASE_CSS = """
 :root{--ink:#23272e;--accent:#1d4ed8;--green:#15803d;--muted:#6b7280;--line:#e5e7eb;}
 *{box-sizing:border-box;}
 body{font-family:'Nanum Gothic',system-ui,sans-serif;color:var(--ink);
      background:#f6f7f9;margin:0;padding:24px;line-height:1.55;}
 .wrap{max-width:760px;margin:0 auto;}
 .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:24px;
       box-shadow:0 1px 3px rgba(0,0,0,.05);margin-bottom:18px;}
 h1{font-size:22px;margin:0 0 4px;}
 .sub{color:var(--muted);font-size:13px;margin-bottom:18px;}
 label{font-weight:700;font-size:14px;display:block;margin:14px 0 6px;}
 input[type=text],input[type=password],select{width:100%;padding:10px 12px;
       border:1px solid var(--line);border-radius:8px;font-size:14px;background:#fff;}
 .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
 .drop{border:2px dashed #c7cdd6;border-radius:12px;padding:26px;text-align:center;
       background:#fafbfc;cursor:pointer;transition:.15s;}
 .drop.hl{border-color:var(--accent);background:#eff4ff;}
 .drop p{margin:6px 0;color:var(--muted);font-size:13px;}
 .files{margin-top:10px;font-size:13px;}
 .btn{display:inline-block;background:var(--accent);color:#fff;border:none;border-radius:9px;
      padding:12px 22px;font-size:15px;font-weight:700;cursor:pointer;}
 .btn.gray{background:#374151;}
 .chk{display:flex;align-items:center;gap:8px;font-size:14px;margin-top:12px;font-weight:600;}
 .hint{font-size:12px;color:var(--muted);margin-top:6px;}
 .nav{display:flex;gap:8px;margin-bottom:14px;}
 .nav a{flex:1;text-align:center;padding:11px;border:1px solid var(--line);border-radius:10px;
        background:#fff;color:var(--ink);text-decoration:none;font-weight:700;font-size:14px;}
 .nav a.on{background:var(--accent);color:#fff;border-color:var(--accent);}
 .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px;}
 table{width:100%;border-collapse:collapse;margin-top:6px;font-size:14px;}
 td,th{padding:8px;border-bottom:1px solid var(--line);text-align:left;}
 .ok{color:var(--green);font-weight:700;} .fail{color:#be123c;font-weight:700;}
 a.dl{color:var(--accent);font-weight:700;text-decoration:none;margin-right:12px;}
 .err{background:#fff1f3;border:1px solid #fecdd3;color:#9f1239;padding:10px 12px;
      border-radius:8px;font-size:13px;margin-top:10px;}
 pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;font-size:12px;
     overflow:auto;white-space:pre-wrap;}
 #overlay{position:fixed;inset:0;background:rgba(255,255,255,.85);display:none;
          align-items:center;justify-content:center;flex-direction:column;z-index:10;}
 .spin{width:44px;height:44px;border:5px solid #d1d5db;border-top-color:var(--accent);
       border-radius:50%;animation:sp 1s linear infinite;}
 @keyframes sp{to{transform:rotate(360deg);}}
"""

INDEX_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>동형모의고사 생성기</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=nav>
    <a href="{{ url_for('index') }}" class=on>📝 동형모의고사 생성</a>
    <a href="{{ url_for('learn_page') }}">🎓 학교 시험지 학습</a>
    <a href="{{ url_for('retitle_page') }}">🔤 제목만 수정</a>
  </div>
  <div class=card>
    <h1>📝 동형모의고사 자동생성</h1>
    <div class=sub>지문을 올리고 학교·학년·난이도를 고르면, 그 학교 스타일의 동형모의고사를 만들어 드립니다.</div>
    <form id=f method=post action="{{ url_for('generate') }}" enctype=multipart/form-data>

      <label>① 지문 파일 (PDF·사진·TXT·HWP, 여러 개 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 파일을 끌어다 놓으세요</p>
        <p>PDF · JPG · PNG · TXT · HWP</p>
        <input id=file type=file name=files multiple
               accept=".pdf,.jpg,.jpeg,.png,.txt,.md,.hwp,.hwpx" hidden>
      </div>
      <div class=files id=filelist></div>

      <div class=grid>
        <div>
          <label>② 학교</label>
          <select name=school>
            {% for s in schools %}
            <option value="{{ s.school_id }}" {{ 'selected' if s.school_id=='jinyang_hs' else '' }}>
              {{ s.name }} ({{ '중' if s.level=='middle' else '고' }}){{ ' · 학습됨' if s.learned else ' · 표준골격' }}
            </option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>③ 학년</label>
          <select name=grade>
            <option>1</option><option>2</option><option>3</option>
          </select>
        </div>
      </div>

      <div class=grid>
        <div>
          <label>④ 난이도</label>
          <select name=difficulty>
            <option value="하">하</option>
            <option value="중" selected>중</option>
            <option value="상">상</option>
          </select>
        </div>
        <div>
          <label>⑤ 저장할 파일 이름 <span class=hint>(비우면 자동)</span></label>
          <input type=text name=outname placeholder="예: 1학년_2차_동형A">
        </div>
      </div>

      <label>⑥ 시험지 머리글 <span class=hint>(선택)</span></label>
      <div class=grid>
        <input type=text name=exam_title placeholder="2026학년도 1학기 2차 시험">
        <input type=text name=subject placeholder="공통영어1">
      </div>

      <label>⑦ Anthropic API 키
        <span class=hint>(실제 문항 생성용 · 비우고 아래 '미리보기'를 쓰면 디자인만 확인)</span>
      </label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}"
             {{ 'readonly' if has_key else '' }}>

      <label class=chk><input type=checkbox name=mock value=1 {{ '' if has_key else 'checked' }}>
        미리보기 (API 키 없이 배치·검증·디자인만 확인)</label>

      <div class=row>
        <button class=btn id=go type=submit>동형모의고사 만들기</button>
        <span class=hint>지문이 많으면 몇 분 걸릴 수 있어요.</span>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">생성 중입니다… 잠시만요</p></div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),
       list=document.getElementById('filelist'),f=document.getElementById('f'),ov=document.getElementById('overlay');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{file.files=ev.dataTransfer.files;show();});
 file.onchange=show;
 function show(){list.innerHTML=[...file.files].map(x=>'📄 '+x.name).join('<br>')||'';}
 f.onsubmit=()=>{if(!file.files.length){alert('지문 파일을 먼저 올려주세요.');return false;} ov.style.display='flex';};
</script>
</body></html>
"""

RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>생성 결과</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=card>
    <h1>✅ 동형모의고사 생성 완료</h1>
    <div class=sub>{{ school }} {{ grade }}학년 · 난이도 {{ difficulty }}
      · 선택형 {{ n_choice }} / 서술형 {{ n_essay }} · {{ total }}점
      {{ '· 미리보기(mock)' if mock else '· LLM 생성' }}

    <table>
      <tr><th>산출물</th><th>열기</th></tr>
      {% for f in downloads %}
      <tr><td>💾 {{ f.name }}</td>
        <td><a class=dl href="{{ url_for('view', fname=f.name) }}" target=_blank>미리보기</a>
            <a class=dl href="{{ url_for('download', fname=f.name) }}">다운로드</a></td></tr>
      {% endfor %}
    </table>
    <div class=hint style="margin-top:8px">
      💡 <b>.exam.json</b> 파일은 <b>제목만 수정</b> 탭에 다시 올리면
      API 재분석 없이 제목·과목만 바꿔 PDF를 다시 뽑을 수 있어요. (비용 없음)
    </div>

    {% for w in warnings %}
    <div class=err style="background:#fff8e1;border-color:#ffe08a;color:#8a5a00">⚠ {{ w }}</div>
    {% endfor %}
    {% if failed %}
    <div class=err>⚠ <b>확인 필요</b> — 생성/배정이 안 된 문항: <b>{{ failed }}</b><br>
      해당 문항은 PDF 맨 끝 <b>'검토 문항'</b> 페이지에 정리돼 있습니다. API 키·요금제를
      확인하거나 다시 생성하면 채워집니다.
    </div>
    {% endif %}
    {% if shortage %}
    <div style="background:#eef4ff;border:1px solid #cfe0ff;color:#1e40af;
                padding:10px 12px;border-radius:8px;font-size:13px;margin-bottom:10px">
      ℹ️ {{ shortage }}
    </div>
    {% endif %}

    <label style="margin-top:18px">검증 결과</label>
    <pre>{{ verify }}</pre>

    {% if logs %}
    <label>지문 배정 참고 <span class=hint>(지문 부족으로 스킵/대체된 슬롯)</span></label>
    <pre>{{ logs }}</pre>
    {% endif %}

    {% if not pdf_ready %}
    <div class=err>PDF 변환기(WeasyPrint)가 없어 HTML로 저장했습니다.
      HTML을 브라우저에서 열고 <b>Ctrl+P → PDF로 저장</b>하면 됩니다.</div>
    {% endif %}

    <div class=row><a class="btn gray" href="{{ url_for('index') }}">← 다시 만들기</a></div>
  </div>
</div></body></html>
"""

LEARN_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>학교 시험지 학습</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=nav>
    <a href="{{ url_for('index') }}">📝 동형모의고사 생성</a>
    <a href="{{ url_for('learn_page') }}" class=on>🎓 학교 시험지 학습</a>
    <a href="{{ url_for('retitle_page') }}">🔤 제목만 수정</a>
  </div>
  <div class=card>
    <h1>🎓 학교 시험지 학습</h1>
    <div class=sub>학교가 낸 <b>실제 시험지</b>를 올리면 문항 유형·배점·문항수를 자동으로 학습합니다.
      이후 그 학교를 고르면 <b>그 학교 스타일 그대로</b> 동형이 생성됩니다.</div>
    {% if err %}<div class=err>{{ err }}</div>{% endif %}
    <form method=post enctype=multipart/form-data id=f>
      <label>① 시험지 파일 (PDF·사진, 여러 장 가능)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 시험지를 끌어다 놓으세요</p>
        <p>PDF · JPG · PNG · HWP (문제지 전체)</p>
        <input id=file type=file name=files multiple accept=".pdf,.jpg,.jpeg,.png,.hwp,.hwpx" hidden>
      </div>
      <div class=files id=filelist></div>

      <label>② 학교 <span class=hint>(기존 학교에 누적하거나, 아래에 새 학교를 입력)</span></label>
      <select name=school>
        <option value="">(새 학교 직접 입력 ↓)</option>
        {% for s in schools %}
        <option value="{{ s.school_id }}">{{ s.name }} ({{ '중' if s.level=='middle' else '고' }})
          {{ '· 학습됨' if s.learned else '· 미학습' }}</option>
        {% endfor %}
      </select>
      <div class=grid style="margin-top:10px">
        <input type=text name=new_name placeholder="새 학교 이름 (예: 진양고)">
        <select name=new_level>
          <option value="high">고등학교</option>
          <option value="middle">중학교</option>
        </select>
      </div>

      <div class=grid>
        <div><label>③ 학년</label>
          <select name=grade><option>1</option><option>2</option><option>3</option></select></div>
        <div><label>④ 시험 이름 <span class=hint>(누적 구분용)</span></label>
          <input type=text name=exam_name placeholder="예: 2024_2학기_기말"></div>
      </div>

      <label>⑤ Anthropic API 키 <span class=hint>(학습은 실제 분석이므로 키가 필요합니다)</span></label>
      <input type=password name=api_key placeholder="sk-ant-..."
             value="{{ '설정됨(그대로 사용)' if has_key else '' }}"
             {{ 'readonly' if has_key else '' }}>

      <div class=row>
        <button class=btn type=submit>이 시험지로 학습하기</button>
        <span class=hint>분석에 30초~1분 걸릴 수 있어요.</span>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">시험지 분석 중…</p></div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),
       list=document.getElementById('filelist'),f=document.getElementById('f'),ov=document.getElementById('overlay');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.add('hl');}));
 ['dragleave','drop'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{file.files=ev.dataTransfer.files;show();});
 file.onchange=show;
 function show(){list.innerHTML=[...file.files].map(x=>'📄 '+x.name).join('<br>')||'';}
 f.onsubmit=()=>{if(!file.files.length){alert('시험지 파일을 먼저 올려주세요.');return false;} ov.style.display='flex';};
</script>
</body></html>
"""

LEARN_RESULT_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>학습 완료</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=nav>
    <a href="{{ url_for('index') }}">📝 동형모의고사 생성</a>
    <a href="{{ url_for('learn_page') }}" class=on>🎓 학교 시험지 학습</a>
    <a href="{{ url_for('retitle_page') }}">🔤 제목만 수정</a>
  </div>
  <div class=card>
    <h1>✅ 학습 완료</h1>
    <div class=sub><b>{{ name }}</b> · {{ grade }}학년 · {{ subject }} · {{ total }}점
      · 선다형 {{ n_choice }} / 서술형 {{ n_essay }}</div>
    <div style="background:#eef4ff;border:1px solid #cfe0ff;color:#1e40af;
                padding:10px 12px;border-radius:8px;font-size:13px;margin-bottom:12px">
      ℹ️ 이제 <a href="{{ url_for('index') }}"><b>동형모의고사 생성</b></a>에서
      <b>{{ name }}</b>을(를) 고르면 이 시험지 스타일대로 만들어집니다.
      (누적 학습됨: {{ exams }})
    </div>

    <label>학습된 출제원리</label>
    <table>
      <tr><td style="width:110px"><b>난이도 경향</b></td><td>{{ difficulty }}</td></tr>
      <tr><td><b>어법 출제 축</b></td><td>{{ grammar_focus or '—' }}</td></tr>
      <tr><td><b>발문 문구</b></td><td>{{ n_stems }}개 유형 학습</td></tr>
    </table>
    {% if notes %}
    <label>출제 스타일 특징</label>
    <ul style="font-size:13px;line-height:1.6;margin:4px 0 0;padding-left:18px">
      {% for n in notes %}<li>{{ n }}</li>{% endfor %}
    </ul>
    {% endif %}

    <label style="margin-top:16px">추출된 문항 구조</label>
    <table>
      <tr><th>#</th><th>구분</th><th>유형</th><th>배점</th></tr>
      {% for it in items %}
      <tr><td>{{ it.no }}</td><td>{{ '서술형' if it.section=='essay' else '선다형' }}</td>
          <td>{{ it.type_ko }}</td><td>{{ it.score }}점</td></tr>
      {% endfor %}
    </table>
    <div class=row><a class="btn gray" href="{{ url_for('learn_page') }}">← 다른 시험지 학습</a>
      <a class=btn href="{{ url_for('index') }}">동형모의고사 생성하러 가기 →</a></div>
  </div>
</div></body></html>
"""

RETITLE_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>제목만 수정</title><style>""" + BASE_CSS + """</style></head>
<body><div class=wrap>
  <div class=nav>
    <a href="{{ url_for('index') }}">📝 동형모의고사 생성</a>
    <a href="{{ url_for('learn_page') }}">🎓 학교 시험지 학습</a>
    <a href="{{ url_for('retitle_page') }}" class=on>🔤 제목만 수정</a>
  </div>
  <div class=card>
    <h1>🔤 제목만 수정 (재분석·비용 없음)</h1>
    <div class=sub>이미 생성된 결과의 <b>.exam.json</b> 파일을 올리고 새 제목만 입력하면,
      API 재분석 없이 <b>제목·과목·파일명만 바꿔</b> PDF를 다시 뽑습니다.
      (생성 결과 페이지에서 받은 <b>.exam.json</b>을 그대로 올리세요.)</div>
    {% if err %}<div class=err>{{ err }}</div>{% endif %}
    <form method=post enctype=multipart/form-data id=f>
      <label>① 분석 결과 파일 (.exam.json)</label>
      <div class=drop id=drop>
        <div style="font-size:26px">⬆️</div>
        <p><b>여기를 클릭</b>하거나 .exam.json 파일을 끌어다 놓으세요</p>
        <p>생성 결과에서 받은 <b>*.exam.json</b></p>
        <input id=file type=file name=exam accept=".json" hidden>
      </div>
      <div class=files id=filelist></div>

      <label>② 새 시험지 머리글 <span class=hint>(비우면 기존 값 유지)</span></label>
      <div class=grid>
        <input type=text name=exam_title placeholder="2026학년도 1학기 2차 시험">
        <input type=text name=subject placeholder="공통영어1">
      </div>

      <label>③ 저장할 파일 이름 <span class=hint>(비우면 자동)</span></label>
      <input type=text name=outname placeholder="예: 1학년_2차_동형A_수정본">

      <div class=row>
        <button class=btn type=submit>제목 바꿔 다시 뽑기</button>
        <span class=hint>바로 만들어집니다 (API 호출 없음).</span>
      </div>
    </form>
  </div>
</div>
<div id=overlay><div class=spin></div><p style="margin-top:14px;font-weight:700">다시 뽑는 중…</p></div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),
       list=document.getElementById('filelist'),f=document.getElementById('f'),ov=document.getElementById('overlay');
 drop.onclick=()=>file.click();
 ['dragover','dragenter'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();ev.stopPropagation();drop.classList.add('hl');}));
 ['dragleave','dragend'].forEach(e=>drop.addEventListener(e,ev=>{ev.preventDefault();ev.stopPropagation();drop.classList.remove('hl');}));
 drop.addEventListener('drop',ev=>{
   ev.preventDefault();ev.stopPropagation();drop.classList.remove('hl');
   // 단일 파일 input 은 dataTransfer.files 직접 대입이 무시될 수 있어 .json 만 골라 새로 담는다.
   const picked=[...(ev.dataTransfer&&ev.dataTransfer.files||[])]
       .filter(x=>/\\.json$/i.test(x.name));
   if(!picked.length){alert('.json 파일을 올려주세요.');return;}
   const dt=new DataTransfer();dt.items.add(picked[0]);file.files=dt.files;show();
 });
 file.onchange=show;
 function show(){list.innerHTML=[...file.files].map(x=>'📄 '+x.name).join('<br>')||'';}
 f.onsubmit=()=>{if(!file.files.length){alert('.exam.json 파일을 먼저 올려주세요.');return false;} ov.style.display='flex';};
</script>
</body></html>
"""

LOGIN_HTML = """
<!doctype html><html lang=ko><head><meta charset=utf-8><title>로그인</title>
<style>""" + BASE_CSS + """</style></head><body><div class=wrap>
<div class=card style="max-width:420px;margin:60px auto;">
  <h1>🔒 로그인</h1><div class=sub>비밀번호를 입력하세요.</div>
  {% if err %}<div class=err>{{ err }}</div>{% endif %}
  <form method=post><label>비밀번호</label><input type=password name=password autofocus>
    <div class=row><button class=btn type=submit>들어가기</button></div></form>
</div></div></body></html>
"""


@app.before_request
def _auth_gate():
    if not APP_PASSWORD or request.endpoint in ("login", "static"):
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


def _schools_for_view():
    out = []
    for s in load_schools_index():
        prof = ROOT / "profiles" / s["school_id"] / "profile.json"
        out.append({**s, "learned": prof.exists()})
    return out


@app.route("/")
def index():
    return render_template_string(INDEX_HTML, schools=_schools_for_view(),
                                  has_key=_has_key())


def _safe_name(stem: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣_\- ]", "_", stem).strip() or "mock_form"


def _unique_stem(stem: str) -> str:
    if not (OUTPUT_DIR / f"{stem}.html").exists() and \
       not (OUTPUT_DIR / f"{stem}.pdf").exists():
        return stem
    i = 2
    while (OUTPUT_DIR / f"{stem}_{i}.html").exists() or \
          (OUTPUT_DIR / f"{stem}_{i}.pdf").exists():
        i += 1
    return f"{stem}_{i}"


@app.route("/generate", methods=["POST"])
def generate():
    files = [f for f in request.files.getlist("files") if f and f.filename]
    mock = bool(request.form.get("mock"))
    school = request.form.get("school") or "jinyang_hs"
    grade = int(request.form.get("grade") or 1)
    difficulty = request.form.get("difficulty") or "중"
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or (os.environ.get("ANTHROPIC_API_KEY") if _has_key() else None)

    if not files:
        return render_template_string(INDEX_HTML, schools=_schools_for_view(),
                                      has_key=_has_key())
    if not mock and not key:
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>API 키가 없습니다. 키를 입력하거나 '미리보기'를 체크하세요.</div><form id=f")
        return render_template_string(html, schools=_schools_for_view(), has_key=_has_key())

    # 업로드 저장
    saved: list[Path] = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            continue
        p = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(p))
        saved.append(p)
    if not saved:
        html = INDEX_HTML.replace("<form id=f",
            "<div class=err>지원하는 지문 파일이 없습니다(PDF·JPG·PNG·TXT·HWP).</div><form id=f")
        return render_template_string(html, schools=_schools_for_view(), has_key=_has_key())

    client = None
    if not mock:
        from mockexam.core.llm import get_client
        client = get_client(key, MODEL)

    warnings: list[str] = []
    try:
        # 문항 생성 단계에서 구조·정답 유일성을 자가검증한다(별도 검수 패스 없음).
        res = generate_mock(school, [str(p) for p in saved], difficulty=difficulty,
                            grade=grade, client=client)

        # ── 아래 조건은 '오류'지만 PDF 는 항상 내보낸다. 경고로만 표시. ──
        # 지문을 하나도 못 읽은 경우(스캔/HWP 등) → 자리표시자로 생성됨
        if res.num_passages == 0:
            warnings.append(
                "업로드 파일에서 지문 텍스트를 읽지 못해 '지문 부족' 자리표시자로 "
                "생성했습니다. 텍스트가 선택되는 PDF로 저장하거나(스캔본은 API 키를 "
                "넣으면 비전으로 읽힘), HWP는 'PDF로 저장' 후 다시 올려주세요.")

        # 일부 문항 생성 실패 → 실패 문항은 마지막 '검토 문항' 페이지에 정리됨
        gen_errs = [l for l in res.logs if l.get("note") == "generation_failed"]
        n_q = len(res.exam.questions) or 1
        if not mock and gen_errs:
            uniq = []
            for l in gen_errs:
                msg = l.get("error", "")
                if msg and msg not in uniq:
                    uniq.append(msg)
            detail = " | ".join(uniq[:2]) or "원인 메시지 없음"
            warnings.append(
                f"일부 문항({len(gen_errs)}/{n_q}) 생성 실패 → 자리표시자로 넣었습니다. "
                f"마지막 '검토 문항' 페이지에서 확인 후 다시 생성하세요. 원인: {detail}")

        raw = (request.form.get("outname") or "").strip()
        if raw.lower().endswith(".pdf"):
            raw = raw[:-4]
        stem = _unique_stem(_safe_name(raw) if raw else
                            f"{school}_{grade}학년_동형모의고사")

        info = {}
        if request.form.get("exam_title"):
            info["exam_title"] = request.form["exam_title"].strip()
        if request.form.get("subject"):
            info["subject"] = request.form["subject"].strip()

        out = render_exam(res.exam, OUTPUT_DIR, header_info=info,
                          footer="이 시험문제는 은아T영어연구소의 저작물입니다.",
                          answer_key="end", basename=stem)
    except Exception as e:
        traceback.print_exc()
        html = INDEX_HTML.replace("<form id=f",
            f"<div class=err>생성 중 오류: {e}</div><form id=f")
        return render_template_string(html, schools=_schools_for_view(), has_key=_has_key())
    finally:
        for p in saved:
            p.unlink(missing_ok=True)

    downloads = [{"name": p.name} for k, p in out.items()
                 if k in ("problem_pdf", "problem_html", "exam_json")]
    # PDF → HTML → JSON 순으로 노출
    def _ord(n):
        return 0 if n.endswith(".pdf") else (1 if n.endswith(".html") else 2)
    downloads.sort(key=lambda d: _ord(d["name"]))
    import json
    logs = json.dumps(res.logs, ensure_ascii=False, indent=2) if res.logs else ""
    shortage = next((l.get("msg") for l in res.logs
                     if l.get("note") == "passage_reuse"), "")
    # 생성 실패·지문부족으로 자리표시자가 된 문항 번호(해설지 ⚠와 연동)
    fail_nos = sorted({f"{'서술형 ' if l.get('section')=='essay' else ''}{l.get('no')}번"
                       for l in res.logs
                       if l.get("note") in ("generation_failed", "no_passage",
                                            "skipped_no_passage")})
    failed = ", ".join(fail_nos) if (fail_nos and not mock) else ""
    school_name = next((s["name"] for s in load_schools_index()
                        if s["school_id"] == school), school)
    return render_template_string(
        RESULT_HTML, school=school_name, grade=grade, difficulty=difficulty,
        n_choice=len(res.exam.choice_questions), n_essay=len(res.exam.essay_questions),
        total=res.blueprint.total_score, mock=mock, shortage=shortage,
        failed=failed, warnings=warnings, downloads=downloads,
        verify=res.verify_report.summary(), logs=logs,
        pdf_ready="problem_pdf" in out)


@app.route("/learn", methods=["GET"])
def learn_page():
    return render_template_string(LEARN_HTML, schools=_schools_for_view(),
                                  has_key=_has_key(), err="")


@app.route("/learn", methods=["POST"])
def learn_run():
    from mockexam.learn_exam import learn_exam
    from mockexam.school import find_school

    def _err(msg):
        return render_template_string(LEARN_HTML, schools=_schools_for_view(),
                                      has_key=_has_key(), err=msg)

    files = [f for f in request.files.getlist("files") if f and f.filename]
    if not files:
        return _err("시험지 파일을 올려주세요.")
    form_key = (request.form.get("api_key") or "").strip()
    key = None if "설정됨" in form_key else (form_key or None)
    key = key or (os.environ.get("ANTHROPIC_API_KEY") if _has_key() else None)
    if not key:
        return _err("학습은 실제 분석이 필요합니다. Anthropic API 키를 입력하세요.")

    school_id = (request.form.get("school") or "").strip()
    new_name = (request.form.get("new_name") or "").strip()
    new_level = request.form.get("new_level") or "high"
    grade = int(request.form.get("grade") or 1)
    exam_name = _safe_name(request.form.get("exam_name") or "") or "exam_1"
    new_school = False
    if not school_id:
        if not new_name:
            return _err("기존 학교를 고르거나 새 학교 이름을 입력하세요.")
        school_id = f"sch_{uuid.uuid4().hex[:6]}"
        new_school = True

    saved: list[Path] = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED:
            continue
        p = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
        f.save(str(p))
        saved.append(p)
    if not saved:
        return _err("지원하는 파일이 없습니다(PDF·JPG·PNG).")

    try:
        from mockexam.core.llm import get_client
        client = get_client(key, MODEL)
        prof, bp = learn_exam(school_id, exam_name, [str(p) for p in saved],
                              client, name=new_name, level=new_level,
                              new_school=new_school)
    except Exception as e:
        traceback.print_exc()
        return _err(f"학습 중 오류: {e}")
    finally:
        for p in saved:
            p.unlink(missing_ok=True)

    items = [{"no": it.no, "section": it.section,
              "type_ko": TYPE_LABEL_KO.get(it.type, it.type),
              "score": _fmt(it.score)} for it in bp.items]
    _diff_ko = {"high": "상", "mid": "중", "low": "하"}
    return render_template_string(
        LEARN_RESULT_HTML, name=bp.meta.name, grade=bp.meta.grade,
        subject=bp.meta.subject, total=_fmt(bp.meta.total_score),
        n_choice=len(bp.choice_items), n_essay=len(bp.essay_items),
        exams=", ".join(prof.get("exams_learned", [])), items=items,
        difficulty=_diff_ko.get(prof.get("difficulty_trend"), "중"),
        grammar_focus=", ".join(prof.get("grammar_focus") or []),
        n_stems=len(prof.get("stem_style") or {}),
        notes=prof.get("notes") or [])


@app.route("/retitle", methods=["GET"])
def retitle_page():
    return render_template_string(RETITLE_HTML, err="")


@app.route("/retitle", methods=["POST"])
def retitle_run():
    from mockexam.render.exam_io import load_exam_json

    def _err(msg):
        return render_template_string(RETITLE_HTML, err=msg)

    f = request.files.get("exam")
    if not f or not f.filename:
        return _err(".exam.json 파일을 올려주세요.")
    try:
        exam, info = load_exam_json(f.read())
    except Exception as e:
        traceback.print_exc()
        return _err(f"파일을 읽지 못했습니다(.exam.json 형식이 맞는지 확인하세요): {e}")
    if not exam.questions:
        return _err("문항 데이터가 비어 있습니다. 올바른 .exam.json 인지 확인하세요.")

    # 제목·과목만 새 값으로 덮어쓴다(입력이 없으면 기존 값 유지).
    info = dict(info or {})
    if request.form.get("exam_title"):
        info["exam_title"] = request.form["exam_title"].strip()
    if request.form.get("subject"):
        info["subject"] = request.form["subject"].strip()

    raw = (request.form.get("outname") or "").strip()
    if raw.lower().endswith(".pdf"):
        raw = raw[:-4]
    stem = _unique_stem(_safe_name(raw) if raw else
                        f"{exam.blueprint.meta.school_id}_동형모의고사_수정본")

    try:
        out = render_exam(exam, OUTPUT_DIR, header_info=info,
                          footer="이 시험문제는 은아T영어연구소의 저작물입니다.",
                          answer_key="end", basename=stem)
    except Exception as e:
        traceback.print_exc()
        return _err(f"재출력 중 오류: {e}")

    downloads = [{"name": p.name} for k, p in out.items()
                 if k in ("problem_pdf", "problem_html", "exam_json")]
    def _ord(n):
        return 0 if n.endswith(".pdf") else (1 if n.endswith(".html") else 2)
    downloads.sort(key=lambda d: _ord(d["name"]))
    return render_template_string(
        RESULT_HTML, school=exam.blueprint.meta.name or "—",
        grade=exam.blueprint.meta.grade or "—",
        difficulty="—",
        n_choice=len(exam.choice_questions), n_essay=len(exam.essay_questions),
        total=_fmt(exam.blueprint.meta.total_score or 0), mock=False,
        shortage="", failed="",
        warnings=["제목만 바꿔 다시 출력했습니다(API 재분석 없음). 문항 내용은 그대로입니다."],
        downloads=downloads, verify="제목 수정 재출력 — 문항은 검증 없이 그대로 유지",
        logs="", pdf_ready="problem_pdf" in out)


def _fmt(s: float) -> str:
    return str(int(s)) if float(s).is_integer() else f"{s:g}"


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
    port = int(os.environ.get("PORT", 5000))
    print("=" * 56)
    print("  동형모의고사 생성 웹앱이 실행되었습니다.")
    print(f"  브라우저에서:  http://localhost:{port}")
    print("  (종료하려면 이 창에서 Ctrl+C)")
    print("=" * 56)
    app.run(host="0.0.0.0", port=port, threaded=True)

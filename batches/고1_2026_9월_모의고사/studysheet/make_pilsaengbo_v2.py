# -*- coding: utf-8 -*-
"""올림포스 10-14강 필생보 v2 — 5섹션 구조.
① 원문  ② 어휘리스트  (page)  ③ 해석연습(빈칸)+어법 형광펜  (page)  ④ 어법칩 목록  (page)  ⑤ O/X/△ 학습지.
학생용/강사용 각각 출력."""
import json, os, html, re, sys
from weasyprint import HTML
import fitz
SC="/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/moui2"
_HERE=os.path.dirname(os.path.abspath(__file__))
FONTDIR=(_HERE+"/fonts") if os.path.exists(_HERE+"/fonts/NanumSquareRoundR.ttf") \
    else "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/fonts"
FOOT="© 2026. 오르티카잉. All rights reserved."
TITLE="고1 2026년 9월 모의고사 · 필생보"
FONTFACE=f"""
@font-face{{ font-family:'NanumSquareRound'; font-weight:400; src:url('file://{FONTDIR}/NanumSquareRoundR.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:700; src:url('file://{FONTDIR}/NanumSquareRoundB.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:800; src:url('file://{FONTDIR}/NanumSquareRoundEB.ttf'); }}
"""
order=json.load(open(SC+"/order.json"))
P=[json.load(open(SC+"/passages/"+fn)) for fn in order]
NOTES={}
if os.path.exists(SC+"/answer_notes.json"):
    try: NOTES=json.load(open(SC+"/answer_notes.json"))
    except Exception: NOTES={}
# --- 어법칩 정합성 검증(관계대명사 주격/목적격·생략 오류를 렌더 전에 차단) ---
sys.path.insert(0,_HERE)
try:
    from verify_grammar import check_passages
    _errs,_warns=check_passages(P)
    for w in _warns: print("  ⚠ 어법 경고:",w)
    if _errs:
        for e in _errs: print("  ❌ 어법 오류:",e)
        sys.exit(f"어법칩 정합성 오류 {len(_errs)}건 → 렌더 중단(데이터 수정 필요)")
    print(f"어법 검증 통과(오류 0, 경고 {len(_warns)})")
except ImportError:
    print("※ verify_grammar 미발견 → 어법 검증 건너뜀")
def esc(s): return html.escape(str(s or ""))
_MK=re.compile(r"\[\[(.+?)\]\]")

# ---- ⑥ 글의 구조도: 흐름 단계 표 ----
CIRC="①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
def circ(n): return CIRC[n-1] if 1<=n<=len(CIRC) else f"({n})"
def parse_range(rg):
    out=[]
    for part in re.split(r"[,\s]+", str(rg or "").strip()):
        m=re.match(r"^(\d+)\s*[~\-–]\s*(\d+)$", part)
        if m: out+=list(range(int(m.group(1)), int(m.group(2))+1))
        elif part.isdigit(): out.append(int(part))
    return out
def fmt_range(rg):
    s=re.sub(r"\s*[~–]\s*","-",str(rg or "").strip())
    return (s+"문장") if s else ""
_KW_STOP={
 "the","a","an","of","to","in","on","for","and","or","but","so","as","that","this","these","those",
 "with","by","from","at","is","are","was","were","be","been","being","am","it","its","they","them",
 "their","we","our","us","you","your","he","she","him","his","her","i","my","me","not","no","nor",
 "than","rather","well","given","ton","tons","what","call","calls","called","such","more","most","very",
 "too","also","about","into","onto","over","under","then","thus","here","there","which","who","whom",
 "whose","when","where","why","how","if","because","while","although","though","each","every","some",
 "any","all","both","either","neither","many","much","few","one","two","do","does","did","have","has",
 "had","can","could","will","would","shall","should","may","might","must","up","out","off","down","away",
 "again","just","only","even","still","yet","own","get","got","make","made","let","lot","kind","sort",
}
def _kw_tokens(text):
    """영어 내용어 토큰(기능어·짧은 단어 제외)."""
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", text or "")
            if len(w)>2 and w.lower() not in _KW_STOP]
def kw_map(p):
    """핵심어(영어) 기준: 지문 전체에서 '반복되는 내용어'를 우선(주제 개념), 기능어·연결어구 제외.
    각 문장에서 vocab 후보를 지문 빈도로 점수화해 상위 1~2개만."""
    from collections import Counter
    freq=Counter()
    for s in p["sentences"]: freq.update(_kw_tokens(s.get("english","")))
    m={}
    for s in p["sentences"]:
        cands=[]
        for v in s.get("vocab",[]):
            w=(v.get("word") or "").strip()
            toks=_kw_tokens(w)
            if not toks: continue                 # 순수 기능어·연결어구 → 제외
            score=max(freq.get(t,0) for t in toks) # 지문 내 최다 반복 토큰 점수
            cands.append((score, len(w), w))
        if not cands: continue
        cands.sort(key=lambda x:(-x[0], -x[1]))   # 반복 많은 것 → 긴 것 순
        picks=[w for sc,_,w in cands if sc>=2][:2] # 2회 이상 반복(주제어) 우선
        if not picks: picks=[cands[0][2]]         # 없으면 가장 내용어다운 1개
        m[s["id"]]=picks
    return m

# ---- 어법칩 형광펜(영어 원문) ----
def _bpat(e):
    l=r"(?<![A-Za-z])" if e[:1].isalpha() else ""
    r=r"(?![A-Za-z])" if e[-1:].isalpha() else ""
    return l+re.escape(e)+r
def _span_is_antecedent(g, e):
    """생략형 관계사처럼 표지 span 이 곧 선행사 명사인 경우 → 보라 형광펜에서 제외(초록 선행사로만)."""
    a=(g.get("antecedent") or "").strip().lower()
    return bool(a) and e.lower() in a
def _ante_anchor(g, raw):
    """관계사 칩이면 선행사 뒤 위치에서 표지를 찾도록 시작 위치 반환(위치 모호성 방지)."""
    a=(g.get("antecedent") or "").strip()
    if not a: return 0
    m=re.search(_bpat(a), raw, re.IGNORECASE)
    return m.end() if m else 0
def _hl_marks(s):
    """어법칩 spans → 형광펜 구간 목록(겹침 없음, 위치 오름차순).
    칩 안에서는 span을 왼→오 순차로 찾고(상관어구 both~and 등 순서 보존),
    이미 칠해진 구간은 건너뛰어(occupied) 칩끼리 같은 단어를 뺏는 오류를 코드로 차단."""
    raw=s.get("english","") or ""
    occupied=[False]*len(raw)
    marks=[]
    def free(st,en): return not any(occupied[st:en])
    def claim(st,en):
        for k in range(st,en): occupied[k]=True
        marks.append((st,en))
    def find_free(e, start):
        while True:
            m=re.search(_bpat(e), raw[start:], re.IGNORECASE)
            if not m: return None
            st,en=start+m.start(), start+m.end()
            if free(st,en): return (st,en)
            start=st+1
    for g in s.get("grammar",[]):
        pos=_ante_anchor(g, raw)   # 관계사는 선행사 뒤에서 표지를 찾아 위치 모호성 제거
        for sp in (g.get("spans") or []):
            e=str(sp).strip()
            if not e: continue
            if _span_is_antecedent(g, e): continue  # 생략형 표지=선행사 → 보라 제외
            hit=find_free(e, pos)          # 선행사/앞 span 뒤에서(순서 보존) 빈 구간
            if hit is None: hit=find_free(e, 0)  # 없으면 문장 전체에서 빈 구간
            if hit is None: continue
            claim(*hit); pos=hit[1]
    marks.sort()
    return marks
def _render_en(raw, marks, slashes):
    """raw를 형광펜(marks) + 청크 슬래시(slashes 오프셋)로 렌더. marks는 겹침 없음."""
    marks=sorted(marks)
    # 슬래시가 형광펜 구간 내부에 걸리면 그 구간 끝으로 밀기
    adj=[]
    for off in sorted(set(slashes)):
        for st,en in marks:
            if st<off<en: off=en; break
        if 0<off<len(raw): adj.append(off)
    adj=sorted(set(adj))
    def emit(a,b):
        out=[]; i=a
        for off in adj:
            if a<off<b:
                out.append(esc(raw[i:off])); out.append(' <span class="sl">/</span> '); i=off
        out.append(esc(raw[i:b])); return "".join(out)
    out=[]; i=0
    for st,en in marks:
        out.append(emit(i,st)); out.append('<mark class="hl">'+esc(raw[st:en])+'</mark>'); i=en
    out.append(emit(i,len(raw)))
    return "".join(out)
def _chunk_bounds(s, raw):
    """청크 사이(en 기준) 슬래시를 넣을 오프셋 목록."""
    ends=[]; pos=0
    for c in s.get("chunks",[]):
        t=_MK.sub(r"\1", c.get("en","") or "").strip()
        if not t: continue
        m=re.search(re.escape(t), raw[pos:])
        if not m:  # 공백 차이 흡수
            t2=re.sub(r"\s+", r"\\s+", re.escape(re.sub(r"\s+"," ",t)))
            m=re.search(t2, raw[pos:])
            if not m: continue
        pos=pos+m.end(); ends.append(pos)
    return ends[:-1]  # 마지막 청크 뒤에는 슬래시 없음
def hl_en(s):
    """어법칩 형광펜만(슬래시 없음) — ⑤ 어법칩용."""
    raw=s.get("english","") or ""
    return _render_en(raw, _hl_marks(s), [])
def en_practice(s, teacher):
    """③ 해석연습 영어: 강사용은 청크 / 끊어읽기(정답), 학생용은 슬래시 없음(끊어읽기=학생 몫). 형광펜은 공통."""
    raw=s.get("english","") or ""
    slashes=_chunk_bounds(s, raw) if teacher else []
    return _render_en(raw, _hl_marks(s), slashes)

def _grammar_marks(s):
    """어법칩 spans(보라 hl) + 관계사 선행사(초록 ha)를 겹치지 않게 표시."""
    raw=s.get("english","") or ""
    occupied=[False]*len(raw); marks=[]
    def free(a,b): return not any(occupied[a:b])
    def claim(a,b,cls):
        for k in range(a,b): occupied[k]=True
        marks.append((a,b,cls))
    def find_free(e,start):
        while True:
            m=re.search(_bpat(e), raw[start:], re.IGNORECASE)
            if not m: return None
            a,b=start+m.start(), start+m.end()
            if free(a,b): return (a,b)
            start=a+1
    for g in s.get("grammar",[]):        # 1) 어법 표지
        pos=_ante_anchor(g, raw)         # 관계사는 선행사 뒤에서 표지 탐색
        for sp in (g.get("spans") or []):
            e=str(sp).strip()
            if not e: continue
            if _span_is_antecedent(g, e): continue  # 생략형 표지=선행사 → 초록으로만
            hit=find_free(e,pos)
            if hit is None: hit=find_free(e,0)
            if hit is None: continue
            claim(hit[0],hit[1],"hl"); pos=hit[1]
    for g in s.get("grammar",[]):        # 2) 관계사 선행사(꾸밈 대상)
        a=(g.get("antecedent") or "").strip()
        if not a: continue
        hit=find_free(a,0)
        if hit: claim(hit[0],hit[1],"ha")
    marks.sort()
    return marks
def hl_en_gram(s):
    """④ 어법칩 영어: 어법 표지(보라) + 선행사(초록) 형광펜."""
    raw=s.get("english","") or ""
    out=[]; i=0
    for a,b,cls in _grammar_marks(s):
        out.append(esc(raw[i:a])); out.append(f'<mark class="{cls}">'+esc(raw[a:b])+'</mark>'); i=b
    out.append(esc(raw[i:])); return "".join(out)

# ---- ④ 직독직해 빈칸(핵심 부분만) ----
def _blank(m):
    inner=re.sub(r'&[a-zA-Z#0-9]+;','x',m.group(1))
    w=min(240,max(30,round(len(inner)*13)+10))  # 정답 글자 수에 비례(한글 1자≈13px)
    return f'<span class="fill" style="min-width:{w}px"></span>'
def ko_line(s, teacher):
    parts=[]
    for c in s.get("chunks",[]):
        ko=c.get("ko","") or ""
        seg=_MK.sub(r'<b class="key">\1</b>', esc(ko)) if teacher else _MK.sub(_blank, esc(ko))
        parts.append(seg)
    return ' <span class="sl">/</span> '.join(parts)

def vcls(v): return "o" if v=="O" else ("t" if v=="△" else "x")

CSS=("""
__FONTS__
@page{ size:A4; margin:13mm 12mm 13mm 12mm;
  @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#22262b; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--green-bg:#e7f0ea;--green-soft:#eef5f0;
  --indigo:#575495;--indigo-bg:#ecebf4;--amber:#a9781f;--red:#a83c2c;--line:#d7ddd6;--sub:#5c636b;}
.psg{break-before:page;} .psg:first-of-type{break-before:auto;}
/* 목차1·2·3: 일반 블록 흐름(위정렬). 한 페이지 보장은 지문별 shrink-to-fit(scale)이 담당.
   flex min-height 채움은 WeasyPrint 분할 오류로 과축소·큰 여백을 유발해 폐기. */
.p1{--ovsc:1;}
.p1 .sec + .sec{margin-top:calc(9px*var(--ovsc));}
/* 목차 1·2·3(원문·어휘·구조도) 한 페이지 보장: 지문별 --ovsc 로 폰트/여백 축소(shrink-to-fit) */
.p1 .sec-t{font-size:calc(11pt*var(--ovsc));}
.p1 .sec-d{font-size:calc(8pt*var(--ovsc));}
.p1 .p-ti{font-size:calc(11pt*var(--ovsc));}
.p1 .panel{padding:calc(7px*var(--ovsc)) calc(11px*var(--ovsc));}
.p1 .orig{font-size:calc(9.8pt*var(--ovsc));}
.p1 .voc{font-size:calc(9.1pt*var(--ovsc));}
.p1 .flow td{font-size:calc(8.8pt*var(--ovsc)); padding:calc(4px*var(--ovsc)) calc(6px*var(--ovsc));}
.p1 .flow .hd{font-size:calc(8.4pt*var(--ovsc));}
.p1 .flow .kwrow{font-size:calc(8.4pt*var(--ovsc));}
.p1 .flow .eg{font-size:calc(7.9pt*var(--ovsc));}
.p1 .flow .stg .rg{font-size:calc(8pt*var(--ovsc));}
.p-h{display:flex; align-items:baseline; gap:8px; border-bottom:2.5px solid var(--green); padding-bottom:4px; margin-bottom:6px;}
.p-no{background:var(--green); color:#fff; font-weight:800; font-size:8.6pt; padding:1px 9px; border-radius:20px; white-space:nowrap;}
.p-ti{font-size:11pt; font-weight:800; color:var(--green-d); line-height:1.35;}
.p-src{margin-left:auto; font-size:7.8pt; color:var(--sub); white-space:nowrap;}
.sec{break-inside:auto;}
.sec.brk{break-before:page;}
.sec-h{display:flex; align-items:center; gap:7px; margin:2px 0 6px;}
.sec-n{background:var(--green-d); color:#fff; font-weight:800; font-size:8.6pt; width:20px; height:20px; line-height:20px; text-align:center; border-radius:50%;}
.sec-t{font-size:11pt; font-weight:800; color:var(--green-d);} .sec-d{font-size:8pt; color:var(--sub);}
.panel{border:1px solid var(--line); border-radius:9px; padding:7px 11px;}
/* ① 원문 */
.orig{font-size:9.8pt; line-height:1.55; color:#1c2024;}
.orig .sn{font-size:6.8pt; font-weight:800; color:var(--green); vertical-align:0.5em; margin:0 2px 0 1px;}
/* ② 어휘 */
.voc{columns:2; column-gap:22px; font-size:9.1pt; line-height:1.5;}
.voc .w{font-weight:800; color:var(--green-d);} .voc .m{color:#3a4250;}
.voc .row{break-inside:avoid;}
/* ③ 해석연습 */
.s{padding:5px 0 6px; border-bottom:1px dotted #e6ebe8; break-inside:avoid;}
.s:last-child{border-bottom:none;}
.en{font-size:9.7pt; line-height:1.55;}
.en .n{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.ko{margin:4px 0 0 21px; font-size:9.2pt; color:#3a4250; line-height:1.7;}
.ko::before{content:"↳ "; color:var(--green); font-weight:800;}
.sl{color:#b9c2ba; font-weight:700; padding:0 2px;}
.fill{display:inline-block; min-width:34px; border-bottom:1.4px solid var(--green); vertical-align:-1px;}
.key{color:var(--indigo); font-weight:800; border-bottom:1.4px solid var(--indigo);}
mark.hl{background:#d8d5f0; padding:0 1px; border-radius:2px; color:inherit;}
/* ④ 어법칩 */
.gl{padding:4px 0; border-bottom:1px dotted #e6ebe8; break-inside:avoid; font-size:9.2pt; line-height:1.55;}
.gl:last-child{border-bottom:none;}
.gl .n{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.chip{display:inline-block; background:var(--indigo-bg); color:var(--indigo); font-weight:800; font-size:8pt; padding:0 7px; border-radius:999px; margin:0 3px 2px 0;}
.gnote{color:#3a4250; font-size:8.6pt;}
mark.ha{background:#dcefe2; padding:0 1px; border-radius:2px; color:inherit; box-shadow:inset 0 -2px 0 #7fae90;}
.rel,.nc{margin:2px 0 0 10px; font-size:8.6pt; line-height:1.55; color:#3a4250;}
.rel b,.nc b{color:var(--indigo); font-weight:800;}
.rel .arr,.nc .arr{color:var(--sub); font-weight:800; margin:0 4px;}
.rel .ante{background:#dcefe2; color:var(--green-d); font-weight:800; border-radius:3px; padding:0 5px; box-shadow:inset 0 -2px 0 #7fae90;}
/* ⑤ ox */
.k-o{color:var(--green-d);} .k-x{color:var(--red);} .k-t{color:var(--amber);}
.sen{margin:7px 0 2px; padding:3px 0 3px 8px; border-left:3px solid var(--green-bg); font-size:9.5pt; line-height:1.5;}
.sen .sn2{display:inline-block; min-width:15px; height:15px; line-height:15px; text-align:center; background:var(--green); color:#fff; font-weight:700; font-size:7.2pt; border-radius:5px; margin-right:6px; vertical-align:1.5px;}
.grp{margin-left:8px;}
.ox{padding:4px 0; border-bottom:1px dotted #eef1ee; break-inside:avoid;}
.ox:last-child{border-bottom:none;}
.stx{font-size:9.3pt; line-height:1.5;} .stx::before{content:"·"; color:var(--sub); font-weight:800; margin-right:6px;} .stx .en2{color:#2b2f6b; font-style:italic;}
.pick{margin:3px 0 0 12px; font-size:8.8pt; color:var(--sub);}
.pick .lab{font-weight:700; color:var(--green-d); margin-right:6px;}
.pick b{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border:1.4px solid #c7cec8; border-radius:50%; margin-right:4px; font-weight:800;}
.pick .fixline{display:inline-block; border-bottom:1px solid #c7cec8; min-width:230px; margin-left:8px; vertical-align:-2px;}
.vd{display:inline-block; width:19px; height:19px; line-height:19px; text-align:center; border-radius:50%; font-weight:800; color:#fff; margin-left:6px;}
.vd.o{background:var(--green);} .vd.x{background:var(--red);} .vd.t{background:var(--amber);}
.kill{color:var(--red); font-weight:800; font-size:7.6pt; margin-left:5px;}
.why{margin:3px 0 0 12px; font-size:8.6pt; color:#3a4250; line-height:1.5;}
.why .cue{background:var(--green-soft); border-radius:3px; padding:0 3px; color:var(--green-d);} .why .typ{color:var(--indigo); font-weight:700; font-size:7.8pt;}
/* ⑥ 글의 구조도 */
table.flow{width:100%; border-collapse:collapse;}
.flow td{border:1px solid var(--line); padding:4px 6px; font-size:8.8pt; vertical-align:top;}
.flow .hd{background:var(--green-bg); color:var(--green-d); font-weight:800; font-size:8.4pt; text-align:center;}
.flow .stg{background:var(--green-soft); font-weight:700; color:var(--green-d); white-space:nowrap; width:78px; text-align:center;}
.flow .stg .rg{display:block; color:var(--sub); font-size:8pt; font-weight:400;}
.flow .kwc{width:31%; background:#fbfcfb;}
.flow .kwrow{display:block; line-height:1.55; font-size:8.4pt;}
.flow .snum{color:var(--green); font-weight:800; margin-right:3px;}
.flow .kw-en{color:var(--indigo); font-weight:700;}
.flow .sumblank{height:24px;}
.flow .note{font-weight:600; line-height:1.55; color:var(--indigo);}
.flow .eg{margin-top:3px; font-size:7.9pt; color:var(--amber); line-height:1.45;}
""").replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)

def sec_head(n,t,d=""):
    return f'<div class="sec-h"><span class="sec-n">{n}</span><span class="sec-t">{t}</span><span class="sec-d">{d}</span></div>'

def phead(p):
    no=esc(p["item_no"].strip()); ti=esc(p["overview"]["theme_ko"])
    return f'<div class="p-h"><span class="p-no">{no}</span><span class="p-ti">{ti}</span><span class="p-src">고1 2026 9월 모의고사</span></div>'

def _first_pos(raw, spans):
    best=None
    for sp in (spans or []):
        e=str(sp).strip()
        if not e: continue
        m=re.search(_bpat(e), raw, re.IGNORECASE)
        if m: best=m.start() if best is None else min(best, m.start())
    return best
def ordered_grammar(s):
    """어법칩을 '문장에 나온 순서'대로 정렬(첫 span 위치 기준). 위치를 못 찾으면 원래 순서로 뒤에."""
    raw=s.get("english","") or ""
    items=list(enumerate(s.get("grammar",[])))
    def key(ig):
        idx,g=ig; p=_first_pos(raw, g.get("spans"))
        return (0,p,idx) if p is not None else (1,0,idx)
    return [g for _,g in sorted(items, key=key)]

# ---- 섹션별 렌더(복수지문은 섹션 묶음 단위로 지문1→지문2→… 반복) ----
def render_overview(p, teacher, scale=1.0):
    """목차 1 원문 · 2 어휘 · 3 글의 구조도 — 항상 한 페이지(shrink-to-fit: scale 로 폰트·여백 축소)."""
    ov=p["overview"]; no=esc(p["item_no"].strip()); sents=p["sentences"]
    st=f' style="--ovsc:{scale:.3f}"' if scale and scale<0.999 else ''
    h=[f'<div class="psg"><div class="p1"{st}>'+phead(p)]
    h.append('<div class="sec">'+sec_head(1,"원문"))
    body=" ".join(f'<span class="sn">{s["id"]}</span>{esc(s["english"])}' for s in sents)
    h.append(f'<div class="panel orig">{body}</div></div>')
    h.append('<div class="sec">'+sec_head(2,"어휘 리스트"))
    seen=set(); rows=[]
    for s in sents:
        for v in s.get("vocab",[]):
            w=v.get("word","").strip()
            if not w or w.lower() in seen: continue
            seen.add(w.lower()); rows.append(f'<div class="row"><span class="w">{esc(w)}</span> <span class="m">{esc(v.get("meaning",""))}</span></div>')
    h.append(f'<div class="panel voc">{"".join(rows)}</div></div>')
    h.append('<div class="sec">'+sec_head(3,"글의 구조도 파악","핵심어(영어)를 단서로 각 단계 내용을 기호로 정리(→ ⇒ ↔ = + ↑↓)"))
    km=kw_map(p); notes=NOTES.get(no) or NOTES.get(p["item_no"]) or []
    h.append('<div class="panel"><table class="flow"><tr>'
             '<td class="hd stg">단계 · 문장</td><td class="hd kwc">핵심어(영어)</td><td class="hd">내용 정리(기호 활용)</td></tr>')
    for i,b in enumerate(ov["flow_blocks"]):
        kws=[]
        for sid in parse_range(b["sentence_range"]):
            if sid in km:
                kws.append(f'<span class="kwrow"><span class="snum">{circ(sid)}</span><span class="kw-en">{esc(" · ".join(km[sid]))}</span></span>')
        kwc="".join(kws) or '<span style="color:var(--sub);font-size:8pt;">—</span>'
        if teacher:
            note=notes[i] if i < len(notes) else re.sub(r"\[\[(.+?)\]\]", r"\1", b["summary"])
            eg=(b.get("easy_example") or "").strip()
            egh=f'<div class="eg">💡 쉬운 예 · {esc(eg)}</div>' if eg else ''
            cell=f'<span class="note">{esc(note)}</span>{egh}'
        else:
            cell='<div class="sumblank"></div>'
        h.append(f'<tr><td class="stg">{esc(b["stage"])}<span class="rg">{fmt_range(b["sentence_range"])}</span></td><td class="kwc">{kwc}</td><td>{cell}</td></tr>')
    h.append('</table></div></div>')
    h.append('</div></div>')  # p1, psg
    return "".join(h)

def render_trans(p, teacher):
    """목차 3 해석 연습 — 영어 청크 / 끊어읽기 + 어법 형광펜, 한글 핵심 빈칸."""
    _desc=("영어에 / 끊어읽기 표시(정답) · 어법칩 형광펜 · 한글은 오역 위험 핵심 어구" if teacher
           else "영어에 직접 / 끊어읽기 표시하며 해석 · 한글 빈칸(오역 위험 핵심) 채우기")
    h=['<div class="psg">'+phead(p)+'<div class="sec">'+sec_head(4,"해석 연습",_desc)+'<div class="panel">']
    for s in p["sentences"]:
        h.append(f'<div class="s"><div class="en"><span class="n">{s["id"]}</span>{en_practice(s, teacher)}</div><div class="ko">{ko_line(s, teacher)}</div></div>')
    h.append('</div></div></div>')
    return "".join(h)

def render_grammar(p, teacher):
    """목차 4 어법칩 — 문장에 나온 순서대로. 관계사는 선행사(꾸밈 대상), 명사절 접속사는 역할 표시."""
    h=['<div class="psg">'+phead(p)+'<div class="sec">'+sec_head(5,"어법칩","문장 순서 · 형광펜=어법 표지 · 초록=관계사가 꾸미는 선행사 · 명사절 접속사는 역할 표시")+'<div class="panel">']
    for s in p["sentences"]:
        chips=ordered_grammar(s)
        if not chips: continue
        h.append(f'<div class="sen"><span class="sn2">{s["id"]}</span>{hl_en_gram(s)}</div><div class="grp">')
        inner=[]
        for g in chips:
            inner.append(f'<span class="chip">{esc(g.get("tag",""))}</span>')
            if teacher and g.get("note"): inner.append(f'<span class="gnote">{esc(g["note"])}</span> ')
        h.append(f'<div class="gl">{"".join(inner)}</div>')
        # 관계사 → 선행사 / 명사절 접속사 → 역할
        for g in chips:
            tag=esc(g.get("tag",""))
            ante=(g.get("antecedent") or "").strip()
            role=(g.get("role") or "").strip()
            if ante:
                h.append(f'<div class="rel">↳ <b>{tag}</b> <span class="arr">→ 꾸밈</span> <span class="ante">{esc(ante)}</span></div>')
            elif role:
                h.append(f'<div class="nc">↳ <b>{tag}</b> <span class="arr">▷ 명사절</span> {esc(role)}</div>')
        h.append('</div>')
    h.append('</div></div></div>')
    return "".join(h)

def render_ox(p, teacher):
    """목차 5 O/X/△ 내용 판단."""
    h=['<div class="psg">'+phead(p)+'<div class="sec">'+sec_head(6,"O / X / △ 내용 판단","맞으면 O·틀리면 X·결론만 맞으면 △, X·△는 근거 고치기")+'<div class="panel">']
    for s in p["sentences"]:
        ms=s.get("misreads",[])
        if not ms: continue
        h.append(f'<div class="sen"><span class="sn2">{s["id"]}</span>{esc(s["english"])}</div><div class="grp">')
        for m in ms:
            v=m.get("verdict","X"); stmt=esc(m.get("statement",""))
            if m.get("english"): stmt=f'<span class="en2">{stmt}</span>'
            if teacher:
                kill='<span class="kill">🔥킬러</span>' if m.get("killer") else ''
                h.append(f'<div class="ox"><div class="stx">{stmt}<span class="vd {vcls(v)}">{v}</span>{kill}</div>')
                if v!="O" and (m.get("why") or m.get("anchor")):
                    an=f'<span class="cue">본문: {esc(m["anchor"])}</span> — ' if m.get("anchor") else ''
                    typ=f' <span class="typ">[{esc(m.get("trap_type",""))}]</span>' if m.get("trap_type") else ''
                    h.append(f'<div class="why">→ 바르게: {an}{esc(m.get("why",""))}{typ}</div>')
                h.append('</div>')
            else:
                h.append(f'<div class="ox"><div class="stx">{stmt}</div>'
                         '<div class="pick"><span class="lab">내 판단</span><b class="k-o">O</b><b class="k-x">X</b><b class="k-t">△</b><span class="fixline"></span></div></div>')
        h.append('</div>')
    h.append('</div></div></div>')
    return "".join(h)

import tempfile
def _overview_pages(p, teacher, scale):
    """지문 하나의 목차1·2·3(overview)만 렌더해서 페이지 수 측정."""
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{render_overview(p, teacher, scale)}</body></html>'
    fd,tmp=tempfile.mkstemp(suffix=".pdf"); os.close(fd)
    try:
        HTML(string=doc).write_pdf(tmp)
        d=fitz.open(tmp); n=d.page_count; d.close()
    finally:
        try: os.remove(tmp)
        except OSError: pass
    return n
_SCALES=[1.0,0.95,0.90,0.86,0.82,0.78,0.74,0.70,0.66,0.62,0.58,0.54,0.50,0.46,0.42,0.38]
def _fit_scale(p, teacher):
    """목차1·2·3 이 '한 페이지'에 들어오는 가장 큰 scale 을 찾는다(shrink-to-fit)."""
    for sc in _SCALES:
        if _overview_pages(p, teacher, sc)<=1:
            return sc
    return _SCALES[-1]

def build(teacher, out):
    scales={}
    for p in P:
        sc=_fit_scale(p, teacher); scales[p["item_no"]]=sc
        if sc<1.0: print(f"  · {p['item_no'].strip()} overview scale={sc}")
    body=[]
    for p in P: body.append(render_overview(p, teacher, scales[p["item_no"]]))  # 목차 1·2·3 (지문별 1페이지 보장)
    for p in P: body.append(render_trans(p, teacher))       # 목차 4 해석연습
    for p in P: body.append(render_grammar(p, teacher))     # 목차 5 어법칩
    for p in P: body.append(render_ox(p, teacher))          # 목차 6 O/X/△
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); n=d.page_count; d.close(); return n

for teacher,suf in [(False,"학생용"),(True,"강사용")]:
    out=f"{SC}/고1_2026_9월_필생보v2_{suf}.pdf"
    print(f"{suf}: {build(teacher,out)}p")
print("PILSAENGBO v2 OK")

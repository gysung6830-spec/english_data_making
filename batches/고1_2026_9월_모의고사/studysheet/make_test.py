# -*- coding: utf-8 -*-
"""고1 2026 9월 — 배열영작 + 순서배열 시험지(학생용/정답).

Part 1 배열영작 : 각 지문 최고난도 문장을 우리말로 주고, 영어 단어를 섞어 제시 → 순서 배열해 영작.
Part 2 순서배열 : 주어진 문장 뒤에 (A)(B)(C) 덩어리를 섞어 제시 → 올바른 글 순서 배열.

정답은 검증된 원문(최고난도 문장·지문 문장 순서)에서 기계적으로 생성 → 항상 정확.
학생용/정답 두 파일 출력."""
import json, os, html, re, random
from weasyprint import HTML
import fitz
SC=os.path.dirname(os.path.abspath(__file__))
FONTDIR=SC+"/fonts"
FOOT="© 2026. 오르티카잉. All rights reserved."
FONTFACE=f"""
@font-face{{ font-family:'NanumSquareRound'; font-weight:400; src:url('file://{FONTDIR}/NanumSquareRoundR.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:700; src:url('file://{FONTDIR}/NanumSquareRoundB.ttf'); }}
@font-face{{ font-family:'NanumSquareRound'; font-weight:800; src:url('file://{FONTDIR}/NanumSquareRoundEB.ttf'); }}
"""
order=json.load(open(SC+"/order.json"))
PDIR=(SC+"/passages") if os.path.isdir(SC+"/passages") else os.path.normpath(SC+"/../passages")
P=[json.load(open(PDIR+"/"+fn)) for fn in order]
def esc(s): return html.escape(str(s or ""))
def sent_of(p, sid):
    for s in p["sentences"]:
        if s["id"]==sid: return s
    return None

# ---------- Part 1: 배열영작 ----------
def scramble_words(sentence, seed):
    """문장을 단어로 쪼개 섞음. 끝 마침표는 제거(끝 힌트 방지)."""
    s=sentence.strip()
    s=re.sub(r'[.]\s*$','',s)          # 문장 끝 마침표만 제거
    toks=[t for t in s.split() if t]
    order=list(range(len(toks)))
    rnd=random.Random(seed)
    for _ in range(20):
        rnd.shuffle(order)
        if order!=list(range(len(toks))) or len(toks)<2: break
    return [toks[i] for i in order], toks  # (섞인 것, 원래 순서)

# ---------- Part 2: 순서배열 ----------
def split3(lst):
    n=len(lst); sizes=[n//3+(1 if i<n%3 else 0) for i in range(3)]
    out=[]; i=0
    for sz in sizes: out.append(lst[i:i+sz]); i+=sz
    return out

def order_problem(p, seed):
    ss=[s["english"].strip() for s in p["sentences"]]
    intro=ss[0]; rest=ss[1:]
    blocks=split3(rest)                       # 원래 순서 c0,c1,c2
    perm=[0,1,2]; rnd=random.Random(seed)
    for _ in range(20):
        rnd.shuffle(perm)
        if perm!=[0,1,2]: break
    shown=[blocks[perm[0]],blocks[perm[1]],blocks[perm[2]]]   # A,B,C = 제시 순서
    labels="ABC"
    # 정답: 원래 순서(c0,c1,c2)를 라벨로
    ans=[labels[perm.index(oi)] for oi in range(3)]
    return intro, shown, "-".join(f"({x})" for x in ans)

# ---------- CSS ----------
def css(teacher):
    return ("""
__FONTS__
@page{ size:A4; margin:15mm 14mm; @bottom-center{ content:"__FOOT__"; font-size:7.5pt; color:#9aa29a; }
       @bottom-right{ content:"__TAG__"; font-size:7.5pt; color:#b06; } }
*{box-sizing:border-box;}
body{font-family:'NanumSquareRound',"Malgun Gothic",sans-serif; color:#23272c; font-size:10pt; margin:0;}
:root{--green:#2c6444;--green-d:#1f4d33;--indigo:#4b4a8f;--rose:#b0434f;--line:#d7ddd6;--sub:#5c636b;--paper:#faf9f6;--ans:#c0392b;}
.doc-h{font-size:14pt;font-weight:800;color:var(--green-d);border-bottom:2.5px solid var(--green);padding-bottom:5px;margin-bottom:3px;}
.doc-d{font-size:8.6pt;color:var(--sub);margin-bottom:6px;}
.part{font-size:11.5pt;font-weight:800;color:#fff;background:var(--green);border-radius:6px;padding:4px 12px;margin:14px 0 4px;}
.guide{font-size:8.8pt;color:var(--sub);margin:0 0 8px 2px;}
.q{border:1px solid var(--line);border-radius:9px;padding:9px 12px 10px;margin-bottom:9px;break-inside:avoid;}
.qh{display:flex;align-items:baseline;gap:8px;margin-bottom:6px;}
.qno{background:var(--green);color:#fff;font-weight:800;font-size:8.4pt;padding:1px 8px;border-radius:20px;white-space:nowrap;}
.qti{font-size:9.4pt;font-weight:700;color:var(--green-d);}
.qtag{margin-left:auto;font-size:7.8pt;color:var(--sub);}
.ko{font-size:9.8pt;line-height:1.55;color:#222;background:#f2f6f2;border-radius:6px;padding:6px 10px;margin-bottom:7px;}
.ko b{color:var(--green-d);}
.bank{display:flex;flex-wrap:wrap;gap:5px 6px;padding:7px 9px;border:1px dashed #b9c3bb;border-radius:7px;background:var(--paper);}
.chip{display:inline-block;font-size:9.3pt;background:#fff;border:1px solid #d3dbd3;border-radius:6px;padding:2px 8px;color:#2b3036;}
.wr{margin-top:8px;border-bottom:1.4px solid #c9c7be;height:15px;}
.wr2{margin-top:14px;}
.intro{font-size:9.6pt;line-height:1.6;color:#23272c;background:#eef3fb;border-left:3px solid var(--indigo);border-radius:0 6px 6px 0;padding:6px 10px;margin-bottom:8px;}
.blk{font-size:9.5pt;line-height:1.58;color:#2b3036;padding:6px 10px;border:1px solid #e4e6ea;border-radius:7px;margin-bottom:6px;}
.blk .bl{display:inline-block;font-weight:800;color:#fff;background:var(--indigo);border-radius:4px;padding:0 7px;margin-right:7px;font-size:8.4pt;vertical-align:1px;}
.ordwr{font-size:9.6pt;color:#333;margin-top:8px;}
.ordwr .u{display:inline-block;min-width:150px;border-bottom:1.4px solid #c9c7be;}
.ans{margin-top:8px;font-size:9.4pt;font-weight:800;color:var(--ans);background:#fdeceb;border:1px solid #f3c9c5;border-radius:6px;padding:5px 10px;}
.ans .lab{font-size:7.8pt;background:var(--ans);color:#fff;border-radius:4px;padding:0 6px;margin-right:6px;font-weight:800;vertical-align:1px;}
""".replace("__FOOT__",FOOT).replace("__FONTS__",FONTFACE)
    .replace("__TAG__","정답" if teacher else "학생용"))

def theme(p): return p["overview"]["theme_ko"]

def part1_q(p, teacher):
    it=p["item_no"].strip()
    h=json.load(open(SC+"/hard/"+it+".json"))
    s=sent_of(p, h["sentence_id"]); raw=s["english"]
    ko=h.get("translation","")
    shuffled,orig=scramble_words(raw, seed=hash("p1"+it)&0xffffffff)
    chips="".join(f'<span class="chip">{esc(w)}</span>' for w in shuffled)
    parts=[f'<div class="q"><div class="qh"><span class="qno">{esc(it)}</span>'
           f'<span class="qti">{esc(theme(p))}</span><span class="qtag">배열영작</span></div>']
    parts.append(f'<div class="ko"><b>우리말</b> · {esc(ko)}</div>')
    parts.append(f'<div class="bank">{chips}</div>')
    if teacher:
        parts.append(f'<div class="ans"><span class="lab">정답</span>{esc(raw)}</div>')
    else:
        parts.append('<div class="wr"></div><div class="wr wr2" style="margin-top:16px"></div>')
    parts.append('</div>')
    return "".join(parts)

def part2_q(p, teacher):
    it=p["item_no"].strip()
    intro,shown,ans=order_problem(p, seed=hash("p2"+it)&0xffffffff)
    parts=[f'<div class="q"><div class="qh"><span class="qno">{esc(it)}</span>'
           f'<span class="qti">{esc(theme(p))}</span><span class="qtag">순서배열</span></div>']
    parts.append(f'<div class="intro"><b>주어진 글</b><br>{esc(intro)}</div>')
    for lab,blk in zip("ABC",shown):
        parts.append(f'<div class="blk"><span class="bl">({lab})</span>{esc(" ".join(blk))}</div>')
    if teacher:
        parts.append(f'<div class="ans"><span class="lab">정답</span>{esc(ans)}</div>')
    else:
        parts.append('<div class="ordwr">글의 순서: <span class="u">&nbsp;</span></div>')
    parts.append('</div>')
    return "".join(parts)

def build(teacher, out):
    ver="정답" if teacher else "학생용"
    body=[f'<div class="doc-h">고1 2026년 9월 모의고사 · 배열영작 &amp; 순서배열 시험지 <span style="font-size:9pt;color:#b06;">[{ver}]</span></div>'
          f'<div class="doc-d">최고난도 문장 20개 배열영작 · 지문 20개 순서배열</div>']
    body.append('<div class="part">Part 1. 배열영작 — 우리말에 맞게 주어진 영어 단어를 순서대로 배열하시오.</div>')
    body.append('<div class="guide">※ 문장 끝 마침표는 스스로 붙이고, 대문자/문장부호도 알맞게 쓰시오.</div>')
    for p in P: body.append(part1_q(p, teacher))
    body.append('<div class="part" style="break-before:page;">Part 2. 순서배열 — 주어진 글 다음에 이어질 순서로 가장 적절한 것을 배열하시오.</div>')
    body.append('<div class="guide">※ (A)(B)(C)를 글의 흐름에 맞게 배열하시오.</div>')
    for p in P: body.append(part2_q(p, teacher))
    doc=f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><style>{css(teacher)}</style></head><body>{"".join(body)}</body></html>'
    HTML(string=doc).write_pdf(out)
    d=fitz.open(out); print(f"{ver}:", d.page_count, "p"); d.close()

build(False, SC+"/고1_2026_9월_배열영작·순서배열_시험지.pdf")
build(True,  SC+"/고1_2026_9월_배열영작·순서배열_정답.pdf")

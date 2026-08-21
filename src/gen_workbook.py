#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""유형별 훈련 — 실제 기출을 '대표 카드'와 동일한 3-STEP 펼침면으로 렌더링.

각 문항 = 2쪽 펼침면:
  · STEP 1 (왼쪽) 직접 풀기 — 깨끗한 지문 + 선지 + 셀프체크
  · STEP 2 (오른쪽 상) 훈련(정답 칠) — 🟡형광펜·🔴신호 + 노랑 도출 + 선지 판정 + 공식
  · STEP 3 (오른쪽 하) 해석(직독직해) — 슬래시(/)로 끊어 읽기 · 영↔한 청크 대응

콘텐츠(도출·직독직해·판정)는 corpus/workbook_content.json 에서 읽는다
(subagent가 지문별로 생성). 콘텐츠가 없는 문항은 간이 훈련 카드로 폴백.

사용: python -m src.gen_workbook [개수]   (기본 80)
출력: samples/유형별훈련_워크북.html
"""
import sys, re, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "corpus" / "passage_bank.jsonl"
CONTENT = ROOT / "corpus" / "workbook_content.json"
CONNECT = ROOT / "corpus" / "workbook_connect.json"
OUT = ROOT / "samples" / "유형별훈련_워크북.html"
_CONNECT = {}
CIRCLED = "①②③④⑤"

SIGNALS = {
  "역접": r"\b(however|but|yet|nevertheless|nonetheless|in contrast|by contrast|on the contrary|on the other hand|instead|conversely|whereas|unlike|rather than|still|no longer)\b",
  "결론": r"\b(thus|therefore|hence|consequently|as a result|in conclusion|in short|in sum|ultimately)\b",
  "한정": r"\b(only when|only if|only|unless|except|as long as)\b",
  "주장": r"\b(should|must|ought to|need to|have to|important|essential|crucial|vital|critical|the most|the only|the single)\b",
  "인과": r"\b(because|since|due to|owing to|lead to|leads to|result in|results in|give rise to|thereby|in order to)\b",
  "통념": r"\b(many believe|it is thought|it is assumed|contrary to|traditionally|surprisingly|paradoxically)\b",
}
SKIP_PAT = r"\b(for example|for instance|such as|e\.g\.|to illustrate|in spite of)\b"

FORMULA = {
  "함축의미": "밑줄 ±(긍정/부정) 판정 → 뜻을 추상화한 선지",
  "요지": "역접·결론 문장 = 요지 / 예시는 스킵",
  "주제": "반복 키워드 + 주제문 → 추상 선지",
  "제목": "주제문을 압축·비유한 선지",
  "빈칸추론": "역접·한정 문장 추상화 / 지문어 복사 선지 = 함정",
  "무관한 문장": "주제에서 벗어난 소재·논리의 문장 1개",
  "글의 순서": "지시어·연결어(this·however·연대)로 흐름 잇기",
  "문장 삽입": "지시어가 갑자기 튀는 '논리 공백' 지점",
  "요약문": "주제문 압축 → 빈칸 두 개는 추상어",
  "어휘": "문맥의 ±(긍정/부정) 방향과 반대로 튀는 낱말 1개",
  "제목(장문)": "장문 전체 주제를 압축·비유한 제목",
}
PROMPT = {
  "21": "밑줄 친 부분이 다음 글에서 의미하는 바로 가장 적절한 것은?",
  "22": "다음 글의 요지로 가장 적절한 것은?",
  "23": "다음 글의 주제로 가장 적절한 것은?",
  "24": "다음 글의 제목으로 가장 적절한 것은?",
  "31-34": "빈칸에 들어갈 말로 가장 적절한 것은?",
  "35": "다음 글에서 전체 흐름과 관계 없는 문장은?",
  "36-37": "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?",
  "38-39": "글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?",
  "40": "다음 글의 내용을 한 문장으로 요약하고자 한다. 빈칸에 들어갈 말로 가장 적절한 것은?",
  "30": "다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?",
  "41": "윗글의 제목으로 가장 적절한 것은?",
}
REMIND = {
  "21": [("역접 However","y"),("한정 only","y"),("주장 must","y"),("예시 For example ✕","g"),("양보 Despite ✕","g")],
  "22": [("역접 However","y"),("결론 Thus","y"),("주장 should","y"),("예시 For example ✕","g")],
  "23": [("역접 However","y"),("결론 Therefore","y"),("반복 키워드","y"),("예시 such as ✕","g")],
  "24": [("역접 However","y"),("결론 In sum","y"),("주장 must","y"),("예시 e.g. ✕","g")],
  "31-34": [("역접 However","y"),("한정 only when","y"),("결론 Thus","y"),("예시 For example ✕","g"),("양보 Despite ✕","g")],
  "35": [("주제 키워드","y"),("역접 However","y"),("예시 For instance ✕","g")],
  "36-37": [("지시어 this·that","y"),("연결어 However·So","y"),("연대·순서","y")],
  "38-39": [("지시어 they·this","y"),("역접 However","y"),("논리 공백","y")],
  "30": [("문맥 ± 방향","y"),("역접 However","y"),("반대로 튀는 낱말","y"),("반복 키워드","y")],
  "41": [("역접 However","y"),("결론 Thus","y"),("반복 키워드","y"),("예시 e.g. ✕","g")],
}
TYPE_TIP = {
  "21": "문항 배치상 <b>대의파악</b>(어휘 문제 아님). 밑줄은 모르는 표현으로 두고 <b>주제로 추론</b> → 한 번에 고르지 말고 <b>오답 4개를 소거</b>해 답을 택한다. 밑줄의 <b>±(긍정/부정) 방향</b>만 잡아도 절반이 소거된다 — <b>PART 0 「긍정/부정 어휘 사전」</b> 활용.",
  "22": "글쓴이가 '<b>결국 하고 싶은 말</b>'. 보기 스타일은 '<b>A는 B이다</b>'. 역접·결론 문장에 답이 있고 예시는 근거일 뿐.",
  "23": "<b>무엇에 대한 글</b>인가. 보기 스타일 '<b>B(전치사) A</b>'. 반복 키워드 + 주제문을 추상화한 선지.",
  "24": "주제문을 <b>압축·비유</b>한 것이 제목(보기 '<b>A′: B′</b>'·창의적 표현). 너무 좁거나 넓으면 오답.",
  "31-34": "빈칸은 <b>변형된 주제 문제</b>. 빈칸부터 읽거나 선지 대입 금지 — <b>주제를 먼저 잡고</b> 지문에서 근거를 찾아 정답과 비교. 지문어 복사는 함정.",
  "35": "코드 둘 — 쉬운 건 <b>내용이 갑자기 산으로</b>(앞 문장 단어를 함정으로), 어려운 건 <b>주제와 '반대'</b>되는 문장.",
  "36-37": "연결되는 곳이 아니라 <b>'단절'되는 곳</b>을 본다. 지시어·연결어·연대 같은 <b>가장 확실한 단서부터</b> 잇는다.",
  "38-39": "주어진 문장은 빠지면 <b>단절이 생기는</b> 문장. 대입이 아니라 ①~⑤를 읽으며 <b>단절을 느끼는</b> 문제다.",
  "40": "요약문을 <b>먼저</b> 읽고 선지 대입으로 경우의 수를 잡은 뒤 지문과 비교. 빈칸 둘은 핵심어를 <b>추상어</b>로 바꾼 것.",
  "30": "어휘 문제지만 <b>단어 뜻 암기 문제가 아님</b>. 글의 <b>±(긍정/부정) 흐름</b>을 잡고, 그 방향과 <b>반대로 튀는 낱말</b> 1개를 찾는다 — <b>PART 0 「긍정/부정 어휘 사전」</b> 활용.",
  "41": "장문(41~42) 지문의 <b>전체 주제</b>를 압축·비유한 제목을 고른다. 너무 좁은 세부·너무 넓은 일반론은 오답.",
}
BAND_TITLE = {
  "21":"함축의미","22":"요지","23":"주제","24":"제목","30":"어휘",
  "31-34":"빈칸추론","35":"무관한 문장","36-37":"글의 순서","38-39":"문장 삽입","40":"요약문","41":"제목(장문)",
}
BAND_ORDER = ["21","22","23","24","30","31-34","35","36-37","38-39","40","41"]
ALLOWED = set(range(21, 25)) | {30} | set(range(31, 42))

def esc(s): return html.escape(str(s), quote=False)


def select(bank, n):
    bank = [r for r in bank if r.get("num") in ALLOWED]
    by = {}
    for r in bank:
        by.setdefault(r["band"], []).append(r)
    for b in by:
        by[b].sort(key=lambda x: (1 if x.get("answer") else 0, x.get("signal_score", 0)), reverse=True)
    picked, i = [], 0
    while len(picked) < n:
        added = False
        for b in BAND_ORDER:
            if b in by and i < len(by[b]):
                picked.append(by[b][i]); added = True
                if len(picked) >= n: break
        if not added: break
        i += 1
    return picked


# ---------- 콘텐츠 기반 렌더 (대표 카드 깊이) ----------

def _inline_tags(text, tags):
    """문장 안 신호어를 <tag>+<rk>로 인라인 표시. tags=[{sig,word}]."""
    out = esc(text)
    for t in (tags or []):
        w = t.get("word") or ""
        sig = t.get("sig") or ""
        if not w:
            continue
        m = re.search(re.escape(w), out, re.I)
        if not m:
            # esc 이후 못 찾으면 원문에서 위치 무시하고 접두 태그만
            out = f'<span class="tag hot">{esc(sig)}</span> ' + out
            continue
        s, e = m.span()
        rep = f'<span class="tag hot">{esc(sig)}</span><span class="rk">{out[s:e]}</span>'
        out = out[:s] + rep + out[e:]
    return out


_CIRC = "①②③④⑤⑥⑦⑧⑨⑩"


# 논리 관계 구문(PART0 사전) 신호 — 노랑 문장에서 자동 감지해 파란 '관계어' 태그로 표시
REL_SIG = [
    ("인과", "cause", r"\b(lead(?:s|ing)? to|led to|result(?:s|ed|ing)? in|bring(?:s|ing)? about|brought about|give(?:s)? rise to|gave rise to|contribute(?:s|d)? to|stem(?:s|med)? from|arise(?:s)? from|arose from|derive(?:s|d)? from|result(?:s|ed|ing)? from|owing to|due to|thereby|responsible for|account(?:s|ed)? for|drive(?:s|n)?|drove|shape(?:s|d)?|determine(?:s|d)?|be based on|is based on|are based on|rooted in)\b"),
    ("등호", "eq", r"\b(reflect(?:s|ed)?|mirror(?:s|ed)?|represent(?:s|ed)?|embod(?:y|ies|ied)|illustrate(?:s|d)?|exemplif(?:y|ies|ied)|amount(?:s|ed)? to|is equivalent to|are equivalent to|define(?:s|d)?|is defined as|be defined as|known as|referred to as|serve(?:s|d)? as|act(?:s|ed)? as|namely)\b"),
    ("대조", "contr", r"\b(unlike|whereas|in contrast|by contrast|on the other hand|on the contrary|contrary to|differ(?:s|ed)? from|different from|distinct from|distinguish(?:es|ed)?|as opposed to|opposed to|conversely|in comparison|compared (?:to|with))\b"),
    ("비교", "comp", r"\b(outweigh(?:s|ed)?|surpass(?:es|ed)?|exceed(?:s|ed)?|prevail(?:s|ed)? over|superior to|inferior to|outnumber(?:s|ed)?|outperform(?:s|ed)?|greater than|less than|more than|rather than|instead of|prefer(?:s|red)?)\b"),
    ("대체", "repl", r"\b(replace(?:s|d)?|displace(?:s|d)?|substitute(?:s|d)? for|give(?:s)? way to|gave way to|switch(?:es|ed)? to|shift(?:s|ed)? from|transition(?:s|ed)? from)\b"),
]


POL_POS = r"\b(critical|crucial|essential|vital|fundamental|indispensable|significant|beneficial|benefit(?:s)?|valuable|invaluable|priceless|advantage(?:s|ous)?|useful|powerful|effective|strength(?:s)?|thrive[sd]?|flourish(?:es|ed)?|promising|emphasi[sz]e[sd]?|enhance[sd]?|reinforce[sd]?|prioriti[sz]e[sd]?|prominent|paramount|pivotal)\b"
POL_NEG = r"\b(abandon(?:s|ed)?|discard(?:s|ed)?|eliminate[sd]?|neglect(?:s|ed)?|ignore[sd]?|dismiss(?:es|ed)?|overlook(?:s|ed)?|reject(?:s|ed)?|refuse[sd]?|den(?:y|ies|ied)|forbid(?:s|den)?|hinder(?:s|ed)?|diminish(?:es|ed)?|obscure[sd]?|undermine[sd]?|disregard(?:s|ed)?|lack(?:s|ed|ing)?|absence|flaw(?:s|ed)?|drawback|fail(?:s|ed|ing)?|problem(?:s|atic)?|threat(?:s|en(?:s|ed)?)?|harm(?:s|ed|ful)?|damage[sd]?|weaken(?:s|ed)?|suffer(?:s|ed|ing)?|danger(?:ous)?|useless|worthless|destroy(?:s|ed)?|hardly|rarely|scarcely|by no means)\b"


def _mark_sentence(text, tags, mark_rel, rel_cap=2, pol_cap=2):
    """노랑/회색 문장 마킹 — ①근거 신호(빨강) ②논리 관계어(파랑) ③±어휘(＋녹/−적).
       관계어·±는 노랑·회색 문장에 표시(mark_rel=True), 겹치면 신호>관계어>±,
       각 유형 문장당 cap개까지."""
    spans, unmatched = [], []
    for t in (tags or []):
        w, sig = t.get("word", ""), t.get("sig", "")
        if not sig:
            continue
        m = re.search(re.escape(w), text, re.I) if w else None
        if m:
            spans.append((m.start(), m.end(), "sig", sig))
        else:
            unmatched.append(sig)
    if mark_rel:
        for name, cls, pat in REL_SIG:
            for m in re.finditer(pat, text, re.I):
                spans.append((m.start(), m.end(), "rel:" + cls, name))
        for m in re.finditer(POL_POS, text, re.I):
            spans.append((m.start(), m.end(), "pol:pl", "＋"))
        for m in re.finditer(POL_NEG, text, re.I):
            spans.append((m.start(), m.end(), "pol:mn", "−"))
    # 겹침 제거 — 신호(0) > 관계어(1) > ±(2), 그다음 이른 위치
    prio = lambda k: 0 if k == "sig" else (1 if k.startswith("rel") else 2)
    spans.sort(key=lambda s: (s[0], prio(s[2])))
    chosen, occ, reln, poln = [], [], 0, 0
    for s in spans:
        a, b, kind = s[0], s[1], s[2]
        if any(not (b <= x or a >= y) for x, y in occ):
            continue
        if kind.startswith("rel"):
            if reln >= rel_cap:
                continue
            reln += 1
        elif kind.startswith("pol"):
            if poln >= pol_cap:
                continue
            poln += 1
        chosen.append(s); occ.append((a, b))
    chosen.sort()
    out, i = [], 0
    for a, b, kind, label in chosen:
        out.append(esc(text[i:a]))
        if kind == "sig":
            out.append(f'<span class="tag hot">{esc(label)}</span><span class="rk">{esc(text[a:b])}</span>')
        elif kind.startswith("rel"):
            cls = kind.split(":", 1)[1]
            out.append(f'<span class="tag rel {cls}">{esc(label)}</span><u class="ru {cls}">{esc(text[a:b])}</u>')
        else:
            cls = kind.split(":", 1)[1]
            out.append(f'<u class="pu {cls}">{esc(text[a:b])}</u><sup class="pm {cls}">{label}</sup>')
        i = b
    tail = "".join(out) + esc(text[i:])
    pre = "".join(f'<span class="tag hot">{esc(s)}</span> ' for s in unmatched)
    html_out = pre + tail
    # 빈칸(31~40): 밑줄 구간을 빈칸 박스로
    html_out = re.sub(r'_{3,}', '<span class="bk">&nbsp;&nbsp;&nbsp;</span>', html_out)
    return html_out


def step2_passage(hl):
    parts = []
    ynum = 0  # 노랑 문장 번호 → 하단 도출 '노랑①②'와 매칭
    for seg in hl:
        role = seg.get("role", "skip")
        txt = seg.get("t", "")
        if role == "skip":
            parts.append(f'<span class="sk">{esc(txt)}</span>')
        else:
            inner = _mark_sentence(txt, seg.get("tags"), role in ("yellow", "gray"))
            cls = "m" if role == "yellow" else "g"
            # 신호어 없는 노랑 = 시험장에서 미리 잡는 신호(위치·반복어·정의) 칩 표시
            pos = seg.get("pos")
            if role == "yellow" and not seg.get("tags") and pos:
                pw = seg.get("posword")
                if pw and esc(pw) in inner:
                    inner = inner.replace(esc(pw), f'<u class="rep">{esc(pw)}</u>', 1)
                inner = f'<span class="tag pos">{esc(pos)}</span>' + inner
            if role == "yellow":
                badge = _CIRC[ynum] if ynum < len(_CIRC) else f"{ynum+1}"
                ynum += 1
                inner = f'<span class="ynum">{badge}</span>' + inner
            parts.append(f'<mark class="{cls}">{inner}</mark>')
    return " ".join(parts)


INS_MARK = "[삽입 문장]"


def _split_insert(hl, insert_en=None):
    """삽입 문항이면 (삽입문장 텍스트, 본문 텍스트), 아니면 (None, 전체 텍스트).
    - '[삽입 문장]' 마커가 있으면 그것을 분리.
    - 없고 insert_en(넣을 문장)이 주어지면: 본문에 그 문장이 박혀 있으면 빼내고(정답 자리엔 번호만 남김),
      본문에 없으면(이미 분리돼 주어진 문장) 그대로 박스만 표시."""
    ins, body = None, []
    for seg in hl:
        t = seg.get("t", "")
        if t.startswith(INS_MARK):
            ins = t[len(INS_MARK):].strip()
        else:
            body.append(t)
    body_txt = " ".join(body).strip()
    if ins is not None:
        return ins, body_txt
    if insert_en:
        en = insert_en.strip()
        if en and en in body_txt:
            body_txt = body_txt.replace(en, " ")
            body_txt = re.sub(r"\s{2,}", " ", body_txt).strip()
            body_txt = re.sub(r"\s+([.,;:])", r"\1", body_txt)
            return en, body_txt
        return en, body_txt
    return None, body_txt


def uline_html(html, phrase):
    """함축의미(21) 지문에서 밑줄 친 부분을 <u>로 표시. 이미 렌더된 HTML 문자열에 적용."""
    if not phrase:
        return html
    p = esc(phrase)
    if p and p in html:
        return html.replace(p, f'<u class="uph">{p}</u>', 1)
    return html


def _clue_html(txt, clues):
    """텍스트 안 연결고리(marker)만 색칠해 HTML로."""
    low = txt.lower()
    spans = []
    for c in (clues or []):
        m = c.get("marker", ""); kind = c.get("kind", "")
        if not m:
            continue
        i = low.find(m.lower())
        if i >= 0:
            spans.append((i, i + len(m), CLUE_CLS.get(kind, "ck-ref")))
    spans.sort()
    merged = []
    for a, b, cls in spans:
        if merged and a < merged[-1][1]:
            continue
        merged.append([a, b, cls])
    out, i = [], 0
    for a, b, cls in merged:
        out.append(esc(txt[i:a]))
        out.append(f'<span class="pclue {cls}">{esc(txt[a:b])}</span>')
        i = b
    out.append(esc(txt[i:]))
    return "".join(out)


def connective_passage(hl, clues, insert_en=None):
    """순서·삽입 전용 STEP2 지문 — 노랑 형광펜 없이 연결고리(지시어·연결어·시간)만 색칠.
       삽입은 '삽입할 문장'을 본문과 띄워 별도 박스로 구분."""
    ins, body = _split_insert(hl, insert_en)
    body_html = _clue_html(body, clues)
    if ins is not None:
        ins_html = _clue_html(ins, clues)
        return (f'<div class="insbox"><span class="inslab">삽입할 문장</span>'
                f'<span class="instext">{ins_html}</span></div>'
                f'<div class="insbody">{body_html}</div>')
    return body_html


def clean_passage(hl, band, insert_en=None):
    """STEP1 문제용 깨끗한 지문 = hl 문장들을 그대로 이어붙임(형광펜 없음).
       삽입은 '삽입할 문장'을 본문과 띄워 별도 박스로 구분."""
    def _fmt(t):
        return re.sub(r'_{3,}', '<span class="bk">&nbsp;&nbsp;&nbsp;</span>', esc(t))
    ins, body = _split_insert(hl, insert_en)
    if ins is not None:
        return (f'<div class="insbox"><span class="inslab">삽입할 문장</span>'
                f'<span class="instext">{_fmt(ins)}</span></div>'
                f'<div class="insbody">{_fmt(body)}</div>')
    return _fmt(body)


def _anchor(text, limit=95):
    """노란 문장의 핵심 어구를 앵커로 — 빈칸/마커는 남기고 길면 축약."""
    t = re.sub(r"\s+", " ", text or "").strip()
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0] + " …"
    return esc(t)


def derive_block(d, yellows=None):
    steps = ""
    _CIR = "①②③④⑤⑥⑦⑧⑨⑩"
    yellows = yellows or []
    for i, s in enumerate(d.get("steps", [])):
        yb = f'노랑{_CIR[i]}' if i < len(_CIR) else '노랑'
        an = f' <span class="an">— {s.get("an","")}</span>' if s.get("an") else ""
        anchor = f'<span class="yanch">“{_anchor(yellows[i])}”</span>' if i < len(yellows) else ""
        steps += (f'<li><span class="yb">{yb}</span>{anchor}'
                  f'<span class="ystep">{s.get("ko","")}{an}</span></li>')
    concl = f'<div class="concl">{d.get("concl","")}</div>' if d.get("concl") else ""
    gnote = f'<div class="gnote">{esc(d.get("gnote",""))}</div>' if d.get("gnote") else ""
    return f'''<div class="derive">
      <div class="dh">🟡 노란색 문장만으로 정답이 나오는 과정 <span style="font-weight:600;color:#a58a3a;font-size:8.3px">(노랑①②③ = 위 지문에 <b>같은 번호</b>로 칠한 노랑 문장)</span></div>
      <ol>{steps}</ol>{concl}{gnote}</div>'''


CLUE_CLS = {"지시어":"ck-ref","연결어":"ck-conj","시간":"ck-time","대응":"ck-echo"}
def connect_block(cn, typ):
    """순서·삽입 전용 — 노랑 형광펜 대신 지시어·연결어·시간으로 조각을 잇는 연결고리 풀이."""
    clues = ""
    for c in cn.get("clues", []):
        kind = c.get("kind", ""); cls = CLUE_CLS.get(kind, "ck-ref")
        clues += (f'<div class="clue"><span class="cw">{esc(c.get("marker",""))}</span>'
                  f'<span class="ck {cls}">{esc(kind)}</span>'
                  f'<span class="cn">{esc(c.get("note",""))}</span></div>')
    steps = "".join(f'<li><span class="ln">{i+1}</span>{esc(s)}</li>'
                    for i, s in enumerate(cn.get("chain", [])))
    lab = esc(cn.get("answer_label", ""))
    head = ("🔗 연결고리로 <b>순서를 잇는</b> 과정" if typ == "순서"
            else "🔗 연결고리로 <b>넣을 자리를 찾는</b> 과정")
    return f'''<div class="derive connect">
      <div class="dh">{head} <span style="font-weight:600;color:#3a6ea5;font-size:8.3px">(노랑 형광펜이 아니라 지시어·연결어·시간으로 조각을 연결)</span></div>
      <div class="clues">{clues}</div>
      <ol class="chain">{steps}</ol>
      <div class="concl">→ 정답: <b>{lab}</b></div>
      <div class="gnote">순서·삽입은 '중요 문장'이 아니라 <b>이어주는 단서(고리)</b>로 푼다.</div></div>'''


def paraphrase_line(p):
    if not p:
        return ""
    frm = esc(p.get("from", "")); to = esc(p.get("to", "")); topt = p.get("to_opt")
    copies = p.get("copies") or []
    cp = " ".join(f'<span class="cp">{esc(c)}</span>' for c in copies)
    tail = f' / 복사 함정 {cp}' if cp else ""
    arw = f'<span class="arw">→</span> {CIRCLED[topt-1] if topt else ""}' if to else ""
    return f'<div class="pline"><span class="lb">패러프레이즈</span> <span class="sw">{frm}</span> {arw} <span class="sw">{to}</span> ✓{tail}</div>'


def opts_block(opts, answer):
    lis = []
    for o in opts:
        n = o.get("n")
        ok = (o.get("verdict") == "ok") or (n == answer)
        cls = "opt ok" if ok else "opt x"
        jd = o.get("jd") or ("✔ 정답" if ok else "✘")
        if ok and jd.startswith("✔") and "정답" not in jd:
            jd = "✔ 정답 · " + jd[1:].strip()
        ko = o.get("ko", "")
        ko_html = f'<span class="oko">{esc(ko)}</span>' if ko else ""
        badge = '<span class="okflag">정답</span>' if ok else ""
        lis.append(f'<div class="{cls}"><span class="n">{CIRCLED[n-1] if n else "·"}</span>'
                    f'<span class="txwrap"><span class="tx">{o.get("tx","")}</span>{ko_html}</span>'
                    f'{badge}<span class="jd">{esc(jd)}</span></div>')
    circ = CIRCLED[answer-1] if answer and 1 <= answer <= 5 else "·"
    head = f'<div class="ans-head">✅ 정답 <span class="ansno">{circ}</span></div>'
    return f'<div class="opts">{head}{"".join(lis)}</div>'


def vocab_underline(html, opts):
    """어휘(30): 지문 속 ①~⑤ 낱말에 밑줄."""
    for i, o in enumerate(opts):
        if i >= len(CIRCLED):
            break
        w = re.sub(r"<[^>]+>", "", o.get("tx", "")).strip()
        if not w:
            continue
        mk = CIRCLED[i]
        html = re.sub(re.escape(mk) + r"\s*" + re.escape(w),
                      f'{mk}<u class="vund">{esc(w)}</u>', html, count=1)
    return html


def vocab_block(vocab):
    """핵심 어휘·숙어 리스트 — 해석 페이지 하단 박스."""
    if not vocab:
        return ""
    items = ""
    for v in vocab:
        if not isinstance(v, dict):
            continue
        w = esc(v.get("w", "")); m = esc(v.get("m", ""))
        if not w:
            continue
        items += f'<div class="vitem"><span class="vw">{w}</span><span class="vm">{m}</span></div>'
    if not items:
        return ""
    return (f'<div class="vocabox"><div class="vh">📚 핵심 어휘·숙어</div>'
            f'<div class="vgrid">{items}</div></div>')


def direct_block(num, typ, direct):
    """해석카드 = 형광펜 색 없이 슬래시(/)로 끊어 읽기 (영↔한 청크 대응)."""
    SL = ' <span class="sl">/</span> '
    rows = ""
    for i, r in enumerate(direct):
        en = SL.join(esc(c[0]) for c in r.get("en", []))
        ko = SL.join(esc(c[0]) for c in r.get("ko", []))
        note = f' <span style="color:#8a6a00;font-weight:700">← {esc(r["note"])}</span>' if r.get("note") else ""
        rows += (f'<div class="row"><span class="bn">{i+1}</span>'
                 f'<div class="en">{en}</div><div class="ko">{ko}{note}</div></div>')
    return rows


def seam_block(seq):
    """순서·삽입 '이음매형' 해석카드 — 조각별 지시어의 한국어 정체 + 어디에 붙는지."""
    if not seq:
        return ""
    rows = ""
    for p in seq.get("pieces", []):
        label = esc(p.get("label", ""))
        cue = p.get("cue", ""); kind = p.get("cue_kind", "")
        cls = CLUE_CLS.get(kind, "ck-ref")
        if cue:
            cuehtml = f'<span class="pclue {cls}">{esc(cue)}</span>'
        else:
            cuehtml = '<span class="nocue">첫머리 단서 없음</span>'
        refers = p.get("refers", "")
        refhtml = (f'<span class="rarw">→</span> <span class="refv">{esc(refers)}</span>'
                   if refers else "")
        en = esc(p.get("en", "")); ko = esc(p.get("ko", "")); link = esc(p.get("link", ""))
        rows += (f'<div class="seamrow"><div class="slab">{label}</div>'
                 f'<div class="sbody"><div class="scue">{cuehtml}{refhtml}</div>'
                 f'<div class="sen">{en}</div><div class="sko">{ko}</div>'
                 f'<div class="slink">{link}</div></div></div>')
    ans = esc(seq.get("answer", ""))
    return f'<div class="seamwrap">{rows}<div class="seamans">→ 정답: <b>{ans}</b></div></div>'


def opt_line(item):
    return item.get("opt_line", "")


def exam_src(eid):
    """exam_id '2026-06' → '2026학년도 6월', '2024-수능' → '2024학년도 수능'."""
    if not eid or "-" not in eid:
        return esc(eid or "")
    y, m = eid.split("-", 1)
    m = {"06": "6월", "09": "9월", "수능": "수능", "11": "수능"}.get(m, m)
    return f"{esc(y)}학년도 {esc(m)}"


def _norm_q(s):
    return re.sub(r"[‘’“”]", "'", s or "").lower()


def _verbatim_word(word, sent):
    """리마인더 칩에는 '지문(노랑 문장)에 실제로 있는' 표현만 남긴다.
       word가 문장에 그대로 있으면 그대로, 아니면 …·;·, 로 쪼갠 조각 중 문장에
       있는 것만 ' … '로 이어 반환. 하나도 없으면 '' (→ 신호명만 표시)."""
    if not word:
        return ""
    ns = _norm_q(sent)
    if _norm_q(word) in ns:
        return word
    frags = [f.strip() for f in re.split(r"\.\.\.|[…;,]", word) if f.strip()]
    keep = [f for f in frags if len(f) >= 4 and _norm_q(f) in ns]
    return " … ".join(keep)


def item_signals(hl):
    """이 문항에 '실제로 쓰인' 노랑 신호로 리마인더 칩 생성 → 노랑 형광펜과 일치.
       칩에 적는 표현은 해당 노랑/회색 문장에 verbatim으로 존재하는 것만(없으면 신호명만)."""
    chips, seen, has_skip = [], set(), False
    def add(label, cls):
        if label and label not in seen:
            seen.add(label); chips.append((label, cls))
    for seg in hl:
        role = seg.get("role")
        if role == "skip":
            has_skip = True; continue
        if role not in ("yellow", "gray"):
            continue
        cls = "y" if role == "yellow" else "g"
        sent = seg.get("t", "")
        for t in (seg.get("tags") or []):
            sig, word = t.get("sig", ""), t.get("word", "")
            if sig:
                vw = _verbatim_word(word, sent)
                add(f"{sig} {vw}".strip(), cls)
        pos = seg.get("pos")
        if role == "yellow" and pos and not seg.get("tags"):
            pw = _verbatim_word(seg.get("posword", ""), sent)
            add(f"{pos} {pw}".strip() if pw else pos, "y")
    if has_skip:
        add("예시·부연 ✕ 넘김", "g")
    return chips[:7]


# ---------- 재진술(패러프레이징) — 문항마다 내장되는 추가 훈련 ----------

_RROLE = {"주제문": "r-main", "재진술": "r-re", "정답근거": "r-ans"}


_RQLAB = ["핵심 소재·주장", "→ 재진술 ①", "→ 재진술 ②", "→ 재진술 ③", "→ 재진술 ④", "→ 재진술 ⑤"]


def contrast_cue(hl):
    """노랑 문장에서 '소재 2개' 단서가 되는 대조·비교 관계어를 뽑는다."""
    pats = [pat for name, cls, pat in REL_SIG if cls in ("contr", "comp")]
    found, seen = [], set()
    for seg in (hl or []):
        if seg.get("role") not in ("yellow", "gray"):
            continue
        t = seg.get("t", "")
        for pat in pats:
            for m in re.finditer(pat, t, re.I):
                w = m.group(0); lw = w.lower()
                if lw not in seen:
                    seen.add(lw); found.append(w)
    return found[:4]


def restate_problem(rt, cue=None):
    """STEP1 문제면 하단 — 지문을 주고 A→A′→A″(→A‴) / A·B 로 '직접 잇는' 재진술 연결 문제."""
    if not rt:
        return ""
    if rt.get("has_restate") is False:
        return ""  # 재진술 없음 → 문제 미출제
    kind = rt.get("kind", "single")
    subs = rt.get("subjects") or []
    # 재진술이 실제로 있는 만큼만 문제화 — 없으면(사슬<2) 문제 자체를 내지 않는다.
    compare = kind == "compare" and len(subs) >= 2 and any(len(s.get("trail") or []) >= 2 for s in subs[:2])
    if compare:
        cols = ""
        for li, s in zip(["A", "B"], subs[:2]):
            trail = s.get("trail") or []
            n = len(trail)
            if n < 1:
                continue
            rows = ""
            for i in range(n):
                lab = "소재(주어짐)" if i == 0 else "→ 재진술 " + "①②③④⑤⑥"[i - 1]
                if i == 0:  # 첫 표현은 알려준다(출발점)
                    t0 = trail[0]
                    cell = (f'<span class="given">{esc(t0.get("en",""))}'
                            f'<i>{esc(t0.get("ko",""))}</i></span>')
                else:
                    cell = '<span class="ln"></span>'
                rows += (f'<div class="rqrow"><span class="pr">{_prime(li, i)}</span>'
                         f'<span class="rqlab">{lab}</span>{cell}</div>')
            name = esc(s.get("name", "")) or f"비교 소재 {li}"
            cols += (f'<div class="rqsub"><div class="rqname"><span class="pr big">{li}</span>'
                     f'{name} <span class="rqcnt">재진술 {max(0,n-1)}개 찾기</span></div>{rows}</div>')
        if cue:
            cue_html = ' · '.join(f'<b>{esc(w)}</b>' for w in cue)
            cbox = (f'<div class="rqcue">🔍 <b>소재 2개</b> 단서 — 지문의 <b>대조·비교 신호</b> {cue_html} '
                    f'→ A·B 두 소재를 견준다</div>')
        else:
            cbox = ('<div class="rqcue">🔍 이 글은 <b>두 소재(A·B)</b>를 나란히 견준다 '
                    '— 대조·비교 흐름을 잡아 각 소재의 재진술을 따로 추적</div>')
        body = cbox + f'<div class="rqsubs">{cols}</div>'
        guide = '각 소재의 <b>첫 표현(A·B)은 주어져</b> 있다. 그것이 <b>재진술된 표현</b>을 <b>A′…·B′…</b>로 찾아 잇는다.'
        nlab = "소재 2개"
    else:
        chain = rt.get("chain") or []
        n = len(chain)
        if n < 2:  # 재진술이 없으면 억지로 문제 만들지 않음
            return ""
        rows = ""
        for i in range(n):
            lab = _RQLAB[i] if i < len(_RQLAB) else "→ 재진술"
            if i == 0:  # 핵심 소재·주장(A)은 알려준다(출발점)
                c0 = chain[0]
                lab = "핵심 소재·주장(주어짐)"
                cell = f'<span class="given">{esc(c0.get("en",""))}<i>{esc(c0.get("ko",""))}</i></span>'
            else:
                cell = '<span class="ln"></span>'
            rows += (f'<div class="rqrow"><span class="pr">{_prime("A", i)}</span>'
                     f'<span class="rqlab">{lab}</span>{cell}</div>')
        body = f'<div class="rqchain">{rows}</div>'
        guide = '<b>핵심 소재·주장(A)은 주어져</b> 있다. 지문에서 그것을 <b>다른 말로 바꾼 표현</b>을 나온 <b>만큼</b> <b>A′→A″…</b>로 찾아 잇는다.'
        nlab = f"재진술 {n-1}개 찾기"
    return f'''<div class="rquiz">
      <div class="rqh"><span class="ico">🔁</span>재진술 연결 문제<span class="add">추가 문제</span>
        <span class="rqno">{nlab}</span></div>
      <div class="rqg">{guide} <b style="color:#a5342d">실제 재진술만 — 없으면 잇지 않는다.</b></div>
      {body}
    </div>'''


def _prime(letter, i):
    """A, A′, A″, A‴ … 재진술 사슬 라벨."""
    return letter + ("′" * i)


def _rrows(letter, seq):
    out = ""
    for i, seg in enumerate(seq or []):
        lab = _prime(letter, i)
        how = seg.get("how", "")
        howhtml = f'<span class="rhow">{esc(how)}</span>' if (how and how != "—") else ""
        arw = '<span class="rarw">↓</span>' if i > 0 else ""
        out += (f'<div class="rc"><span class="pr">{esc(lab)}</span>{arw}{howhtml}'
                f'<span class="ren">{esc(seg.get("en",""))}</span>'
                f'<span class="rko">{esc(seg.get("ko",""))}</span></div>')
    return out


def restate_card(rt):
    """STEP3 오른쪽 — 재진술 지도. 한 소재 A→A′→A″→A‴ / 두 소재 A…·B…로 되풀이를 추적."""
    if not rt:
        return ""
    if rt.get("has_restate") is False:
        return ""
    thesis = esc(rt.get("thesis", ""))
    echo = esc(rt.get("echo", ""))
    kind = rt.get("kind", "single")
    subs = rt.get("subjects") or []
    compare = kind == "compare" and len(subs) >= 2 and any(len(s.get("trail") or []) >= 2 for s in subs[:2])
    if not compare and len(rt.get("chain") or []) < 2:
        return ""  # 재진술 없음 → 정답 카드도 내지 않음(문제와 짝)
    if compare:
        blocks = ""
        for li, s in zip(["A", "B"], subs[:2]):
            blocks += (f'<div class="rsub"><div class="rname"><span class="pr big">{li}</span>'
                       f'{esc(s.get("name",""))}</div>{_rrows(li, s.get("trail"))}</div>')
        body = f'<div class="rsubs">{blocks}</div>'
        hint = '두 소재를 <b>A→A′→A″</b> · <b>B→B′→B″</b>로 나란히 추적 — 각 소재가 표현만 바뀌며 되풀이된다'
    else:
        body = f'<div class="rchain">{_rrows("A", rt.get("chain"))}</div>'
        hint = '같은 소재 <b>A</b>가 <b>A→A′→A″→A‴</b>로 표현만 바뀌며 되풀이 → 마지막이 정답 선지'
    thesis_html = f'<div class="thesis"><span class="lb">핵심(A)</span>{thesis}</div>' if thesis else ""
    echo_html = f'<div class="rEcho"><span class="lb">정답</span>{echo}</div>' if echo else ""
    return f'''<div class="card restate">
      <div class="hd"><span class="no rno">🔁</span><span class="ty">재진술 지도</span>
        <span class="kind" style="color:#8a5a1a;border-color:#e0b94a">재진술 연결 문제 · 정답</span>
        <span class="tm">패러프레이징</span></div>
      {thesis_html}
      <div class="rhint">{hint}</div>
      {body}
      {echo_html}
    </div>'''


def mugwan_html(mug, step2=False):
    """무관한 문장(35) — 도입문 + ①②③④⑤ 번호 문장. step2면 무관(정답) 문장을 표시."""
    intro = mug.get("intro", "")
    cands = mug.get("cands", [])
    irr = mug.get("irrelevant", 0)
    parts = []
    if intro:
        parts.append(f'<span class="mg-intro">{esc(intro)}</span>')
    for i, t in enumerate(cands, 1):
        badge = f'<span class="mgn">{CIRCLED[i-1]}</span>'
        if step2 and i == irr:
            parts.append(f'{badge}<span class="mg-x">{esc(t)}<span class="mg-xt">✕ 흐름과 무관</span></span>')
        else:
            parts.append(f'{badge}{esc(t)}')
    return " ".join(parts)


def mugwan_opts(mug):
    """무관 STEP2 선지 판정 — ①~⑤ 중 무관 문장이 정답."""
    cands = mug.get("cands", []); irr = mug.get("irrelevant", 0)
    out = []
    for i, t in enumerate(cands, 1):
        tx = (t[:38] + "…") if len(t) > 40 else t
        ok = (i == irr)
        cls = "opt ok" if ok else "opt x"
        jd = "✔ 주제 이탈 → 정답" if ok else "흐름 유지"
        out.append(f'<div class="{cls}"><span class="n">{CIRCLED[i-1]}</span>'
                   f'<span class="tx">{esc(tx)}</span><span class="jd">{esc(jd)}</span></div>')
    return f'<div class="opts">{"".join(out)}</div>'


def mugwan_direct(mug):
    """무관(35) 해석 카드 — 도입 + ①~⑤ 다섯 문장 전부 영↔한, 무관(정답) 문장 표시."""
    intro = mug.get("intro", ""); intro_ko = mug.get("intro_ko", "")
    cands = mug.get("cands", []); cands_ko = mug.get("cands_ko", [])
    irr = mug.get("irrelevant", 0)
    rows = ""
    if intro:
        rows += (f'<div class="row"><span class="bn bn-i">도입</span>'
                 f'<div class="en">{esc(intro)}</div>'
                 f'<div class="ko">{esc(intro_ko)}</div></div>')
    for i, en in enumerate(cands, 1):
        ko = cands_ko[i-1] if i-1 < len(cands_ko) else ""
        if i == irr:
            rows += (f'<div class="row mgirr"><span class="bn irr">{CIRCLED[i-1]}</span>'
                     f'<div class="en">{esc(en)}</div>'
                     f'<div class="ko">{esc(ko)}<span class="mgtag">✕ 흐름과 무관 = 정답</span></div></div>')
        else:
            rows += (f'<div class="row"><span class="bn">{CIRCLED[i-1]}</span>'
                     f'<div class="en">{esc(en)}</div>'
                     f'<div class="ko">{esc(ko)}</div></div>')
    return rows


def solution_block(rec, c, idx):
    """형광펜 해설(오른쪽) 조립 — STEP2 정답 칠 + STEP3 직독직해 + 재진술. 답지(해설지)에서도 재사용."""
    num = rec["num"]; typ = BAND_TITLE.get(rec["band"], rec.get("type", ""))
    answer = c.get("answer") or rec.get("answer")
    hl = c.get("hl") or []
    formula = FORMULA.get(typ, "")
    src_ans = c.get("answer_src", "given")
    ans_note = "" if src_ans == "given" else " <span style=\"font-size:8px;color:#a86b00\">(정답 미공개 → 풀이로 확정)</span>"
    seqtype = "순서" if num in (36, 37) else ("삽입" if num in (38, 39) else "")
    cn = _CONNECT.get(f'{rec.get("exam_id","")}|{num}') if seqtype else None
    insert_en = None
    if seqtype == "삽입":
        _sd = c.get("seq_direct") or {}
        _p = next((p for p in _sd.get("pieces", []) if p.get("label") == "넣을 문장"), None)
        if _p:
            insert_en = _p.get("en")
    mug = c.get("mugwan") if num == 35 else None
    uline = c.get("uline")
    rt = c.get("restate")

    step2_kind = "STEP 2 · 훈련 (연결고리 잇기)" if seqtype else "STEP 2 · 훈련 (정답 칠)"
    _yellows = [h.get("t", "") for h in hl if h.get("role") == "yellow"]
    reason_block = connect_block(cn, seqtype) if (seqtype and cn) else derive_block(c.get("derive", {}), _yellows)
    pline = "" if seqtype else paraphrase_line(c.get("paraphrase"))
    passage_html = connective_passage(hl, cn.get("clues") if cn else [], insert_en) if (seqtype and cn) else step2_passage(hl)
    if mug:
        passage_html = mugwan_html(mug, step2=True)
    passage_html = uline_html(passage_html, uline)
    if num == 30:
        passage_html = vocab_underline(passage_html, c.get("opts", []))
    clue_legend = ('<div class="clue-legend"><span class="pclue ck-ref">지시어</span><span class="pclue ck-conj">연결어</span>'
                   '<span class="pclue ck-time">시간·순서</span> 만 표시 — 노랑 형광펜은 쓰지 않아요</div>') if seqtype else ""
    color_legend = "" if seqtype else (
        '<div class="color-legend"><span class="clh">형광펜 3색</span>'
        '<span class="cl m">🟡 정답 핵심<b>무조건 읽기</b></span>'
        '<span class="cl g">🟩 주제·배경<b>화제만 파악 · 근거 아님</b></span>'
        '<span class="cl sk">⬜ 예시·부연<b>넘겨도 됨</b></span>'
        '<span class="cl" style="background:#fff"><span class="tag pos" style="font-size:7px">반복어</span> '
        '= 신호어 없이 <b>자리·반복어·정의</b>로 잡는 노랑</span>'
        '<span class="cl" style="background:#fff"><span class="tag rel eq" style="font-size:7px">관계어</span> '
        '= <b>인과·등호·대조·비교</b> 논리 신호 <span style="color:#8a929b">(PART 0 구문 사전)</span></span>'
        '<span class="cl" style="background:#fff"><u class="pu pl">긍정</u><sup class="pm pl">＋</sup> '
        '<u class="pu mn">부정</u><sup class="pm mn">−</sup> = <b>±어휘</b> <span style="color:#8a929b">(PART 0 ± 사전)</span></span></div>')
    right = f'''<div class="qsolution">
    <div class="card">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span><span class="kind">{step2_kind}</span><span class="tm">평가원 {exam_src(rec.get("exam_id",""))} {num}번 · #{idx}{ans_note}</span></div>
      {clue_legend}{color_legend}
      <div class="psg">{passage_html}</div>
      {reason_block}
      {pline}
      {mugwan_opts(mug) if mug else opts_block(c.get("opts", []), answer)}
      {'<div class="reconnote">※ 원본 선지 일부가 유실되어 <b>선지를 학습용으로 재구성</b>했습니다 (지문·정답은 기출 그대로).</div>' if c.get("recon_opts") else ""}
      <div class="formula"><span class="k">공식</span>{esc(formula)}</div>
    </div>'''
    seqd = c.get("seq_direct") if seqtype else None
    if seqd:
        step3_kind = "STEP 3 · 해석 (조각 잇기)"; step3_tm = "🔗 지시어·이음매"
        step3_head = ("🔗 조각별 해석 — <b>지시어가 가리키는 것</b>과 <b>어디에 붙는지</b>로 순서를 확인"
                      if seqtype == "순서" else
                      "🔗 조각별 해석 — <b>넣을 문장의 지시어</b>가 앞을 받아 <b>끊긴 흐름</b>을 메우는지 확인")
        step3_body = seam_block(seqd)
    elif mug:
        step3_kind = "STEP 3 · 해석 (다섯 문장 전체)"; step3_tm = "①~⑤ 전문장"
        step3_head = "🔍 다섯 문장 전체 해석 — ①~⑤ 중 <b>흐름과 무관한 정답 문장</b>까지 모두 확인"
        step3_body = mugwan_direct(mug)
    else:
        step3_kind = "STEP 3 · 해석 (직독직해)"; step3_tm = "🟡문장·선지만"
        step3_head = "🟡 무조건 읽는 문장 — 슬래시(/)로 끊어 읽기 · 영↔한 대응"
        step3_body = direct_block(num, typ, c.get("direct", []))
        if num == 40 and c.get("summary"):
            _atx = next((o.get("tx", "") for o in c.get("opts", []) if o["n"] == answer), "")
            _parts = re.split(r"\s*(?:…|\.\.\.|·)\s*", _atx, maxsplit=1)
            _a, _b = (_parts + ["", ""])[:2]
            step3_body = summary_box(c.get("summary"), fill=(_a, _b)) + step3_body
    right2 = f'''<div class="card trans">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span><span class="kind" style="color:var(--src-line);border-color:var(--src-line)">{step3_kind}</span><span class="tm">{step3_tm}</span></div>
      <div class="dchl">
        <span class="kt">{step3_head}</span>
        {step3_body}
        <div class="opt-line">{opt_line(c)}</div>
      </div>
    </div>'''
    return right + right2 + restate_card(rt) + '\n  </div>'


def summary_box(summary, fill=None):
    """요약문(40) 요약 문장 — (A)/(B) 빈칸. fill=(a_word,b_word)면 정답으로 채워 강조."""
    if not summary:
        return ""
    s = esc(summary)
    if fill:
        a, b = fill
        s = s.replace("___(A)___", f'<span class="sfa">(A) {esc(a)}</span>')
        s = s.replace("___(B)___", f'<span class="sfb">(B) {esc(b)}</span>')
        head = "🧩 요약문 완성"
    else:
        s = s.replace("___(A)___", '<span class="sbk">(A)</span>')
        s = s.replace("___(B)___", '<span class="sbk">(B)</span>')
        head = "🧩 한 문장 요약"
    return f'<div class="sumbox"><div class="sh">{head}</div><div class="sent">{s}</div></div>'


def render_spread(rec, c, idx):
    band = rec["band"]; typ = BAND_TITLE.get(band, rec.get("type", ""))
    num = rec["num"]; pts = f'{rec.get("points")}점' if rec.get("points") else ""
    answer = c.get("answer") or rec.get("answer")
    hl = c.get("hl") or []
    choices = rec.get("choices") or {}
    prompt = PROMPT.get(band, "다음 글을 읽고 물음에 답하시오.")
    # STEP1 선지
    # STEP1 선지: 원본 choices가 완전하면 그대로, 불완전(누락·손상)하면 검증된 content opts로 대체
    _opts = c.get("opts", [])
    if _opts and len(choices) < len(_opts):
        choices = {str(o["n"]): (o.get("tx") or "") for o in _opts}
    opt_lines = ""
    for k in sorted(int(x) for x in choices):
        opt_lines += f'<span class="o">{CIRCLED[k-1]} {esc(choices[str(k)])}</span>'
    formula = FORMULA.get(typ, "")
    src_ans = c.get("answer_src", "given")
    ans_note = "" if src_ans == "given" else " <span style=\"font-size:8px;color:#a86b00\">(정답 미공개 → 풀이로 확정)</span>"
    # 순서(36·37)·삽입(38·39)은 '연결고리' 풀이법
    seqtype = "순서" if num in (36, 37) else ("삽입" if num in (38, 39) else "")
    # 신호 리마인더 칩 — 순서·삽입은 연결고리(고정), 그 외는 '이 문항 실제 노랑 신호'로 생성
    _sig = REMIND.get(band, REMIND["31-34"]) if seqtype else (item_signals(hl) or REMIND.get(band, REMIND["31-34"]))
    chips = "".join(f'<span class="chip {cl}">{esc(tx)}</span>' for tx, cl in _sig)
    cn = _CONNECT.get(f'{rec.get("exam_id","")}|{num}') if seqtype else None
    # 삽입: 삽입할 문장(seq_direct의 '넣을 문장')을 본문과 분리해 띄워 표시
    insert_en = None
    if seqtype == "삽입":
        _sd = c.get("seq_direct") or {}
        _p = next((p for p in _sd.get("pieces", []) if p.get("label") == "넣을 문장"), None)
        if _p:
            insert_en = _p.get("en")
    if seqtype:
        how = ("🔗 <b>연결고리로 푼다</b> — 노랑 형광펜이 아니라 각 조각의 <b>지시어·연결어·시간 표현</b>을 표시해 이어보세요."
               if seqtype == "순서" else
               "🔗 <b>연결고리로 푼다</b> — 주어진 문장의 <b>지시어(this·they)</b>가 가리킬 자리와 <b>흐름이 끊긴 곳</b>을 찾으세요.")
        g3 = (('<div class="s"><span class="k">1</span>주어진 글 끝 내용 파악</div>'
               '<div class="s"><span class="k">2</span>각 단락 첫머리 지시어·연결어가 어디를 받나</div>'
               '<div class="s"><span class="k">3</span>연대·인과로 사슬 잇기 → 배열</div>')
              if seqtype == "순서" else
              ('<div class="s"><span class="k">1</span>주어진 문장의 지시어·대명사 확인</div>'
               '<div class="s"><span class="k">2</span>그 지시어가 가리킬 선행어 위치 찾기</div>'
               '<div class="s"><span class="k">3</span>넣었을 때 논리 공백이 메워지는 곳</div>'))
        checks = ('<li>각 조각의 첫 지시어·연결어를 표시했나?</li><li>연대·인과로 사슬이 이어지나?</li><li>대명사가 가리킬 선행어가 앞에 있나?</li>'
                  if seqtype == "순서" else
                  '<li>주어진 문장의 지시어(this·they)를 확인했나?</li><li>그 선행어가 있는 위치 뒤인가?</li><li>넣으니 흐름 단절이 메워지나?</li>')
    else:
        how = "🖍 신호 사전을 떠올리며 <b>무조건 읽을 문장에 형광펜</b>을 직접 치고, 예시는 넘기며 답을 골라보세요."
        g3 = ('<div class="s"><span class="k">1</span>묻는 문장부터 읽고 \'무엇을 묻나\' 파악</div>'
              '<div class="s"><span class="k">2</span>역접·한정·결론 신호 문장만 🟡, 예시는 넘기기</div>'
              '<div class="s"><span class="k">3</span>지문어 복사 선지 소거 → 바꿔 말한 선지</div>')
        checks = '<li>근거 신호 문장을 찾아 칠했나?</li><li>예시·양보절은 회색으로 넘겼나?</li><li>지문 단어 그대로 쓴 선지부터 지웠나?</li>'
    remind_label = "🔗 연결고리 단서" if seqtype else "📢 신호 리마인더"
    uline = c.get("uline")  # 함축의미(21): 밑줄 친 부분
    step1_psg = uline_html(clean_passage(hl, band, insert_en), uline)
    # 무관한 문장(35): 도입 + ①~⑤ 번호 문장, 선지는 번호
    mug = c.get("mugwan") if num == 35 else None
    if mug:
        step1_psg = mugwan_html(mug, step2=False)
        opt_lines = ('<span class="o">① ② ③ ④ ⑤ 중 <b>전체 흐름과 관계 없는 문장</b>의 번호를 고르시오.</span>')
    if num == 30:
        step1_psg = vocab_underline(step1_psg, c.get("opts", []))
    rt = c.get("restate")  # 재진술(추가 문제)
    _cue = contrast_cue(hl) if (rt and rt.get("kind") == "compare") else None
    rquiz = restate_problem(rt, _cue)

    left = f'''<div class="qproblem"><span class="wbm">wbspread</span>
    <div class="pbanner"><span class="no">{num}</span><span class="ty">{esc(typ)}</span>
      {'<span class="daepyo">⭐ 대표</span>' if c.get("daepyo") else ''}{'<span class="pt">'+pts+'</span>' if pts else ''}<span class="psrc">평가원 {exam_src(rec.get("exam_id",""))} {num}번</span><span class="step">STEP 1 · 직접 풀기 ✍️</span></div>
    <div class="pbody">
      <div class="pmain">
        <div class="how">{how}</div>
        <div class="psg work">{step1_psg}</div>
        <div class="pracopts"><div class="ttl">{esc(prompt)}</div>{summary_box(c.get("summary")) if num == 40 else ""}{opt_lines}</div>
      </div>
      <div class="pside">
        <div class="mini"><div class="h">{remind_label}</div>{chips}</div>
        <div class="mini"><div class="h">✅ 셀프 체크</div>
          <ul class="check">{checks}</ul>
        </div>
        <div class="memo"><div class="h">✍️ 내 풀이</div>
          <div class="row">걸린 시간 <span class="fill"></span></div>
          <div class="row">내가 고른 답 <span class="fill"></span></div>
          <div class="row">근거 문장(내 생각):<span class="big"></span></div>
        </div>
        <div class="ptip"><div class="h">💡 {esc(typ)} 팁</div>{esc(formula)}</div>
      </div>
    </div>
    {rquiz}
    {vocab_block(c.get("vlist", []))}
  </div>'''

    right = solution_block(rec, c, idx)
    return f'<div class="spread">{left}{right}</div>'


# ---------- 폴백(콘텐츠 없음): 간이 훈련 카드 ----------

def _fallback_hl(passage):
    sents = re.split(r'(?<=[.!?])\s+', passage.strip())
    out = []
    for s in sents:
        if not s.strip():
            continue
        low = s.lower()
        if re.search(SKIP_PAT, low):
            out.append(f'<span class="sk">{esc(s)}</span>'); continue
        hit = None
        for name, pat in SIGNALS.items():
            m = re.search(pat, s, re.I)
            if m:
                hit = (name, m.group(0)); break
        if hit:
            inner = _inline_tags(s, [{"sig": hit[0], "word": hit[1]}])
            out.append(f'<mark class="m">{inner}</mark>')
        else:
            out.append(esc(s))
    return " ".join(out)


def render_fallback(rec, idx):
    band = rec["band"]; typ = BAND_TITLE.get(band, rec.get("type", ""))
    num = rec["num"]; pts = f'{rec.get("points")}점' if rec.get("points") else ""
    ans = rec.get("answer"); choices = rec.get("choices") or {}
    ch = ""
    for k in sorted(int(x) for x in choices):
        cls = ' class="opt ok"' if ans == k else ' class="opt x"'
        jd = '<span class="jd">✔ 정답</span>' if ans == k else '<span class="jd"></span>'
        ch += f'<div{cls}><span class="n">{CIRCLED[k-1]}</span><span class="tx">{esc(choices[str(k)])}</span>{jd}</div>'
    formula = FORMULA.get(typ, "")
    return f'''<div class="card solo">
      <div class="hd"><span class="no">{num}</span><span class="ty">{esc(typ)}</span>
        {'<span class="pt">'+pts+'</span>' if pts else ''}<span class="kind">훈련(정답 칠)</span>
        <span class="tm">{esc(rec.get("exam_id",""))} · #{idx}</span></div>
      <div class="psg">{_fallback_hl(rec["passage"])}</div>
      <div class="opts">{ch}</div>
      <div class="formula"><span class="k">공식</span>{esc(formula)}</div>
    </div>'''


def band_divider(b, recs, seq, total_bands):
    """번호대 섹션 = 한 페이지 가득 채우는 유형 표지(공식·접근법·신호 리마인더)."""
    typ = BAND_TITLE.get(b, b)
    cnt = len(recs)
    formula = FORMULA.get(typ, "")
    tip = TYPE_TIP.get(b, "")
    chips = "".join(f'<span class="chip {cl}">{esc(tx)}</span>' for tx, cl in REMIND.get(b, REMIND["31-34"]))
    # 대표 번호 배지(번호대 첫 숫자)
    head_no = b.split("-")[0]
    seqmode = b in ("36-37", "38-39")
    if seqmode:
        stype = "순서" if b == "36-37" else "삽입"
        formula = "지시어·연결어·시간으로 조각을 잇는다 (노랑 형광펜 아님)"
        tip = ("각 조각의 <b>첫머리 지시어·연결어</b>가 어느 조각 뒤에 오는지로 사슬을 잇는다. 학생들이 가장 어려워하는 유형 — 지시어만 잡으면 풀린다."
               if stype == "순서" else
               "주어진 문장의 <b>지시어(this·they)</b>가 가리킬 선행어 자리, 그리고 <b>흐름이 끊긴 곳</b>을 찾는다. 지시어 추적이 열쇠다.")
        trap = ('<li>지시어 없는 조각 = 대개 <b>첫 번째</b>(주어진 글 바로 뒤)</li>'
                '<li>각 조각 <b>첫 단어</b>부터 확인 — 성급히 첫 조각 확정 금지</li>'
                '<li>연결어 <b>방향</b>(But 역접·also 첨가·so 인과) 어긋나면 오답</li>'
                if stype == "순서" else
                '<li>넣을 문장의 <b>지시어</b>부터 → 선행어 있는 위치 <b>뒤</b>만 후보</li>'
                '<li>넣기 <b>전·후 both</b> 읽어 흐름 끊김 확인</li>'
                '<li>연결어·지시어가 <b>갑자기 튀는</b> 곳이 정답</li>')
        attack = f'''
      <div class="bd-formula"><span class="k">유형 공식</span>{esc(formula)}</div>
      <div class="bd-tip"><span class="h">이렇게 접근한다</span>{tip}</div>
      <div class="bd-attack">
        <div class="atk">
          <div class="ah">🔎 지시어 잡는 법 — 이 유형의 열쇠</div>
          <ul>
            <li><b>this/that/these + 명사</b> → 바로 앞에 그 명사·개념이 있어야 함</li>
            <li><b>it/they/them</b> → 수(단·복수) 맞는 <b>가장 가까운 앞 명사</b></li>
            <li><b>such · the same · another</b> → '먼저 나온 것'이 전제</li>
            <li>핵심: <b>지시어는 늘 '앞'을 가리킨다.</b> 선행어가 앞에 없으면 그 자리엔 못 온다.</li>
          </ul>
        </div>
        <div class="atk trap">
          <div class="ah">🚫 오답 찍기 방지 체크</div>
          <ul>{trap}</ul>
        </div>
      </div>
      <div class="bd-drill">
        <div class="ah">✏️ 지시어 미니 드릴 — 밑줄이 가리키는 것은?</div>
        <div class="drow">Robots now handle many factory jobs. <u>These changes</u> worry some workers. <span class="ar">→</span> <span class="ans">robots handling factory jobs</span></div>
        <div class="drow">She solved the puzzle in seconds. <u>Such speed</u> amazed everyone. <span class="ar">→</span> <span class="ans">solving the puzzle in seconds</span></div>
        <div class="drow">The city built three new parks. <u>They</u> soon became popular. <span class="ar">→</span> <span class="ans">the three new parks</span></div>
      </div>'''
        body = attack
    else:
        body = f'''
      <div class="bd-formula"><span class="k">유형 공식</span>{esc(formula)}</div>
      <div class="bd-tip"><span class="h">이렇게 접근한다</span>{tip}</div>
      <div class="bd-steps">
        <div class="st"><span class="k">STEP 1</span><b>직접 풀기</b><span class="d">신호를 떠올리며 직접 형광펜을 치고 답을 고른다 (왼쪽 페이지)</span></div>
        <div class="st"><span class="k">STEP 2</span><b>훈련 · 정답 칠</b><span class="d">🟡읽을 문장·🔴칠한 근거 + 노랑만으로 정답 도출 + 선지 판정</span></div>
        <div class="st"><span class="k">STEP 3</span><b>직독직해</b><span class="d">슬래시(/)로 끊어 읽기 · 영↔한 청크 대응 (오른쪽 페이지)</span></div>
      </div>'''
    remind_head = "🔗 연결고리 단서" if seqmode else "📢 이 유형 신호 리마인더"
    return f'''<section class="banddiv"><span class="wbm">wbspread</span>
      <div class="bd-top">
        <span class="bd-seq">유형 {seq:02d} / {total_bands:02d}</span>
        <span class="bd-part">PART 1 · 유형별 훈련</span>
      </div>
      <div class="bd-hero">
        <div class="bd-no">{esc(head_no)}</div>
        <div class="bd-titlewrap">
          <div class="bd-ty">{esc(typ)}</div>
          <div class="bd-meta">{esc(b)}번대 · 실제 기출 <b>{cnt}문항</b></div>
        </div>
      </div>{body}
      <div class="bd-remind"><span class="h">{remind_head}</span><div class="chips">{chips}</div></div>
    </section>'''


def _op_piece(lab, seam_html, mid_html, hook_lb, hook_html, give=False):
    mid = f'<span class="op-mid">{mid_html}</span>' if mid_html else ""
    return (f'<div class="op-piece"><div class="op-lab{" give" if give else ""}">{lab}</div>'
            f'<div class="op-pc"><span class="op-seam">{seam_html}</span> {mid}'
            f'<div class="op-hook"><span class="op-lb">{hook_lb}</span>{hook_html}</div></div></div>')


def onepass_page(seqtype):
    """순서·삽입 유형 표지 앞에 오는 '한 번에 푸는 법(1-PASS)' 특강 1쪽."""
    if seqtype == "순서":
        title = "순서를 '한 번에' 푸는 법"
        steps = (
            '<div class="op-st"><span class="k">STEP 1</span><b>끝에서 갈고리 하나</b>'
            '<span class="d">주어진 글의 <b>끝</b>에서 “다음엔 반드시 ___가 와야 한다”를 <b>딱 하나</b>만 건다.</span></div>'
            '<div class="op-st"><span class="k">STEP 2</span><b>첫머리만 본다</b>'
            '<span class="d">(A)(B)(C)의 <b>첫 1~2문장</b>만. 몸통은 건너뛰고 <b>갈고리를 채우는 조각</b>을 고른다.</span></div>'
            '<div class="op-st"><span class="k">STEP 3</span><b>끝→첫머리 반복</b>'
            '<span class="d">고른 조각의 <b>끝</b>에서 새 갈고리 → 남은 첫머리에 맞춘다. 되돌아가지 않는다.</span></div>')
        demo_cap = '각 조각의 <b>첫머리(이음매)</b>만 진하게, <b>몸통</b>은 흐리게 표시했다. 순서는 <b>첫머리 단서</b>만으로 정해진다.'
        demo_src = "2024학년도 수능 37번"
        pieces = (
            _op_piece("주어진 글",
                      'Norms emerge in groups … Thus, the start of a norm occurs when one person acts …',
                      "", "갈고리",
                      "한 사람이 <b>'그 행동'을 시작</b> → 다음엔 <b>그 행동을 이어받는</b> 조각이 와야 함", give=True)
            + _op_piece("(C)",
                        'Others may then conform to <span class="op-clue ck-ref">this behavior</span> <span class="op-clue ck-time">then</span> …',
                        "The person who performed the initial action may think …", "이음매",
                        "<b>this behavior·then</b> = 주어진 글의 그 행동을 받음 <span class='op-ar'>→</span> <b>주어진 글 바로 뒤</b>")
            + _op_piece("(A)",
                        'Thus, she may prescribe the behavior to <span class="op-clue ck-ref">them</span> …',
                        "Alternately, she may communicate … In addition, she may threaten to sanction them …", "이음매",
                        "<b>them</b> = (C)의 'others' <span class='op-ar'>→</span> <b>(C) 뒤</b>")
            + _op_piece("(B)",
                        '<span class="op-clue ck-conj">But</span> some others will not need to have the behavior prescribed …',
                        "They will observe the regularity of behavior … either rational or moral reasons.", "이음매",
                        "<b>But</b> = (A)의 '규정하면 따른다'를 뒤집어 마무리 <span class='op-ar'>→</span> <b>(A) 뒤</b>"))
        path = ("읽은 것은 <b>이음매 4곳</b>뿐 (몸통 7문장은 안 읽음). &nbsp;주어진 글 <span class='op-arrow'>→</span> (C) "
                "<span class='op-arrow'>→</span> (A) <span class='op-arrow'>→</span> (B) &nbsp;∴ 정답 <b>(C)-(A)-(B)</b>")
    else:
        title = "문장 삽입을 '한 번에' 푸는 법"
        steps = (
            '<div class="op-st"><span class="k">STEP 1</span><b>넣을 문장 먼저 · 손잡이 둘</b>'
            '<span class="d"><b>뒤 손잡이</b>(지시어 this·they·But → 앞에 뭐가 있어야) + <b>앞 손잡이</b>(새 화제 → 뒤에 뭐가 와야).</span></div>'
            '<div class="op-st"><span class="k">STEP 2</span><b>한 번 훑어 끊긴 곳</b>'
            '<span class="d">본문을 <b>딱 한 번</b> 훑으며 <b>흐름이 끊긴 한 군데</b>(대명사가 받을 게 없거나 화제가 튀는 곳)를 찾는다.</span></div>'
            '<div class="op-st"><span class="k">STEP 3</span><b>끊긴 자리 = 정답</b>'
            '<span class="d">손잡이를 쥐고 들어가니 <b>다섯 자리를 시험하지 않는다.</b></span></div>')
        demo_cap = '<b>넣을 문장</b>의 손잡이(지시어)를 먼저 뽑고, 본문에서 <b>흐름이 끊긴 한 곳</b>만 찾는다.'
        demo_src = "2024학년도 6월 39번"
        pieces = (
            _op_piece("넣을 문장",
                      '<span class="op-clue ck-ref">As a result, they</span> are fit and grow better, but they aren’t particularly long-lived.',
                      "", "손잡이",
                      "<b>they</b> = 앞의 'Some individuals'(홀로 광합성하는 그 나무들) → <b>그 문장 뒤</b>에 놓여야", give=True)
            + _op_piece("① 앞 문장",
                        'Some individuals photosynthesize like mad until sugar positively bubbles …',
                        "", "이음매",
                        "여기서 <b>흐름이 끊김</b> — 'they'가 받을 대상이 바로 여기 <span class='op-ar'>→</span> <b>이 뒤(②)가 자리</b>")
            + _op_piece("② 뒤 문장",
                        '<span class="op-clue ck-ref">This</span> is because a tree can be only as strong as the forest …',
                        "", "이음매",
                        "<b>This</b> = 넣을 문장의 '오래 못 산다'는 결과 <span class='op-ar'>→</span> 그 이유를 이어 <b>공백을 메움</b>"))
        path = ("<b>넣을 문장</b>의 they를 쥐고 본문을 한 번 훑자 <b>② 자리</b>에서 딱 걸림 (다섯 자리 안 넣어봄). &nbsp;∴ 정답 <b>②</b>")

    demo = (f'<div class="op-demo"><div class="op-cap">{demo_cap} '
            f'<span class="op-srcnote">({demo_src})</span></div>'
            f'<div class="op-legend">단서 색: <span class="op-clue ck-ref">지시어</span>'
            f'<span class="op-clue ck-time">시간·순서</span><span class="op-clue ck-conj">연결어</span></div>'
            f'<div class="op-pass">{pieces}</div>'
            f'<div class="op-path">{path}</div></div>')
    habits = (
        '<ol><li><b>묻는 것 먼저</b> — 주어진 글·넣을 문장부터. 갈고리를 쥐고 본문에 들어가면 되돌아갈 일이 없다.</li>'
        '<li><b>몸통 말고 이음매</b> — 조각의 끝과 다음 첫머리만. 가운데 문장은 순서 판단에 필요 없다.</li>'
        '<li><b>눈으로 외우지 말고 손으로 표시</b> — 지시어→선행어를 화살표로 그으며 간다.</li></ol>')
    return f'''<section class="onepass"><span class="wbm">wbspread</span>
      <div class="op-top"><span class="op-badge">1-PASS</span><h1>{title}</h1>
        <span class="op-sub">형광펜 독해 · 유형 특강</span></div>
      <div class="op-diag">왜 자꾸 <b>여러 번 읽게</b> 될까? — 조각의 <b>'내용'</b>을 이해하려 읽기 때문.
        순서·삽입은 이해 문제가 아니라 <b>'어디에 붙나'를 잇는 문제</b>다.
        읽는 목적을 <b>“무슨 말이지?” → “어디에 붙지?”</b> 로 바꾸면 <b>한 번의 전진 읽기</b>로 끝난다.</div>
      <div class="op-h2">{"순서" if seqtype=="순서" else "삽입"} — 한 번에 푸는 3단계</div>
      <div class="op-steps">{steps}</div>
      <div class="op-h2">시범 — {"몸통은 넘기고 '이음매'만 따라간다" if seqtype=="순서" else "손잡이 뽑고 '끊긴 곳' 한 번에"}</div>
      {demo}
      <div class="op-h2">재독을 없애는 습관 3</div>
      <div class="op-habit">{habits}</div>
    </section>'''


DAEPYO = ["2022-06|21", "2022-06|34"]  # 대표 문항 — 유형편 각 유형 맨 앞에 배치


def build(n=80):
    bank = [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]
    bankmap = {f'{r["exam_id"]}|{r["num"]}': r for r in bank}
    picked = select(bank, n)
    pk = {f'{r["exam_id"]}|{r["num"]}' for r in picked}
    for k in DAEPYO:  # 대표 강제 포함
        if k not in pk and k in bankmap:
            picked.append(bankmap[k]); pk.add(k)
    content = {}
    if CONTENT.exists():
        for c in json.loads(CONTENT.read_text(encoding="utf-8")):
            content[c.get("key")] = c
    if CONNECT.exists():
        for c in json.loads(CONNECT.read_text(encoding="utf-8")):
            _CONNECT[c.get("key")] = c
    groups = {}
    for r in picked:
        groups.setdefault(r["band"], []).append(r)
    for b in groups:  # 대표를 각 유형 맨 앞으로
        groups[b].sort(key=lambda r: 0 if f'{r["exam_id"]}|{r["num"]}' in DAEPYO else 1)
    present_bands = [b for b in BAND_ORDER if b in groups]
    body, idx, full = [], 0, 0
    for si, b in enumerate(present_bands, 1):
        if b == "36-37":
            body.append(onepass_page("순서"))
        elif b == "38-39":
            body.append(onepass_page("삽입"))
        body.append(band_divider(b, groups[b], si, len(present_bands)))
        for r in groups[b]:
            idx += 1
            key = f'{r["exam_id"]}|{r["num"]}'
            c = content.get(key)
            if c and c.get("hl"):
                body.append(render_spread(r, c, idx)); full += 1
            else:
                body.append(render_fallback(r, idx))
    doc = TEMPLATE.replace("{{BODY}}", "\n".join(body)).replace("{{N}}", str(idx)).replace("{{FULL}}", str(full))
    OUT.write_text(doc, encoding="utf-8")
    print(f"워크북 생성: {idx}문항(대표형 {full} · 폴백 {idx-full}) → {OUT}")


TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>유형별 훈련</title><style>
@page{ size:A4; margin:10mm 11mm; }
*{ box-sizing:border-box; }
body{ font-family:"Liberation Serif","DejaVu Serif","NanumSquareRound",serif; color:#23272e; font-size:10px; line-height:1.5; margin:0; background:#fff; }
:root{ --ink:#1f7a5c; --ink-d:#12543d; --src:#e9f4ef; --src-line:#1f7a5c; --trap:#cd5049;
  --must:#ffe9a8; --must-line:#e0b94a; --skip:#9aa0a6; --muted:#6b7280; --line:#e6e8ea; }
/* PART 1 표지 — 한 페이지 가득 채우는 히어로 */
.cover{ height:275mm; display:flex; flex-direction:column; justify-content:center; color:#fff; text-align:center;
  background:linear-gradient(160deg,#12543d 0%, #1f7a5c 72%, #2a916d 100%); border-radius:10px; padding:0 22mm; break-after:page; }
.cover .kick{ font-size:13px; font-weight:800; letter-spacing:3px; opacity:.85; margin-bottom:10px; }
.cover .t{ font-size:44px; font-weight:800; line-height:1.15; }
.cover .n{ display:inline-block; background:var(--must); color:#12543d; font-weight:800; border-radius:8px; padding:2px 12px; }
.cover .rule{ width:64mm; height:4px; background:var(--must); border-radius:3px; margin:20px auto; }
.cover .s{ font-size:13px; line-height:1.9; opacity:.95; max-width:150mm; margin:0 auto; }
.cover .legend{ margin-top:22px; font-size:12px; opacity:.92; }
.cover .legend b{ color:var(--must); }

/* 번호대 유형 표지 — 한 페이지 가득 */
.banddiv{ height:274mm; display:flex; flex-direction:column; break-before:page; break-inside:avoid; padding:5mm 3mm; }
/* 1-PASS 특강 페이지 (순서·삽입 표지 앞) */
.onepass{ break-before:page; break-inside:avoid; padding:4mm 3mm; }
.onepass .op-top{ display:flex; align-items:center; gap:10px; border-bottom:3px solid var(--ink); padding-bottom:8px; margin-bottom:12px; }
.op-badge{ background:var(--ink); color:#fff; font-weight:800; font-size:12px; padding:3px 12px; border-radius:8px; }
.onepass h1{ font-size:19px; font-weight:800; color:var(--ink-d); margin:0; }
.op-sub{ margin-left:auto; font-size:10.5px; color:var(--muted); }
.op-diag{ font-size:12px; line-height:1.65; background:#fff7ef; border:1px solid var(--must-line); border-radius:8px; padding:9px 13px; margin-bottom:13px; }
.op-diag b{ color:#a8641a; }
.op-h2{ font-size:13.5px; font-weight:800; color:var(--ink-d); margin:0 0 8px; padding-left:9px; border-left:5px solid var(--ink); }
.op-steps{ display:flex; gap:10px; margin-bottom:14px; }
.op-steps .op-st{ flex:1; background:#fff; border:1.5px solid var(--line); border-top:4px solid var(--ink); border-radius:9px; padding:10px 12px; }
.op-steps .op-st .k{ display:inline-block; font-size:10px; font-weight:800; color:#fff; background:var(--ink-d); border-radius:6px; padding:2px 9px; margin-bottom:6px; }
.op-steps .op-st b{ display:block; font-size:12.5px; color:var(--ink-d); margin-bottom:4px; }
.op-steps .op-st .d{ font-size:11px; line-height:1.55; color:#48525c; }
.op-demo{ border:1.5px solid #cfe0d9; border-radius:10px; padding:11px 15px 6px; margin-bottom:14px; background:#fbfdfc; }
.op-cap{ font-size:11px; color:var(--muted); margin-bottom:7px; } .op-cap b{ color:var(--ink-d); } .op-srcnote{ color:#8a929b; }
.op-legend{ font-size:9.5px; color:#5a636c; margin-bottom:5px; }
.op-clue{ color:#fff; font-weight:700; padding:0 4px; border-radius:3px; margin:0 1px; }
.op-clue.ck-ref{ background:#2f6fb0; } .op-clue.ck-conj{ background:#cd5049; } .op-clue.ck-time{ background:#1f7a5c; }
.op-pass{ font-size:12px; line-height:1.75; }
.op-piece{ display:flex; gap:9px; padding:6px 0; border-bottom:1px dashed #dbe6e1; }
.op-piece:last-child{ border-bottom:none; }
.op-lab{ flex:none; width:56px; height:fit-content; text-align:center; font-weight:800; font-size:10px; color:#1f4d7a; background:#e2eefa; border-radius:6px; padding:4px 3px; }
.op-lab.give{ color:var(--ink-d); background:#e2efe9; }
.op-pc{ flex:1; min-width:0; }
.op-seam{ font-family:'NanumSquareRound',sans-serif; font-weight:600; }
.op-mid{ font-family:'NanumSquareRound',sans-serif; color:#aab0b6; font-size:10.5px; }
.op-hook{ font-size:10.5px; color:#1f4d7a; margin-top:3px; }
.op-hook .op-lb{ display:inline-block; font-size:8.5px; font-weight:800; color:#fff; background:#2f6fb0; border-radius:8px; padding:1px 7px; margin-right:5px; }
.op-hook b{ color:var(--ink-d); } .op-ar{ color:#9bb4cc; font-weight:800; margin:0 4px; }
.op-path{ margin-top:9px; background:#eef4f1; border-left:4px solid var(--ink); border-radius:7px; padding:9px 13px; font-size:12px; line-height:1.6; }
.op-path b{ color:var(--ink-d); } .op-path .op-arrow{ color:var(--ink); font-weight:800; }
.op-habit{ background:#fff; border:1.5px solid var(--line); border-radius:9px; padding:6px 16px; }
.op-habit ol{ margin:6px 0; padding-left:18px; } .op-habit li{ font-size:11.5px; line-height:1.65; margin-bottom:5px; }
.op-habit li b{ color:var(--ink-d); }
.bd-top{ display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid var(--ink); padding-bottom:7px; }
.bd-top .bd-seq{ font-size:12px; font-weight:800; color:#fff; background:var(--ink); border-radius:6px; padding:3px 12px; }
.bd-top .bd-part{ font-size:11px; font-weight:800; color:var(--ink-d); letter-spacing:1px; }
.bd-hero{ display:flex; align-items:center; gap:20px; margin:22mm 0 14mm; }
.bd-hero .bd-no{ font-size:64px; font-weight:800; color:#fff; background:linear-gradient(150deg,var(--ink-d),var(--ink)); border-radius:16px; width:118px; height:118px; line-height:118px; text-align:center; flex:none; box-shadow:0 4px 14px rgba(18,84,61,.28); }
.bd-hero .bd-ty{ font-size:40px; font-weight:800; color:var(--ink-d); line-height:1.1; }
.bd-hero .bd-meta{ font-size:15px; color:var(--muted); margin-top:8px; } .bd-hero .bd-meta b{ color:var(--ink-d); }
.bd-formula{ font-size:14px; font-weight:800; color:var(--ink-d); background:#e9f4ef; border:2px solid var(--ink); border-radius:9px; padding:12px 16px; margin-bottom:11px; }
.bd-formula .k{ display:inline-block; background:var(--ink); color:#fff; font-size:11px; padding:2px 10px; border-radius:9px; margin-right:9px; vertical-align:2px; }
.bd-tip{ font-size:13.5px; line-height:1.75; color:#2b3a34; background:#fffdf3; border:1px solid var(--must-line); border-radius:9px; padding:12px 16px; margin-bottom:14px; }
.bd-tip .h{ display:block; font-size:11px; font-weight:800; color:#a86b00; margin-bottom:4px; } .bd-tip b{ color:var(--ink-d); }
.bd-steps{ display:flex; gap:11px; margin-bottom:14px; }
.bd-steps .st{ flex:1; background:#fff; border:1.5px solid var(--line); border-top:4px solid var(--ink); border-radius:9px; padding:11px 13px; }
.bd-steps .st .k{ display:inline-block; font-size:10px; font-weight:800; color:#fff; background:var(--ink-d); border-radius:6px; padding:2px 9px; margin-bottom:6px; }
.bd-steps .st b{ display:block; font-size:14px; color:var(--ink-d); margin-bottom:5px; }
.bd-steps .st .d{ font-size:11px; line-height:1.55; color:var(--muted); }
.bd-attack{ display:flex; gap:11px; margin-bottom:13px; }
.bd-attack .atk{ flex:1; background:#fff; border:1.5px solid var(--line); border-radius:9px; padding:11px 14px 12px; }
.bd-attack .atk.trap{ background:#fdf3f2; border-color:#e6bcb7; }
.bd-attack .ah{ font-size:12px; font-weight:800; color:var(--ink-d); margin-bottom:7px; }
.bd-attack .atk.trap .ah{ color:#b3453b; }
.bd-attack .atk ul{ margin:0; padding-left:16px; }
.bd-attack .atk li{ font-size:11.5px; line-height:1.68; color:#33414d; margin-bottom:4px; }
.bd-attack .atk li b{ color:var(--ink-d); } .bd-attack .atk.trap li b{ color:#b3453b; }
.bd-drill{ background:#f3f8ff; border:1.5px solid #cadcf0; border-radius:9px; padding:11px 15px 12px; margin-bottom:14px; }
.bd-drill .ah{ font-size:12px; font-weight:800; color:#2f6fb0; margin-bottom:8px; }
.bd-drill .drow{ font-size:12px; line-height:1.5; color:#2b3a34; padding:5px 0; border-bottom:1px dashed #d3e2f1; }
.bd-drill .drow:last-child{ border-bottom:none; }
.bd-drill .drow u{ color:#2f6fb0; text-decoration-color:#8ab3dc; font-weight:700; }
.bd-drill .drow .ar{ color:#9bb4cc; font-weight:800; margin:0 5px; }
.bd-drill .drow .ans{ display:inline-block; background:#e2eefa; color:#1f4e79; font-weight:700; border-radius:6px; padding:1px 8px; }
.bd-remind{ margin-top:auto; background:#eef4f1; border-radius:9px; padding:12px 16px; }
.bd-remind .h{ display:block; font-size:12px; font-weight:800; color:var(--ink-d); margin-bottom:7px; }
.bd-remind .chip{ font-size:11.5px; padding:2px 10px; }
@media print{
  .spread{ display:block; }
  /* 워크북은 유형 표지(1쪽)가 좌우 짝을 깨므로 강제 좌/우 정렬을 쓰지 않는다
     → 표지·문제·해설이 빈 페이지 없이 연달아 흐르도록 break-before:page 만 사용 */
  /* 한 문항 = 3면 나눔:  ① 문제(+재진술 연결 문제)  ② 훈련(정답 칠)  ③ 해석(직독직해)+재진술 정답 */
  .qproblem{ break-before:page; break-inside:avoid; }        /* ① 문제면 */
  .qsolution{ break-before:page; }                            /* ② 훈련(STEP2)면 시작 */
  .qsolution .card.trans{ break-before:page; }                /* ③ 해석면 시작(STEP3+재진술은 같은 면) */
  .qsolution .card{ break-inside:avoid; }
  .card.solo{ break-inside:avoid; }
}
.spread{ margin-bottom:6px; }
.wbm{ font-size:2px; color:#fff; line-height:0; }

/* 카드 공통 */
.card{ background:#fff; border-radius:8px; box-shadow:0 1px 6px rgba(0,0,0,.1); padding:12px 15px; margin-bottom:10px; }
.card.solo{ border:1px solid var(--line); }
.hd{ display:flex; align-items:center; gap:8px; border-bottom:2px solid var(--ink-d); padding-bottom:6px; margin-bottom:8px; }
.hd .no{ background:var(--ink-d); color:#fff; font-weight:800; font-size:12px; padding:2px 9px; border-radius:5px; }
.hd .ty{ font-weight:800; font-size:13px; color:var(--ink-d); }
.hd .kind{ font-size:9px; font-weight:700; color:var(--ink); border:1px solid var(--ink); border-radius:9px; padding:1px 8px; }
.hd .pt{ font-size:9px; font-weight:700; color:#fff; background:var(--trap); padding:1px 7px; border-radius:9px; }
.hd .tm{ margin-left:auto; font-size:9px; font-weight:700; color:var(--muted); }
.psg{ font-size:11px; line-height:1.85; border:1px solid var(--line); border-radius:6px; padding:9px 11px; margin-bottom:8px; }
mark.m{ background:var(--must); padding:0 2px; border-radius:2px; }
mark.g{ background:var(--src); padding:0 2px; border-radius:2px; }
.ynum{ font-size:10px; font-weight:800; color:#b3610d; margin-right:1px; vertical-align:0.5px; }
.uph{ text-decoration:underline; text-decoration-thickness:1.6px; text-underline-offset:2.5px; text-decoration-color:#12543d; font-weight:700; }
.color-legend{ display:flex; align-items:center; flex-wrap:wrap; gap:5px; margin-bottom:6px; font-size:8.2px; color:#4b5560; }
.color-legend .clh{ font-weight:800; color:#33414d; margin-right:2px; }
.color-legend .cl{ display:inline-flex; align-items:center; gap:3px; padding:1px 6px; border-radius:9px; font-weight:700; }
.color-legend .cl b{ font-weight:800; color:#2b3540; }
.color-legend .cl.m{ background:var(--must); }
.color-legend .cl.g{ background:var(--src); }
.color-legend .cl.sk{ background:#eef0f2; color:#8a929b; } .color-legend .cl.sk b{ color:#7a828b; }
.sk{ color:var(--skip); }
.bk{ display:inline-block; min-width:60px; border-bottom:2px solid #111; }
/* 무관한 문장(35) 번호 매기기 */
.mgn{ display:inline-block; font-size:9.5px; font-weight:800; color:#fff; background:var(--ink-d); border-radius:50%; width:15px; height:15px; line-height:15px; text-align:center; margin:0 3px 0 2px; vertical-align:1px; }
.mg-intro{ font-weight:600; }
.mg-x{ background:#fdecea; border-bottom:2px solid var(--trap); border-radius:2px; padding:0 2px; }
.mg-xt{ font-size:7.5px; font-weight:800; color:#fff; background:var(--trap); border-radius:7px; padding:0 5px; margin-left:4px; vertical-align:1px; }
.tag{ font-size:7.5px; font-weight:800; color:#fff; background:var(--trap); border:1px solid var(--trap); border-radius:3px; padding:0 4px; vertical-align:1px; margin:0 1px; }
.tag.hot{ color:#fff; background:var(--trap); border-color:var(--trap); }
.tag.pos{ color:#7a5c00; background:var(--must); border-color:var(--must-line); }
/* 논리 관계어 태그(파랑 계열) — 빨강 '근거 신호'와 구분 */
.tag.rel{ color:#fff; border:none; }
.tag.rel.cause{ background:#1f7a5c; } .tag.rel.eq{ background:#2f6fb0; } .tag.rel.contr{ background:#0f766e; } .tag.rel.comp{ background:#b8860b; } .tag.rel.repl{ background:#64748b; }
u.ru{ text-decoration:underline; text-decoration-thickness:1.4px; text-underline-offset:2px; font-weight:600; }
u.ru.cause{ text-decoration-color:#1f7a5c; } u.ru.eq{ text-decoration-color:#2f6fb0; } u.ru.contr{ text-decoration-color:#0f766e; } u.ru.comp{ text-decoration-color:#b8860b; } u.ru.repl{ text-decoration-color:#64748b; }
/* ±(긍정/부정) 어휘 — 콤팩트한 ＋/− 부호 + 밑줄 */
u.pu{ text-decoration:underline; text-decoration-thickness:1.4px; text-underline-offset:2px; font-weight:600; }
u.pu.pl{ text-decoration-color:#1f7a5c; } u.pu.mn{ text-decoration-color:#b3453b; }
.pm{ font-size:7.5px; font-weight:800; vertical-align:3px; }
.pm.pl{ color:#12543d; } .pm.mn{ color:#a5342d; }
.reconnote{ font-size:8.2px; color:#8a6a00; background:#fffdf3; border:1px dashed var(--must-line); border-radius:5px; padding:4px 8px; margin-top:6px; }
.psg .rep{ text-decoration:underline; text-decoration-color:#c99a2e; text-decoration-thickness:1.4px; text-underline-offset:2px; font-weight:700; }
.rk{ background:#f4b8b2; color:#7a1f19; font-weight:700; padding:0 2px; border-radius:2px; box-shadow:inset 0 -2px 0 #d98b84; }

/* 문제 페이지(왼쪽) */
.pbanner{ background:linear-gradient(100deg,var(--ink-d),var(--ink)); color:#fff; border-radius:9px 9px 0 0; padding:11px 15px; display:flex; align-items:center; gap:9px; }
.pbanner .no{ background:#fff; color:var(--ink-d); font-weight:800; font-size:15px; padding:2px 11px; border-radius:6px; }
.pbanner .ty{ font-size:15px; font-weight:800; }
.pbanner .pt{ font-size:9px; font-weight:700; background:var(--trap); padding:1px 8px; border-radius:9px; }
.pbanner .psrc{ font-size:9px; font-weight:700; color:#12543d; background:#ffe9a8; padding:2px 9px; border-radius:9px; }
.pbanner .daepyo{ font-size:9px; font-weight:800; color:#fff; background:#cd5049; padding:2px 9px; border-radius:9px; }
.pbanner .step{ margin-left:auto; font-size:9px; font-weight:800; background:rgba(255,255,255,.18); padding:3px 10px; border-radius:11px; }
.pbody{ border:2px solid var(--ink-d); border-top:none; border-radius:0 0 9px 9px; padding:15px 17px 13px; display:flex; gap:15px; min-height:360px; }
.pmain{ flex:2; display:flex; flex-direction:column; }
.pside{ flex:1; border-left:1.5px dashed var(--line); padding-left:13px; }
.how{ font-size:9px; color:#8a6a00; background:var(--must); border-radius:5px; padding:7px 10px; margin-bottom:10px; font-weight:700; }
.psg.work{ font-size:11.5px; line-height:2.15; border:none; padding:0; }
.pracopts{ font-size:9.6px; line-height:1.85; margin-top:9px; padding:8px 11px; background:#fff; border:1px dashed var(--must-line); border-radius:5px; }
.pracopts .o{ display:block; }
.pracopts .ttl{ font-size:8.7px; font-weight:800; color:#a86b00; margin-bottom:3px; }
/* 요약문(40) 요약 문장 박스 */
.sumbox{ margin:5px 0 7px; padding:7px 10px; background:#f4faf7; border:1.5px solid var(--ink); border-radius:6px; }
.sumbox .sh{ font-size:8px; font-weight:800; color:var(--ink-d); margin-bottom:3px; }
.sumbox .sent{ font-size:10px; line-height:1.75; color:#23272e; }
.sbk{ display:inline-block; min-width:34px; text-align:center; font-weight:800; color:#a86b00; border-bottom:1.4px solid var(--must-line); background:#fff7e6; border-radius:3px; padding:0 6px; margin:0 2px; }
.sfa,.sfb{ display:inline-block; font-weight:800; color:#12543d; background:var(--must); border-radius:3px; padding:0 5px; margin:0 2px; }
.dchl .sumbox{ margin:0 0 8px; }
.pguide{ margin-top:auto; background:#e9f4ef; border:1px solid var(--ink); border-radius:7px; padding:9px 12px; }
.pguide .h{ font-size:9.5px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.pguide .g3{ display:flex; gap:8px; }
.pguide .g3 .s{ flex:1; font-size:8.6px; line-height:1.4; }
.pguide .g3 .k{ display:inline-block; width:15px; height:15px; line-height:15px; text-align:center; background:var(--ink); color:#fff; border-radius:50%; font-size:8.5px; font-weight:800; margin-right:3px; }
.ptip{ margin-top:11px; background:#fff7ed; border:1px solid #f0c48a; border-radius:6px; padding:8px 10px; font-size:8.8px; color:#8a5a1a; }
.ptip .h{ font-weight:800; color:#b3610d; margin-bottom:2px; }
.mini{ margin-bottom:11px; }
.mini .h{ font-size:9px; font-weight:800; color:var(--ink-d); margin-bottom:4px; border-bottom:1px solid var(--line); padding-bottom:2px; }
.chip{ display:inline-block; font-size:8.2px; font-weight:700; border-radius:9px; padding:1px 7px; margin:0 3px 3px 0; border:1px solid; }
.chip.y{ color:#a86b00; border-color:var(--must-line); background:#fffdf3; }
.chip.g{ color:var(--skip); border-color:#d5d9dd; background:#fafafa; }
.check{ list-style:none; margin:0; padding:0; font-size:8.8px; }
.check li{ margin-bottom:4px; padding-left:17px; position:relative; line-height:1.35; }
.check li::before{ content:"☐"; position:absolute; left:0; font-size:11px; color:var(--ink); }
.memo{ margin-top:10px; background:#eef4f1; border:1px solid var(--line); border-radius:6px; padding:8px 10px; }
.memo .h{ font-size:9px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.memo .row{ font-size:9px; margin-bottom:6px; color:#4a5560; }
.memo .fill{ display:inline-block; min-width:38px; border-bottom:1.5px solid var(--ink); margin:0 4px; }
.memo .big{ display:block; height:24px; border-bottom:1px dotted #b9cfc6; }

/* 도출/판정 */
.derive{ margin-top:6px; background:#fffdf3; border:1px solid var(--must-line); border-radius:6px; padding:9px 12px; }
.derive .dh{ font-size:9.3px; font-weight:800; color:#8a6a00; margin-bottom:6px; }
.derive ol{ margin:0 0 6px; padding:0; list-style:none; }
.derive li{ font-size:9.5px; line-height:1.55; margin-bottom:4px; padding-left:42px; position:relative; }
.derive li .yb{ position:absolute; left:0; top:1px; font-size:7.5px; font-weight:800; color:#7a5c00; background:var(--must); border:1px solid var(--must-line); border-radius:7px; padding:1px 5px; }
.derive li u{ text-decoration:none; background:var(--must); padding:0 2px; border-radius:2px; font-weight:700; }
.derive li .an{ color:var(--muted); font-size:8.7px; }
.derive li .yanch{ display:block; font-size:8.8px; color:#8a6a00; background:#fff6d8; border-radius:3px; padding:1px 5px; margin-bottom:2px; font-style:italic; }
.derive li .ystep{ display:block; }
.derive .concl{ font-size:9.6px; font-weight:700; color:#23272e; background:#eaf5f0; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:6px 10px; margin-top:2px; }
.derive .concl b{ color:var(--ink-d); }
.derive .gnote{ font-size:8.6px; color:var(--muted); margin-top:5px; padding-left:2px; }
/* 순서·삽입 연결고리 풀이 (노랑 대신 파랑 계열) */
.derive.connect{ background:#f2f7fc; border-color:#a9c8e8; }
.derive.connect .dh{ color:#2f5f92; } .derive.connect .dh b{ color:#1f4d7a; }
.derive.connect .clues{ margin-bottom:6px; }
.derive.connect .clue{ display:flex; gap:5px; align-items:baseline; font-size:9.2px; line-height:1.5; margin-bottom:2px; }
.derive.connect .clue .cw{ flex:none; font-weight:800; color:#1f4d7a; background:#dcebf9; border-radius:3px; padding:0 4px; }
.derive.connect .clue .ck{ flex:none; font-size:7.4px; font-weight:800; color:#fff; border-radius:8px; padding:0 6px; }
.ck-ref{ background:#2f6fb0; } .ck-conj{ background:#cd5049; } .ck-time{ background:#1f7a5c; } .ck-echo{ background:#8a6a00; }
/* 지문 속 연결고리 색칠(순서·삽입) */
.psg .pclue{ color:#fff; font-weight:700; padding:0 3px; border-radius:3px; }
.pclue{ font-size:7.4px; font-weight:800; color:#fff; border-radius:8px; padding:0 6px; }
.clue-legend{ font-size:8.2px; color:#33414d; margin-bottom:5px; }
.clue-legend .pclue{ margin-right:3px; }
/* 삽입 문항 — 삽입할 문장을 본문과 띄워 구분 */
.psg .insbox{ background:#eef4fb; border:1px solid #c3d8ee; border-left:4px solid #2f6fb0; border-radius:6px; padding:6px 10px; margin-bottom:11px; }
.psg .insbox .inslab{ display:inline-block; font-size:8px; font-weight:800; color:#fff; background:#2f6fb0; border-radius:9px; padding:1px 8px; margin-right:7px; vertical-align:1.5px; }
.psg .insbox .instext{ font-weight:600; }
.psg .insbody{ }
.psg.work .insbox{ background:#f4f7fb; }
.derive.connect .clue .cn{ flex:1; color:#33414d; }
.derive.connect ol.chain{ margin:4px 0 6px; }
.derive.connect ol.chain li{ padding-left:20px; font-size:9.4px; }
.derive.connect ol.chain li .ln{ position:absolute; left:0; top:1px; width:14px; height:14px; line-height:14px; text-align:center; background:#2f6fb0; color:#fff; border-radius:50%; font-size:8px; font-weight:800; }
.derive.connect .concl{ background:#e6f0f9; border-left-color:#2f6fb0; } .derive.connect .concl b{ color:#1f4d7a; }
.pline{ margin-top:6px; background:#eef4f1; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:5px 9px; font-size:9.3px; }
.pline .lb{ font-size:8px; font-weight:800; color:#fff; background:var(--ink); border-radius:8px; padding:1px 6px; margin-right:5px; }
.pline .sw{ background:#dbe7e0; border-radius:3px; padding:0 4px; font-weight:700; color:var(--ink-d); }
.pline .cp{ background:#ffe0dd; border-radius:3px; padding:0 4px; font-weight:700; color:#a5342d; }
.pline .arw{ color:var(--ink); font-weight:800; }
.opts{ margin-top:7px; border-top:1px dashed var(--line); padding-top:7px; }
.opt{ display:flex; gap:6px; align-items:baseline; font-size:9.5px; margin-bottom:3px; }
.opt .n{ flex:none; font-weight:800; width:14px; } .opt .txwrap{ flex:1; } .opt .tx{ display:inline; } .opt .jd{ flex:none; font-size:8.6px; font-weight:800; }
.opt .oko{ display:block; font-size:8.8px; color:#5a6169; margin-top:1px; line-height:1.4; }
.opt.ok .oko{ color:#12543d; }
.opt.ok{ background:#dff0e8; border:1.5px solid var(--ink); border-radius:5px; padding:3px 6px; } .opt.ok .jd{ color:var(--ink-d); } .opt.x .jd{ color:var(--trap); }
/* 정답 선지: 동그라미 번호를 초록 채움 + '정답' 배지 */
.opt.ok .n{ color:#fff; background:var(--ink); border-radius:50%; width:15px; height:15px; line-height:15px; text-align:center; font-size:10px; }
.opt.ok .tx{ font-weight:800; }
.opt .okflag{ flex:none; font-size:8px; font-weight:800; color:#fff; background:var(--ink); border-radius:3px; padding:1px 5px; margin:0 5px; }
.opt.x{ opacity:.92; }
/* 정답 배너 */
.ans-head{ display:flex; align-items:center; gap:7px; font-size:11px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.ans-head .ansno{ display:inline-block; min-width:20px; height:20px; line-height:20px; text-align:center; color:#fff; background:var(--ink); border-radius:50%; font-size:13px; font-weight:800; }
.reuse{ background:#ffe0dd; border-radius:2px; padding:0 2px; font-weight:700; color:#a5342d; }
/* 어휘(30) 밑줄 */
u.vund{ text-decoration:underline; text-decoration-thickness:1.5px; text-underline-offset:2px; font-weight:700; }
/* 핵심 어휘·숙어 박스 (STEP3 하단) */
.vocabox{ margin-top:9px; border:1px solid var(--src-line); border-radius:6px; background:#f4faf7; padding:7px 9px; break-inside:avoid; }
.vocabox .vh{ font-size:9.6px; font-weight:800; color:var(--ink-d); margin-bottom:5px; }
.vgrid{ display:grid; grid-template-columns:1fr 1fr; gap:2px 16px; }
.vitem{ display:flex; gap:6px; font-size:9px; line-height:1.5; align-items:baseline; }
.vitem .vw{ font-weight:700; color:#12543d; }
.vitem .vm{ color:#3a4148; flex:1; }
.formula{ margin-top:8px; background:#e9f4ef; border:1.5px solid var(--ink); border-radius:6px; padding:6px 10px; font-weight:800; color:var(--ink-d); font-size:9.6px; }
.formula .k{ background:var(--ink); color:#fff; font-size:8px; padding:1px 6px; border-radius:8px; margin-right:6px; }

/* 직독직해 */
.card.trans{ border-left:5px solid var(--src-line); }
.dchl .kt{ display:block; font-weight:800; color:var(--src-line); font-size:8.8px; margin:2px 0 5px; }
.dchl .row{ margin-bottom:7px; padding-left:19px; position:relative; }
.dchl .bn{ position:absolute; left:0; top:1px; width:14px; height:14px; line-height:14px; text-align:center; background:var(--src-line); color:#fff; border-radius:50%; font-size:8px; font-weight:800; }
.dchl .en{ font-size:10.2px; line-height:1.95; color:#23272e; }
.dchl .ko{ font-size:9.6px; line-height:1.95; color:#23272e; margin-top:2px; }
.dchl .sl{ color:#b3beb6; font-weight:400; padding:0 1px; }
.hl0,.hl1,.hl2,.hl3,.hl4{ color:#23272e; padding:1px 4px; border-radius:3px; box-decoration-break:clone; -webkit-box-decoration-break:clone; }
.hl0{ background:#c9e0ec; } .hl1{ background:#c7e0da; } .hl2{ background:#e8dfb2; } .hl3{ background:#e2dac8; } .hl4{ background:#d5ddb9; }
.dchl .opt-line{ margin-top:7px; padding-top:7px; border-top:1px dashed var(--line); font-size:9.3px; }
.dchl .opt-line .co{ color:var(--src-line); font-weight:800; } .dchl .opt-line .xo{ color:var(--trap); font-weight:700; }
/* 무관(35) 다섯 문장 해석카드 */
.dchl .bn.bn-i{ width:auto; padding:0 5px; border-radius:7px; font-size:7.6px; }
.dchl .row.mgirr{ background:#fdecea; border-radius:5px; padding:4px 6px 4px 21px; margin-left:-2px; }
.dchl .row.mgirr .bn.irr{ left:2px; top:5px; background:var(--trap); }
.dchl .row.mgirr .en{ font-weight:600; }
.mgtag{ display:inline-block; font-size:7.6px; font-weight:800; color:#fff; background:var(--trap); border-radius:7px; padding:0 6px; margin-left:5px; vertical-align:1px; }
/* 순서·삽입 이음매형 해석카드 */
.seamwrap{ margin-top:2px; }
.seamrow{ display:flex; gap:7px; padding:5px 0; border-bottom:1px dashed #dbe6f0; }
.seamrow:last-of-type{ border-bottom:none; }
.seamrow .slab{ flex:none; width:46px; font-size:8.6px; font-weight:800; color:#1f4d7a; background:#e2eefa; border-radius:5px; padding:3px 4px; text-align:center; height:fit-content; }
.seamrow .sbody{ flex:1; min-width:0; }
.seamrow .scue{ font-size:9px; margin-bottom:2px; }
.seamrow .scue .pclue{ font-size:8px; }
.seamrow .scue .nocue{ font-size:8.2px; color:#8a929b; font-style:italic; }
.seamrow .scue .rarw{ color:#9bb4cc; font-weight:800; margin:0 3px; }
.seamrow .scue .refv{ font-weight:800; color:#1f4d7a; background:#eaf2fb; border-radius:3px; padding:0 4px; }
.seamrow .sen{ font-size:9.6px; line-height:1.7; color:#23272e; }
.seamrow .sko{ font-size:9.3px; line-height:1.7; color:#33414d; margin-top:1px; }
.seamrow .slink{ font-size:8.4px; font-weight:700; color:#2f6fb0; margin-top:2px; }
.seamans{ margin-top:6px; background:#e6f0f9; border-left:3px solid #2f6fb0; border-radius:5px; padding:5px 9px; font-size:9.4px; font-weight:700; color:#1f4d7a; }
.seamans b{ color:#12406e; }
/* STEP1 재진술 연결 문제(추가 문제, 풀칸) */
.rquiz{ margin-top:10px; border:1.5px solid #e0b94a; border-radius:9px; background:#fffdf6; padding:11px 15px; }
.rquiz .rqh{ font-size:11.5px; font-weight:800; color:#8a5a1a; display:flex; align-items:center; gap:6px; }
.rquiz .rqh .ico{ font-size:12px; } .rquiz .rqh .add{ font-size:8px; font-weight:800; color:#fff; background:#c9a24a; border-radius:8px; padding:1px 7px; }
.rquiz .rqh .rqno{ margin-left:auto; font-size:8.5px; font-weight:800; color:#8a5a1a; background:#ffe9a8; border:1px solid #e0b94a; border-radius:8px; padding:1px 8px; }
.rquiz .rqg{ font-size:9px; line-height:1.5; color:#6e5316; margin:5px 0 9px; } .rquiz .rqg b{ color:#8a5a1a; }
.rquiz .rqcue{ font-size:8.8px; line-height:1.5; color:#0f5f57; background:#e7f4f2; border:1px solid #a9d6cf; border-radius:6px; padding:5px 9px; margin-bottom:9px; }
.rquiz .rqcue b{ color:#0f766e; }
.rquiz .rqchain{ display:flex; flex-direction:column; gap:7px; }
.rquiz .rqrow{ display:flex; align-items:center; gap:8px; }
.rquiz .rqrow .pr{ flex:none; min-width:22px; text-align:center; font-size:10px; font-weight:800; color:#7a5416; background:#ffe9a8; border:1px solid #e0b94a; border-radius:6px; padding:1px 5px; }
.rquiz .rqrow .pr.big{ font-size:11px; margin-right:4px; }
.rquiz .rqrow .rqlab{ flex:none; width:74px; font-size:8.6px; font-weight:700; color:#8a6a00; }
.rquiz .rqrow .ln{ flex:1; border-bottom:1.4px dotted #d7b968; height:15px; }
.rquiz .rqrow .given{ flex:1; font-size:9.5px; color:#23272e; background:#fff9e6; border:1px solid #ecdcb0; border-radius:6px; padding:2px 8px; line-height:1.35; }
.rquiz .rqrow .given i{ color:#8a6a00; font-style:normal; font-size:8.5px; margin-left:6px; }
.rquiz .rqsubs{ display:flex; gap:12px; }
.rquiz .rqsub{ flex:1; min-width:0; }
.rquiz .rqsub .rqname{ display:flex; align-items:center; gap:5px; font-size:9.3px; font-weight:800; color:#8a5a1a; border-bottom:1px solid #f0e3bf; padding-bottom:4px; margin-bottom:6px; }
.rquiz .rqcnt{ margin-left:auto; font-size:7.6px; font-weight:800; color:#8a6a00; background:#fff4d9; border-radius:7px; padding:1px 6px; }
.rquiz .rqsub .rqrow .rqlab{ width:52px; }
/* STEP3 재진술 지도 카드 */
.card.restate{ border-left:5px solid #e0b94a; background:#fffdf6; }
.card.restate .hd{ border-bottom-color:#e0b94a; }
.card.restate .rno{ background:none; font-size:14px; padding:0; }
.card.restate .ty{ color:#8a5a1a; }
.card.restate .tm{ color:#a58a3a; }
.restate .thesis{ font-size:9.8px; font-weight:700; color:#7a5416; background:#fff4d9; border-radius:6px; padding:6px 10px; margin-bottom:7px; }
.restate .thesis .lb, .restate .rEcho .lb{ display:inline-block; font-size:7.6px; font-weight:800; color:#fff; background:#c9a24a; border-radius:7px; padding:1px 7px; margin-right:6px; vertical-align:1px; }
.restate .rhint{ font-size:8.5px; color:#8a6a00; background:#fff8e6; border-radius:6px; padding:4px 9px; margin-bottom:6px; } .restate .rhint b{ color:#8a5a1a; font-weight:800; }
.restate .rchain{ margin-bottom:2px; }
.restate .rc{ display:flex; flex-wrap:wrap; align-items:baseline; gap:5px; padding:5px 0; border-bottom:1px dashed #ecdcb0; }
.restate .rc:last-child{ border-bottom:none; }
.restate .pr{ flex:none; min-width:20px; text-align:center; font-size:9.5px; font-weight:800; color:#7a5416; background:#ffe9a8; border:1px solid #e0b94a; border-radius:6px; padding:0 5px; }
.restate .pr.big{ font-size:10.5px; margin-right:5px; }
.restate .rarw{ flex:none; color:#c9a24a; font-weight:800; font-size:9px; margin:0 -1px; }
.restate .rhow{ flex:none; font-size:7.6px; font-weight:800; color:#a5342d; background:#ffe0dd; border-radius:7px; padding:1px 7px; }
.restate .ren{ font-size:9.5px; font-weight:600; color:#23272e; background:var(--must); border-radius:3px; padding:0 3px; }
.restate .rko{ flex-basis:100%; font-size:8.8px; color:#5a636c; padding-left:23px; }
/* compare — 두 소재를 A…·B…로 나란히 */
.restate .rsubs{ display:flex; gap:8px; margin-bottom:2px; }
.restate .rsub{ flex:1; min-width:0; background:#fff; border:1px solid #ecdcb0; border-radius:7px; padding:6px 9px; }
.restate .rsub .rname{ display:flex; align-items:center; font-size:9px; font-weight:800; color:#8a5a1a; border-bottom:1px solid #f0e3bf; padding-bottom:3px; margin-bottom:4px; }
.restate .rsub .rc{ padding:4px 0; }
.restate .rsub .ren{ font-size:9px; }
.restate .rsub .rko{ padding-left:23px; }
.restate .rEcho{ margin-top:6px; font-size:9.4px; font-weight:700; color:#12543d; background:#eaf5f0; border-left:3px solid var(--ink); border-radius:0 5px 5px 0; padding:5px 10px; }
</style></head><body>
<div class="cover">
  <div class="kick">PART 1</div>
  <div class="t">유형별 훈련</div>
  <div class="rule"></div>
  <div class="s">실제 평가원 기출 <span class="n">{{N}}문항</span></div>
</div>
{{BODY}}
</body></html>'''

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 999
    build(n)

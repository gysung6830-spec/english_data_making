"""얇은 챕터를 5 mc + 5 short 로 채우기 위한 '실제 기출 후보 문장'을 챕터별로 추출.

- 1부 구문: corpus type 태그
- 2부 코드: corpus code 태그
- 3부 추상: 내용 정규식(재진술/예시/비유/추상명사) + contrast는 code=contrast
- 이미 교재에 쓴 문장·제외문항(20·25~29)은 뺀다. 자기완결 우선.
결과: scratchpad/candidates.json  {chapter:{part,need_mc,need_sh,focus,sentences:[{text,source}]}}
"""
from __future__ import annotations
import json, re, sys, yaml
from pathlib import Path
from src.guide.corpus_store import query, load_corpus

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scratchpad/candidates.json")

recs = load_corpus()
def norm(t): return re.sub(r"\s+", " ", t.lower()).strip()

# 이미 쓴 문장(전역) + 현재 mc/short 개수(파트별, 제외 반영)
used = set(); cur = {}
from src.guide.codes import keep_source
_FILEPART = {"src/guide/syntax_practice.yaml": "1부",
             "src/guide/codes_practice.yaml": "2부",
             "src/guide/abstract_practice.yaml": "3부"}
for fn, part in _FILEPART.items():
    d = yaml.safe_load(open(fn, encoding="utf-8"))
    for ch, items in d.get("practice", {}).items():
        for it in items:
            used.add(norm(it.get("sentence", "")))
        kept = [it for it in items if keep_source(it.get("source", ""))]
        cur[(part, ch)] = {"mc": sum(1 for it in kept if it.get("kind") == "mc"),
                           "sh": sum(1 for it in kept if it.get("kind") == "short")}

# 챕터 간 문장 중복 배정 방지(전역 누적)
assigned = set()

def rank(cands):
    cands.sort(key=lambda r: (0 if r.get("difficulty") == "고" else 1, -len(r["text"]), r["id"]))
    return cands

def fresh_by_type(t):
    return rank([r for r in query(recs, type=t) if norm(r["text"]) not in used])

def fresh_by_code(c):
    return rank([r for r in query(recs, code=c) if norm(r["text"]) not in used])

def fresh_by_regex(rx):
    p = re.compile(rx, re.I)
    return rank([r for r in query(recs) if norm(r["text"]) not in used and p.search(r["text"])])

# 챕터 정의: (part, source-spec, focus)
SYN = {
  "emphasis": "강조구문(It ~ that / do 강조 / 재귀 강조)",
  "inversion": "도치(부정어·보어·장소부사 문두 → 주어·동사 도치)",
  "parallel": "병렬(and/or/but로 이어진 대등 요소 짝맞추기)",
  "apposition": "동격(명사=명사, that절·콜론·대시로 같은 것 다시 말하기)",
  "what_clause": "what절(관계대명사 what = the thing which, 명사절 덩어리)",
  "insertion": "삽입(콤마·대시 사이 삽입어구를 걷어내고 뼈대 잡기)",
  "participle": "분사(현재/과거분사구가 명사 수식 또는 분사구문)",
  "that_clause": "that절(동격 that / 관계사 that / 접속사 that 구분)",
  "wh_clause": "wh절(관계부사·의문사절 구분, where/when/how/why)",
  "prep_stack": "전치사구 중첩(of/in/for … 여러 전치사구가 겹쳐 수식)",
}
CODE = {
  "causation": "인과(A가 B를 낳는다: cause/lead to/result in/attributable to)",
  "contrast": "대조(but/however/unlike/whereas/while 앞뒤 뒤집기)",
  "equivalence": "동치·환언(즉·다시 말해: that is/in other words/namely)",
  "comparison": "비교(비교급·최상급·as~as, more/less than)",
  "connective": "담화표지(therefore/moreover/for instance 등 연결어 방향)",
  "polarity_positive": "긍정·강조 신호(central/essential/key 등 필자 강조)",
}
ABS = {  # 3부 추상→구체
  "nominalization": ("regex", r"\b(ability|tendency|notion|assumption|capacity|fact|idea|belief|claim|view|principle|possibility) (that|of|to)\b", "추상명사 뒤 that/of/to로 내용을 구체화"),
  "restate": ("regex", r"\b(that is|in other words|namely|put simply|i\.e\.)\b", "재진술(즉/다시 말해)로 추상어를 쉬운 말로"),
  "example": ("regex", r"\b(such as|for example|for instance|including)\b|:", "예시(such as/for example/콜론)로 추상을 사례화"),
  "contrast": ("code", "contrast", "대비로 구체화(A와 달리 B로 뜻을 또렷하게)"),
  "metaphor": ("regex", r"\b(is like|as if|a kind of|as though|serve[sd]? as|act[s]? as|is a\b)\b", "비유(like/as if/a kind of)로 추상을 이미지화"),
}

out = {}
def add(ch, part, focus, cands, cur_key=None):
    c = cur.get(cur_key or (part, ch), {"mc": 0, "sh": 0})
    need_mc = max(0, 5 - c["mc"]); need_sh = max(0, 5 - c["sh"])
    total_need = need_mc + need_sh
    # 다른 챕터에 이미 배정된 문장 제외 후 상위 N
    cands = [r for r in cands if norm(r["text"]) not in assigned]
    picked = cands[:total_need]
    for r in picked:
        assigned.add(norm(r["text"]))
    # 가용량이 모자라면 mc 우선 배분
    got = len(picked)
    if got < total_need:
        a_mc = min(need_mc, got); a_sh = got - a_mc
    else:
        a_mc, a_sh = need_mc, need_sh
    out[ch] = {"part": part, "focus": focus, "have_mc": c["mc"], "have_sh": c["sh"],
               "make_mc": a_mc, "make_sh": a_sh, "avail": len(cands),
               "sentences": [{"text": r["text"], "source": r["source"]} for r in picked]}

for ch, focus in SYN.items():
    add(ch, "1부", focus, fresh_by_type(ch))
for ch, focus in CODE.items():
    add(ch, "2부", focus, fresh_by_code(ch))
for ch, (mode, spec, focus) in ABS.items():
    cands = fresh_by_code(spec) if mode == "code" else fresh_by_regex(spec)
    add("abs_" + ch, "3부", focus, cands, cur_key=("3부", ch))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"→ {OUT}")
for ch, v in out.items():
    short = "" if len(v["sentences"]) >= v["make_mc"] + v["make_sh"] else "  ⚠부족"
    print(f"  {ch:18s} 보유 {v['have_mc']}/{v['have_sh']} → 작성 mc{v['make_mc']}+sh{v['make_sh']} (가용 {v['avail']}){short}")

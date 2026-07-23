"""기출 예문(교재 '어떻게 읽는지' 섹션)을 챕터당 4개로 채우기 위한 후보 추출.
1부 syntax_formula(type) / 3부 abstract(내용검색·code) / 어휘유추(혼합) 별로,
이미 쓴 문장(예문·연습·카드) 제외, 자기완결·제외문항 필터.
결과: scratchpad/ex_candidates.json
"""
from __future__ import annotations
import json, re, sys, yaml
from pathlib import Path
from src.guide.corpus_store import query, load_corpus
from src.guide.codes import keep_source

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("scratchpad/ex_candidates.json")
recs = load_corpus()
def norm(t): return re.sub(r"\s+", " ", str(t).lower()).strip()

used = set()
def walk(x):
    if isinstance(x, dict):
        if isinstance(x.get("en"), str) and len(x["en"]) > 30: used.add(norm(x["en"]))
        if "sentence" in x: used.add(norm(x["sentence"]))
        for v in x.values(): walk(v)
    elif isinstance(x, list):
        for e in x: walk(e)
for fn in ["src/guide/syntax_formula.yaml","src/guide/abstract.yaml","src/guide/inference.yaml",
           "src/guide/syntax_practice.yaml","src/guide/codes_practice.yaml","src/guide/abstract_practice.yaml"]:
    walk(yaml.safe_load(open(fn, encoding="utf-8")))
import samples.guide_mock as gm
for ch in gm.mock_guide().chapters:
    for c in getattr(ch, "cards", []): used.add(norm(c.sentence))

assigned = set()
def rank(cs):
    cs.sort(key=lambda r: (0 if r.get("difficulty")=="고" else 1, -len(r["text"]), r["id"]))
    return cs
def take(cands, n):
    cands = [r for r in cands if norm(r["text"]) not in used and norm(r["text"]) not in assigned]
    picked = rank(cands)[:n]
    for r in picked: assigned.add(norm(r["text"]))
    return [{"text": r["text"], "source": r["source"]} for r in picked]

out = {}
SYN_FOCUS = {
 "wh_clause":"wh절(관계부사·의문사절 구분)","participle":"분사구·분사구문","insertion":"콤마·대시 삽입어구",
 "apposition":"동격(명사=명사)","prep_stack":"전치사구 중첩","inversion":"도치","emphasis":"강조구문",
 "parallel":"병렬","what_clause":"what절","that_clause":"that절",
}
sf = yaml.safe_load(open("src/guide/syntax_formula.yaml", encoding="utf-8"))["formulas"]
for cid, focus in SYN_FOCUS.items():
    cur = sum(1 for e in sf[cid].get("examples", []) if keep_source(e.get("src","")))
    need = max(0, 4 - cur)
    out["syn::"+cid] = {"part":"1부","focus":focus,"need":need,
                        "sentences": take([r for r in query(recs, type=cid)], need)}

ABS = {"nominalization":("regex",r"\b(ability|tendency|notion|assumption|capacity|fact|idea|belief|claim|view|principle) (that|of|to)\b","추상명사 뒤 that/of/to로 구체화"),
       "restate":("regex",r"\b(that is|in other words|namely|i\.e\.)\b","재진술(즉/다시 말해)"),
       "example":("regex",r"\b(such as|for example|for instance|including)\b|:","예시(such as/콜론)"),
       "contrast":("code","contrast","대비로 구체화"),
       "metaphor":("regex",r"\b(is like|as if|a kind of|as though|serve[sd]? as|act[s]? as|is a\b)\b","비유")}
ab = {c["id"]: c for c in yaml.safe_load(open("src/guide/abstract.yaml", encoding="utf-8"))["chapters"]}
for cid,(mode,spec,focus) in ABS.items():
    cur = sum(1 for e in ab[cid].get("examples", []) if keep_source(e.get("src","")))
    need = max(0, 4 - cur)
    if mode=="code": cands=[r for r in query(recs, code=spec)]
    else:
        p=re.compile(spec,re.I); cands=[r for r in query(recs) if p.search(r["text"])]
    out["abs::"+cid] = {"part":"3부","focus":focus,"need":need,"sentences": take(cands, need)}

# 어휘유추: 다양한 단서(대조/재진술/극성) 섞어서 3개
inf_cands=[r for r in query(recs) if re.search(r"\b(but|however|unlike|rather than|that is|such as|not|never|rarely)\b", r["text"], re.I)]
out["inf::infer"] = {"part":"어휘유추","focus":"단서(대조·재진술·극성)로 모르는 단어 뜻 유추","need":3,
                     "sentences": take(inf_cands, 3)}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("→", OUT)
for k,v in out.items():
    got=len(v["sentences"]); short="" if got>=v["need"] else "  ⚠부족"
    print("  %-22s need %d got %d%s"%(k, v["need"], got, short))

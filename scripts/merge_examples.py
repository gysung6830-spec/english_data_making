"""ex_g*.yaml(키: syn::id / abs::id / inf::id → 예문 리스트)을
syntax_formula.yaml·abstract.yaml·inference.yaml의 examples에 append(중복 문장 제외)."""
from __future__ import annotations
import re, sys, yaml
from pathlib import Path

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")
def norm(t): return re.sub(r"\s+", " ", str(t).lower()).strip()

merged = {}
for f in sorted(SP.glob("ex_g*.yaml")):
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for k, v in data.items():
        merged.setdefault(k, []).extend(v or [])

# 파일별 기존 문장 집합
def existing(path, getter):
    s = set(); d = yaml.safe_load(open(path, encoding="utf-8"))
    for exs in getter(d):
        for e in exs: s.add(norm(e.get("en", "")))
    return d, s

added = 0
# 1부 syntax_formula
sf_path = "src/guide/syntax_formula.yaml"
sf = yaml.safe_load(open(sf_path, encoding="utf-8"))
sf_seen = set(norm(e.get("en","")) for fm in sf["formulas"].values() for e in fm.get("examples",[]))
for k, exs in merged.items():
    if not k.startswith("syn::"): continue
    cid = k.split("::",1)[1]
    fm = sf["formulas"][cid]; fm.setdefault("examples", [])
    for e in exs:
        if norm(e["en"]) in sf_seen: continue
        sf_seen.add(norm(e["en"])); fm["examples"].append({"en":e["en"],"src":e.get("src",""),"cut":e.get("cut","")}); added+=1
open(sf_path,"w",encoding="utf-8").write(yaml.dump(sf, allow_unicode=True, sort_keys=False))

# 3부 abstract
ab_path = "src/guide/abstract.yaml"
ab = yaml.safe_load(open(ab_path, encoding="utf-8"))
ab_seen = set(norm(e.get("en","")) for c in ab["chapters"] for e in c.get("examples",[]))
ab_by = {c["id"]: c for c in ab["chapters"]}
for k, exs in merged.items():
    if not k.startswith("abs::"): continue
    cid = k.split("::",1)[1]; c = ab_by.get(cid)
    if not c: print("  ⚠ abstract 챕터 없음:", cid); continue
    c.setdefault("examples", [])
    for e in exs:
        if norm(e["en"]) in ab_seen: continue
        ab_seen.add(norm(e["en"])); c["examples"].append({"en":e["en"],"src":e.get("src",""),"cut":e.get("cut","")}); added+=1
open(ab_path,"w",encoding="utf-8").write(yaml.dump(ab, allow_unicode=True, sort_keys=False))

# 어휘유추 inference
inf_path = "src/guide/inference.yaml"
inf = yaml.safe_load(open(inf_path, encoding="utf-8"))
inf_seen = set(norm(e.get("en","")) for c in inf["chapters"] for e in c.get("examples",[]))
for k, exs in merged.items():
    if not k.startswith("inf::"): continue
    c = inf["chapters"][0]; c.setdefault("examples", [])
    for e in exs:
        if norm(e["en"]) in inf_seen: continue
        inf_seen.add(norm(e["en"])); c["examples"].append({"en":e["en"],"src":e.get("src",""),"cut":e.get("cut","")}); added+=1
open(inf_path,"w",encoding="utf-8").write(yaml.dump(inf, allow_unicode=True, sort_keys=False))

print(f"예문 {added}개 병합 완료")

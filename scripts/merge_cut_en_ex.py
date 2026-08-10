"""예문/특강 파일에 cut_en 병합(yaml.dump; 대상 파일들은 주석이 없어 안전).
- syntax_formula.yaml : formulas[ch].examples[i].cut_en
- abstract.yaml       : chapters(id=ch).examples[i].cut_en
- inference.yaml      : chapters(id=infer).examples[i].cut_en / practice[i].solution.cut_en
"""
import sys, yaml
SP = sys.argv[1] if len(sys.argv) > 1 else "."

def load(p):
    return yaml.safe_load(open(p, encoding="utf-8"))

def dump(p, d):
    open(p, "w", encoding="utf-8").write(yaml.dump(d, allow_unicode=True, sort_keys=False))

n = 0
# 1) syntax_formula 예문
mp = load(f"{SP}/cuten_formula.yaml") or {}
d = load("src/guide/syntax_formula.yaml")
for ch, idxmap in mp.items():
    exs = d["formulas"][ch]["examples"]
    for i, v in idxmap.items():
        exs[int(i)]["cut_en"] = v; n += 1
dump("src/guide/syntax_formula.yaml", d)

# 2) abstract 예문
mp = load(f"{SP}/cuten_abs_ex.yaml") or {}
d = load("src/guide/abstract.yaml")
byid = {c["id"]: c for c in d["chapters"]}
for ch, idxmap in mp.items():
    exs = byid[ch]["examples"]
    for i, v in idxmap.items():
        exs[int(i)]["cut_en"] = v; n += 1
dump("src/guide/abstract.yaml", d)

# 3) inference 예문 + 해설
mp = load(f"{SP}/cuten_inf.yaml") or {}
d = load("src/guide/inference.yaml")
infer = next(c for c in d["chapters"] if c.get("id") == "infer")
for i, v in (mp.get("infer", {}).get("examples", {}) or {}).items():
    infer["examples"][int(i)]["cut_en"] = v; n += 1
for i, v in (mp.get("infer", {}).get("practice", {}) or {}).items():
    sol = infer["practice"][int(i)].get("solution")
    if sol is not None:
        sol["cut_en"] = v; n += 1
dump("src/guide/inference.yaml", d)

print(f"예문/특강 cut_en 병합: {n}건")

"""catch_g*.yaml(챕터→[{id,catch}])의 catch를 예문 소스에 되쓴다."""
from __future__ import annotations
import sys, yaml
from pathlib import Path

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")

merged = {}
for f in sorted(SP.glob("catch_g*.yaml")):
    d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for k, v in d.items():
        merged.setdefault(k, {})
        for row in v or []:
            merged[k][row["id"]] = row.get("catch", "")

def apply_syntax():
    sf = yaml.safe_load(open("src/guide/syntax_formula.yaml", encoding="utf-8"))
    n = 0
    for cid, fm in sf["formulas"].items():
        if cid not in merged:
            continue
        for i, e in enumerate(fm.get("examples", [])):
            if i in merged[cid] and merged[cid][i]:
                e["catch"] = merged[cid][i]; n += 1
    open("src/guide/syntax_formula.yaml", "w", encoding="utf-8").write(
        yaml.dump(sf, allow_unicode=True, sort_keys=False))
    return n

def apply_chapters(path, keys):
    d = yaml.safe_load(open(path, encoding="utf-8"))
    n = 0
    for c in d["chapters"]:
        if c["id"] not in merged or c["id"] not in keys:
            continue
        for i, e in enumerate(c.get("examples", [])):
            if i in merged[c["id"]] and merged[c["id"]][i]:
                e["catch"] = merged[c["id"]][i]; n += 1
    open(path, "w", encoding="utf-8").write(yaml.dump(d, allow_unicode=True, sort_keys=False))
    return n

abs_keys = {"nominalization","restate","example","contrast","metaphor"}
a = apply_syntax()
b = apply_chapters("src/guide/abstract.yaml", abs_keys)
c = apply_chapters("src/guide/inference.yaml", {"infer"})
print(f"catch 적용: 1부 {a} · 3부 {b} · 어휘유추 {c} = {a+b+c}개")

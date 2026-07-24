"""audit_g*.yaml(챕터→검증된 최종 예문 리스트)로 syntax_formula.yaml의
해당 챕터 examples를 통째 교체(문법 불일치 예문 제거·교체 반영)."""
from __future__ import annotations
import sys, yaml
from pathlib import Path

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")

final = {}
for f in sorted(SP.glob("audit_g*.yaml")):
    d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for cid, exs in d.items():
        final[cid] = [{"en": e["en"], "src": e.get("src", ""),
                       "cut": e.get("cut", ""), "how": e.get("how", "")} for e in (exs or [])]

sf = yaml.safe_load(open("src/guide/syntax_formula.yaml", encoding="utf-8"))
report = []
for cid, exs in final.items():
    if cid in sf["formulas"]:
        before = len(sf["formulas"][cid].get("examples", []))
        sf["formulas"][cid]["examples"] = exs
        report.append((cid, before, len(exs)))
open("src/guide/syntax_formula.yaml", "w", encoding="utf-8").write(
    yaml.dump(sf, allow_unicode=True, sort_keys=False))
for cid, b, a in report:
    print(f"  {cid:14s} {b} → {a}")
print("총 챕터:", len(report))

"""backfill_g*.yaml(챕터→문제 리스트)을 syntax_practice.yaml에 append.
vocab 문자열→dict 정규화, 문장 중복 방지."""
from __future__ import annotations
import re, sys, yaml
from pathlib import Path

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")
def norm(t): return re.sub(r"\s+", " ", str(t).lower()).strip()

def fix_vocab(it):
    v = it.get("vocab")
    if isinstance(v, list):
        nv = []
        for e in v:
            if isinstance(e, str):
                m = re.split(r"\s*[:\-–]\s*", e, maxsplit=1)
                nv.append({"word": m[0].strip(), "meaning": (m[1].strip() if len(m) == 2 else "")})
            elif isinstance(e, dict):
                nv.append({"word": e.get("word", ""), "meaning": e.get("meaning", "")})
        it["vocab"] = nv
    return it

merged = {}
for f in sorted(SP.glob("backfill_g*.yaml")):
    d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for ch, items in d.items():
        merged.setdefault(ch, []).extend(items or [])

fn = "src/guide/syntax_practice.yaml"
doc = yaml.safe_load(open(fn, encoding="utf-8"))
pr = doc["practice"]
seen = set(norm(it.get("sentence", "")) for items in pr.values() for it in items)
added = {}
for ch, items in merged.items():
    pr.setdefault(ch, [])
    n = 0
    for it in items:
        k = norm(it.get("sentence", ""))
        if k in seen:
            continue
        seen.add(k); pr[ch].append(fix_vocab(it)); n += 1
    added[ch] = n
open(fn, "w", encoding="utf-8").write(yaml.dump(doc, allow_unicode=True, sort_keys=False))
print("백필 추가:", added, "총", sum(added.values()))

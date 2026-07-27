"""C형(오역 진단) 변환 결과(챕터→[{idx,prompt,options,answer_index}])를 임의의 practice yaml에 반영.
사용법: python scripts/merge_mcC_any.py <target_yaml> <glob1> [glob2 ...]
예:   python scripts/merge_mcC_any.py src/guide/codes_practice.yaml \
          /tmp/.../scratchpad/mcC2_g*.yaml
"""
import sys, glob, yaml

target = sys.argv[1]
patterns = sys.argv[2:]

merged = {}
for pat in patterns:
    for f in sorted(glob.glob(pat)):
        d = yaml.safe_load(open(f, encoding="utf-8")) or {}
        for ch, rows in d.items():
            merged.setdefault(ch, {})
            for r in rows:
                merged[ch][r["idx"]] = r

doc = yaml.safe_load(open(target, encoding="utf-8"))
n = 0
for ch, items in doc["practice"].items():
    if ch not in merged:
        continue
    for i, it in enumerate(items):
        if i in merged[ch]:
            r = merged[ch][i]
            it["prompt"] = r["prompt"]
            it["options"] = r["options"]
            it["answer_index"] = r["answer_index"]
            n += 1
open(target, "w", encoding="utf-8").write(
    yaml.dump(doc, allow_unicode=True, sort_keys=False)
)
print(f"C형 반영: {n}문항 -> {target}")

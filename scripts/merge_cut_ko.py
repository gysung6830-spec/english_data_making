"""한글 끊어읽기 매핑을 practice/카드 yaml의 cut에 반영.
사용법:
  python scripts/merge_cut_ko.py <target_yaml> <mapping_yaml> [--field solution.cut|cut]
매핑 구조: { chapter_id: { "리스트인덱스": "한글 끊어읽기" } }
"""
import sys, yaml

target = sys.argv[1]
mapping_path = sys.argv[2]
field = "solution.cut"
if "--field" in sys.argv:
    field = sys.argv[sys.argv.index("--field") + 1]

mp = yaml.safe_load(open(mapping_path, encoding="utf-8")) or {}
doc = yaml.safe_load(open(target, encoding="utf-8"))
root = doc["practice"] if "practice" in doc else doc

n = 0
missing = []
for ch, idxmap in mp.items():
    items = root.get(ch)
    if items is None:
        missing.append(f"{ch}(챕터없음)")
        continue
    for idx, newcut in idxmap.items():
        i = int(idx)
        if i >= len(items):
            missing.append(f"{ch}[{i}](범위초과)")
            continue
        it = items[i]
        if field == "solution.cut":
            sol = it.get("solution")
            if not sol:
                missing.append(f"{ch}[{i}](solution없음)")
                continue
            sol["cut"] = newcut
        else:  # 'cut'
            it["cut"] = newcut
        n += 1

open(target, "w", encoding="utf-8").write(
    yaml.dump(doc, allow_unicode=True, sort_keys=False)
)
print(f"cut 한글화 반영: {n}건 -> {target}")
if missing:
    print("  주의(미반영):", missing)

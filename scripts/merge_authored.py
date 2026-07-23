"""서브에이전트가 쓴 out_g*.yaml(챕터→문제리스트)을 3개 practice YAML에 병합.

- 챕터가 어느 파일(1부 syntax / 2부 codes / 3부 abstract)에 속하는지 매핑해 append.
- vocab 항목이 문자열이면 {word,meaning} dict로 정규화(과거 이슈 방지).
- 문장 중복(기존/신규 간)은 건너뛰고 로그.
"""
from __future__ import annotations
import re, sys, glob, yaml
from pathlib import Path

SYN = {"emphasis","inversion","parallel","apposition","what_clause","insertion",
       "participle","that_clause","wh_clause","prep_stack"}
CODE = {"causation","contrast","equivalence","comparison","connective",
        "polarity_positive","polarity_negative"}
ABS = {"nominalization","restate","example","reference","metaphor"}
# 주의: 'contrast'는 2부·3부 양쪽에 존재. 출력 파일별로 구분 필요 → 파일 소속으로 판정 불가.
# 따라서 각 out 파일은 '어느 파트'인지 태그가 필요. 파일명 규칙으로 처리(아래 GROUP_PART).

GROUP_PART = {  # out_g*.yaml → part
    "out_g1.yaml":"1부","out_g2.yaml":"1부","out_g3.yaml":"1부","out_g4.yaml":"1부",
    "out_g5.yaml":"2부","out_g6.yaml":"3부","out_g7.yaml":"3부","out_g8.yaml":"3부",
}
PART_FILE = {
    "1부":"src/guide/syntax_practice.yaml",
    "2부":"src/guide/codes_practice.yaml",
    "3부":"src/guide/abstract_practice.yaml",
}

def norm(t): return re.sub(r"\s+"," ",str(t).lower()).strip()

def fix_vocab(item):
    v = item.get("vocab")
    if isinstance(v, list):
        nv = []
        for e in v:
            if isinstance(e, str):
                # "word: 뜻" 또는 "word - 뜻" 형태 분해
                m = re.split(r"\s*[:\-–]\s*", e, maxsplit=1)
                if len(m) == 2:
                    nv.append({"word": m[0].strip(), "meaning": m[1].strip()})
                else:
                    nv.append({"word": e.strip(), "meaning": ""})
            elif isinstance(e, dict):
                nv.append({"word": e.get("word","") , "meaning": e.get("meaning","")})
        item["vocab"] = nv
    return item

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")

# 1) out 파일들을 파트별로 모은다
by_part_ch = {"1부":{}, "2부":{}, "3부":{}}
for f in sorted(SP.glob("out_g*.yaml")):
    part = GROUP_PART.get(f.name)
    if not part:
        print(f"SKIP(unknown part) {f.name}"); continue
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for ch, items in data.items():
        by_part_ch[part].setdefault(ch, []).extend(items or [])

# 2) 각 파트 파일에 병합
grand_added = 0
for part, fn in PART_FILE.items():
    p = Path(fn)
    d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    pr = d.setdefault("practice", {})
    # 파트 전체의 기존 문장 집합
    seen = set()
    for ch, items in pr.items():
        for it in items: seen.add(norm(it.get("sentence","")))
    added_here = 0
    for ch, items in by_part_ch[part].items():
        if ch not in pr:
            pr[ch] = []
            print(f"  [{part}] 신규 챕터 키 {ch} 생성")
        for it in items:
            key = norm(it.get("sentence",""))
            if key in seen:
                print(f"  [{part}/{ch}] 중복 문장 건너뜀: {it.get('sentence','')[:40]}...")
                continue
            seen.add(key)
            pr[ch].append(fix_vocab(it))
            added_here += 1
    p.write_text(yaml.dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"[{part}] {fn}: +{added_here}문제")
    grand_added += added_here

print(f"\n총 추가: {grand_added}문제")

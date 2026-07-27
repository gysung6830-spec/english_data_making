"""mcC_g*.yaml(챕터→[{idx,prompt,options,answer_index}])을 syntax_practice.yaml에 반영(C형)."""
import sys, yaml
from pathlib import Path
SP=Path(sys.argv[1]) if len(sys.argv)>1 else Path("/tmp/claude-0/-home-user-english-data-making/99a0ddf4-ca89-531d-9eee-587a9a5b2671/scratchpad")
merged={}
for f in sorted(SP.glob("mcC_g*.yaml")):
    d=yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for ch,rows in d.items():
        merged.setdefault(ch,{})
        for r in rows: merged[ch][r["idx"]]=r
fn="src/guide/syntax_practice.yaml"
doc=yaml.safe_load(open(fn,encoding="utf-8")); n=0
for ch,items in doc["practice"].items():
    if ch not in merged: continue
    for i,it in enumerate(items):
        if i in merged[ch]:
            r=merged[ch][i]
            it["prompt"]=r["prompt"]; it["options"]=r["options"]; it["answer_index"]=r["answer_index"]; n+=1
open(fn,"w",encoding="utf-8").write(yaml.dump(doc,allow_unicode=True,sort_keys=False))
print("C형 반영:",n,"문항")

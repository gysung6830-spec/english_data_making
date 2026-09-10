# -*- coding: utf-8 -*-
"""어법칩 정합성 검증 — 특히 관계대명사 주격/목적격 혼동과 생략(무엇이 생략됐는지) 오류를 코드로 차단.

규칙(고신뢰):
  · 관계대명사(who/which/that) 뒤에 '주어로 시작하는 말'(대명사·관사·소유격·지시사)이 오면 목적격,
    그렇지 않으면(동사/부사+동사) 주격. whom은 항상 목적격. whose는 소유격.
  · 주격 관계대명사는 생략 불가 → '주격 … 생략' 태그는 오류.
  · 생략(목적격 관대/관계부사)은 선행사 뒤에 '주어(S)'가 이어져야 함.
  · 관계사 칩은 antecedent 필요, 명사절 칩은 role 필요(구조 검증).
import 해서 check_passages(P)로 쓰거나 단독 실행."""
import re

SUBJ_START = {  # 관계사 뒤 이게 오면 관계사절의 '새 주어' → 관계사는 목적격
    "i","you","he","she","it","we","they","one","people","someone","everyone","nobody",
    "my","your","his","her","its","our","their","one's",
    "the","a","an","this","that","these","those","some","many","most","much","each","every",
    "any","no","all","both","either","neither","another","such","few","several","various","other",
}
REL_PRON = {"who","whom","which","that"}
REL_ADV  = {"where","when","why","how"}
VERB_AUX = {  # 관계사 뒤 이게 오면 관계사절에 주어가 없음 → 관계사는 주격
    "is","are","was","were","be","been","being","am","'s","'re",
    "has","have","had","'ve","do","does","did",
    "can","could","will","would","shall","should","may","might","must",
}

def _tokens_after(raw, marker, start=0):
    m = re.search(r'(?<![A-Za-z])'+re.escape(marker)+r'(?![A-Za-z])', raw[start:], re.I)
    if not m: return None, None
    end = start + m.end()
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw[end:])
    return toks, end

def _first(toks):
    return (toks[0].lower() if toks else "")

def derive_rel_case(raw, marker, antecedent=""):
    """관계대명사 격 추정: '목적격'|'주격'|'' (관계부사/소유격/불확실)."""
    mk = marker.strip().lower()
    if mk == "whom": return "목적격"
    if mk == "whose": return ""      # 소유격
    if mk in REL_ADV: return ""       # 관계부사
    if " " in mk: return ""           # 전치사+관계대명사 등
    if mk not in REL_PRON: return ""
    # 선행사 뒤에서 관계사 찾기(정확한 위치 앵커)
    start = 0
    if antecedent:
        am = re.search(re.escape(antecedent), raw, re.I)
        if am: start = am.start()
    toks, _ = _tokens_after(raw, marker, start)
    if toks is None:
        toks, _ = _tokens_after(raw, marker, 0)
    nxt = _first(toks)
    if not nxt: return ""
    # 고신뢰만 판정: 주어시작어→목적격, 조동사/be/do→주격. 그 외(맨명사 등)는 판정보류('')
    if nxt in SUBJ_START: return "목적격"
    if nxt in VERB_AUX:   return "주격"
    return ""

def check_passages(P):
    """P: [passage dict]. 반환: (errors, warns) 문자열 리스트."""
    errors=[]; warns=[]
    for d in P:
        it=d.get("item_no","?").strip()
        for s in d["sentences"]:
            raw=s["english"]; sid=s["id"]
            for g in s.get("grammar",[]):
                tag=g.get("tag","") or ""; spans=g.get("spans") or []
                ante=(g.get("antecedent") or "").strip()
                role=(g.get("role") or "").strip()
                is_rel = "관계" in tag
                is_omit = "생략" in tag
                is_noun = ("명사절" in tag) or ("that절" in tag) or ("간접의문" in tag)
                loc=f"{it} S{sid} {tag!r}"
                # 구조 검증
                if is_rel and not is_omit and "what" not in tag.lower():
                    if not ante:
                        warns.append(f"{loc}: 관계사인데 antecedent 없음")
                if is_noun and not role:
                    warns.append(f"{loc}: 명사절인데 role 없음")
                # 주격 생략 불가
                if is_omit and "주격" in tag:
                    errors.append(f"{loc}: '주격' 관계대명사 생략은 불가(주격은 생략 못함)")
                # 생략: 선행사 뒤에 주어가 와야 목적격 관대/관계부사 생략이 성립
                if is_omit and ("목적격" in tag or "관계대명사" in tag):
                    toks,_=_tokens_after(raw, ante or (spans[0] if spans else ""), 0)
                    nxt=_first(toks)
                    if nxt in VERB_AUX:  # 선행사 뒤 바로 동사 → 목적격 생략 아님(주격/다른 구조)
                        errors.append(f"{loc}: 목적격 관대 생략인데 선행사 뒤가 동사({nxt!r}) → 생략 성립 안 함")
                # 관계대명사 격 검증
                if is_rel and not is_omit and spans:
                    mk=str(spans[0]).strip()
                    derived=derive_rel_case(raw, mk, ante)
                    if derived:
                        if "목적격" in tag and derived=="주격":
                            errors.append(f"{loc}: 태그는 목적격인데 구조상 주격(rel {mk!r} 뒤=동사)")
                        if "주격" in tag and derived=="목적격":
                            errors.append(f"{loc}: 태그는 주격인데 구조상 목적격(rel {mk!r} 뒤=주어)")
                        if mk.lower()=="whom" and "주격" in tag:
                            errors.append(f"{loc}: whom은 목적격")
    return errors, warns

if __name__=="__main__":
    import json, os
    SC=os.path.dirname(os.path.abspath(__file__))
    order=json.load(open(SC+"/order.json"))
    P=[json.load(open(SC+"/passages/"+fn)) for fn in order]
    errs,warns=check_passages(P)
    print(f"=== ERRORS({len(errs)}) ===")
    for e in errs: print("  ❌",e)
    print(f"=== WARN({len(warns)}) ===")
    for w in warns: print("  ⚠",w)
    print("GRAMMAR CHECK", "FAIL" if errs else "OK")

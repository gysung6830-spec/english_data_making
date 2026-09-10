# -*- coding: utf-8 -*-
"""어법칩 정합성 검증 — 이번 작업에서 나온 어법칩 오류 유형을 '코드로' 전수 차단.

검증하는 오류 유형(이 세션에서 실제로 나왔던 것들):
  1) 형광펜이 엉뚱한 곳/안 그어짐:  span·선행사(antecedent)가 문장 영어에 '그대로' 없으면 오류.
  2) 시험 나올 어법칩인데 형광펜 표시 안 됨:  spans 비어 있으면 경고.
  3) 관계사 선행사 누락:  관계대명사(주격/목적격)·전치사+관계대명사·관계부사·생략형은 antecedent 필요.
  4) 명사절 접속사 역할 누락 / 관계사와 혼동:  명사절·간접의문·동격은 role 필요, antecedent 있으면 오류.
  5) 관계대명사 주격/목적격 혼동:  관계사 뒤가 동사면 주격, 새 주어면 목적격(whom=목적격)과 태그 대조.
  6) 불가능한 생략:  '주격 관계대명사 생략'은 불가.  목적격 관대 생략인데 선행사 뒤가 동사면 오류.

import 해서 check_passages(P) 로 쓰거나 단독 실행.
errors 는 렌더 중단, warns 는 경고만."""
import re

SUBJ_START = {  # 관계사 뒤 이게 오면 관계사절의 '새 주어' → 목적격
    "i","you","he","she","it","we","they","one","people","someone","everyone","nobody",
    "my","your","his","her","its","our","their","one's",
    "the","a","an","this","that","these","those","some","many","most","much","each","every",
    "any","no","all","both","either","neither","another","such","few","several","various","other",
}
VERB_AUX = {  # 관계사 뒤 이게 오면 절에 주어가 없음 → 주격
    "is","are","was","were","be","been","being","am","'s","'re",
    "has","have","had","'ve","do","does","did",
    "can","could","will","would","shall","should","may","might","must",
}
REL_PRON = {"who","whom","which","that"}
REL_ADV  = {"where","when","why","how"}

def _found(term, raw):
    """term 이 raw(영어)에 단어경계 지켜 존재하나(형광펜 렌더러와 동일 기준)."""
    t=(term or "").strip()
    if not t: return True
    l = r"(?<![A-Za-z])" if t[:1].isalpha() else ""
    r = r"(?![A-Za-z])" if t[-1:].isalpha() else ""
    return re.search(l+re.escape(t)+r, raw, re.I) is not None

def _tokens_after(raw, marker, start=0):
    m = re.search(r'(?<![A-Za-z])'+re.escape(marker)+r'(?![A-Za-z])', raw[start:], re.I)
    if not m: return None
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw[start+m.end():])
    return toks

def _first(toks):
    return (toks[0].lower() if toks else "")

def derive_rel_case(raw, marker, antecedent=""):
    """관계대명사 격 추정: '목적격'|'주격'|'' (관계부사/소유격/전치사+관대/불확실은 '')."""
    mk = marker.strip().lower()
    if mk == "whom": return "목적격"
    if mk == "whose": return ""
    if mk in REL_ADV: return ""
    if " " in mk: return ""
    if mk not in REL_PRON: return ""
    start = 0
    if antecedent:
        am = re.search(re.escape(antecedent), raw, re.I)
        if am: start = am.start()
    toks = _tokens_after(raw, marker, start)
    if toks is None: toks = _tokens_after(raw, marker, 0)
    nxt = _first(toks)
    if not nxt: return ""
    if nxt in SUBJ_START: return "목적격"
    if nxt in VERB_AUX:   return "주격"
    return ""

def check_passages(P):
    errors=[]; warns=[]
    for d in P:
        it=d.get("item_no","?").strip()
        for s in d["sentences"]:
            raw=s["english"]; sid=s["id"]
            for g in s.get("grammar",[]):
                tag=g.get("tag","") or ""
                spans=g.get("spans") or []
                ante=(g.get("antecedent") or "").strip()
                role=(g.get("role") or "").strip()
                loc=f"{it} S{sid} {tag!r}"
                is_rel   = "관계" in tag
                is_omit  = "생략" in tag
                is_what  = "what" in tag.lower()
                is_reladv= "관계부사" in tag
                is_prep  = "전치사+관계" in tag
                # 복합관계사(wherever/whenever/however/whatever/whoever/no matter …)는
                # 선행사를 자체 포함 → 선행사 필요 없음(오탐 방지).
                is_compound = ("복합관계" in tag) or any(w in tag.lower() for w in
                    ("wherever","whenever","however","whatever","whoever","whichever","no matter"))
                is_noun  = ("명사절" in tag) or ("that절" in tag) or ("간접의문" in tag)
                is_appos = "동격" in tag

                # 1) span 이 영어에 실재하는가(형광펜 실패 방지)
                for sp in spans:
                    if str(sp).strip() and not _found(sp, raw):
                        errors.append(f"{loc}: span {sp!r} 이 문장 영어에 없음 → 형광펜 실패")
                # 1'') 단일 span 위치 모호(여러 번 등장) → 형광펜 오배치 위험(선행사·복수 span 은 코드가 위치 특정하므로 예외)
                _ne=[str(sp).strip() for sp in spans if str(sp).strip()]
                if len(_ne)==1 and not ante:
                    e=_ne[0]
                    l=r"(?<![A-Za-z])" if e[:1].isalpha() else ""
                    r=r"(?![A-Za-z])" if e[-1:].isalpha() else ""
                    n=len(re.findall(l+re.escape(e)+r, raw, re.I))
                    if n>1:
                        errors.append(f"{loc}: 단일 span {e!r} 이 문장에 {n}번 등장(위치 모호) → span 을 유일하게(앞뒤 한 단어 포함 등)")
                # 2) 형광펜 표시 안 됨(경고)
                if not [sp for sp in spans if str(sp).strip()]:
                    warns.append(f"{loc}: spans 비어 있음 → 형광펜 표시 안 됨")
                # 1') 선행사가 영어에 실재하는가
                if ante and not _found(ante, raw):
                    errors.append(f"{loc}: 선행사 {ante!r} 이 문장 영어에 없음")

                # 3) 관계사 선행사 필요(what·복합관계사·계속적 절부연 제외는 경고)
                if is_rel and not is_what and not is_compound:
                    if not ante:
                        # 주격/목적격/전치사+관대/관계부사/생략형은 선행사가 있어야 함
                        if any(k in tag for k in ("주격","목적격","전치사+관계","관계부사")) or is_omit:
                            errors.append(f"{loc}: 관계사인데 선행사(antecedent) 없음")
                        else:
                            warns.append(f"{loc}: 관계사인데 선행사(antecedent) 없음")

                # 4) 명사절/간접의문은 role 필요, 동격은 role 권장 아님(명사구 동격 존재).
                #    명사절·동격 모두 antecedent 는 금지(관계사와 혼동 방지).
                if is_noun and not is_rel and not role:
                    warns.append(f"{loc}: 명사절/간접의문인데 role(역할) 없음")
                if (is_noun or is_appos) and not is_rel and ante:
                    errors.append(f"{loc}: 명사절/동격에 선행사가 있음 → 관계사와 혼동")

                # 5) 관계대명사 주격/목적격 혼동
                if is_rel and not is_omit and not is_what and not is_prep and not is_reladv and spans:
                    mk=str(spans[0]).strip()
                    derived=derive_rel_case(raw, mk, ante)
                    if derived:
                        if "목적격" in tag and derived=="주격":
                            errors.append(f"{loc}: 태그=목적격인데 구조상 주격(rel {mk!r} 뒤=동사)")
                        if "주격" in tag and derived=="목적격":
                            errors.append(f"{loc}: 태그=주격인데 구조상 목적격(rel {mk!r} 뒤=새 주어)")
                    if mk.lower()=="whom" and "주격" in tag:
                        errors.append(f"{loc}: whom 은 목적격")

                # 6) 불가능한/부정합 생략
                if is_omit and "주격" in tag:
                    errors.append(f"{loc}: '주격 관계대명사 생략'은 불가(주격은 생략 못함)")
                if is_omit and ("목적격" in tag):
                    toks=_tokens_after(raw, ante or (spans[0] if spans else ""), 0)
                    nxt=_first(toks or [])
                    if nxt in VERB_AUX:
                        errors.append(f"{loc}: 목적격 관대 생략인데 선행사 뒤가 동사({nxt!r}) → 생략 성립 안 함")
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

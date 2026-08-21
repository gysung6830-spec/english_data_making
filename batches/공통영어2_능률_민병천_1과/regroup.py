# -*- coding: utf-8 -*-
"""능률 1과: 8소단원 → 5소단원 통합. 문장별 내용(chunks/문법칩/어휘/오답)은 그대로
재사용하고, 묶음 단위(개관·핵심문법·흐름)만 다시 구성한다."""
import sys, importlib.util, os, re
BD=os.path.dirname(os.path.abspath(__file__))  # regroup.py 가 있는 폴더(gen·_helpers·mt·산출물 모두 여기)
sys.path.insert(0,"/home/user/english_data_making"); sys.path.insert(0,BD)
from _helpers import (build, finalize, Overview, KeyGrammar, GrammarNote, GrammarDrill,
    FlowBlock, RestatementChain)
from src.lecture_render import render_lecture_pdf
from verify import verify_passages, print_report
import fitz
def load(n):
    s=importlib.util.spec_from_file_location(n[:-3],os.path.join(BD,n)); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
O=[]
for n in ["gen_gen1.py","gen_gen2.py","gen_gen3.py","gen_gen4.py"]:
    O+=list(load(n).PARTS)   # O[0..7] = 8개 원본 소단원(속보,조난1,조난2,수색,제보,추론,구조,마무리)

def merge(passages, item_no, title, ov_over):
    """passages를 이어 붙여 새 소단원. ov_over=Overview(문장 재번호 반영)."""
    r=[]; items=[]
    for P in passages:
        for ls, si in zip(P.sentences, P.analysis.sentences):
            r.append(ls.text); si.id=len(items)+1; items.append(si)
    return build(title, item_no, r, ov_over)  # build(title,no,r,ov,items)

def OV(theme,topic,stance,sreason,structure,streason,key,flows,chains):
    return Overview(theme_ko=theme,key_grammar=key,topic=topic,stance=stance,
        stance_reason=sreason,structure=structure,structure_reason=streason,
        restatement_chains=chains,flow_blocks=flows)

def build2(title,no,r,ov,items):
    from src.lecture_schemas import LecturePassage, SentenceAnalysis, LectureSentence
    p=LecturePassage(title=title,source=O[0].source,item_no=no,
        sentences=[LectureSentence(id=i,text=t) for i,t in enumerate(r,1)],
        overview=ov,analysis=SentenceAnalysis(sentences=items))
    p.analysis.validate_all(len(r)); return p

def merge(passages, no, title, ov):
    r=[]; items=[]
    for P in passages:
        for ls, si in zip(P.sentences, P.analysis.sentences):
            r.append(ls.text); si.id=len(items)+1; items.append(si)
    return build2(title,no,r,ov,items)

def chains2(a,b=None):
    cs=list(a.overview.restatement_chains)
    if b: cs+=list(b.overview.restatement_chains)
    return cs[:2]

# ---- G1 (1-10): 속보 + 조난 경위 / key = 계속적 which(O[1]) ----
G1=merge([O[0],O[1]],"1 · 속보와 조난 경위","Rescue ① 속보·조난",
 OV("사진 한 장으로 구조된 실종 등산객 — 산불로 표지판이 사라져 조난에 이른 경위",
    "실종 등산객 Compean이 구조됐다는 속보와, 숙련 등산객인 그가 산불로 표지판이 사라져 길을 잃고 밤·추위 속에 고립되는 조난 경위를 전하는 뉴스 도입부야.",
    "중립적","앵커 속보와 기자 중계로 사건의 발단(구조 사실→조난 경위)을 시간순으로 보도하는 부분이야.",
    "시간·순서(나열)","속보(1~3) → 조난 경위(4~7) → 상황 악화(8~10)로 시간 순서로 전개돼.",
    O[1].overview.key_grammar,
    [FlowBlock(stage="속보",sentence_range="1~3",summary="실종 등산객 Compean이 구조됐고, [[사진 한 장]]이 결정적 역할을 했다는 속보."),
     FlowBlock(stage="조난 경위",sentence_range="4~7",summary="숙련 등산객이 홀로 등산 중, [[산불이 표지판을 망가뜨려]] 길을 잘못 들어 조난된다.",easy_example="이정표가 사라져 길을 잃는 상황."),
     FlowBlock(stage="악화",sentence_range="8~10",summary="SOS를 쓰며 도움을 청하지만 밤·강풍·추위로 [[상황이 나빠진다]].")],
    chains2(O[1],O[0])))

# ---- G2 (11-22): 구조 요청 + 수색 난관 / key = 독립부정사(O[2]) ----
G2=merge([O[2],O[3]],"2 · 구조 요청과 수색의 난관","Rescue ② 요청·수색",
 OV("약한 신호로 보낸 문자·사진, 그러나 경찰 수색은 난관에 부딪히다",
    "깊은 숲에서 배터리가 거의 방전된 채 약한 신호로 친구에게 문자·사진을 보내고, 그것이 경찰에 전달되지만 화질과 위치 설정 문제로 수색이 난항을 겪는 부분이야.",
    "중립적","구조 요청 과정과 경찰 수색의 실패를 시간순으로 보도하는 부분이야.",
    "시간·순서(나열)","신호 확보(1~4) → 사진 전송(5~7) → 경찰 수색 실패(8~12)로 전개돼.",
    O[2].overview.key_grammar,
    [FlowBlock(stage="신호 확보",sentence_range="1~4",summary="깊은 숲·[[배터리 방전]] 속, 높은 곳에서 약한 신호를 찾아 친구에게 문자를 보낸다."),
     FlowBlock(stage="사진 전송",sentence_range="5~7",summary="길을 잃고 도움이 필요하다는 메시지와 [[주변 사진]]을 보내 친구가 경찰에 공유한다."),
     FlowBlock(stage="수색 실패",sentence_range="8~12",summary="경찰이 밤샘 수색에도 위치를 못 찾고, 사진도 [[화질·위치설정]] 탓에 도움이 안 된다.",easy_example="흐릿한 사진으로는 어디인지 알 수 없는 상황.")],
    chains2(O[2],O[3])))

# ---- G3 (23-29): 제보자 Ben Kuo / 원본 O[4] 개관 그대로 재사용 ----
G3=merge([O[4]],"3 · 제보자 Ben Kuo의 등장",O[4].title,O[4].overview)

# ---- G4 (30-37): 추론 + 구조 / key = 조동사 must(O[5]) ----
G4=merge([O[5],O[6]],"4 · Kuo의 추론과 구조","Rescue ④ 추론·구조",
 OV("검은 재와 식물을 단서로 남쪽을 추론해 마침내 위치를 찾아내다",
    "Kuo가 다리의 검은 재로 산불을, 사진 속 식물·지형으로 산의 남쪽임을 추론하고, 위성 이미지 비교로 위치를 특정해 경찰이 헬기로 Compean을 구조하는 부분이야.",
    "중립적","단서 해석→위치 특정→구조로 이어지는 문제 해결 과정을 시간순으로 보도해.",
    "시간·순서(나열)","단서 추론(1~2) → 지역 지식·남쪽 추론(3~5) → 위성 일치·구조(6~8)로 전개돼.",
    O[5].overview.key_grammar,
    [FlowBlock(stage="단서 추론",sentence_range="1~2",summary="다리의 [[검은 재]]가 최근 산불을 떠올리게 해 대략적 위치를 추론한다."),
     FlowBlock(stage="남쪽 추론",sentence_range="3~5",summary="이전 화재 추적·위성 확인 경험과 사진 속 [[식물]]로 산의 남쪽임을 추론한다(북쪽엔 푸른 골짜기가 없음).",easy_example="풍경 특징으로 방위를 좁히는 것."),
     FlowBlock(stage="구조",sentence_range="6~8",summary="위성 이미지와 [[일치하는 곳]]을 찾아 위치를 넘겨, 경찰이 헬기로 1마일 이내에서 구조한다.")],
    chains2(O[5],O[6])))

# ---- G5 (38-41): 결말·당부 / 원본 O[7] 개관 그대로 재사용 ----
G5=merge([O[7]],"5 · 결말과 안전 당부",O[7].title,O[7].overview)

ALL=[G1,G2,G3,G4,G5]
# 오역 팁(mistips) 오버레이 — 학생용 전용 (병합·재번호된 최종 item_no+sid 기준)
import glob
MT={}
for f in sorted(glob.glob(os.path.join(BD,"mt_*.py"))):
    s=importlib.util.spec_from_file_location(os.path.basename(f)[:-3],f); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); MT.update(m.MT)
if MT:
    n_mt=0
    for p in ALL:
        for s in p.analysis.sentences:
            k=(p.item_no.strip(), s.id)
            if k in MT: s.mistips=list(MT[k]); n_mt+=len(s.mistips)
    print("오역 팁 적용:",n_mt,"개")
for p in ALL: finalize(p)
print("통합 후 소단원:",len(ALL))
ok=print_report(verify_passages(ALL))
for p in ALL: print("  -",p.item_no,"|",len(p.sentences),"문장 | 핵심문법:",p.overview.key_grammar.point)
if ok:
    FOOT="© 2026. ortica영어. All rights reserved."
    stem="공통영어2 능률_민병천_1과"
    render_lecture_pdf(ALL,f"{BD}/{stem}_학생용.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(ALL,f"{BD}/{stem}_강사용.pdf",teacher=True,footer_note=FOOT)
    for suf in ["학생용","강사용"]:
        d=fitz.open(f"{BD}/{stem}_{suf}.pdf"); print(f"  {suf}: {d.page_count}p"); d.close()
    print("RENDER OK")
else:
    print("ERROR — 렌더 보류")

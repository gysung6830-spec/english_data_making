# -*- coding: utf-8 -*-
"""감사 결과(항상표기 7종·생략·⑤ 반영)를 15개 지문에 소급 반영해 합본 재생성.
ADD[(item_no, sentence_id)] = [(tag, note), ...] — 개념 중복은 자동 스킵(같은 tag 접두 존재 시).
"""
import sys; sys.path.insert(0,'/home/user/english_data_making'); sys.path.insert(0,'.')
import gen_ol, gen_u12, gen_u13
from src.lecture_schemas import GrammarChip
from src.lecture_render import render_lecture_pdf
import fitz
ALL=list(gen_ol.OL_ALL)+list(gen_u12.U12_ALL)+list(gen_u13.ALL)
FOOT="© 2026. ortica영어. All rights reserved."

ADD = {
 # ---- Unit10-3 (도치 이미 있음 → 과거분사구만) ----
 ("Unit10-3",1): [("분사(과거분사구)","as practiced by the peoples = as (it was) practiced — forest gardening 수식(수동)")],
 # ---- Unit11-ANALYSIS ----
 ("Unit11-ANALYSIS",1): [("분사(현재분사 수식)","teenagers using social media = teenagers who use~ (후치수식)"),
                          ("공통 조동사 will","will [post] or [share] — will이 두 동사에 공통")],
 # ---- Unit11-1 ----
 ("Unit11-1",1): [("관계부사 생략","The reason [why] pessimists sound smart — reason 뒤 why 생략")],
 # ---- Unit11-2 ----
 ("Unit11-2",2): [("관계부사 생략","The reason [why] we understand differently — reason 뒤 why 생략")],
 ("Unit11-2",4): [("최상급","the closest item — 최상급")],
 ("Unit11-2",5): [("수동태","could be understood — 조동사+be+p.p.")],
 ("Unit11-2",6): [("수동태(진행)","a story ... was being told — be being p.p."),
                   ("목적격 관계대명사 생략","the story [which] he was about to hear — 목적격 관계대명사 생략")],
 # ---- Unit12-ANALYSIS (⑤ 이중부정 반영) ----
 ("Unit12-ANALYSIS",2): [("이중부정","doesn't mean ... isn't a big deal — 부정+부정=강한 긍정(⑤)")],
 ("Unit12-ANALYSIS",4): [("병렬 공통 조동사 can","can [sneak up and] [kill] — can이 두 동사에 공통")],
 ("Unit12-ANALYSIS",5): [("병렬 공통 to","to [detect] and [orient to] cars — to가 두 부정사에 공통")],
 # ---- Unit12-1 (⑤ 병렬구조 반영) ----
 ("Unit12-1",1): [("공통 조동사 may","may [change] or [appear to end] — may가 공통")],
 ("Unit12-1",2): [("병렬구조","find, cut it, peel it, cook it, and mash it — 동사원형 병렬(⑤)")],
 ("Unit12-1",3): [("공통 조동사 may","may [choose to use...] and [cut out...] — may가 공통")],
 ("Unit12-1",4): [("병렬구조","[no longer make...] and [choose instead to use...] — many families에 공통")],
 # ---- Unit12-2 (⑤=관계대명사 what; 분사구문 thus depleting은 ③ 유지) ----
 ("Unit12-2",1): [("공통 목적어(병렬)","[ignore] or [underestimate] the power of markets — 목적어 공통")],
 ("Unit12-2",5): [("분사구문","thus depleting resources even faster — 결과의 분사구문")],
 ("Unit12-2",6): [("수동태 be allowed","if markets are allowed to ~ — be+p.p."),
                   ("비교급 much longer","resources will last much longer — much 강조 비교급")],
 # ---- Unit12-3 (⑤ 양보 although 반영) ----
 ("Unit12-3",4): [("수동태 be run","how it might be run — 조동사+be+p.p.")],
 ("Unit12-3",5): [("양보 접속사 although","Although ~ should be avoided, 주절 — 양보(⑤)"),
                   ("비교급 better","new and better ways — 비교급")],
 ("Unit12-3",6): [("비교급 more easily","more easily resolved — more 비교급")],
 ("Unit12-3",8): [("접속사 that 생략","they believe (that) their views ~ — believe 뒤 that 생략")],
 # ---- Unit13-2 (⑤ so...that 반영) ----
 ("Unit13-2",1): [("관계부사 생략","the way (that/how) we interact — the way 뒤 관계부사 생략")],
 ("Unit13-2",4): [("공통 조동사 have","have [posted, pinned, tweeted, sent, received] — have가 공통")],
 ("Unit13-2",5): [("so+형용사+(that) 강조·결과","so prolific, (that) researchers worried — that 생략(⑤)")],
 # ---- Unit13-3 (⑤ 부정사 목적 반영) ----
 ("Unit13-3",2): [("수동태","comments are made / what they are told — be+p.p.")],
 ("Unit13-3",4): [("부정사 부사적용법(목적)","To help ~, to see ~, ... to defuse ~ — 목적의 부정사(⑤)")],
 # ---- Unit14-ANALYSIS (⑤ the 비교급 반영) ----
 ("Unit14-ANALYSIS",7): [("the 비교급~, the 비교급~","the more bystanders ~, the less likely ~ — 비례 비교(⑤)")],
 ("Unit14-ANALYSIS",8): [("반복어구 생략(대동사 would)","just as we hope we would (respond) — respond 반복 생략")],
 # ---- 서술형 Practice (⑤ 동명사 주어 반영) ----
 ("서술형 Practice",1): [("동명사 주어 수일치","learning to sing or play ... changes — 동명사구 주어=단수(⑤)")],
 ("서술형 Practice",3): [("수동태","you are 'right-lateralised' — be+p.p.")],
 # ---- Unit13-ANALYSIS (⑤ not A but B 반영) ----
 ("Unit13-ANALYSIS",1): [("최상급","One of the biggest reasons — biggest 최상급"),
                          ("관계부사 생략","the reasons [why] people are concerned — reasons 뒤 why 생략")],
 ("Unit13-ANALYSIS",4): [("상관접속사 not A but B","not looking for a performance, but for an address(⑤)")],
 ("Unit13-ANALYSIS",5): [("비교급","seem more human — more+형용사 비교급")],
 # ---- Unit13-1 (⑤ 분사구문 반영) ----
 ("Unit13-1",3): [("분사구문","when planted ~ / helping clean the water — 분사구문(⑤)"),
                   ("수동태","water that's delivered to them — is delivered, be+p.p."),
                   ("공통 목적어","[use] and [remove] nutrients — 목적어 nutrients 공통")],
 ("Unit13-1",5): [("수동태","are constructed — be+p.p.")],
 ("Unit13-1",6): [("수동태","what is known as biological engineering — is known as")],
}

def apply(passages):
    for p in passages:
        for s in p.analysis.sentences:
            key=(p.item_no.strip(), s.id)
            for tag,note in ADD.get(key,[]):
                if any(g.tag==tag for g in s.grammar): continue
                s.grammar.append(GrammarChip(tag=tag,note=note))
    return passages

if __name__=="__main__":
    apply(ALL)
    n=sum(len(v) for v in ADD.values())
    print("추가 대상 칩:",n)
    render_lecture_pdf(ALL,"hapbon_olympus_ALL_student.pdf",teacher=False,footer_note=FOOT)
    render_lecture_pdf(ALL,"hapbon_olympus_ALL_teacher.pdf",teacher=True,footer_note=FOOT)
    ds=fitz.open("hapbon_olympus_ALL_student.pdf"); dt=fitz.open("hapbon_olympus_ALL_teacher.pdf")
    print("합본 student",ds.page_count,"/ teacher",dt.page_count); ds.close(); dt.close()
    print("APPLIED")

"""학교 시험지(PDF/이미지/텍스트) → LLM 으로 blueprint 추출 → 학교 프로파일 학습.

'학교를 고르면 그 학교가 학습한 경향대로 동형이 생성된다'의 학습 입력을, 손으로 만든
blueprint.json 대신 실제 시험지에서 자동으로 뽑아 준다.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .core.models import Blueprint, BlueprintMeta, Item
from .pipeline import learn_from_blueprint
from .school import find_school, register_school, save_profile

_IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_UNDERLINE_TYPES = {"grammar", "grammar_vocab_mix", "vocab_odd"}

# 우리 생성기가 아는 유형(코드) — LLM 이 이 코드로만 답하도록 강제.
CHOICE_TYPES = {
    "grammar", "grammar_vocab_mix", "vocab_odd", "vocab_3blank_abc",
    "main_point", "title", "blank_single", "order", "irrelevant_sentence",
    "implied_meaning", "inference_mismatch", "dialogue_mismatch",
    "notice_match", "summary_ab",
}
ESSAY_TYPES = {
    "prep_find_and_translate", "word_arrange", "arrange_and_translate",
    "condition_write_inflect", "summary_fill_from_text", "blank_choose_no_change",
    "grammar_fix_and_answer", "dialogue_arrange_inflect", "chart_fix_and_arrange",
}

TYPE_GUIDE = (
    "[선다형(choice) 유형 코드 = 설명]\n"
    "- grammar: 밑줄 친 부분 중 어법상 틀린 것(밑줄 5개)\n"
    "- grammar_vocab_mix: 어법 또는 문맥상 낱말 쓰임이 부적절한 것(밑줄 5개)\n"
    "- vocab_odd: 문맥상 낱말 쓰임이 부적절한 것(밑줄 5개)\n"
    "- vocab_3blank_abc: (A)(B)(C) 네모 안 낱말 짝짓기\n"
    "- main_point: 요지/주장\n- title: 제목\n- blank_single: 빈칸 추론(한 개)\n"
    "- order: 글의 순서 (A)(B)(C)\n- irrelevant_sentence: 전체 흐름과 무관한 문장\n"
    "- implied_meaning: 밑줄 친 부분의 함의\n- inference_mismatch: 내용 (불)일치\n"
    "- dialogue_mismatch: 대화 내용 (불)일치\n- notice_match: 안내문 (불)일치\n"
    "- summary_ab: 요약문 (A),(B) 빈칸\n"
    "[서술형(essay) 유형 코드 = 설명]\n"
    "- prep_find_and_translate: 공통 전치사 쓰기 + 우리말 해석\n"
    "- word_arrange: [보기] 배열 영작\n"
    "- arrange_and_translate: [보기] 배열 영작 + 본문 우리말 답\n"
    "- condition_write_inflect: 괄호 단어 어형변형해 빈칸 채우기\n"
    "- summary_fill_from_text: 요약문 빈칸을 본문 단어로(변형 금지)\n"
    "- blank_choose_no_change: [보기]에서 골라 빈칸(변형 금지)\n"
    "- grammar_fix_and_answer: 어법 틀린 곳 고치기 + 영어 질문에 영어 답\n"
    "- dialogue_arrange_inflect: 대화문 [보기] 배열 영작(어형변형)\n"
    "- chart_fix_and_arrange: 도표와 다른 곳 고치기 + 배열 영작\n"
)

SYSTEM = (
    "당신은 학교 영어 내신 시험지를 분석해 '구조'와 '출제원리'를 함께 추출하는 전문가다. "
    "각 문항의 번호·구분(선다형/서술형)·유형 코드·배점·발문 문구를 식별하고, 이 학교의 "
    "어법 출제 축·오답 구성 방식·함정 스타일·난이도 경향을 파악한다. 유형은 반드시 주어진 "
    "코드 목록 중에서만 고른다. 반드시 요구된 JSON 스키마로만 답한다."
)


class ExamItemOut(BaseModel):
    no: int = Field(..., description="문항 번호(선다형·서술형 각각 1부터)")
    section: str = Field(..., description="'choice'(선다형) 또는 'essay'(서술형)")
    type: str = Field(..., description="유형 코드(주어진 목록 중 하나)")
    score: float = Field(..., description="이 문항의 배점(점)")
    underlines: int | None = Field(None, description="어법·어휘처럼 밑줄이 있으면 개수, 없으면 null")
    stem: str = Field("", description="이 문항의 발문(문제 지시문) 문구를 배점 표시 없이 그대로")


class ExamBlueprintOut(BaseModel):
    grade: int = Field(..., description="학년(1~3)")
    subject: str = Field(..., description="과목명(예: 공통영어1)")
    time_min: int = Field(..., description="시험 시간(분)")
    total_score: float = Field(..., description="총점(대개 100)")
    difficulty: str = Field("중", description="전반적 난이도: '상' 또는 '중' 또는 '하'")
    grammar_focus: list[str] = Field(default_factory=list, description=(
        "어법 문항이 자주 다루는 문법 포인트(예: 관계사, 태, 분사, 수일치, 시제). "
        "어법 문항의 정답을 근거로 3~6개."))
    style_notes: list[str] = Field(default_factory=list, description=(
        "이 학교의 출제 스타일 특징 3~6개(예: '오답은 지문 단어를 재활용한 함정', "
        "'빈칸은 결론부를 비움', '서술형은 본문 단어만 사용 조건', '지문 소재가 과학·환경 위주'). "
        "각 항목은 한 문장으로 간결하게."))
    items: list[ExamItemOut] = Field(..., description="문항 목록(선다형 먼저, 서술형 나중)")


def _read_exam_text(path: str | Path) -> str:
    """시험지 원문 텍스트(한글 유지). 이중언어 정제를 쓰지 않는다(발문·배점 보존)."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext in (".txt", ".md"):
        return p.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(str(p)) as pdf:
            return "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    if ext in (".hwp", ".hwpx"):
        from .ingest.loader import _read_hwp
        return _read_hwp(p)
    return ""


def _clean_stem(s: str) -> str:
    """발문에서 배점 표시·앞 번호를 제거해 순수 발문 문구만 남긴다."""
    s = re.sub(r"\[[^\]]*점\]", "", s or "")        # [3점] 제거
    s = re.sub(r"^\s*\d+\s*[.)]\s*", "", s)          # 앞 번호 '1.' 제거
    return re.sub(r"\s+", " ", s).strip()


_DIFF_MAP = {"상": "high", "중": "mid", "하": "low",
             "high": "high", "mid": "mid", "low": "low"}


def _coerce_type(section: str, t: str) -> str:
    """알 수 없는 유형 코드는 구분에 맞는 안전한 기본값으로 보정."""
    t = (t or "").strip()
    if section == "choice":
        return t if t in CHOICE_TYPES else "main_point"
    return t if t in ESSAY_TYPES else "word_arrange"


def extract_blueprint(client: Any, files: list[str | Path], grade: int = 1) -> ExamBlueprintOut:
    """시험지 파일들에서 blueprint 구조를 LLM 으로 추출한다."""
    imgs = [f for f in files if Path(f).suffix.lower() in _IMG_EXT]
    text_files = [f for f in files if f not in imgs]
    body = "\n\n".join(_read_exam_text(f) for f in text_files).strip()

    prompt = (
        f"{TYPE_GUIDE}\n\n"
        "아래 학교 시험지를 분석하라.\n"
        "(1) 구조: '모든 문항'의 번호·구분(choice/essay)·유형 코드·배점·발문 문구(stem)를 "
        "추출한다. 선다형과 서술형을 구분하고, 배점 합이 총점과 맞도록 각 문항 배점을 읽는다. "
        "어법·어휘 유형이면 밑줄 개수(대개 5)를 underlines 에 넣는다.\n"
        "(2) 출제원리: 이 학교의 어법 출제 축(grammar_focus), 출제 스타일 특징(style_notes: "
        "오답 구성·함정·소재·서술형 조건 등), 전반적 난이도(difficulty)를 파악한다.\n\n"
        f"[학교 시험지 내용]\n{body if body else '(첨부 이미지 참조)'}"
    )
    image_path = imgs[0] if imgs and not body else None
    return client.structured(SYSTEM, prompt, ExamBlueprintOut, max_retries=2,
                             image_path=image_path)


def _build_blueprint(school_id: str, name: str, level: str,
                     out: ExamBlueprintOut) -> Blueprint:
    """추출 결과 → Blueprint(배점 합을 총점에 정규화)."""
    choice = [it for it in out.items if it.section == "choice"]
    essay = [it for it in out.items if it.section != "choice"]
    items: list[Item] = []
    for seq, it in enumerate(choice, 1):
        typ = _coerce_type("choice", it.type)
        ul = it.underlines if it.underlines else (5 if typ in _UNDERLINE_TYPES else None)
        items.append(Item(no=seq, section="choice", type=typ,
                          score=round(float(it.score), 2), underlines=ul))
    for seq, it in enumerate(essay, 1):
        items.append(Item(no=seq, section="essay", type=_coerce_type("essay", it.type),
                          score=round(float(it.score), 2)))
    # 배점 합 정규화(검증기 통과 보장) — 마지막 문항으로 오차 보정
    total = round(float(out.total_score) or 100.0, 2)
    s = round(sum(i.score for i in items), 2)
    if items and abs(s - total) >= 0.01:
        items[-1].score = round(items[-1].score + (total - s), 2)

    meta = BlueprintMeta(
        school_id=school_id, name=name or school_id, level=level,
        grade=int(out.grade or 1), subject=out.subject or "영어",
        time_min=int(out.time_min or 50), total_score=total, learned=True)
    return Blueprint(meta=meta, items=items)


def learn_exam(school_id: str, exam_name: str, files: list[str | Path],
               client: Any, name: str = "", level: str = "high",
               new_school: bool = False) -> tuple[dict[str, Any], Blueprint]:
    """시험지 파일에서 blueprint 를 추출해 그 학교 프로파일에 누적 학습한다.

    반환: (갱신된 profile dict, 추출된 blueprint).
    """
    school = find_school(school_id)
    if school is None or new_school:
        register_school(school_id, name or school_id, level)
        school = find_school(school_id) or {"name": name, "level": level}

    out = extract_blueprint(client, files)
    bp = _build_blueprint(school_id, school.get("name", name or school_id),
                          school.get("level", level), out)
    prof = learn_from_blueprint(school_id, exam_name, bp,
                                name=school.get("name", name or school_id),
                                level=school.get("level", level))

    # ── 출제원리 학습분 병합(생성 시 stem_style·grammar_focus·notes·난이도로 주입됨) ──
    ss = prof.setdefault("stem_style", {})
    for it in out.items:
        stem = _clean_stem(it.stem)
        if len(stem) > 4:                       # 유형별 대표 발문 문구
            ss[_coerce_type(it.section, it.type)] = stem
    if out.grammar_focus:
        prof["grammar_focus"] = list(dict.fromkeys(
            (prof.get("grammar_focus") or []) + list(out.grammar_focus)))
    if out.style_notes:
        notes = prof.get("notes") or []
        for n in out.style_notes:
            n = (n or "").strip()
            if n and n not in notes:
                notes.append(n)
        prof["notes"] = notes
    prof["difficulty_trend"] = _DIFF_MAP.get((out.difficulty or "").strip(), "mid")
    save_profile(school_id, prof)
    return prof, bp

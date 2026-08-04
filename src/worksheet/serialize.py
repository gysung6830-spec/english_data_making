"""분석 결과(Analysis) ↔ JSON 직렬화.

API 로 한 번 분석한 결과를 JSON 으로 저장해 두면, 나중에 '제목·헤더만' 고쳐 다시
출력할 때 재분석(API 비용) 없이 그대로 렌더할 수 있다. asdict 로 저장하고, 불러올
때는 누락 필드에 안전한 기본값을 채워 dataclass 로 복원한다(손으로 편집한 JSON 도 허용).
"""
from __future__ import annotations

import json
from dataclasses import asdict

from .models import (Analysis, FlowStep, GrammarChip, KeyWord, LitChunk,
                     LiteralSentence, Point, Sentence, Token, VocabEntry)

SCHEMA = "ortica.worksheet.analysis/1"      # 파일 형식 식별자(버전 포함)


# ---------------------------------------------------------------------------
# 저장(dump)
# ---------------------------------------------------------------------------
def analyses_to_json(analyses, indent: int = 2) -> str:
    """Analysis 목록을 JSON 문자열로. (지문 여러 개면 배열)"""
    payload = {"schema": SCHEMA, "analyses": [asdict(a) for a in _as_list(analyses)]}
    return json.dumps(payload, ensure_ascii=False, indent=indent)


def _as_list(analyses):
    if isinstance(analyses, Analysis):
        return [analyses]
    return list(analyses)


# ---------------------------------------------------------------------------
# 복원(load) — 누락 키에 기본값을 채워 방어적으로 복원
# ---------------------------------------------------------------------------
def _token(d: dict) -> Token:
    return Token(
        text=d.get("text", ""),
        role=d.get("role"),
        note=d.get("note"),
        note_kind=d.get("note_kind", "lbl"),
        wrong=d.get("wrong"),
        above=d.get("above"),
        hl=d.get("hl"),
        underline=bool(d.get("underline", False)),
        color=d.get("color"),
        slash=bool(d.get("slash", False)),
    )


def _point(d: dict) -> Point:
    return Point(kind=d.get("kind", "reading"),
                 caption=d.get("caption", ""),
                 body_html=d.get("body_html", ""))


def _sentence(d: dict) -> Sentence:
    lines = [[_token(t) for t in (ln or [])] for ln in d.get("lines", [])]
    return Sentence(
        index=int(d.get("index", 0) or 0),
        lines=lines,
        translation=d.get("translation", "") or "",
        reading_ko=d.get("reading_ko", "") or "",
        badge=d.get("badge"),
        gloss_en=d.get("gloss_en"),
        gloss_ko=d.get("gloss_ko"),
        refs=list(d.get("refs") or []),
        points=[_point(p) for p in d.get("points", [])],
    )


def _vocab(d: dict) -> VocabEntry:
    return VocabEntry(word=d.get("word", ""), meaning=d.get("meaning", ""),
                      syn=d.get("syn", ""), ant=d.get("ant", ""), sent=d.get("sent"))


def _flow(d: dict) -> FlowStep:
    return FlowStep(label=d.get("label", ""), text=d.get("text", ""),
                    easy=d.get("easy", ""), sentences=d.get("sentences", ""))


def _keyword(d: dict) -> KeyWord:
    return KeyWord(word=d.get("word", ""), meaning=d.get("meaning", ""))


def _litchunk(d: dict) -> LitChunk:
    return LitChunk(english=d.get("english", ""), korean=d.get("korean", ""),
                    words=[_keyword(w) for w in d.get("words", [])])


def _chip(d: dict) -> GrammarChip:
    return GrammarChip(point=d.get("point", ""), explanation=d.get("explanation", ""),
                       key=bool(d.get("key", False)), ci=d.get("ci"))


def _literal(d: dict) -> LiteralSentence:
    return LiteralSentence(
        no=int(d.get("no", 0) or 0),
        chunks=[_litchunk(c) for c in d.get("chunks", [])],
        grammar=[_chip(g) for g in d.get("grammar", [])],
        note=d.get("note", ""),
    )


def _analysis(d: dict) -> Analysis:
    return Analysis(
        title_en=d.get("title_en", "") or "",
        title_ko=d.get("title_ko", "") or "",
        summary=d.get("summary", "") or "",
        summary_easy=d.get("summary_easy", "") or "",
        lecture_label=str(d.get("lecture_label", "") or ""),
        source_name=d.get("source_name", "") or "",
        date=d.get("date", "") or "",
        sentences=[_sentence(s) for s in d.get("sentences", [])],
        vocab=[_vocab(v) for v in d.get("vocab", [])],
        flow=[_flow(f) for f in d.get("flow", [])],
        literal=[_literal(l) for l in d.get("literal", [])],
        back_tight=bool(d.get("back_tight", False)),
        front_density=d.get("front_density", "") or "",
        vocab_test=[_vocab(v) for v in d.get("vocab_test", [])],
    )


def analyses_from_json(text: str) -> list[Analysis]:
    """JSON 문자열 → Analysis 목록. {'analyses': [...]} 또는 [...] 모두 허용."""
    data = json.loads(text)
    items = data.get("analyses") if isinstance(data, dict) else data
    if not items:
        return []
    return [_analysis(a) for a in items]

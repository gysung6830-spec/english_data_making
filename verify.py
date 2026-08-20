# -*- coding: utf-8 -*-
"""강의컨셉 교재(LecturePassage) 자동검증기.

생성 직후 호출해 '형식·정합성 오류'를 기계적으로 걸러낸다(사람 검수 이전 1차 방어선).

사용법:
    from verify import verify_passages, print_report
    issues = verify_passages(passages)      # passages: LecturePassage 하나 또는 리스트
    ok = print_report(issues)               # 콘솔 출력 + ERROR 없으면 True

    # 여러 지문을 합본으로 낼 때는 리스트로 넘겨야 교차검사(핵심문법 중복·정답 위치 쏠림)까지 돈다.

CLI:
    python verify.py            # 내장 mock 지문으로 자기점검(스모크 테스트)
    python verify.py mod:NAME   # 파이썬 모듈 mod 의 전역 NAME(리스트/단일)을 불러 검증
"""
from __future__ import annotations

import importlib
import re
import sys
from collections import Counter
from dataclasses import dataclass

from markupsafe import escape

from src.lecture_schemas import STANCES, STRUCTURES, LecturePassage

_MARK = re.compile(r"\[\[|\]\]")
_BLANK = re.compile(r"\[\[.*?\]\]", re.S)  # 빈칸 한 개(통째/단어)
_ELLIPSIS = ("...", "…")   # ASCII 세 점 · 유니코드 말줄임표

# 빈칸을 안 뚫어도 되는 '순전한 기능어'(관사·전치사·접속사·대명사·be동사 등).
# 이 집합에 없는 4글자+ 단어가 조각에 있으면 '내용어가 있는데 빈칸이 없다'고 본다.
_FUNC = {
    "the", "a", "an", "and", "or", "but", "so", "for", "nor", "yet",
    "of", "to", "in", "on", "at", "by", "with", "from", "into", "onto",
    "as", "is", "am", "are", "was", "were", "be", "been", "being",
    "it", "its", "he", "she", "they", "them", "his", "her", "their",
    "we", "our", "us", "you", "your", "i", "my", "me", "this", "that",
    "these", "those", "there", "here", "then", "not", "no", "do", "does",
    "did", "has", "have", "had", "will", "would", "can", "could", "may",
    "might", "must", "shall", "should", "up", "out", "off", "over", "than",
    "too", "very", "also", "just", "only", "about", "if", "when", "while",
}


def _content_words(en: str) -> int:
    """조각에서 '내용어(4글자+, 기능어 아님)' 개수. 0이면 빈칸을 안 뚫어도 되는 조각."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", _strip(en).lower())
    return sum(1 for w in words if len(w) >= 4 and w not in _FUNC)


def _strip(s: str) -> str:
    return _MARK.sub("", s or "")


def _norm(s: str) -> str:
    """대소문자·따옴표·공백·구두점 주변 여백을 정규화해 문자열 비교용으로 만든다."""
    s = _strip(s).replace("’", "'").replace("‘", "'").replace('"', "'")
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"\s*([.,;:!?—-])\s*", r"\1", s)
    return s


def _tokens(s: str) -> set[str]:
    """문법명에서 비교용 토큰(한글 2자+ / 영단어)을 뽑는다."""
    s = _strip(s)
    kr = re.findall(r"[가-힣]{2,}", s)
    en = [e.lower() for e in re.findall(r"[A-Za-z]+", s)]
    return set(kr) | set(en)


@dataclass
class Issue:
    level: str   # "ERROR" | "WARN"
    where: str
    msg: str


def _as_list(passages) -> list[LecturePassage]:
    if isinstance(passages, LecturePassage):
        return [passages]
    return list(passages)


def verify_passages(passages, *, cross_check: bool = True) -> list[Issue]:
    """LecturePassage(들)의 형식·정합성을 검사해 Issue 리스트를 돌려준다.

    ERROR = 반드시 고쳐야 하는 결함 / WARN = 확인이 필요한 항목.
    cross_check=True 면 여러 지문 간(합본) 핵심문법 중복·정답 위치 분포까지 본다.
    """
    reps = _as_list(passages)
    issues: list[Issue] = []
    def err(w, m): issues.append(Issue("ERROR", w, m))
    def warn(w, m): issues.append(Issue("WARN", w, m))

    for p in reps:
        tag = (p.item_no or p.theme_ko or "?").strip()
        n = len(p.sentences)
        ov = p.overview
        htext = str(escape(" ".join(s.text for s in p.sentences)))

        # 1) 문장 분석 개수·번호
        ids = sorted(s.id for s in p.analysis.sentences)
        if ids != list(range(1, n + 1)):
            err(tag, f"문장 분석 번호가 1~{n}과 불일치: {ids}")

        # 2) 문장별: ①원문 ↔ ③조각 일치 / 오답 존재 / 말줄임표
        by_id = {s.id: s for s in p.analysis.sentences}
        for sid in range(1, n + 1):
            s = by_id.get(sid)
            if s is None:
                continue
            raw = p.sentences[sid - 1].text
            joined = " ".join(c.en for c in s.chunks)
            if _norm(raw) != _norm(joined):
                err(f"{tag} S{sid}", "③ 조각(en)을 이으면 ①원문과 불일치(누락/오타/…)")
            if not s.misreads:
                err(f"{tag} S{sid}", "오답(misread)이 없음")
            if not s.chunks:
                err(f"{tag} S{sid}", "③ 끊어읽기 조각이 없음")
            # ③ 끊어읽기 영↔한 정합 · 한글 해석 누락
            for ci, c in enumerate(s.chunks, 1):
                en_t = _strip(c.en).strip()
                ko_t = _strip(c.ko).strip()
                if any(e in c.en for e in _ELLIPSIS):
                    err(f"{tag} S{sid}", f"③ 영어 조각에 말줄임표: {en_t[:40]!r}")
                if not en_t:
                    err(f"{tag} S{sid}", f"{ci}번째 조각의 영어가 비어 있음")
                if not ko_t:
                    err(f"{tag} S{sid}", f"{ci}번째 조각의 '한글 해석이 누락'됨 (en={en_t[:30]!r})")
                # 영어 칸에 알파벳이 없거나 / 한글 칸에 한글이 없으면 영↔한 뒤바뀜·미번역 의심
                elif en_t and not re.search(r"[A-Za-z]", en_t):
                    warn(f"{tag} S{sid}", f"{ci}번째 영어 조각에 알파벳이 없음(영↔한 뒤바뀜 의심): {en_t[:30]!r}")
                elif ko_t and not re.search(r"[가-힣]", ko_t):
                    warn(f"{tag} S{sid}", f"{ci}번째 한글 조각에 한글이 없음(미번역·뒤바뀜 의심): {ko_t[:30]!r}")
                # 공백으로 둘러싸인 '/'(끊어읽기 구분자 모양)가 조각 안에 있으면 영·한 조각 수가 어긋나 보임
                # ('and/or', 'either/or' 처럼 문자 사이 '/'는 정상이므로 제외)
                if re.search(r"(^|\s)/(\s|$)", c.en) or re.search(r"(^|\s)/(\s|$)", c.ko):
                    warn(f"{tag} S{sid}", f"{ci}번째 조각에 구분자 모양의 ' / '가 있어 끊어읽기와 겹칠 수 있음")
            # 영어 조각 수 == 한글 조각 수 (Chunk 쌍이므로 항상 같아야 함)
            n_en = sum(1 for c in s.chunks if _strip(c.en).strip())
            n_ko = sum(1 for c in s.chunks if _strip(c.ko).strip())
            if n_en != n_ko:
                err(f"{tag} S{sid}", f"③ 영어 조각 수({n_en})와 한글 조각 수({n_ko})가 불일치")

            # ③ 빈칸 규칙: (1) 문장 전체 빈칸 0개 = 학생이 채울 게 없음
            #             (2) '내용어가 있는 조각'은 빈칸을 하나 뚫어야 함(순전한 기능어 조각만 예외)
            #             (3) 통째 빈칸(조각 전체 [[ ]])은 문장당 최대 2개
            if s.chunks:
                n_blank_total = sum(len(_BLANK.findall(c.ko)) for c in s.chunks)
                if n_blank_total == 0:
                    warn(f"{tag} S{sid}", "③ 이 문장에 빈칸이 하나도 없음(학생용에서 채울 게 없음)")
                n_whole = 0
                for ci, c in enumerate(s.chunks, 1):
                    ko_raw = c.ko or ""
                    en_raw = c.en or ""
                    if re.fullmatch(r"\s*\[\[.*\]\][\.,\?\!;:”'\)]*\s*", ko_raw, re.S):
                        n_whole += 1
                    if "[[" not in ko_raw and _content_words(en_raw) >= 1:
                        warn(f"{tag} S{sid}",
                             f"{ci}번째 조각에 내용어가 있는데 빈칸이 없음: {_strip(en_raw).strip()[:34]!r}")
                    # en 과 ko 의 빈칸 유무는 짝이 맞아야 함
                    if ("[[" in ko_raw) != ("[[" in en_raw):
                        warn(f"{tag} S{sid}",
                             f"{ci}번째 조각의 영어/한글 빈칸 유무가 어긋남: en={_strip(en_raw).strip()[:24]!r}")
                if n_whole > 2:
                    warn(f"{tag} S{sid}", f"③ 통째 빈칸이 {n_whole}개(문장당 최대 2개 권장)")

            # ④ '오답만 읽어도 이해' — 각 오답 해설(why)이 실질적이어야(뜻을 설명)
            for mi, m in enumerate(s.misreads, 1):
                st = _strip(m.statement).strip()
                wy = _strip(m.why).strip()
                if not st:
                    err(f"{tag} S{sid}", f"{mi}번째 오답의 '틀린 진술(statement)'이 비어 있음")
                if not wy:
                    err(f"{tag} S{sid}", f"{mi}번째 오답의 '해설(why)'이 비어 있음")
                elif len(wy) < 15:
                    warn(f"{tag} S{sid}",
                         f"{mi}번째 오답 해설이 너무 짧아 뜻 전달 부족(<15자): {wy!r}")

            # 오역 팁(mistips, 학생용 전용) 형식 검사
            for ti, t in enumerate(getattr(s, "mistips", []) or [], 1):
                tt = _strip(t).strip()
                if not tt:
                    err(f"{tag} S{sid}", f"{ti}번째 오역 팁이 비어 있음")
                    continue
                if t.count("[[") != t.count("]]"):
                    err(f"{tag} S{sid}", f"{ti}번째 오역 팁의 [[ ]] 짝이 안 맞음: {tt[:30]!r}")
                if any(e in t for e in _ELLIPSIS):
                    warn(f"{tag} S{sid}", f"{ti}번째 오역 팁에 말줄임표: {tt[:30]!r}")
                if len(tt) < 12:
                    warn(f"{tag} S{sid}", f"{ti}번째 오역 팁이 너무 짧음(<12자): {tt!r}")

        # 2-b) ④ '오답만 읽어도 이해되도록' 설계 점검(지문 단위)
        #   - 문장 커버리지: 모든 문장이 오답을 하나씩 가져야(위 S{sid} 루프에서 ERROR) '오답만 읽어도
        #     전 문장을 훑는다'가 성립. 여기서는 '지칭·함축' 층위가 오답 스트림에 담겼는지 본다.
        sents = p.analysis.sentences
        if len(sents) >= 5:
            allm = [m for s in sents for m in s.misreads]
            blob = " ".join(_strip(m.statement) + " " + _strip(m.why) for m in allm)
            has_ref = bool(re.search(r"지칭|가리키|가리켜", blob))
            has_imp = bool(re.search(r"함축|반어|가정법|속뜻|진짜 뜻|실제로는", blob))
            # 지시어(this/that/they/these/those/it 계열)가 여러 번 쓰였는데 '지칭' 오답이 없으면 누락 의심
            en_all = " ".join(si.english for si in sents)
            n_dem = len(re.findall(r"\b(this|that|these|those|they|them|their|it|its)\b",
                                   en_all, re.IGNORECASE))
            if n_dem >= 3 and not has_ref:
                warn(tag, "④ 지시어가 여러 번 나오는데 '지칭' 오답이 없음(오답만 읽어도 지칭 이해 목표 미달)")
            if len(sents) >= 6 and not has_imp:
                warn(tag, "④ '함축·속뜻(반어/가정법 등)'을 다루는 오답이 없음(오답만 읽어도 함축 이해 목표 미달)")

        # 3) ④ 재진술 표현이 지문에 실제로 있는지(형광펜 매칭)
        for c in ov.restatement_chains:
            for e in c.expressions:
                if any(x in e for x in _ELLIPSIS):
                    err(tag, f"재진술 표현에 말줄임표 → 형광펜 매칭 실패: {e!r}")
                    continue
                e2 = str(escape(e)).strip()
                if e2 and not re.search(re.escape(e2), htext, re.IGNORECASE):
                    err(tag, f"재진술 표현이 지문에 없음 → 형광펜 안 됨: {e!r}")

        # 4) stance / structure 값
        if ov.stance not in STANCES:
            err(tag, f"stance 값 오류: {ov.stance!r}")
        if ov.structure not in STRUCTURES:
            err(tag, f"structure 값 오류: {ov.structure!r}")

        # 5) ④ 흐름이 1~n 문장을 다 덮는지
        covered: set[int] = set()
        for b in ov.flow_blocks:
            for part in re.split(r"[,·]", b.sentence_range or ""):
                part = part.strip().replace("문장", "")
                m = re.match(r"(\d+)\s*[~-]\s*(\d+)", part)
                if m:
                    covered |= set(range(int(m.group(1)), int(m.group(2)) + 1))
                elif part.isdigit():
                    covered.add(int(part))
        miss = set(range(1, n + 1)) - covered
        if miss:
            warn(tag, f"④ 흐름이 안 덮는 문장: {sorted(miss)}")

        # 6) ⑤ 연습문제 구성·정답
        kg = ov.key_grammar
        d = list(kg.drills)
        nmc = sum(1 for x in d if x.kind == "객관식")
        nwr = sum(1 for x in d if x.kind == "영작")
        if len(d) != 5:
            err(tag, f"연습문제가 5개가 아님({len(d)})")
        if nmc != 3 or nwr != 2:
            warn(tag, f"'객관식3+영작2' 구성 아님(객{nmc}/영{nwr})")
        for x in d:
            if x.kind == "객관식":
                if x.answer not in x.options:
                    err(tag, f"객관식 정답이 보기에 없음: {x.answer[:30]!r}")
                if any(e in x.question for e in _ELLIPSIS):
                    warn(tag, f"객관식 문항에 말줄임표: {x.question[:40]!r}")
            if x.kind == "영작" and not x.words:
                warn(tag, "영작 제시어(words)가 비어 있음")

        # 7) ⑤ 핵심문법이 '그 문법이 나온 문장'의 ③칩에도 있는지(중복조율 삭제 규칙)
        src = _norm(kg.source_sentence)
        if src:
            hit = None
            head = " ".join(src.split()[:6])
            for sid in range(1, n + 1):
                t = _norm(p.sentences[sid - 1].text)
                if t and (t in src or (head and head in t) or src[:40] in t):
                    hit = by_id.get(sid)
                    break
            if hit is not None:
                core = _tokens(kg.point)
                chip_tokens: set[str] = set()
                for g in hit.grammar:
                    chip_tokens |= _tokens(g.tag)
                if core and not (core & chip_tokens):
                    warn(f"{tag} S{hit.id}",
                         f"⑤ 핵심문법('{kg.point}')이 그 문장 ③칩에 안 보임")

    # 8) 교차검사(합본): 핵심문법 중복 · 객관식 정답 위치 쏠림
    if cross_check and len(reps) > 1:
        seen: dict[str, str] = {}
        for p in reps:
            pt = p.overview.key_grammar.point
            if pt in seen:
                err("합본", f"핵심문법 중복: '{pt}' ({seen[pt]} ↔ {p.item_no})")
            else:
                seen[pt] = p.item_no or "?"
        pos: Counter = Counter()
        for p in reps:
            for x in p.overview.key_grammar.drills:
                if x.kind == "객관식" and x.answer in x.options:
                    pos[x.options.index(x.answer)] += 1
        total = sum(pos.values())
        if total and max(pos.values()) / total > 0.55:
            warn("합본", f"객관식 정답 위치 쏠림: {dict(sorted(pos.items()))} "
                        "(0=1번,1=2번,2=3번 · 균등 권장)")

    return issues


def print_report(issues: list[Issue]) -> bool:
    """이슈를 콘솔에 출력하고 ERROR 가 하나도 없으면 True 를 반환한다."""
    errs = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]
    for i in errs:
        print(f"  ✗ ERROR [{i.where}] {i.msg}")
    for i in warns:
        print(f"  ⚠ WARN  [{i.where}] {i.msg}")
    if not issues:
        print("  ✓ 이상 없음 (ERROR 0 · WARN 0)")
    else:
        print(f"  → ERROR {len(errs)} · WARN {len(warns)}")
    return not errs


def _load(spec: str):
    """'module:NAME' 형태에서 전역 NAME 을 불러온다."""
    mod_name, _, attr = spec.partition(":")
    mod = importlib.import_module(mod_name)
    return getattr(mod, attr or "PASSAGES")


def main(argv: list[str]) -> int:
    if argv:
        passages = _load(argv[0])
        print(f"[verify] {argv[0]} 검증")
    else:
        from samples.lecture_mock import mock_lecture_passage
        passages = mock_lecture_passage()
        print("[verify] 내장 mock 지문 자기점검")
    ok = print_report(verify_passages(passages))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

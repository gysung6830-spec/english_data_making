#!/usr/bin/env python3
"""교습소 자료·운영 관리 CLI.

지문을 분석해 PDF 를 뽑는 일은 `run.py` 가, **쌓인 자료를 굴리는 일**은 이 파일이 한다.

    python manage.py status                        전체 현황 한 장
    python manage.py library list --level H1       자료 찾기
    python manage.py curriculum plan H1            주차별 진도표
    python manage.py curriculum gap                레벨별 자료 부족분
    python manage.py class next H1A                다음 회차 준비물
    python manage.py pack review --class H1A --last 8   누적 복습 자료 만들기

각 명령에 `-h` 를 붙이면 옵션 설명이 나옵니다.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

from src.config import ROOT, load_config
from src.curriculum import load_curriculum
from src.library import CATEGORIES, STATUSES, Library
from src.school import School


# ---------------------------------------------------------------------------
# 표 출력 (한글은 폭이 2 이므로 직접 계산해야 열이 맞는다)
# ---------------------------------------------------------------------------
def _w(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1
               for ch in str(text))


def _pad(text: str, width: int) -> str:
    return str(text) + " " * max(width - _w(text), 0)


def table(headers: list[str], rows: list[list], empty: str = "(없음)") -> None:
    if not rows:
        print(f"  {empty}")
        return
    cols = [max(_w(h), *(_w(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("  " + "  ".join(_pad(h, c) for h, c in zip(headers, cols)))
    print("  " + "  ".join("-" * c for c in cols))
    for r in rows:
        print("  " + "  ".join(_pad(v, c) for v, c in zip(r, cols)))


def head(title: str) -> None:
    print()
    print(f"── {title} " + "─" * max(52 - _w(title), 0))


def _csv(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


# ---------------------------------------------------------------------------
# library
# ---------------------------------------------------------------------------
def cmd_library_add(args) -> int:
    from src.schemas import Report

    lib = Library()
    added = skipped = 0
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            print(f"  ! 파일 없음: {path}")
            continue
        try:
            report = Report.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ! 분석 결과를 읽지 못했습니다 ({path.name}): {e}")
            continue
        mat, created = lib.add(report, level=args.level, category=args.category,
                               source=args.source, tags=_csv(args.tags),
                               status=args.status, notes=args.notes,
                               allow_duplicate=args.allow_duplicate)
        if created:
            added += 1
            print(f"  + {mat.id}  {mat.title}")
        else:
            skipped += 1
            print(f"  = 이미 있는 지문 → {mat.id} ({path.name})")
    if added:
        lib.rebuild_catalog()
    print(f"\n  등록 {added}건 · 중복 건너뜀 {skipped}건")
    return 0


def cmd_library_list(args) -> int:
    lib = Library()
    mats = lib.search(level=args.level, category=args.category, tag=args.tag,
                      status=args.status, genre=args.genre, q=args.q,
                      unused=args.unused)
    head(f"자료 목록 ({len(mats)}건)")
    table(["ID", "레벨", "유형", "제목", "주제", "어휘", "상태", "사용"],
          [[m.id, m.level or "-", m.category, m.title[:28],
            (m.theme_ko or "-")[:24], str(m.stats.vocab), m.status,
            str(len(m.used_in))] for m in mats[:args.limit]])
    if len(mats) > args.limit:
        print(f"\n  … 외 {len(mats) - args.limit}건 (--limit 로 더 보기)")
    return 0


def cmd_library_show(args) -> int:
    lib = Library()
    mat = lib.get(args.id)
    if mat is None:
        print(f"  자료를 찾을 수 없습니다: {args.id}")
        return 1
    head(f"{mat.id} · {mat.title}")
    for k, v in [("주제", mat.theme_ko), ("레벨", mat.level), ("유형", mat.category),
                 ("출처", mat.source), ("문항번호", mat.item_no), ("장르", mat.genre),
                 ("상태", mat.status), ("등록일", mat.added),
                 ("태그", ", ".join(mat.tags)), ("지문", mat.hash),
                 ("사용이력", ", ".join(mat.used_in)), ("메모", mat.notes)]:
        if v:
            print(f"  {_pad(k, 10)} {v}")
    print(f"  {_pad('통계', 10)} 단어 {mat.stats.words} · 문장 {mat.stats.sentences} "
          f"· 문장당 {mat.stats.avg_sentence} · 어휘 {mat.stats.vocab} "
          f"· 문법 {mat.stats.grammar}")
    head("핵심 어휘")
    print("  " + ", ".join(mat.vocab) if mat.vocab else "  (없음)")
    head("문법 포인트")
    for i, g in enumerate(mat.grammar_points, 1):
        print(f"  {i:2d}. {g}")
    return 0


def cmd_library_set(args) -> int:
    lib = Library()
    fields = {}
    if args.level:
        fields["level"] = args.level.upper()
    if args.status:
        fields["status"] = args.status
    if args.tags is not None:
        fields["tags"] = _csv(args.tags)
    if args.notes is not None:
        fields["notes"] = args.notes
    if args.source is not None:
        fields["source"] = args.source
    if not fields:
        print("  바꿀 항목을 지정하세요 (--level/--status/--tags/--notes/--source)")
        return 1
    mat = lib.update(args.id, **fields)
    lib.rebuild_catalog()
    print(f"  수정 완료: {mat.id} → {fields}")
    return 0


def cmd_library_index(args) -> int:
    lib = Library()
    cj, cm = lib.rebuild_catalog()
    print(f"  색인 갱신: {cj.relative_to(ROOT)} · {cm.relative_to(ROOT)}")
    return 0


def cmd_library_stats(args) -> int:
    st = Library().stats()
    head("자료 라이브러리 통계")
    print(f"  총 자료 {st['total']}건 · 고유 어휘 {st['vocab_unique']}개 "
          f"· 미사용 {st['unused']}건")
    head("레벨별")
    table(["레벨", "자료 수"], [[k, str(v)] for k, v in st["by_level"].items()])
    head("유형별")
    table(["유형", "자료 수"], [[k, str(v)] for k, v in st["by_category"].items()])
    head("상태별")
    table(["상태", "자료 수"], [[k, str(v)] for k, v in st["by_status"].items()])
    return 0


def cmd_library_dupes(args) -> int:
    """같은 지문을 두 번 등록했는지 확인(지문 fingerprint 기준)."""
    lib = Library()
    groups: dict[str, list[str]] = {}
    for m in lib.all():
        groups.setdefault(m.hash, []).append(m.id)
    dupes = {h: ids for h, ids in groups.items() if len(ids) > 1}
    head(f"중복 의심 자료 ({len(dupes)}건)")
    table(["지문 fingerprint", "자료 ID"],
          [[h, ", ".join(ids)] for h, ids in dupes.items()],
          empty="중복 없음 👍")
    return 0


# ---------------------------------------------------------------------------
# curriculum
# ---------------------------------------------------------------------------
def cmd_curr_levels(args) -> int:
    cur = load_curriculum()
    head(f"레벨 체계 ({len(cur.levels)}단계 · 목표 자료 {cur.total_target()}편)")
    table(["레벨", "이름", "학년", "목표어휘", "지문길이", "문장길이", "목표자료", "중점"],
          [[lv.code, lv.name, lv.grades, str(lv.vocab_target),
            f"{lv.passage_words[0]}~{lv.passage_words[1]}",
            f"{lv.sentence_words[0]}~{lv.sentence_words[1]}",
            str(lv.material_target), lv.focus[:26]] for lv in cur.levels])
    return 0


def cmd_curr_plan(args) -> int:
    cur = load_curriculum()
    lv = cur.level(args.level)
    rows = cur.plan(lv.code)
    head(f"{lv.code} {lv.name} · {cur.term_weeks}주 진도표 ({lv.grades})")
    print(f"  중점: {lv.focus}")
    print(f"  주당 지문 {cur.passages_per_week}편 → 학기당 "
          f"{cur.passages_per_week * cur.term_weeks}편 필요\n")
    table(["주", "문법 주제", "지문", "평가", "리포트"],
          [[str(r["week"]), r["grammar"],
            f"{r['passage_from']}~{r['passage_to']}",
            ", ".join(r["assessments"]) or "-",
            ", ".join(r["reporting"]) or "-"] for r in rows])
    return 0


def cmd_curr_gap(args) -> int:
    cur = load_curriculum()
    lib = Library()
    if args.level:
        lv = cur.level(args.level)
        rows = cur.source_gap(lib, lv.code)
        head(f"{lv.code} 유형별 자료 부족분 (목표 {lv.material_target}편)")
        table(["유형", "비중", "보유", "목표", "부족"],
              [[r["category"], f"{r['share']}%", str(r["have"]),
                str(r["target"]), str(r["missing"])] for r in rows])
        return 0

    rows = cur.gap_report(lib)
    total_have = sum(r["have"] for r in rows)
    total_target = sum(r["target"] for r in rows)
    head(f"레벨별 자료 구축 현황 ({total_have}/{total_target}편 "
         f"· {round(total_have / total_target * 100, 1) if total_target else 0}%)")
    table(["레벨", "이름", "보유", "목표", "부족", "달성률", "커버 주수"],
          [[r["level"], r["name"], str(r["have"]), str(r["target"]),
            str(r["missing"]), f"{r['pct']}%", f"{r['weeks_covered']}주"]
           for r in rows])
    print("\n  ※ '커버 주수' = 지금 자료로 몇 주 수업이 가능한가 (주 2편 기준)")
    return 0


# ---------------------------------------------------------------------------
# class / student
# ---------------------------------------------------------------------------
def cmd_class_list(args) -> int:
    sc = School()
    rooms = sc.classes(active_only=not args.all)
    head(f"반 목록 ({len(rooms)}개)")
    table(["반코드", "이름", "레벨", "요일", "시간", "인원", "진행회차"],
          [[c.code, c.name, c.level, "·".join(c.days), c.time,
            str(len(c.students)), str(len(sc.progress(c.code)))] for c in rooms])
    return 0


def cmd_class_next(args) -> int:
    sc, lib, cur = School(), Library(), load_curriculum()
    plan = sc.next_session(args.klass, cur, lib)
    head(f"{args.klass} · {plan['session_no']}회차 준비물 ({plan['week']}주차)")
    print(f"  레벨      {plan['level']}")
    print(f"  문법 주제 {plan['grammar'] or '-'}")
    print(f"  필요 지문 {plan['need']}편")
    if plan["shortage"]:
        print(f"\n  ⚠ 쓸 수 있는 {plan['level']} 자료가 {plan['shortage']}편 부족합니다. "
              f"`python manage.py curriculum gap --level {plan['level']}` 로 확인하세요.")
    head("추천 자료")
    table(["ID", "제목", "주제", "유형", "어휘"],
          [[c["id"], c["title"][:28], (c["theme"] or "-")[:24],
            c["category"], str(c["vocab"])] for c in plan["candidates"]])
    if plan["candidates"]:
        ids = ",".join(c["id"] for c in plan["candidates"][:plan["need"]])
        print(f"\n  수업 후 기록:  python manage.py class log {args.klass} "
              f"--materials {ids}")
    return 0


def cmd_class_log(args) -> int:
    sc = School()
    log = sc.log_session(args.klass, _csv(args.materials), when=args.date,
                         grammar=args.grammar, homework=args.homework,
                         absent=_csv(args.absent), note=args.note)
    Library().rebuild_catalog()
    print(f"  기록 완료: {log.class_code} {log.session_no}회차 ({log.date}) "
          f"· 자료 {len(log.material_ids)}편")
    return 0


def cmd_class_history(args) -> int:
    sc = School()
    logs = sc.progress(args.klass)
    head(f"{args.klass} 진도 기록 ({len(logs)}회차)")
    table(["회차", "날짜", "문법", "자료", "결석"],
          [[str(l.session_no), l.date, l.grammar[:24] or "-",
            ", ".join(l.material_ids) or "-", ", ".join(l.absent) or "-"]
           for l in logs])
    return 0


def cmd_student_list(args) -> int:
    sc = School()
    studs = sc.students(active_only=not args.all)
    head(f"학생 명단 ({len(studs)}명)")
    table(["코드", "이름", "레벨", "학교", "학년", "등록일", "메모"],
          [[s.code, s.name, s.level, s.school, s.grade, s.enrolled, s.note[:22]]
           for s in studs])
    return 0


def cmd_student_report(args) -> int:
    sc = School()
    r = sc.report_card(args.code)
    head(f"{r['student']} {r['name']} · 학습 리포트")
    print(f"  레벨      {r['level']}")
    print(f"  소속 반   {', '.join(r['classes']) or '-'}")
    print(f"  수업      {r['sessions']}회차 · 출석률 {round(r['attendance'] * 100, 1)}%")
    print(f"  테스트    {r['tests']}회 · 누적 {r['score']}/{r['total']} "
          f"· 성취율 {round(r['mastery'] * 100, 1)}%")
    head("자주 틀린 단어")
    table(["단어", "틀린 횟수"], [[w, str(n)] for w, n in r["weak_words"]],
          empty="기록 없음")
    if r["weak_words"]:
        print(f"\n  개인 시험지:  python manage.py pack personal {r['student']}")
    return 0


def cmd_student_score(args) -> int:
    sc = School()
    row = sc.log_score(args.code, kind=args.kind, score=args.score,
                       total=args.total, when=args.date,
                       material_ids=_csv(args.materials), wrong=_csv(args.wrong),
                       note=args.note)
    print(f"  기록 완료: {row['student']} {row['kind']} "
          f"{row['score']}/{row['total']} · 오답 {len(row['wrong'])}개")
    return 0


# ---------------------------------------------------------------------------
# pack
# ---------------------------------------------------------------------------
def _resolve_ids(args, sc: School) -> list[str]:
    if args.ids:
        return _csv(args.ids)
    if args.klass:
        used = sc.used_materials(args.klass)
        if args.last:
            used = used[-args.last:]
        return used
    return []


def cmd_pack_review(args) -> int:
    from src import packs

    cfg, sc = load_config(), School()
    ids = _resolve_ids(args, sc)
    if not ids:
        print("  --ids 또는 --class 로 대상 자료를 지정하세요.")
        return 1
    name = args.name or (f"{args.klass}_누적복습" if args.klass else "누적복습")
    recs = packs.build_review_pack(cfg, ids, name=name, seed=args.seed)
    head(f"누적 복습 자료 ({len(ids)}편 기준)")
    for r in recs:
        print(f"  {r['label']}  {r['path'].name}")
    return 0


def cmd_pack_homework(args) -> int:
    from src import packs

    cfg, sc = load_config(), School()
    ids = _resolve_ids(args, sc)
    if not ids:
        print("  --ids 또는 --class 로 대상 자료를 지정하세요.")
        return 1
    recs = packs.build_homework(cfg, ids, name=args.name or "숙제")
    for r in recs:
        print(f"  {r['label']}  {r['path'].name}")
    return 0


def cmd_pack_personal(args) -> int:
    from src import packs

    cfg, sc = load_config(), School()
    weak = [w for w, _ in sc.weak_words(args.code, limit=args.limit)]
    if not weak:
        print(f"  {args.code} 의 오답 기록이 없습니다. "
              f"먼저 `python manage.py student score` 로 테스트 결과를 기록하세요.")
        return 1
    recs = packs.build_personal_test(cfg, args.code, weak, seed=args.seed)
    for r in recs:
        print(f"  {r['label']}  {r['path'].name}  (단어 {r['words']}개)")
        if r["missing"]:
            print(f"    · 라이브러리에 없어 제외된 단어: {', '.join(r['missing'])}")
    return 0


# ---------------------------------------------------------------------------
# status — 전체 현황 한 장
# ---------------------------------------------------------------------------
def cmd_status(args) -> int:
    lib, sc = Library(), School()
    st = lib.stats()
    print("=" * 58)
    print("  교습소 자료·운영 현황")
    print("=" * 58)
    head("자료 라이브러리")
    print(f"  총 {st['total']}건 · 고유 어휘 {st['vocab_unique']}개 "
          f"· 아직 수업에 안 쓴 자료 {st['unused']}건")

    try:
        cur = load_curriculum()
        rows = cur.gap_report(lib)
        have = sum(r["have"] for r in rows)
        target = sum(r["target"] for r in rows)
        pct = round(have / target * 100, 1) if target else 0
        head(f"커리큘럼 대비 구축률  {have}/{target}편 ({pct}%)")
        table(["레벨", "보유", "목표", "부족", "커버 주수"],
              [[r["level"], str(r["have"]), str(r["target"]), str(r["missing"]),
                f"{r['weeks_covered']}주"] for r in rows])
    except (OSError, ValueError, KeyError) as e:
        print(f"  커리큘럼을 읽지 못했습니다: {e}")

    rooms = sc.classes()
    head(f"운영 중인 반 ({len(rooms)}개)")
    table(["반코드", "레벨", "인원", "진행회차", "쓴 자료"],
          [[c.code, c.level, str(len(c.students)), str(len(sc.progress(c.code))),
            str(len(sc.used_materials(c.code)))] for c in rooms])

    print("\n  다음에 할 일:")
    print("    python manage.py curriculum gap        어느 레벨 자료부터 채울지 보기")
    print("    python manage.py class next <반코드>    다음 회차 준비물 뽑기")
    return 0


# ---------------------------------------------------------------------------
# 파서
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="manage.py", description="교습소 자료·운영 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    sub = p.add_subparsers(dest="group", required=True)

    # -- library ---------------------------------------------------------
    lp = sub.add_parser("library", help="자료 라이브러리").add_subparsers(
        dest="cmd", required=True)

    a = lp.add_parser("add", help="분석 결과(report.json)를 라이브러리에 등록")
    a.add_argument("paths", nargs="+", help="report.json 경로(여러 개 가능)")
    a.add_argument("--level", default="", help="레벨 코드 (예: H1)")
    a.add_argument("--category", default="custom", choices=sorted(CATEGORIES),
                   help="자료 유형")
    a.add_argument("--source", default="", help="출처 상세 (교재명·회차 등)")
    a.add_argument("--tags", default="", help="태그, 쉼표로 구분")
    a.add_argument("--status", default="ready", choices=STATUSES)
    a.add_argument("--notes", default="", help="메모")
    a.add_argument("--allow-duplicate", action="store_true",
                   help="같은 지문이어도 강제로 새로 등록")
    a.set_defaults(func=cmd_library_add)

    a = lp.add_parser("list", help="자료 찾기")
    a.add_argument("--level", default="")
    a.add_argument("--category", default="")
    a.add_argument("--tag", default="")
    a.add_argument("--status", default="")
    a.add_argument("--genre", default="", choices=["", "logic", "emotional"])
    a.add_argument("--q", default="", help="제목·주제·출처·단어 검색")
    a.add_argument("--unused", action="store_true", help="아직 수업에 안 쓴 자료만")
    a.add_argument("--limit", type=int, default=40)
    a.set_defaults(func=cmd_library_list)

    a = lp.add_parser("show", help="자료 한 건 상세")
    a.add_argument("id")
    a.set_defaults(func=cmd_library_show)

    a = lp.add_parser("set", help="자료 메타데이터 수정")
    a.add_argument("id")
    a.add_argument("--level", default="")
    a.add_argument("--status", default="", choices=["", *STATUSES])
    a.add_argument("--tags", default=None)
    a.add_argument("--notes", default=None)
    a.add_argument("--source", default=None)
    a.set_defaults(func=cmd_library_set)

    lp.add_parser("index", help="catalog.json · CATALOG.md 갱신").set_defaults(
        func=cmd_library_index)
    lp.add_parser("stats", help="보유 자료 통계").set_defaults(func=cmd_library_stats)
    lp.add_parser("dupes", help="중복 등록 점검").set_defaults(func=cmd_library_dupes)

    # -- curriculum ------------------------------------------------------
    cp = sub.add_parser("curriculum", help="커리큘럼").add_subparsers(
        dest="cmd", required=True)
    cp.add_parser("levels", help="레벨 체계 보기").set_defaults(func=cmd_curr_levels)

    a = cp.add_parser("plan", help="레벨별 주차 진도표")
    a.add_argument("level")
    a.set_defaults(func=cmd_curr_plan)

    a = cp.add_parser("gap", help="자료 부족분 리포트")
    a.add_argument("--level", default="", help="레벨을 주면 유형별로 쪼개서 표시")
    a.set_defaults(func=cmd_curr_gap)

    # -- class -----------------------------------------------------------
    kp = sub.add_parser("class", help="반 운영").add_subparsers(
        dest="cmd", required=True)
    a = kp.add_parser("list", help="반 목록")
    a.add_argument("--all", action="store_true", help="종료된 반도 표시")
    a.set_defaults(func=cmd_class_list)

    a = kp.add_parser("next", help="다음 회차 준비물")
    a.add_argument("klass", metavar="반코드")
    a.set_defaults(func=cmd_class_next)

    a = kp.add_parser("log", help="수업 회차 기록")
    a.add_argument("klass", metavar="반코드")
    a.add_argument("--materials", default="", help="사용한 자료 ID, 쉼표로 구분")
    a.add_argument("--grammar", default="", help="다룬 문법 주제")
    a.add_argument("--homework", default="", help="낸 숙제")
    a.add_argument("--absent", default="", help="결석 학생코드, 쉼표로 구분")
    a.add_argument("--date", default="", help="수업일 (기본: 오늘)")
    a.add_argument("--note", default="")
    a.set_defaults(func=cmd_class_log)

    a = kp.add_parser("history", help="반 진도 기록")
    a.add_argument("klass", metavar="반코드")
    a.set_defaults(func=cmd_class_history)

    # -- student ---------------------------------------------------------
    sp = sub.add_parser("student", help="학생").add_subparsers(
        dest="cmd", required=True)
    a = sp.add_parser("list", help="학생 명단")
    a.add_argument("--all", action="store_true", help="퇴원생 포함")
    a.set_defaults(func=cmd_student_list)

    a = sp.add_parser("report", help="학생 학습 리포트")
    a.add_argument("code", metavar="학생코드")
    a.set_defaults(func=cmd_student_report)

    a = sp.add_parser("score", help="테스트 결과 기록")
    a.add_argument("code", metavar="학생코드")
    a.add_argument("--kind", default="vocabtest")
    a.add_argument("--score", type=int, default=0)
    a.add_argument("--total", type=int, default=0)
    a.add_argument("--wrong", default="", help="틀린 단어, 쉼표로 구분")
    a.add_argument("--materials", default="", help="시험 범위 자료 ID")
    a.add_argument("--date", default="")
    a.add_argument("--note", default="")
    a.set_defaults(func=cmd_student_score)

    # -- pack ------------------------------------------------------------
    pp = sub.add_parser("pack", help="누적 자료 만들기").add_subparsers(
        dest="cmd", required=True)

    a = pp.add_parser("review", help="누적 어휘 리스트·시험지·문법 시트")
    a.add_argument("--ids", default="", help="자료 ID, 쉼표로 구분")
    a.add_argument("--class", dest="klass", default="", help="반코드(그 반이 쓴 자료 사용)")
    a.add_argument("--last", type=int, default=0, help="최근 N편만")
    a.add_argument("--name", default="", help="자료 이름(파일명에 들어감)")
    a.add_argument("--seed", type=int, default=None, help="문제 순서 고정용 시드")
    a.set_defaults(func=cmd_pack_review)

    a = pp.add_parser("homework", help="숙제지(학생용 빈칸 분석지)")
    a.add_argument("--ids", default="")
    a.add_argument("--class", dest="klass", default="")
    a.add_argument("--last", type=int, default=0)
    a.add_argument("--name", default="")
    a.set_defaults(func=cmd_pack_homework)

    a = pp.add_parser("personal", help="학생 오답 기반 개인 시험지")
    a.add_argument("code", metavar="학생코드")
    a.add_argument("--limit", type=int, default=30, help="최대 단어 수")
    a.add_argument("--seed", type=int, default=None)
    a.set_defaults(func=cmd_pack_personal)

    # -- status ----------------------------------------------------------
    sub.add_parser("status", help="전체 현황 한 장").set_defaults(func=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError, FileNotFoundError) as e:
        print(f"  ✗ {e}")
        return 1
    except BrokenPipeError:
        # `... | head` 처럼 출력을 중간에 끊었을 때 조용히 끝낸다
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())

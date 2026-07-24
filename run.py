#!/usr/bin/env python
"""동형모의고사 자동생성 CLI (§0 파이프라인).

사용 예:
  # 학교 목록 보기
  python run.py schools

  # 생성(오프라인 mock: API 키 없으면 자동으로 구조만 채운 미리보기 생성)
  python run.py generate --school jinyang_hs --grade 1 --difficulty 중 \
      --input input --out output

  # 학습(learn): 추출된 blueprint(json)로 학교 프로파일 누적
  python run.py learn --school jinyang_hs --name 2026_2_final \
      --blueprint path/to/blueprint.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from mockexam.core.blueprint import blueprint_from_profile
from mockexam.core.models import Blueprint, BlueprintMeta, Item
from mockexam.pipeline import generate_mock, learn_from_blueprint
from mockexam.render.exam import render_exam
from mockexam.school import find_school, load_schools_index

ROOT = Path(__file__).resolve().parent


def _load_cfg(path: str | None) -> dict:
    p = Path(path) if path else (ROOT / "mock_config.yaml")
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {}


def _get_client(model: str):
    load_dotenv(ROOT / ".env")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or "여기에" in key:
        return None
    from mockexam.core.llm import get_client
    return get_client(key, model)


def _collect_inputs(input_arg: str) -> list[str]:
    p = Path(input_arg)
    if p.is_dir():
        files: list[str] = []
        for ext in ("*.pdf", "*.txt", "*.md", "*.jpg", "*.jpeg", "*.png", "*.hwp"):
            files.extend(sorted(str(x) for x in p.glob(ext)))
        return files
    return sorted(glob.glob(input_arg))


def cmd_schools(args):
    for s in load_schools_index():
        prof = (ROOT / "profiles" / s["school_id"] / "profile.json")
        state = "학습됨" if prof.exists() else "미학습(표준골격)"
        print(f"- {s['school_id']:14s} {s['name']:8s} [{s['level']}] {state}")


def cmd_generate(args):
    cfg = _load_cfg(args.config)
    school = args.school or cfg.get("school_id", "jinyang_hs")
    grade = args.grade or int(cfg.get("grade", 1))
    difficulty = args.difficulty or cfg.get("difficulty", "중")
    out_dir = args.out or cfg.get("paths", {}).get("output", "output")
    input_arg = args.input or cfg.get("paths", {}).get("input", "input")
    model = cfg.get("model", "claude-opus-4-8")
    header_info = dict(cfg.get("header_info", {}) or {})
    footer = cfg.get("footer", "")
    answer_key = cfg.get("answer_key", "end")
    num_forms = int(cfg.get("num_forms", 1))

    if not find_school(school):
        print(f"[경고] 등록되지 않은 학교: {school} (schools.json 확인)")

    inputs = _collect_inputs(input_arg)
    if not inputs:
        print(f"[오류] 입력 지문이 없습니다: {input_arg}")
        return
    print(f"입력 지문 {len(inputs)}개: {[Path(i).name for i in inputs]}")

    client = None if args.mock else _get_client(model)
    print(f"모드: {'오프라인 mock' if client is None else 'LLM 생성'}  "
          f"학교={school} 학년={grade} 난이도={difficulty}")

    forms = "ABCDEF"
    for f_i in range(num_forms):
        res = generate_mock(school, inputs, difficulty=difficulty, grade=grade,
                            client=client)
        info = dict(header_info)
        info.setdefault("subject", res.blueprint.meta.subject)
        out = render_exam(res.exam, out_dir, form=forms[f_i], header_info=info,
                          footer=footer, answer_key=answer_key)
        print(f"\n[{forms[f_i]}형] 검증:")
        print(res.verify_report.summary())
        _short = next((l.get("msg") for l in res.logs
                       if l.get("note") == "passage_reuse"), "")
        if _short:
            print(f"\nℹ [지문 배정] {_short}")
        if res.logs:
            print("지문 배정 로그:", json.dumps(res.logs, ensure_ascii=False))
        for k, v in out.items():
            print(f"  {k}: {v}")
        # blueprint 저장(감사용)
        bp_path = Path(out_dir) / f"blueprint_{forms[f_i]}.json"
        bp_path.write_text(json.dumps(res.blueprint.to_dict(), ensure_ascii=False, indent=2),
                           encoding="utf-8")
        print(f"  blueprint: {bp_path}")


def cmd_learn(args):
    data = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
    school = find_school(args.school) or {}
    meta_raw = data.get("meta", {})
    meta = BlueprintMeta(
        school_id=args.school, name=school.get("name", args.school),
        level=school.get("level", "high"), grade=int(meta_raw.get("grade", 1)),
        subject=meta_raw.get("subject", ""), time_min=int(meta_raw.get("time_min", 50)),
        total_score=float(meta_raw.get("total_score", 100)), learned=True)
    items = [Item(no=i["no"], section=i["section"], type=i["type"], score=float(i["score"]),
                  underlines=i.get("underlines"), subparts=i.get("subparts", []))
             for i in data.get("items", [])]
    bp = Blueprint(meta=meta, items=items)
    prof = learn_from_blueprint(args.school, args.name, bp,
                                name=school.get("name", args.school),
                                level=school.get("level", "high"))
    print(f"학습 완료: {args.school} ← {args.name}")
    print(f"  누적 시험: {prof.get('exams_learned')}")
    print(f"  counts: {prof.get('counts')}  total: {prof.get('score_pattern')}")


def main():
    ap = argparse.ArgumentParser(description="동형모의고사 자동생성")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("schools", help="등록 학교 목록")
    sp.set_defaults(func=cmd_schools)

    gp = sub.add_parser("generate", help="동형모의고사 생성")
    gp.add_argument("--school"); gp.add_argument("--grade", type=int)
    gp.add_argument("--difficulty"); gp.add_argument("--input"); gp.add_argument("--out")
    gp.add_argument("--config"); gp.add_argument("--mock", action="store_true",
                    help="API 키 무시하고 오프라인 구조 미리보기")
    gp.set_defaults(func=cmd_generate)

    lp = sub.add_parser("learn", help="학교 시험지 blueprint 로 프로파일 학습")
    lp.add_argument("--school", required=True); lp.add_argument("--name", required=True)
    lp.add_argument("--blueprint", required=True)
    lp.set_defaults(func=cmd_learn)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

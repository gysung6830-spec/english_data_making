"""한 지문에 대해 추출 + 6개 섹션을 개별 호출로 분석하고 Report 로 조립."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor

from . import prompts, schemas
from .client import ClaudeClient
from .config import Config


def extract_passages(client: ClaudeClient, cfg: Config, raw_text: str) -> schemas.PassageSet:
    """0단계(PDF): 원문 텍스트 -> 여러 지문(제목/출처/문단)."""
    return client.structured(
        system=prompts.EXTRACT_SYSTEM,
        prompt=prompts.extract_prompt(raw_text),
        model_cls=schemas.PassageSet,
        max_tokens=12000,
        max_retries=cfg.processing.max_retries,
    )


def extract_passages_image(client: ClaudeClient, cfg: Config, image_path: str) -> schemas.PassageSet:
    """0단계(사진): 이미지 -> 여러 지문(비전으로 읽음)."""
    return client.structured(
        system=prompts.EXTRACT_SYSTEM,
        prompt=prompts.extract_image_prompt(),
        model_cls=schemas.PassageSet,
        max_tokens=12000,
        max_retries=cfg.processing.max_retries,
        image_path=image_path,
    )


def analyze_passage(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> schemas.Report:
    """추출된 본문으로 6개 섹션을 각각 요청하여 Report 조립."""
    title, body = extraction.title, extraction.body
    r = cfg.processing.max_retries

    def do_summary():
        return client.structured(prompts.SYSTEM, prompts.summary_prompt(title, body),
                                 schemas.SummarySection, max_retries=r)

    def do_literal():
        return client.structured(prompts.SYSTEM, prompts.literal_prompt(title, body),
                                 schemas.LiteralSection, max_tokens=12000, max_retries=r)

    def do_grammar():
        return client.structured(prompts.SYSTEM, prompts.grammar_prompt(title, body),
                                 schemas.GrammarSection, max_retries=r)

    def do_vocab():
        lo, hi = cfg.vocab.min, cfg.vocab.max
        return client.structured(
            prompts.SYSTEM, prompts.vocab_prompt(title, body, lo, hi),
            schemas.VocabSection, max_retries=r,
            extra_validate=lambda v: v.validate_count(lo, hi),
        )

    def do_structure():
        return client.structured(prompts.SYSTEM, prompts.structure_prompt(title, body),
                                 schemas.StructureSection, max_retries=r)

    # 1차: exam 을 제외한 5개 섹션 (exam 은 문법·어휘 결과를 참고하므로 이후 실행)
    tasks = {
        "summary": do_summary,
        "literal": do_literal,
        "grammar": do_grammar,
        "vocab": do_vocab,
        "structure": do_structure,
    }

    results: dict[str, object] = {}
    if cfg.processing.parallel_sections:
        with ThreadPoolExecutor(max_workers=5) as ex:
            futs = {name: ex.submit(fn) for name, fn in tasks.items()}
            for name, fut in futs.items():
                results[name] = fut.result()
    else:
        for name, fn in tasks.items():
            results[name] = fn()

    grammar = results["grammar"]
    vocab = results["vocab"]

    # 2차: 출제 포인트 (③④ 결과 참고)
    exam = client.structured(
        prompts.SYSTEM,
        prompts.exam_prompt(title, body, grammar, vocab),
        schemas.ExamSection,
        max_retries=r,
    )

    return schemas.Report(
        title=title,
        source=extraction.source,
        summary=results["summary"],
        literal=results["literal"],
        grammar=grammar,
        vocab=vocab,
        structure=results["structure"],
        exam=exam,
    )


def _qa_evidence_in_passage(qa: schemas.WSQAType, body: str) -> None:
    """유형7 문답의 '근거(evidence)'가 지문 안의 문장인지 검증(추론 금지).

    근거가 지문에 없으면 ValueError 를 던져 재생성을 유도한다.
    (공백/개행 차이는 정규화해 비교)
    """
    nb = " ".join(body.split())
    for i, it in enumerate(qa.items, 1):
        ev = " ".join((it.evidence or "").split()).rstrip(".")
        if ev and ev not in nb:
            raise ValueError(f"{i}번 문답의 근거가 지문에 없습니다(추론 금지): {ev[:60]}")


def _summary_answers_grounded(sec: schemas.WSSummaryType, body: str) -> None:
    """유형2 요약 정답이 '원문에 근거한 단어'인지 느슨하게 대조(어형 변화 허용)."""
    low = body.lower()
    for it in sec.items:
        for b in it.blanks:
            a = (b.answer or "").strip().lower()
            if not a:
                continue
            stem = a[:4] if len(a) >= 4 else a  # 어형 변화 허용(앞 4글자)
            if a not in low and stem not in low:
                raise ValueError(f"요약 정답 '{b.answer}'가 지문에 없습니다(원문 단어 사용).")


# 서술형 교재 유형 필드 순서(재생성·번호 매김 기준)
WS_TASK_NAMES = ["summary", "paraphrase", "arrange", "compose", "choice", "error", "qa"]


def _ws_tasks(client: ClaudeClient, cfg: Config, title: str, body: str) -> dict:
    """유형별 생성기(name -> 호출 가능한 함수) 딕셔너리. analyze/재생성에서 공용."""
    r = cfg.processing.max_retries
    S = prompts.WS_SYSTEM
    nb = " ".join(body.split())

    def _gen_qa():
        # 문답 생성 후, 근거가 지문에 없는 항목은 '제거'(유형 전체를 버리지 않음)
        qa = client.structured(S, prompts.ws_qa_prompt(title, body),
                               schemas.WSQAType, max_retries=r)
        kept = [it for it in qa.items
                if not (it.evidence and " ".join(it.evidence.split()).rstrip(".") not in nb)]
        if not kept:
            raise ValueError("문답 근거가 모두 지문 밖입니다.")
        return schemas.WSQAType(items=kept)

    def _gen_paraphrase():
        # 표준 구조화 호출(재시도 포함). 성공하면 그대로 사용.
        try:
            return client.structured(
                S, prompts.ws_paraphrase_prompt(title, body),
                schemas.WSParaphraseType, max_tokens=10000, max_retries=r)
        except Exception as e:
            print(f"[정보] 문장변형 표준 파싱 실패 → 문항 단위 살리기 시도: {e}", file=sys.stderr)
        # 살리기: 원시 JSON 을 받아 '유효한 문항만' 골라 구성(1개라도 있으면 유형 유지).
        from .client import build_request, extract_text
        req = build_request(client.model, S, prompts.ws_paraphrase_prompt(title, body),
                            schemas.WSParaphraseType, max_tokens=10000)
        msg = client.raw.messages.create(**req)
        data = json.loads(extract_text(msg))
        good = []
        for q in data.get("questions", []):
            try:
                good.append(schemas.WSParaphraseQ.model_validate(q))
            except Exception:
                continue
        if not good:
            raise ValueError("문장변형 유효 문항이 없습니다.")
        return schemas.WSParaphraseType(questions=good)

    return {
        "summary": lambda: client.structured(
            S, prompts.ws_summary_prompt(title, body),
            schemas.WSSummaryType, max_retries=r,
            extra_validate=lambda s: _summary_answers_grounded(s, body)),
        "paraphrase": _gen_paraphrase,
        "arrange": lambda: client.structured(
            S, prompts.ws_arrange_prompt(title, body),
            schemas.WSArrangeType, max_retries=r),
        "compose": lambda: client.structured(
            S, prompts.ws_compose_prompt(title, body),
            schemas.WSComposeType, max_retries=r),
        "choice": lambda: client.structured(
            S, prompts.ws_choice_prompt(title, body),
            schemas.WSChoiceType, max_tokens=10000, max_retries=r),
        "error": lambda: client.structured(
            S, prompts.ws_error_prompt(title, body),
            schemas.WSErrorType, max_retries=r),
        "qa": _gen_qa,
    }


def _run_ws_tasks(cfg: Config, tasks: dict, names) -> dict:
    """지정한 유형만 생성. 유형 단위 부분 성공(실패 시 None)."""
    def _safe(name, fn):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            print(f"[경고] 서술형 '{name}' 유형 생성 실패 → 건너뜀: {e}", file=sys.stderr)
            return None

    sel = [(n, tasks[n]) for n in names if n in tasks]
    results: dict[str, object] = {}
    if cfg.processing.parallel_sections and len(sel) > 1:
        with ThreadPoolExecutor(max_workers=len(sel)) as ex:
            futs = {n: ex.submit(_safe, n, fn) for n, fn in sel}
            for n, fut in futs.items():
                results[n] = fut.result()
    else:
        for n, fn in sel:
            results[n] = _safe(n, fn)
    return results


def _verify_ws_types(client: ClaudeClient, cfg: Config, title: str, body: str,
                     results: dict) -> None:
    """(옵트인) 어법·문장변형 2차 검증. verify_content=true 일 때만, results 를 제자리 교정."""
    r = cfg.processing.max_retries
    S = prompts.WS_SYSTEM
    if not cfg.processing.verify_content:
        return
    if results.get("error") is not None:
        try:
            results["error"] = client.structured(
                S, prompts.ws_error_verify_prompt(title, body, results["error"]),
                schemas.WSErrorType, max_retries=r)
        except Exception as e:
            print(f"[경고] 어법 2차 검증 실패 → 원본 사용: {e}", file=sys.stderr)
    if results.get("paraphrase") is not None:
        try:
            results["paraphrase"] = client.structured(
                S, prompts.ws_paraphrase_verify_prompt(title, body, results["paraphrase"]),
                schemas.WSParaphraseType, max_tokens=10000, max_retries=r)
        except Exception as e:
            print(f"[경고] 문장변형 2차 검증 실패 → 원본 사용: {e}", file=sys.stderr)


def analyze_worksheet(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> schemas.Worksheet:
    """추출된 본문으로 서술형 대비 교재(7개 유형)를 각각 개별 호출로 생성."""
    title, body = extraction.title, extraction.body
    tasks = _ws_tasks(client, cfg, title, body)
    results = _run_ws_tasks(cfg, tasks, WS_TASK_NAMES)
    if all(v is None for v in results.values()):
        raise RuntimeError("서술형 교재의 모든 유형 생성에 실패했습니다.")
    _verify_ws_types(client, cfg, title, body, results)
    return schemas.Worksheet(
        title=title, source=extraction.source, passage=body,
        **{n: results.get(n) for n in WS_TASK_NAMES},
    )


def regenerate_worksheet(
    client: ClaudeClient, cfg: Config, ws: schemas.Worksheet,
    targets=None,
) -> schemas.Worksheet:
    """기존 Worksheet 에서 '지정한(또는 누락된) 유형만' 지문(ws.passage)으로 다시 생성.

    targets 가 None 이면 '현재 None(누락)인 유형'만 재생성한다. 성공한 것만 교체하고
    나머지 유형과 실패분은 그대로 둔다(비용은 재생성 유형 수만큼만 발생).
    """
    if not (ws.passage or "").strip():
        raise ValueError("재생성하려면 지문(passage)이 필요합니다. 지문이 저장된 JSON 인지 확인하세요.")
    if targets is None:
        targets = [n for n in WS_TASK_NAMES if getattr(ws, n, None) is None]
    else:
        targets = [n for n in WS_TASK_NAMES if n in set(targets)]
    if not targets:
        return ws
    tasks = _ws_tasks(client, cfg, ws.title, ws.passage)
    results = _run_ws_tasks(cfg, tasks, targets)
    _verify_ws_types(client, cfg, ws.title, ws.passage, results)
    # 성공한 유형만 교체(실패=None 은 기존 값 유지)
    update = {n: v for n, v in results.items() if v is not None}
    return ws.model_copy(update=update) if update else ws

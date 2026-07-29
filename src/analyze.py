"""한 지문에 대해 추출 + 6개 섹션을 개별 호출로 분석하고 Report 로 조립."""
from __future__ import annotations

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


def analyze_worksheet(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> schemas.Worksheet:
    """추출된 본문으로 서술형 대비 교재(7개 유형)를 각각 개별 호출로 생성."""
    title, body = extraction.title, extraction.body
    r = cfg.processing.max_retries
    S = prompts.WS_SYSTEM

    tasks = {
        "summary": lambda: client.structured(
            S, prompts.ws_summary_prompt(title, body),
            schemas.WSSummaryType, max_retries=r),
        "paraphrase": lambda: client.structured(
            S, prompts.ws_paraphrase_prompt(title, body),
            schemas.WSParaphraseType, max_tokens=10000, max_retries=r),
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
        "qa": lambda: client.structured(
            S, prompts.ws_qa_prompt(title, body),
            schemas.WSQAType, max_retries=r,
            extra_validate=lambda qa: _qa_evidence_in_passage(qa, body)),
    }

    # 유형 단위 부분 성공: 한 유형이 (재시도까지) 실패해도 None 으로 두고 계속.
    import sys

    def _safe(name, fn):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            print(f"[경고] 서술형 '{name}' 유형 생성 실패 → 건너뜀: {e}", file=sys.stderr)
            return None

    results: dict[str, object] = {}
    if cfg.processing.parallel_sections:
        with ThreadPoolExecutor(max_workers=7) as ex:
            futs = {name: ex.submit(_safe, name, fn) for name, fn in tasks.items()}
            for name, fut in futs.items():
                results[name] = fut.result()
    else:
        for name, fn in tasks.items():
            results[name] = _safe(name, fn)

    if all(v is None for v in results.values()):
        raise RuntimeError("서술형 교재의 모든 유형 생성에 실패했습니다.")

    return schemas.Worksheet(
        title=title,
        source=extraction.source,
        passage=body,
        summary=results["summary"],
        paraphrase=results["paraphrase"],
        arrange=results["arrange"],
        compose=results["compose"],
        choice=results["choice"],
        error=results["error"],
        qa=results["qa"],
    )

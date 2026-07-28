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
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction,
    want_train: bool | None = None,
) -> schemas.Report:
    """추출된 본문으로 6개 섹션을 각각 요청하여 Report 조립.

    want_train: 모의고사 훈련서(⑦)까지 생성할지. None 이면 cfg.outputs.train 을 따른다.
    (훈련서는 별도 API 호출이라, 출력에서 선택했을 때만 만들어 비용을 아낀다.)
    """
    title, body = extraction.title, extraction.body
    r = cfg.processing.max_retries
    want_train = cfg.outputs.train if want_train is None else want_train

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

    # ⑦ 모의고사 훈련서 (선택 시에만 생성; 본문만으로 독립 생성)
    train = None
    if want_train:
        train = client.structured(
            prompts.SYSTEM,
            prompts.train_prompt(title, body),
            schemas.TrainSection,
            max_tokens=12000,
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
        train=train,
    )

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


def analyze_worksheet(
    client: ClaudeClient, cfg: Config, extraction: schemas.Extraction
) -> schemas.Worksheet:
    """추출된 본문으로 서술형 대비 교재(7개 유형)를 각각 개별 호출로 생성."""
    title, body = extraction.title, extraction.body
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

    tasks = {
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

    # 유형 단위 부분 성공: 한 유형이 (재시도까지) 실패해도 None 으로 두고 계속.
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

    # (옵트인) 어법 유형 2차 검증: 모델에게 오류 판정을 재채점시켜 교정본을 채택.
    #   비용이 늘어나므로 config 의 processing.verify_content=true 일 때만 동작.
    if cfg.processing.verify_content and results.get("error") is not None:
        try:
            fixed = client.structured(
                S, prompts.ws_error_verify_prompt(title, body, results["error"]),
                schemas.WSErrorType, max_retries=r)
            results["error"] = fixed
        except Exception as e:  # 검증 실패 시 원본 유지
            print(f"[경고] 어법 2차 검증 실패 → 원본 사용: {e}", file=sys.stderr)

    # (옵트인) 문장 변형 2차 검증: 정답을 넣은 완성문이 문법적·무중복인지 재검수.
    #   'was observed noticed' 같은 빈칸-원어 중복 비문을 잡아낸다. verify_content=true 일 때만.
    if cfg.processing.verify_content and results.get("paraphrase") is not None:
        try:
            fixed = client.structured(
                S, prompts.ws_paraphrase_verify_prompt(title, body, results["paraphrase"]),
                schemas.WSParaphraseType, max_tokens=10000, max_retries=r)
            results["paraphrase"] = fixed
        except Exception as e:  # 검증 실패 시 원본 유지
            print(f"[경고] 문장변형 2차 검증 실패 → 원본 사용: {e}", file=sys.stderr)

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

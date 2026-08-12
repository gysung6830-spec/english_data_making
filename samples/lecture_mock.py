"""API 없이 강의컨셉 교재 렌더링/파이프라인을 검증하기 위한 목(mock) 데이터."""
from __future__ import annotations

from src.lecture_schemas import (LectureAnalysis, LecturePassage, LectureSentence,
                                 ParaphraseItem, RoleBlock, TranslationTrap,
                                 TrapQuestion, VocabHint)


def mock_lecture_passage(title: str = "The Paradox of Ownership",
                         source: str = "Mock Reader 2024",
                         item_no: str = "") -> LecturePassage:
    sents = [
        "Many people believe that owning more things makes them more generous.",
        "However, research suggests the opposite is often true.",
        "As individuals accumulate possessions, they tend to share them less.",
        "For example, people with large libraries rarely lend their books.",
        "This tendency stems from a psychological sense of attachment.",
        "Therefore, generosity may depend less on wealth than on mindset.",
    ]
    sentences = [LectureSentence(id=i, text=t) for i, t in enumerate(sents, 1)]
    analysis = LectureAnalysis(
        vocab_hints=[
            VocabHint(word="generous", meaning="너그러운, 잘 나누는"),
            VocabHint(word="accumulate", meaning="축적하다, 모으다"),
            VocabHint(word="possessions", meaning="소유물, 재산"),
            VocabHint(word="attachment", meaning="애착"),
            VocabHint(word="mindset", meaning="사고방식, 마음가짐"),
        ],
        translation_traps=[
            TranslationTrap(
                sentence_id=2,
                wrong_translation="하지만 연구는 반대가 종종 사실이라고 제안했다.",
                correct_translation="하지만 연구는 흔히 그 반대가 사실임을 시사한다.",
                trap_type="다의어",
                reason="suggest 는 여기서 '제안하다'가 아니라 '시사하다'의 뜻이다.",
            ),
            TranslationTrap(
                sentence_id=6,
                wrong_translation="따라서 너그러움은 부보다 사고방식에 더 적게 의존한다.",
                correct_translation="따라서 너그러움은 부보다 사고방식에 달려 있을 수 있다.",
                trap_type="구조오인",
                reason="'less on A than on B' 는 'A보다 B에 달려 있다'는 비교 구조다.",
            ),
        ],
        role_blocks=[
            RoleBlock(sentence_ids=[1], correct_label="통념",
                      reason="사람들이 흔히 믿는 생각을 제시한다."),
            RoleBlock(sentence_ids=[2], correct_label="전환",
                      reason="However 로 통념을 뒤집는다."),
            RoleBlock(sentence_ids=[3], correct_label="근거",
                      reason="통념과 반대되는 주장을 뒷받침한다."),
            RoleBlock(sentence_ids=[4, 5], correct_label="예시",
                      reason="For example 로 구체적 사례와 원인을 든다."),
            RoleBlock(sentence_ids=[6], correct_label="결론",
                      reason="Therefore 로 글의 결론을 맺는다."),
        ],
        trap_question=TrapQuestion(
            type="연결어 반전 오독",
            sentence_id=2,
            question_text="S2의 However 가 지문에서 하는 역할로 알맞은 것은?",
            option_wrong="앞 문장에 대한 예시를 덧붙인다.",
            option_correct="앞의 통념을 반박하며 흐름을 뒤집는다.",
            explanation="However 는 역접 연결어로, 앞의 통념을 부정하고 반대 주장을 이끈다.",
        ),
        paraphrase_items=[
            ParaphraseItem(
                choice_text="The more you own, the less you tend to give away.",
                matched_sentence_ids=[3],
            ),
            ParaphraseItem(
                choice_text="Being open-handed is shaped by attitude rather than riches.",
                matched_sentence_ids=[6],
            ),
            ParaphraseItem(
                choice_text="Book collectors seldom hand their volumes to others.",
                matched_sentence_ids=[4],
            ),
        ],
    )
    return LecturePassage(title=title, source=source, item_no=item_no,
                          sentences=sentences, analysis=analysis)

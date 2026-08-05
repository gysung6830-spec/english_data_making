"""뒷페이지(요약) 생성 — 어휘 리스트 / 논리 흐름도 / 쉬운 예시 목차.

지문 전체(문장 + 해석)를 보고 한 번의 LLM 호출로 세 가지를 만든다.
- 어휘 리스트 : 핵심 어휘 + 유의어/반의어
- 논리 흐름도 : 글의 전개 구조(도입→전개→…→결론)
- 쉬운 예시   : 지문을 쉽게 이해하도록 학생 눈높이 비유 한 줄씩
"""
from __future__ import annotations

from ..client import ClaudeClient
from .llm_schemas import OverviewBundle
from .models import Analysis, FlowStep, ImplicitPoint, VocabEntry

SYSTEM = (
    "당신은 한국 고등학교 영어 지문 학습지의 '요약 정리 페이지'를 만드는 전문 강사입니다. "
    "지문의 핵심 어휘(유의어·반의어 포함), 글의 논리 흐름, 그리고 학생이 쉽게 이해할 수 있는 "
    "비유 예시를 정리합니다. "
    "어투는 '오래 가르친 교사가 직접 손으로 쓴 학습지'처럼 간결·담백하게. "
    "AI 티 나는 상투어(예: '~을 통해 알 수 있습니다', '중요한 역할을 합니다', 과장·감탄·이모지, "
    "억지 유행어)는 쓰지 마세요. 부제·예시는 군더더기 없이 핵심만. "
    "요청된 JSON 스키마로만 응답하세요."
)


def _passage_block(analysis: Analysis) -> str:
    lines = []
    for s in analysis.sentences:
        lines.append(f"{s.index}. {s.text}")
        if s.translation:
            lines.append(f"   ({s.translation})")
    return "\n".join(lines)


def build_prompt(analysis: Analysis) -> str:
    n = len(analysis.sentences)
    return (
        f"다음은 지문(총 {n}문장)입니다. 문장번호·원문·해석을 참고해 '요약 정리 페이지'를 만드세요.\n\n"
        f"[지문]\n{_passage_block(analysis)}\n\n"
        "[작성 규칙]\n"
        "0) title_ko / title_en (⚠️ 한글 제목을 '먼저' 정하고, 그걸 영어로 '번역'하는 순서):\n"
        "   ① 먼저 지문 '내용'을 대표하는 한국어 제목(title_ko)을 짓습니다(핵심 주제 한 줄, 8~16자 권장).\n"
        "   ② 그 다음 title_ko 를 '그대로 영어로 옮긴' 영문 제목(title_en, 3~7단어)을 씁니다.\n"
        "   ⚠️ 반드시 '한글 → 영어' 방향으로 만들어, 두 제목의 소재·표현·의미가 '완전히 일치'하게 하세요"
        "(영어를 먼저 짓고 한글을 갖다 붙이지 마세요). "
        "예: 먼저 '친환경 전환에 숨은 비용' → 번역 'The Hidden Cost of Going Green'.\n"
        "0.5) summary / summary_easy (분석 페이지 상단 요약 박스, 각각 '한 문장'):\n"
        "   · summary: 지문의 '주제'를 한 문장으로. 글이 말하려는 핵심 주장을 담백하게(40~70자 권장).\n"
        "   · summary_easy: 그 주제를 '쉽게 말하면' 학생 눈높이의 실생활 비유·예시 한 문장으로 "
        "(반말/구어 OK, 40~70자 권장). '쉽게 말하면' 같은 접두어는 붙이지 말고 예시 문장만 쓰세요.\n"
        "1) vocab: 지문 핵심 어휘 8~12개. 각 항목 word(단어/표현), meaning(한글 뜻), "
        "syn(유의어, 없으면 '—'), ant(반의어, 없으면 '—'), sent(등장 문장 번호).\n"
        "   ▸ 선정 기준(중요): '유의어·반의어가 뚜렷한' 단어를 최우선으로 고르세요. "
        "품사 우선순위는 ①동사 ②형용사 ③부사. 관용구·구동사·연어(collocation)도 좋습니다. "
        "명사는 원칙적으로 제외하되, 그 지문의 '핵심 키워드'인 명사라면 넣어도 됩니다. "
        "쉬운 기초 단어나 지엽적 명사(고유명사·일반 사물 등), 유의어·반의어가 마땅치 않은 단어는 "
        "가급적 넣지 마세요.\n"
        "2) flow: 글의 논리 흐름을 4~6단계로. 각 단계에 논리와 쉬운 예시를 '함께' 담습니다. "
        "label(도입/전개/전환/주장/결론 등 짧은 이름), text(개조식 논리 한 줄), "
        "easy(그 단계를 학생 눈높이 반말로 풀어준 쉬운 비유 한 줄), sentences(관련 문장 번호, 예 '1~3').\n"
        "3) implicit(출제 포인트·함축의미): '직역만으로는 뜻이 안 통하고 맥락을 알아야 풀리는' "
        "함축·비유 표현(빈칸·함축추론 출제 후보)이 있는 문장을 1~3개 고릅니다. 그런 표현이 뚜렷하지 "
        "않으면 빈 배열. 각 항목:\n"
        "   · sent: 문장 번호.\n"
        "   · phrase: 그 문장에서 핵심이 되는 '영어 표현'을 원문 그대로(구/절 단위, 너무 길지 않게).\n"
        "   · meaning_ko: 그 표현의 '문맥상 의미'를 한글로(왜 그런 뜻이 되는지 맥락 포함, 1~2문장).\n"
        "   · answer_en: 그 함축을 '쉬운 영어'로 바꿔 쓴 정답 표현 한 문장(패러프레이즈, 서술형/빈칸 정답감).\n"
        "   · trap_ko: '직역 함정' — 그 표현을 단순 직역하면 놓치는 맥락을 한 문장으로 경고 "
        "(예: \"'the norm rather than the rule'을 '규칙보다 규범'으로 직역하면 표준화되었다는 맥락을 놓친다\").\n"
    )


def build_overview(
    client: ClaudeClient,
    analysis: Analysis,
    max_retries: int = 1,
) -> tuple[str, str, str, str, list[VocabEntry], list[FlowStep], list[ImplicitPoint]]:
    """LLM 로 제목(영/한) + 요약(주제/쉽게) + 뒷페이지(어휘 / 논리 흐름 / 함축의미) 생성. 실패 시 빈 값."""
    try:
        b: OverviewBundle = client.structured(
            system=SYSTEM,
            prompt=build_prompt(analysis),
            model_cls=OverviewBundle,
            max_tokens=4000,
            max_retries=max_retries,
        )
    except Exception:
        return "", "", "", "", [], [], []
    vocab = [VocabEntry(word=v.word, meaning=v.meaning, syn=v.syn or "—",
                        ant=v.ant or "—", sent=(v.sent or None)) for v in b.vocab if v.word]
    flow = [FlowStep(label=f.label, text=f.text, easy=f.easy, sentences=f.sentences)
            for f in b.flow if f.label and f.text]
    implicit = [ImplicitPoint(sent=(i.sent or 0), phrase=i.phrase, meaning_ko=i.meaning_ko,
                              answer_en=i.answer_en, trap_ko=i.trap_ko)
                for i in b.implicit if (i.phrase or i.meaning_ko)]
    return (b.title_en.strip(), b.title_ko.strip(),
            b.summary.strip(), b.summary_easy.strip(), vocab, flow, implicit)

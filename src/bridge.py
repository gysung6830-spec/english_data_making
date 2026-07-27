# -*- coding: utf-8 -*-
"""난이도 맞춤 '기초 브릿지 교재' 자동 생성.

지문(Extraction) + 난이도(1~5) -> LLM 구조화 출력(BridgeGen) -> 교재 PDF.

기존 client.structured() 파이프라인과 templates/bridge_gen.html.j2 를 재사용한다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)


# ---------------------------------------------------------------------------
# 난이도 단계 (슬라이더 1~5, 각 키워드/설명)
# ---------------------------------------------------------------------------
LEVELS = {
    1: {"key": "왕기초",
        "desc": "문법 제로 · 뼈대·be동사·3인칭 -s·과거·의문/부정문까지, 모르는 단어 전부",
        "vocab": "지문에서 조금이라도 모를 만한 단어를 거의 전부 (최대한 많이, 25개 이상 가능)",
        "grammar": "가장 기초 문법을 한 번에 훑기 — 문장 뼈대(주어+동사), be동사, 일반동사 3인칭 -s, 과거형(-ed), 의문/부정문(do·does) 중 지문에 나오는 것을 3~5개 아주 쉽게. 관계사·분사·가정법 등 어려운 건 설명하지 말고 kind='note'로 '지금은 몰라도 OK'",
        "tone": "초등학생에게 말하듯 아주 쉬운 우리말. 문법 용어는 최소화하고 풀어서 설명"},
    2: {"key": "기초",
        "desc": "동사는 아는 학생 · to부정사·동명사·원급/비교급",
        "vocab": "모를 만한 단어 다수(18~20개 안팎)",
        "grammar": "준동사와 비교 중심 — to부정사(~하기 위해), 동명사(-ing), 원급 as~as, 「the 비교급, the 비교급」 중 지문에 나오는 것 3~4개. 하나는 kind='core'. 관계사·가정법 등은 note로 가볍게",
        "tone": "친근한 '~해요' 말투로 밑바닥부터"},
    3: {"key": "기본",
        "desc": "관계사가 안 보이는 학생 · 관계대명사·분사·동격 that",
        "vocab": "핵심+중등 단어 위주(16개 안팎)",
        "grammar": "관계사·분사 입문 — 관계대명사(주격·목적격·계속적 입문), 분사구문(-ing), 동격 that 중 지문에 나오는 것 3~4개. 하나는 kind='core'",
        "tone": "친근하지만 표준적인 설명"},
    4: {"key": "표준",
        "desc": "고1 평균·내신 대비 · 지문 핵심 문법 전부",
        "vocab": "고1 핵심 어휘 위주(14개 안팎)",
        "grammar": "지문의 핵심 문법 4~5개를 정확히 — 가정법·현재완료·과거완료·수동태·분사구문·관계사 등 지문에 실제로 나오는 것을 빠짐없이",
        "tone": "표준적인 내신 대비 설명"},
    5: {"key": "실전",
        "desc": "상위권·서술형 · 어법 함정·구문 비교·출제 포인트",
        "vocab": "고난도·핵심 어휘 위주(12개 안팎), 유의어/반의어 언급 가능",
        "grammar": "문법 포인트 5개 이상 촘촘히 + 어법 함정·서술형 대비 — 관계사 that 구분, 분사 능동/수동, 동격 vs 관계사, 수 일치, 삽입절 제거 등 출제 포인트를 rule 안에 짚어줌",
        "tone": "내신 심화. 시험에 어떻게 나오는지·서술형까지"},
}


def level_meta(level: int) -> dict:
    return LEVELS.get(int(level), LEVELS[2])


# ---------------------------------------------------------------------------
# LLM 구조화 출력 스키마
# ---------------------------------------------------------------------------
class BExample(BaseModel):
    en: str = Field(description="영어 예문(핵심어는 <b></b>로 강조 가능)")
    ko: str = Field(description="우리말 뜻/설명")


class BGrammar(BaseModel):
    kind: str = Field(description="'core'(오늘의 핵심) / 'normal'(보통) / 'note'(지금은 몰라도 OK)")
    tag: str = Field(description="짧은 배지 문구, 예: '오늘의 핵심', '문법 2', '지금은 몰라도 OK'")
    title: str = Field(description="문법 제목, 예: 'be동사 = ~이다'")
    rule: str = Field(description="쉬운 설명. 강조는 <b></b>만 사용")
    examples: list[BExample] = Field(description="지문/쉬운 예문 1~2개")


class BVocab(BaseModel):
    en: str
    pron: str = Field(description="발음 한글 표기(참고용)")
    pos: str = Field(description="품사(명사/동사/형용사/부사/숙어 등)")
    ko: str = Field(description="뜻")


class BLiteral(BaseModel):
    no: int
    en: str = Field(description="영어 문장. 의미 단위로 ' / '(공백-슬래시-공백)로 끊어서")
    ko: str = Field(description="우리말 직독직해. 영어와 같은 위치에서 ' / '로 끊어서")


class BPassageLine(BaseModel):
    no: int
    en: str


class BQuizWord(BaseModel):
    en: str
    ko: str


class BQuizGrammar(BaseModel):
    point: str = Field(description="이 문제가 묻는 핵심 문법 이름. 예: '3인칭 -s', '관계대명사 which'")
    question: str = Field(description="반드시 지문 문장을 그대로 사용. 괄호 택1 '( A / B )' 또는 빈칸 '____' 형태. 예: 'A mosquito ( sneak / sneaks ) in.'")
    answer: str = Field(description="정답만 짧게. 예: 'sneaks'")
    why: str = Field(description="정답 근거 한 줄. 예: '주어 a mosquito=하나 → 동사에 -s'")


class BQuizTranslate(BaseModel):
    en: str
    ko: str = Field(description="모범 해석(정답)")


class BridgeGen(BaseModel):
    title: str = Field(description="학습지 제목(한국어, 지문 주제). 예: '모기는 어떻게 무는가'")
    summary_oneline: str = Field(description="이 지문 전체를 한 문장으로 요약(한국어)")
    summary_body: str = Field(description="이 지문이 무슨 내용인지 2~4문장으로 쉽게 설명(한국어)")
    part_heading: Optional[str] = Field(default=None, description="지문 소제목이 있으면(없으면 null)")
    goal_grammar: str = Field(description="오늘의 목표 문법 한 줄")
    goal_sub: str = Field(description="목표 부연 한 줄(격려)")
    passage: list[BPassageLine] = Field(description="지문 문장들(번호와 함께)")
    vocab: list[BVocab]
    grammar: list[BGrammar]
    literal: list[BLiteral]
    quiz_word: list[BQuizWord] = Field(description="단어 뜻 쓰기용 8~10개")
    quiz_grammar: list[BQuizGrammar] = Field(description="핵심 문법 연습문제 4~6개. 반드시 '지문에 실제로 나온 문장'을 그대로 사용하고, 오늘 배운 핵심 문법만 물을 것")
    quiz_translate: list[BQuizTranslate] = Field(description="지문 문장 해석 2개")


# ---------------------------------------------------------------------------
# 프롬프트
# ---------------------------------------------------------------------------
SYSTEM = (
    "당신은 한국 고등학생을 가르치는 영어 선생님입니다. "
    "중학교 기초가 부족한 학생도 스스로 공부할 수 있는 '기초 브릿지 학습지'를 만듭니다. "
    "반드시 주어진 JSON 스키마에 맞춰 한국어로 작성하고, 강조는 <b></b> 태그만 사용하세요. "
    "그 외 HTML 태그나 마크다운은 쓰지 마세요."
)


def gen_prompt(title: str, body: str, level: int) -> str:
    m = level_meta(level)
    return f"""아래 영어 지문으로 '기초 브릿지 학습지' 한 부를 만드세요.

[학습자 난이도] {level}단계 — {m['key']}
- 단어: {m['vocab']}
- 문법: {m['grammar']}
- 말투/수준: {m['tone']}

[작성 규칙]
1) passage: 지문을 문장 단위로 번호를 매겨 그대로 싣기(원문 유지).
2) vocab: 위 난이도 지침대로 뽑고, 발음은 참고용 한글 표기, 품사와 뜻을 정확히.
3) grammar: 위 난이도 지침대로 개수/난이도를 맞추기. 각 카드는 지문 속 실제 예문으로.
   - kind는 'core'(가장 중요), 'normal', 'note'(지금은 몰라도 OK) 중 하나.
   - 1~2단계에서는 어려운 문법을 억지로 설명하지 말고 note 카드로 안심시키기.
4) literal(끊어읽기): 모든 지문 문장을 의미 단위로 ' / '로 끊고, 우리말도 같은 위치에서 ' / '로 끊어 직독직해.
5) quiz: 오늘 배운 것 확인 문제. 정답 포함.
   - quiz_grammar(핵심 문법 연습문제)는 반드시 <b>지문에 실제로 나온 문장</b>을 그대로 가져와서,
     오늘의 핵심 문법이 걸린 자리를 괄호 택1 '( A / B )' 또는 빈칸 '____' 로 만들 것. 4~6개.
   - 각 문제에 point(묻는 문법 이름)와 why(정답 근거 한 줄)를 채울 것.
6) 모든 설명은 해당 난이도의 학생이 이해할 수 있는 쉬운 한국어로.

[제목] {title}

[지문]
{body}
"""


# ---------------------------------------------------------------------------
# 생성
# ---------------------------------------------------------------------------
def generate(client, cfg, extraction, level: int) -> BridgeGen:
    """지문 1개(Extraction) -> 난이도 맞춤 BridgeGen."""
    return client.structured(
        system=SYSTEM,
        prompt=gen_prompt(extraction.title, extraction.body, level),
        model_cls=BridgeGen,
        max_tokens=20000,
        max_retries=cfg.processing.max_retries,
    )


# ---------------------------------------------------------------------------
# BridgeGen -> 템플릿 렌더용 dict
# ---------------------------------------------------------------------------
_KIND2LEVEL = {"core": "core", "normal": "", "note": "up"}


def _quiz_html(gen: BridgeGen) -> str:
    # A. 단어 뜻 쓰기(영→한)
    rows = []
    ws = gen.quiz_word
    half = (len(ws) + 1) // 2
    for i in range(half):
        left = ws[i]
        right = ws[i + half] if i + half < len(ws) else None
        r = (f'<tr><td class="q-num">{i+1}</td><td class="q-word">{left.en}</td><td class="q-blank"></td>')
        if right:
            r += f'<td class="q-num">{i+half+1}</td><td class="q-word">{right.en}</td><td class="q-blank"></td>'
        else:
            r += '<td></td><td></td><td></td>'
        rows.append(r + "</tr>")
    a = (f'<div class="q-block"><div class="q-h"><span class="q-badge">A</span>단어 뜻 쓰기 (영어 → 우리말)</div>'
         f'<table class="q"><tbody>{"".join(rows)}</tbody></table></div>')

    # B. 핵심 문법 연습문제 (지문 문장 그대로)
    gitems = []
    for i, g in enumerate(gen.quiz_grammar):
        point = getattr(g, "point", "")
        badge = f' &nbsp;<span class="g-point">[{point}]</span>' if point else ""
        gitems.append(f'<div class="q-line"><b>{i+1})</b> {g.question}{badge}</div>')
    glines = "".join(gitems)
    c = ('<div class="q-block"><div class="q-h"><span class="q-badge">B</span>핵심 문법 연습문제 '
         '<span style="font-weight:600;color:#6b7280;font-size:9.5px">— 지문 문장에서 알맞은 것 고르기 / 빈칸 채우기</span>'
         f'</div>{glines}</div>')

    # D. 해석
    dlines = "".join(f'<div class="q-line">{i+1}) {t.en}<span class="q-write"></span></div>'
                     for i, t in enumerate(gen.quiz_translate))
    d = (f'<div class="q-block"><div class="q-h"><span class="q-badge">C</span>다음 문장을 우리말로 해석하기</div>{dlines}</div>')
    return a + c + d


def _answer_html(gen: BridgeGen) -> str:
    a = " &nbsp; ".join(f"{i+1} {w.ko}" for i, w in enumerate(gen.quiz_word))
    c = " &nbsp; ".join(
        f"{i+1} <b>{g.answer}</b>{f' ({g.why})' if getattr(g, 'why', '') else ''}"
        for i, g in enumerate(gen.quiz_grammar))
    d = " &nbsp; ".join(f"{i+1} {t.ko}" for i, t in enumerate(gen.quiz_translate))
    return (f'<div class="ans-block"><b>A.</b> {a}</div>'
            f'<div class="ans-block"><b>B.</b> {c}</div>'
            f'<div class="ans-block"><b>C.</b> {d}</div>')


def to_render(gen: BridgeGen, level: int, source: str) -> dict:
    m = level_meta(level)
    cover = {
        "title": "영어, 처음부터 다시",
        "subtitle": gen.title,
        "tag": f"난이도 {level}단계 · {m['key']}",
        "book": f"지문 출처 : {source}",
        "intro": [
            f"이 학습지는 <b>난이도 {level}단계({m['key']})</b>에 맞춰 만들었어요.",
            "지문에 나온 <b>단어</b>와 <b>끊어읽기 해석</b>을 함께 담았어요.",
            "문법은 이 수준에 맞춰 <b>꼭 필요한 것</b>만 골라 설명했어요.",
            "마지막엔 <b>직접 풀어보는 문제</b>로 확인합니다.",
        ],
    }
    overview = {
        "source": source,
        "oneline": f"한 문장 요약 &nbsp;→&nbsp; \"{gen.summary_oneline}\"",
        "parts": [{"title": "이 글은 무슨 이야기?", "en": "", "body": gen.summary_body}],
        "flow": [],
        "extra": f"난이도 <b>{m['key']}</b> · {m['desc']}",
    }
    day = {
        "day_no": 1,
        "title": gen.title,
        "range_label": f"난이도 {level} · {m['key']}",
        "part_heading": gen.part_heading,
        "goal_grammar": gen.goal_grammar,
        "goal_sub": gen.goal_sub,
        "passage": [{"no": p.no, "en": p.en} for p in gen.passage],
        "vocab": [{"en": v.en, "pron": v.pron, "pos": v.pos, "ko": v.ko} for v in gen.vocab],
        "vocab_tip": "※ 발음은 참고용 한글 표기예요. 단어는 &lsquo;영어→뜻&rsquo;, &lsquo;뜻→영어&rsquo; 양방향으로 외우면 좋아요.",
        "grammar": [{"level": _KIND2LEVEL.get(g.kind, ""), "tag": g.tag, "title": g.title,
                     "rule": g.rule, "examples": [{"en": e.en, "ko": e.ko} for e in g.examples]}
                    for g in gen.grammar],
        "literal": [{"no": s.no, "en": s.en, "ko": s.ko} for s in gen.literal],
        "quiz_html": _quiz_html(gen),
        "answer_html": _answer_html(gen),
    }
    return {"cover": cover, "overview": overview, "day": day, "source": source}


def mock_gen(title: str = "모기는 어떻게 무는가", level: int = 1) -> BridgeGen:
    """API 없이 디자인만 확인하는 샘플 BridgeGen."""
    return BridgeGen(
        title=title,
        summary_oneline="작고 성가신 모기가, 사실은 인류 역사상 가장 많은 사람을 죽인 존재였다.",
        summary_body="모기가 어떻게 사람을 물고 먹잇감을 찾는지 설명하는 글이에요. "
                     "암컷 모기는 알을 낳는 데 필요한 단백질 때문에 우리 피를 빱니다.",
        part_heading="PART 1  THE NUISANCE (성가신 존재)",
        goal_grammar="문장의 뼈대 — 누가(주어) + 뭐했다(동사)",
        goal_sub="누가/뭐했다만 찾아도 오늘은 성공!",
        passage=[
            BPassageLine(no=1, en="A mosquito sneaks in and pierces your skin."),
            BPassageLine(no=2, en="It fills its belly with blood and then escapes."),
        ],
        vocab=[
            BVocab(en="mosquito", pron="머스키토우", pos="명사", ko="모기"),
            BVocab(en="pierce", pron="피어스", pos="동사", ko="뚫다, 찌르다"),
            BVocab(en="belly", pron="벨리", pos="명사", ko="배, 복부"),
            BVocab(en="escape", pron="이스케입", pos="동사", ko="달아나다"),
        ],
        grammar=[
            BGrammar(kind="core", tag="가장 먼저", title="문장의 뼈대 = 주어 + 동사",
                     rule="<b>누가(주어) + 뭐했다(동사)</b> 두 개만 먼저 찾으면 절반은 성공! 나머지는 살이라 몰라도 돼요.",
                     examples=[BExample(en="<b>A mosquito</b> <b>sneaks</b> in.", ko="모기가 몰래 들어온다")]),
            BGrammar(kind="note", tag="지금은 몰라도 OK", title="어려운 문법은 나중에 배워요!",
                     rule="지금은 &lsquo;누가/뭐했다&rsquo;만 잡아도 충분해요.",
                     examples=[BExample(en="It fills its belly with blood.", ko="그것이 배를 피로 채운다")]),
        ],
        literal=[
            BLiteral(no=1, en="A mosquito sneaks in / and pierces your skin.",
                     ko="모기가 몰래 들어온다 / 그리고 네 피부를 뚫는다."),
            BLiteral(no=2, en="It fills its belly with blood / and then escapes.",
                     ko="그것은 배를 피로 채운다 / 그런 다음 달아난다."),
        ],
        quiz_word=[BQuizWord(en="mosquito", ko="모기"), BQuizWord(en="pierce", ko="뚫다"),
                   BQuizWord(en="belly", ko="배"), BQuizWord(en="escape", ko="달아나다")],
        quiz_grammar=[
            BQuizGrammar(point="3인칭 -s", question="A mosquito ( sneak / sneaks ) in and ( pierce / pierces ) your skin.",
                         answer="sneaks, pierces", why="주어 a mosquito=하나 → 동사에 -s"),
            BQuizGrammar(point="be동사", question="This ( is / are ) a mild allergic reaction.",
                         answer="is", why="주어 This=하나 → is"),
            BQuizGrammar(point="3인칭 -s", question="It ( fill / fills ) its belly with blood.",
                         answer="fills", why="주어 It=하나 → -s"),
            BQuizGrammar(point="주어 찾기", question="밑줄 친 진짜 주어에 ○: ( A mosquito ) sneaks in and pierces your skin.",
                         answer="A mosquito", why="동사(sneaks) 앞의 명사가 주어"),
        ],
        quiz_translate=[BQuizTranslate(en="It fills its belly with blood and then escapes.",
                                        ko="그것은 배를 피로 채우고 그런 다음 달아난다.")],
    )


def render_pdf(gen: BridgeGen, out_path: str | Path, level: int, source: str = "") -> Path:
    from weasyprint import HTML

    ctx = to_render(gen, level, source)
    html = _env.get_template("bridge_gen.html.j2").render(**ctx)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path))
    return out_path

// document.js — 문서 조립 (명세 §5.1 문서 구조)
//
// 1. 표지 (제목/부제/출처/사용법 — "쌤이 알려주는 사용법", 반말 지도 톤)
// 2. 챕터마다: 제목 → 무엇인가요 → 신호 → 해석법 → 같이 풀어보기(2) → 혼자 풀어보기(나머지) → 페이지브레이크
// 3. 맨 뒤: 정답 섹션 (챕터별 그룹핑, practice 만 — chunks 를 이어붙인 한글)

const {
  Document, Paragraph, TextRun, AlignmentType, ShadingType,
  Table, TableRow, TableCell, WidthType, BorderStyle,
  TabStopType, TabStopPosition, LeaderType,
} = require('docx');
const S = require('./styles');
const B = require('./boxes');
const { makeTip } = require('./tip');
const { tokenizeSignals } = require('./signals');

// 지문 문장 → PART0 신호 형광펜이 칠해진 docx TextRun 배열
const HL_STYLE = {
  sig: { highlight: 'yellow' },
  skip: { shading: { type: ShadingType.CLEAR, fill: 'E9EBED' }, color: '7A7F86' },
  pos: { shading: { type: ShadingType.CLEAR, fill: 'D9EFE1' }, color: '0C3F26', bold: true },
  neg: { shading: { type: ShadingType.CLEAR, fill: 'FBE0DB' }, color: 'B24A38', bold: true },
};
function hlRunsDocx(en) {
  return tokenizeSignals(en).map((tok) => new TextRun({
    text: tok.t, size: 22, font: S.FONT_EN, ...(tok.cls ? HL_STYLE[tok.cls] : {}),
  }));
}

// 각 챕터의 worked 를 앞 2문장만 "같이 풀어보기" 로 쓰고, 나머지는 steps 를
// 떼어 "혼자 풀어보기(practice)" 앞쪽으로 이동시킨다(명세 §4). 원본은 건드리지 않음.
function splitWorked(categories) {
  return categories.map((cat) => {
    const keepWorked = cat.worked.slice(0, 2);
    const moved = cat.worked.slice(2).map((w) => ({
      src: w.src, en: w.en, chunks: w.chunks, catch: w.catch, vocab: w.vocab, trap: w.trap,
    }));
    return { ...cat, worked: keepWorked, practice: [...moved, ...cat.practice] };
  });
}

// 문장별 함정 문구 선택: 문장에 trap 이 있으면 그걸, 없으면 챕터 traps 를 순환.
function pickTrap(cat, s, i) {
  if (s && s.trap) return s.trap;
  const arr = cat && cat.traps;
  return Array.isArray(arr) && arr.length ? arr[i % arr.length] : '';
}

// ── 표지 ─────────────────────────────────────────────
function coverParagraphs() {
  const center = (children, after) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after }, children });
  return [
    center([new TextRun({ text: '문법으로 뚫는 영어 해석 교재', bold: true, size: 44, color: S.NAVY, font: S.FONT })], 200),
    // 부제는 실제 챕터 순서(수동태→…→분사구문)에 맞춰 표기
    center([new TextRun({ text: '전치사구 · 수동태 · to부정사 · 동명사 · 관계사 · 분사 · 분사구문', size: 26, color: S.BRASS, bold: true, font: S.FONT })], 100),
    center([new TextRun({ text: '자료 출처: 2023학년도 수능 · 2024년 9월 평가원 모의평가(고3) 기출', size: 20, italics: true, font: S.FONT })], 100),
    center([new TextRun({ text: '기초 문법 학습용 · 과외 교재', size: 18, color: '666666', font: S.FONT })], 700),

    new Paragraph({
      spacing: { before: 200, after: 100 },
      shading: { type: ShadingType.CLEAR, fill: S.LIGHTGRAY },
      children: [new TextRun({ text: '  📌 쌤이 알려주는 사용법', bold: true, size: 22, color: S.NAVY, font: S.FONT })],
    }),
    B.p('문법 용어가 낯설어도 괜찮아. 이 교재는 그런 너를 위해 만든 거야 — 순서대로만 따라오면 돼.'),
    B.bullet('챕터마다 순서는 이래: ① 이게 뭔지 쌤이 설명 → ② 어떻게 알아채는지(신호) → ③ 쌤이랑 같이 풀기(2문장) → ④ 너 혼자 풀어보기(나머지 전부)'),
    B.bullet('문장마다 박스 순서는 이래: 어휘 → 끊어읽기 팁 → 끊어읽기(영어→한글) → ⚠️ 이거 조심(함정) → 이 정도는 캐치.'),
    B.bullet('끊어읽기는 앞에서부터만 읽어, 뒤로 돌아가지 말고 — 그게 진짜 독해야. 영어 원문은 볼드로 크게 표시해뒀어.'),
    B.bullet('⚠️ 이거 조심 박스는 자주 틀리는 함정을 미리 알려줘 — 읽기 전에 꼭 체크해. 연습문제는 답 쓰는 칸이 비어있으니 직접 써보고, 정답은 맨 뒤에서 확인해.'),
    B.pageBreak(),
  ];
}

// ── 설명 섹션 ────────────────────────────────────────
function introSection(cat) {
  const out = [B.h1(cat.title)];
  out.push(B.h2('무엇인가요?'));
  cat.intro.forEach((t) => out.push(B.p(t)));
  out.push(B.h2('어떻게 찾나요? (신호)'));
  cat.signal.forEach((t) => out.push(B.bullet(t)));
  out.push(B.h2('어떻게 해석하나요?'));
  cat.method.forEach(([l, t]) => out.push(new Paragraph({
    spacing: { after: 50 },
    indent: { left: 300 },
    children: [
      new TextRun({ text: l + '  ', bold: true, color: S.NAVY, size: 20, font: S.FONT }),
      new TextRun({ text: t, size: 20, font: S.FONT }),
    ],
  })));
  return out;
}

// ── 문장 렌더 ────────────────────────────────────────
// 순서: 어휘 → 끊어읽기 팁(어디서 끊을지) → 끊어읽기 → 함정 주의 → (내 해석) → 캐치
function renderWorked(w, trap) {
  return [
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.tipBox(makeTip(w.chunks)),
    ...B.chunkBox(w.chunks),
    ...B.trapBox(trap),
    ...B.catchBox(w.catch),
  ];
}
// 연습문제: 초록 끊어읽기 카드는 빼고, 학생이 직접 끊어 읽고 해석을 쓰는 칸을 준다.
// (끊어읽기 정답·캐치는 맨 뒤 정답·해설 섹션에서 확인)
function renderPractice(w, idx, trap) {
  return [
    B.h3(`연습 ${idx + 1}`),
    B.engHeader(w.en, w.src),
    ...B.vocabBox(w.vocab),
    ...B.tipBox(makeTip(w.chunks)),
    ...B.trapBox(trap),
    ...B.answerWriteBox(),
  ];
}

// ── 챕터 ─────────────────────────────────────────────
function chapterParagraphs(cat) {
  const out = [...introSection(cat)];
  // 같이 풀어보기 · 혼자 풀어보기는 각각 새 페이지에서 시작
  out.push(B.pageBreak());
  out.push(B.h2('같이 풀어보기'));
  cat.worked.forEach((w, i) => out.push(...renderWorked(w, pickTrap(cat, w, i))));
  out.push(B.pageBreak());
  out.push(B.h2('혼자 풀어보기 (연습문제)'));
  cat.practice.forEach((w, i) => out.push(...renderPractice(w, i, pickTrap(cat, w, i))));
  out.push(B.pageBreak());
  return out;
}

// ── 정답·해설 섹션 (맨 뒤, practice 만) ────────────────
//    문제마다 끊어읽기 정답(영어/한글) + 핵심(캐치)을 실어 해설로 제공.
function answerParagraphs(categories) {
  const out = [B.pageBreak(), B.h1('정답 · 해설 — 혼자 풀어보기')];
  out.push(B.p('직접 푼 걸 여기서 맞춰보자. 끊어읽기 정답과 이 문장에서 붙잡을 핵심을 정리했어.'));
  categories.forEach((cat) => {
    if (!cat.practice || cat.practice.length === 0) return;
    out.push(B.h2(cat.key));
    cat.practice.forEach((w, i) => {
      out.push(B.h3(`${i + 1}. ${w.en}  [${w.src}]`));
      out.push(...B.chunkBox(w.chunks));   // 끊어읽기 정답(영어/한글)
      out.push(...B.catchBox(w.catch));    // 핵심
    });
  });
  return out;
}

// ── 지문(passage) 모드 docx ─────────────────────────
// 목차=지문, 문장 원문 순서, 문법은 '구문 포인트' 표기, 지문 요지 캐치.
function passageSentenceParas(s, idx) {
  const out = [
    new Paragraph({
      spacing: { before: 200, after: 40 },
      children: [
        new TextRun({ text: `${idx}. `, bold: true, size: 22, color: S.NAVY, font: S.FONT }),
        new TextRun({ text: s.en, bold: true, size: 24, font: S.FONT_EN, color: '111111' }),
      ],
    }),
  ];
  if (s.point) {
    out.push(new Paragraph({
      spacing: { after: 80 },
      children: [new TextRun({ text: `구문 포인트 — ${s.point}`, bold: true, size: 18, color: S.BRASS, font: S.FONT })],
    }));
  }
  // 순서: 어휘 → 해석(쓰기) → 캐치(쓰기) → 이거 조심(오역 주의)
  //   (끊어읽기 원리는 책 앞 '끊어읽기 팁 — 어디서 끊을까?' 페이지에 한 번)
  out.push(...B.vocabBox(s.vocab));
  out.push(...B.interpretWriteBox());
  out.push(...B.catchWriteBox());
  out.push(...B.trapBox(s.trap));
  return out;
}

// 책 앞 '끊어읽기 팁 — 어디서 끊을까?' 페이지 (목차 항목 1회)
const CUT_SIGNALS_DOCX = [
  ['① 전치사 앞 (in/on/at/of/with/for…)', "전치사구(전치사+명사)는 한 덩어리 — 예) in 1937 → ‘1937년에’"],
  ['② to부정사 앞 (to+동사원형)', "‘~하는 것/~할/~하기 위해’ 덩어리 — 예) to house his works → ‘작품을 소장하기 위한’"],
  ['③ 접속사 앞 (and/but/that/because/when…)', '뒤에 새 절(주어+동사)이 붙어 — 예) …, and he started teaching → 새 사건 시작'],
  ['④ 관계사 앞 (who/which/that/where…)', '앞 명사를 꾸미는 절의 시작 — 예) the man who lives … → ‘…하는 그 남자’'],
  ['⑤ 분사 · 콤마 (-ing/-ed 수식, ,)', '새 수식 덩어리 시작·이미 찍힌 경계 — 예) …, was established → 콤마·수동에서 끊기'],
];
function principlePageParas() {
  const out = [B.h1('끊어읽기 팁 — 어디서 끊을까?')];
  out.push(B.p('핵심 원리: 진짜 주어+동사(뼈대)를 먼저 잡고, 나머지 수식 덩어리는 신호어 앞에서 끊어 앞에서부터 붙여 읽어 — 되돌아가지 않기!', { bold: true }));
  out.push(B.h2('끊는 신호 5가지'));
  CUT_SIGNALS_DOCX.forEach(([name, rule]) => {
    out.push(new Paragraph({
      spacing: { after: 40 }, indent: { left: 200 },
      children: [
        new TextRun({ text: `${name}  `, bold: true, size: 21, color: S.NAVY, font: S.FONT }),
        new TextRun({ text: rule, size: 20, font: S.FONT }),
      ],
    }));
  });
  out.push(B.p('끊는 자리는 늘 ‘새 덩어리가 시작되는 신호어 앞’ — 지문에서 이 5개만 찾으면 문장이 저절로 끊긴다.'));
  out.push(B.pageBreak());
  return out;
}

// ── 독해의 원리(PART0) — Ortica 영어 '형광펜 독해' 원리 총론 (docx) ──
const PP_TEAL = '14603A'; const PP_GRAM = '5E4C9E';
function ppH(t, sub) {
  const out = [B.h1(t)];
  if (sub) out.push(B.p(sub, { italics: true, color: '666666' }));
  return out;
}
function ppGoal(t) { return B.p(`핵심 — ${t}`, { bold: true }); }
function ppKV(k, v) {
  return new Paragraph({
    spacing: { after: 40 }, indent: { left: 200 },
    children: [
      new TextRun({ text: `${k}  `, bold: true, size: 20, color: PP_TEAL, font: S.FONT }),
      new TextRun({ text: v, size: 19, font: S.FONT }),
    ],
  });
}
function ppEx(label, en, note) {
  return [
    new Paragraph({
      spacing: { before: 30, after: note ? 10 : 40 }, indent: { left: 240 },
      children: [
        new TextRun({ text: `[${label}] `, bold: true, size: 17, color: PP_GRAM, font: S.FONT }),
        new TextRun({ text: en, italics: true, size: 19, font: S.FONT }),
      ],
    }),
  ].concat(note ? [new Paragraph({ spacing: { after: 40 }, indent: { left: 300 }, children: [new TextRun({ text: `↳ ${note}`, size: 18, color: '555555', font: S.FONT })] })] : []);
}
// 태도·완급·추론·연결사·재진술·5변환 (글의 구조 앞)
function principlesFrontParas() {
  const out = [];
  out.push(...ppH('모의고사 점수는 ‘태도’에서 나온다', '“정확히 모든 문장 해석” ≠ “좋은 점수” — 점수는 글의 중심 내용을 잡은 사람에게 간다'));
  out.push(ppGoal('구문을 완벽히 분석한 사람이 아니라 “무슨 말을 하려는가”를 잡은 사람이 점수를 가져간다.'));
  out.push(B.bullet('공부할 때 = 걸어다니는 사전: 단어·구문을 끝까지 정확히(실력의 바탕).'));
  out.push(B.bullet('시험 칠 때 = 모르는 건 추론: 멈추지 말고 문맥으로 추론, “무슨 말을 하려는가”만.'));
  out.push(B.bullet('HOW: 초반 3문장을 관통하는 하나의 키워드를 잡는다(반복되는 말). 주제 문제 정답=그 키워드(같은 용어 아니어도).'));
  out.push(B.pageBreak());

  out.push(...ppH('완급조절 — OLD / MAIN / SUPPORT로 나눠 읽기', '한 문장은 주절(MAIN)에 힘이 실린다 · 문두 배경과 뒤 부연은 약하게'));
  out.push(B.p('📖 예시로 나눠보기 — 한 문장을 세 역할로 쪼개봐 (Although the plan looks simple, it often fails in practice, leaving many beginners confused.)', { bold: true }));
  const wex = (tag, tagColor, en, note) => new Paragraph({
    spacing: { after: 40 }, indent: { left: 200 },
    children: [
      new TextRun({ text: `[${tag}] `, bold: true, size: 18, color: tagColor, font: S.FONT }),
      new TextRun({ text: en, size: 20, italics: true, font: S.FONT }),
      new TextRun({ text: `  → ${note}`, size: 17, color: '666666', font: S.FONT }),
    ],
  });
  out.push(wex('OLD · 부사절', '6B7280', 'Although the plan looks simple,', '문두 배경(부사절·전치사구) — 약하게'));
  out.push(wex('MAIN · 주절', '14603A', 'it often fails in practice,', '진짜 하고 싶은 말(주절) — 가장 강하게'));
  out.push(wex('SUPPORT · 분사구문', 'B07A1C', 'leaving many beginners confused.', '뒤 부연(분사구문·관계사) — 약하게'));
  out.push(B.p('▶ 문두 부사절·전치사구(OLD)와 뒤의 분사구문·「,which」관계사(SUPPORT)는 약하게, 가운데 주절(MAIN)에 힘준다.'));
  out.push(ppKV('OLD (배경)', '문두 부사절(Although~)·전치사구(In~) → 약하게'));
  out.push(ppKV('MAIN (주제)', '주절 — 필자가 진짜 하고 싶은 말 → 가장 강하게'));
  out.push(ppKV('SUPPORT (부연)', '뒤의 분사구문(, -ing/-ed)·관계사(, which) → 약하게'));
  out.push(B.bullet('OLD 신호: 문두에서 컴마로 끊기는 부사절·전치사구. SUPPORT 신호: 뒤에 붙는 분사구문·「,which」비제한 관계사.'));
  out.push(...ppEx('OLD→NEW', 'Although this is true, it has also become a tired argument.', '양보(OLD)는 약하게 → 주절 ‘진부한 주장’(NEW·핵심)이 하고 싶은 말.'));
  out.push(...ppEx(',관계사', '…rediscovered Mendel’s work, which of course had been there all along.', '「,which」이하는 부연 — 핵심은 ‘세 과학자가 재발견’.'));
  out.push(B.pageBreak());

  out.push(...ppH('모르는 것은 ‘추론’한다 — 어순·구두점', '영어는 General → Specific · 추상적인 말이 앞에 오면 뒤에 구체 정보'));
  out.push(ppGoal('모르는 단어에 멈추지 말고 ‘뒤가 알려줄 것’이라 믿고 읽어라.'));
  out.push(ppKV('BE동사 (A=B)', '정의를 여는 신호. Tax is the application… → ‘Tax=분배 정의 이론의 적용’.'));
  out.push(ppKV('콜론 :', '부연·재진술·열거. A:B에서 A 이해되면 B는 확인만.'));
  out.push(ppKV('대쉬 —', '상술. 앞 이해되면 약하게(중간 삽입=대쉬, 끝=콜론).'));
  out.push(ppKV('세미콜론 ;', '두 문장 연결(and·but·so). ‘관련 있구나’만.'));
  out.push(ppKV('따옴표 “ ”', '인용·강조, 또는 단어를 비틀어 씀(필자 의도).'));
  out.push(ppKV('병렬 A,B and C', '하나만 알면 나머지는 비슷한 문맥으로 넘긴다.'));
  out.push(B.pageBreak());

  out.push(...ppH('연결사 = “어디가 중요한지 알려줄게”', '문장 어디에 있든 앞뒤 ‘사이’에 놓고 읽어라 · 역접은 완급의 분기점'));
  out.push(ppKV('Switching (A‹B)', '‘그러나·대신에’ 뒤가 핵심, 앞은 약하게 — however·but·still·nevertheless·instead·rather'));
  out.push(ppKV('Contrast (A=B)', '‘반면에’ 두 대상 다 중요 — on the other hand·by contrast·conversely'));
  out.push(B.bullet('but/however: 1순위 그러나·반면에 / 2순위 강조(Emphasis).'));
  out.push(B.bullet('In fact: 순접(사실상)/역접(하지만 사실은). on the contrary: 오히려(앞 부정·강조) ≠ on the other hand.'));
  out.push(B.pageBreak());

  out.push(...ppH('재진술(Paraphrasing) — 같은 말을 알아채기', '독해의 최종 기술 · 명시적 단서 없이 “앞의 그 말을 바꿔 한 거구나”를 느끼는 것'));
  out.push(ppGoal('필자는 핵심을 한 번만 말하지 않고 표현을 바꿔 되풀이하며, 정답 선지는 그 되풀이의 마지막 한 번이다.'));
  out.push(B.p('🔁 이 교재에선 지문마다 「재진술 사슬」 문제로 훈련 — 소재 하나면 A→A′→A″…, 비교 지문이면 A→A′… · B→B′… (억지로 만들지 않음).'));
  out.push(ppKV('재진술', 'that is · in other words · in effect · indeed'));
  out.push(ppKV('예시·요약', 'for example · for instance / in short · in conclusion'));
  out.push(ppKV('나열·인과', 'similarly · moreover / therefore · thus · as a result'));
  out.push(B.bullet('재진술 독해 = G(일반화)↔S(구체화)를 오간다. 표현 달라도 하나의 범주면 같은 말.'));
  out.push(B.pageBreak());

  out.push(...ppH('재진술로 정답을 만든다 — 5변환 · 오답 함정', '정답=뜻 그대로 단어만 바꿈 / 오답=단어 그대로 두고 뜻 왜곡'));
  out.push(ppKV('① 동의어 치환', 'proper·forces·detailed → careful·drives·thorough'));
  out.push(ppKV('② 구체→추상', 'a songwriter·a boundary → creative people·locality'));
  out.push(ppKV('③ 품사 전환', 'decide(동사) → decision-making(명사)'));
  out.push(ppKV('④ 반대구조', 'does not shrink → expands'));
  out.push(ppKV('⑤ 비유→직설', 'a window to other worlds → unfamiliar perspectives'));
  out.push(B.bullet('오답 4잣대: copy(지문 단어 그대로)·reverse(방향 반대)·distort(한 군데 어긋남)·off(근거 없음).'));
  out.push(B.bullet('흔한 오해: all·always·only 극단어=오답은 사설 요령. 평가원은 ‘지문 근거와의 관계’로 오답을 만든다.'));
  out.push(B.pageBreak());
  return out;
}
// 논리관계 구문 ①②, 형광펜 신호 사전 (필자 입장 뒤)
const HIGHLIGHT_SIGNALS_DOCX = [
  ['① 역접·대조', 'However·But·Yet·Nevertheless·In contrast·On the contrary·Instead·Conversely·Unlike·Whereas·Still·No longer·not A but B — 앞을 뒤집는다=필자 주장'],
  ['② 결론·귀결', 'Thus·Therefore·Hence·So·Consequently·As a result·In conclusion·In short·Ultimately — 글을 닫는 문장=주제'],
  ['③ 인과', 'because·since·due to·owing to·lead to·result in·give rise to·thereby·in order to — 논리의 뼈대'],
  ['④ 강조·주장', 'should·must·ought to·need to·important·essential·crucial·vital·key·In fact·Indeed·above all — 대놓고 미는 문장'],
  ['⑤ 최상·유일·한정', 'the most·the best·the only·first·only when·only if·unless·except·as long as — 정답 단골 자리'],
  ['⑥ 통념·반전', 'Many believe·It is thought·Traditionally·Contrary to popular belief·Surprisingly·Ironically — 통념 깨는 곳=주제'],
  ['⑦ 정의·재정의', 'is defined as·means·refers to·that is·in other words·콜론(:)·대시(—) 뒤 — 개념 못 박는 문장'],
  ['⑧ 태도·평가어(±)', '＋ benefit·valuable·effective ↔ − problem·risk·illusion·myth·fail·drawback — 정답의 방향(＋/−)'],
  ['⑨ 예시 후 일반화', 'In each case·In general·Overall·This suggests/shows/means — 예시 접고 결론 복귀'],
  ['⑩ 위치', '글 첫 문장·각 단락 첫 문장·마지막 문장·빈칸/밑줄 문장+앞뒤 — 무조건 읽는 자리'],
  ['⑪ 지시·연결', 'this·these·that·those·such(a)·one·another·the former·the latter — 순서·삽입의 핵심'],
  ['⑫ 첨가·병렬', 'not only~but also·moreover·furthermore·in addition·similarly·likewise — 같은 방향 추가(주제 강화)'],
];
function principlesBackParas() {
  const out = [];
  out.push(...ppH('논리관계 구문 — 인과(→) · 등호(=)', '독해 = 문장들의 ‘관계’ 잡기 · 관계는 넷 — 인과·등호·대조·비교'));
  out.push(ppKV('원인 → 결과', 'A cause/lead to/result in/bring about/give rise to/trigger/contribute to B'));
  out.push(ppKV('결과 ← 원인', 'A result from/stem from/arise from/derive from/be based on/attribute A to B'));
  out.push(ppKV('등호·정의 A=B', 'A is B/be called/define A as/refer to A as/represent/regard A as B (신호: that is·i.e.·such as)'));
  out.push(B.pageBreak());

  out.push(...ppH('논리관계 구문 — 대조(↔) · 비교(>)', '이 표현=글에 소재가 둘(A·B)이라는 신호 · 관계를 기호로 잡아라'));
  out.push(ppKV('A > B (우위)', 'more A than B·outweigh·surpass·exceed·prevail over·prefer A to B·A rather than B'));
  out.push(ppKV('A < B (밀림)', 'less A than B·inferior to·be overwhelmed/overshadowed/dwarfed by'));
  out.push(ppKV('A ↔ B (대조)', 'differ from·distinguish A from B·unlike·whereas·on the other hand·the former/the latter'));
  out.push(ppKV('A ⇒ B (대체)', 'replace·displace·give way to·shift/move from A to B'));
  out.push(B.bullet('초점: not A but B — B가 필자의 초점, A는 버리는 미끼(−). 필자가 미는 쪽(>·B)이 곧 주제.'));
  out.push(B.pageBreak());

  out.push(...ppH('형광펜 독해 — 무엇을 읽고 무엇을 버릴까', '아래 신호가 보이면 무조건 읽는다 · 훑기 → 칠하기 → 찍기'));
  HIGHLIGHT_SIGNALS_DOCX.forEach(([k, v]) => out.push(ppKV(k, v)));
  out.push(B.bullet('스킵: for example·such as·take/consider(예시) · 숫자·연도·인명 나열 · Although/Despite 양보절 · 긴 관계절(, which~) — 주절·주장만.'));
  out.push(B.pageBreak());
  return out;
}

// 책 앞 '글의 구조 — 어떤 짜임이 있나?' 페이지 (목차 항목 1회, 모의고사 지문 기준)
const STRUCTURE_GUIDE_DOCX = [
  ['① 통념 → 반박(반전)',
    '통념: many people think/believe · it is widely believed · traditionally · most people assume  →  반전: But · However · Yet · In fact · Contrary to',
    '흔한 생각(통념)을 깔아둔 뒤 뒤집어 필자 주장을 편다'],
  ['② 주장 → 근거·예시',
    '주장: should · must · it is important that  →  근거·예시: because · for example · research shows · therefore',
    '주장을 먼저 내세우고 이유·연구·예시로 뒷받침'],
  ['③ 문제 → 해결(방안)',
    '문제: problem · challenge · issue · concern  →  해결: solution · solve · address · one way to · need to',
    '문제를 제기하고 해결책·방안을 제시'],
  ['④ 비교 · 대조',
    '대조: while · whereas · unlike · in contrast · on the other hand  ·  비교: similarly · likewise · just as · both',
    'A와 B의 공통점·차이점을 견줌'],
  ['⑤ 시간 · 순서(나열)',
    '순서: first · second · then · next · later · after · finally  ·  시간: in 1937 · meanwhile · over time',
    '사건·과정을 시간·순서대로(전기·실험·역사)'],
  ['⑥ 예시 → 일반화(결론)',
    '예시: for example · for instance · such as · consider  →  결론: thus · therefore · in short · this suggests · overall',
    '구체 사례들을 든 뒤 일반 원리·결론으로 묶음'],
];
function structureTypesPageParas() {
  const out = [B.h1('글의 구조 — 어떤 짜임이 있나?')];
  out.push(B.p('글의 구조 = 필자가 생각을 배치한 ‘틀’. 전환어(But/However…)와 연결어를 신호로 잡으면 구조가 보이고, 구조가 보이면 요지·필자 주장이 빨리 잡힌다. (모의고사·수능 독해 지문 기준 6가지)', { bold: true }));
  STRUCTURE_GUIDE_DOCX.forEach(([name, sig, flow]) => {
    out.push(new Paragraph({
      spacing: { after: 20 }, indent: { left: 200 },
      children: [new TextRun({ text: `${name}  —  ${flow}`, bold: true, size: 21, color: S.NAVY, font: S.FONT })],
    }));
    out.push(new Paragraph({
      spacing: { after: 90 }, indent: { left: 360 },
      children: [new TextRun({ text: `🔎 ${sig}`, size: 18, italics: true, color: '5E4C9E', font: S.FONT })],
    }));
  });
  out.push(B.p('지문마다 ‘글의 구조 — 해석 전에 예측!’에서 이 6개 중 하나를 골라 보고, 지문 끝에서 정답과 맞춰본다.'));
  out.push(B.pageBreak());
  return out;
}

// 필자 입장 신호 어휘 — Ortica 영어 VOCA(DAY 31·32·33) 전량, 뉘앙스별 그룹.
const STANCE_POS_DOCX = ['이익·유익', 'benefit · beneficial · fruitful · merit · valuable · priceless · work(효과가 있다)',
  '중요·핵심·필수', 'core · key · point · critical · crucial · essential · integral · indispensable · necessary · fundamental · vital · significant · substantial · prime · principal · prevailing · matter · count · be of importance · relevant',
  '집중·주목', 'center on · concentrate on · focus on · attend to',
  '강조·강화·향상', 'emphasize · stress · enhance · reinforce · prioritize',
  '필요·추구·선호', 'need · require · seek to V · fond of · desirable · in favor of',
  '강조 구문·부사', 'only · invariably · substantially · nothing but · not just A but also B · without A · It is … that V · win out'];
const STANCE_NEG_DOCX = ['버리다·제거', 'abandon · discard · scrap · drop · remove · eliminate · discharge · leave out · rule out · removal',
  '무시·간과', 'disregard · ignore · overlook · neglect · dismiss',
  '부족·부재·결핍', 'lack · shortage · absence · absent from · free from · incapable of · of little account',
  '제한·회피·벗어남', 'restrict · limit · avoid · sidestep · bypass · shy away from · deviate from · break away from · move away from · disengage from · apart from · aside from · departure from · quit · detach',
  '거절·거부·금지', 'refuse · reject · resist · exclude · deny · say no to · disapprove · discourage · forbid',
  '방해·차단·단절', 'interfere with · stand in the way of · cut off · break with · displace · stop/prevent/keep A from Ving',
  '실패·상실·약화', 'fail · lose out · diminish',
  '비판·의심·이의', 'criticize · question · doubt · obscure · challenge',
  '무가치·문제·결함', 'drawback · downside · side effect · flaw · myth · misleading · worthless · irrelevant · unnecessary · poor · costly · challenging · mere',
  '무관·독립', 'have nothing to do with · have no bearing on · have no idea of · independent of A · independently · immune to · isolation',
  '부정 부사·구문', "hardly · rarely · by no means · don't bother · unlikely to V · allergic to · erroneously · other than · at the price[expense] of · It is of no use to V · It's not so much … but ~ · strip[free] A of B · reluctance · exception"];
const STANCE_NEU_DOCX = ['유보·추측(단정 회피)', 'may · might · can · tend to · seem · appear · suggest · some · often · in some cases · not necessarily',
  '양면·균형 제시', 'on one hand … on the other hand · while ~ · both A and B · it depends · vary',
  '객관 서술(관찰·보고)', 'describe · explain · report · note · observe · according to · studies show (해석 없이 나열만)'];
function stancePanelParas(title, color, arr, note) {
  const out = [new Paragraph({
    spacing: { before: 120, after: note ? 30 : 50 },
    children: [new TextRun({ text: title, bold: true, size: 22, color, font: S.FONT })],
  })];
  if (note) out.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 200 }, children: [new TextRun({ text: note, size: 17, color: '555555', font: S.FONT })] }));
  for (let i = 0; i < arr.length; i += 2) {
    out.push(new Paragraph({
      spacing: { after: 40 }, indent: { left: 200 },
      children: [
        new TextRun({ text: `${arr[i]}   `, bold: true, size: 17, color, font: S.FONT }),
        new TextRun({ text: arr[i + 1], size: 18, font: S.FONT }),
      ],
    }));
  }
  return out;
}
function stanceTypesPageParas() {
  const out = [B.h1('필자의 입장 — 어떤 어휘로 드러나나?')];
  out.push(B.p('필자가 대상을 두고 쓴 ‘평가 어휘’를 잡으면 입장이 보인다. 진짜 주장은 보통 마지막 문장(therefore·in conclusion)이나 But·However 뒤, should·must 에서 터져 나온다. (Ortica 영어 VOCA 기반)', { bold: true }));
  out.push(...stancePanelParas('👍 긍정 · 중요 — 필자가 좋게·중요하게 봄', '14603A', STANCE_POS_DOCX));
  out.push(...stancePanelParas('👎 부정 — 필자가 비판·경계·배제·부정', 'B24A38', STANCE_NEG_DOCX));
  out.push(...stancePanelParas('🤔 중립 — 좋다·나쁘다 평가가 없을 때', '6B7280', STANCE_NEU_DOCX,
    '긍정·부정 평가어가 뚜렷이 없고, 판단을 유보하거나 양쪽을 균형 있게 보여주면 중립이다(한쪽으로 몰지 않음).'));
  out.push(new Paragraph({ spacing: { before: 120, after: 30 }, children: [new TextRun({ text: '🔄 ± 방향을 뒤집는 신호 — 놓치면 정반대로 읽는다(평가원 오답 단골 ‘반대구조’)', bold: true, size: 20, color: 'C77A17', font: S.FONT })] }));
  out.push(B.bullet('부정·결여·분리: not·no·never·no longer·hardly·rarely·by no means·free from·absent from·immune to·independent of·apart from·far from·cease·stop'));
  out.push(B.bullet('전환 예: does not shrink=＋expands · free from bias=＋객관적 · immune to=−영향 안 받음 · not necessarily=약화'));
  out.push(B.p('문장 뜻을 다 몰라도 핵심어의 ± 방향만 잡으면 요지·함축·정답 선지가 보인다.'));
  out.push(B.pageBreak());
  return out;
}

// 지문 끝 답지 — 문장별 모범 해석(끊어읽기) + 모범 캐치
// 답지 맨 위: 이 지문을 관통하는 비유 하나(쉬운 예시의 통일성)
function analogyBannerParas(analogy) {
  if (!analogy || !analogy.name) return [];
  const ic = analogy.ic || '💡';
  return [
    B.makeBox('FBF3E0', 'F0D9A8', [
      new Paragraph({
        children: [
          new TextRun({ text: `${ic} 이 지문의 비유 — ‘${analogy.name}’  `, bold: true, size: 19, color: 'B07A1C', font: S.FONT }),
          new TextRun({ text: analogy.desc || '', size: 17, color: '6A4D12', font: S.FONT }),
        ],
      }),
    ]),
    B.spacer(),
  ];
}
// '이 정도는 캐치' 답지 = 필자가 하고 싶은 말(say) + 쉬운 예시(ex, 지문 공통 비유)
function catchAnswerParas(say, ex) {
  if (!say && !ex) return [];
  const kids = [
    new Paragraph({
      spacing: { after: say ? 20 : 0 },
      children: [
        new TextRun({ text: '✅ 이 정도는 캐치!  ', bold: true, size: 16, color: '0C3F26', font: S.FONT }),
        new TextRun({ text: '— 필자가 이 문장으로 하고 싶은 말', size: 13, color: '5F6B64', font: S.FONT }),
      ],
    }),
  ];
  if (say) kids.push(new Paragraph({ spacing: { after: ex ? 40 : 0 }, children: [new TextRun({ text: say, size: 15, color: '1C2620', font: S.FONT })] }));
  if (ex) {
    kids.push(new Paragraph({
      shading: { type: ShadingType.CLEAR, fill: 'FBF3E0' }, spacing: { before: 10 },
      children: [
        new TextRun({ text: '💡 쉬운 예시  ', bold: true, size: 14, color: 'B07A1C', font: S.FONT }),
        new TextRun({ text: ex, size: 14, color: '6A4D12', font: S.FONT }),
      ],
    }));
  }
  return [B.makeBox('E6F1EA', 'BAD5C2', kids), B.spacer()];
}
// 답지 헤더 영어에 끊어읽기(/) 직접 표시 (조각이 원문을 못 덮으면 원문 그대로)
function headChunkedEn(s) {
  const chunks = (s.chunks || []).filter((c) => Array.isArray(c) && c[0]);
  if (chunks.length >= 2) {
    const joined = chunks.map((c) => c[0]).join(' ');
    const hasEllipsis = chunks.some((c) => /…|\.\.\./.test(c[0]));
    const nrm = (x) => String(x).toLowerCase().replace(/[^a-z0-9]/g, '');
    if (!hasEllipsis && nrm(joined).length >= nrm(s.en || '').length * 0.85) {
      return chunks.map((c) => c[0]).join(' / ');
    }
  }
  return s.en || '';
}
// 답지 한글 끊어읽기(영어는 헤더에 있으니 한글만)
function korChunkBoxParas(chunks) {
  const list = (chunks || []).filter((c) => Array.isArray(c) && c[1]);
  if (!list.length) return [];
  const ko = list.map((c) => c[1]).join('  /  ');
  return [
    B.makeBox('F2F4F5', '8A8F98', [
      new Paragraph({
        children: [
          new TextRun({ text: '한글  ', bold: true, size: 16, color: '8A8F98', font: S.FONT }),
          new TextRun({ text: ko, size: 19, color: '333333', font: S.FONT }),
        ],
      }),
    ]),
    B.spacer(),
  ];
}
function passageAnswerParas(p) {
  const out = [B.pageBreak(), B.h1('답지 — 끊어읽기 · 캐치'), B.p('위에서 직접 푼 걸 여기서 맞춰보자 (영어 문장에 / 로 끊어읽기).')];
  out.push(...analogyBannerParas(p.analogy));
  (p.sentences || []).forEach((s, i) => {
    // src(문항번호)가 짧은 라벨일 때만 표시. AI 가 문장 전체를 넣는 경우는 생략.
    const tag = s.src && String(s.src).length <= 10 ? `  [${s.src}]` : '';
    out.push(B.h3(`${i + 1}. ${headChunkedEn(s)}${tag}`));
    out.push(...korChunkBoxParas(s.chunks));
    out.push(...catchAnswerParas(s.catch, s.ex));
  });
  return out;
}

// 🧩 글의 구조 고르기 (해석 전에) — 체크 목록
const STRUCTURE_TYPES = [
  '통념 → 반박(반전)', '주장 → 근거·예시', '문제 → 해결(방안)',
  '비교 · 대조', '시간 · 순서(나열)', '예시 → 일반화(결론)',
];
// 재진술 '사슬' 도우미 — html.js 와 동일 규칙(핵심어 하나가 A→A′→A″ 로 반복, links 2개 이상만)
function validChains(p) {
  return (Array.isArray(p.paraphrases) ? p.paraphrases : [])
    .map((ch) => ({
      keyword: ch && ch.keyword ? String(ch.keyword) : '',
      why: ch && ch.why ? String(ch.why) : '',
      links: (ch && Array.isArray(ch.links) ? ch.links : [])
        .filter((v) => v && String(v).trim()).map((v) => String(v).trim()),
    }))
    .filter((ch) => ch.links.length >= 2);
}

// 해석 전 예측 4코너(소재·필자주장·구조·재진술) — 직접 쓰는 체크 목록
function predictChoiceParas(p) {
  const out = [];
  out.push(B.p('통째로 읽고, 해석 들어가기 전에 먼저 예측해봐! (정답은 지문 끝)', { bold: true }));
  out.push(B.p('🔎 소재 — 이 지문, 뭐에 관한 글이야? (한 줄):  ______________________________________'));
  out.push(B.p('🗣️ 필자 주장 — 긍정 · 부정 · 중립?   ☐ 긍정적   ☐ 부정적·비판적   ☐ 중립적   (평가어·마지막 문장으로 판단)'));
  out.push(B.p('     · 긍정: 좋다·이롭다 / should · thanks to · valuable 같은 칭찬·권장', { color: '14603A' }));
  out.push(B.p('     · 부정: 문제·해롭다 / But·However 뒤집기 · overlook·fail · should not 같은 비판·경고', { color: 'B24A38' }));
  out.push(B.p('     · 중립: 사실 설명·양쪽 비교만, 편들지 않음', { color: '6B7280' }));
  out.push(B.p('🧩 이 글, 어떤 구조야? (하나 ✓ · 앞 “글의 구조” 페이지 참고)'));
  STRUCTURE_TYPES.forEach((t) => out.push(new Paragraph({
    spacing: { after: 30 }, indent: { left: 240 },
    children: [new TextRun({ text: `☐  ${t}`, size: 21, font: S.FONT })],
  })));
  out.push(B.p('     근거(전환·연결 표현이나 문장 번호): ____________________________'));
  const chains = validChains(p);
  if (chains.length) {
    out.push(B.p('🔗 재진술 사슬 찾기 — 첫 표현이 지문에서 같은 뜻으로 어떻게 다시 나오는지 순서대로 찾아 써봐 (정답은 지문 끝):'));
    chains.forEach((ch) => out.push(...chainQuestionParas(ch)));
  }
  return out;
}
// 재진술 사슬 문제: [핵심어] 첫 표현 A → ______ → ______ (학생이 지문에서 찾아 씀)
function chainQuestionParas(ch) {
  const out = [];
  if (ch.keyword) {
    out.push(new Paragraph({
      spacing: { before: 40, after: 15 }, indent: { left: 200 },
      children: [new TextRun({ text: `[ ${ch.keyword} ]`, bold: true, size: 20, color: GRAM, font: S.FONT })],
    }));
  }
  const kids = [new TextRun({ text: ch.links[0], bold: true, size: 21, font: S.FONT })];
  ch.links.slice(1).forEach(() => {
    kids.push(new TextRun({ text: '  →  ', bold: true, size: 21, color: GRAM, font: S.FONT }));
    kids.push(new TextRun({ text: '________________', size: 21, font: S.FONT }));
  });
  out.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 240 }, children: kids }));
  return out;
}
// 지문 끝: 해석 전 예측 정답 공개 — 별도 페이지 + 항목별 카드(가독성↑)
const GRAM = '5E4C9E'; const GRAMBG = 'F0EDF9'; const GRAMLINE = 'DDD4F2';
function revealItem(label, main, why) {
  const kids = [new Paragraph({
    spacing: { after: why ? 50 : 0 },
    children: [
      new TextRun({ text: `${label}  `, bold: true, size: 22, color: GRAM, font: S.FONT }),
      new TextRun({ text: main, bold: true, size: 22, font: S.FONT }),
    ],
  })];
  if (why) kids.push(new Paragraph({ children: [new TextRun({ text: why, size: 20, color: '4B4B57', font: S.FONT })] }));
  return B.makeBox(GRAMBG, GRAMLINE, kids);
}
function predictRevealParas(p) {
  const chains = validChains(p);
  const out = [B.pageBreak(), B.h2('✅ 해석 전 예측 — 정답 확인  ·  소재 · 필자 주장 · 글의 구조 · 재진술')];
  if (p.topic) { out.push(revealItem('🔎 소재', p.topic, '')); out.push(B.spacer()); }
  if (p.claim && p.claim.stance) { out.push(revealItem('🗣️ 필자 주장', p.claim.stance, p.claim.why || '')); out.push(B.spacer()); }
  if (p.structure && p.structure.type) { out.push(revealItem('🧩 글의 구조', p.structure.type, p.structure.why || '')); out.push(B.spacer()); }
  if (chains.length) {
    const kids = [new Paragraph({
      spacing: { after: 70 },
      children: [new TextRun({ text: '🔗 재진술 사슬 (같은 말)', bold: true, size: 22, color: GRAM, font: S.FONT })],
    })];
    chains.forEach((ch) => {
      if (ch.keyword) kids.push(new Paragraph({
        spacing: { before: 80, after: 30 },
        children: [new TextRun({ text: `📂 ${ch.keyword}`, bold: true, size: 20, color: GRAM, font: S.FONT })],
      }));
      const flow = [];
      ch.links.forEach((l, i) => {
        if (i) flow.push(new TextRun({ text: '  →  ', bold: true, size: 20, color: GRAM, font: S.FONT }));
        flow.push(new TextRun({ text: l, bold: i === 0, size: 20, color: i === 0 ? '000000' : '4B4B57', font: S.FONT }));
      });
      kids.push(new Paragraph({ spacing: { after: ch.why ? 20 : 50 }, children: flow }));
      if (ch.why) kids.push(new Paragraph({
        spacing: { after: 60 }, indent: { left: 200 },
        children: [
          new TextRun({ text: '↳ 변주  ', bold: true, size: 18, color: GRAM, font: S.FONT }),
          new TextRun({ text: ch.why, size: 18, color: '5B5B66', font: S.FONT }),
        ],
      }));
    });
    out.push(B.makeBox(GRAMBG, GRAMLINE, kids)); out.push(B.spacer());
  }
  return out;
}

function passageParagraphs(p, idx) {
  const out = [B.h1(p.title || `지문 ${idx + 1}`)];
  out.push(B.p(`출처: ${p.source || '지문'}`, { italics: true, color: '666666' }));
  out.push(B.h2('지문 통째로 읽기'));
  out.push(new Paragraph({
    spacing: { after: 40 },
    children: [
      new TextRun({ text: '🖍️ 형광펜 — ', bold: true, size: 15, color: '0C3F26', font: S.FONT }),
      new TextRun({ text: '연결·신호', size: 15, highlight: 'yellow', font: S.FONT }),
      new TextRun({ text: ' / ', size: 15, color: '888888', font: S.FONT }),
      new TextRun({ text: '＋어휘', size: 15, color: '0C3F26', shading: { type: ShadingType.CLEAR, fill: 'D9EFE1' }, font: S.FONT }),
      new TextRun({ text: ' / ', size: 15, color: '888888', font: S.FONT }),
      new TextRun({ text: '−어휘', size: 15, color: 'B24A38', shading: { type: ShadingType.CLEAR, fill: 'FBE0DB' }, font: S.FONT }),
      new TextRun({ text: '  (PART 0 신호가 지문에 나오면 자동 표시)', size: 13, color: '9AA0A6', font: S.FONT }),
    ],
  }));
  out.push(new Paragraph({
    spacing: { after: 160 },
    children: (p.sentences || []).flatMap((s, i) => [
      new TextRun({ text: `${i + 1} `, bold: true, color: S.NAVY, size: 20, font: S.FONT }),
      ...hlRunsDocx(`${s.en} `),
    ]),
  }));
  out.push(B.h2('해석 전 예측 — 소재·주장·구조·재진술'));
  out.push(...predictChoiceParas(p));
  out.push(B.pageBreak());
  out.push(B.h2('한 문장씩 직접 풀기'));
  (p.sentences || []).forEach((s, i) => out.push(...passageSentenceParas(s, i + 1)));
  // 지문 끝: 답지(해석·캐치) → 해석 전 예측 정답 → 지문 전체 요지
  out.push(...passageAnswerParas(p));
  out.push(...predictRevealParas(p));
  if (p.catch) { out.push(B.h2('이 지문, 이 정도는 캐치! (전체 요지)')); out.push(...B.catchBox(p.catch)); }
  out.push(B.pageBreak());
  return out;
}

function passageCoverParagraphs(meta = {}) {
  const TEAL = '14603A'; const TEALD = '0C3F26'; const GRAY = '6B7280';
  const center = (children, after, before) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after, before }, children });
  const gray = (t, extra) => new TextRun({ text: t, color: GRAY, font: S.FONT, ...extra });
  const hl = (t, size) => new TextRun({ text: t, bold: true, color: TEAL, font: S.FONT, size });
  return [
    center([new TextRun({ text: '수능·평가원 독해 훈련', bold: true, size: 20, color: TEALD, font: S.FONT })], 200, 700),
    center([new TextRun({ text: '필 생 보', bold: true, size: 108, color: TEAL, font: S.FONT })], 60),
    // 필·생·보 = 필자의 생각이 보이는 (앞 글자 강조)
    center([hl('필', 26), gray('자의 ', { size: 26, bold: true }), hl('생', 26), gray('각이 ', { size: 26, bold: true }), hl('보', 26), gray('이는', { size: 26, bold: true })], 140),
    center([new TextRun({ text: '영 어 독 해', bold: true, size: 44, color: S.NAVY, font: S.FONT })], 160),
    center([
      new TextRun({ text: '소재', bold: true, size: 22, color: TEALD, font: S.FONT }),
      new TextRun({ text: '  ›  ', bold: true, size: 22, color: TEAL, font: S.FONT }),
      new TextRun({ text: '필자 주장', bold: true, size: 22, color: TEALD, font: S.FONT }),
      new TextRun({ text: '  ›  ', bold: true, size: 22, color: TEAL, font: S.FONT }),
      new TextRun({ text: '글 구조', bold: true, size: 22, color: TEALD, font: S.FONT }),
      new TextRun({ text: '  ›  ', bold: true, size: 22, color: TEAL, font: S.FONT }),
      new TextRun({ text: '재진술', bold: true, size: 22, color: TEALD, font: S.FONT }),
    ], 120),
    B.pageBreak(),
  ];
}

// 목차 + 사용법 페이지(표지 다음)
const TOC_GUIDE = [
  ['끊어읽기 원리', '어디서 끊을까 — 5가지 신호'],
  ['독해 태도', '점수는 태도에서 나온다'],
  ['완급조절', 'OLD / MAIN / SUPPORT'],
  ['추론 — 어순·구두점', '모르는 건 추론한다'],
  ['연결사 지도', 'Switching vs Contrast'],
  ['재진술', '같은 말을 알아채기'],
  ['재진술 5변환·함정', '정답이 만들어지는 법'],
  ['글의 구조', '6가지 글의 틀'],
  ['필자 입장 신호', '긍정·부정(±) 어휘'],
  ['논리관계 구문 ①', '인과 · 등호'],
  ['논리관계 구문 ②', '대조 · 비교'],
  ['형광펜 신호 사전', '무엇을 읽고 버릴까'],
];
function passageTocParagraphs(passages) {
  const TEAL = '14603A'; const GRAM = '5E4C9E';
  const out = [B.h1('목차 · Contents')];
  out.push(B.p('먼저 독해 원리를 익히고 → 지문으로 훈련하는 순서다.', { color: '666666' }));
  // 매거진 인덱스 스타일: 큰 번호 + 굵은 제목 + 오른쪽 설명 태그
  const mgRow = (numText, name, tag, color) => new Paragraph({
    spacing: { after: 60 }, indent: { left: 100 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      new TextRun({ text: `${numText}   `, bold: true, size: 30, color, font: S.FONT }),
      new TextRun({ text: name, bold: true, size: 22, font: S.FONT }),
      new TextRun({ text: `\t${tag}`, size: 18, color: '888888', font: S.FONT }),
    ],
  });
  out.push(new Paragraph({ spacing: { before: 140, after: 60 }, children: [new TextRun({ text: 'STEP 1 — 먼저 익히는 독해 원리', bold: true, size: 22, color: TEAL, font: S.FONT })] }));
  TOC_GUIDE.forEach(([name, tag], i) => out.push(mgRow(String(i + 1).padStart(2, '0'), name, tag, TEAL)));
  out.push(new Paragraph({ spacing: { before: 200, after: 60 }, children: [new TextRun({ text: `STEP 2 — 지문으로 훈련 · 지문 ${(passages || []).length}편`, bold: true, size: 22, color: GRAM, font: S.FONT })] }));
  (passages || []).forEach((p, i) => out.push(mgRow(String(i + 1), p.title || `지문 ${i + 1}`, p.source || '지문', GRAM)));
  // 사용법
  out.push(new Paragraph({
    spacing: { before: 260, after: 100 }, shading: { type: ShadingType.CLEAR, fill: S.LIGHTGRAY },
    children: [new TextRun({ text: '  📌 쌤이 알려주는 사용법', bold: true, size: 22, color: S.NAVY, font: S.FONT })],
  }));
  out.push(B.bullet('지문마다: ① 통째로 쭉 읽고 → ② 한 문장씩 [어휘·팁·이거조심] 보고 해석과 캐치를 직접 써 → ③ 지문 끝 "답지"에서 해석·캐치 맞춰보고 → ④ "이 지문 이 정도는 캐치"로 전체 요지 확인.'));
  out.push(B.bullet('캐치는 매 문장 한 줄로 줄여 쓰는 연습이야 — 누가/무엇이 → 어쨌다만 남기고 곁가지는 버려.'));
  out.push(B.bullet('목표는 하나 — 소재·필자 주장·글 구조·재진술을 잡아 한 지문을 통째로 읽어내는 거야.'));
  out.push(B.pageBreak());
  return out;
}

function buildPassageDocument(passages, meta = {}) {
  const children = [
    ...passageCoverParagraphs(meta),
    ...passageTocParagraphs(passages),
    ...principlePageParas(),      // 끊어읽기 원리
    ...principlesFrontParas(),    // 태도·완급·추론·연결사·재진술·5변환
    ...structureTypesPageParas(), // 글의 구조
    ...stanceTypesPageParas(),    // 필자 입장(± 어휘)
    ...principlesBackParas(),     // 논리관계 ①②·형광펜 신호
    ...passages.flatMap((p, i) => passageParagraphs(p, i)),
  ];
  return new Document({
    styles: { default: { document: { run: { font: S.FONT, size: 22 } } } },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } } },
      children,
    }],
  });
}

// ── 최상위 조립 ──────────────────────────────────────
function buildDocument(rawCategories) {
  const categories = splitWorked(rawCategories);
  const children = [
    ...coverParagraphs(),
    ...categories.flatMap(chapterParagraphs),
    ...answerParagraphs(categories),
  ];

  return new Document({
    styles: { default: { document: { run: { font: S.FONT, size: 22 } } } },
    sections: [{
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } },
      },
      children,
    }],
  });
}

module.exports = {
  buildDocument, splitWorked, coverParagraphs, chapterParagraphs, answerParagraphs,
  buildPassageDocument, passageParagraphs,
};

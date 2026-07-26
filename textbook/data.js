// data.js — 교재 데이터 (명세 §4 스키마)
//
// ⚠️ 샘플/플레이스홀더 안내
//   이 파일의 문장·해석·어휘는 파이프라인이 끝까지 동작하는지 보여 주기 위한
//   "예시(illustrative)" 문장이야. 명세가 말하는 실제 2023학년도 수능 기출 문장이
//   아니라, 각 문법 포인트를 깔끔히 보여 주는 대표 예문으로 채워 놨어.
//   → 선생님의 실제 data.js 를 붙여 주면 이 내용을 그대로 교체하면 돼.
//   → 실제 기출로 채울 때도 아래 스키마/불변식(§4)만 지키면 build 가 그대로 돈다.
//
// 목차 순서 (명세 §2, 확정):
//   ① 수동태 → ② to부정사 → ③ 동명사 → ④ 관계사 → ⑤ 분사 → ⑥ 분사구문
//   ※ 챕터를 추가/재배열하면 title 의 원문자 번호(①~⑥)도 함께 갱신할 것.
//
// 스키마 요약:
//   Category { key, title, intro[], signal[], method:[label,text][],
//              worked:[2], practice:[…] }
//   Sentence { src, en, chunks:[en,kor][], catch, vocab:[word,mean][], steps? }
//     - worked 는 steps 있음, practice 는 steps 없음(학생이 직접 채움)
//     - chunks 를 순서대로 이어 붙인 한글이 정답이 됨 → 이어 읽어 자연스럽게 작성

const categories = [
  // ─────────────────────────────────────────── ① 수동태
  {
    key: '수동태',
    title: "① 수동태 — 주어가 '당하는' 문장",
    intro: [
      "자, 수동태는 '주어가 직접 하는 게 아니라 당하는' 문장이야.",
      "'나는 케이크를 만들었다' 는 내가 한 거지만, '케이크가 만들어졌다' 는 케이크가 당한 거지?",
      "이렇게 주어가 뭔가를 '당하는' 느낌이면 수동태라고 생각하면 돼.",
    ],
    signal: [
      "be동사(is/are/was/were …) + 동사의 p.p.(과거분사) 가 나란히 있음",
      "p.p. 뒤에 'by + 사람/사물' 이 자주 따라옴 (누구에 의해)",
      "해석했을 때 '~되다 / ~당하다' 가 자연스러움",
    ],
    method: [
      ['be동사부터 찾기', 'is/was/were 같은 be동사와 그 뒤 p.p. 를 한 덩어리로 묶어.'],
      ["'~되다'로 뒤집기", "'했다' 가 아니라 '~되었다/당했다' 로 읽어."],
      ["by 는 '~에 의해'", 'by 가 있으면 누가 했는지 알려주는 거니까 괄호로 빼서 읽어.'],
    ],
    worked: [
      {
        src: '예문',
        en: 'The bridge was built by local workers in 1920.',
        chunks: [
          ['The bridge', '그 다리는'],
          ['was built', '지어졌다'],
          ['by local workers', '지역 일꾼들에 의해'],
          ['in 1920.', '1920년에'],
        ],
        catch: "was + p.p.(built) 가 보이면 주어가 '직접 한 게 아니라 당한 거' 라는 거예요! 다리가 스스로 지은 게 아니라 지어진 거야.",
        vocab: [['build (built)', '짓다'], ['local', '지역의'], ['worker', '일꾼, 노동자']],
        steps: [
          ['뼈대(주어+동사)', "The bridge / was built — 다리가 '지어진' 거야(당함)"],
          ['괄호(수식어)', 'by local workers (누가), in 1920 (언제)'],
        ],
      },
      {
        src: '예문',
        en: 'These results were not expected by the researchers.',
        chunks: [
          ['These results', '이 결과들은'],
          ['were not expected', '예상되지 않았다'],
          ['by the researchers.', '연구자들에게'],
        ],
        catch: "were + not + p.p. 처럼 not 이 중간에 껴도 뼈대는 그대로 'be + p.p.' 야. '~되지 않았다' 로 읽자!",
        vocab: [['result', '결과'], ['expect', '예상하다'], ['researcher', '연구자']],
        steps: [
          ['뼈대(주어+동사)', "These results / were not expected — 결과가 '예상당한' 게 아니라 안 됐어"],
          ['괄호(수식어)', 'by the researchers (누구에게)'],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'The old house has been sold to a young couple.',
        chunks: [
          ['The old house', '그 오래된 집은'],
          ['has been sold', '팔렸다'],
          ['to a young couple.', '젊은 부부에게'],
        ],
        catch: "has been + p.p. 는 '완료 + 수동' 이 합쳐진 모양이야. 그래도 핵심은 p.p. 라 '팔렸다' 로 읽으면 돼!",
        vocab: [['sell (sold)', '팔다'], ['couple', '부부, 커플']],
      },
      {
        src: '예문',
        en: 'Many trees are planted along the river every spring.',
        chunks: [
          ['Many trees', '많은 나무들이'],
          ['are planted', '심어진다'],
          ['along the river', '강을 따라'],
          ['every spring.', '봄마다'],
        ],
        catch: "are planted — '심는다' 가 아니라 '심어진다' 야. 나무는 스스로 못 심으니까 당하는 쪽이지!",
        vocab: [['plant', '심다'], ['along', '~을 따라']],
      },
    ],
  },

  // ─────────────────────────────────────────── ② to부정사
  {
    key: 'to부정사',
    title: "② to부정사 — 'to + 동사' 가 만드는 덩어리",
    intro: [
      "'to + 동사원형' 을 to부정사라고 불러.",
      "얘는 상황에 따라 '~하는 것 / ~하려고 / ~할' 세 가지 뜻으로 변신해.",
      '겁먹지 말고, 뒤 문맥 보고 셋 중 하나 골라 읽으면 돼!',
    ],
    signal: [
      "'to' 바로 뒤에 '동사원형' 이 옴 (to go, to make …)",
      "'to + 명사' 는 전치사라 to부정사가 아님 — 뒤가 동사인지 명사인지 꼭 확인",
      '문장 앞/뒤, be동사 뒤 등 위치가 다양함',
    ],
    method: [
      ['뒤가 동사인지 확인', "to 뒤가 동사원형이면 to부정사, 명사면 전치사 '~로/에게'."],
      ['세 가지 뜻 대입', "'~하는 것 / ~하려고 / ~할' 중 문맥에 맞는 걸로."],
      ["앞 명사 있으면 '~할'", "바로 앞에 명사가 있으면 그 명사를 꾸미는 '~할' 로 읽어."],
    ],
    worked: [
      {
        src: '예문',
        en: 'She went to the library to borrow some books.',
        chunks: [
          ['She went', '그녀는 갔다'],
          ['to the library', '도서관에'],
          ['to borrow some books.', '책을 몇 권 빌리려고'],
        ],
        catch: "같은 'to' 라도 뒤에 명사가 오면 '~로(전치사)', 동사가 오면 '~하려고(to부정사)' 야. 뒤를 보고 구분하자!",
        vocab: [['borrow', '빌리다'], ['library', '도서관'], ['some', '몇몇의']],
        steps: [
          ['뼈대(주어+동사)', 'She / went — 그녀가 갔어'],
          ['괄호(수식어)', "to the library (어디로 — 전치사 to) / to borrow some books (왜 갔는지 — to부정사 '~하려고')"],
        ],
      },
      {
        src: '예문',
        en: 'Her goal was to become a doctor.',
        chunks: [
          ['Her goal was', '그녀의 목표는'],
          ['to become a doctor.', '의사가 되는 것이었다'],
        ],
        catch: "be동사 뒤의 'to + 동사' 는 '~하는 것' 이라고 읽으면 딱 맞아. '목표 = 의사가 되는 것' 처럼 등호로 이어져!",
        vocab: [['goal', '목표'], ['become', '되다'], ['doctor', '의사']],
        steps: [
          ['뼈대(주어+동사)', 'Her goal / was — 목표는 ~였다'],
          ['괄호(보충)', "to become a doctor (무엇이었는지 — to부정사 '~하는 것')"],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'He worked hard to pass the exam.',
        chunks: [
          ['He worked hard', '그는 열심히 공부했다'],
          ['to pass the exam.', '시험에 합격하려고'],
        ],
        catch: "문장 뒤에 붙은 'to + 동사' 는 '~하려고(목적)' 로 읽으면 열에 아홉은 맞아!",
        vocab: [['hard', '열심히'], ['pass', '합격하다, 통과하다'], ['exam', '시험']],
      },
      {
        src: '예문',
        en: 'The teacher told us to be quiet.',
        chunks: [
          ['The teacher told us', '선생님은 우리에게 말했다'],
          ['to be quiet.', '조용히 하라고'],
        ],
        catch: "'tell 사람 to 동사' 는 '~에게 ~하라고 말하다' 야. 명령을 전달하는 느낌이지!",
        vocab: [['tell (told)', '말하다'], ['quiet', '조용한']],
      },
    ],
  },

  // ─────────────────────────────────────────── ③ 동명사
  {
    key: '동명사',
    title: "③ 동명사 — '-ing' 가 '~하는 것' 이 될 때",
    intro: [
      "동사 뒤에 '-ing' 를 붙이면 '~하는 것' 이라는 명사처럼 쓸 수 있어. 이걸 동명사라고 해.",
      "'수영하다(swim)' → '수영하는 것(swimming)' 처럼 행동을 '하나의 명사' 로 만든 거야.",
      '그래서 주어·목적어 자리, 전치사 뒤에 올 수 있어.',
    ],
    signal: [
      "'-ing' 형태가 주어·목적어 자리에 있음 (Reading is fun)",
      "전치사(at, of, for, in …) 바로 뒤의 '-ing'",
      'enjoy, finish, keep, mind 같은 동사 뒤의 -ing',
    ],
    method: [
      ["'~하는 것'으로 읽기", "-ing 를 '~하는 것/~하기' 로 바꿔 읽어."],
      ['전치사 뒤는 무조건 -ing', "전치사 뒤에는 동사를 못 써서 -ing 로 바뀐 거야. '~하는 것을' 로."],
      ['진행형과 구분', 'be동사 + -ing(진행형)이 아니면 대개 동명사야.'],
    ],
    worked: [
      {
        src: '예문',
        en: 'Reading books every day improves your vocabulary.',
        chunks: [
          ['Reading books every day', '매일 책을 읽는 것은'],
          ['improves', '향상시킨다'],
          ['your vocabulary.', '네 어휘력을'],
        ],
        catch: "문장 맨 앞의 '-ing' 는 '~하는 것은' 이라고 읽어봐. 여기선 '읽는 것' 자체가 주인공(주어)이야!",
        vocab: [['improve', '향상시키다'], ['vocabulary', '어휘(력)'], ['every day', '매일']],
        steps: [
          ['뼈대(주어+동사)', "Reading books every day / improves — '읽는 것' 이 주어야"],
          ['괄호(목적어)', 'your vocabulary (무엇을)'],
        ],
      },
      {
        src: '예문',
        en: 'She is good at solving difficult problems.',
        chunks: [
          ['She is good at', '그녀는 잘한다'],
          ['solving difficult problems.', '어려운 문제 푸는 것을'],
        ],
        catch: "전치사(at, of, in …) 뒤에는 동사를 못 써서 '-ing' 로 바꿔 써. 'at solving = 푸는 것을' 이야!",
        vocab: [['solve', '풀다, 해결하다'], ['difficult', '어려운'], ['problem', '문제']],
        steps: [
          ['뼈대(주어+동사)', 'She / is good at — 그녀는 ~을 잘해'],
          ['괄호(전치사의 목적어)', 'solving difficult problems (무엇을 잘하는지 — 전치사 at 뒤라 -ing)'],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'Thank you for helping me yesterday.',
        chunks: [
          ['Thank you', '고마워'],
          ['for helping me', '나를 도와줘서'],
          ['yesterday.', '어제'],
        ],
        catch: "'for + -ing' 는 '~해줘서 / ~한 것에 대해' 야. 전치사 for 뒤라서 help 가 helping 이 된 거지!",
        vocab: [['thank', '감사하다'], ['help', '돕다']],
      },
      {
        src: '예문',
        en: 'They enjoy playing soccer on weekends.',
        chunks: [
          ['They enjoy', '그들은 즐긴다'],
          ['playing soccer', '축구 하는 것을'],
          ['on weekends.', '주말마다'],
        ],
        catch: "enjoy 뒤에는 항상 '-ing' 만 와. 'enjoy playing = 하는 것을 즐기다' 로 외워두자!",
        vocab: [['enjoy', '즐기다'], ['weekend', '주말']],
      },
    ],
  },

  // ─────────────────────────────────────────── ④ 관계사
  {
    key: '관계사',
    title: '④ 관계사 — 명사를 뒤에서 꾸며 주는 절',
    intro: [
      "관계사는 '앞에 나온 명사' 를 뒤에서 자세히 꾸며 주는 연결고리야.",
      "who/which/that/where 가 나오면 '아, 앞 명사를 설명하려는구나' 하고 생각하면 돼.",
      '긴 문장도 관계사에서 한 번 끊으면 훨씬 쉬워져!',
    ],
    signal: [
      'who/whom/whose/which/that (사람·사물 꾸밈)',
      'where/when (장소·시간 꾸밈)',
      '관계사 앞에는 꾸밈받는 명사(관계사 앞 명사)가 있음',
    ],
    method: [
      ['관계사에서 끊기', 'who/which/that 이 보이면 거기서 한 번 끊어.'],
      ['앞 명사에 붙여 읽기', "'(어떤 명사?)' 하고 뒤 절을 앞 명사에 붙여 설명으로 읽어."],
      ['길면 풀어 읽기', "'그런데 그건 ~해' 처럼 뒤에서 이어 설명하듯 읽어도 좋아."],
    ],
    worked: [
      {
        src: '예문',
        en: 'The man who lives next door is a famous artist.',
        chunks: [
          ['The man', '그 남자는'],
          ['who lives next door', '(옆집에 사는 사람인데)'],
          ['is a famous artist.', '유명한 예술가야'],
        ],
        catch: "who/which/that 가 보이면 '앞 명사를 꾸며 주는 신호' 야. 'who lives next door' 는 앞의 man 을 설명해 주는 거지!",
        vocab: [['next door', '옆집(에)'], ['famous', '유명한'], ['artist', '예술가']],
        steps: [
          ['뼈대(주어+동사)', 'The man / is a famous artist — 그 남자는 예술가야'],
          ['괄호(수식)', 'who lives next door (어떤 남자? — 관계사 who 가 앞 명사 man 을 꾸밈)'],
        ],
      },
      {
        src: '예문',
        en: 'This is the book that I told you about.',
        chunks: [
          ['This is the book', '이게 바로 그 책이야'],
          ['that I told you about.', '(내가 너한테 말했던 거 있잖아)'],
        ],
        catch: "관계사 뒤에 '주어+동사(I told)' 가 오면 앞 명사를 설명해 주는 거야. 'that I told you about = 내가 말했던 (그 책)' 이지!",
        vocab: [['tell (told)', '말하다'], ['about', '~에 대해']],
        steps: [
          ['뼈대(주어+동사)', 'This / is the book — 이게 그 책이야'],
          ['괄호(수식)', 'that I told you about (어떤 책? — 내가 말했던 그 책, 목적격 관계대명사 that)'],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'I visited the town where my grandmother grew up.',
        chunks: [
          ['I visited the town', '나는 그 마을을 방문했다'],
          ['where my grandmother grew up.', '(우리 할머니가 자란 곳이야)'],
        ],
        catch: "where 는 '장소' 를 꾸며 주는 신호야. 'where ~ grew up = (그곳에서) ~가 자란' 이라고 앞의 장소에 붙여 읽자!",
        vocab: [['visit', '방문하다'], ['grow up (grew)', '자라다'], ['town', '마을']],
      },
      {
        src: '예문',
        en: 'She is the teacher who helped me the most.',
        chunks: [
          ['She is the teacher', '그녀는 그 선생님이야'],
          ['who helped me the most.', '(나를 가장 많이 도와준 분이지)'],
        ],
        catch: "사람 뒤의 who 는 '어떤 사람?' 을 설명해. '나를 가장 많이 도와준' 선생님이라는 거야!",
        vocab: [['the most', '가장 많이'], ['help', '돕다'], ['teacher', '선생님']],
      },
    ],
  },

  // ─────────────────────────────────────────── ⑤ 분사
  {
    key: '분사',
    title: "⑤ 분사 — 명사를 꾸미는 '-ing / -ed'",
    intro: [
      "분사는 동사를 '형용사처럼' 만들어서 명사를 꾸미는 거야.",
      "'-ing' 는 '~하는(능동)', '-ed(p.p.)' 는 '~된/당한(수동)' 이라는 뜻이야.",
      "명사 바로 뒤에 붙어서 '어떤 명사인지' 를 설명해 줘.",
    ],
    signal: [
      "명사 바로 뒤의 '-ing' 또는 '-ed(p.p.)'",
      "'-ing' 는 명사가 직접 하는 것(능동), '-ed' 는 명사가 당하는 것(수동)",
      '관계사(who is …)가 생략된 자리라고 봐도 됨',
    ],
    method: [
      ['명사 뒤 분사 찾기', '명사 뒤에 -ing/-ed 가 붙어 꾸미는지 확인.'],
      ['능동/수동 구분', "직접 하면 -ing '~하는', 당하면 -ed '~된' 으로."],
      ['앞 명사에 붙이기', "'(어떤 명사?) ~하는/~된' 으로 앞 명사에 붙여 읽어."],
    ],
    worked: [
      {
        src: '예문',
        en: 'The boy sitting on the bench is my brother.',
        chunks: [
          ['The boy', '그 소년은'],
          ['sitting on the bench', '벤치에 앉아 있는데'],
          ['is my brother.', '내 동생이야'],
        ],
        catch: "명사 뒤의 '-ing' 는 '~하고 있는' 으로 앞 명사를 꾸며. 'the boy sitting = 앉아 있는 소년' 이야!",
        vocab: [['sit', '앉다'], ['bench', '벤치'], ['brother', '형제, 남동생']],
        steps: [
          ['뼈대(주어+동사)', 'The boy / is my brother — 그 소년은 내 동생이야'],
          ['괄호(수식)', "sitting on the bench (어떤 소년? — '앉아 있는', 능동이라 -ing)"],
        ],
      },
      {
        src: '예문',
        en: 'The letter written in French was hard to read.',
        chunks: [
          ['The letter', '그 편지는'],
          ['written in French', '프랑스어로 쓰여 있어서'],
          ['was hard to read.', '읽기 어려웠다'],
        ],
        catch: "'-ed(p.p.)' 로 꾸미면 '~된, ~당한' 이야. 편지는 스스로 못 쓰니까 'written = 쓰여진' 이지! -ing 랑 반대야.",
        vocab: [['letter', '편지'], ['written (write)', '쓰인'], ['French', '프랑스어']],
        steps: [
          ['뼈대(주어+동사)', 'The letter / was hard to read — 그 편지는 읽기 어려웠어'],
          ['괄호(수식)', "written in French (어떤 편지? — '쓰여진', 당하는 거라 -ed/p.p.)"],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'Look at the dog running toward us.',
        chunks: [
          ['Look at the dog', '저 개를 봐'],
          ['running toward us.', '(우리 쪽으로 달려오고 있잖아)'],
        ],
        catch: "'the dog running = 달려오는 개'. 개가 직접 달리니까 능동, 그래서 -ing 야!",
        vocab: [['look at', '~을 보다'], ['run toward', '~쪽으로 달리다']],
      },
      {
        src: '예문',
        en: 'I found a wallet dropped on the street.',
        chunks: [
          ['I found a wallet', '나는 지갑을 발견했다'],
          ['dropped on the street.', '(길에 떨어져 있던 거야)'],
        ],
        catch: "'dropped = 떨어뜨려진' 이야. 지갑은 스스로 못 떨어지고 당한 거니까 -ed(p.p.) 를 쓴 거지!",
        vocab: [['find (found)', '발견하다, 찾다'], ['wallet', '지갑'], ['drop', '떨어뜨리다']],
      },
    ],
  },

  // ─────────────────────────────────────────── ⑥ 분사구문
  {
    key: '분사구문',
    title: "⑥ 분사구문 — '-ing' 로 시작하는 부가 설명",
    intro: [
      "분사구문은 문장 앞이나 뒤에 '-ing …, ' 형태로 붙어서 상황을 설명해 주는 거야.",
      "'~하면서 / ~해서 / ~하다가' 같은 배경 정보를 툭 던져 주는 느낌이야.",
      "문법용어로 외울 필요 없이, '앞의 -ing 덩어리는 상황 설명이구나' 하면 돼.",
    ],
    signal: [
      "문장 맨 앞의 '-ing …, 주어 + 동사' 구조",
      '쉼표(,)로 본문과 분리되어 있음',
      "'Not -ing' 이면 '~하지 않아서'",
    ],
    method: [
      ['-ing 덩어리 끊기', '맨 앞 -ing 부터 쉼표까지 한 덩어리로 끊어.'],
      ["'~하면서/해서'로 읽기", "시간·이유·상황에 맞게 '~하면서 / ~해서 / ~하다가' 로."],
      ['주어는 뒤 문장과 같음', '분사구문의 주어는 보통 뒤 문장 주어와 같아 — 그대로 이어 읽어.'],
    ],
    worked: [
      {
        src: '예문',
        en: 'Walking along the beach, she found a beautiful shell.',
        chunks: [
          ['Walking along the beach,', '해변을 걷다가,'],
          ['she found', '그녀는 발견했다'],
          ['a beautiful shell.', '예쁜 조개껍데기를'],
        ],
        catch: "문장 맨 앞의 '-ing, 주어…' 는 '~하면서 / ~하다가' 로 읽어. 뒤 문장의 배경 상황을 깔아주는 거야!",
        vocab: [['walk along', '~을 따라 걷다'], ['beach', '해변'], ['shell', '조개껍데기']],
        steps: [
          ['뼈대(주어+동사)', 'she / found — 그녀가 발견했어'],
          ['괄호(~하면서/하다가)', "Walking along the beach (언제·상황 — 분사구문 '걷다가')"],
        ],
      },
      {
        src: '예문',
        en: 'Feeling tired, he decided to take a short break.',
        chunks: [
          ['Feeling tired,', '피곤했기 때문에,'],
          ['he decided', '그는 결심했다'],
          ['to take a short break.', '잠깐 쉬기로'],
        ],
        catch: "'-ing' 로 시작하는 분사구문은 '~해서 / ~하면서' 로 이유·상황을 나타내. 'Feeling tired = 피곤해서' 처럼!",
        vocab: [['feel tired', '피곤함을 느끼다'], ['decide', '결심하다'], ['take a break', '쉬다, 휴식하다']],
        steps: [
          ['뼈대(주어+동사)', 'he / decided — 그는 결심했어'],
          ['괄호(이유/상황)', "Feeling tired (왜? — 분사구문 '피곤해서')"],
          ['추가(to부정사)', 'to take a short break (무엇을 결심했는지)'],
        ],
      },
    ],
    practice: [
      {
        src: '예문',
        en: 'Opening the door, I saw a small cat.',
        chunks: [
          ['Opening the door,', '문을 열자,'],
          ['I saw a small cat.', '나는 작은 고양이를 봤다'],
        ],
        catch: "'Opening the door = 문을 열자/열면서'. 맨 앞 -ing 는 뒤 일이 일어난 상황을 알려줘!",
        vocab: [['open', '열다'], ['see (saw)', '보다']],
      },
      {
        src: '예문',
        en: 'Not knowing what to say, she remained silent.',
        chunks: [
          ['Not knowing what to say,', '무슨 말을 해야 할지 몰라서,'],
          ['she remained silent.', '그녀는 말없이 있었다'],
        ],
        catch: "분사구문 앞에 'Not' 이 붙으면 '~하지 않아서' 야. 'Not knowing = 몰라서' 로 읽자!",
        vocab: [['know what to say', '무슨 말을 할지 알다'], ['remain', '(계속) ~인 채로 있다'], ['silent', '조용한, 말없는']],
      },
    ],
  },
];

module.exports = categories;

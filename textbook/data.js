// data.js — 교재 데이터 (명세 §4 스키마)
//
// 목차 순서 (명세 §2):
//   ① 전치사구 → ② 수동태 → ③ to부정사 → ④ 동명사 → ⑤ 관계사 → ⑥ 분사 → ⑦ 분사구문
//   ※ 챕터를 추가/재배열하면 title 의 원문자 번호(①~⑦)도 함께 갱신할 것.
//
// 자료 출처: 2023학년도 수능(② 수동태 ~ ⑦ 분사구문) + 2024년 9월 평가원 모의평가
//            WORKBOOK 0(① 전치사구, 고3) 지문.
//
// 스키마 요약:
//   Category { key, title, intro[], signal[], method:[label,text][],
//              worked:[…], practice:[…] }
//   Sentence { src, en, chunks:[en,kor][], catch, vocab:[word,mean][], steps? }
//
// ※ worked 에는 2문장을 초과해 넣어도 된다. build_v4.js 가 각 챕터의
//   worked 를 앞에서 2문장만 "같이 풀어보기" 로 쓰고, 나머지는 steps 를 떼서
//   "혼자 풀어보기(practice)" 로 자동 이동시킨다(명세 §4 불변식은 빌드 결과 기준).
//   → 따라서 데이터에는 worked 를 최소 2개 이상 넣어 두면 된다.

const categories = [
  {
    // 전치사구 챕터 예문 출처: 2024년 9월 한국교육과정평가원 모의평가(고3) WORKBOOK 0
    //   (20·26·32번 지문). 나머지 6챕터는 2023학년도 수능 기반.
    "key": "전치사구",
    "title": "① 전치사구 — '전치사 + 명사' 덩어리로 읽기",
    "intro": [
      "전치사(in, on, of, with, for, by, about, to …)가 나오면, 그 뒤 명사까지 한 덩어리로 묶어서 읽는 거야. 이게 '전치사구'야.",
      "이 덩어리는 두 가지 일을 해 — ① 바로 앞 명사를 꾸미거나(어떤 명사?), ② 문장 전체에 '언제·어디서·어떻게·왜'를 더해줘.",
      "단어는 아는데 문장이 길어 보이는 이유가 바로 이 전치사구가 여러 개 붙어서야. 덩어리로 묶으면 확 짧아져!"
    ],
    "signal": [
      "in / on / at / of / with / for / by / about / to / from / through … 같은 전치사가 보인다.",
      "전치사 바로 뒤에는 (동사가 아니라) 명사·대명사·-ing가 온다.",
      "전치사구가 명사 바로 뒤에 붙으면 그 명사를 꾸미고(형용사 역할), 그 외엔 대개 문장을 꾸민다(부사 역할)."
    ],
    "method": [
      [
        "1단계",
        "전치사부터 그 뒤 명사 끝까지를 한 덩어리로 묶는다."
      ],
      [
        "2단계",
        "덩어리를 '~에서 / ~로 / ~에 대해 / ~와 함께'처럼 통째로 해석한다."
      ],
      [
        "3단계",
        "그 덩어리가 앞 명사를 꾸미는지(어떤 명사?), 문장을 꾸미는지(언제·어디서) 판단한다."
      ]
    ],
    "worked": [
      {
        "src": "26",
        "en": "He went to the United States in 1937, and about a decade later, he started teaching visual design at the Massachusetts Institute of Technology (MIT).",
        "chunks": [
          [
            "He went",
            "그는 갔다"
          ],
          [
            "to the United States",
            "미국으로"
          ],
          [
            "in 1937,",
            "1937년에,"
          ],
          [
            "and about a decade later,",
            "그리고 약 10년 후,"
          ],
          [
            "he started teaching visual design",
            "그는 시각 디자인을 가르치기 시작했다"
          ],
          [
            "at the Massachusetts Institute of Technology (MIT).",
            "매사추세츠 공과대학(MIT)에서"
          ]
        ],
        "catch": "그는 1937년에 미국으로 가서, 약 10년 뒤 MIT에서 시각 디자인을 가르치기 시작했다는 거예요!",
        "vocab": [
          [
            "go to",
            "~로 가다"
          ],
          [
            "a decade",
            "10년"
          ],
          [
            "institute",
            "(전문)대학, 연구소"
          ]
        ],
        "steps": [
          [
            "덩어리 묶기",
            "to the United States(미국으로) / in 1937(1937년에) / at MIT(MIT에서) — 전치사+명사를 각각 한 덩어리로"
          ],
          [
            "역할",
            "모두 '어디로/언제/어디서'를 알려주는 부사 역할. 뼈대는 He went ~ he started teaching ~"
          ]
        ]
      },
      {
        "src": "20",
        "en": "One of the greatest threats to the accumulation of knowledge can now be found on social media platforms.",
        "chunks": [
          [
            "One of the greatest threats",
            "가장 큰 위협 중 하나가"
          ],
          [
            "to the accumulation of knowledge",
            "(지식 축적에 대한 위협인데)"
          ],
          [
            "can now be found",
            "이제 발견될 수 있다"
          ],
          [
            "on social media platforms.",
            "소셜 미디어 플랫폼에서"
          ]
        ],
        "catch": "지식 축적을 위협하는 가장 큰 것 중 하나를 이제 소셜 미디어에서 볼 수 있다는 거예요!",
        "vocab": [
          [
            "threat",
            "위협"
          ],
          [
            "accumulation",
            "축적"
          ],
          [
            "platform",
            "플랫폼, 기반"
          ]
        ],
        "steps": [
          [
            "덩어리 묶기",
            "to the accumulation of knowledge = '지식의 축적에 대한' / on social media platforms = '소셜 미디어 플랫폼에서'"
          ],
          [
            "역할",
            "앞 to구는 명사 threats를 꾸밈(어떤 위협?), 뒤 on구는 문장에 '어디서'를 더함(부사)"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "26",
        "en": "He studied painting at the Royal Academy of Fine Arts in Budapest, Hungary.",
        "chunks": [
          [
            "He studied painting",
            "그는 회화를 공부했다"
          ],
          [
            "at the Royal Academy of Fine Arts",
            "왕립 미술 아카데미에서"
          ],
          [
            "in Budapest, Hungary.",
            "헝가리 부다페스트에 있는"
          ]
        ],
        "catch": "그는 헝가리 부다페스트에 있는 왕립 미술 아카데미에서 회화를 공부했다는 거예요!",
        "vocab": [
          [
            "academy",
            "아카데미, 학교"
          ],
          [
            "fine arts",
            "미술"
          ],
          [
            "painting",
            "회화, 그림"
          ]
        ]
      },
      {
        "src": "26",
        "en": "In 1995, a museum to house his works was established in Eger, Hungary.",
        "chunks": [
          [
            "In 1995,",
            "1995년에,"
          ],
          [
            "a museum to house his works",
            "그의 작품을 소장하기 위한 박물관이"
          ],
          [
            "was established",
            "설립되었다"
          ],
          [
            "in Eger, Hungary.",
            "헝가리 Eger에"
          ]
        ],
        "catch": "1995년에 그의 작품을 소장할 박물관이 헝가리 Eger에 세워졌다는 거예요!",
        "vocab": [
          [
            "museum",
            "박물관"
          ],
          [
            "house",
            "소장하다, 보관하다"
          ],
          [
            "establish",
            "설립하다"
          ]
        ]
      },
      {
        "src": "32",
        "en": "Take, for example, the installation of fibre-optic communications cable across the African continent.",
        "chunks": [
          [
            "Take, for example,",
            "예를 들어보자,"
          ],
          [
            "the installation of fibre-optic communications cable",
            "광섬유 통신 케이블의 설치를"
          ],
          [
            "across the African continent.",
            "아프리카 대륙 전역에 걸친"
          ]
        ],
        "catch": "아프리카 대륙 전역에 광섬유 통신 케이블을 까는 일을 예로 들어보자는 거예요!",
        "vocab": [
          [
            "installation",
            "설치"
          ],
          [
            "cable",
            "케이블"
          ],
          [
            "continent",
            "대륙"
          ]
        ]
      }
    ]
  },
  {
    "key": "수동태",
    "title": "② 수동태 — 주어가 '당하는' 문장",
    "intro": [
      "동사 자리에 'be동사(is/are/was/were/been/being) + p.p.'가 보이면 바로 이거야. 주어가 스스로 하는 게 아니라 '~되다/받다/당하다'라는 뜻이라고 생각하면 돼."
    ],
    "signal": [
      "is / are / was / were / be / been / being 바로 뒤에 p.p.가 있다.",
      "뒤에 'by 누구'가 붙으면 '~에 의해'라는 뜻인데, 자연스럽게 능동으로 바꿔 해석해도 좋다."
    ],
    "method": [
      [
        "기본 해석",
        "주어 + ~되다/~받다/~당하다"
      ],
      [
        "자연스러운 해석",
        "'by 행위자'가 있으면 '행위자가 주어를 ~한다'로 능동처럼 바꿔도 된다."
      ]
    ],
    "worked": [
      {
        "src": "22",
        "en": "Urban delivery vehicles can be adapted to better suit the density of urban distribution, which often involves smaller vehicles such as vans, including bicycles.",
        "chunks": [
          [
            "Urban delivery vehicles",
            "도시의 배달 운송 수단은"
          ],
          [
            "can be adapted",
            "개조될 수 있는데"
          ],
          [
            "to better suit the density of urban distribution,",
            "도시 배치의 밀집 상태에 더 잘 맞도록,"
          ],
          [
            "which often involves smaller vehicles",
            "그런데 거기에는 자주 더 작은 운송 수단을 포함한다"
          ],
          [
            "such as vans, including bicycles.",
            "밴과 같은, 자전거도 포함해서."
          ]
        ],
        "catch": "도시 배달 수단은 도시 상황에 맞게 바뀔 수 있다는 거예요!",
        "vocab": [
          [
            "adapted",
            "개조된"
          ],
          [
            "suit",
            "맞다"
          ],
          [
            "density",
            "밀집"
          ],
          [
            "distribution",
            "배치"
          ]
        ],
        "steps": [
          [
            "분석",
            "can be adapted = 개조될 수 있다 (수단이 스스로 바뀌는 게 아니라 '개조됨을 당함')"
          ]
        ]
      },
      {
        "src": "21",
        "en": "Over time and with rereading, disparate entries, events, and happenstances could be rendered into insights and narratives about the self, and allowed for the formation of subjectivity.",
        "chunks": [
          [
            "Over time and with rereading,",
            "시간이 지남에 따라 그리고 다시 읽음으로써,"
          ],
          [
            "disparate entries, events, and happenstances",
            "이질적인 항목, 사건 및 우연이"
          ],
          [
            "could be rendered into insights and narratives about the self,",
            "자신에 관한 통찰력과 이야기로 만들어질 수 있었으며,"
          ],
          [
            "and allowed for the formation of subjectivity.",
            "주체성의 형성을 가능하게 만들었다."
          ]
        ],
        "catch": "시간이 지나고 다시 읽으면서 일기 내용이 통찰력과 이야기로 바뀔 수 있었다는 거예요!",
        "vocab": [
          [
            "disparate",
            "이질적인"
          ],
          [
            "entries",
            "항목"
          ],
          [
            "happenstances",
            "우연"
          ],
          [
            "rendered",
            "만들어진"
          ]
        ],
        "steps": [
          [
            "분석",
            "could be rendered = 만들어질 수 있었다 (항목들이 '만들어짐을 당함')"
          ]
        ]
      },
      {
        "src": "23",
        "en": "If automobile manufacturers are required to measure and publicize the safety characteristics of cars, potential car purchasers can trade safety concerns against other attributes, such as price and styling.",
        "chunks": [
          [
            "If automobile manufacturers are required",
            "자동차 제조업체가 요구받는다면"
          ],
          [
            "to measure and publicize the safety characteristics of cars,",
            "자동차의 안전 특성을 측정하고 공개하도록,"
          ],
          [
            "potential car purchasers can trade safety concerns",
            "잠재적인 자동차 구매자는 안전에 대한 우려를 맞바꿀 수 있다"
          ],
          [
            "against other attributes,",
            "다른 속성과,"
          ],
          [
            "such as price and styling.",
            "가격과 스타일 같은."
          ]
        ],
        "catch": "자동차 회사가 안전성을 공개해야 하면, 소비자는 안전과 다른 요소를 비교할 수 있다는 거예요!",
        "vocab": [
          [
            "manufacturers",
            "제조업체"
          ],
          [
            "measure",
            "측정하다"
          ],
          [
            "publicize",
            "공개하다"
          ],
          [
            "purchasers",
            "구매자"
          ]
        ],
        "steps": [
          [
            "분석",
            "are required = 요구받다 (제조업체가 '요구당함')"
          ]
        ]
      },
      {
        "src": "41-42",
        "en": "A similar idea is supported by further evidence that 'checklists' can improve the quality of expert decisions in a range of domains by ensuring that important steps or considerations aren't missed when people are feeling overloaded.",
        "chunks": [
          [
            "A similar idea is supported",
            "유사한 아이디어가 뒷받침된다"
          ],
          [
            "by further evidence",
            "추가적인 증거에 의해"
          ],
          [
            "that 'checklists' can improve the quality of expert decisions",
            "'체크리스트'가 전문가의 결정의 질을 향상할 수 있다는"
          ],
          [
            "in a range of domains",
            "다양한 영역에서"
          ],
          [
            "by ensuring that important steps or considerations aren't missed",
            "중요한 조치나 고려 사항을 놓치지 않도록 함으로써"
          ],
          [
            "when people are feeling overloaded.",
            "사람들이 일이 너무 많다고 느낄 때."
          ]
        ],
        "catch": "체크리스트가 전문가 판단의 질을 높인다는 증거가 이 생각을 뒷받침한다는 거예요!",
        "vocab": [
          [
            "supported",
            "뒷받침되는"
          ],
          [
            "evidence",
            "증거"
          ],
          [
            "ensuring",
            "확실히 하는 것"
          ],
          [
            "overloaded",
            "과부하된"
          ]
        ],
        "steps": [
          [
            "분석",
            "is supported by further evidence = 추가 증거에 의해 뒷받침된다"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "40",
        "en": "Craftsmanship cuts a far wider swath than skilled manual labor; it serves the computer programmer, the doctor, and the artist; parenting improves when it is practiced as a skilled craft, as does citizenship.",
        "chunks": [
          [
            "Craftsmanship cuts a far wider swath",
            "장인정신은 훨씬 더 넓은 구획을 가르는데"
          ],
          [
            "than skilled manual labor;",
            "숙련된 육체 노동보다;"
          ],
          [
            "it serves the computer programmer, the doctor, and the artist;",
            "그것은 컴퓨터 프로그래머, 의사, 예술가에게 도움이 되고;"
          ],
          [
            "parenting improves",
            "양육은 향상된다"
          ],
          [
            "when it is practiced as a skilled craft,",
            "그것이 숙련된 기술로서 실행될 때,"
          ],
          [
            "as does citizenship.",
            "시민정신과 마찬가지로."
          ]
        ],
        "catch": "장인정신은 육체노동뿐 아니라 프로그래머·의사·예술가·양육·시민정신에도 적용된다는 거예요!",
        "vocab": [
          [
            "swath",
            "구획, 범위"
          ],
          [
            "manual labor",
            "육체 노동"
          ],
          [
            "practiced",
            "실행되는"
          ],
          [
            "citizenship",
            "시민정신"
          ]
        ]
      },
      {
        "src": "40",
        "en": "The craftsman often faces conflicting objective standards of excellence; the desire to do something well for its own sake can be weakened by competitive pressure, by frustration, or by obsession.",
        "chunks": [
          [
            "The craftsman often faces conflicting objective standards of excellence;",
            "장인은 흔히 뛰어남에 대한 상충되는 객관적 기준에 직면하며;"
          ],
          [
            "the desire to do something well for its own sake",
            "어떤 일 그 자체를 위해 그것을 잘하려는 욕망은"
          ],
          [
            "can be weakened",
            "약화될 수 있다"
          ],
          [
            "by competitive pressure,",
            "경쟁적 압력에 의해,"
          ],
          [
            "by frustration,",
            "좌절에 의해,"
          ],
          [
            "or by obsession.",
            "또는 집착에 의해."
          ]
        ],
        "catch": "장인이 뭔가 잘하고 싶은 욕망은 경쟁·좌절·집착 때문에 약해질 수 있다는 거예요!",
        "vocab": [
          [
            "conflicting",
            "상충되는"
          ],
          [
            "excellence",
            "뛰어남"
          ],
          [
            "weakened",
            "약화된"
          ],
          [
            "obsession",
            "집착"
          ]
        ]
      },
      {
        "src": "23",
        "en": "If restaurant customers are informed of the calories in their meals, those who want to lose weight can make use of the information...",
        "chunks": [
          [
            "If restaurant customers are informed of the calories in their meals,",
            "식당 손님들에게 식사의 칼로리를 알려주면,"
          ],
          [
            "those who want to lose weight",
            "살을 빼고 싶은 사람들은"
          ],
          [
            "can make use of the information...",
            "그 정보를 이용할 수 있다..."
          ]
        ],
        "catch": "식당에서 칼로리를 알려주면 살 빼고 싶은 사람이 그 정보를 쓸 수 있다는 거예요!",
        "vocab": [
          [
            "informed",
            "정보를 받은"
          ],
          [
            "make use of",
            "~을 이용하다"
          ]
        ]
      }
    ]
  },
  {
    "key": "to부정사",
    "title": "③ to부정사 — 'to+동사원형'의 3가지 얼굴",
    "intro": [
      "'to + 동사원형' 모양이야. 쌤이 자주 강조하는 건데, 이게 ①명사처럼(~하는 것) ②형용사처럼(~할, 명사 뒤에서 꾸밈) ③부사처럼(~하기 위해서) 이렇게 3가지로 바뀔 수 있어."
    ],
    "signal": [
      "to부정사 앞에 명사가 있으면 → ②형용사(~할)",
      "동사(want/need/decide 등) 뒤 목적어 자리면 → ①명사(~하는 것)",
      "문장 앞/끝에서 이유를 나타내면 → ③목적(~하기 위해서)",
      "가주어 It ~ to- 구문이면 → ①명사(~하는 것)"
    ],
    "method": [
      [
        "1단계",
        "to부정사 앞에 뭐가 있는지 확인한다 (명사? 동사? 문장 처음?)."
      ],
      [
        "2단계",
        "① 명사 ② 형용사 ③ 부사 중 어떤 역할인지 판단한다."
      ],
      [
        "3단계",
        "역할에 맞게 해석한다."
      ]
    ],
    "worked": [
      {
        "src": "24",
        "en": "It is natural to assume that anyone who sees an object sees everything about it — the shape, color, location, and movement.",
        "chunks": [
          [
            "It is natural",
            "당연하다"
          ],
          [
            "to assume",
            "추정하는 것은"
          ],
          [
            "that anyone who sees an object",
            "물체를 보는 사람은 누구든"
          ],
          [
            "sees everything about it",
            "그것에 관한 모든 것을 보고 있다고"
          ],
          [
            "— the shape, color, location, and movement.",
            "모양, 색깔, 위치, 움직임 등."
          ]
        ],
        "catch": "물체를 보면 그것에 관한 모든 걸 다 본다고 생각하기 쉽다는 거예요!",
        "vocab": [
          [
            "assume",
            "추정하다"
          ],
          [
            "movement",
            "움직임"
          ]
        ],
        "steps": [
          [
            "분석",
            "It은 가짜 주어, to assume 이하가 진짜 주어 → ①명사(~하는 것)"
          ]
        ]
      },
      {
        "src": "20",
        "en": "The strategy is to analyze all the possible scenarios that the future holds and then to see what proportion of them lead to success or failure.",
        "chunks": [
          [
            "The strategy is",
            "전략은"
          ],
          [
            "to analyze all the possible scenarios",
            "모든 가능한 시나리오를 분석하는 것이다"
          ],
          [
            "that the future holds",
            "미래가 안고 있는"
          ],
          [
            "and then to see",
            "그런 다음 살펴보는 것"
          ],
          [
            "what proportion of them lead to success or failure.",
            "그것들이 성공이나 실패로 이어질 비율이 얼마나 되는지를."
          ]
        ],
        "catch": "미래의 가능한 시나리오를 분석해서 성공/실패 비율을 보는 게 전략이라는 거예요!",
        "vocab": [
          [
            "strategy",
            "전략"
          ],
          [
            "scenarios",
            "시나리오"
          ],
          [
            "proportion",
            "비율"
          ]
        ],
        "steps": [
          [
            "분석",
            "is 뒤 주격보어 자리 → ①명사(~하는 것)"
          ]
        ]
      },
      {
        "src": "32",
        "en": "People have always wanted to be around other people and to learn from them.",
        "chunks": [
          [
            "People have always wanted",
            "사람들은 항상 원해 왔다"
          ],
          [
            "to be around other people",
            "다른 사람들 주위에 머무르기를"
          ],
          [
            "and to learn from them.",
            "그리고 그들로부터 배우기를."
          ]
        ],
        "catch": "사람들은 늘 다른 사람과 함께 있고 배우고 싶어했다는 거예요!",
        "vocab": [
          [
            "be around",
            "주위에 있다"
          ]
        ],
        "steps": [
          [
            "분석",
            "wanted의 목적어 자리 → ①명사(~하는 것)"
          ]
        ]
      },
      {
        "src": "31",
        "en": "This reluctance to take sports journalism seriously produces the paradoxical outcome that sports newspaper writers are much read but little admired.",
        "chunks": [
          [
            "This reluctance to take sports journalism seriously",
            "스포츠 저널리즘을 진지하게 여기기를 꺼리는 이것은"
          ],
          [
            "produces the paradoxical outcome",
            "역설적인 결과를 낳는다"
          ],
          [
            "that sports newspaper writers are much read",
            "스포츠 신문 작가들이 많이 읽히면서도"
          ],
          [
            "but little admired.",
            "거의 존경받지 못하는."
          ]
        ],
        "catch": "스포츠 저널리즘을 진지하게 안 받아들이려는 태도가 역설적 결과를 낳는다는 거예요!",
        "vocab": [
          [
            "reluctance",
            "꺼림, 주저함"
          ],
          [
            "outcome",
            "결과"
          ],
          [
            "admired",
            "존경받는"
          ]
        ],
        "steps": [
          [
            "분석",
            "reluctance(명사) 바로 뒤 → ②형용사(~하는 것에 대한/~하려는)"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "20",
        "en": "The mathematical theory of probability hasn't eliminated risk, but it allows us to manage that risk more effectively.",
        "chunks": [
          [
            "The mathematical theory of probability",
            "확률에 대한 수학적 이론은"
          ],
          [
            "hasn't eliminated risk,",
            "위험을 제거하지는 않았지만,"
          ],
          [
            "but it allows us",
            "우리가 할 수 있게 해준다"
          ],
          [
            "to manage that risk more effectively.",
            "그 위험을 더 효과적으로 관리할 수 있게."
          ]
        ],
        "catch": "확률 이론이 위험을 없애진 않지만 더 잘 관리하게 해준다는 거예요!",
        "vocab": [
          [
            "probability",
            "확률"
          ],
          [
            "eliminated",
            "제거된"
          ],
          [
            "effectively",
            "효과적으로"
          ]
        ]
      },
      {
        "src": "22",
        "en": "The latter have the potential to become a preferred 'last-mile' vehicle, particularly in high-density and congested areas.",
        "chunks": [
          [
            "The latter have the potential",
            "후자(자전거)는 잠재력이 있다"
          ],
          [
            "to become a preferred 'last-mile' vehicle,",
            "선호되는 '최종 단계' 운송 수단이 될,"
          ],
          [
            "particularly in high-density and congested areas.",
            "특히 밀도가 높고 혼잡한 지역에서."
          ]
        ],
        "catch": "자전거가 혼잡한 지역에서 최종 배송수단이 될 가능성이 있다는 거예요!",
        "vocab": [
          [
            "potential",
            "잠재력"
          ],
          [
            "preferred",
            "선호되는"
          ],
          [
            "congested",
            "혼잡한"
          ]
        ]
      },
      {
        "src": "24",
        "en": "Consequently, after localized brain damage, it is possible to see certain aspects of an object and not others.",
        "chunks": [
          [
            "Consequently,",
            "따라서,"
          ],
          [
            "after localized brain damage,",
            "국부적 뇌 손상 후,"
          ],
          [
            "it is possible",
            "가능하다"
          ],
          [
            "to see certain aspects of an object",
            "물체의 특정한 측면은 볼 수 있으면서"
          ],
          [
            "and not others.",
            "다른 측면은 볼 수 없는 것이."
          ]
        ],
        "catch": "뇌 특정 부위가 손상되면 어떤 측면은 보이고 어떤 건 안 보일 수 있다는 거예요!",
        "vocab": [
          [
            "consequently",
            "따라서"
          ],
          [
            "localized",
            "국부적인"
          ],
          [
            "aspects",
            "측면"
          ]
        ]
      },
      {
        "src": "40",
        "en": "Craftsmanship names an enduring, basic human impulse, the desire to do a job well for its own sake.",
        "chunks": [
          [
            "Craftsmanship names an enduring, basic human impulse,",
            "장인정신은 지속적이고 기본적인 인간의 충동을 말한다,"
          ],
          [
            "the desire to do a job well",
            "일을 잘하고 싶은 욕망"
          ],
          [
            "for its own sake.",
            "그 자체를 위해."
          ]
        ],
        "catch": "장인정신은 일 자체를 위해 잘하고 싶은 욕망이라는 거예요!",
        "vocab": [
          [
            "enduring",
            "지속적인"
          ],
          [
            "impulse",
            "충동"
          ],
          [
            "for its own sake",
            "그 자체를 위해"
          ]
        ]
      },
      {
        "src": "40",
        "en": "Social and economic conditions, however, often stand in the way of the craftsman's discipline and commitment: schools may fail to provide the tools to do good work...",
        "chunks": [
          [
            "Social and economic conditions, however,",
            "그러나 사회적, 경제적 조건은,"
          ],
          [
            "often stand in the way of the craftsman's discipline and commitment:",
            "흔히 장인의 수련과 전념을 방해하는데:"
          ],
          [
            "schools may fail to provide the tools",
            "학교는 도구를 제공하지 못할 수 있다"
          ],
          [
            "to do good work...",
            "일을 잘하기 위한..."
          ]
        ],
        "catch": "사회·경제적 조건이 장인정신을 방해할 수 있다는 거예요!",
        "vocab": [
          [
            "stand in the way of",
            "~을 방해하다"
          ],
          [
            "discipline",
            "수련"
          ],
          [
            "commitment",
            "전념"
          ]
        ]
      }
    ]
  },
  {
    "key": "동명사",
    "title": "④ 동명사 — '동사원형+ing'가 명사가 될 때",
    "intro": [
      "'동사원형+ing'가 문장의 주어 자리, enjoy/avoid/finish 같은 특정 동사의 목적어 자리, 또는 By/of/in 같은 전치사 바로 뒤에 오면 '~하는 것'이라는 명사로 쓰인 거야."
    ],
    "signal": [
      "문장 맨 앞에 ~ing로 시작하고 뒤에 동사가 있다 (주어 자리).",
      "전치사(By, of, in, without 등) 바로 뒤에 ~ing가 온다.",
      "to부정사와 뜻은 비슷하지만, 동명사는 전치사 뒤에도 올 수 있다는 게 다르다."
    ],
    "method": [
      [
        "1단계",
        "~ing가 어느 자리에 있는지 본다 (문장 맨 앞? 전치사 뒤?)."
      ],
      [
        "2단계",
        "'~하는 것'으로 해석한다."
      ]
    ],
    "worked": [
      {
        "src": "20",
        "en": "Trusting our intuition to make the choice often ends up with us making a suboptimal choice.",
        "chunks": [
          [
            "Trusting our intuition to make the choice",
            "선택을 하기 위해 우리의 직관을 믿는 것은"
          ],
          [
            "often ends up",
            "흔히 결국 끝난다"
          ],
          [
            "with us making a suboptimal choice.",
            "우리가 차선의 선택을 하는 것으로."
          ]
        ],
        "catch": "직관만 믿고 선택하면 결국 안 좋은 선택으로 끝난다는 거예요!",
        "vocab": [
          [
            "intuition",
            "직관"
          ],
          [
            "ends up with",
            "결국 ~로 끝나다"
          ],
          [
            "suboptimal",
            "차선의"
          ]
        ],
        "steps": [
          [
            "분석",
            "Trusting이 문장 맨 앞 주어 자리 → ~하는 것"
          ]
        ]
      },
      {
        "src": "35",
        "en": "Learning to control your voice and use it for different purposes is, therefore, one of the most important skills to develop as an early career teacher.",
        "chunks": [
          [
            "Learning to control your voice and use it for different purposes",
            "목소리를 통제하고 다양한 목적을 위해 사용하는 것을 배우는 것은"
          ],
          [
            "is, therefore,",
            "따라서,"
          ],
          [
            "one of the most important skills",
            "가장 중요한 기술 중 하나이다"
          ],
          [
            "to develop as an early career teacher.",
            "경력 초기의 교사로서 개발해야 할."
          ]
        ],
        "catch": "목소리 조절법을 배우는 게 초보 교사에게 제일 중요한 기술 중 하나라는 거예요!",
        "vocab": [
          [
            "purposes",
            "목적"
          ],
          [
            "skills",
            "기술"
          ]
        ],
        "steps": [
          [
            "분석",
            "Learning이 문장 맨 앞 주어 자리 → ~하는 것 (그 안의 to control은 Learning을 꾸며주는 to부정사)"
          ]
        ]
      },
      {
        "src": "41-42",
        "en": "Using checklists to ensure that no crucial steps are missed has proved to be remarkably effective in a range of medical contexts, from preventing live infections to reducing pneumonia.",
        "chunks": [
          [
            "Using checklists to ensure that no crucial steps are missed",
            "중요한 조치라도 놓치지 않기 위해 체크리스트를 사용하는 것은"
          ],
          [
            "has proved to be remarkably effective",
            "현저하게 효과적이라는 것이 입증되었다"
          ],
          [
            "in a range of medical contexts,",
            "다양한 의학적 상황에서,"
          ],
          [
            "from preventing live infections",
            "당면한 감염을 예방하는 것에서부터"
          ],
          [
            "to reducing pneumonia.",
            "폐렴을 줄이는 것에 이르기까지."
          ]
        ],
        "catch": "체크리스트를 쓰는 게 여러 의료 상황에서 효과적이라고 입증됐다는 거예요!",
        "vocab": [
          [
            "crucial",
            "중요한"
          ],
          [
            "remarkably",
            "현저하게"
          ],
          [
            "preventing",
            "예방하는 것"
          ],
          [
            "reducing",
            "줄이는 것"
          ]
        ],
        "steps": [
          [
            "분석",
            "Using이 문장 맨 앞 주어 자리 → ~하는 것 (from A to B의 A, B 자리도 각각 동명사)"
          ]
        ]
      },
      {
        "src": "21",
        "en": "By making the self public in a private sphere, the self also became an object for self-inspection and self-critique.",
        "chunks": [
          [
            "By making the self public in a private sphere,",
            "자아를 사적 영역에서 공적으로 만들면서,"
          ],
          [
            "the self also became an object",
            "자아는 또한 대상이 되었다"
          ],
          [
            "for self-inspection and self-critique.",
            "자기 점검과 자기 비판의."
          ]
        ],
        "catch": "자아를 사적 공간에서 공개하니까 자기 점검의 대상이 됐다는 거예요!",
        "vocab": [
          [
            "sphere",
            "영역"
          ],
          [
            "self-inspection",
            "자기 점검"
          ],
          [
            "self-critique",
            "자기 비판"
          ]
        ],
        "steps": [
          [
            "분석",
            "전치사 By 바로 뒤 making → ~함으로써(~하는 것을 통해)"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "20",
        "en": "Turning the uncertainty into numbers has proved a potent way of analyzing the paths and finding the shortcut to your destination.",
        "chunks": [
          [
            "Turning the uncertainty into numbers",
            "불확실성을 숫자로 바꾸는 것은"
          ],
          [
            "has proved a potent way",
            "강력한 방법으로 입증되었다"
          ],
          [
            "of analyzing the paths",
            "길을 분석하고"
          ],
          [
            "and finding the shortcut to your destination.",
            "목적지로 가는 지름길을 찾는."
          ]
        ],
        "catch": "불확실성을 숫자로 바꾸는 게 길을 분석하는 강력한 방법이었다는 거예요!",
        "vocab": [
          [
            "uncertainty",
            "불확실성"
          ],
          [
            "potent",
            "강력한"
          ],
          [
            "shortcut",
            "지름길"
          ]
        ]
      },
      {
        "src": "24",
        "en": "Centuries ago, people found it difficult to imagine how someone could see an object without seeing what color it is.",
        "chunks": [
          [
            "Centuries ago,",
            "수 세기 전,"
          ],
          [
            "people found it difficult",
            "사람들은 어렵다고 느꼈다"
          ],
          [
            "to imagine how someone could see an object",
            "어떻게 누군가가 물체를 볼 수 있는지 상상하기가"
          ],
          [
            "without seeing what color it is.",
            "색깔이 무엇인지 못 보면서."
          ]
        ],
        "catch": "옛날엔 색깔 안 보고 물체를 본다는 걸 상상하기 어려웠다는 거예요!",
        "vocab": [
          [
            "centuries ago",
            "수 세기 전"
          ],
          [
            "imagine",
            "상상하다"
          ]
        ]
      },
      {
        "src": "31",
        "en": "In discharging their usual responsibilities of description and commentary, reporters' accounts of sports events are eagerly consulted by sports fans, while in their broader journalistic role of covering sport in its many forms, sports journalists are among the most visible of all contemporary writers.",
        "chunks": [
          [
            "In discharging their usual responsibilities of description and commentary,",
            "기자들이 설명하고 논평하는 통상적인 일을 이행할 때,"
          ],
          [
            "reporters' accounts of sports events",
            "스포츠 경기에 관한 기자들의 설명은"
          ],
          [
            "are eagerly consulted by sports fans,",
            "스포츠팬들이 열심히 찾아보는 반면,"
          ],
          [
            "while in their broader journalistic role of covering sport in its many forms,",
            "여러 형식으로 스포츠를 취재하는 더 폭넓은 저널리스트의 역할에서는,"
          ],
          [
            "sports journalists are among the most visible of all contemporary writers.",
            "스포츠 저널리스트는 동시대의 모든 작가 중에서 가장 눈에 띈다."
          ]
        ],
        "catch": "기자가 설명·논평할 때 팬들이 열심히 찾아보고, 취재 역할에서는 가장 눈에 띈다는 거예요!",
        "vocab": [
          [
            "discharging",
            "이행하는 것"
          ],
          [
            "commentary",
            "논평"
          ],
          [
            "consulted",
            "찾아봐지는"
          ],
          [
            "contemporary",
            "동시대의"
          ]
        ]
      },
      {
        "src": "35",
        "en": "However, I would always advise that you use your loudest voice incredibly sparingly and avoid shouting as much as possible.",
        "chunks": [
          [
            "However,",
            "그러나,"
          ],
          [
            "I would always advise",
            "나는 항상 조언하고자 한다"
          ],
          [
            "that you use your loudest voice incredibly sparingly",
            "가장 큰 목소리는 놀랍도록 드물게 쓰고"
          ],
          [
            "and avoid shouting",
            "소리치는 것을 피해야 한다고"
          ],
          [
            "as much as possible.",
            "최대한."
          ]
        ],
        "catch": "큰 목소리는 드물게 쓰고 소리치는 건 최대한 피하라는 거예요!",
        "vocab": [
          [
            "sparingly",
            "드물게"
          ],
          [
            "avoid",
            "피하다"
          ],
          [
            "shouting",
            "소리치는 것"
          ]
        ]
      },
      {
        "src": "41-42",
        "en": "For example, algorithms have proved more accurate than humans in predicting whether a prisoner released on parole will go on to commit another crime, or in predicting whether a potential candidate will perform well in a job in future.",
        "chunks": [
          [
            "For example,",
            "예를 들어,"
          ],
          [
            "algorithms have proved more accurate than humans",
            "알고리즘이 인간보다 더 정확하다는 것이 입증되었다"
          ],
          [
            "in predicting whether a prisoner released on parole will go on to commit another crime,",
            "가석방으로 풀려난 죄수가 계속해서 다른 범죄를 저지를 것인지 예측하는 데,"
          ],
          [
            "or in predicting whether a potential candidate will perform well in a job in future.",
            "또는 잠재적인 후보자가 장차 직장에서 일을 잘할 것인지를 예측하는 데."
          ]
        ],
        "catch": "알고리즘이 재범이나 채용 예측에서 인간보다 더 정확했다는 거예요!",
        "vocab": [
          [
            "accurate",
            "정확한"
          ],
          [
            "released on parole",
            "가석방으로 풀려난"
          ],
          [
            "commit (a crime)",
            "범죄를 저지르다"
          ]
        ]
      }
    ]
  },
  {
    "key": "관계사",
    "title": "⑤ 관계사 — 앞의 명사를 자세히 설명해주는 문장",
    "intro": [
      "who / which / that / whose / where 뒤에 (주어나 목적어가 하나 빠진) 문장이 이어지면, 쌤은 그걸 바로 앞 명사를 자세히 설명해주는 걸로 봐. '그런데 그건/그 사람은 ~하는' 이렇게 이해하면 편해."
    ],
    "signal": [
      "명사 뒤에 who / which / that / whose / where 가 나온다.",
      "그 뒤 문장에 주어나 목적어가 하나 비어있다 (그 자리가 원래 앞 명사 자리).",
      "관계사절이 콤마(,) 뒤에 나오면 '그런데 그것은~'으로 이어서 해석한다."
    ],
    "method": [
      [
        "1단계",
        "관계사 앞 명사(선행사)에 동그라미 친다."
      ],
      [
        "2단계",
        "관계사절 전체를 괄호로 묶는다."
      ],
      [
        "3단계",
        "괄호 안을 '~하는'으로 바꿔서 선행사 앞(또는 뒤)에 자연스럽게 붙인다."
      ]
    ],
    "worked": [
      {
        "src": "24",
        "en": "Cells that help your hand muscles reach out to an object need to know the size and location of the object, but they don't need to know about color.",
        "chunks": [
          [
            "Cells",
            "세포들은"
          ],
          [
            "that help your hand muscles reach out to an object",
            "손 근육이 물체에 닿도록 돕는"
          ],
          [
            "need to know the size and location of the object,",
            "그 물체의 크기와 위치를 알아야 하지만,"
          ],
          [
            "but they don't need to know about color.",
            "색깔에 대해 알 필요는 없다."
          ]
        ],
        "catch": "손 근육 돕는 세포는 크기·위치만 알면 되고 색깔은 몰라도 된다는 거예요!",
        "vocab": [
          [
            "cells",
            "세포"
          ],
          [
            "muscles",
            "근육"
          ],
          [
            "reach out to",
            "~에 닿다"
          ],
          [
            "location",
            "위치"
          ]
        ],
        "steps": [
          [
            "선행사",
            "Cells"
          ],
          [
            "관계사절(괄호)",
            "(that help your hand muscles reach out to an object) = 손 근육이 물체에 닿도록 돕는"
          ]
        ]
      },
      {
        "src": "40",
        "en": "\"Craftsmanship\" may suggest a way of life that declined with the arrival of industrial society — but this is misleading.",
        "chunks": [
          [
            "\"Craftsmanship\" may suggest a way of life",
            "'장인정신'은 삶의 방식을 나타낼지도 모른다"
          ],
          [
            "that declined with the arrival of industrial society",
            "산업 사회의 도래와 함께 쇠퇴한"
          ],
          [
            "— but this is misleading.",
            "하지만 이것은 오해의 소지가 있다."
          ]
        ],
        "catch": "'장인정신'이 쇠퇴한 삶의 방식처럼 들리지만 그건 오해라는 거예요!",
        "vocab": [
          [
            "craftsmanship",
            "장인정신"
          ],
          [
            "declined",
            "쇠퇴했다"
          ],
          [
            "arrival",
            "도래"
          ],
          [
            "misleading",
            "오해의 소지가 있는"
          ]
        ],
        "steps": [
          [
            "선행사",
            "a way of life"
          ],
          [
            "관계사절(괄호)",
            "(that declined with the arrival of industrial society) = 산업 사회의 도래와 함께 쇠퇴한"
          ]
        ]
      },
      {
        "src": "32",
        "en": "Cities drive taste change because they offer the greatest exposure to other people, who not surprisingly are often the creative people cities seem to attract.",
        "chunks": [
          [
            "Cities drive taste change",
            "도시는 취향 변화를 이끄는데"
          ],
          [
            "because they offer the greatest exposure to other people,",
            "다른 사람들과의 가장 많은 접촉을 제공하기 때문이다,"
          ],
          [
            "who not surprisingly are often the creative people",
            "그런데 그들은 놀랍지 않게도 흔히 창의적인 사람들인데"
          ],
          [
            "cities seem to attract.",
            "도시가 끌어들이는 듯 보이는."
          ]
        ],
        "catch": "도시가 사람들과 접촉을 많이 시켜줘서 취향 변화를 이끈다는 거예요!",
        "vocab": [
          [
            "exposure",
            "접촉, 노출"
          ],
          [
            "not surprisingly",
            "놀랍지 않게도"
          ],
          [
            "attract",
            "끌어들이다"
          ]
        ],
        "steps": [
          [
            "선행사",
            "other people (콤마 뒤라서 '그런데 그들은~'으로 해석)"
          ],
          [
            "관계사절(괄호)",
            "(who not surprisingly are often the creative people cities seem to attract) = 그런데 그들은 도시가 끌어들이는 듯한 창의적인 사람들인데"
          ]
        ]
      },
      {
        "src": "21",
        "en": "They provided a space where one could write daily about her whereabouts, feelings, and thoughts.",
        "chunks": [
          [
            "They provided a space",
            "그것은 공간을 제공했다"
          ],
          [
            "where one could write daily",
            "그곳에서 매일 쓸 수 있는"
          ],
          [
            "about her whereabouts, feelings, and thoughts.",
            "자신의 행방, 감정, 생각에 대해."
          ]
        ],
        "catch": "일기는 사람이 매일 자기 얘기를 쓸 수 있는 공간이었다는 거예요!",
        "vocab": [
          [
            "provided",
            "제공했다"
          ],
          [
            "whereabouts",
            "행방"
          ]
        ],
        "steps": [
          [
            "선행사",
            "a space"
          ],
          [
            "관계사절(괄호)",
            "(where one could write daily about her whereabouts, feelings, and thoughts) = 그곳에서 매일 자신의 행방·감정·생각을 쓸 수 있는"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "23",
        "en": "For example, energy efficiency requirements for appliances may produce goods that work less well or that have characteristics that consumers do not want.",
        "chunks": [
          [
            "For example,",
            "예를 들어,"
          ],
          [
            "energy efficiency requirements for appliances",
            "가전제품에 대한 에너지 효율 요건은"
          ],
          [
            "may produce goods",
            "제품을 만들어 낼 수도 있다"
          ],
          [
            "that work less well",
            "덜 잘 작동하거나"
          ],
          [
            "or that have characteristics",
            "또는 특성을 가진"
          ],
          [
            "that consumers do not want.",
            "소비자가 원하지 않는."
          ]
        ],
        "catch": "에너지 효율 요건 때문에 오히려 덜 좋은 제품이 나올 수도 있다는 거예요!",
        "vocab": [
          [
            "requirements",
            "요건"
          ],
          [
            "appliances",
            "가전제품"
          ],
          [
            "characteristics",
            "특성"
          ]
        ]
      },
      {
        "src": "24",
        "en": "Cells that help you recognize people's faces need to be extremely sensitive to details of shape, but they can pay less attention to location.",
        "chunks": [
          [
            "Cells",
            "세포는"
          ],
          [
            "that help you recognize people's faces",
            "여러분이 사람의 얼굴을 인식하도록 돕는"
          ],
          [
            "need to be extremely sensitive to details of shape,",
            "모양의 세부 사항에 극도로 예민해야 하지만,"
          ],
          [
            "but they can pay less attention to location.",
            "위치에는 신경을 덜 쓸 수 있다."
          ]
        ],
        "catch": "얼굴 인식 돕는 세포는 모양은 예민하게, 위치는 덜 신경써도 된다는 거예요!",
        "vocab": [
          [
            "recognize",
            "인식하다"
          ],
          [
            "sensitive",
            "예민한"
          ],
          [
            "pay attention to",
            "~에 신경 쓰다"
          ]
        ]
      },
      {
        "src": "31",
        "en": "Yet sports journalists do not have a standing in their profession that corresponds to the size of their readerships or of their pay packets...",
        "chunks": [
          [
            "Yet sports journalists do not have a standing in their profession",
            "그러나 스포츠 저널리스트는 그들 전문성에서의 지위를 누리지 못한다"
          ],
          [
            "that corresponds to the size of their readerships",
            "독자 수의 크기에 상응하는"
          ],
          [
            "or of their pay packets...",
            "또는 급여 액수의..."
          ]
        ],
        "catch": "스포츠 기자는 독자수·연봉만큼의 지위를 못 누린다는 거예요!",
        "vocab": [
          [
            "standing",
            "지위"
          ],
          [
            "profession",
            "직업"
          ],
          [
            "corresponds to",
            "~에 상응하다"
          ],
          [
            "readerships",
            "독자 수"
          ]
        ]
      },
      {
        "src": "32",
        "en": "It spreads outward, in a manner not unlike transmissible disease, which itself typically \"takes off\" in cities.",
        "chunks": [
          [
            "It spreads outward,",
            "그것은 외부로 퍼져나가는데,"
          ],
          [
            "in a manner not unlike transmissible disease,",
            "전염성 질병과 다르지 않은 방식으로,"
          ],
          [
            "which itself typically \"takes off\" in cities.",
            "그런데 그 전염성 질병 자체도 보통 도시에서 '이륙한다.'"
          ]
        ],
        "catch": "속어는 전염병처럼 퍼지는데, 그 전염병도 보통 도시에서 시작된다는 거예요!",
        "vocab": [
          [
            "spreads",
            "퍼지다"
          ],
          [
            "transmissible disease",
            "전염성 질병"
          ],
          [
            "typically",
            "보통"
          ]
        ]
      },
      {
        "src": "21",
        "en": "Diaries were central media through which enlightened and free subjects could be constructed.",
        "chunks": [
          [
            "Diaries were central media",
            "일기는 중심 매체였다"
          ],
          [
            "through which enlightened and free subjects",
            "그것을 통해 계몽되고 자유로운 주체가"
          ],
          [
            "could be constructed.",
            "구성될 수 있는."
          ]
        ],
        "catch": "일기를 통해서 계몽된 자유로운 자아가 만들어질 수 있었다는 거예요!",
        "vocab": [
          [
            "media",
            "매체"
          ],
          [
            "enlightened",
            "계몽된"
          ],
          [
            "constructed",
            "구성된"
          ]
        ]
      },
      {
        "src": "40",
        "en": "Craftsmanship, a human desire that has persisted over time in diverse contexts, often encounters factors that limit its full development.",
        "chunks": [
          [
            "Craftsmanship,",
            "장인정신은,"
          ],
          [
            "a human desire that has persisted over time in diverse contexts,",
            "다양한 상황에서 시간이 지남에 따라 존속되어 온 인간의 욕망인데,"
          ],
          [
            "often encounters factors",
            "흔히 요소들과 마주친다"
          ],
          [
            "that limit its full development.",
            "그 완전한 발전을 제한하는."
          ]
        ],
        "catch": "장인정신은 오래된 욕망인데, 그 발전을 막는 요소들과 자주 부딪힌다는 거예요!",
        "vocab": [
          [
            "persisted",
            "존속되었다"
          ],
          [
            "diverse",
            "다양한"
          ],
          [
            "encounters",
            "마주친다"
          ],
          [
            "limit",
            "제한하다"
          ]
        ]
      }
    ]
  },
  {
    "key": "분사",
    "title": "⑥ 분사 — 명사 딱 붙어서 꾸며주는 말",
    "intro": [
      "이번엔 -ing나 p.p. 딱 한 단어(또는 짧은 어구)가 명사 앞이나 뒤에 붙어서 그 명사를 꾸며주는 경우야. -ing는 '~하는/~하게 하는', p.p.는 '~된/~당한'으로 해석하면 돼."
    ],
    "signal": [
      "명사 바로 앞에 -ing나 p.p.가 붙어 있다.",
      "명사 바로 뒤에 -ing나 p.p.로 시작하는 짧은 어구가 붙어 있다.",
      "그 명사가 스스로 하면 -ing, 누가 해줘서 당하면 p.p."
    ],
    "method": [
      [
        "1단계",
        "꾸밈 받는 명사를 찾는다."
      ],
      [
        "2단계",
        "-ing/p.p.가 앞에 있는지 뒤에 있는지 확인한다."
      ],
      [
        "3단계",
        "능동(~하는)인지 수동(~된)인지 구별해서 해석한다."
      ]
    ],
    "worked": [
      {
        "src": "20",
        "en": "At every step in our journey through life we encounter junctions with many different pathways leading into the distance.",
        "chunks": [
          [
            "At every step in our journey through life",
            "평생을 두고 우리 여정의 모든 단계에서"
          ],
          [
            "we encounter junctions",
            "우리는 분기점을 만난다"
          ],
          [
            "with many different pathways",
            "많은 다른 길들이 있는"
          ],
          [
            "leading into the distance.",
            "먼 곳으로 이어지는."
          ]
        ],
        "catch": "우리는 살면서 여러 갈래길이 있는 갈림길을 만난다는 거예요!",
        "vocab": [
          [
            "journey",
            "여정"
          ],
          [
            "encounter",
            "만나다"
          ],
          [
            "junctions",
            "분기점"
          ],
          [
            "pathways",
            "길"
          ]
        ],
        "steps": [
          [
            "분석",
            "leading into the distance가 pathways를 뒤에서 꾸밈 (길이 스스로 이어짐 → 능동, -ing)"
          ]
        ]
      },
      {
        "src": "22",
        "en": "Due to their low acquisition and maintenance costs, cargo bicycles convey much potential in developed and developing countries alike, such as the becak (a three-wheeled bicycle) in Indonesia.",
        "chunks": [
          [
            "Due to their low acquisition and maintenance costs,",
            "매입과 유지 비용이 낮아서,"
          ],
          [
            "cargo bicycles convey much potential",
            "짐 자전거는 많은 잠재력을 전달한다"
          ],
          [
            "in developed and developing countries alike,",
            "선진국과 개발도상국에서 똑같이,"
          ],
          [
            "such as the becak (a three-wheeled bicycle) in Indonesia.",
            "인도네시아의 becak(바퀴가 세 개 달린 자전거)와 같이."
          ]
        ],
        "catch": "짐 자전거는 돈이 적게 들어서 선진국이든 개발도상국이든 다 잠재력이 있다는 거예요!",
        "vocab": [
          [
            "acquisition",
            "매입"
          ],
          [
            "maintenance",
            "유지"
          ],
          [
            "convey",
            "전달하다"
          ],
          [
            "potential",
            "잠재력"
          ]
        ],
        "steps": [
          [
            "분석",
            "developed와 developing이 각각 countries를 앞에서 꾸밈 (developed=발전된 p.p. / developing=발전하고 있는 -ing)"
          ]
        ]
      },
      {
        "src": "32",
        "en": "Slang, or, if you prefer, \"lexical innovation,\" has always started in cities — an outgrowth of all those different people so frequently exposed to one another.",
        "chunks": [
          [
            "Slang, or, if you prefer, \"lexical innovation,\"",
            "속어, 또는 '어휘의 혁신'은,"
          ],
          [
            "has always started in cities",
            "항상 도시에서 시작되었다"
          ],
          [
            "— an outgrowth of all those different people",
            "그 모든 별의별 사람의 결과물인데"
          ],
          [
            "so frequently exposed to one another.",
            "그렇게도 빈번히 서로에게 접촉한."
          ]
        ],
        "catch": "속어는 도시에서 시작되는데, 그건 사람들이 서로 자주 접촉해서 생긴 결과라는 거예요!",
        "vocab": [
          [
            "slang",
            "속어"
          ],
          [
            "lexical innovation",
            "어휘의 혁신"
          ],
          [
            "outgrowth",
            "결과물"
          ],
          [
            "frequently",
            "빈번히"
          ]
        ],
        "steps": [
          [
            "분석",
            "exposed to one another가 people을 뒤에서 꾸밈 (사람들이 노출을 당함 → 수동, p.p.)"
          ]
        ]
      },
      {
        "src": "41-42",
        "en": "When there are a lot of different factors involved and a situation is very uncertain, simple formulas can win out by focusing on the most important factors and being consistent...",
        "chunks": [
          [
            "When there are a lot of different factors involved",
            "관련된 많은 다른 요인이 있을 때"
          ],
          [
            "and a situation is very uncertain,",
            "그리고 상황이 매우 불확실할 때,"
          ],
          [
            "simple formulas can win out",
            "간단한 공식이 승리할 수 있다"
          ],
          [
            "by focusing on the most important factors",
            "가장 중요한 요소에 초점을 맞춤으로써"
          ],
          [
            "and being consistent...",
            "그리고 일관성을 유지함으로써..."
          ]
        ],
        "catch": "요인이 많고 상황이 불확실할 땐 간단한 공식이 오히려 더 잘 맞는다는 거예요!",
        "vocab": [
          [
            "factors",
            "요인"
          ],
          [
            "involved",
            "관련된"
          ],
          [
            "consistent",
            "일관된"
          ],
          [
            "salient",
            "두드러진"
          ]
        ],
        "steps": [
          [
            "분석",
            "involved가 factors를 뒤에서 꾸밈 (요인이 '관련됨을 당함' → 수동, p.p.)"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "23",
        "en": "Regulatory mandates are blunt swords; they tend to neglect diversity and may have serious unintended adverse effects.",
        "chunks": [
          [
            "Regulatory mandates are blunt swords;",
            "규제하는 명령은 무딘 칼인데;"
          ],
          [
            "they tend to neglect diversity",
            "그것들은 다양성을 무시하는 경향이 있으며"
          ],
          [
            "and may have serious unintended adverse effects.",
            "의도하지 않은 심각한 역효과를 발생시킬 수도 있다."
          ]
        ],
        "catch": "규제는 무딘 칼 같아서 의도하지 않은 나쁜 효과를 낼 수도 있다는 거예요!",
        "vocab": [
          [
            "mandates",
            "명령"
          ],
          [
            "blunt",
            "무딘"
          ],
          [
            "neglect",
            "무시하다"
          ],
          [
            "unintended",
            "의도하지 않은"
          ]
        ]
      },
      {
        "src": "22",
        "en": "Services using electrically assisted delivery tricycles have been successfully implemented in France and are gradually being adopted across Europe for services as varied as parcel and catering deliveries.",
        "chunks": [
          [
            "Services using electrically assisted delivery tricycles",
            "전기 보조 배달용 세발자전거를 이용하는 서비스는"
          ],
          [
            "have been successfully implemented in France",
            "프랑스에서 성공적으로 시행되었고"
          ],
          [
            "and are gradually being adopted across Europe",
            "유럽 전역에서 점차 도입되고 있다"
          ],
          [
            "for services as varied as parcel and catering deliveries.",
            "소포나 음식 배달과 같은 다양한 서비스를 위해."
          ]
        ],
        "catch": "전기 세발자전거 서비스가 프랑스에서 성공했고 유럽 전역으로 퍼지고 있다는 거예요!",
        "vocab": [
          [
            "assisted",
            "보조되는"
          ],
          [
            "implemented",
            "시행된"
          ],
          [
            "gradually",
            "점차"
          ],
          [
            "adopted",
            "도입된"
          ]
        ]
      },
      {
        "src": "32",
        "en": "If, as the noted linguist Leonard Bloomfield argued, the way a person talks is a \"composite result of what he has heard before,\" then language innovation would happen where the most people heard and talked to the most other people.",
        "chunks": [
          [
            "If, as the noted linguist Leonard Bloomfield argued,",
            "저명한 언어학자 Leonard Bloomfield가 주장하듯,"
          ],
          [
            "the way a person talks",
            "한 사람이 말하는 방식이"
          ],
          [
            "is a \"composite result of what he has heard before,\"",
            "'그가 전에 들었던 것을 합성한 결과물'이라면,"
          ],
          [
            "then language innovation would happen",
            "언어 혁신은 일어날 것이다"
          ],
          [
            "where the most people heard and talked to the most other people.",
            "가장 많은 사람이 가장 많이 듣고 말한 곳에서."
          ]
        ],
        "catch": "유명 언어학자에 따르면, 사람들이 가장 많이 듣고 말하는 곳에서 언어 혁신이 일어난다는 거예요!",
        "vocab": [
          [
            "noted",
            "저명한, 유명한"
          ],
          [
            "linguist",
            "언어학자"
          ],
          [
            "composite",
            "합성의"
          ],
          [
            "innovation",
            "혁신"
          ]
        ]
      },
      {
        "src": "32",
        "en": "Media, ever more global, ever more far-reaching, spread language faster to more people.",
        "chunks": [
          [
            "Media,",
            "미디어는,"
          ],
          [
            "ever more global,",
            "그 어느 때보다 더 전방위적이고,"
          ],
          [
            "ever more far-reaching,",
            "그 어느 때보다 더 멀리까지 미치는,"
          ],
          [
            "spread language faster to more people.",
            "언어를 더 빨리 더 많은 사람에게 퍼뜨린다."
          ]
        ],
        "catch": "미디어가 더 전방위적이고 멀리 미칠수록 언어를 더 빨리 퍼뜨린다는 거예요!",
        "vocab": [
          [
            "far-reaching",
            "멀리까지 미치는"
          ],
          [
            "spread",
            "퍼뜨리다"
          ]
        ]
      },
      {
        "src": "35",
        "en": "A quiet, authoritative and measured tone has so much more impact than slightly panicked shouting.",
        "chunks": [
          [
            "A quiet, authoritative and measured tone",
            "조용하고 권위 있으며 침착한 어조는"
          ],
          [
            "has so much more impact",
            "훨씬 더 큰 효과를 가진다"
          ],
          [
            "than slightly panicked shouting.",
            "약간 당황한 고함보다."
          ]
        ],
        "catch": "조용하고 침착한 어조가 당황한 고함보다 훨씬 효과적이라는 거예요!",
        "vocab": [
          [
            "authoritative",
            "권위 있는"
          ],
          [
            "measured",
            "침착한, 신중한"
          ],
          [
            "impact",
            "효과"
          ],
          [
            "panicked",
            "당황한"
          ]
        ]
      }
    ]
  },
  {
    "key": "분사구문",
    "title": "⑦ 분사구문 — 문장에 붙는 곁다리 설명",
    "intro": [
      "자, 이번 건 문장 앞·중간·끝에 콤마(,)랑 같이 '동사원형+ing' 또는 'p.p.(과거분사)'로 시작하거나 끝나는 덩어리가 붙어있는 경우야. 이건 진짜 주어+동사가 아니라 쌤이 '곁다리 설명'이라고 부르는 거야."
    ],
    "signal": [
      "문장 맨 앞이 ~ing/p.p.로 시작하고 콤마(,)가 있다.",
      "문장 뒤쪽에 콤마(,) + ~ing 덩어리가 붙어 끝난다.",
      "when/while 같은 접속사가 남아있는 채로 ~ing가 오기도 한다 (예: when combined with)."
    ],
    "method": [
      [
        "1단계",
        "~ing/p.p. 덩어리를 괄호로 묶는다."
      ],
      [
        "2단계",
        "괄호 다음(또는 앞) 진짜 주어+동사(뼈대)부터 해석한다."
      ],
      [
        "3단계",
        "괄호 안을 ~하면서 / ~해서 / ~한 채로 / ~하면 중 하나로 연결한다."
      ]
    ],
    "worked": [
      {
        "src": "21",
        "en": "Coming of age in the 18th and 19th centuries, the personal diary became a centerpiece in the construction of a modern subjectivity...",
        "chunks": [
          [
            "Coming of age in the 18th and 19th centuries,",
            "18~19세기에 발달하면서,"
          ],
          [
            "the personal diary became a centerpiece",
            "개인 일기는 중심물이 되었다"
          ],
          [
            "in the construction of a modern subjectivity...",
            "근대적 주체성을 구축하는 데..."
          ]
        ],
        "catch": "18~19세기에 개인 일기가 근대적 자아를 만드는 데 중심이 됐다는 거예요!",
        "vocab": [
          [
            "come of age",
            "발달하다, 성숙하다"
          ],
          [
            "centerpiece",
            "중심물"
          ],
          [
            "construction",
            "구축"
          ],
          [
            "subjectivity",
            "주체성"
          ]
        ],
        "steps": [
          [
            "뼈대",
            "the personal diary became a centerpiece = 개인 일기는 중심물이 되었다"
          ],
          [
            "괄호(~하면서)",
            "18~19세기에 발달하면서"
          ]
        ]
      },
      {
        "src": "23",
        "en": "If restaurant customers are informed of the calories in their meals, those who want to lose weight can make use of the information, leaving those who are unconcerned about calories unaffected.",
        "chunks": [
          [
            "If restaurant customers are informed of the calories in their meals,",
            "식당 손님들에게 식사의 칼로리를 알려주면,"
          ],
          [
            "those who want to lose weight",
            "살을 빼고 싶은 사람들은"
          ],
          [
            "can make use of the information,",
            "그 정보를 이용할 수 있고,"
          ],
          [
            "leaving those who are unconcerned about calories",
            "칼로리에 신경 쓰지 않는 사람들은"
          ],
          [
            "unaffected.",
            "영향을 받지 않은 채로 있게 된다."
          ]
        ],
        "catch": "식당에서 칼로리를 알려주면, 신경쓰는 사람은 이용하고 신경 안 쓰는 사람은 그냥 영향 안 받는다는 거예요!",
        "vocab": [
          [
            "informed",
            "정보를 받은"
          ],
          [
            "make use of",
            "~을 이용하다"
          ],
          [
            "unconcerned",
            "신경 쓰지 않는"
          ],
          [
            "unaffected",
            "영향받지 않은"
          ]
        ],
        "steps": [
          [
            "뼈대",
            "...those who want to lose weight can make use of the information (~할 수 있다)까지가 진짜 문장"
          ],
          [
            "괄호(~한 채로/결과)",
            "leaving those who are unconcerned about calories unaffected = 칼로리에 신경 쓰지 않는 사람들은 영향받지 않은 채로 남겨두면서"
          ]
        ]
      },
      {
        "src": "31",
        "en": "The ruminations of the elite class of 'celebrity' sports journalists are much sought after by the major newspapers, their lucrative contracts being the envy of colleagues in other 'disciplines' of journalism.",
        "chunks": [
          [
            "The ruminations of the elite class of 'celebrity' sports journalists",
            "'유명인급' 스포츠 저널리스트 중 엘리트 계층의 생각은"
          ],
          [
            "are much sought after",
            "많이 원해지고"
          ],
          [
            "by the major newspapers,",
            "주요 신문사들에 의해,"
          ],
          [
            "their lucrative contracts being the envy of colleagues",
            "그들의 돈 잘 버는 계약은 동료들의 선망 대상이 되는데"
          ],
          [
            "in other 'disciplines' of journalism.",
            "저널리즘의 다른 '부문'에 있는."
          ]
        ],
        "catch": "유명 스포츠 기자는 신문사들이 원하고, 그들의 돈 잘버는 계약을 다른 분야 기자들이 부러워한다는 거예요!",
        "vocab": [
          [
            "ruminations",
            "생각, 숙고"
          ],
          [
            "sought after",
            "원해지는, 인기 있는"
          ],
          [
            "lucrative",
            "돈이 되는"
          ],
          [
            "envy",
            "부러움의 대상"
          ]
        ],
        "steps": [
          [
            "뼈대",
            "The ruminations... are much sought after by the major newspapers = 그들의 생각은 신문사들이 많이 원한다"
          ],
          [
            "괄호(~하는데, 부가상황)",
            "their lucrative contracts being the envy of colleagues = 그들의 돈 잘 버는 계약은 동료들의 선망 대상인데 (주어+분사, '독립분사구문'이라는 조금 어려운 형태예요)"
          ]
        ]
      }
    ],
    "practice": [
      {
        "src": "22",
        "en": "Using bicycles as cargo vehicles is particularly encouraged when combined with policies that restrict motor vehicle access to specific areas of a city, such as downtown or commercial districts, or with the extension of dedicated bike lanes.",
        "chunks": [
          [
            "Using bicycles as cargo vehicles",
            "자전거를 화물 운송 수단으로 사용하는 것은"
          ],
          [
            "is particularly encouraged",
            "특히 장려된다"
          ],
          [
            "when combined with policies",
            "정책과 결합될 때"
          ],
          [
            "that restrict motor vehicle access",
            "자동차 접근을 제한하는"
          ],
          [
            "to specific areas of a city,",
            "도시의 특정 지역에"
          ],
          [
            "such as downtown or commercial districts,",
            "도심이나 상업 지구처럼,"
          ],
          [
            "or with the extension of dedicated bike lanes.",
            "또는 자전거 전용 도로의 확장과 (결합될 때)."
          ]
        ],
        "catch": "자전거를 화물용으로 쓰는 게, 자동차 제한 정책이랑 같이 있으면 더 권장된다는 거예요!",
        "vocab": [
          [
            "encouraged",
            "권장되는"
          ],
          [
            "combined with",
            "~와 결합될 때"
          ],
          [
            "restrict",
            "제한하다"
          ],
          [
            "dedicated",
            "전용의"
          ]
        ]
      },
      {
        "src": "35",
        "en": "There are times when being able to project your voice loudly will be very useful when working in school, and knowing that you can cut through a noisy classroom, dinner hall or playground is a great skill to have.",
        "chunks": [
          [
            "There are times",
            "그런 경우가 있다"
          ],
          [
            "when being able to project your voice loudly",
            "목소리를 크게 내보낼 수 있는 것이"
          ],
          [
            "will be very useful",
            "매우 유용할"
          ],
          [
            "when working in school,",
            "학교에서 일할 때,"
          ],
          [
            "and knowing that you can cut through a noisy classroom, dinner hall or playground",
            "그리고 시끄러운 교실, 구내식당이나 운동장을 (목소리로) 가를 수 있다는 것을 아는 것은"
          ],
          [
            "is a great skill to have.",
            "갖춰야 할 훌륭한 기술이다."
          ]
        ],
        "catch": "학교에서 일할 때 목소리를 크게 낼 수 있는 게 유용할 때가 있다는 거예요!",
        "vocab": [
          [
            "project (voice)",
            "목소리를 내보내다"
          ],
          [
            "cut through",
            "가르다, 뚫고 나가다"
          ],
          [
            "a great skill to have",
            "갖춰야 할 훌륭한 기술"
          ]
        ]
      }
    ]
  }
];

// ────────────────────────────────────────────────────────────────
// 2024년 9월 평가원 모의평가(고3) WORKBOOK 0 추가 연습문제
//   각 챕터의 '혼자 풀어보기(practice)'를 8문제로 균일화하기 위한 보강분.
//   src 는 "9월 N" 으로 표기해 2023 수능(② 이후 챕터)과 출처를 구분한다.
//   기존 데이터는 건드리지 않고 아래에서 practice 뒤에 이어 붙인다.
// ────────────────────────────────────────────────────────────────
const MORE = {
  "전치사구": [
    {
      "src": "9월 40",
      "en": "Human speech differs from the cries of other species in many ways.",
      "chunks": [
        ["Human speech differs", "인간의 말은 다르다"],
        ["from the cries of other species", "다른 종의 울음소리와"],
        ["in many ways.", "여러 가지 면에서"]
      ],
      "catch": "인간의 말은 여러 가지 면에서 다른 동물의 울음소리와 다르다는 거예요!",
      "vocab": [["differ from", "~와 다르다"], ["cries", "울음소리"], ["species", "종"]]
    },
    {
      "src": "9월 20",
      "en": "Truth is essential for progress and the development of knowledge.",
      "chunks": [
        ["Truth is essential", "진실은 필수적이다"],
        ["for progress and the development of knowledge.", "진보와 지식의 발전에"]
      ],
      "catch": "진실은 진보와 지식의 발전에 꼭 필요하다는 거예요!",
      "vocab": [["essential", "필수적인"], ["progress", "진보"], ["development", "발전"]]
    },
    {
      "src": "9월 39",
      "en": "Managers need confidence in the likely outcomes of their interventions.",
      "chunks": [
        ["Managers need confidence", "관리자는 확신이 필요하다"],
        ["in the likely outcomes", "가능한 결과에 대한"],
        ["of their interventions.", "자기 개입의"]
      ],
      "catch": "관리자는 자기 개입이 가져올 결과를 확신할 수 있어야 한다는 거예요!",
      "vocab": [["confidence", "확신"], ["outcome", "결과"], ["intervention", "개입"]]
    },
    {
      "src": "9월 38",
      "en": "Without such an ability, no goal-oriented action would be possible.",
      "chunks": [
        ["Without such an ability,", "그러한 능력이 없으면,"],
        ["no goal-oriented action", "목표 지향적인 행동은"],
        ["would be possible.", "불가능할 것이다"]
      ],
      "catch": "그런 능력이 없으면 목표를 향한 행동 자체가 불가능하다는 거예요!",
      "vocab": [["ability", "능력"], ["goal-oriented", "목표 지향적인"], ["possible", "가능한"]]
    },
    {
      "src": "9월 40",
      "en": "In a typical human language there are something like thirty or forty distinctive speech sounds.",
      "chunks": [
        ["In a typical human language", "일반적인 인간의 언어에는"],
        ["there are something like thirty or forty distinctive speech sounds.", "대략 30~40개의 독특한 말소리가 있다"]
      ],
      "catch": "보통 인간의 언어에는 30~40개쯤의 독특한 말소리가 있다는 거예요!",
      "vocab": [["typical", "일반적인, 전형적인"], ["distinctive", "독특한"], ["speech sound", "말소리"]]
    }
  ],
  "수동태": [
    {
      "src": "9월 40",
      "en": "These sounds can be combined into chains to form a literally unlimited number of words.",
      "chunks": [
        ["These sounds can be combined", "이 소리들은 결합될 수 있다"],
        ["into chains", "연쇄로"],
        ["to form a literally unlimited number of words.", "말 그대로 무제한적인 수의 단어를 만들기 위해"]
      ],
      "catch": "이 소리들을 이어 붙여서 무한히 많은 단어를 만들 수 있다는 거예요!",
      "vocab": [["combine", "결합하다"], ["chain", "연쇄, 사슬"], ["unlimited", "무제한의"]]
    },
    {
      "src": "9월 18",
      "en": "Just then, she heard an announcement saying that her flight had been \"delayed.\"",
      "chunks": [
        ["Just then, she heard an announcement", "바로 그때, 그녀는 안내 방송을 들었다"],
        ["saying that her flight had been \"delayed.\"", "자신의 항공편이 '지연되었다'고 하는"]
      ],
      "catch": "바로 그때 그녀는 자기 항공편이 '지연됐다'는 안내 방송을 들었다는 거예요!",
      "vocab": [["announcement", "안내 방송, 발표"], ["flight", "항공편"], ["delay", "지연시키다"]]
    },
    {
      "src": "9월 21",
      "en": "Thus, their observations were primarily conducted from their verandas.",
      "chunks": [
        ["Thus, their observations were primarily conducted", "그리하여 그들의 관찰은 주로 행해졌다"],
        ["from their verandas.", "그들의 베란다에서"]
      ],
      "catch": "그래서 그들의 관찰은 주로 자기 베란다에서 이뤄졌다는 거예요!",
      "vocab": [["observation", "관찰"], ["primarily", "주로"], ["conduct", "수행하다"]]
    }
  ],
  "to부정사": [
    {
      "src": "9월 41-42",
      "en": "One function of poetry is to depict the world with a fresh perception.",
      "chunks": [
        ["One function of poetry is", "시의 한 가지 기능은"],
        ["to depict the world with a fresh perception.", "신선한 인식으로 세상을 묘사하는 것이다"]
      ],
      "catch": "시의 한 가지 기능은 세상을 신선한 눈으로 새롭게 그려내는 것이라는 거예요!",
      "vocab": [["function", "기능"], ["depict", "묘사하다"], ["perception", "인식"]]
    }
  ],
  "동명사": [
    {
      "src": "9월 35",
      "en": "The best dealers offer a much broader service than merely having their goods on display and 'selling from stock'.",
      "chunks": [
        ["The best dealers offer a much broader service", "최고의 판매업자는 훨씬 폭넓은 서비스를 제공한다"],
        ["than merely having their goods on display", "단지 상품을 전시하는 것보다"],
        ["and 'selling from stock'.", "그리고 '재고를 판매하는 것'보다"]
      ],
      "catch": "최고의 판매업자는 그냥 물건을 진열해 파는 것보다 훨씬 폭넓은 서비스를 준다는 거예요!",
      "vocab": [["dealer", "판매업자, 상인"], ["broader", "더 폭넓은"], ["on display", "전시되어"]]
    }
  ],
  "분사": [
    {
      "src": "9월 43-45",
      "en": "For months, she had been looking for a Philodendron gloriosum, a Colombian plant with dark, velvety leaves shaped like hearts.",
      "chunks": [
        ["For months, she had been looking for", "그녀는 몇 달 동안 ~을 찾고 있었다"],
        ["a Philodendron gloriosum, a Colombian plant", "필로덴드론 글로리오섬, 즉 콜롬비아 식물을"],
        ["with dark, velvety leaves", "짙은 벨벳 같은 잎을 가진"],
        ["shaped like hearts.", "하트 모양의"]
      ],
      "catch": "그녀는 하트 모양의 짙은 벨벳 같은 잎을 가진 콜롬비아 식물을 몇 달째 찾고 있었다는 거예요!",
      "vocab": [["velvety", "벨벳 같은"], ["leaves", "잎(leaf의 복수)"], ["shaped like", "~모양의"]]
    }
  ],
  "분사구문": [
    {
      "src": "9월 18",
      "en": "Letting out a deep sigh, she finally felt at ease.",
      "chunks": [
        ["Letting out a deep sigh,", "깊은 한숨을 내쉬며,"],
        ["she finally felt at ease.", "그녀는 마침내 마음이 편해졌다"]
      ],
      "catch": "깊은 한숨을 내쉬고 나서 그녀는 마침내 마음이 놓였다는 거예요!",
      "vocab": [["let out", "(소리를) 내다"], ["sigh", "한숨"], ["at ease", "편안한"]]
    },
    {
      "src": "9월 18",
      "en": "Worried that she could not get to the boarding gate in time, she rushed through the crowds of people.",
      "chunks": [
        ["Worried that she could not get to the boarding gate in time,", "시간 내에 탑승구에 도착 못 할까 봐 걱정하며,"],
        ["she rushed through the crowds of people.", "그녀는 수많은 사람들을 뚫고 돌진했다"]
      ],
      "catch": "탑승구에 제때 못 갈까 봐 걱정하며 그녀는 인파를 뚫고 달렸다는 거예요!",
      "vocab": [["boarding gate", "탑승구"], ["in time", "시간 내에"], ["rush through", "~을 뚫고 돌진하다"]]
    },
    {
      "src": "9월 43-45",
      "en": "Arriving at the building, Helen could identify Julia by the large paper bag she was holding.",
      "chunks": [
        ["Arriving at the building,", "건물에 도착했을 때,"],
        ["Helen could identify Julia", "Helen은 Julia를 알아볼 수 있었다"],
        ["by the large paper bag she was holding.", "그녀가 들고 있는 커다란 종이봉투로"]
      ],
      "catch": "건물에 도착한 Helen은 커다란 종이봉투를 든 걸 보고 Julia를 알아봤다는 거예요!",
      "vocab": [["arrive at", "~에 도착하다"], ["identify", "알아보다, 식별하다"], ["hold", "들다"]]
    },
    {
      "src": "9월 43-45",
      "en": "Laughing, the woman said, \"Yes! Please take good care of this plant.\"",
      "chunks": [
        ["Laughing,", "웃으며,"],
        ["the woman said, \"Yes! Please take good care of this plant.\"", "그 여자는 '네! 이 식물을 잘 돌봐주세요.'라고 말했다"]
      ],
      "catch": "그 여자는 웃으며 '이 식물을 잘 돌봐 달라'고 말했다는 거예요!",
      "vocab": [["laugh", "웃다"], ["take care of", "~을 돌보다"], ["plant", "식물"]]
    },
    {
      "src": "9월 43-45",
      "en": "Handing over the bag, Julia replied that she was not a plant expert.",
      "chunks": [
        ["Handing over the bag,", "봉투를 건네며,"],
        ["Julia replied", "Julia는 답했다"],
        ["that she was not a plant expert.", "자신은 식물 전문가가 아니라고"]
      ],
      "catch": "Julia는 봉투를 건네며 자신은 식물 전문가가 아니라고 답했다는 거예요!",
      "vocab": [["hand over", "건네주다"], ["reply", "답하다"], ["expert", "전문가"]]
    }
  ]
};

categories.forEach((cat) => {
  if (MORE[cat.key]) cat.practice.push(...MORE[cat.key]);
});

module.exports = categories;

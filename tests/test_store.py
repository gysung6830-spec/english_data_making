"""판매 사이트(store.py · store_admin.py) 오프라인 테스트.

실행: python -m tests.test_store   (또는 pytest tests/test_store.py)
API 키도, 인터넷도 필요 없습니다. 실제 데이터 대신 임시 폴더를 씁니다.

검증 항목:
  - 고객 페이지가 모두 열리는지 (교재별 페이지·공지·프리패스·시험지 보내기 포함)
  - 주문서 입력값 검증과 금액 계산
  - 자료 요청(지문 없이) / 맞춤 제작 두 경로
  - 시험지 제출 → 관리자 승인 → 쿠폰 발급 → 주문에서 할인 적용까지 한 줄로
  - 관리자 화면에서 상품·교재·분류·공지·설정을 고치면 고객 화면에 반영되는지
  - 백업 내려받기·되돌리기
  - 로그인 잠금과 파일 경로 탈출 차단
"""
from __future__ import annotations

import io
import json
import pathlib
import os
import re
import shutil
import tempfile
from pathlib import Path

# 실제 store_data 를 건드리지 않도록, 복사본을 만들어 그쪽을 보게 합니다.
_TMP = Path(tempfile.mkdtemp())
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "store_data"


def _skip_real_files(folder, names):
    """설정(JSON)만 복사하고, 실제로 파는·나눠 주는 파일은 가져오지 않습니다.

    사장님이 자료를 넣어 두시면 그게 테스트 결과를 바꿔 버립니다.
    파일이 필요한 테스트는 각자 만들어 씁니다.
    """
    here = Path(folder).name
    if here in ("free", "deliverables", "samples", "submissions", "lineup", ".cache"):
        return [n for n in names if n != ".gitkeep"]
    return []


shutil.copytree(_SRC, _TMP / "store_data", dirs_exist_ok=True, ignore=_skip_real_files)
os.environ["STORE_DB"] = str(_TMP / "store_data" / "store.db")
os.environ.setdefault("ADMIN_PASSWORD", "test1234")

import store_common as sc  # noqa: E402

# 파일을 쓰는 경로는 하나도 빠짐없이 임시 폴더로 돌려 놓아야 합니다.
sc.DATA_DIR = _TMP / "store_data"
sc.SAMPLE_DIR = sc.DATA_DIR / "samples"
sc.SUBMIT_DIR = sc.DATA_DIR / "submissions"
sc.DELIVER_DIR = sc.DATA_DIR / "deliverables"
sc.FREE_DIR = sc.DATA_DIR / "free"
sc.SHOT_DIR = sc.DATA_DIR / "lineup"
sc.DB_PATH = sc.DATA_DIR / "store.db"

import store  # noqa: E402

store.app.config["TESTING"] = True
# 테스트는 한 대에서 폼을 수십 번 보내므로 남용 제한을 꺼 둡니다.
# 제한 자체는 test_public_forms_are_rate_limited 에서 따로 확인합니다.
sc.FORM_MAX = 100000


def client():
    return store.app.test_client()


def admin():
    c = client()
    assert c.post("/admin/login", data={"password": "test1234"}).status_code == 302
    return c


def body(resp) -> str:
    return resp.get_data(as_text=True)


# ---- 1. 고객 페이지 --------------------------------------------------------
def test_public_pages_open():
    c = client()
    for path, must in [
        ("/", "지문분석지"),
        ("/products", "자료 목록"),
        ("/lineup", "오르티카잉 라인업"),
        ("/free", "무료 자료"),
        ("/custom", "자료 요청"),
        ("/submit", "시험지"),
        ("/notice", "자료는 언제 올라오나요"),
        ("/pass", "프리패스"),
        ("/guide", "환불 규정"),
    ]:
        resp = c.get(path)
        assert resp.status_code == 200, f"{path} 가 열리지 않습니다"
        assert must in body(resp), f"{path} 에 '{must}' 가 없습니다"
    # 예전 '무료 샘플' 목록 주소는 라인업으로 넘겨 줍니다 (검색에 걸린 주소가 끊기지 않게)
    moved = c.get("/samples")
    assert moved.status_code == 301 and "/lineup" in moved.headers["Location"]
    assert c.get("/products/없는상품").status_code == 404
    assert c.get("/books/없는교재").status_code == 404
    print("PASS  고객 페이지 열림")


def test_categories_include_textbook():
    text = body(client().get("/products"))
    for name in ("교과서", "모의고사", "EBS 부교재", "형광펜 독해"):
        assert name in text, name
    print("PASS  분류 4종(교과서 포함) 노출")


def test_lineup_shows_all_materials():
    """라인업에 있는 자료가 그룹별로 하나도 빠짐없이 나와야 합니다."""
    text = body(client().get("/lineup"))
    mats = sc.load_materials()["materials"]
    for m in mats:
        assert m["name"] in text, m["name"]
    for group in ("지문 이해", "시그니처 자료", "시험 대비", "어휘"):
        assert group in text, group
    # 번호는 1부터 빠짐없이 이어져야 합니다 (자료를 더해도 어긋나지 않게)
    assert [m["no"] for m in mats] == [f"{i:02d}" for i in range(1, len(mats) + 1)]
    assert "필자의 생각이 보이는 영어독해" in text              # 시그니처 묶음 제목
    assert 'lineup-group dark' in text                          # 그 묶음만 진한 배경
    assert "SIGNATURE" in text and "주문제작자료" in text        # 표시
    assert "읽고 · 뜯어보고" in text                             # 머리말
    print(f"PASS  오르티카잉 라인업 {len(mats)}종 · 묶음 · 표시 노출")


def test_home_reflects_lineup():
    text = body(client().get("/"))
    assert "고등영어자료는" in text and "오르티카잉" in text          # 머리말
    assert "곁에 두는 선생님 같은 자료" in text                     # 학생 쪽
    assert "이것만 해도 충분하다는 확신" in text                    # 선생님 쪽
    assert "평가원 9개년의 설계 원리" in text
    assert "17종 변형문제" in text and "/lineup#variants" in text
    assert "3종 세트" not in text     # 옛 문구가 남아 있으면 안 됩니다
    print("PASS  홈이 라인업을 반영")


def test_two_packages_per_book():
    """교재마다 '지문 분석 패키지'와 '문제 패키지' 두 개가 있어야 합니다."""
    def own(html):                      # 짝 패키지 안내 앞부분 = 이 상품의 구성
        return html.split("같은 교재의")[0]

    analysis = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert "지문 분석 패키지" in analysis
    for name in ("한줄해석", "한줄영어", "좌지문우해석", "지문분석지", "필생보"):
        assert name in own(analysis), name
    for name in ("통합 영어 워크북", "17종 변형문제", "서술형 대비 교재"):
        assert name not in own(analysis), f"분석 패키지에 {name} 이 섞였습니다"

    problem = body(client().get("/products/mock-2026-06-g3-problem"))
    assert "문제 패키지" in problem
    for name in ("통합 영어 워크북", "서술형 대비 교재", "17종 변형문제"):
        assert name in own(problem), name
    for name in ("한줄해석", "좌지문우해석", "필생보"):
        assert name not in own(problem), f"문제 패키지에 {name} 이 섞였습니다"
    assert "/lineup#variants" in problem      # 라인업 설명으로 이어지는 링크
    print("PASS  교재마다 분석 · 문제 패키지 두 갈래")


def test_sibling_package_cross_sell():
    """분석 패키지를 보면 같은 교재의 문제 패키지를 권해 줘야 합니다."""
    text = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert "같은 교재의 문제 패키지도 있습니다" in text
    assert "/products/mock-2026-06-g3-problem" in text
    back = body(client().get("/products/mock-2026-06-g3-problem"))
    assert "같은 교재의 지문 분석 패키지도 있습니다" in back
    print("PASS  짝 패키지 서로 권하기")


def test_textbook_subjects_are_the_four():
    """교과서는 공통영어1 · 공통영어2 · 영어1 · 영어2 로 나눕니다."""
    from urllib.parse import quote
    page = body(client().get("/products?category=textbook"))
    want = ["공통영어1", "공통영어2", "영어1", "영어2"]
    at = [page.find("subject=" + quote(v)) for v in want]
    assert all(i > 0 for i in at), at          # 자료가 아직 없는 과목도 보입니다
    assert at == sorted(at), "적어 둔 차례대로 나와야 합니다"

    # '영어1' 을 골랐는데 '공통영어1' 이 딸려 나오면 안 됩니다
    one = body(client().get("/products?category=textbook&subject=영어1"))
    assert "등록된 자료가 없습니다" in one, "이름이 겹쳐 딸려 나왔습니다"
    common = body(client().get("/products?category=textbook&subject=공통영어1"))
    assert "능률(김성곤) 공통영어 1" in common

    # 학년처럼 '고1~고2' 로 걸친 값은 그대로 두 갈래에 다 걸립니다
    with store.app.app_context():
        catalog = sc.load_raw_catalog()
    keep = {x["slug"]: x.get("grade") for x in catalog["products"]
            if x.get("book") == "mock-2026-03-g2"}
    for x in catalog["products"]:
        if x.get("book") == "mock-2026-03-g2":
            x["grade"] = "고1~고2"
    sc.save_catalog(catalog)
    try:
        for g in ("고1", "고2"):
            got = body(client().get(f"/products?category=mock&grade={g}"))
            assert "2026년 3월 학력평가" in got, g
    finally:
        catalog = sc.load_raw_catalog()
        for x in catalog["products"]:
            if x["slug"] in keep:
                x["grade"] = keep[x["slug"]]
        sc.save_catalog(catalog)
    print("PASS  교과서 과목 네 가지 · 이름이 겹쳐도 안 딸려 나옴")


def test_material_chips_are_coloured_by_package():
    """자료 딱지 색은 시그니처가 아니라 '어느 패키지에 드는가' 로 갈립니다."""
    with store.app.app_context():
        where = sc.material_package()
    pkgs = {p["id"]: p["materials"] for p in sc.load_catalog()["packages"]}
    assert where["analysis"] == "analysis" and where["variants"] == "problem"
    # 두 패키지에 겹쳐 든 자료는 먼저 나오는 쪽으로 묶습니다 (색이 셋이 되면 안 됩니다)
    for mid in ("wordlist", "wordtest"):
        assert mid in pkgs["analysis"] and mid in pkgs["problem"]
        assert where[mid] == "analysis", mid

    page = body(client().get("/products?category=ebs"))
    assert "mat-chip pk-analysis" in page and "mat-chip pk-problem" in page
    assert "sig-chip" not in page, "시그니처로 색을 가르던 것이 남아 있습니다"

    css = body(client().get("/static/store.css"))
    assert ".mat-chip.pk-analysis" in css and ".mat-chip.pk-problem" in css
    assert ".mat-chip.sig-chip" not in css
    # 두 색이 서로 달라야 갈립니다
    a = css.split(".mat-chip.pk-analysis{")[1].split("}")[0]
    b = css.split(".mat-chip.pk-problem{")[1].split("}")[0]
    assert a != b, (a, b)
    print("PASS  자료 딱지 색을 패키지로 가름")


def test_package_filter():
    """패키지로 거르면 그 갈래에 든 자료만 남아야 합니다."""
    # 교재 칸에 걸리는 자료 딱지로 봅니다 (안내 문구에도 같은 말이 나오니
    # 번호까지 붙은 딱지 모양을 그대로 찾습니다)
    # 딱지에는 번호 없이 이름만 붙습니다
    mats = sc.material_map()
    chip = lambda mid: f'pk-{sc.material_package()[mid]}">{mats[mid]["name"]}'
    only_analysis = body(client().get("/products?package=analysis"))
    assert chip("analysis") in only_analysis
    assert chip("variants") not in only_analysis

    only_problem = body(client().get("/products?package=problem"))
    assert chip("variants") in only_problem
    assert chip("analysis") not in only_problem
    print("PASS  목록에서 패키지로 필터링")


def test_products_grouped_by_book():
    """같은 교재의 두 패키지가 카드 한 장에 나란히 묶여야 합니다."""
    text = body(client().get("/products"))
    # 교재 이름은 한 번만, 그 아래 패키지 두 개
    assert text.count("능률(김성곤) 공통영어 1") == 1
    head = text.split("찾으시는 교재가 없나요")[0]
    assert head.count('class="book-group"') >= 5
    assert "지문 분석 패키지" in head and "문제 패키지" in head
    print("PASS  자료 목록이 교재별로 묶임")


def test_grade_filter_and_sort():
    """학년 버튼과 정렬 버튼이 실제로 걸러 주고 줄 세워야 합니다.

    학년은 모의고사에서만 씁니다. 교과서·EBS 부교재는 책 이름에 이미 학년이
    들어 있어 학년 필터링이 군더더기입니다.
    """
    mock = body(client().get("/products?category=mock"))
    assert '<span class="filter-label">학년</span>' in mock
    go2 = body(client().get("/products?category=mock&grade=고2"))
    assert "2026년 3월 학력평가 (고2)" in go2
    assert "2026학년도 6월 모의평가 (고3)" not in go2     # 고3 회차는 빠져야 합니다

    # 교과서는 학년이 아니라 과목으로 갈립니다
    book = body(client().get("/products?category=textbook"))
    assert '<span class="filter-label">학년</span>' not in book
    assert '<span class="filter-label">과목</span>' in book
    assert ">공통영어1</a>" in book
    assert "능률(김성곤) 공통영어 1" in body(
        client().get("/products?category=textbook&subject=공통영어1"))
    # 그 분류에 없는 과목을 넣으면 아무것도 안 남습니다
    none = body(client().get("/products?category=textbook&subject=영어2"))
    assert "능률(김성곤) 공통영어 1" not in none

    # 학년을 주소에 붙여도 교과서에서는 걸러지지 않습니다 (갈래가 과목이므로)
    assert "능률(김성곤) 공통영어 1" in body(
        client().get("/products?category=textbook&grade=고3"))

    # 갈래가 없는 분류와 '전체' 에서는 그 줄이 아예 안 나옵니다
    for url in ("/products", "/products?category=ebs"):
        page = body(client().get(url))
        assert '<span class="filter-label">학년</span>' not in page, url
        assert '<span class="filter-label">과목</span>' not in page, url

    # 다른 버튼을 눌러도 고른 갈래가 따라갑니다
    assert "subject=%EA%B3%B5%ED%86%B5%EC%98%81%EC%96%B41" in body(
        client().get("/products?category=textbook&subject=공통영어1"))

    import re
    cheap = body(client().get("/products?order=price"))
    # 교재 카드마다 가장 싼 값 = 첫 번째 가격. 그 값이 오름차순이어야 합니다.
    cards = cheap.split('class="book-group"')[1:]
    firsts = [int(re.search(r'<span class="price">([\d,]+)원</span>', c)
                  .group(1).replace(",", "")) for c in cards if "price" in c]
    assert firsts == sorted(firsts), firsts
    # 갈래는 관리자 화면에서 켜고 끕니다 (여럿 고를 수 있어 체크박스입니다)
    a = admin()
    page = body(a.get("/admin/books"))
    assert 'name="splits"' in page
    for label in ("학년", "과목", "시행년도", "시행월"):
        assert f"<span>{label}</span>" in page, label
    assert 'name="subject"' in body(a.get("/admin/books/neungyule-kim/edit"))

    a.post("/admin/categories", data={"action": "rename", "id": "ebs",
                                      "name": "EBS 부교재", "splits": "grade"},
           follow_redirects=True)
    assert '<span class="filter-label">학년</span>' in body(client().get("/products?category=ebs"))
    a.post("/admin/categories", data={"action": "rename", "id": "ebs",
                                      "name": "EBS 부교재"}, follow_redirects=True)
    assert '<span class="filter-label">학년</span>' not in body(
        client().get("/products?category=ebs"))
    print("PASS  분류 안 갈래 — 모의고사는 학년 · 교과서는 과목")


def test_popular_order():
    """'인기순' 은 실제로 값을 치른 주문 수로 줄을 세웁니다."""
    a = admin()
    hot = "mock-2026-03-g2-analysis"          # 이 자료를 세 번 팔아 봅니다
    mild = "mock-2026-06-g3-analysis"

    def buy(slug, email):
        c = client()
        r = c.post("/order", data={"slug": slug, "name": "인기테스트",
                                   "phone": "010-1111-2222", "email": email, "agree": "1"})
        assert r.status_code == 302
        key = r.headers["Location"].rsplit("/", 1)[-1]
        row = sc.sqlite3.connect(sc.DB_PATH).execute(
            "SELECT id FROM orders WHERE view_key = ?", (key,)).fetchone()
        return row[0]

    # 다른 시험이 먼저 팔아 둔 것이 있을 수 있어, 늘어난 만큼으로 봅니다
    with store.app.test_request_context():
        base = sc.sold_counts()

    # 값을 안 치른 주문은 인기에 안 들어갑니다
    buy(hot, "notpaid@example.com")
    with store.app.test_request_context():
        assert sc.sold_counts().get(hot, 0) == base.get(hot, 0)

    for i in range(3):
        oid = buy(hot, f"hot{i}@example.com")
        a.post(f"/admin/orders/{oid}", data={"status": "입금확인"})
    oid = buy(mild, "mild@example.com")
    a.post(f"/admin/orders/{oid}", data={"status": "입금확인"})

    with store.app.test_request_context():
        counts = sc.sold_counts()
    assert counts[hot] - base.get(hot, 0) == 3
    assert counts[mild] - base.get(mild, 0) == 1
    assert counts[hot] > counts[mild]

    # 버튼이 있고, 많이 팔린 교재가 앞에 옵니다
    page = body(client().get("/products?order=popular"))
    assert ">인기순</a>" in page
    head = page.split("찾으시는 교재가 없나요")[0]
    # 교재 칸은 칸 전체가 링크라, 제목에 <a> 가 따로 없습니다
    names = re.findall(r'class="bg-open"[\s\S]*?<h3>([^<]+)</h3>', head)
    assert names, head[:200]
    assert names[0].startswith("2026년 3월 학력평가"), names[:3]
    assert "아직 판매 기록이 없어" not in page          # 판 자료가 있으니 안내가 없어야 합니다
    print("PASS  인기순 — 값을 치른 주문이 많은 자료가 앞에")


def test_book_page_splits_lanes():
    text = body(client().get("/books/mock-2026-06-g3"))
    assert "지문 분석 패키지" in text and "문제 패키지" in text
    assert "읽고 뜯어보는 자료" in text          # 갈래 설명
    print("PASS  교재 페이지가 두 갈래로 갈림")


def test_search_finds_by_publisher_and_book():
    """강사는 '능률' 처럼 교재 이름 일부만 칩니다. 그걸로 찾아져야 합니다."""
    import re
    def names(html):                       # 검색 결과에 실제로 뜬 상품 이름만
        head = html.split("찾으시는 교재가 없나요")[0]
        # 교재 칸(칸 전체가 링크) 과 낱개 자료 카드(제목이 링크) 를 모두 봅니다
        return (re.findall(r'class="bg-open"[\s\S]*?<h3>([^<]+)</h3>', head)
                + re.findall(r"<h3><a [^>]*>([^<]+)</a></h3>", head))

    hit = names(body(client().get("/products?q=능률")))
    assert hit and all("능률" in n for n in hit), hit

    # 출판사(EBS)로도 찾아집니다
    ebs = names(body(client().get("/products?q=EBS")))
    assert ebs and all(("수능특강" in n or "수능완성" in n) for n in ebs), ebs

    # 없는 것을 치면 자료 요청으로 안내
    miss = body(client().get("/products?q=없는교재이름"))
    assert "찾은 자료가 없습니다" in miss and "자료 요청하기" in miss
    print("PASS  교재·출판사 검색")


def test_share_and_branding():
    """카톡·밴드에 링크를 뿌렸을 때 제대로 보여야 합니다."""
    home = body(client().get("/"))
    assert 'property="og:image"' in home and "og.png" in home
    assert 'name="twitter:card"' in home
    assert 'property="og:url"' in home and 'property="og:site_name"' in home
    assert "🌿" not in home                      # 이모지 로고를 걷어냈는지
    assert 'class="logo-mark"' in home           # 자체 마크로 바뀌었는지

    assert client().get("/static/og.png").status_code == 200
    assert client().get("/static/favicon.svg").status_code == 200
    print("PASS  공유 썸네일 · 자체 로고")


def test_book_page_lists_only_its_products():
    text = body(client().get("/books/mock-2026-06-g3"))
    assert "2026학년도 6월 모의평가" in text
    assert "3월 학력평가" not in text.split("같은 분류의 다른 교재")[0]
    print("PASS  교재별 페이지가 해당 교재 자료만 보여 줌")


def test_home_links_every_category_and_search_word():
    """홈에서 분류·학년·무료 자료로 한 번에 갈 수 있어야 합니다.

    검색으로 들어온 사람이 첫 화면에서 자기가 찾던 말을 봐야 안 나갑니다.
    """
    text = body(client().get("/"))
    for cid in ("textbook", "mock", "ebs", "highlighter"):
        assert f"category={cid}" in text, cid
    from urllib.parse import quote
    for grade in ("고1", "고2", "고3"):
        assert f"grade={quote(grade)}" in text, grade
    for word in ("한줄해석", "좌지문우해석", "17종 변형문제", "동형모의고사"):
        assert word in text, word
    print("PASS  홈에서 분류·학년·무료 자료로 바로 가기")


def test_pass_twelve_month_price():
    text = body(client().get("/pass"))
    assert "220,000원" in text
    print("PASS  프리패스 12개월 220,000원")


def test_pass_preorder_discount():
    """사전 신청 할인은 12개월권에만 붙습니다.

    짧은 요금제까지 같은 금액을 깎으면 한 달만 끊어 전부 내려받는 쪽이 이득이 됩니다.
    """
    text = body(client().get("/pass"))
    assert "12개월권을 사전 신청하시면" in text and "30,000원을 깎아 드립니다" in text
    assert "정가 220,000원" in text and "190,000원" in text      # 12개월 — 깎임
    assert "정가 99,000원" not in text and "69,000원" not in text   # 3개월 — 정가 그대로
    assert "39,000원" in text and "정가 39,000원" not in text       # 1개월 — 정가 그대로
    assert text.count("사전 신청 −30,000원") == 1
    # 월 환산도 깎인 값 기준이어야 합니다 (220,000 → 190,000 이면 18,333 → 15,833)
    assert "월 15,833원 꼴" in text and "월 18,333원 꼴" not in text
    # 배지가 없는 요금제는 자리만 비워 둡니다 (동그라미가 보이면 안 됩니다)
    assert 'class="badge" style="visibility:hidden;"' in text

    # 실제 판매로 바꾸면 정가로 돌아가야 합니다
    site = json.loads((sc.DATA_DIR / "site.json").read_text(encoding="utf-8"))
    site["pass"]["mode"] = "sale"
    (sc.DATA_DIR / "site.json").write_text(json.dumps(site, ensure_ascii=False), encoding="utf-8")
    sale = body(client().get("/pass"))
    assert "깎아 드립니다" not in sale and "정가 220,000원" not in sale
    site["pass"]["mode"] = "preorder"
    (sc.DATA_DIR / "site.json").write_text(json.dumps(site, ensure_ascii=False), encoding="utf-8")
    print("PASS  프리패스 사전 신청 30,000원 할인")


def test_pass_preorder_records_promised_price():
    """사전 신청을 받으면 약속한 가격이 주문 기록에 남아야 합니다."""
    resp = client().post("/pass", data={
        "plan": "12개월", "name": "김선생", "email": "teacher@example.com",
        "phone": "010-2222-3333", "agree": "1"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "사전 신청이 접수되었습니다" in body(resp)
    row = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT detail_json FROM orders WHERE kind='pass' ORDER BY id DESC LIMIT 1").fetchone()
    detail = json.loads(row[0])
    assert detail["정가"] == 220000 and detail["사전 신청가"] == 190000
    assert detail["약속한 할인"] == 30000
    print("PASS  사전 신청에 약속한 가격이 기록됨")


# ---- 2. 주문 --------------------------------------------------------------
def test_order_rejects_bad_input():
    resp = client().post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "홍길동",
        "phone": "010-1234-5678", "email": "이메일아님"})
    assert resp.status_code == 400
    assert "이메일 주소를 정확히" in body(resp)
    assert "동의해 주셔야" in body(resp)
    print("PASS  잘못된 주문서 반려")


def test_order_saves_and_multiplies_amount():
    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "홍길동",
        "phone": "010-1234-5678", "email": "teacher@example.com", "agree": "1"})
    assert resp.status_code == 302
    done = body(c.get(resp.headers["Location"]))
    want = next(p["price"] for p in sc.load_catalog()["products"]
                if p["slug"] == "mock-2026-06-g3-analysis")
    assert f"{want:,}원" in done, want
    # 디지털 자료라 부수 개념이 없습니다. 대신 몇 번째 구매인지로 깎아 줍니다.
    form = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert 'name="quantity"' not in form
    assert "결제하실 금액" in form
    print("PASS  주문 저장 · 금액 표시")


def test_order_both_packages_at_once():
    """두 패키지를 사려고 주문을 두 번 하게 만들면 안 됩니다."""
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    one, two = price["mock-2026-06-g3-analysis"], price["mock-2026-06-g3-problem"]
    form = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert "문제 패키지도 함께 받기" in form and f"+{two:,}원" in form

    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "also": "1", "name": "둘다",
        "phone": "010-1212-3434", "email": "both@example.com", "agree": "1"})
    assert resp.status_code == 302
    done = body(c.get(resp.headers["Location"]))
    # 두 패키지를 더한 값. 2개까지는 정가입니다 (3개부터 할인)
    assert f"{one + two:,}원" in done
    assert "지문 분석 패키지" in done and "문제 패키지" in done

    key = resp.headers["Location"].rsplit("/", 1)[-1]
    row = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT extra_slugs FROM orders WHERE view_key = ?", (key,)).fetchone()
    assert row[0] == "mock-2026-06-g3-problem"
    print("PASS  두 패키지 한 번에 주문")


def test_order_rejects_unknown_coupon():
    resp = client().post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "홍길동", "phone": "010-1234-5678",
        "email": "a@b.com", "agree": "1", "coupon": "ORT-XXXX-XXXX"})
    assert resp.status_code == 400
    assert "쿠폰 코드가 없습니다" in body(resp)
    print("PASS  없는 쿠폰 코드 반려")


# ---- 3. 자료 요청 / 맞춤 제작 ---------------------------------------------
def test_request_needs_no_passage():
    """지문을 하나도 주지 않아도 자료 요청이 접수되어야 합니다."""
    resp = client().post("/custom", data={
        "mode": "request", "wanted": "비상(홍민표) 공통영어1 2과",
        "name": "김선생", "phone": "01098765432", "email": "kim@example.com", "agree": "1"})
    assert resp.status_code == 200
    assert "자료 요청이 접수되었습니다" in body(resp)
    assert "따로 보내실 자료는 없습니다" in body(resp)
    print("PASS  지문 없이 자료 요청 접수")


def test_custom_request_accepted():
    resp = client().post("/custom", data={
        "mode": "custom", "wanted": "학원 자체 교재", "passage_count": "20개",
        "materials": ["분석지"], "name": "박선생", "phone": "01011112222",
        "email": "park@example.com", "agree": "1"})
    assert "맞춤 제작 문의가 접수되었습니다" in body(resp)
    print("PASS  맞춤 제작 의뢰 접수")


def test_request_requires_wanted():
    resp = client().post("/custom", data={
        "mode": "request", "name": "김선생", "phone": "01098765432",
        "email": "kim@example.com", "agree": "1"})
    assert resp.status_code == 400
    assert "찾으시는지 적어 주세요" in body(resp)
    print("PASS  교재 이름 없으면 반려")


def test_submit_takes_photos_by_drag_and_drop():
    """시험지 보내기 — 폰으로 찍거나 끌어다 놓아 여러 장을 보낼 수 있어야 합니다."""
    import io as _io
    page = body(client().get("/submit"))
    assert 'class="dropzone"' in page and "끌어다 놓기" in page
    assert 'name="files"' in page and "multiple" in page
    assert "add(e.dataTransfer.files)" in page            # 끌어다 놓은 것이 담깁니다
    # 폰에서 바로 찍을 수 있어야 하고, 찍은 사진은 앞의 것에 이어 붙습니다
    assert 'capture="environment"' in page and 'id="shot"' in page
    assert "사진 찍기" in page
    assert "new DataTransfer()" in page                  # 이어 붙이는 자리
    # 쿠폰은 메일로 가니 이메일은 꼭 받습니다
    email = page[page.index('id="email"'):page.index('id="email"') + 200]
    assert "required" in email
    assert "쿠폰 코드를 이 주소로 보내 드립니다" in page

    c = client()
    resp = c.post("/submit", data={
        "school": "여러장고", "grade": "고2", "exam_type": "기말고사",
        "files": [(_io.BytesIO(b"%PDF-1.4 a"), "1쪽.pdf"),
                  (_io.BytesIO(b"\x89PNG\r\n\x1a\n"), "2쪽.png"),
                  (_io.BytesIO(b"\x89PNG\r\n\x1a\n"), "3쪽.png")],
        "name": "박선생", "phone": "010-5555-6666", "email": "many@example.com",
        "agree": "1", "agree_source": "1"}, content_type="multipart/form-data")
    assert resp.status_code == 200 and "시험지 잘 받았습니다" in body(resp)

    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM submissions WHERE email = 'many@example.com'").fetchone()
    names = row["file_name"].split(", ")
    assert len(names) == 3, names
    assert all(n.startswith(row["submit_no"]) for n in names), names   # 이름은 우리가 붙입니다
    for n in names:
        assert (sc.SUBMIT_DIR / n).is_file()

    # 관리자 화면에 올라온 만큼 다 걸리고, 눌러 받을 수 있습니다
    a = admin()
    listed = body(a.get("/admin/submissions"))
    for n in names:
        assert n in listed, n
    assert a.get(f"/admin/submissions/file/{names[0]}").status_code in (200, 302)

    # 파일도 링크도 없으면 반려합니다
    none = client().post("/submit", data={
        "school": "빈손고", "name": "홍", "phone": "010-1-2",
        "email": "none@example.com", "agree": "1", "agree_source": "1"})
    assert none.status_code == 400 and "올리거나" in body(none)

    for n in names:
        (sc.SUBMIT_DIR / n).unlink(missing_ok=True)
    print("PASS  시험지 보내기 — 찍거나 끌어다 놓아 여러 장")


# ---- 4. 시험지 제출 → 쿠폰 → 할인 (한 줄로) -------------------------------
def test_submission_to_coupon_to_discount():
    c = client()
    resp = c.post("/submit", data={
        "school": "대치고등학교", "grade": "고3", "exam_type": "중간고사",
        "exam_term": "2026년 1학기", "scope": "수능특강 1~5강",
        "files": [(io.BytesIO(b"%PDF-1.4 fake"), "exam.pdf"),
                  (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "2쪽.png")],
        "name": "이선생", "phone": "010-3333-4444", "email": "lee@example.com",
        "agree": "1", "agree_source": "1"},
        content_type="multipart/form-data")
    assert resp.status_code == 200 and "시험지 잘 받았습니다" in body(resp)

    a = admin()
    listed = body(a.get("/admin/submissions"))
    assert "대치고등학교" in listed and "검토대기" in listed

    row = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT id FROM submissions ORDER BY id DESC LIMIT 1").fetchone()
    assert a.post(f"/admin/submissions/{row[0]}",
                  data={"status": "승인"}).status_code == 302

    coupon = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT code, value FROM coupons ORDER BY id DESC LIMIT 1").fetchone()
    assert coupon and coupon[1] == 5000

    # 발급된 쿠폰으로 실제 할인이 되어야 합니다.
    checked = client().get(f"/coupon/check?code={coupon[0]}&amount=22000").get_json()
    assert checked["ok"] and checked["discount"] == 5000 and checked["final"] == 17000

    c2 = client()
    resp = c2.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "이선생", "phone": "010-3333-4444",
        "email": "lee@example.com", "agree": "1", "coupon": coupon[0]})
    assert resp.status_code == 302
    want = next(p["price"] for p in sc.load_catalog()["products"]
                if p["slug"] == "mock-2026-06-g3-analysis") - 5000
    assert f"{want:,}원" in body(c2.get(resp.headers["Location"]))   # 쿠폰 5,000원

    # 한 번 쓴 쿠폰은 다시 못 씁니다.
    again = client().get(f"/coupon/check?code={coupon[0]}&amount=22000").get_json()
    assert not again["ok"] and "이미 사용" in again["message"]
    print("PASS  시험지 제출 → 승인 → 쿠폰 → 할인 → 재사용 차단")


def test_submission_requires_file_or_link():
    resp = client().post("/submit", data={
        "school": "○○고", "name": "이선생", "phone": "010-3333-4444",
        "email": "lee@example.com", "agree": "1", "agree_source": "1"})
    assert resp.status_code == 400
    assert "파일을 올리거나" in body(resp)
    print("PASS  파일도 링크도 없으면 반려")


# ---- 4-2. 입금 확인 → 다운로드 링크 → 파일 받기 ---------------------------
def test_order_to_download_flow():
    """자료를 올리고, 주문을 받고, 링크를 내고, 실제로 파일을 받기까지."""
    a = admin()
    slug = "mock-2026-06-g3-analysis"

    # 파일이 없으면 링크를 낼 수 없어야 합니다.
    c = client()
    resp = c.post("/order", data={
        "slug": slug, "name": "다운로드테스트", "phone": "010-5555-6666",
        "email": "dl@example.com", "agree": "1"})
    assert resp.status_code == 302
    key = resp.headers["Location"].rsplit("/", 1)[-1]
    conn = sc.sqlite3.connect(sc.DB_PATH)
    row = conn.execute("SELECT id, order_no FROM orders WHERE view_key = ?", (key,)).fetchone()
    order_no = row[1]
    a.post(f"/admin/orders/{row[0]}/deliver")
    assert sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT COUNT(*) FROM downloads WHERE order_no = ?",
        (order_no,)).fetchone()[0] == 0, "파일 없이 링크가 나갔습니다"

    # 파일을 올립니다.
    up = a.post(f"/admin/products/{slug}/files", data={
        "files": [(io.BytesIO(b"%PDF-1.4 analysis"), "지문분석지.pdf"),
                  (io.BytesIO(b"PK\x03\x04zip"), "묶음.zip")]},
        content_type="multipart/form-data")
    assert up.status_code == 302
    assert "지문분석지.pdf" in body(a.get(f"/admin/products/{slug}/files"))

    # 올릴 수 없는 형식은 막힙니다.
    bad = a.post(f"/admin/products/{slug}/files", data={
        "files": (io.BytesIO(b"nope"), "hack.exe")}, content_type="multipart/form-data")
    assert bad.status_code == 302
    # 거부 안내에는 파일 이름이 나오므로, 실제로 저장됐는지로 확인합니다.
    assert "hack.exe" not in [f["name"] for f in sc.product_files(slug)]

    # 이제 링크를 냅니다. 주문은 발송완료가 되어야 합니다.
    assert a.post(f"/admin/orders/{row[0]}/deliver").status_code == 302
    dl = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT token, order_no FROM downloads ORDER BY id DESC LIMIT 1").fetchone()
    assert dl and dl[1] == order_no
    status = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT status FROM orders WHERE order_no = ?", (order_no,)).fetchone()[0]
    assert status == "발송완료"

    # 손님이 링크로 들어가 파일을 받습니다.
    page = client().get(f"/d/{dl[0]}")
    assert page.status_code == 200
    assert "지문분석지.pdf" in body(page) and order_no in body(page)
    # 파일은 이름 순으로 매겨지므로 PDF 가 몇 번째인지 찾아서 받습니다.
    names = [f["name"] for f in sc.product_files(slug)]
    idx = names.index("지문분석지.pdf")

    # 기본은 '보기 + 파일 받기 둘 다' 입니다. 파일을 달라면 그대로 줍니다.
    got = client().get(f"/d/{dl[0]}/{idx}")
    assert got.status_code == 200, got.status_code
    # ZIP 같은 것은 화면에서 못 여니 언제나 그대로 받습니다
    zidx = names.index("묶음.zip")
    assert client().get(f"/d/{dl[0]}/{zidx}").status_code == 200

    # '화면 인쇄만' 으로 잠그면 PDF 는 파일로 안 나갑니다
    site = sc.load_site(); site["delivery"] = {"mode": "view"}; sc.save_site(site)
    assert client().get(f"/d/{dl[0]}/{idx}").status_code == 302
    site["delivery"] = {"mode": "both"}; sc.save_site(site)
    got = client().get(f"/d/{dl[0]}/{idx}")
    assert got.status_code == 200, got.status_code
    assert got.data.startswith(b"%PDF"), got.data[:20]
    site["delivery"] = {"mode": "view"}; sc.save_site(site)

    # 엉뚱한 토큰과 폴더 밖 요청은 막힙니다.
    assert client().get("/d/없는토큰").status_code == 404
    assert client().get(f"/d/{dl[0]}/99").status_code == 404
    print("PASS  파일 올리기 → 링크 발급 → 손님이 받기")


def test_deliver_by_external_link():
    """파일을 안 올리고 구글 드라이브 링크만 걸어도 팔 수 있어야 합니다."""
    a = admin()
    slug = "mock-2026-06-g3-problem"          # 파일을 올리지 않은 상품
    assert not sc.product_files(slug)

    # http 로 시작하지 않는 주소는 걸러집니다.
    a.post(f"/admin/products/{slug}/links", data={
        "link_name": ["잘못된 주소"], "link_url": ["drive.google.com/abc"]})
    saved = next(x for x in sc.load_raw_catalog()["products"] if x["slug"] == slug)
    assert saved.get("file_links") == []

    a.post(f"/admin/products/{slug}/links", data={
        "link_name": ["6월 모평 문제 패키지", ""],
        "link_url": ["https://drive.google.com/file/demo", ""]})
    saved = next(x for x in sc.load_raw_catalog()["products"] if x["slug"] == slug)
    assert len(saved["file_links"]) == 1

    c = client()
    resp = c.post("/order", data={
        "slug": slug, "name": "링크손님", "phone": "010-9090-1010",
        "email": "link@example.com", "agree": "1"})
    key = resp.headers["Location"].rsplit("/", 1)[-1]
    oid, order_no = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT id, order_no FROM orders WHERE view_key = ?", (key,)).fetchone()
    assert a.post(f"/admin/orders/{oid}/deliver").status_code == 302

    token = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT token FROM downloads WHERE order_no = ?", (order_no,)).fetchone()[0]
    page = body(client().get(f"/d/{token}"))
    assert "6월 모평 문제 패키지" in page
    assert "https://drive.google.com/file/demo" in page
    print("PASS  파일 없이 링크만으로 판매 · 발송")


def test_download_revoke_and_limit():
    a = admin()
    dl = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT id, token FROM downloads ORDER BY id DESC LIMIT 1").fetchone()

    # 횟수를 다 쓰면 막힙니다.
    conn = sc.sqlite3.connect(sc.DB_PATH)
    conn.execute("UPDATE downloads SET download_count = max_downloads WHERE id = ?", (dl[0],))
    conn.commit()
    assert "횟수를 다 쓰셨습니다" in body(client().get(f"/d/{dl[1]}"))
    conn.execute("UPDATE downloads SET download_count = 0 WHERE id = ?", (dl[0],))
    conn.commit()

    # 관리자가 막으면 못 받습니다.
    assert a.post(f"/admin/downloads/{dl[0]}/revoke").status_code == 302
    assert client().get(f"/d/{dl[1]}").status_code == 404
    assert client().get(f"/d/{dl[1]}/0").status_code == 404
    print("PASS  다운로드 횟수 제한 · 링크 차단")


# ---- 4-3. 세금 · 증빙 ------------------------------------------------------
def test_receipt_request_and_sales():
    c = client()
    # 증빙을 고르고 번호를 안 적으면 반려됩니다.
    bad = c.post("/order", data={
        "slug": "mock-2026-06-g3-problem", "name": "학원장", "phone": "010-7777-8888",
        "email": "academy@example.com", "agree": "1", "receipt_kind": "tax_invoice"})
    assert bad.status_code == 400 and "사업자등록번호나 휴대폰 번호" in body(bad)

    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-problem", "name": "학원장", "phone": "010-7777-8888",
        "email": "academy@example.com", "affiliation": "오르티카잉학원", "agree": "1",
        "receipt_kind": "tax_invoice", "receipt_no": "123-45-67890"})
    assert resp.status_code == 302
    key = resp.headers["Location"].rsplit("/", 1)[-1]

    a = admin()
    conn = sc.sqlite3.connect(sc.DB_PATH)
    oid = conn.execute("SELECT id FROM orders WHERE view_key = ?", (key,)).fetchone()[0]
    a.post(f"/admin/orders/{oid}", data={"status": "입금확인"})

    page = body(a.get("/admin/sales"))
    assert "123-45-67890" in page and "세금계산서" in page
    paid = next(p["price"] for p in sc.load_catalog()["products"]
                if p["slug"] == "mock-2026-06-g3-problem")
    assert f"{paid:,}원" in page                     # 문제 패키지 결제금액
    net = round(paid / 1.1)                          # 공급가액 · 부가세
    assert f"{net:,}원" in page and f"{paid - net:,}원" in page

    assert a.post(f"/admin/orders/{oid}/receipt").status_code == 302
    assert "123-45-67890" not in body(a.get("/admin/sales"))   # 발행 대기에서 빠짐

    csv = body(a.get("/admin/orders.csv"))
    assert "공급가액" in csv and "부가세" in csv and "증빙종류" in csv
    print("PASS  증빙 요청 → 매출 집계 → 발행 처리 → CSV")


# ---- 5. 관리자 잠금 --------------------------------------------------------
def test_every_admin_route_is_locked():
    """관리자 주소를 하나도 빠짐없이 훑어, 로그인 없이는 못 들어가는지 확인합니다."""
    c = client()
    checked = 0
    for rule in store.app.url_map.iter_rules():
        if not rule.rule.startswith("/admin"):
            continue
        if rule.endpoint in ("admin.login", "admin.logout", "static"):
            continue
        # <int:order_id> 같은 자리는 아무 값이나 넣어 봅니다.
        path = re.sub(r"<[^>]+>", "1", rule.rule)
        for method in ("GET", "POST"):
            if method not in rule.methods:
                continue
            resp = c.open(path, method=method)
            assert resp.status_code == 302, f"{method} {path} 가 {resp.status_code} 로 열렸습니다"
            assert "/admin/login" in resp.headers.get("Location", ""), path
            checked += 1
    assert checked >= 40, f"검사한 주소가 {checked}개뿐입니다"
    print(f"PASS  관리자 주소 {checked}개 전부 잠김")


def test_login_blocks_repeated_guesses():
    """비밀번호를 계속 찍으면 막혀야 합니다."""
    import store_admin
    store_admin._login_tries.clear()
    c = client()
    for _ in range(store_admin.LOGIN_MAX_TRIES):
        assert c.post("/admin/login", data={"password": "틀린비번"}).status_code == 401
    blocked = c.post("/admin/login", data={"password": "틀린비번"})
    assert blocked.status_code == 429 and "분 뒤에 다시" in body(blocked)
    # 막힌 동안에는 맞는 비밀번호도 안 받습니다.
    assert c.post("/admin/login", data={"password": "test1234"}).status_code == 429
    store_admin._login_tries.clear()
    assert c.post("/admin/login", data={"password": "test1234"}).status_code == 302
    print("PASS  비밀번호 무차별 대입 차단")


def test_admin_not_indexed_and_login_is_standalone():
    resp = admin().get("/admin")
    assert "noindex" in resp.headers.get("X-Robots-Tag", "")
    assert "no-store" in resp.headers.get("Cache-Control", "")
    assert resp.headers.get("X-Frame-Options") == "DENY"

    login = body(client().get("/admin/login"))
    assert 'name="robots"' in login and "noindex" in login
    assert "오르티카잉 라인업" not in login       # 고객 메뉴가 딸려 나오지 않아야 함

    robots = body(client().get("/robots.txt"))
    assert "Disallow: /admin" in robots and "Disallow: /d/" in robots
    print("PASS  관리자·다운로드 주소 검색 차단, 로그인 화면 분리")


def test_login_next_cannot_leave_admin():
    """로그인 뒤 엉뚱한 사이트로 튕겨 보내는 수법을 막습니다."""
    c = client()
    resp = c.post("/admin/login?next=https://evil.example.com",
                  data={"password": "test1234"})
    assert resp.status_code == 302
    assert "evil.example.com" not in resp.headers["Location"]
    assert resp.headers["Location"].endswith("/admin/")
    print("PASS  로그인 후 이동 주소 제한")


def test_setup_checklist_guides_first_day():
    """첫날 관리자 화면이 '무엇부터 하라'를 순서로 보여 줘야 합니다."""
    text = body(admin().get("/admin"))
    assert "문 열기까지" in text and "단계 남았습니다" in text
    for step in ("연락처와 입금 계좌 넣기", "내 상품 등록하기",
                 "상품에 판매할 파일 올리기", "자료 샘플 PDF 올리기",
                 "무료 자료 한 건 올리기", "네이버 · 구글에 사이트 등록하기"):
        assert step in text, step
    assert "지금 사이트에 보이는 상품은 예시입니다" in text     # 예시 데이터 경고 상자
    print("PASS  첫날 준비 체크리스트")


def test_clear_sample_data():
    a = admin()
    before = len(sc.load_raw_catalog()["products"])
    assert before and any(p.get("sample") for p in sc.load_raw_catalog()["products"])

    # 내가 만든 상품은 남아야 합니다.
    a.post("/admin/products/new", data={
        "slug": "my-real-product", "name": "진짜 상품", "category": "mock",
        "price": "10000", "active": "1", "package": "analysis"})
    assert a.post("/admin/products/clear-samples").status_code == 302

    left = sc.load_raw_catalog()["products"]
    assert [p["slug"] for p in left] == ["my-real-product"]
    assert not sc.load_raw_catalog()["books"]
    # 예시가 없어지면 경고 상자도 사라집니다.
    assert "지금 사이트에 보이는 상품은 예시입니다" not in body(a.get("/admin"))
    print("PASS  예시 데이터 한 번에 지우기 (내 상품은 남김)")


def _wipe_visits():
    with store.app.app_context():
        sc.get_db().execute("DELETE FROM visits")
        sc.get_db().commit()


PHONE = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2) Safari/605"}


def _visits():
    with store.app.app_context():
        return [dict(r) for r in sc.get_db().execute(
            "SELECT * FROM visits ORDER BY id")]


def test_footprints_count_people_not_files():
    """손님이 어느 화면을 보셨는지 남기되, 누구인지는 안 남겨야 합니다."""
    _wipe_visits()
    c = client()
    c.get("/", headers=PHONE)
    c.get("/products?category=mock", headers=PHONE)
    c.get("/products?q=수능특강", headers=PHONE)
    c.get("/products/neungyule-kim-analysis", headers=PHONE)
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"}, headers=PHONE)

    rows = _visits()
    seen = [(r["endpoint"], r["kind"]) for r in rows]
    assert ("home", "page") in seen and ("cart_add", "action") in seen
    assert [r["cat"] for r in rows if r["cat"]] == ["mock"]
    assert [r["q"] for r in rows if r["q"]] == ["수능특강"]
    assert "neungyule-kim-analysis" in [r["slug"] for r in rows]

    # 남는 것은 화면 주소와 시각뿐입니다. 주소(IP)도 이메일도 안 남습니다.
    assert set(rows[0]) == {"id", "at", "day", "vid", "endpoint", "kind",
                            "cat", "slug", "q", "ref"}
    # 표는 그날치 소금으로 뒤섞은 값이라, 날이 바뀌면 이어지지 않습니다
    a = sc.visit_id("소금", "1.2.3.4", "브라우저", "2026-09-07")
    b = sc.visit_id("소금", "1.2.3.4", "브라우저", "2026-09-08")
    assert a != b and "1.2.3.4" not in a and len(a) == 16
    assert a == sc.visit_id("소금", "1.2.3.4", "브라우저", "2026-09-07")

    # 세지 않는 것 — 관리자 · 기계가 읽는 주소 · 파일 · 사람 아닌 접속
    _wipe_visits()
    admin().get("/admin/traffic")
    client().get("/robots.txt", headers=PHONE)
    client().get("/healthz", headers=PHONE)
    client().get("/sitemap.xml", headers=PHONE)
    client().get("/", headers={"User-Agent": "Googlebot/2.1 (+http://google.com)"})
    client().get("/", headers={"User-Agent": "python-requests/2.31"})
    client().get("/", headers={"User-Agent": ""})
    client().get("/", headers={})          # 시험 도구(Werkzeug)도 사람이 아닙니다
    assert _visits() == [], _visits()

    # 없는 주소(404)도 안 셉니다 — 있지도 않은 화면이 인기 화면이 되면 안 됩니다
    client().get("/없는화면", headers=PHONE)
    assert _visits() == []
    print("PASS  발자국은 화면만 · 누구인지는 안 남김")


def test_footprints_tell_where_people_come_from():
    """어디서 오셨는지. 우리 사이트 안에서 옮겨 다닌 것은 안 셉니다."""
    assert sc.ref_source("https://search.naver.com/x", "ortica.com") == "네이버"
    assert sc.ref_source("https://www.google.co.kr/", "ortica.com") == "구글"
    assert sc.ref_source("", "ortica.com") == "직접 · 즐겨찾기"
    # 우리 집 안에서 옮겨 다닌 것 (포트가 붙어 들어와도 알아봐야 합니다)
    assert sc.ref_source("https://ortica.com/lineup", "ortica.com:5000") == ""
    assert sc.ref_source("https://www.ortica.com/x", "ortica.com") == ""
    # 이름만 비슷한 남의 집은 우리 집이 아닙니다
    assert sc.ref_source("https://notortica.com/x", "ortica.com") == "notortica.com"

    _wipe_visits()
    c = client()
    c.get("/", headers=PHONE, environ_base={"HTTP_REFERER": "https://m.search.naver.com/s"})
    c.get("/lineup", headers=PHONE, environ_base={"HTTP_REFERER": "http://localhost/"})
    with store.app.app_context():
        refs = {r["key"]: r["views"] for r in sc.visits_top("ref", 7)}
    assert refs == {"네이버": 1}, refs
    print("PASS  어디서 오셨나 · 우리 안에서 옮긴 것은 안 셈")


def test_footprints_show_where_people_stop():
    """사는 데까지 어느 칸에서 줄어드는지 — 고칠 자리를 찾는 데 씁니다."""
    _wipe_visits()
    c = client()
    c.get("/products", headers=PHONE)
    c.get("/products/neungyule-kim-analysis", headers=PHONE)
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"}, headers=PHONE)
    with store.app.app_context():
        steps = {f["label"]: f["people"] for f in sc.visits_funnel(7)}
        assert steps["자료를 보러 옴"] == 1
        assert steps["자료를 들여다봄"] == 1
        assert steps["장바구니에 담음"] == 1
        assert steps["주문서까지 감"] == 0, "안 간 칸을 갔다고 하면 안 됩니다"
        # 오래된 발자국은 저절로 지워집니다
        sc.get_db().execute(
            """INSERT INTO visits (at, day, vid, endpoint, kind, cat, slug, q, ref)
               VALUES ('2020-01-01T00:00:00', '2020-01-01', 'x', 'home', 'page',
                       '', '', '', '')""")
        sc.get_db().commit()
        assert sc.prune_visits() == 1
        assert not [r for r in _visits() if r["day"] == "2020-01-01"]
    print("PASS  사는 데까지 · 오래된 발자국 치우기")


def test_traffic_numbers_never_reach_customers():
    """통계는 관리자 화면에서만 보여야 합니다.

    손님이 '지금 3명이 보고 있습니다' 를 보면 장사가 안 되는 것까지 같이
    보입니다. 세는 것과 보여 주는 것은 다른 일이라, 세더라도 손님 화면에는
    한 숫자도 새면 안 됩니다.
    """
    _wipe_visits()
    c = client()
    for _ in range(3):
        c.get("/", headers=PHONE)
        c.get("/products?q=수능특강", headers=PHONE)
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"}, headers=PHONE)

    # 잠겨 있어야 합니다 — 로그인 없이는 못 봅니다
    for url in ("/admin/traffic", "/admin/traffic?days=7"):
        got = client().get(url)
        assert got.status_code == 302, url
        assert "/admin/login" in got.headers.get("Location", ""), url

    # 손님 화면 어디에도 숫자가 안 나옵니다
    words = ("발자국", "지금 보고 계신", "오신 분", "본 화면", "사는 데까지",
             "많이 본 화면", "찾으신 말", "어디서 오셨나", "visits")
    for url in ("/", "/products", "/products?category=mock", "/lineup", "/free",
                "/notice", "/guide", "/cart", "/words", "/contact",
                "/books/ybm-han", "/products/neungyule-kim-analysis",
                "/sitemap.xml", "/robots.txt"):
        page = body(c.get(url, headers=PHONE))
        for w in words:
            assert w not in page, f"{url} 에 '{w}' 가 새어 나갑니다"

    # 통계를 읽는 길은 관리자 화면 하나뿐이어야 합니다
    src = (_ROOT / "store.py").read_text() + (_ROOT / "store_common.py").read_text()
    for fn in ("visits_now", "visits_span", "visits_top", "visits_funnel",
               "visits_by_day"):
        assert f"sc.{fn}(" not in src, f"손님 쪽 코드가 {fn} 를 읽고 있습니다"
    for tpl in (_ROOT / "store_templates").glob("*.html"):
        assert "visits" not in tpl.read_text(), tpl.name
    _wipe_visits()
    print("PASS  통계는 관리자 화면에서만")


def test_admin_traffic_screen_reads_at_a_glance():
    """통계 화면은 숫자만이 아니라 '무엇을 고칠지' 를 말해 줘야 합니다."""
    _wipe_visits()
    c = client()
    for _ in range(3):
        c.get("/products?category=mock", headers=PHONE)
    c.get("/products?q=고1 3월", headers=PHONE)

    page = body(admin().get("/admin/traffic"))
    assert "손님 발자국" in page
    assert "지금 보고 계신 분" in page
    assert "모의고사" in page, "분류 이름을 사람 말로 보여야 합니다"
    assert "고1 3월" in page, "찾으신 말이 있어야 다음에 만들 자료를 압니다"
    assert "자료 목록" in page and "products" not in page.split("많이 본 화면")[1][:600]
    assert "누구인지는 안 남깁니다" in page
    # 기간을 바꿔 볼 수 있어야 합니다
    for d in (7, 30, 90):
        assert f"days={d}" in page
    assert admin().get("/admin/traffic?days=999").status_code == 200
    _wipe_visits()
    print("PASS  관리자 통계 화면")


def test_submit_page_promises_only_a_coupon():
    """시험지를 보내 주시면 무엇이 돌아오는지, 지킬 수 있는 것만 적어야 합니다.

    '더 정확한 자료로 돌려드립니다' 는 보내 주신 그 시험지를 고쳐서 돌려주는
    것처럼 읽힙니다. 실제로 돌아가는 것은 할인 쿠폰이고, 시험지는 앞으로
    만드는 자료의 난이도·유형을 맞추는 데 씁니다.
    """
    page = body(client().get("/submit"))
    assert "할인 쿠폰으로 돌려드립니다" in page
    assert "더 정확한 자료로 돌려" not in page, "못 지킬 약속입니다"
    assert "나눠 주시면" not in page, "보내 주시는 것이지 나눠 주시는 것이 아닙니다"
    # 무엇이 돌아오는지 · 무엇은 안 돌아오는지를 둘 다 적습니다
    assert "고쳐서 돌려드리는 것은 아니" in page
    assert "앞으로 만드는" in page
    assert "재배포하지 않습니다" in page

    # 자료 파일과 서식 기본값이 서로 딴말을 하면 안 됩니다
    head = sc.load_site()["submit_reward"]["headline"]
    assert "돌려드립니다" in head and "정확한 자료로" not in head
    tpl = (_ROOT / "store_templates" / "submit.html").read_text()
    assert head in tpl, "자료 파일이 비면 서식 기본값이 나오는데, 둘이 다릅니다"

    # 돌아가는 사이트의 자료 파일에는 옛 문구가 이미 심겨 있습니다. 파일을
    # 고치는 것만으로는 안 내려가니, 토씨가 같을 때만 코드가 바로잡습니다.
    for bad, good in sc.RETIRED_COPY.items():
        assert bad != good and "더 정확한 자료로" not in good
    raw = sc.load_json("site.json", {})
    keep = raw["submit_reward"]["headline"]
    raw["submit_reward"]["headline"] = "학교 시험지를 나눠 주시면, 더 정확한 자료로 돌려드립니다"
    sc.save_json("site.json", raw)
    try:
        assert sc.load_site()["submit_reward"]["headline"] == \
            "학교 시험지를 보내 주시면, 할인 쿠폰으로 돌려드립니다"
        assert "나눠 주시면" not in body(client().get("/submit"))
        # 사장님이 손수 쓰신 글은 건드리지 않습니다
        raw["submit_reward"]["headline"] = "시험지 주시면 쿠폰 드려요"
        sc.save_json("site.json", raw)
        assert sc.load_site()["submit_reward"]["headline"] == "시험지 주시면 쿠폰 드려요"
    finally:
        raw["submit_reward"]["headline"] = keep
        sc.save_json("site.json", raw)
    print("PASS  시험지 보내기 — 돌아오는 것은 쿠폰")


def test_word_study_is_reachable_from_the_menu():
    """화면에서 바로 푸는 기능이 눌러서 닿는 자리에 있어야 합니다.

    만들어 두고 링크를 안 걸면 없는 기능입니다. 단어장 목록은 '시험지 만들기'
    화면으로만 들어오므로, 거기에 길이 없으면 아무도 못 찾습니다.
    """
    c = client()
    # 머리말에 제 자리가 있어야 합니다 — 내 자료함과 같은 층, 그림 단추로.
    home = body(c.get("/"))
    assert 'class="study-link' in home and 'href="/study"' in home
    assert 'aria-label="학습"' in home                 # 단어와 지문을 함께 담는 자리
    head = home[home.index("head-cta"):home.index("</header>")]
    for must in ("/cart", "/study", "/my"):                # 장바구니 · 단어 학습 · 자료함
        assert must in head, must

    # 그 자리를 누르면 교재를 고르는 화면이 열립니다
    study = body(c.get("/study"))
    for must in ("단어 학습", "지문 암기", "시험지 뽑기"):
        assert must in study, must                     # 세 갈래를 맨 위에서 가름
    slug0 = sc.load_words()["books"][0]["slug"]
    assert f"/words/{slug0}/study" in study, "책 카드가 바로 풀기로 가야 합니다"

    # 무엇을 어떻게 할지 먼저 고릅니다 — 뜻만 볼지, 철자까지 쓸지, 깜빡이로 훑을지
    setup = body(c.get(f"/words/{slug0}/study"))
    for way in ("뜻 고르기", "철자 채우기", "둘 다 섞기", "깜빡이"):
        assert way in setup, way
    quiz = body(c.get(f"/words/{slug0}/study?kind=choice&n=5"))
    assert "sq-choices" in quiz and "뜻 고르기" not in quiz.split("sq-play")[0][-400:]
    flash = body(c.get(f"/words/{slug0}/study?mode=flash&n=5"))
    assert "fl-card" in flash and "깜빡이" in flash

    # 메뉴 → 단어장 목록 → 책 고르기 → 여기서도 '단어 풀기' 가 보여야 합니다
    assert "/words" in home
    listing = body(c.get("/words"))
    slug = sc.load_words()["books"][0]["slug"]
    assert f"/words/{slug}" in listing
    landed = body(c.get(f"/words/{slug}/make"))
    assert f"/words/{slug}/study" in landed, "시험지 만들기 화면에 길이 없습니다"
    assert "화면에서 바로 풀어 보기" in landed

    # 범위 고르는 화면에도 그대로 있습니다
    assert f"/words/{slug}/study" in body(c.get(f"/words/{slug}"))
    # 눌러 가면 실제로 열립니다
    assert c.get(f"/words/{slug}/study").status_code == 200
    print("PASS  단어 학습 — 머리말 그림 단추 · 시험지 화면 둘 다에서 닿음")


def test_admin_menu_is_short():
    """관리자 메뉴는 자주 여는 것만 밖에 나와 있어야 합니다.

    19개가 한 줄로 늘어서 있으면 메뉴가 벽이 됩니다. 겹치는 화면은 합치고,
    한 번 해 두면 그만인 것은 접어 두었습니다.
    """
    page = body(admin().get("/admin"))
    nav = page[page.index('adm-nav'):page.index('adm-side-foot')]
    daily, rare = nav.split("가끔 여는 것", 1)

    # 밖에 나와 있는 것 — 매일·매주 여는 것만
    for must in ("오늘 할 일", "주문 · 문의", "시험지 · 쿠폰", "매출 · 지표",
                 "손님 발자국", "상품", "교재 · 분류", "오르티카잉 라인업",
                 "무료 자료실", "단어장", "지문", "공지", "메일 · 명단"):
        assert must in daily, must
    assert daily.count('</a>') == 13, daily.count('</a>')

    # 접힌 칸 — 한 번 해 두면 그만인 것
    for later in ("가게 정보", "가격 가이드", "빠진 것 점검", "검색 등록", "백업"):
        assert later in rare, later

    # 합친 화면은 메뉴에서 사라졌습니다 (주소로 확인 — 이름은 합친 쪽에 남아 있습니다)
    for gone in ("/admin/metrics", "/admin/coupons", "/admin/leads"):
        assert gone not in nav, gone

    # 그래도 옛 주소로 오시면 합쳐진 자리로 보내 드립니다
    a = admin()
    for old, new in [("/admin/metrics", "/admin/sales"),
                     ("/admin/coupons", "/admin/submissions"),
                     ("/admin/leads", "/admin/mail")]:
        resp = a.get(old)
        assert resp.status_code == 302 and resp.headers["Location"].endswith(new), old
    print("PASS  관리자 메뉴 11개 · 가끔 쓰는 것은 접어 둠")


def test_admin_pages_open():
    a = admin()
    for path, must in [
        ("/admin", "오늘 할 일"),
        ("/admin/orders", "주문 · 문의"),
        ("/admin/submissions", "시험지 제출"),
        ("/admin/submissions", "쿠폰 목록"),        # 쿠폰은 시험지 화면으로 합쳤습니다
        ("/admin/products", "새 상품 만들기"),
        ("/admin/books", "교재 · 분류"),
        ("/admin/sales", "월별 매출"),
        ("/admin/mail", "이메일 명단"),             # 명단은 메일 화면으로 합쳤습니다
        ("/admin/products/mock-2026-06-g3-analysis/files", "손님에게 보낼 파일"),
        ("/admin/materials", "오르티카잉 라인업"),
        ("/admin/materials/analysis", "특징 묶음 제목"),
        ("/admin/notices", "새 공지 쓰기"),
        ("/admin/settings", "입금 계좌"),
        ("/admin/backup", "전체 백업 받기"),
    ]:
        resp = a.get(path)
        assert resp.status_code == 200, f"{path} [{resp.status_code}]"
        assert must in body(resp), f"{path} 에 '{must}' 가 없습니다"
    print("PASS  관리자 화면 전부 열림")


# ---- 6. 관리자에서 고친 내용이 고객 화면에 반영되는지 ----------------------
def test_admin_forms_offer_buttons_not_typing():
    """관리자에서 직접 타이핑할 일이 최대한 없어야 합니다."""
    a = admin()
    form = body(a.get("/admin/products/new"))
    # 학년·배지·형식·발송·가격이 버튼으로 나와야 합니다.
    for label in ("고3", "인기", "PDF (A4, 인쇄용)", "자주 쓰는 값", "맨 위"):
        assert label in form, label
    assert 'data-target="grade"' in form and 'data-target="badge"' in form
    # 이름·주소는 자동으로 만들어지므로 처음엔 못 쓰게 잠겨 있어야 합니다.
    assert "교재와 패키지를 고르면 자동으로 만들어집니다" in form
    assert form.count("readonly") >= 3

    bookform = body(a.get("/admin/books/new"))
    for label in ("평가원", "EBS", "능률(NE)", "고1~고2"):
        assert label in bookform, label

    coupon = body(a.get("/admin/submissions"))     # 쿠폰 만들기는 여기로 옮겼습니다
    for label in ("5,000원", "10%", "석 달", "기한 없음", "첫 구매 감사"):
        assert label in coupon, label

    notice = body(a.get("/admin/notices"))
    assert "자주 쓰는 문장" in notice and 'data-target="tag"' in notice

    settings = body(a.get("/admin/settings"))
    for label in ("카카오뱅크", "기본 문구 넣기"):
        assert label in settings, label
    print("PASS  관리자 폼이 타이핑 대신 버튼으로")


def test_admin_creates_product_visible_on_site():
    a = admin()
    resp = a.post("/admin/products/new", data={
        "slug": "test-new-set", "name": "테스트 신규 세트", "subtitle": "시험용",
        "category": "mock", "book": "mock-2026-06-g3", "price": "12345",
        "list_price": "20000", "sort": "1", "active": "1",
        "includes": "분석지\n어휘 리스트", "highlights": "장점 하나",
        "description": "관리자 화면에서 만든 상품입니다.",
        "format": "PDF", "delivery": "24시간 이내"})
    assert resp.status_code == 302

    detail = client().get("/products/test-new-set")
    assert detail.status_code == 200
    assert "12,345원" in body(detail) and "관리자 화면에서 만든 상품" in body(detail)
    assert "/products/test-new-set" in body(client().get("/books/mock-2026-06-g3"))

    # 숨기면 고객 화면에서 사라집니다.
    assert a.post("/admin/products/test-new-set/toggle").status_code == 302
    assert client().get("/products/test-new-set").status_code == 404

    assert a.post("/admin/products/test-new-set/delete").status_code == 302
    assert "test-new-set" not in body(a.get("/admin/products"))
    print("PASS  상품 만들기 → 사이트 반영 → 숨김 → 삭제")


def test_admin_edits_material_and_site_reflects():
    a = admin()
    resp = a.post("/admin/materials/oneline-ko", data={
        "no": "01", "name": "한줄해석", "en": "Line-by-line KO", "group": "understand",
        "tagline": "테스트로 바꾼 한 줄 소개", "active": "1",
        "variant_name": ["원문만", ""], "variant_desc": ["설명", ""],
        "feature_title": ["새 특징"], "feature_body": ["새 특징 설명"],
        "for_whom": "테스트 대상자"})
    assert resp.status_code == 302
    text = body(client().get("/lineup"))
    assert "테스트로 바꾼 한 줄 소개" in text and "새 특징" in text
    print("PASS  오르티카잉 라인업 수정 → 고객 화면 반영")


def test_admin_product_materials_saved():
    a = admin()
    assert a.post("/admin/products/new", data={
        "slug": "test-mat-set", "name": "자료 선택 테스트", "category": "mock",
        "price": "10000", "sort": "1", "active": "1",
        "materials": ["analysis", "mocktest", "없는자료"],   # 없는 것은 걸러져야 합니다
        "format": "PDF", "delivery": "24시간"}).status_code == 302

    saved = next(x for x in sc.load_raw_catalog()["products"] if x["slug"] == "test-mat-set")
    assert saved["materials"] == ["analysis", "mocktest"]

    detail = body(client().get("/products/test-mat-set"))
    assert "지문분석지" in detail and "동형모의고사 2회" in detail
    assert "주문제작" in detail                    # 08 의 표시가 따라옵니다
    a.post("/admin/products/test-mat-set/delete")
    print("PASS  상품의 포함 자료 저장 · 없는 자료 걸러냄")


def test_admin_rejects_duplicate_slug():
    resp = admin().post("/admin/products/new", data={
        "slug": "mock-2026-06-g3-analysis", "name": "중복", "category": "mock", "price": "1000"})
    assert resp.status_code == 400
    assert "이미 다른 상품이 쓰고 있습니다" in body(resp)
    print("PASS  주소 이름 중복 반려")


def test_admin_book_and_category_flow():
    a = admin()
    assert a.post("/admin/categories",
                  data={"action": "add", "id": "workbook", "name": "부교재"}).status_code == 302
    assert "workbook" in [c["id"] for c in sc.load_raw_catalog()["categories"]]

    assert a.post("/admin/books/new", data={
        "slug": "test-book", "name": "테스트 교재", "category": "workbook",
        "publisher": "테스트출판", "grade": "고1", "sort": "1", "active": "1",
        "description": "설명"}).status_code == 302

    # 상품이 없는 교재는 고객 화면 목록에 안 나오지만 주소로는 열립니다.
    assert client().get("/books/test-book").status_code == 200

    # 그 상품이 쓰는 분류는 지울 수 없어야 합니다.
    a.post("/admin/categories", data={"action": "delete", "id": "workbook"})
    assert "workbook" in json.dumps(sc.load_raw_catalog(), ensure_ascii=False)

    assert a.post("/admin/books/test-book/delete").status_code == 302
    assert a.post("/admin/categories",
                  data={"action": "delete", "id": "workbook"}).status_code == 302
    # 화면 글자로 확인하면 기존 'EBS 부교재' 에 걸리므로 분류 아이디로 확인합니다.
    assert "workbook" not in [c["id"] for c in sc.load_raw_catalog()["categories"]]
    print("PASS  교재·분류 추가 → 사용 중 삭제 차단 → 정리")


def test_admin_notice_appears_on_home():
    a = admin()
    assert a.post("/admin/notices/save", data={
        "date": "2026-09-02", "tag": "업데이트", "title": "테스트 공지입니다",
        "body": "내용", "pinned": "1"}).status_code == 302
    assert "테스트 공지입니다" in body(client().get("/"))
    assert "테스트 공지입니다" in body(client().get("/notice"))
    assert a.post("/admin/notices/0/delete").status_code == 302
    print("PASS  공지 작성 → 홈 띠 반영 → 삭제")


def test_admin_settings_change_reaches_customer():
    a = admin()
    resp = a.post("/admin/settings", data={
        "brand": "오르티카잉", "tagline": "테스트 태그라인",
        "contact_email": "real@ortica.kr",
        "contact_kakao_url": "https://open.kakao.com/o/g0a1w2Li",
        "contact_kakao_label": "카카오톡 오픈채팅 문의",
        "contact_hours": "평일 10-19", "payment_bank_name": "국민은행",
        "payment_bank_account": "111-222-333444", "payment_bank_holder": "홍길동",
        "payment_notice": "곧 보내 드립니다",
        "business_company": "오르티카잉", "business_owner": "홍길동",
        "business_reg_no": "123-45-67890", "business_mailorder_no": "제2026-서울-1234호",
        "business_address": "서울시", "policy_refund": "환불규정", "policy_license": "이용범위",
        "policy_privacy": "개인정보", "pass_enabled": "1", "pass_mode": "preorder",
        "pass_headline": "제목", "pass_lead": "설명",
        "plan_name": ["12개월"], "plan_price": ["220000"], "plan_per_month": ["18333"],
        "plan_period": ["365일"], "plan_badge": [""], "plan_desc": ["설명"],
        "reward_enabled": "1", "reward_kind": "amount", "reward_value": "7000",
        "reward_min_amount": "10000", "reward_days_valid": "60",
        "reward_headline": "시험지 주세요", "reward_lead": "설명"})
    assert resp.status_code == 302

    home = body(client().get("/"))
    assert "real@ortica.kr" in home and "123-45-67890" in home
    assert "010-9999-8888" not in home        # 전화번호는 아예 안 받습니다
    assert "7,000원 할인" in body(client().get("/submit"))
    print("PASS  가게 정보 저장 → 고객 화면 반영")


def test_backup_download_and_restore():
    a = admin()
    dump = a.get("/admin/backup/download")
    assert dump.status_code == 200
    bundle = json.loads(dump.get_data(as_text=True))
    assert "products.json" in bundle and "site.json" in bundle

    # 지금 상품 하나를 지운 뒤, 백업으로 되돌리면 살아나야 합니다.
    catalog = sc.load_raw_catalog()
    keep = len(catalog["products"])
    catalog["products"] = catalog["products"][1:]
    sc.save_catalog(catalog)
    assert len(sc.load_raw_catalog()["products"]) == keep - 1

    resp = a.post("/admin/backup/restore", data={
        "file": (io.BytesIO(dump.get_data()), "backup.json")},
        content_type="multipart/form-data")
    assert resp.status_code == 302
    assert len(sc.load_raw_catalog()["products"]) == keep
    print("PASS  백업 내려받기 → 되돌리기")


def test_full_backup_has_orders():
    """전체 백업에는 주문 기록이 함께 들어가야 합니다. 설정만 받으면 주문이 날아갑니다."""
    import zipfile
    a = admin()
    # 주문을 하나 만들어 둡니다
    client().post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "백업테스트",
        "phone": "010-9999-8888", "email": "backup@example.com", "agree": "1"},
        follow_redirects=True)
    resp = a.get("/admin/backup/full")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resp.data)) as z:
        names = z.namelist()
        for want in ("설정/site.json", "주문내역.csv", "이메일명단.csv", "store.db", "읽어주세요.txt"):
            assert want in names, f"{want} 가 백업에 없습니다 — {names}"
        assert "백업테스트" in z.read("주문내역.csv").decode("utf-8")
        assert z.read("store.db")[:15] == b"SQLite format 3"
    print("PASS  전체 백업에 설정 · 주문 · 장부 원본이 다 들어감")


# ---- 7. 글꼴 · 보안 --------------------------------------------------------
def sheet_text(url: str) -> str:
    """시험지 PDF 를 받아 글자만 뽑습니다. 시험지는 이제 진짜 PDF 입니다."""
    import io as _io
    from pypdf import PdfReader
    pdf = client().get(url.replace("/sheet?", "/sheet.pdf?"))
    assert pdf.status_code == 200, url
    assert pdf.data[:4] == b"%PDF", "PDF 가 아닙니다"
    doc = PdfReader(_io.BytesIO(pdf.data))
    return "\n".join(pg.extract_text() for pg in doc.pages)


def sheet_pages(url: str) -> int:
    """시험지가 몇 쪽인지."""
    import io as _io
    from pypdf import PdfReader
    pdf = client().get(url.replace("/sheet?", "/sheet.pdf?"))
    return len(PdfReader(_io.BytesIO(pdf.data)).pages)


def test_word_quiz():
    """단어 시험지 — 관리자가 붙여넣으면 손님이 범위·유형을 골라 뽑습니다."""
    a = admin()
    # 단어장은 이름만 적으면 됩니다 (주소는 알아서 붙습니다)
    a.post("/admin/words/new", data={"name": "quiz test book", "publisher": "테스트"},
           follow_redirects=True)
    made = sc.load_raw_words()["books"][-1]
    assert made["slug"] == "quiz-test-book" and "grade" not in made
    words = "\n".join(f"word{i}\t뜻{i}" for i in range(1, 13))
    # 강도 이름 한 칸만. 번호는 이름에서 만듭니다 ('Day 47' → 47)
    r = a.post("/admin/words/quiz-test-book/unit",
               data={"unit_name": "Day 47", "words": words + "\n망한줄"},
               follow_redirects=True)
    assert "단어 12개를 넣었습니다" in body(r)
    assert "읽지 못한 줄 1개" in body(r)          # 뜻이 없는 줄은 건너뜁니다

    # 손님 화면
    assert sc.load_raw_words()["books"][-1]["units"][0]["id"] == "47"
    assert "quiz test book" in body(client().get("/words"))
    pick = body(client().get("/words/quiz-test-book"))
    assert "Day 47" in pick and "12개" in pick

    url = "/words/quiz-test-book/sheet?unit=47&kind=en_ko&kind=ko_en&kind=choice&count=4&seed=777"
    page = body(client().get(url))
    text = sheet_text(url)
    # 유형마다 한 장씩, 학생용 3장 + 정답지 3장
    assert sheet_pages(url) == 6
    assert "A4 세로 6쪽" in page and "학생용 3쪽, 정답지 3쪽" in page
    assert page.count("/sheet/") == 6           # 쪽마다 그림 한 장씩 보여 줍니다
    assert "PDF 받기" in page and "인쇄하기" in page
    # 인쇄는 PDF 를 새 창에 열어 줍니다 (모바일 앱 안에서는 window.print 가 없습니다)
    assert "window.print()" not in page
    assert page.count("/sheet.pdf?") == 2 and "open=1" in page
    for roman, title in (("Ⅰ", "영단어 → 우리말 뜻"), ("Ⅱ", "우리말 뜻 → 영단어"),
                         ("Ⅲ", "영단어 → 뜻 고르기")):
        assert f"{roman}." in text and title in text
    assert "첫 글자 힌트 제공" in text                            # 한→영 힌트 안내
    # 유형마다 4문항씩 · 학생용 3장 + 정답지 3장 = 01 번이 여섯 번 나옵니다
    assert text.count("01") >= 6 and "05" not in text.replace("2025", "")
    assert "정답이 채워진 답지입니다" in text
    assert "All rights reserved" in text
    assert "이름" in text and "점수" in text
    assert "시험지 번호 777" in page
    assert "noindex" in page

    # 같은 번호면 같은 시험지, 번호가 없으면 매번 다릅니다
    assert sheet_text(url) == text
    once = sheet_text(url.replace("&seed=777", ""))
    twice = sheet_text(url.replace("&seed=777", ""))
    assert once != twice

    # 쪽 그림도 진짜로 나옵니다
    png = client().get("/words/quiz-test-book/sheet/0.png"
                       "?unit=47&kind=en_ko&kind=ko_en&kind=choice&count=4&seed=777")
    assert png.status_code == 200 and png.data[:4] == b"\x89PNG"
    assert client().get("/words/quiz-test-book/sheet/99.png?unit=47&seed=777").status_code == 404

    # 단어가 다섯 개도 안 되면 객관식은 자동으로 빠집니다
    a.post("/admin/words/quiz-test-book/unit",
           data={"unit_name": "Day 48", "words": "solo\t혼자"}, follow_redirects=True)
    tiny = sheet_text("/words/quiz-test-book/sheet?unit=48&kind=choice&count=5")
    assert "고르세요" not in tiny

    # ---- 손님이 단어를 하나하나 골라서 ----------------------------------
    pick = body(client().get("/words/quiz-test-book/pick?unit=47"))
    assert "낼 단어 고르기" in pick
    assert pick.count('name="pick"') == 12          # 12개가 다 체크된 채로 나옵니다
    assert 'checked' in pick
    chosen = "&".join(f"pick={i}" for i in (0, 2, 4, 6))
    # 유형 둘을 골라도 고른 단어를 저마다 다 씁니다 (Day 하나로 두 방향 시험)
    both = sheet_text(f"/words/quiz-test-book/sheet?{chosen}&kind=en_ko&kind=ko_en&count=0")
    assert sheet_pages(f"/words/quiz-test-book/sheet?{chosen}&kind=en_ko&kind=ko_en&count=0") == 4
    assert both.count("총 4문항") == 4                # 2유형 × (학생용 + 정답지)

    only = sheet_text(f"/words/quiz-test-book/sheet?{chosen}&kind=en_ko&count=0")
    assert only.count("총 4문항") == 2                # 고른 4개 × (학생용 + 정답지)
    # 고른 것보다 적게 정하면 그중에서 뽑습니다
    few = sheet_text(f"/words/quiz-test-book/sheet?{chosen}&kind=en_ko&count=2")
    assert few.count("총 2문항") == 2

    a.post("/admin/words/quiz-test-book/delete", follow_redirects=True)
    assert "시험용 단어장" not in body(client().get("/words"))
    print("PASS  단어 시험지 — 붙여넣기 → 범위·유형 · 단어 골라서 → 학생용 + 정답지")


def test_save_sheet_to_my_locker():
    """만든 시험지를 자료함에 담고, 언제든 똑같이 다시 꺼냅니다."""
    a = admin()
    a.post("/admin/words/new", data={"name": "save test book"}, follow_redirects=True)
    a.post("/admin/words/save-test-book/unit",
           data={"unit_name": "3강",
                 "words": "\n".join(f"w{i}\t뜻{i}" for i in range(1, 21))},
           follow_redirects=True)

    args = "unit=03&kind=en_ko&n_en_ko=10&seed=4242&title=9월 어휘 확인&date=2026. 9. 5."
    c = client()

    # 이메일이 없거나 이상하면 안 담습니다
    assert c.post("/words/save-test-book/save",
                  data={"email": "not-a-mail", "args": args}).status_code == 400
    assert c.post("/words/save-test-book/save",
                  data={"email": "keep@example.com", "args": ""}).status_code == 400

    got = c.post("/words/save-test-book/save",
                 data={"email": "Keep@Example.com", "args": args}).get_json()
    assert got["ok"]
    # 이름은 시험지 제목과 날짜로 — 나중에 알아보실 수 있게
    assert got["name"] == "9월 어휘 확인 (2026. 9. 5.)"
    assert "/my/" in got["locker"]

    # 같은 것을 또 담아도 줄이 늘지 않습니다 (날짜만 새로 씀)
    c.post("/words/save-test-book/save",
           data={"email": "keep@example.com", "args": args})
    with store.app.app_context():
        rows = sc.my_sheets("keep@example.com")
    assert len(rows) == 1, [dict(r) for r in rows]
    assert rows[0]["questions"] == 10 and rows[0]["pages"] == 2
    assert rows[0]["book_name"] == "save test book" and rows[0]["scope"] == "3강"

    # 내 자료함에 보입니다
    locker = body(c.get(got["locker"]))
    assert "만들어 두신 단어 시험지" in locker
    assert "9월 어휘 확인 (2026. 9. 5.)" in locker
    assert "10문항" in locker and "2쪽" in locker
    assert "/words/save-test-book/sheet.pdf?" in locker

    # 눌러 보면 그때 그 시험지가 그대로 나옵니다
    again = sheet_text(f"/words/save-test-book/sheet?{args}")
    assert "9월 어휘 확인" in again and "2026. 9. 5." in again
    assert again == sheet_text(f"/words/save-test-book/sheet?{args}")

    # 제목을 안 적으면 교재와 범위로 이름을 짓습니다
    plain = c.post("/words/save-test-book/save",
                   data={"email": "keep@example.com",
                         "args": "unit=03&kind=en_ko&n_en_ko=5&seed=7"}).get_json()
    assert plain["name"].startswith("어휘 TEST · save test book · 3강 (")

    # 지우기 — 내 것만
    with store.app.app_context():
        rows = sc.my_sheets("keep@example.com")
        token = sc.locker_token("keep@example.com")
    c.post(f"/my/{token}/sheet/{rows[0]['id']}/delete", follow_redirects=True)
    with store.app.app_context():
        assert len(sc.my_sheets("keep@example.com")) == 1
        assert not sc.drop_sheet(rows[0]["id"], "other@example.com")

    # 만들기 화면에 담기 단추가 있습니다
    page = body(c.get("/words/save-test-book/make"))
    assert "내 자료함에 저장" in page and 'id="save-email"' in page

    a.post("/admin/words/save-test-book/delete", follow_redirects=True)
    print("PASS  단어 시험지 저장 — 제목·날짜로 이름 · 내 자료함에서 다시 꺼내기")


def test_make_screen_four_steps():
    """단어장 만들기 — 교재 · 어휘 · 설정 · 미리보기를 한 화면에서."""
    a = admin()
    a.post("/admin/words/new", data={"name": "make test book"}, follow_redirects=True)
    for no, pairs in ((1, [("alpha", "첫째"), ("beta", "둘째"), ("gamma", "셋째")]),
                      (2, [("delta", "넷째"), ("epsilon", "다섯째"), ("zeta", "여섯째")])):
        a.post("/admin/words/make-test-book/unit",
               data={"unit_name": f"{no}강",
                     "words": "\n".join(f"{e}\t{k}" for e, k in pairs)},
               follow_redirects=True)

    page = body(client().get("/words/make-test-book/make"))
    for step in ("STEP 1", "STEP 2", "STEP 3", "STEP 4"):
        assert step in page, step
    # 기본 순서 — 교재 → 강 → 유형별 문항 수 → 설정·미리보기
    # (머리말 소개글에도 같은 말이 나오니 제목 표시를 그대로 찾습니다)
    order = ["<b>교재 선택</b>", "<b>강 선택</b>", "<b>유형별 문항 수</b>",
             "<b>시험지 설정 · 미리보기</b>"]
    seen = [page.index(x) for x in order]
    assert seen == sorted(seen), seen
    assert "1강" in page and "2강" in page                      # 강 칩
    assert page.count('class="chip u-chip"') == 2
    for label in sc.QUIZ_KINDS.values():
        assert label in page                                    # 유형 세 가지
    assert page.count('class="k-n"') == 3                       # 유형마다 문항 수 칸
    assert 'value="40"' in page and 'value="15"' in page        # 기본값

    # 단어 하나하나 고르기는 접어 두었습니다 (기본 길이 아닙니다)
    assert "단어를 하나하나 고르기" in page and "<details" in page
    assert page.count('class="w-box"') == 6                    # 펴면 단어 여섯 개
    assert page.index("유형별 문항 수") < page.index("단어를 하나하나 고르기")

    # 단어장 목록에서 이 화면으로 옵니다
    assert "/make" in body(client().get("/words"))

    # ---- 단어마다 유형을 정해 시험지를 냅니다 --------------------------
    url = ("/words/make-test-book/sheet?en_ko=0,1&ko_en=2,3&choice=4&seed=99"
           "&title=만들기+시험")
    text = sheet_text(url)
    assert "만들기 시험" in text
    assert "총 2문항" in text and "총 1문항" in text
    # 유형마다 정해 준 단어가 그 자리에 갑니다
    lines = text.split("Ⅱ.")
    assert "alpha" in lines[0] and "beta" in lines[0]           # Ⅰ. 영단어 → 뜻
    assert "셋째" in lines[1] and "넷째" in lines[1]             # Ⅱ. 뜻 → 영단어
    assert sheet_pages(url) == 6                               # 세 유형 × 학생용·정답지

    # 같은 번호면 같은 시험지
    assert sheet_text(url) == text

    # 쪽수를 물어보는 자리 (미리보기가 몇 장 걸지 정할 때 씁니다)
    got = client().get(url.replace("/sheet?", "/sheet/pages.json?")).get_json()
    assert got["pages"] == 6

    # 시험지 화면의 링크에도 고른 단어가 그대로 실립니다
    made = body(client().get(url))
    assert "en_ko=0%2C1" in made or "en_ko=0,1" in made
    assert "PDF 받기" in made

    # 없는 번호는 조용히 버립니다
    assert sheet_pages("/words/make-test-book/sheet?en_ko=0,999,-3&seed=1") == 2

    a.post("/admin/words/make-test-book/delete", follow_redirects=True)
    print("PASS  단어장 만들기 — 네 단계 · 단어마다 유형 · 바로 미리보기")


def test_wordbooks_are_grouped_by_publisher():
    """단어장은 EBS · 능률 · YBM · ETOOS 로 나뉘어 보여야 합니다."""
    assert sc.WORD_PUBLISHERS == ["EBS", "능률", "YBM", "ETOOS"], sc.WORD_PUBLISHERS

    a = admin()
    a.post("/admin/words/new", data={"name": "능률 테스트 단어장", "publisher": "능률"},
           follow_redirects=True)
    slug = sc.load_raw_words()["books"][-1]["slug"]
    a.post(f"/admin/words/{slug}/unit", data={
        "unit_name": "1강", "words": "apple\t사과\nbanana\t바나나"}, follow_redirects=True)

    groups = sc.words_by_publisher(sc.load_words()["books"])
    names = [g["name"] for g in groups]
    assert names[:4] == sc.WORD_PUBLISHERS, names   # 교재가 없어도 자리는 남습니다
    ebs = next(g for g in groups if g["name"] == "EBS")
    neung = next(g for g in groups if g["name"] == "능률")
    assert ebs["count"] >= 1 and neung["count"] == 1
    assert neung["words"] == 2

    page = body(client().get("/words"))
    for pub in sc.WORD_PUBLISHERS:
        assert f'>{pub}<' in page or f"{pub}<span" in page, pub
    assert "능률 테스트 단어장" in page
    # 아직 교재가 없는 곳은 숨기지 않고, 교재를 알려 달라고 합니다
    assert "준비하고 있습니다" in page and 'class="pub-tab' in page

    # 출판사가 없는 단어장은 '그 외' 로 갑니다 (사라지면 안 됩니다)
    a.post("/admin/words/new", data={"name": "출판사 없는 단어장", "publisher": ""},
           follow_redirects=True)
    etc_slug = sc.load_raw_words()["books"][-1]["slug"]
    a.post(f"/admin/words/{etc_slug}/unit", data={
        "unit_name": "1강", "words": "cat\t고양이"}, follow_redirects=True)
    groups = sc.words_by_publisher(sc.load_words()["books"])
    etc = next(g for g in groups if g["name"] == sc.WORD_PUBLISHER_ETC)
    assert etc["count"] == 1
    print("PASS  단어장을 출판사별로 — EBS · 능률 · YBM · ETOOS")


def test_word_counts_per_kind_and_cap():
    """문항 수는 유형마다 따로. 다 더해 500문항까지."""
    a = admin()
    a.post("/admin/words/new", data={"name": "cap test book"}, follow_redirects=True)
    big = "\n".join(f"w{i}\t뜻{i}" for i in range(1, 601))          # 600단어
    a.post("/admin/words/cap-test-book/unit",
           data={"unit_name": "Day 1", "words": big}, follow_redirects=True)

    # 유형마다 따로 정한 수가 그대로 나옵니다
    text = sheet_text("/words/cap-test-book/sheet"
                      "?unit=01&kind=en_ko&kind=ko_en&n_en_ko=30&n_ko_en=10&seed=5")
    assert "총 30문항" in text and "총 10문항" in text

    # 다 더해 500문항을 넘기면 뒤쪽 유형부터 깎습니다
    over = sheet_text("/words/cap-test-book/sheet"
                      "?unit=01&kind=en_ko&kind=ko_en&n_en_ko=400&n_ko_en=400&seed=5")
    import re as _re
    got = [int(x) for x in _re.findall(r"총 (\d+)문항", over)]
    assert sum(set(got)) == 500, got                      # 400 + 100
    assert 400 in got and 100 in got

    # 예전 주소가 쓰던 count 도 그대로 받습니다
    old_url = sheet_text("/words/cap-test-book/sheet"
                         "?unit=01&kind=en_ko&kind=ko_en&count=25&seed=5")
    assert old_url.count("총 25문항") == 4                 # 두 유형 × 학생용·정답지

    # 고르는 화면에 유형마다 문항 수 칸이 있어야 합니다
    pick = body(client().get("/words/cap-test-book"))
    for k, n in (("en_ko", 40), ("ko_en", 40), ("choice", 15)):
        assert f'name="n_{k}" value="{n}"' in pick, k
    assert "500문항까지" in pick

    a.post("/admin/words/cap-test-book/delete", follow_redirects=True)
    print("PASS  유형마다 문항 수 정하기 · 한 번에 500문항까지")


def test_word_file_upload():
    """단어를 엑셀·CSV·PDF 파일로 올리면, 읽은 내용을 보여 준 뒤에 저장합니다."""
    import io as _io
    a = admin()
    a.post("/admin/words/new", data={"name": "file test book"}, follow_redirects=True)

    # 엑셀 — 첫 줄 머리글은 알아서 뺍니다
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["영어", "뜻"])
    for en, ko in [("retain", "유지하다"), ("vary", "다르다, 달라지다"), ("seek", "추구하다")]:
        ws.append([en, ko])
    buf = _io.BytesIO(); wb.save(buf)
    r = a.post("/admin/words/file-test-book/upload",
               data={"unit_name": "Day 1",
                     "file": (_io.BytesIO(buf.getvalue()), "단어.xlsx")},
               content_type="multipart/form-data")
    page = body(r)
    assert "읽은 내용을 확인해 주세요" in page
    assert "단어 3개" in page                      # 머리글 한 줄이 빠졌습니다
    assert "retain\t유지하다" in page
    assert "영어\t뜻" not in page
    # 아직 저장 전입니다
    assert sc.word_count(sc.find_wordbook("file-test-book", raw=True)) == 0

    # CSV 도 같은 길로
    csv = "영어,뜻\nintensity,강도\nsolo,혼자\n".encode("utf-8-sig")
    assert "단어 2개" in body(a.post("/admin/words/file-test-book/upload",
        data={"unit_name": "Day 2", "file": (_io.BytesIO(csv), "단어.csv")},
        content_type="multipart/form-data"))

    # 올릴 수 없는 형식은 반려
    bad = a.post("/admin/words/file-test-book/upload",
                 data={"file": (_io.BytesIO(b"x"), "몰래.exe")},
                 content_type="multipart/form-data", follow_redirects=True)
    assert "올릴 수 없는 형식" in body(bad)

    # 미리보기에서 확인한 내용을 저장하면 그때 들어갑니다
    a.post("/admin/words/file-test-book/unit",
           data={"unit_name": "Day 1", "words": "retain\t유지하다\nvary\t다르다"},
           follow_redirects=True)
    assert sc.word_count(sc.find_wordbook("file-test-book", raw=True)) == 2

    # 끌어다 놓는 자리가 있어야 합니다
    page = body(a.get("/admin/words/file-test-book"))
    assert 'class="dropzone"' in page and "끌어다 놓으세요" in page
    assert "unit_id" not in page                      # 강 번호 칸은 없앴습니다

    a.post("/admin/words/file-test-book/delete", follow_redirects=True)
    print("PASS  단어를 엑셀·CSV 로 올리기 → 미리보기 → 저장 (끌어다 놓기)")


def test_sheet_heading():
    """시험지 맨 위 — 학원 이름 · 제목 · 날짜. 모두 선택 사항입니다."""
    c = client()
    slug = sc.load_words()["books"][0]["slug"]
    unit = sc.load_words()["books"][0]["units"][0]["id"]

    # 아무것도 안 적으면 지금까지처럼 나옵니다
    plain = sheet_text(f"/words/{slug}/sheet?unit={unit}&kind=en_ko&seed=7")
    assert "어휘 TEST ·" in plain
    assert "이름" in plain and "점수" in plain

    # 적으면 제목이 그것으로 바뀌고, 학원 이름이 제목 위에 붙습니다
    tail = "&place=오르티카잉+영어학원&title=9월+어휘+확인&date=2026.+9.+4."
    fancy = sheet_text(f"/words/{slug}/sheet?unit={unit}&kind=en_ko&seed=7" + tail)
    assert "오르티카잉 영어학원" in fancy
    assert "9월 어휘 확인" in fancy
    assert "2026. 9. 4." in fancy
    assert "어휘 TEST" not in fancy           # 적어 주신 제목이 대신 들어갑니다

    # 학생용과 정답지 두 장 모두에 들어갑니다
    assert fancy.count("오르티카잉 영어학원") == 2
    assert fancy.count("9월 어휘 확인") == 2

    # '다른 문제로 다시' 를 눌러도 제목이 그대로 따라갑니다
    page = body(c.get(f"/words/{slug}/sheet?unit={unit}&kind=en_ko&seed=7" + tail))
    assert "place=" in page and "title=" in page

    # 고르는 화면 두 곳 모두에 꾸미기 칸이 있습니다
    for url in (f"/words/{slug}", f"/words/{slug}/pick?unit={unit}"):
        page = body(c.get(url))
        assert "시험지 맨 위 꾸미기" in page
        assert 'name="place"' in page and 'name="dateblank"' in page
    print("PASS  시험지 맨 위 — 학원 이름 · 제목 · 날짜 (선택)")


def test_whole_book_upload():
    """단어책 전체가 담긴 한 파일을 올리면, 강을 알아서 나눠 한꺼번에 넣습니다."""
    import io as _io
    import openpyxl
    a = admin()
    a.post("/admin/words/new", data={"name": "whole book"}, follow_redirects=True)

    # (1) 강 칸이 따로 있는 표 — Day | 영어 | 뜻
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["Day", "영어", "뜻"])
    rows = [("Day 1", "retain", "유지하다"), ("Day 1", "vary", "다르다"),
            ("Day 2", "seek", "추구하다"), ("Day 2", "yield", "산출하다"),
            ("Day 3", "grasp", "붙잡다")]
    for r in rows:
        ws.append(list(r))
    buf = _io.BytesIO(); wb.save(buf)
    page = body(a.post("/admin/words/whole-book/upload",
                       data={"unit_name": "", "file": (_io.BytesIO(buf.getvalue()), "전체.xlsx")},
                       content_type="multipart/form-data"))
    assert "강 3개" in page and "단어 5개" in page
    assert "## Day 1" in page and "## Day 3" in page
    assert "강 3개 한꺼번에 넣기" in page
    assert sc.word_count(sc.find_wordbook("whole-book", raw=True)) == 0   # 아직 저장 전

    text = "## Day 1\nretain\t유지하다\nvary\t다르다\n## Day 2\nseek\t추구하다\n"          \
           "yield\t산출하다\n## Day 3\ngrasp\t붙잡다"
    done = body(a.post("/admin/words/whole-book/unit",
                       data={"unit_name": "", "words": text}, follow_redirects=True))
    assert "강 3개 · 단어 5개를 넣었습니다" in done
    book = sc.find_wordbook("whole-book", raw=True)
    assert [u["name"] for u in book["units"]] == ["Day 1", "Day 2", "Day 3"]
    assert sc.word_count(book) == 5

    # (2) 시트가 강마다 하나씩
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for day, pairs in [("Day 10", [("brisk", "활기찬")]), ("Day 11", [("cling", "매달리다")])]:
        sh = wb.create_sheet(day)
        sh.append(["영어", "뜻"])
        for en, ko in pairs:
            sh.append([en, ko])
    buf = _io.BytesIO(); wb.save(buf)
    assert "강 2개" in body(a.post("/admin/words/whole-book/upload",
        data={"unit_name": "", "file": (_io.BytesIO(buf.getvalue()), "시트별.xlsx")},
        content_type="multipart/form-data"))

    # (3) 단어 사이에 'Day 47' 만 있는 줄이 끼어 있는 CSV
    csv = "Day 47\nadept,능숙한\nDay 48\ncoarse,거친\n".encode("utf-8-sig")
    page = body(a.post("/admin/words/whole-book/upload",
                       data={"unit_name": "", "file": (_io.BytesIO(csv), "구분줄.csv")},
                       content_type="multipart/form-data"))
    assert "강 2개" in page and "## Day 48" in page       # ## Day 47 은 도움말에도 있습니다

    # 강 하나짜리 파일은 예전처럼 이름을 적어 넣습니다
    csv1 = "영어,뜻\nplain,분명한\n".encode("utf-8-sig")
    one = body(a.post("/admin/words/whole-book/upload",
                      data={"unit_name": "Day 99", "file": (_io.BytesIO(csv1), "한강.csv")},
                      content_type="multipart/form-data"))
    assert "이 강에 넣기" in one and "강 2개 한꺼번에 넣기" not in one
    assert "plain\t분명한" in one

    # 같은 이름으로 다시 넣으면 덮어씁니다 (강이 늘어나지 않습니다)
    a.post("/admin/words/whole-book/unit",
           data={"unit_name": "", "words": "## Day 1\nretain\t유지하다"},
           follow_redirects=True)
    book = sc.find_wordbook("whole-book", raw=True)
    assert len(book["units"]) == 3 and len(book["units"][0]["words"]) == 1

    a.post("/admin/words/whole-book/delete", follow_redirects=True)
    print("PASS  단어책 전체를 한 파일로 올리기 → 강 자동 나누기")


def test_wordfile_table_shapes():
    """단어책 표는 파일마다 칸 차례가 다릅니다. 값 생김새로 알아봐야 합니다."""
    def read(rows):
        out = sc.rows_to_lines(rows)
        return ([x[3:] for x in out if x.startswith("## ")],
                [x for x in out if not x.startswith("## ")])

    days = [[f"Day {d}", f"word{d}{i}", f"뜻{i}"] for d in (1, 2, 3) for i in range(4)]

    # 강 칸이 앞 · 뒤 · 없음 — 어디에 있어도 찾아냅니다
    assert read([["Day", "영어", "뜻"], ["Day 1", "apple", "사과"],
                 ["Day 1", "bear", "곰"], ["Day 2", "cat", "고양이"]]) \
        == (["Day 1", "Day 2"], ["apple\t사과", "bear\t곰", "cat\t고양이"])
    assert read([["단어", "의미", "강"], ["apple", "사과", "1강"], ["bear", "곰", "2강"]])[0] \
        == ["1강", "2강"]
    assert read([["영어", "뜻"], ["apple", "사과"]]) == ([], ["apple\t사과"])

    # 머리글이 없어도 됩니다. 머리글이 영어여도 데이터로 세지 않습니다
    assert read(days)[0] == ["Day 1", "Day 2", "Day 3"]
    assert read([["Word", "Meaning", "Unit"], ["apple", "사과", "Unit 1"]])[0] == ["Unit 1"]

    # '번호' 처럼 줄마다 다른 숫자 칸은 강이 아닙니다
    seq = [["번호", "영어", "뜻"]] + [[str(i), f"word{i}", f"뜻{i}"] for i in range(1, 6)]
    assert read(seq)[0] == [] and len(read(seq)[1]) == 5
    bare = [[str(i), f"word{i}", f"뜻{i}"] for i in range(1, 9)]
    assert read(bare)[0] == [] and len(read(bare)[1]) == 8       # 머리글이 없어도 안 지웁니다

    # 단어 사이에 'Day 47' 만 있는 줄
    assert read([["Day 47"], ["apple", "사과"], ["Day 48"], ["bear", "곰"]])[0] \
        == ["Day 47", "Day 48"]

    # 강 칸과 번호 칸이 함께 있어도 뜻을 강으로 착각하지 않습니다
    both = [["강", "번호", "영어", "뜻"], ["1강", "1", "apple", "사과"],
            ["1강", "2", "bear", "곰"], ["2강", "1", "cat", "고양이"]]
    assert read(both) == (["1강", "2강"], ["apple\t사과", "bear\t곰", "cat\t고양이"])

    # 뜻 안의 쉼표는 그대로 둡니다
    assert read([["영어", "뜻"], ["vary", "다르다, 달라지다"]])[1] == ["vary\t다르다, 달라지다"]
    print("PASS  단어 표 — 강 칸이 앞·뒤·구분줄 어디에 있어도 알아봄")


def test_pass_shows_what_each_plan_covers():
    """값만 있으면 비싼지 싼지 알 수 없습니다.

    '99,000원' 은 판단이 안 서고, '한 학기를 통째로 · 낱개로 사시면 184,000원'
    이라야 섭니다. 문구를 손으로 적어 두면 지문 수를 고치는 순간 거짓말이
    되므로, 실제 카탈로그에서 세어 만듭니다.
    """
    text = body(client().get("/pass"))
    assert "한 학기를 통째로" in text and "1년 내내" in text
    assert "낱개로 사시면 약" in text and "아끼십니다" in text
    assert "이미 열어 두셨으니 고르기만" in text     # 바닥 한 줄
    assert "지문 묶음으로 여세요" not in text        # 무슨 말인지 모릅니다

    # 강사는 한 강에 분석과 문제를 둘 다 쓰시므로 지문이 두 번 빠집니다.
    # 이것을 안 세면 '시험 한 번' 이 절반짜리가 됩니다.
    one = sc.exam_round_passages()
    assert one > 100, one
    assert sc.plan_covers(one).startswith("시험 한 번")
    assert sc.plan_covers(one * 2).startswith("한 학기")
    assert sc.plan_covers(one * 4).startswith("1년")
    assert sc.plan_covers(0) == ""

    # 견줌은 우리에게 불리한 쪽으로 셉니다 — 낱개 정가가 아니라 수량 할인가로,
    # 지문당 값이 싼 패키지(분석) 기준으로.
    per = sc.piece_price_per_passage()
    site = sc.load_site()
    best = max((t["percent"] for t in
                (site.get("discount") or {}).get("count_tiers") or []), default=0)
    assert sc.plan_alone_price(100) == round(100 * per * (100 - best) / 100 / 1000) * 1000

    # 낱개가 더 싸면 견줄 말이 없으니 아예 안 붙입니다
    plans = [pl for pl in site["pass"]["plans"]]
    for pl in plans:
        alone = sc.plan_alone_price(pl["passages"])
        if alone <= pl["price"]:
            assert f"낱개로 사시면 약 {alone:,}원" not in text, pl["name"]

    print("PASS  프리패스 — 무엇을 덮는지 · 낱개로 사면 얼마인지")


def test_pass_counts_passages():
    """프리패스는 무제한이 아니라 지문 n개까지이고, 세는 법이 적혀 있어야 합니다."""
    import re as _re
    text = body(client().get("/pass"))
    assert "지문 400개" in text and "지문 160개" in text and "지문 55개" in text
    assert "무제한" not in text
    assert "지문당" in text                      # 낱개보다 싸다는 것이 보여야 합니다

    # '지문 1개' 가 무엇인지 화면에 적혀 있어야 합니다
    assert "지문은 이렇게 빠집니다" in text
    assert "그 지문의 자료 한 묶음" in text
    # 단위로 환산한 예시가 있어야 손님이 감을 잡습니다
    assert "모의고사 7회차 + 부교재 40강 + 교과서 8과" in text

    # 오래 쓰는 요금제일수록 지문당 값이 싸야 합니다 (거꾸로면 살 이유가 없습니다)
    per = [int(x.replace(",", "")) for x in
           _re.findall(r"지문당 ([\d,]+)원", text)]
    assert len(per) == 3, per
    assert per == sorted(per, reverse=True), per
    print("PASS  프리패스 — 지문 n개까지 · 세는 법 · 오래 쓸수록 싸게")


class fake_post:
    """메일이 실제로 나간 셈 치고 받는 사람과 글을 모아 둡니다."""

    def __init__(self):
        self.box = []

    def __enter__(self):
        self._keep = sc.send_mail
        os.environ["SMTP_HOST"] = "테스트우체국"
        def fake(subject, body, to_addr=""):
            self.box.append({"to": to_addr, "subject": subject, "body": body})
            return True
        sc.send_mail = fake
        return self

    def __exit__(self, *a):
        sc.send_mail = self._keep
        os.environ.pop("SMTP_HOST", None)


def _mail_log():
    with store.app.app_context():
        return sc.get_db().execute(
            "SELECT * FROM mailouts ORDER BY id DESC LIMIT 1").fetchone()


def test_metrics_screen():
    """매출 화면 하나에 돈과 지표가 다 있어야 합니다.

    전에는 '매출·세금' 과 '지표' 가 따로 있으면서 달마다 표를 똑같은 질의로
    두 번 그렸습니다. 한 화면으로 합쳤습니다.
    """
    a = admin()
    page = body(a.get("/admin/sales"))
    assert "매출 · 지표" in page
    assert "자료 하나당 평균" in page and "실수령" in page
    assert "월별 매출" in page and "많이 팔린 자료" in page
    assert "한 번도 안 팔린 자료" in page
    # 없던 값을 읽어 늘 같은 숫자만 내던 '제작비 회수' 칸은 뺐습니다
    assert "제작비 회수" not in page
    # 지표 화면은 없앴습니다. 옛 주소는 여기로 옵니다
    assert a.get("/admin/metrics").headers["Location"].endswith("/admin/sales")

    # 값을 치른 주문이 있으면 순위에 뜹니다
    slug = "mock-2026-03-g2-analysis"
    c = client()
    r = c.post("/order", data={"slug": slug, "name": "지표", "phone": "010-5555-1111",
                               "email": "metric@example.com", "agree": "1"})
    key = r.headers["Location"].rsplit("/", 1)[-1]
    oid = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT id FROM orders WHERE view_key = ?", (key,)).fetchone()[0]
    a.post(f"/admin/orders/{oid}", data={"status": "입금확인"}, follow_redirects=True)

    page = body(a.get("/admin/sales"))
    assert "2026년 3월 학력평가" in page
    # 손님 화면에는 이런 숫자가 새어 나가면 안 됩니다
    for path in ("/", "/products", "/cart"):
        assert "실수령" not in body(client().get(path))
    print("PASS  매출 한 화면 — 돈 · 단위당 평균 · 자료별 순위")


def test_storage_warning_when_data_would_vanish():
    """인터넷 서버에 디스크를 안 붙이면, 자료가 날아간다고 크게 알려 줍니다."""
    import os as _os
    a = admin()

    # 내 컴퓨터에서 볼 때 — 겁줄 필요 없습니다
    here = body(a.get("/admin/checkup"))
    assert "자료가 저장되는 곳" in here and "내 컴퓨터" in here
    assert "다시 배포하면 사라집니다" not in here

    # 인터넷 서버인데 디스크가 없을 때 — 빨간 경고
    _os.environ["RENDER"] = "true"
    try:
        danger = body(a.get("/admin/checkup"))
        assert "지금 올리시는 자료는 다시 배포하면 사라집니다" in danger
        assert "STORE_DATA" in danger and "/var/data" in danger
        assert "전부 사라집니다" in danger

        # 디스크를 붙였을 때 — 안전하다고 알려 줍니다
        _os.environ["STORE_DATA"] = str(sc.DATA_DIR)
        safe = body(a.get("/admin/checkup"))
        assert "안전합니다" in safe and "그대로 남습니다" in safe
        assert "다시 배포하면 사라집니다" not in safe
    finally:
        _os.environ.pop("RENDER", None)
        _os.environ.pop("STORE_DATA", None)

    # 크기를 못 잰 값도 화면을 깨지 않아야 합니다
    assert sc.human_size(None) == "-"
    print("PASS  자료 저장되는 곳 — 날아갈 상태면 크게 알려 줌")


def test_checkup_screen():
    """빠진 것 점검 — 손님이 못 사는 상품을 찾아 줘야 합니다."""
    a = admin()
    page = body(a.get("/admin/checkup"))
    assert "빠진 것 점검" in page
    # 파일 없는 상품은 '급함' 으로 뜹니다
    assert "받을 파일이 없는 상품" in page and "급함" in page
    assert "값을 받고 못 드립니다" in page
    # 예시값 그대로인 가게 정보도 잡아 줍니다
    site = sc.load_site()
    keep = dict(site["business"])
    site["business"]["reg_no"] = "000-00-00000"        # 예시값으로 되돌려 봅니다
    sc.save_site(site)
    page = body(a.get("/admin/checkup"))
    assert "예시값 그대로인 가게 정보" in page and "사업자등록번호" in page
    site = sc.load_site(); site["business"] = keep; sc.save_site(site)
    assert "사업자등록번호" not in body(a.get("/admin/checkup"))

    # 값이 0원인 상품을 하나 만들어 두면 잡힙니다
    catalog = sc.load_raw_catalog()
    catalog["products"].append({"slug": "zero-price-test", "name": "값 없는 자료",
                                "price": 0, "active": True, "passages": 5,
                                "book": "ybm-han", "package": "analysis"})
    sc.save_catalog(catalog)
    page = body(a.get("/admin/checkup"))
    assert "값이 0원인 상품" in page and "값 없는 자료" in page

    catalog = sc.load_raw_catalog()
    catalog["products"] = [p for p in catalog["products"] if p["slug"] != "zero-price-test"]
    sc.save_catalog(catalog)
    print("PASS  빠진 것 점검 — 파일·값·교재·샘플·가게 정보")


def test_mail_to_leads_and_coupons():
    """명단에 소식·쿠폰을 보내고, 보낸 기록이 남아야 합니다."""
    a = admin()
    # 무료 자료를 받아 가면서 이메일이 쌓입니다
    free = sc.load_raw_freebies()["items"][0]
    for i in range(3):
        client().post(f"/free/{free['slug']}/get",
                      data={"email": f"lead{i}@example.com", "news": "1", "agree": "1"})

    page = body(a.get("/admin/mail"))
    assert "새 자료 · 소식 알리기" in page and "할인 쿠폰 뿌리기" in page
    assert "담아만 두고 안 사신 분" in page
    # 메일 설정이 없으면 보내기 단추가 잠겨 있어야 합니다
    assert "아직 메일을 보낼 수 없습니다" in page and "disabled" in page
    blocked = body(a.post("/admin/mail/news", data={
        "subject": "제목", "body": "내용", "who": "news"}, follow_redirects=True))
    assert "한 통도 나가지 않습니다" in blocked

    with fake_post() as post:
        assert "아직 메일을 보낼 수 없습니다" not in body(a.get("/admin/mail"))

        # 시험 삼아 나에게만 한 통
        a.post("/admin/mail/news", data={
            "subject": "시험", "body": "시험 발송", "who": "news",
            "test": "1", "test_to": "me@example.com"}, follow_redirects=True)
        assert len(post.box) == 1 and post.box[0]["to"] == "me@example.com"
        post.box.clear()

        # 소식 보내기
        done = body(a.post("/admin/mail/news", data={
            "subject": "9월 학평 자료가 올라왔습니다",
            "body": "선생님 안녕하세요.", "who": "news"}, follow_redirects=True))
        assert "통 보냈습니다" in done
        assert len(post.box) >= 3
        assert "선생님 안녕하세요." in post.box[0]["body"]
        assert "명단에서 빼 드리겠습니다" in post.box[0]["body"]   # 수신 거부 안내
        log = _mail_log()
        assert log["kind"] == "news" and log["sent"] >= 3 and log["failed"] == 0

        # 쿠폰 뿌리기 — 사람마다 다른 번호가 나가야 합니다
        with store.app.app_context():
            before = sc.get_db().execute(
                "SELECT COUNT(*) AS n FROM coupons").fetchone()["n"]
        a.post("/admin/mail/coupon", data={
            "kind": "amount", "value": "3000", "days": "14", "min_amount": "10000",
            "note": "9월 시험 대비", "who": "news",
            "subject": "쿠폰을 보내 드립니다", "body": "안녕하세요."}, follow_redirects=True)
    with store.app.app_context():
        db = sc.get_db()
        after = db.execute("SELECT COUNT(*) AS n FROM coupons").fetchone()["n"]
        made = db.execute("SELECT * FROM coupons WHERE note = '9월 시험 대비'").fetchall()
    assert after - before >= 3
    assert len({c["code"] for c in made}) == len(made), "같은 쿠폰 번호가 나갔습니다"
    assert made[0]["value"] == 3000 and made[0]["min_amount"] == 10000
    assert all("@" in (c["issued_to"] or "") for c in made), \
        "쿠폰에 받는 사람이 안 적혔습니다"
    assert _mail_log()["kind"] == "coupon"

    # 못 보낸 쿠폰은 도로 지웁니다 — 손에 없는 번호가 쌓이면 안 됩니다
    os.environ["SMTP_HOST"] = "없는우체국"
    with store.app.app_context():
        was = sc.get_db().execute("SELECT COUNT(*) AS n FROM coupons").fetchone()["n"]
    a.post("/admin/mail/coupon", data={
        "kind": "amount", "value": "1000", "days": "7", "min_amount": "0",
        "note": "실패 시험", "who": "news", "subject": "x", "body": "x"},
        follow_redirects=True)
    with store.app.app_context():
        now = sc.get_db().execute("SELECT COUNT(*) AS n FROM coupons").fetchone()["n"]
        leftover = sc.get_db().execute(
            "SELECT COUNT(*) AS n FROM coupons WHERE note = '실패 시험'").fetchone()["n"]
    os.environ.pop("SMTP_HOST", None)
    assert now == was and leftover == 0, "못 보낸 쿠폰이 남았습니다"
    print("PASS  명단에 소식·쿠폰 보내기 · 못 보낸 쿠폰은 도로 지움")


def test_left_cart_reminder():
    """담아만 두고 안 사신 분께 하루 뒤 한 번만 알려 드립니다."""
    a = admin()
    c = client()
    c.post("/cart/add", data={"slug": "ybm-han-analysis"})
    c.post("/cart/add", data={"slug": "ybm-han-problem"})
    email = "left@example.com"
    # 주문서에서 이메일을 적으면 (금액을 다시 물어볼 때) 기억해 둡니다
    c.get(f"/order/quote?cart=1&email={email}")
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM carts_left WHERE email = ?", (email,)).fetchone()
    assert row and row["amount"] > 0 and "ybm-han-analysis" in row["slugs"]

    # 방금 담은 것은 아직 안 보냅니다 (하루가 지나야)
    assert "지금은 알려 드릴 분이 없습니다" in body(a.get("/admin/mail"))

    # 하루 지난 것으로 돌려 놓습니다
    with store.app.app_context():
        db = sc.get_db()
        db.execute("UPDATE carts_left SET created_at = ? WHERE email = ?",
                   ("2020-01-01T00:00:00+09:00", email))
        db.commit()
    page = body(a.get("/admin/mail"))
    assert email in page and "1분께 알려 드리기" in page

    with fake_post() as post:
        a.post("/admin/mail/cart", data={"hours": "24"}, follow_redirects=True)
        assert _mail_log()["kind"] == "cart"
        assert len(post.box) == 1 and post.box[0]["to"] == email
        assert "장바구니에 담아 두신 자료가 있습니다" in post.box[0]["body"]
    # 한 번 보냈으면 다시 안 나옵니다
    assert email not in body(a.get("/admin/mail"))

    # 값을 치르시면 대상에서 빠집니다
    c2 = client()
    c2.post("/cart/add", data={"slug": "ybm-han-analysis"})
    c2.get("/order/quote?cart=1&email=bought@example.com")
    ordered = c2.post("/order", data={"cart": "1", "name": "산분",
                                      "phone": "010-2222-3333",
                                      "email": "bought@example.com", "agree": "1"})
    assert ordered.status_code == 302, body(ordered)[:300]
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM carts_left WHERE email = ?", ("bought@example.com",)).fetchone()
    assert row and row["ordered_at"], "값을 치렀는데 되살리기 대상에 남았습니다"
    print("PASS  장바구니 두고 간 분 되살리기 (하루 뒤 · 한 번만)")


def test_pass_quota():
    """프리패스 — 지문이 깎이고, 다 쓰면 막히고, 두 번 받아도 한 번만 깎입니다."""
    a = admin()
    email = "passuser@example.com"

    # 관리자가 이용권을 열어 줍니다
    page = body(a.post("/admin/passes/new", data={
        "email": email, "plan": "12개월", "quota": "40", "days": "365",
        "note": "테스트"}, follow_redirects=True))
    assert "열어 드렸습니다" in page and email in page

    # 손님이 프리패스로 자료를 받습니다 (mock-2026-06-g3-analysis 는 지문 28개)
    site = sc.load_site()
    site["pass"]["mode"] = "sale"
    sc.save_site(site)

    detail = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert "프리패스로 받기" in detail and "지문 28개가 깎입니다" in detail

    c = client()
    got = body(c.post("/pass/use", data={"slug": "mock-2026-06-g3-analysis",
                                         "email": email}, follow_redirects=True))
    assert "지문 28개를 썼습니다" in got and "남은 지문 12개" in got
    assert "프리패스 남은 지문" in got and "12개" in got

    # 같은 자료를 또 받아도 깎이지 않습니다
    again = body(c.post("/pass/use", data={"slug": "mock-2026-06-g3-analysis",
                                           "email": email}, follow_redirects=True))
    assert "이미 받으신 자료입니다" in again
    with store.app.app_context():
        assert sc.pass_left(sc.active_pass(email)) == 12

    # 남은 지문보다 큰 자료는 막힙니다
    over = body(c.post("/pass/use", data={"slug": "mock-2026-03-g2-analysis",
                                          "email": email}, follow_redirects=True))
    assert "남은 지문이 12개인데 이 자료는 28개가 필요합니다" in over

    # 이용권이 없는 이메일은 안내를 받습니다
    none = body(client().post("/pass/use", data={"slug": "mock-2026-06-g3-analysis",
                                                 "email": "nopass@example.com"},
                              follow_redirects=True))
    assert "쓸 수 있는 프리패스가 없습니다" in none

    # 관리자가 지문을 더해 주면 다시 받을 수 있습니다
    with store.app.app_context():
        pid = sc.active_pass(email)["id"]
    a.post(f"/admin/passes/{pid}", data={"action": "add", "more_quota": "100",
                                         "more_days": "0"}, follow_redirects=True)
    ok2 = body(c.post("/pass/use", data={"slug": "mock-2026-03-g2-analysis",
                                         "email": email}, follow_redirects=True))
    assert "지문 28개를 썼습니다" in ok2

    # 끊으면 더 못 받습니다
    a.post(f"/admin/passes/{pid}", data={"action": "revoke"}, follow_redirects=True)
    dead = body(c.post("/pass/use", data={"slug": "ybm-han-analysis",
                                          "email": email}, follow_redirects=True))
    assert "쓸 수 있는 프리패스가 없습니다" in dead

    # 사전 신청 상태로 되돌리면 '프리패스로 받기' 가 사라집니다
    site = sc.load_site(); site["pass"]["mode"] = "preorder"; sc.save_site(site)
    assert "프리패스로 받기" not in body(client().get("/products/mock-2026-06-g3-analysis"))
    print("PASS  프리패스 — 지문 차감 · 재다운로드 무료 · 한도 초과 차단 · 끊기")


def test_my_locker():
    """내 자료함 — 회원가입 없이, 이메일과 자료함 열쇠로 다시 받기."""
    # 주문을 하나 넣고, 관리자가 발송까지 마칩니다
    resp = client().post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "박선생",
        "phone": "010-7777-6666", "email": "Locker@Example.com", "agree": "1"},
        follow_redirects=True)
    done = body(resp)
    assert "주문이 접수되었습니다" in done
    # 주문 확인 화면에서 자료함으로 바로 들어갈 수 있어야 합니다
    assert "내 자료함 열기" in done
    key = re.search(r'href="(/my/[A-Za-z0-9_-]+)"', done).group(1)

    text = body(client().get(key))
    assert "내 자료함" in text
    assert "locker@example.com" in text            # 대소문자를 가리지 않고 찾습니다
    assert "mock-2026-06-g3-analysis" in text or "6월 모의평가" in text
    assert "입금이 확인되면" in text                 # 아직 발송 전
    assert "용지 A4 · 배율 100%" in text            # 인쇄 안내
    assert "noindex" in text                       # 남의 자료함이 검색에 잡히면 안 됩니다

    # 열쇠는 바뀌지 않습니다 — 즐겨찾기 해 두고 계속 쓰시게
    again = body(client().get(key))
    assert "내 자료함" in again
    assert client().get("/my/없는열쇠123").status_code == 404

    # 문 앞 화면: 이메일을 넣으면 주문 여부와 상관없이 같은 문구가 나와야 합니다.
    # (다르면 아무 주소나 넣어 보며 '이 사람이 샀는지' 를 알아낼 수 있습니다)
    import os as _os
    got = body(client().post("/my", data={"email": "locker@example.com"}))
    never = body(client().post("/my", data={"email": "nobody@example.com"}))
    assert got == never, "산 사람과 안 산 사람에게 다른 화면이 나갑니다"

    # 메일을 못 보내는 동안에는 '보냈습니다' 라고 하면 안 됩니다 —
    # 오지 않을 메일을 기다리게 됩니다
    assert not sc.mail_ready()
    assert "보내 드렸습니다" not in got
    assert "메일 대신 바로 보내 드리겠습니다" in got and "문의" in got

    # 메일이 나갈 수 있으면 예전대로 안내합니다
    _os.environ["SMTP_HOST"] = "smtp.example.com"
    try:
        ok = body(client().post("/my", data={"email": "locker@example.com"}))
        none2 = body(client().post("/my", data={"email": "nobody@example.com"}))
        assert "자료함 주소를 보내 드렸습니다" in ok
        assert ok == none2, "여기서도 두 화면이 같아야 합니다"
    finally:
        _os.environ.pop("SMTP_HOST", None)

    assert body(client().post("/my", data={"email": "이메일아님"})) .count("정확히 입력") == 1

    # 주소가 곧 열쇠라, 눈에 보이게 내놓고 한 번에 복사하게 합니다
    assert "keep-box" in text and 'class="keep-url"' in text
    assert key in text, "자료함 주소가 화면에 안 보입니다"

    # 검색엔진이 열쇠 주소를 훑지 않게
    assert "Disallow: /my/" in body(client().get("/robots.txt"))
    assert "/my/" not in body(client().get("/sitemap.xml"))
    print("PASS  내 자료함 — 다시 받기 · 주소 저장 · 열쇠 보호 · 못 보낼 땐 사실대로")


def test_owner_can_hand_out_locker_link():
    """메일이 안 나가는 동안에도 사장님이 자료함 주소를 건네실 수 있어야 합니다.

    손님이 자료함을 못 열면 산 자료를 못 받습니다. 메일이 막혀 있으면 관리자
    화면에서 주소를 복사해 카카오톡으로 보내 주는 길이 있어야 합니다.
    """
    import re as _re
    page = body(admin().get("/admin/orders"))
    assert "자료함 주소 복사" in page

    # 화면에 걸린 주소는 그 주문한 분의 자료함으로 실제로 열려야 합니다
    links = _re.findall(r'data-copy="([^"]+)"', page)
    assert links, "복사할 주소가 하나도 없습니다"
    token = links[0].rstrip("/").rsplit("/", 1)[-1]
    opened = client().get(f"/my/{token}")
    assert opened.status_code == 200, opened.status_code
    assert "내 자료함" in body(opened)

    # 메일이 막혀 있다는 것도 사장님께 알려 드립니다
    assert not sc.mail_ready()
    assert "자동 메일이 나가지 않습니다" in page
    print("PASS  메일이 막혀도 자료함 주소를 건네줄 수 있음")


def test_contact_has_no_phone():
    """전화번호는 안 받습니다. 오픈채팅으로 받습니다."""
    site = sc.load_site()
    assert "phone" not in site["contact"], site["contact"]
    assert site["contact"]["kakao_url"].startswith("https://open.kakao.com/")

    for url in ("/", "/contact", "/guide"):
        page = body(client().get(url))
        assert "전화 ·" not in page, url
        assert site["contact"]["kakao_url"] in page, url

    # 관리자 설정에도 전화 칸이 없습니다
    adm = body(admin().get("/admin/settings"))
    assert 'name="contact_phone"' not in adm
    # 오픈채팅 주소 칸은 하나뿐이어야 합니다. 똑같이 생긴 칸이 두 개 있었는데
    # 위쪽 것은 저장할 때 아무도 안 읽어, 적어 넣어도 사라졌습니다.
    assert adm.count('카카오톡 오픈채팅 주소') == 1, adm.count('카카오톡 오픈채팅 주소')
    assert 'name="contact_kakao_url"' in adm
    assert 'name="contact_kakao"' not in adm.replace('name="contact_kakao_url"', '') \
                                          .replace('name="contact_kakao_label"', '')

    # 저장해도 전화번호가 다시 생기지 않습니다.
    # (설정 저장은 화면 전체를 덮어쓰므로, 확인한 뒤 원래대로 돌려놓습니다)
    keep = json.loads(json.dumps(sc.load_site()))
    keep["contact"]["phone"] = "010-1234-5678"           # 예전 설정에 남아 있던 것처럼
    sc.save_site(keep)
    admin().post("/admin/settings", data={
        "brand": site["brand"], "contact_email": site["contact"]["email"],
        "contact_phone": "010-1234-5678",
        "contact_kakao_url": site["contact"]["kakao_url"],
        "contact_hours": site["contact"]["hours"]}, follow_redirects=True)
    assert "phone" not in sc.load_site()["contact"]
    keep["contact"].pop("phone", None)
    sc.save_site(keep)
    print("PASS  문의는 오픈채팅으로 · 전화번호 없음")


def test_contact_page():
    """문의 창구 — 급한 분은 바로 연락, 기록이 남아야 하면 폼으로."""
    text = body(client().get("/contact"))
    assert "문의하기" in text
    # 폼을 채우기 전에 카카오톡·이메일이 먼저 보여야 합니다
    assert 'class="contact-ways"' in text
    assert text.index('class="contact-ways"') < text.index('class="form-card"')
    for label in ("주문 · 입금 · 영수증", "자료가 안 왔어요", "학원 제휴 · 대량 구매"):
        assert label in text, label
    assert "주문번호" in text                       # 자료 미도착 문의를 바로 찾기 위해

    # 위 메뉴에 문의는 없습니다. 발밑과 이용 안내에서 갑니다.
    home = body(client().get("/"))
    assert home.count('href="/contact"') >= 1                  # 바닥글
    assert 'href="/contact"' in body(client().get("/guide"))

    # 내용을 안 적으면 반려
    bad = client().post("/contact", data={"topic": "order", "name": "홍길동",
                                          "email": "a@b.com", "agree": "1"})
    assert bad.status_code == 400 and "문의하실 내용을 적어" in body(bad)

    resp = client().post("/contact", data={
        "topic": "delivery", "order_no": "OR-260902-11111", "name": "김선생",
        "email": "teacher@example.com", "body": "자료가 아직 안 왔습니다.",
        "agree": "1"}, follow_redirects=True)
    assert resp.status_code == 200 and "문의가 접수되었습니다" in body(resp)
    row = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT product_name, message, detail_json FROM orders "
        "WHERE kind='inquiry' ORDER BY id DESC LIMIT 1").fetchone()
    assert "자료가 안 왔어요" in row[0] and "아직 안 왔습니다" in row[1]
    assert "OR-260902-11111" in row[2]
    # 관리자 주문 화면에서 '문의'로 걸러 볼 수 있어야 합니다
    assert "문의" in body(admin().get("/admin/orders?kind=inquiry"))
    # 사이트맵에도 들어갑니다
    assert "/contact" in body(client().get("/sitemap.xml"))
    print("PASS  문의 창구 — 바로 연락 · 문의 폼 · 관리자에서 확인")


def test_locker_sits_next_to_the_cart():
    """오른쪽 위는 장바구니 · 내 자료함 · 자료 보러 가기 순입니다."""
    home = body(client().get("/"))
    cta = home.split('class="head-cta"', 1)[1].split("</header>", 1)[0]
    assert 'class="cart-link' in cta and 'class="locker-link' in cta
    seen = [cta.index('aria-label="장바구니"'),
            cta.index('aria-label="내 자료함"'),
            cta.index("자료 보러 가기")]
    assert seen == sorted(seen), seen
    print("PASS  장바구니 · 내 자료함 · 자료 보러 가기 순")


def test_email_is_not_an_id_and_the_key_can_be_changed():
    """이메일은 아이디가 아닙니다. 자료함 열쇠는 주소이고, 새로 받을 수 있어야 합니다."""
    mine = "locker-owner@example.com"
    with store.app.app_context():
        token = sc.locker_token(mine)

    # 1) 남의 이메일을 알아도 열리지 않습니다 — 메일이 그쪽으로 갈 뿐입니다
    page = body(client().post("/my", data={"email": mine}, follow_redirects=True))
    assert token not in page, "이메일만 넣었는데 자료함 주소가 화면에 나왔습니다"
    assert "아이디가 아니라" in page

    # 2) 열쇠는 찍어서 맞힐 수 없는 길이여야 합니다
    assert len(token) >= 24, token
    assert client().get("/my/" + "z" * len(token)).status_code == 404

    # 3) 주소가 새어 나갔을 때 손님이 스스로 잠글 수 있어야 합니다
    opened = body(client().get(f"/my/{token}"))
    assert "새 주소 받기" in opened and "주소가 곧 열쇠" in opened
    resp = client().post(f"/my/{token}/reset", follow_redirects=False)
    assert resp.status_code == 302, resp.status_code
    fresh = resp.headers["Location"].rstrip("/").rsplit("/", 1)[-1]
    assert fresh != token
    assert client().get(f"/my/{token}").status_code == 404, "옛 주소가 아직 열립니다"
    assert client().get(f"/my/{fresh}").status_code == 200
    with store.app.app_context():
        assert sc.locker_email(fresh) == mine

    # 4) 없는 주소로는 새 주소를 만들 수 없습니다
    assert client().post("/my/없는주소/reset").status_code == 404
    print("PASS  이메일은 아이디가 아님 · 자료함 열쇠 바꾸기")


def test_no_page_promises_pdf_by_email():
    """자료는 메일로 날아오지 않습니다. 그렇게 적힌 화면이 있으면 안 됩니다."""
    # 실제 동작: 입금 확인 → 주문 화면·내 자료함에서 바로 열림. 메일은 링크 백업.
    site = sc.load_site()
    site["delivery"] = json.loads((_SRC / "site.json").read_text())["delivery"]
    site["payment"] = json.loads((_SRC / "site.json").read_text())["payment"]
    sc.save_site(site)

    live = [x for x in sc.load_catalog()["products"] if x.get("active", True)]
    assert live, "팔 수 있는 상품이 하나도 없습니다"
    paths = ["/", "/guide", f"/products/{live[0]['slug']}", "/order"]
    for path in paths:
        page = body(client().get(path))
        for bad in ("이메일로 PDF", "이메일로 자료를 보내", "이메일 발송",
                    "PDF가 발송됩니다", "24시간 이내 이메일"):
            assert bad not in page, f"{path} 에 '{bad}' 가 남아 있습니다"

    # 대신 '이 화면에서 바로' 라고 말해야 합니다
    assert "바로" in body(client().get("/guide"))
    detail = body(client().get(f"/products/{live[0]['slug']}"))
    assert "받는 법" in detail and "바로" in detail
    # 상품마다 따로 적던 발송 문구는 없앴습니다 (가게 전체가 한 문장)
    assert all("delivery" not in x for x in sc.load_raw_catalog()["products"])

    # 한 문장으로 말하되, 메일이 나갈 수 있을 때만 메일 이야기를 합니다
    import os as _os
    line = sc.delivery_line(sc.load_site())
    assert "바로" in line and "자료함" in line
    assert "메일" not in line, "메일을 못 보내는데 보낸다고 합니다"
    _os.environ["SMTP_HOST"] = "smtp.example.com"
    try:
        assert "메일" in sc.delivery_line(sc.load_site())
    finally:
        _os.environ.pop("SMTP_HOST", None)
    print("PASS  '메일로 PDF 보냄' 문구 없음 · 받는 법은 한 문장")


def test_file_comes_with_the_order_no_extra_charge():
    """산 자료는 파일로도 그냥 드립니다. 대신 주문번호가 새겨져 나갑니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    # 배포되는 기본값이 '보기 + 파일 받기 둘 다' 여야 합니다
    # (앞선 테스트가 임시본을 고쳐 놓으므로 원본을 봅니다)
    shipped = json.loads((_SRC / "site.json").read_text())["delivery"]
    assert shipped["mode"] == "both", shipped
    assert "파일" in shipped["note"]
    site = sc.load_site()
    site["delivery"] = dict(shipped)
    # 표시 설정도 배포되는 기본값으로 되돌려 놓고 봅니다
    site["watermark"] = json.loads((_SRC / "site.json").read_text())["watermark"]
    sc.save_site(site)

    # 이 시점에 실제로 살아 있는 상품 하나를 씁니다 (앞 테스트가 지웠을 수 있습니다)
    live = [x for x in sc.load_catalog()["products"]
            if x.get("active", True) and sc.to_int(x.get("price"), 0) > 0]
    assert live, "팔 수 있는 상품이 하나도 없습니다"
    prod = live[0]
    slug = prod["slug"]
    folder = sc.product_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    from reportlab.pdfgen import canvas as rl_canvas
    page = rl_canvas.Canvas(str(folder / "본문.pdf"))
    page.drawString(72, 700, "passage one")
    page.showPage()
    page.save()

    c = client()
    resp = c.post("/order", data={"slug": slug, "name": "받는이", "phone": "010-2222-3333",
                                  "email": "getfile@example.com", "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'getfile@example.com'").fetchone()
    assert row is not None, (resp.status_code, body(resp)[:400])
    amount = row["amount"]
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        tok = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()[0]

    # 값을 더 받지 않습니다 — 상품 값 그대로입니다
    assert amount == prod["price"], (amount, prod["price"])

    # 받는 화면에 '보고 인쇄' 와 '파일로 받기' 가 나란히 있습니다
    page_html = body(c.get(f"/d/{tok}"))
    assert "화면에서 보고 인쇄" in page_html and "파일로 받기" in page_html

    names = [f["name"] for f in sc.product_files(slug)]
    idx = names.index("본문.pdf")
    got = c.get(f"/d/{tok}/{idx}")
    assert got.status_code == 200 and got.data[:4] == b"%PDF"

    # 파일에도 주문번호가 새겨져 나갑니다
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(got.data)).pages[0].extract_text()
    assert row["order_no"] in text
    print("PASS  파일도 그냥 드림 · 대신 주문번호가 새겨짐")


def test_css_change_reaches_the_visitor():
    """디자인을 고쳐 올리면 손님 화면에도 바로 보여야 합니다.

    store.css 는 30일 캐시라, 주소가 그대로면 브라우저가 예전 것을 계속
    씁니다. 화면이 실제로 어긋나 보인 적이 있어 테스트로 못박습니다.
    """
    import re as _re
    home = body(client().get("/"))
    m = _re.search(r'href="(/static/store\.css\?v=(\d+))"', home)
    assert m, "store.css 주소에 v= 가 없습니다"
    first = m.group(2)
    assert client().get(m.group(1)).status_code == 200

    # 파일을 고치면 주소가 바뀝니다
    css = Path(store.app.static_folder) / "store.css"
    old = css.stat().st_mtime
    try:
        os.utime(css, (old + 120, old + 120))
        again = _re.search(r'store\.css\?v=(\d+)', body(client().get("/"))).group(1)
        assert again != first, "고쳐도 주소가 그대로입니다"
    finally:
        os.utime(css, (old, old))

    # 아이콘 같은 다른 정적 파일도 같은 길을 씁니다
    assert "/static/favicon.svg?v=" in home

    # 관리자 화면도 마찬가지입니다. 여기를 빠뜨려 통계 화면이 판이 깨진 채로
    # 나온 적이 있습니다 — 화면은 새것인데 CSS 만 예전 것이었습니다.
    adm = body(admin().get("/admin/traffic"))
    assert "/static/admin.css?v=" in adm, "관리자 CSS 주소에 v= 가 없습니다"
    assert "/static/store.css?v=" in adm

    # 서식 어디에도 v= 없는 CSS·아이콘 링크가 남아 있으면 안 됩니다
    for tpl in sorted((_ROOT / "store_templates").rglob("*.html")):
        text = tpl.read_text()
        for line in text.splitlines():
            if "url_for('static'" not in line:
                continue
            assert ("stylesheet" not in line and 'rel="icon"' not in line
                    and "apple-touch-icon" not in line), \
                f"{tpl.name}: {line.strip()[:80]} — asset() 를 쓰셔야 합니다"
    print("PASS  디자인을 고치면 손님·관리자 화면에 바로 반영")


def test_home_shows_real_pages_not_just_names():
    """첫 화면 자료 타일에 실제 지면 사진을 겁니다. 이름만 부르면 안 팔립니다."""
    from PIL import Image
    import io as _io
    mid = "analysis"
    folder = sc.shot_dir(mid)
    folder.mkdir(parents=True, exist_ok=True)
    src = folder / "01.png"
    Image.new("RGB", (1076, 1369), (250, 250, 250)).save(src)

    # 원본 왼쪽 위에서 같은 비율만큼 잘라 3:4 로 맞춘 판이 생깁니다.
    # (원본 모양대로 두면 자료마다 글씨 크기가 달라집니다)
    thumb = sc.shot_thumb(mid)
    assert thumb is not None and thumb.exists()
    with Image.open(thumb) as im:
        assert im.width == sc.SHOT_THUMB_W
        assert abs(im.width / im.height - sc.SHOT_THUMB_RATIO) < 0.01
    assert thumb.stat().st_size < src.stat().st_size, "원본보다 커졌습니다"
    assert src.exists(), "원본을 건드리면 안 됩니다"

    got = client().get(f"/lineup/thumb/{mid}.webp")
    assert got.status_code == 200 and got.data[:4] == b"RIFF"     # webp
    assert "max-age" in got.headers.get("Cache-Control", "")
    assert client().get("/lineup/thumb/없는자료.webp").status_code == 404

    # 원본이 가로로 넓든 세로로 길든 타일은 같은 모양으로 나옵니다
    for size in ((1200, 500), (1000, 4000)):
        Image.new("RGB", size, (240, 240, 240)).save(src)
        sc.shot_thumb(mid).unlink()
        with Image.open(sc.shot_thumb(mid)) as im:
            assert im.width == sc.SHOT_THUMB_W
            # 원본이 잘라야 할 만큼 길지 않으면 있는 만큼만 — 나머지는 화면이 채웁니다
            assert im.width / im.height >= sc.SHOT_THUMB_RATIO - 0.01, (size, im.size)

    home = body(client().get("/"))
    assert f"/lineup/thumb/{mid}.webp" in home
    assert 'class="mt-shot"' in home and 'loading="lazy"' in home
    # 타일 창은 어느 사진이 와도 같은 크기 — 줄이 들쭉날쭉해지지 않습니다
    css = body(client().get("/static/store.css"))
    assert ".mt-shot{aspect-ratio:3/4; overflow:hidden;}" in css
    assert "object-fit:cover; object-position:left top" in css
    # 지면 사진이 없는 자료는 타일에 안 걸고, 아래 한 줄로 적습니다
    assert 'class="mat-rest"' in home and 'class="mat-tile"' not in home.replace(
        'class="mat-tile has-shot"', "")

    src.unlink()
    print("PASS  첫 화면 자료 타일에 실제 지면 사진")


def test_lineup_takes_the_home_middle():
    """첫 화면 가운데는 자료 목록이 아니라 오르티카잉 라인업입니다."""
    home = body(client().get("/"))
    assert "오르티카잉 라인업 보기" in home                    # 맨 위 두 번째 단추
    assert "라인업 자세히 보기" in home                      # 가운데 단추
    assert home.index("오르티카잉 라인업 보기") < home.index("라인업 자세히 보기")
    assert "자료 목록 보기" in home                          # 목록도 갈 수 있게 남겨 둡니다
    print("PASS  첫 화면 가운데가 오르티카잉 라인업")


def test_menu_has_no_duplicates():
    """메뉴에 같은 항목이 두 번 들어가면 안 됩니다. (실제로 두 번 겪은 실수입니다)"""
    home = body(client().get("/"))
    head = home.split('class="nav"', 1)[1].split("</nav>", 1)[0]
    bar = home.split('class="qb-track"', 1)[1].split("</nav>", 1)[0]
    for where, html in (("머리말 메뉴", head), ("폰 줄띠", bar)):
        for label in ("무료 자료", "단어 시험지", "모의고사", "EBS 부교재",
                      "할인쿠폰", "이용 안내", "프리패스"):
            n = html.count(f">{label}</a>")
            assert n == 1, f"{where} 에 '{label}' 가 {n}번 들어 있습니다"
        # 이만큼만 둡니다. 나머지는 첫 화면 가운데와 발밑에 있습니다.
        for gone in ("자료 목록", "오르티카잉 라인업", "공지", "문의", "내 자료함",
                     "교과서", "형광펜 독해"):
            assert f">{gone}</a>" not in html, f"{where} 에 '{gone}' 가 남아 있습니다"
    print("PASS  메뉴 일곱 가지 · 같은 항목이 두 번 안 들어감")


def test_mobile_quick_bar():
    """폰에서 메뉴를 누르지 않아도 갈 곳이 다 보여야 합니다."""
    home = body(client().get("/"))
    assert 'class="quick-bar"' in home
    # 위 메뉴와 같은 여섯 가지
    track = home.split('class="qb-track"', 1)[1].split("</nav>", 1)[0]
    for word in ("무료 자료", "단어 시험지", "모의고사", "EBS 부교재",
                 "이용 안내", "프리패스"):
        assert word in track, word
    # 지금 보고 있는 자리를 표시해 줍니다
    picked = body(client().get("/products?category=mock"))
    assert 'class="on">모의고사' in picked
    # 햄버거 버튼은 없앴습니다
    assert "nav-toggle" not in home
    css = body(client().get("/static/store.css"))
    assert ".quick-bar{display:none;}" in css       # 넓은 화면에선 띠가 안 보임
    print("PASS  폰에서 카테고리 줄띠")


def _wordbook_pdf(shape: str) -> bytes:
    """시험에 쓸 단어책 PDF 를 그 자리에서 만듭니다 (진짜 인쇄물과 같은 모양).

    shape — one: 한 칸짜리 · two: 두 칸으로 나눈 쪽 · unit: 강 칸이 있는 표 ·
            example: 예문이 딸린 쪽 · blank: 글자가 없는(스캔한) 쪽
    """
    import io as _io
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import store_sheet_pdf as sp
    face, _bold = sp._fonts()
    W, H = A4
    buf = _io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    words = [("retain", "유지하다"), ("intensity", "강도"), ("give up", "포기하다"),
             ("fertile", "비옥한"), ("glacier", "빙하"), ("separate", "분리된")]

    if shape == "blank":                          # 스캔해서 사진만 든 쪽
        c.setFillColorRGB(.8, .8, .8)
        c.rect(60, 400, 400, 300, fill=1, stroke=0)
        c.save()
        return buf.getvalue()

    c.setFont(face, 11)
    if shape == "two":                            # 왼쪽·오른쪽 두 칸
        c.drawString(50, H - 50, "Day 47")
        half = (len(words) + 1) // 2
        for col, chunk in enumerate((words[:half], words[half:])):
            x, y = 50 + col * 270, H - 80
            for en, ko in chunk:
                c.drawString(x, y, en)
                c.drawString(x + 130, y, ko)
                y -= 22
    elif shape == "unit":                         # 줄마다 'Day 47' 이 붙는 표
        y = H - 60
        c.drawString(50, y, "Day"); c.drawString(130, y, "영어")
        c.drawString(300, y, "뜻"); y -= 22
        for i, (en, ko) in enumerate(words):
            c.drawString(50, y, f"Day {47 if i < 3 else 48}")
            c.drawString(130, y, en)
            c.drawString(300, y, ko)
            y -= 22
    elif shape == "example":                      # 표제어 아래에 예문이 붙는 쪽
        y = H - 60
        c.drawString(50, y, "Day 47"); y -= 26
        for en, ko in words[:3]:
            c.drawString(50, y, en); c.drawString(220, y, ko); y -= 15
            c.drawString(66, y, f"The {en} thing happens here.")
            c.drawString(320, y, "이것은 예문입니다."); y -= 24
    else:                                         # one — 번호 · 영어 · 뜻
        y = H - 60
        c.drawString(60, y, "Day 47"); y -= 24
        for i, (en, ko) in enumerate(words, 1):
            c.drawString(60, y, str(i))
            c.drawString(90, y, en)
            c.drawString(250, y, ko)
            y -= 20
    c.save()
    return buf.getvalue()


def test_word_pdf_is_actually_read():
    """단어책 PDF 를 실제로 읽어내야 합니다.

    글자를 나오는 차례대로만 읽으면 단어와 뜻이 따로 떨어져 한 개도 못 읽습니다.
    인쇄된 자리를 보고 같은 높이끼리 묶어야 두 칸짜리 단어책까지 읽힙니다.
    """
    want = {"retain": "유지하다", "give up": "포기하다", "glacier": "빙하"}

    for shape in ("one", "two", "unit"):
        text, note = sc.read_wordfile("책.pdf", _wordbook_pdf(shape))
        rows, warn = sc.parse_words(text)
        got = {r["en"]: r["ko"] for r in rows}
        assert len(rows) == 6, (shape, len(rows), text)
        assert not warn, (shape, warn)
        for en, ko in want.items():
            assert got.get(en) == ko, (shape, en, got)
        assert "PDF" in note

    # 강이 나뉘어 있으면 '## 강이름' 으로 표시해 둡니다
    two = sc.read_wordfile("책.pdf", _wordbook_pdf("two"))[0]
    assert "## Day 47" in two
    unit = sc.read_wordfile("책.pdf", _wordbook_pdf("unit"))[0]
    assert "## Day 47" in unit and "## Day 48" in unit
    assert "Day\t영어" not in unit                  # 머리줄을 단어로 읽으면 안 됩니다

    # 예문은 빼고 표제어만 — 안 그러면 지울 줄이 단어 수만큼 늘어납니다
    ex, note = sc.read_wordfile("책.pdf", _wordbook_pdf("example"))
    rows, _ = sc.parse_words(ex)
    assert len(rows) == 3, rows
    assert "예문" in note
    assert not any("happens here" in r["en"] for r in rows)
    # 숙어는 예문이 아닙니다
    for phrase in ("give up", "in spite of", "in the long run"):
        assert not sc._looks_like_sentence(phrase), phrase
    assert sc._looks_like_sentence("The soil retains water well.")

    # 스캔해서 사진만 든 PDF 는 못 읽는다고 분명히 말해 줍니다
    blank, note = sc.read_wordfile("책.pdf", _wordbook_pdf("blank"))
    assert blank == "" and "스캔" in note

    # 관리자 화면에서 올리면 미리보기를 거쳐 그대로 저장됩니다
    a = admin()
    a.post("/admin/words/new", data={"name": "pdf read book"}, follow_redirects=True)
    up = a.post("/admin/words/pdf-read-book/upload", data={
        "file": (io.BytesIO(_wordbook_pdf("two")), "단어책.pdf"), "unit_name": ""},
        content_type="multipart/form-data")
    page = body(up)
    assert "읽은 내용을 확인해 주세요" in page
    assert "retain" in page and "유지하다" in page
    a.post("/admin/words/pdf-read-book/unit",
           data={"unit_name": "", "words": sc.read_wordfile("x.pdf", _wordbook_pdf("two"))[0]},
           follow_redirects=True)
    book = sc.find_wordbook("pdf-read-book")
    assert sc.word_count(book) == 6, book
    assert book["units"][0]["name"] == "Day 47"

    a.post("/admin/words/pdf-read-book/delete", follow_redirects=True)
    print("PASS  단어책 PDF 를 실제로 읽어냄 (두 칸 · 강 칸 · 예문 · 스캔)")


def test_passage_memorizing_reads_then_blanks():
    """지문 암기 — 문장마다 해석을 보고, 빈칸 5단계로 외웁니다."""
    books = sc.load_passages()["books"]
    assert books, "예시 지문이 없습니다"
    b = books[0]
    assert sc.passage_count(b) >= 3 and sc.sentence_count(b) >= 15
    for u in b["units"]:
        for x in u["items"]:
            assert x["sentences"], x
            # 해석이 문장마다 하나씩 붙어 있어야 눌러서 볼 수 있습니다
            assert all(s["ko"].strip() for s in x["sentences"]), x["title"]
            assert all(s["en"].strip() for s in x["sentences"]), x["title"]

    c = client()
    assert b["name"] in body(c.get("/memorize"))
    listing = body(c.get(f"/memorize/{b['slug']}"))
    first = b["units"][0]["items"][0]
    assert first["title"] in listing

    import html as _html
    page = body(c.get(f"/memorize/{b['slug']}/{b['units'][0]['id']}/{first['id']}"))
    for tab in ("내용이해", "직독직해", "빈칸채우기"):
        assert tab in page, tab
    # 차례가 중요합니다 — 내용부터 알고 영어로 갑니다
    assert page.index("내용이해") < page.index("직독직해") < page.index("빈칸채우기")
    # 단위가 낱말이 아니라 의미 덩어리·문장이어야 합니다
    assert "ck-row" in page and "ord-pool" in page
    plain = _html.unescape(page)                        # 따옴표는 escape 되어 나갑니다
    assert first["sentences"][0]["en"] in plain
    assert first["sentences"][0]["ko"] in plain         # 해석은 접혀 있되 실려 있습니다
    for lv in sc.BLANK_LEVELS:                          # 난이도 5단계
        assert f'data-no="{lv["no"]}"' in page, lv
    assert "sent-say" in page                           # 소리 내어 읽기

    # 시작하기 전에 무슨 이야기인지. 줄글이 아니라 흐름으로 — 학생은 다섯 줄짜리
    # 설명을 안 읽습니다. 외울 낱말은 도드라지게 합니다.
    assert "이 지문, 이런 이야기예요" in page
    br = sc.brief_of(first)
    assert br["beats"], "첫 지문에 줄거리 토막이 없습니다"
    assert br["hook"] and br["keywords"]
    assert "beat-tag" in page and "brief-hook" in page
    for beat in br["beats"]:
        assert beat["tag"] and beat["text"]
        assert sc.emphasize(beat["text"]) in plain, beat
    assert '<b class="key">' in page, "외울 낱말이 도드라지지 않습니다"
    # 별표는 굵게 바뀌고, 태그는 그대로 나가면 안 됩니다
    assert sc.emphasize("재능은 *타고난다*") == '재능은 <b class="key">타고난다</b>'
    assert "<script>" not in sc.emphasize("<script>alert(1)</script>")
    assert "*" not in page.split("brief-hook")[1][:200]

    # 직독직해는 보여 주는 것이 아니라 맞춰 보는 자리입니다
    assert "맞춰 보기" in page and "보면서 읽기" in page
    assert "우리말 어순으로 바꾸지 말고" in page
    # 맞출 자리와 우리말 조각은 문장 수만큼 있어야 합니다
    n = sum(len(sn.get("chunks") or []) for sn in first["sentences"])
    assert n >= 10, n
    assert page.count('"en":') >= n or "chunk_rows" in page or "ck-test" in page

    # 내용이해는 우리말이 먼저입니다. 차례 세우기도 우리말 문장으로 합니다.
    assert "우리말로 읽어 보기" in page and "이야기 차례 세우기" in page
    assert "먼저 이 말부터" in page                     # 어려운 개념 풀이
    for t in first.get("terms") or []:
        assert t["word"] in plain and t["note"][:20] in plain, t["word"]
    assert first.get("terms"), "첫 지문에 풀어 둔 말이 없습니다"

    # 퀘스트 — 브라우저에만 남습니다. 서버로 아무것도 안 보냅니다.
    assert "오늘의 퀘스트" in page and "localStorage" in page
    assert "q-dot" in page

    # 빈칸 난이도 — 힌트를 먼저 거두고, 그다음 범위를 넓힙니다
    lv = sc.BLANK_LEVELS
    assert len(lv) == 6
    assert [x["hint"] for x in lv] == ["first", "len", "len", "none", "none", "none"]
    assert [x["scope"] for x in lv] == ["content"] * 4 + ["all"] * 2
    rank = lambda x: ({"content": 0, "all": 1}[x["scope"]],
                      {"first": 0, "len": 1, "none": 2}[x["hint"]], x["ratio"])
    for a, b2 in zip(lv, lv[1:]):
        assert rank(a) < rank(b2), (a["name"], b2["name"])   # 뒤로 갈수록 어려워야 합니다
        # 한 단계에 두 가지가 한꺼번에 어려워지면 거기서 벽이 섭니다
        moved = (a["scope"] != b2["scope"]) + (a["hint"] != b2["hint"])
        assert moved <= 1, (a["name"], b2["name"])

    # 직독직해 — 문장을 의미 덩어리로 끊습니다
    ck = sc.auto_chunks("The city council has announced a plan to turn the old "
                        "railway line into a walking path.")
    assert len(ck) >= 3 and " ".join(ck).split() == \
        "The city council has announced a plan to turn the old railway line " \
        "into a walking path.".split(), ck
    assert all(len(c.split()) >= 2 for c in ck), ck    # 한 낱말짜리 조각은 안 만듭니다
    # 덩어리 해석은 영어 차례 그대로여야 합니다 (예시 지문에 다 붙여 두었습니다)
    every = [c for u in b["units"] for x in u["items"]
             for sn in x["sentences"] for c in (sn.get("chunks") or [])]
    assert every and all(c["ko"].strip() for c in every), "덩어리 해석이 빈 곳이 있습니다"

    # 손으로 '/' 를 넣어 두시면 그쪽이 이깁니다
    saved = {"en": "A b c d.", "chunks": [{"en": "A b", "ko": "가"}, {"en": "c d.", "ko": "나"}]}
    assert sc.chunk_pairs(saved) == [{"en": "A b", "ko": "가"}, {"en": "c d.", "ko": "나"}]
    assert sc.split_chunks("A b / c d.") == ["A b", "c d."]
    assert sc.split_chunks("끊은 데가 없음") == []

    # 문법 — 이 지문에 실제로 든 것만. 담은 것이 없으면 갈래가 안 열립니다
    marked = [(u, x, i) for u in b["units"] for x in u["items"]
              for i, sn in enumerate(x["sentences"]) if sn.get("grammar")]
    assert marked, "예시 지문에 문법 자리가 하나도 없습니다"
    u0, x0, _ = marked[0]
    gram = body(c.get(f"/memorize/{b['slug']}/{u0['id']}/{x0['id']}"))
    # 무엇이 있는지 미리 알려 주지 않습니다. 자리만 칠하고 '이게 뭐냐' 를 묻습니다.
    assert "gr-mark" in gram and "이건 어떤 문법일까요?" in gram
    assert "gr-choices" in gram
    tags = {t for _g, t, _p, _n in sc.GRAMMAR_RULES} | set(sc.GRAMMAR_PHRASES)
    for sn in x0["sentences"]:
        for m in sc.grammar_quiz(sn["en"], sn.get("grammar")):
            assert m["text"] and m["text"] in sn["en"], m
            assert m["text"] == m["text"].strip()      # 형광펜 양 끝에 빈칸이 없어야
            assert len(m["text"].split()) <= 3, m      # 딱 그 문법 자리만 칠합니다
            assert m["tag"] in m["choices"] and len(m["choices"]) == 4, m
            assert len(set(m["choices"])) == 4 and set(m["choices"]) <= tags, m
            # 오답은 같은 갈래에서 — 다른 갈래에서 뽑으면 몰라도 찍힙니다
            mine = sc.grammar_group(m["tag"])
            same = [c for c in m["choices"] if sc.grammar_group(c) == mine]
            assert len(same) == 4, (m["tag"], mine, m["choices"])
            # 보기 차례는 늘 같아야 합니다 (새로 고칠 때마다 바뀌면 외운 것과 못 가립니다)
            again = sc.grammar_quiz(sn["en"], sn.get("grammar"))
            assert [q["choices"] for q in again] == \
                [q["choices"] for q in sc.grammar_quiz(sn["en"], sn.get("grammar"))]
    # 형광펜이 겹치면 어느 쪽을 물은 것인지 알 수 없습니다
    two = sc.grammar_quiz("It means working at the edge of your ability, where mistakes are frequent.",
                          [{"tag": "관계부사", "note": ""}, {"tag": "관계부사", "note": ""}])
    assert len(two) == 1, two

    # 사장님이 주신 어법 목록이 갈래대로 다 들어 있는지
    assert sc.GRAMMAR_GROUPS == ["관계사", "준동사", "절·접속", "동사 어형",
                                 "구문·강조", "비교·부정·기타", "숙어·표현"]
    per = {}
    for g, t, _p, note in sc.GRAMMAR_RULES:
        assert g in sc.GRAMMAR_GROUPS and note.strip(), (g, t)
        per[g] = per.get(g, 0) + 1
    for g in sc.GRAMMAR_GROUPS[:-1]:
        assert per.get(g, 0) >= 5, (g, per.get(g))   # 오답 보기를 뽑을 만큼
    assert len(sc.GRAMMAR_PHRASES) >= 30
    assert all(v.strip() for v in sc.GRAMMAR_PHRASES.values())

    # 규칙마다 '딱 그 문법 자리' 만 칠하는지 하나씩 봅니다
    for tag, sent, want in [
            ("명사절 that", "Many people believe that talent is born.", "that"),
            ("관계대명사", "It is hard, which is why people avoid it.", "which"),
            ("관계부사", "the edge of your ability, where mistakes are frequent", "where"),
            ("부사절 접속사", "When scientists studied it, they found the answer.", "When"),
            ("강조구문 It ~ that", "It was John that broke the window.", "It was"),
            ("분사구문", "He left the room, humming a quiet tune.", "humming"),
            ("수동태", "The rails will be removed soon.", "be removed"),
            ("to부정사 (형용사적)", "a plan to turn the line into a path", "to turn"),
            ("비교급", "This road is wider than the old one.", "wider than"),
            ("최상급", "It was the strongest predictor of skill.", "the strongest"),
            ("가정법", "If he had money, he would buy the house.", "would buy"),
            ("가주어 - 진주어", "It is clear that the plan will work.", "It"),
            ("사역·지각동사", "The teacher made him repeat the sentence.", "made him repeat"),
            ("so ~ that", "The book was so long that nobody finished it.", "so long that"),
            ("동명사 주어", "Reading old letters is a quiet pleasure.", "Reading"),
            # 사장님이 주신 어법 목록대로 갈래마다 하나씩
            ("관계대명사 소유격", "I met a boy whose father is a pilot.", "whose"),
            ("전치사 + 관계대명사", "the room in which he slept", "in which"),
            ("관계대명사 what", "This is what you need.", "what"),
            ("복합관계사", "Whoever comes will be welcome.", "Whoever"),
            ("계속적 용법", "He was late, which annoyed her.", "which"),
            ("감정분사", "The film was boring to everyone.", "boring"),
            ("to부정사 (명사적)", "They decided to leave early.", "to leave"),
            ("to부정사 (부사적)", "He ran in order to catch the bus.", "in order to catch"),
            ("to부정사 의미상 주어", "It is easy for him to swim.", "for him to swim"),
            ("동명사 목적어", "She avoided meeting him.", "meeting"),
            ("명사절 의문사", "Nobody knows what happened.", "what"),
            ("명사절 whether·if", "I wonder whether it rains.", "whether"),
            ("상관접속사", "It is both cheap and fast.", "both cheap and"),
            ("접속사 vs 전치사", "It closed because of the rain.", "because of"),
            ("동격 that", "The fact that he lied hurt her.", "that"),
            ("완료수동태", "The road has been repaired.", "been repaired"),
            ("완료시제", "He has finished the work.", "has finished"),
            ("진행시제", "She is reading a long book.", "is reading"),
            ("완료진행", "They have been waiting for an hour.", "have been waiting"),
            ("수일치", "Each of the boys is ready.", "is"),
            ("조동사 + have p.p.", "He must have missed the train.", "must have missed"),
            ("대동사", "So do I.", "So do"),
            ("도치", "Never had he seen such a thing.", "Never"),
            ("가목적어 - 진목적어", "They made it clear that he was wrong.", "it"),
            ("5형식 목적격보어", "The noise made the room unbearable.", "unbearable"),
            ("원급 as ~ as", "It is as cold as ice.", "as cold as"),
            ("비교급 강조", "This is much better than that.", "much better"),
            ("부분부정", "Not all birds can fly.", "Not all"),
            ("재귀대명사", "He hurt himself badly.", "himself"),
            ("take advantage of", "We take advantage of the sale.", "take advantage of"),
            ("so ~ that", "The book was so long that nobody finished it.", "so long that")]:
        at = sc.grammar_span(sent, tag)
        assert at, tag
        assert sent[at[0]:at[1]] == want, (tag, sent[at[0]:at[1]])
    # 기계가 짚어 주되, 담은 것만 나갑니다
    hints = sc.grammar_hints("Many people believe that talent is something you are born with.")
    assert any(h["tag"] == "명사절 that" for h in hints), hints
    assert sc.grammar_hints("The dog ran.") == []

    # 문장 나누기 — 줄임말의 마침표에서 끊으면 문장이 토막 납니다
    got = sc.split_sentences("Mr. Kim came at 9 a.m. He left. It was fine.")
    assert got == ["Mr. Kim came at 9 a.m.", "He left.", "It was fine."], got
    # 해석 수가 안 맞으면 억지로 맞추지 않고 말해 줍니다
    rows, note = sc.pair_sentences("A cat sat. A dog ran.", "고양이가 앉았다.")
    assert [r["ko"] for r in rows] == ["고양이가 앉았다.", ""] and "수가 다릅니다" in note

    # 가릴 낱말은 내용어부터 — 기능어(the·of)부터 가리면 눈치 시험이 됩니다
    assert sc.blank_score("community") > sc.blank_score("the")
    assert sc.blank_score("13") == -1                   # 숫자는 안 가립니다

    # 단어 학습과 서로 오갈 수 있어야 합니다
    assert 'href="/memorize"' in body(c.get("/study"))
    assert 'href="/study"' in body(c.get("/memorize"))
    print("PASS  지문 암기 — 읽고(해석·소리) 외우기(빈칸 5단계)")


def test_admin_puts_a_passage_in_by_pasting():
    """본문과 해석을 통째로 붙여넣으면 문장으로 잘라 짝지어 줘야 합니다."""
    a = admin()
    a.post("/admin/passages/new", data={"name": "paste test book", "publisher": "EBS"},
           follow_redirects=True)
    slug = "paste-test-book"
    got = a.post(f"/admin/passages/{slug}/item", data={
        "unit_name": "3강", "title": "붙여넣기 시험", "source": "2025년 3월 20번",
        "body": "A cat sat on the mat. The dog ran away. Rain fell all night.",
        "trans": "고양이가 매트 위에 앉았다. 개가 달아났다. 비가 밤새 내렸다."},
        follow_redirects=True)
    assert got.status_code == 200

    book = sc.find_passage_book(slug, raw=True)
    unit = book["units"][0]
    item = unit["items"][0]
    assert unit["name"] == "3강" and item["title"] == "붙여넣기 시험"
    assert len(item["sentences"]) == 3
    assert item["sentences"][1] == {"en": "The dog ran away.", "ko": "개가 달아났다."}

    # 손님 화면에 그대로 뜹니다
    page = body(client().get(f"/memorize/{slug}/{unit['id']}/{item['id']}"))
    assert "A cat sat on the mat." in page and "고양이가 매트 위에 앉았다." in page

    # 지우면 사라집니다
    a.post(f"/admin/passages/{slug}/item/{unit['id']}/{item['id']}/delete",
           follow_redirects=True)
    assert sc.passage_count(sc.find_passage_book(slug, raw=True)) == 0
    a.post(f"/admin/passages/{slug}/delete", follow_redirects=True)
    assert sc.find_passage_book(slug, raw=True) is None
    print("PASS  지문 넣기 — 붙여넣으면 문장으로 잘라 짝지음")


def test_admin_marks_grammar_only_after_checking():
    """기계가 짚은 문법은 사장님이 확인해 담으신 것만 손님 화면에 나가야 합니다."""
    a = admin()
    a.post("/admin/passages/new", data={"name": "gram test book"}, follow_redirects=True)
    slug = "gram-test-book"
    a.post(f"/admin/passages/{slug}/item", data={
        "unit_name": "1강", "title": "문법 시험",
        "body": "Many people believe that the plan will work. The dog ran away.",
        "trans": "많은 사람들은 그 계획이 통할 것이라고 믿는다. 개가 달아났다."},
        follow_redirects=True)
    book = sc.find_passage_book(slug, raw=True)
    u, x = book["units"][0], book["units"][0]["items"][0]

    # 담기 전에는 문법 갈래가 안 열립니다
    page = body(client().get(f"/memorize/{slug}/{u['id']}/{x['id']}"))
    assert 'data-tab="gram"' not in page

    form = body(a.get(f"/admin/passages/{slug}/grammar/{u['id']}/{x['id']}"))
    assert "명사절 that" in form, "기계가 짚어 주지 않았습니다"
    for group in ("절·접속", "관계사"):                  # 갈래로 묶어 보여 줍니다
        assert group in form, group
    a.post(f"/admin/passages/{slug}/grammar/{u['id']}/{x['id']}",
           data={"g0": "명사절 that", "n0_명사절 that": "that 이하가 통째로 목적어입니다."},
           follow_redirects=True)

    after = sc.find_passage_book(slug, raw=True)["units"][0]["items"][0]
    assert after["sentences"][0]["grammar"] == [
        {"tag": "명사절 that", "note": "that 이하가 통째로 목적어입니다."}]
    assert not after["sentences"][1].get("grammar")     # 안 고른 문장은 비어 있습니다
    page = body(client().get(f"/memorize/{slug}/{u['id']}/{x['id']}"))
    assert 'data-tab="gram"' in page and "that 이하가 통째로 목적어입니다." in page

    # 체크를 풀면 다시 사라집니다
    a.post(f"/admin/passages/{slug}/grammar/{u['id']}/{x['id']}", data={}, follow_redirects=True)
    assert not sc.find_passage_book(slug, raw=True)["units"][0]["items"][0]["sentences"][0].get("grammar")
    a.post(f"/admin/passages/{slug}/delete", follow_redirects=True)
    print("PASS  문법은 확인해 담은 것만 나감")


def test_admin_writes_the_brief_as_a_flow():
    """줄거리는 줄글이 아니라 흐름 토막으로 넣습니다."""
    a = admin()
    a.post("/admin/passages/new", data={"name": "brief test book"}, follow_redirects=True)
    slug = "brief-test-book"
    a.post(f"/admin/passages/{slug}/item", data={
        "unit_name": "1강", "title": "줄거리 시험",
        "body": "A cat sat. The dog ran.", "trans": "고양이가 앉았다. 개가 달렸다."},
        follow_redirects=True)
    book = sc.find_passage_book(slug, raw=True)
    u, x = book["units"][0], book["units"][0]["items"][0]

    form = body(a.get(f"/admin/passages/{slug}/brief/{u['id']}/{x['id']}"))
    assert "줄글은 학생이 안 읽습니다" in form and "별표" in form
    a.post(f"/admin/passages/{slug}/brief/{u['id']}/{x['id']}", data={
        "hook": "*고양이*와 개 이야기",
        "tag": ["앞", "뒤", ""], "text": ["고양이가 *앉았다*", "개가 *달렸다*", ""],
        "keys": "cat, dog"}, follow_redirects=True)

    got = sc.brief_of(sc.find_passage_book(slug, raw=True)["units"][0]["items"][0])
    assert got["hook"] == "*고양이*와 개 이야기"
    assert len(got["beats"]) == 2, got["beats"]     # 빈 줄은 안 담깁니다
    assert got["beats"][0] == {"tag": "앞", "text": "고양이가 *앉았다*"}
    assert got["keywords"] == ["cat", "dog"]

    page = body(client().get(f"/memorize/{slug}/{u['id']}/{x['id']}"))
    assert '<b class="key">고양이</b>' in page and '<b class="key">앉았다</b>' in page
    assert "beat-tag" in page and ">cat<" in page

    # 다 비우면 줄거리 상자가 사라집니다
    a.post(f"/admin/passages/{slug}/brief/{u['id']}/{x['id']}",
           data={"hook": "", "tag": [], "text": [], "keys": ""}, follow_redirects=True)
    assert "이 지문, 이런 이야기예요" not in body(
        client().get(f"/memorize/{slug}/{u['id']}/{x['id']}"))
    a.post(f"/admin/passages/{slug}/delete", follow_redirects=True)
    print("PASS  줄거리는 흐름 토막 · 외울 낱말은 도드라지게")


def test_sample_wordbooks_are_enough_to_try_it():
    """예시 단어장은 '눌러 보면 실제로 돌아가는' 만큼 들어 있어야 합니다.

    단어가 몇 개뿐이면 뜻 고르기의 오답 보기를 못 만들고, 범위를 골라 볼
    수도 없어 화면이 도는지 알 수 없습니다.
    """
    books = [b for b in sc.load_words()["books"] if b.get("sample")]
    assert len(books) >= 2, "예시 단어장이 모자랍니다"
    for b in books:
        words = [w for u in b["units"] for w in u["words"]]
        assert len(b["units"]) >= 2, b["slug"]          # 범위를 골라 볼 수 있게
        assert len(words) >= 40, (b["slug"], len(words))
        assert b.get("publisher"), b["slug"]
        ens = [w["en"] for w in words]
        assert len(ens) == len(set(ens)), "같은 단어가 두 번 들었습니다"
        for w in words:
            assert w["ko"].strip() and w["en"].strip(), w
            # 철자 채우기는 영문자만 낼 수 있습니다
            assert all(c.isascii() for c in w["en"]), w["en"]

    # 화면 두 곳에서 다 보이고, 실제로 풀립니다
    c = client()
    for b in books:
        assert b["name"] in body(c.get("/study")), b["name"]
        assert b["name"] in body(c.get("/words")), b["name"]
        ids = [u["id"] for u in b["units"]]
        page = body(c.get(f"/words/{b['slug']}/study?kind=choice&"
                          + "&".join(f"unit={i}" for i in ids) + "&n=10"))
        assert "문제" in page and b["name"] in page

    # 관리자에서 예시만 다시 깔 수 있어야 합니다 (내 단어장은 그대로)
    a = admin()
    a.post("/admin/words/new", data={"name": "keep me words"}, follow_redirects=True)
    assert "예시 단어장 불러오기" in body(a.get("/admin/words"))
    assert not sc.stale_sample_words(), "지금은 최신판인데 뒤처졌다고 합니다"
    raw = sc.load_raw_words()
    for b in raw["books"]:
        if b.get("sample"):
            b["units"] = b["units"][:1]                  # 예시를 옛 판인 척 줄입니다
            b.pop("sample", None)                        # 옛 판에는 이 표시가 없었습니다
    sc.save_words(raw)
    # 뒤처지면 관리자 화면이 눈에 띄게 알려 줘야 합니다 (모르면 '예시가 없다' 가 됩니다)
    late = sc.stale_sample_words()
    assert len(late) == 2, late
    page = body(a.get("/admin/words"))
    assert "예시 단어장이 옛 판입니다" in page and "alert-warn" in page
    a.post("/admin/words/refresh-samples", follow_redirects=True)
    after = sc.load_raw_words()
    assert any(b["slug"] == "keep-me-words" for b in after["books"]), "내 단어장이 사라졌습니다"
    # 옛 판에 'sample' 표시가 없어도 새 판으로 바뀌어야 합니다 (주소가 같으면 우리 것)
    for b in books:
        assert sc.word_count(sc.find_wordbook(b["slug"], raw=True)) == \
            sum(len(u["words"]) for u in b["units"]), b["slug"]
    assert not sc.stale_sample_words()
    assert "예시 단어장이 옛 판입니다" not in body(a.get("/admin/words"))
    a.post("/admin/words/keep-me-words/delete", follow_redirects=True)
    print("PASS  예시 단어장 — 눌러 보면 실제로 돌아감 · 관리자에서 다시 깔기")


def test_study_and_sheet_share_one_wordbook():
    """단어 학습과 단어 시험지는 같은 단어를 봐야 합니다.

    한쪽에만 있는 단어가 생기면, 화면에서 푼 것을 시험지로 뽑을 수 없고
    틀린 단어를 다시 낼 수도 없습니다. 두 화면이 단어장 하나를 함께 씁니다.
    PDF 로 올린 단어도 마찬가지여야 합니다 — 올리는 길이 하나이기 때문입니다.
    """
    a = admin()
    a.post("/admin/words/new", data={"name": "shared word book", "publisher": "EBS"},
           follow_redirects=True)
    slug = "shared-word-book"
    # 올리는 길은 하나 — PDF 하나만 올리고 두 화면을 다 봅니다
    a.post(f"/admin/words/{slug}/unit",
           data={"unit_name": "", "words": sc.read_wordfile("책.pdf", _wordbook_pdf("unit"))[0]},
           follow_redirects=True)

    book = sc.find_wordbook(slug)
    words = {(w["en"], w["ko"]) for u in book["units"] for w in u["words"]}
    assert len(words) == 6, words
    assert [u["name"] for u in book["units"]] == ["Day 47", "Day 48"]

    c = client()
    # 두 화면 모두 같은 단어장을 읽습니다 (읽는 함수가 하나여야 합니다)
    assert store.flat_words(book) == store.flat_words(sc.find_wordbook(slug))
    ids = [u["id"] for u in book["units"]]
    sheet = body(c.get(f"/words/{slug}"))
    study = body(c.get(f"/words/{slug}/study?kind=choice&"
                       + "&".join(f"unit={i}" for i in ids) + "&n=6"))
    for name in ("Day 47", "Day 48"):
        assert name in sheet, name                 # 시험지는 강을 골라 뽑습니다
    # 학습 화면에 실린 단어는 모두 그 단어장에서 온 것이어야 합니다
    for en, ko in words:
        assert en in study, en

    # 올린 단어를 고치면 두 화면에 함께 반영됩니다 (한쪽만 옛것이면 안 됩니다)
    a.post(f"/admin/words/{slug}/unit",
           data={"unit_name": "Day 49", "words": "keen\t예리한"}, follow_redirects=True)
    again = sc.find_wordbook(slug)
    assert sc.word_count(again) == 7
    assert "Day 49" in body(c.get(f"/words/{slug}"))   # 시험지 범위에 새 강이 섭니다
    new_id = [u["id"] for u in again["units"] if u["name"] == "Day 49"][0]
    assert "keen" in body(c.get(f"/words/{slug}/study?kind=spell&unit={new_id}&n=1"))

    # 단어 학습 목록과 시험지 목록에 같은 책이 서고, 서로 오갈 수 있습니다
    for url in ("/study", "/words"):
        assert "shared word book" in body(c.get(url)), url
    assert 'href="/study"' in body(c.get("/words"))
    assert 'href="/words"' in body(c.get("/study"))

    a.post(f"/admin/words/{slug}/delete", follow_redirects=True)
    print("PASS  단어 학습 · 시험지가 단어장 하나를 함께 씀 (PDF 로 올린 것도)")


def test_word_study_screen():
    """화면에서 한 문제씩 푸는 자리 — 뜻 고르기 · 철자 채우기 · 소리 · 오답 시험지."""
    import json as _json
    a = admin()
    a.post("/admin/words/new", data={"name": "study test book", "publisher": "EBS"},
           follow_redirects=True)
    slug = "study-test-book"
    a.post(f"/admin/words/{slug}/unit", data={
        "unit_name": "Day 1",
        "words": "\n".join(f"word{i}\t뜻{i}번" for i in range(12))},
        follow_redirects=True)

    page = body(client().get(f"/words/{slug}/study?kind=choice&kind=spell&n=8&seed=42"))
    deck = _json.loads(page.split('id="sq-deck">', 1)[1].split("</script>", 1)[0]
                       .replace("\\u003c", "<"))
    assert len(deck) == 8, len(deck)

    kinds = {q["kind"] for q in deck}
    assert kinds == {"choice", "spell"}, kinds
    for q in deck:
        assert q["en"] and q["ko"]
        assert "no" in q                      # 틀린 것을 시험지로 넘길 때 쓰는 번호
        if q["kind"] == "choice":
            assert len(q["choices"]) == 5 and len(set(q["choices"])) == 5
            assert q["choices"][q["answer"]] == q["ko"]       # 정답이 보기 안에 있어야
        else:
            keys = set(q["keys"])
            # 알파벳이 아닌 글자(빈칸·붙임표·숫자)는 화면에 미리 채워 두므로 자판에 없습니다
            need = {c for c in q["en"].lower() if c.isascii() and c.isalpha()}
            assert need <= keys, (q["en"], q["keys"])          # 답을 칠 수 있어야
            assert len(keys) > len(need)                        # 미끼도 섞여야
            assert q["vowels"] and set(q["vowels"]) <= keys

    # 소리는 브라우저에 든 목소리로 냅니다 — 파일을 따로 받지 않습니다
    assert "speechSynthesis" in page
    assert "en-US" in page and "ko-KR" in page
    # 철자 문제에서 영단어를 들으면 오답으로 둡니다
    assert "영단어 듣기는 오답으로 기록돼요" in page

    # 틀린 것만 다시 — 번호로 골라 다시 냅니다
    only = ",".join(str(q["no"]) for q in deck[:3])
    again = body(client().get(f"/words/{slug}/study?only={only}"))
    deck2 = _json.loads(again.split('id="sq-deck">', 1)[1].split("</script>", 1)[0]
                        .replace("\\u003c", "<"))
    assert len(deck2) == 3
    assert {q["no"] for q in deck2} == {q["no"] for q in deck[:3]}

    # 틀린 단어가 그대로 시험지 PDF 로 넘어갑니다 (이미 있던 길을 씁니다)
    picks = "&".join(f"pick={q['no']}" for q in deck[:3])
    sheet = client().get(f"/words/{slug}/sheet?kind=en_ko&n_en_ko=3&{picks}")
    assert sheet.status_code == 200
    pdf = client().get(f"/words/{slug}/sheet.pdf?kind=en_ko&n_en_ko=3&{picks}")
    assert pdf.status_code == 200 and pdf.data[:4] == b"%PDF"

    # 시험지 만드는 화면에서 들어가는 길이 있어야 합니다
    book = body(client().get(f"/words/{slug}"))
    assert f"/words/{slug}/study" in book and "화면에서 바로 풀어 보기" in book

    a.post(f"/admin/words/{slug}/delete", follow_redirects=True)
    print("PASS  단어 풀기 — 뜻 고르기 · 철자 · 오답 시험지")


def test_hidden_really_hides():
    """display 를 정해 둔 자리도 hidden 이면 숨어야 합니다.

    .sq-choices{display:grid} 가 브라우저 기본 [hidden] 규칙을 이겨서,
    철자 문제에 앞 문제의 보기가 그대로 남아 있던 일이 있었습니다.
    """
    css = body(client().get("/static/store.css"))
    assert "[hidden]{display:none !important;}" in css
    print("PASS  hidden 은 display 규칙을 이김")


def test_policy_tables_stack_on_phone():
    """폰에서 규정 표가 두 칸으로 서면 오른쪽이 좁아 두세 글자씩 끊깁니다."""
    guide = body(client().get("/guide"))
    # 칸 너비를 태그 안에 박아 두면 좁은 화면에서 못 풉니다
    table = guide.split('class="spec policy-table', 1)[1]
    assert 'style="width:' not in table.split("</table>", 1)[0]
    css = body(client().get("/static/store.css"))
    narrow = css.split("@media (max-width: 640px)")
    stacked = [b for b in narrow[1:] if ".policy-table th" in b]
    assert stacked, "좁은 화면에서 규정 표를 쌓는 규칙이 없습니다"
    rule = stacked[0]
    assert "display:block" in rule and "width:auto" in rule
    print("PASS  폰에서 규정 표는 위아래로 쌓임")


def test_nanumsquareround_font_is_served():
    """모든 글자가 나눔스퀘어라운드로 나와야 합니다(외부 CDN 없이 자체 제공)."""
    css = body(client().get("/static/store.css"))
    assert "NanumSquareRound" in css
    assert "cdn.jsdelivr.net" not in css
    for weight in ("R", "B"):
        resp = client().get(f"/static/fonts/NanumSquareRound{weight}.woff")
        assert resp.status_code == 200 and resp.data[:4] == b"wOFF"
    print("PASS  나눔스퀘어라운드 글꼴 제공")


def test_order_page_cannot_be_enumerated():
    """주문번호를 찍어 남의 이름·연락처를 훔쳐볼 수 없어야 합니다."""
    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "비밀손님",
        "phone": "010-7777-1234", "email": "secret@example.com", "agree": "1"})
    key = resp.headers["Location"].rsplit("/", 1)[-1]
    assert len(key) >= 20, "주소 열쇠가 너무 짧습니다"

    conn = sc.sqlite3.connect(sc.DB_PATH)
    order_no = conn.execute("SELECT order_no FROM orders WHERE view_key = ?",
                            (key,)).fetchone()[0]
    # 열쇠를 가진 본인은 열리고 — 입금자명·이메일이 보여야 입금을 할 수 있습니다.
    ok = client().get(f"/order/done/{key}")
    assert ok.status_code == 200
    assert "비밀손님" in body(ok) and "secret@example.com" in body(ok)
    # 주문번호를 찍어서는 못 엽니다. (여기가 막혀야 고객 명단이 안 샙니다)
    assert client().get(f"/order/done/{order_no}").status_code == 404
    # 열쇠를 한 글자만 바꿔도 안 됩니다.
    # (원래 글자와 다른 것으로 바꿔야 합니다. 우연히 같으면 시험이 헛돕니다)
    other = "y" if key[-1] == "x" else "x"
    assert client().get(f"/order/done/{key[:-1]}{other}").status_code == 404
    print("PASS  주문 확인 화면 열거 차단")


def test_security_headers_everywhere():
    for path in ("/", "/products", "/guide"):
        h = client().get(path).headers
        assert h.get("X-Content-Type-Options") == "nosniff", path
        assert "Referrer-Policy" in h, path
        assert "Permissions-Policy" in h, path
    print("PASS  공통 보안 헤더")


def test_public_forms_are_rate_limited():
    """장난으로 주문을 쏟아붓지 못하게 막습니다."""
    keep = sc.FORM_MAX
    sc.FORM_MAX = 5                      # 이 테스트 동안만 낮춰서 확인
    sc._form_hits.clear()
    try:
        c = client()
        data = {"slug": "mock-2026-06-g3-analysis", "name": "도배",
                "phone": "010-0000-1111", "email": "flood@example.com", "agree": "1"}
        codes = [c.post("/order", data=data).status_code for _ in range(8)]
        assert codes.count(302) == 5, codes          # 5번까지만 받고
        assert codes[-1] == 429                      # 그다음은 막힘
        assert "잠시 뒤에" in body(c.post("/order", data=data))
    finally:
        sc.FORM_MAX = keep
        sc._form_hits.clear()
    print("PASS  공개 폼 남용 제한")


def test_file_path_traversal_blocked():
    assert client().get("/samples/..%2f..%2fstore.py").status_code == 404
    assert admin().get("/admin/submissions/file/..%2f..%2fstore.py").status_code == 404
    print("PASS  폴더 밖 파일 요청 차단")


def test_uses_temp_data_only():
    """테스트가 진짜 store_data 를 건드리면 안 됩니다."""
    real = Path(__file__).resolve().parent.parent / "store_data"
    for path in (sc.DATA_DIR, sc.SAMPLE_DIR, sc.SUBMIT_DIR, sc.DELIVER_DIR,
                 sc.FREE_DIR, sc.DB_PATH):
        assert real not in Path(path).resolve().parents and Path(path).resolve() != real, path
    print("PASS  실제 데이터 폴더를 건드리지 않음")


# ---- 무료 자료실 ----------------------------------------------------------
def _put_free_file(slug: str, name: str = "sample.pdf") -> None:
    folder = sc.free_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(b"%PDF-1.4 free\n")


def test_free_list_hides_items_without_files():
    """파일이 없는 자료를 목록에 늘어놓으면 '준비 중' 버튼만 가득 찹니다."""
    text = body(client().get("/free"))
    assert "곧 올라옵니다" in text                     # 준비 중 칸에는 보이고
    assert "무료로 받기" not in text                   # 받기 버튼은 아직 없어야
    _put_free_file("2026-03-goh1-oneline")
    text = body(client().get("/free"))
    assert "무료로 받기" in text
    assert "고1 3월 학력평가 한줄해석" in text
    print("PASS  무료 자료실 — 파일 있는 것만 목록에")


def test_free_open_item_downloads_without_email():
    """한줄해석 같은 가벼운 자료는 이메일 없이 바로 받아야 합니다."""
    _put_free_file("2026-03-goh1-oneline")
    c = client()
    page = body(c.get("/free/2026-03-goh1-oneline"))
    assert "받으실 파일" in page
    assert "이메일만 적으면" not in page
    got = c.get("/free/2026-03-goh1-oneline/file/0")
    assert got.status_code == 200 and got.data.startswith(b"%PDF")
    print("PASS  가벼운 무료 자료는 그냥 받기")


def test_free_gated_item_needs_email():
    """직독직해는 이메일을 적어야 열립니다."""
    _put_free_file("2026-03-goh3-literal")
    c = client()
    page = body(c.get("/free/2026-03-goh3-literal"))
    assert "이메일만 적으면" in page and "받으실 파일" not in page
    # 이메일 없이 파일 주소를 직접 쳐도 안 열립니다
    assert c.get("/free/2026-03-goh3-literal/file/0").status_code == 302

    bad = c.post("/free/2026-03-goh3-literal/get", data={"email": "엉터리", "agree": "1"})
    assert bad.status_code == 400 and "정확히 적어" in body(bad)

    ok = c.post("/free/2026-03-goh3-literal/get",
                data={"email": "teacher@school.com", "agree": "1", "news": "1"},
                follow_redirects=True)
    assert "받으실 파일" in body(ok)
    assert c.get("/free/2026-03-goh3-literal/file/0").status_code == 200

    rows = body(admin().get("/admin/mail"))        # 명단은 메일 화면 안에 있습니다
    assert "teacher@school.com" in rows and "고3 3월 학력평가 직독직해" in rows
    print("PASS  직독직해는 이메일 받고 내어 주기")


def test_free_notify_collects_email():
    c = client()
    c.post("/free/notify", data={"email": "alarm@school.com"}, follow_redirects=True)
    assert "alarm@school.com" in body(admin().get("/admin/mail"))
    assert "alarm@school.com" in body(admin().get("/admin/leads.csv"))
    print("PASS  새 자료 알림 신청")


def test_admin_creates_free_item_end_to_end():
    """관리자 화면에서 만든 무료 자료가 고객 화면에 그대로 나와야 합니다."""
    a = admin()
    resp = a.post("/admin/free/new", data={
        "slug": "test-free-item", "title": "고2 6월 모평 한줄해석",
        "summary": "전 지문 한 줄 해석", "grade": "고2", "exam": "2026년 6월 모의평가",
        "kinds": ["oneline_ko"], "gate": "open", "date": "2026-06-05",
        "body": "설명입니다.", "active": "1"}, follow_redirects=True)
    assert resp.status_code == 200
    # 파일이 없으면 아직 '곧 올라옵니다'
    assert "무료로 받기" not in body(client().get("/free")).split("곧 올라옵니다")[0] \
        or "고2 6월 모평 한줄해석" in body(client().get("/free"))
    _put_free_file("test-free-item")
    text = body(client().get("/free"))
    assert "고2 6월 모평 한줄해석" in text

    # 종류로 필터링
    assert "고2 6월 모평 한줄해석" in body(client().get("/free?kind=oneline_ko"))
    assert "고2 6월 모평 한줄해석" not in body(client().get("/free?kind=literal"))

    a.post("/admin/free/test-free-item/delete", follow_redirects=True)
    assert "고2 6월 모평 한줄해석" not in body(client().get("/free"))
    print("PASS  관리자에서 무료 자료 만들기 → 고객 화면 → 지우기")


def test_free_kind_suggests_email_gate():
    """직독직해가 들어가면 이메일 받기를 기본으로 잡아야 합니다."""
    assert sc.suggested_gate(["oneline_ko"]) == "open"
    assert sc.suggested_gate(["side", "literal"]) == "email"
    # 폼에서 gate 를 안 보내도 종류를 보고 정합니다
    import store_admin as sa
    item, errors = sa.freebie_from_form(
        _fake_form({"slug": "x-gate-test", "title": "제목", "kinds": ["literal"], "gate": ""}))
    assert not errors and item["gate"] == "email"
    print("PASS  직독직해면 이메일 받기를 자동으로 권함")


class _fake_form(dict):
    """getlist 가 있는 아주 작은 폼 흉내."""
    def getlist(self, key):
        value = self.get(key, [])
        return value if isinstance(value, list) else [value]

    def get(self, key, default=None):
        value = dict.get(self, key, default)
        return value if not isinstance(value, list) else (value[0] if value else default)


# ---- 검색 등록 ------------------------------------------------------------
def test_seo_tags_on_public_pages():
    home = body(client().get("/"))
    assert 'rel="canonical"' in home
    assert '"@type": "Organization"' in home
    detail = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert '"@type": "Product"' in detail and '"priceCurrency": "KRW"' in detail
    assert '"@type": "BreadcrumbList"' in detail
    # JSON 문법이 깨지면 검색엔진이 통째로 버립니다
    for chunk in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            detail + home, re.S):
        json.loads(chunk)
    print("PASS  검색용 표시(canonical · 구조화 데이터)")


def test_seo_verification_code_paste():
    """네이버가 주는 meta 태그를 통째로 붙여 넣어도 코드만 뽑아내야 합니다."""
    a = admin()
    a.post("/admin/seo", data={
        "naver": '<meta name="naver-site-verification" content="navercode123" />',
        "google": "googlecode456"}, follow_redirects=True)
    home = body(client().get("/"))
    assert 'name="naver-site-verification" content="navercode123"' in home
    assert 'name="google-site-verification" content="googlecode456"' in home
    print("PASS  검색 등록 확인 코드 붙여넣기")


def test_sitemap_lists_free_items():
    _put_free_file("2026-03-goh1-oneline")
    xml = body(client().get("/sitemap.xml"))
    assert "/free" in xml and "/free/2026-03-goh1-oneline" in xml
    print("PASS  사이트맵에 무료 자료실 포함")


def test_lineup_offers_sample_pdf():
    """샘플 PDF는 이제 라인업의 자료마다 붙습니다."""
    sc.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    (sc.SAMPLE_DIR / "analysis-sample.pdf").write_bytes(b"%PDF-1.4 sample\n")
    data = sc.load_materials()
    for m in data["materials"]:
        if m["id"] == "analysis":
            m["sample_file"] = "analysis-sample.pdf"
    sc.save_materials(data)

    text = body(client().get("/lineup"))
    assert "지문분석지 샘플 PDF" in text
    got = client().get("/samples/analysis-sample.pdf")
    assert got.status_code == 200 and got.data.startswith(b"%PDF")

    # 파일이 없는 자료에는 버튼이 붙지 않아야 합니다
    assert "필생보 샘플 PDF" not in text
    print("PASS  라인업 자료마다 샘플 PDF")


def test_free_search_and_filters():
    _put_free_file("2026-03-goh1-oneline")
    _put_free_file("2026-03-goh2-side")

    hit = body(client().get("/free?q=한줄해석"))
    assert "고1 3월 학력평가 한줄해석" in hit
    assert "고2 3월 학력평가 좌지문우해석" not in hit

    by_grade = body(client().get("/free?grade=고2"))
    assert "좌지문우해석" in by_grade and "고1 3월 학력평가 한줄해석" not in by_grade

    by_exam = body(client().get("/free?exam=2026년 3월 학력평가"))
    assert "고1 3월 학력평가 한줄해석" in by_exam

    miss = body(client().get("/free?q=없는자료이름"))
    assert "조건에 맞는 자료가 없습니다" in miss
    print("PASS  무료 자료실 검색 · 학년 · 종류 · 시험 필터링")


def test_policy_sections_are_filled_in():
    """환불·이용범위·개인정보는 사장님이 따로 쓰지 않아도 되게 채워 둡니다."""
    text = body(client().get("/guide"))
    for must in ("환불 규정 (청약철회)", "전자상거래법 제17조",
                 "자료 이용 범위", "이렇게 쓰실 수 있습니다", "이건 안 됩니다",
                 "개인정보 처리방침", "수집하는 항목과 목적", "보유 기간",
                 "제3자 제공", "이용자의 권리", "개인정보 보호책임자"):
        assert must in text, must
    assert '"@type": "FAQPage"' in text          # 구글에 질문·답이 펼쳐지도록
    print("PASS  약관 3종이 업계 표준 내용으로 채워짐")


def test_request_menu_renamed_to_jaryo():
    text = body(client().get("/"))
    assert "교재 요청" not in text
    assert "자료 요청" in body(client().get("/custom"))
    print("PASS  '교재 요청' → '자료 요청'")


def test_page_width_uses_the_screen():
    """넓은 화면에서 좌우가 허전하지 않도록, 내용 폭을 한 곳에서 정합니다."""
    css = open("store_static/store.css", encoding="utf-8").read()
    # 폭은 :root 의 값 하나로 정하고, 쓰는 곳은 그 값을 따라갑니다
    assert "--wrap:1180px" in css and "--wrap-narrow:820px" in css
    assert ".wrap{max-width:var(--wrap);" in css
    assert ".narrow{max-width:var(--wrap-narrow);}" in css
    assert "max-width:1080px" not in css          # 따로 박아 둔 값이 남아 있으면 안 됩니다
    # 아주 넓은 화면에서는 더 벌립니다
    assert "@media (min-width:1600px){ :root{ --wrap:1280px;" in css
    # 폰에서는 좌우 20px 을 그대로 지킵니다
    assert "--gutter:clamp(20px," in css
    print("PASS  넓은 화면에서 좌우 여백 줄이기 (내용 1180 · 1600px 이상 1280)")


def test_brand_is_korean_for_search():
    """검색은 한글로 일어납니다. 이름은 한글, 로고 그림만 영문으로 둡니다."""
    c = client()
    home = body(c.get("/"))
    import json as _json
    shipped = _json.load(open("store_data/site.json", encoding="utf-8"))
    assert shipped["brand"] == "오르티카잉"
    assert shipped["business"]["company"] == "오르티카잉"
    assert shipped["brand_en"] == "Ortica"

    # 로고 그림은 영문 그대로 두되, 이름은 한글로 읽히게 합니다
    assert 'aria-label="오르티카잉"' in home
    assert "Ortica<i>English</i>" in home

    # 검색엔진에 '오르티카잉'·'Ortica' 가 같은 곳임을 알려 줍니다
    import json as _j, re as _re
    blocks = [_j.loads(m) for m in
              _re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, _re.S)]
    org = next(b for b in blocks if b.get("@type") == "Organization")
    assert org["name"] == "오르티카잉"
    assert set(org["alternateName"]) == {"Ortica English", "Ortica",
                                        "오르티카잉글리시", "오르티카", "오르티카영어"}

    # 메일 제목도 한글 이름을 씁니다
    assert "[오르티카잉]" in open("store.py", encoding="utf-8").read()
    assert "Ortica영어" not in open("store.py", encoding="utf-8").read()

    # 로고에 새길 영문 이름은 관리자 화면에서 고칩니다
    assert 'name="brand_en"' in body(admin().get("/admin/settings"))
    print("PASS  이름은 한글 '오르티카잉' · 로고 글자만 영문")


def test_old_brand_is_renamed_even_on_the_live_disk():
    """상호를 바꾸면 이미 저장된 글에서도 같이 바뀌어야 합니다.

    자료 파일은 배포해도 안 덮이는 디스크에 있어서, 파일만 고쳐서는 이미
    돌아가는 사이트에 안 내려갑니다. 읽을 때마다 바꿔야 확실히 바뀝니다.
    """
    import store_common as sc

    # 조사까지 같이 고칩니다. 받침이 생겼으니까요.
    assert sc.rename_brand("오르티카영어") == "오르티카잉"
    assert sc.rename_brand("고등영어자료는 오르티카로 정착") == "고등영어자료는 오르티카잉으로 정착"
    assert sc.rename_brand("오르티카영어가 만듭니다") == "오르티카잉이 만듭니다"
    assert sc.rename_brand("저작권은 오르티카영어에 있으며") == "저작권은 오르티카잉에 있으며"
    assert sc.rename_brand("오르티카영어를 찾으셨나요") == "오르티카잉을 찾으셨나요"
    assert sc.rename_brand("오르티카영어(Ortica)") == "오르티카잉(Ortica)"

    # 사업자등록 상호는 그대로 둡니다. 사업자 정보란에는 등록증에 적힌
    # 이름이 그대로 있어야 합니다.
    assert sc.rename_brand("오르티카잉글리시") == "오르티카잉글리시"
    assert sc.BRAND_LEGAL == "오르티카잉글리시"

    # 이미 바뀐 글은 두 번 바꾸지 않습니다
    assert sc.rename_brand("오르티카잉 라인업") == "오르티카잉 라인업"
    assert sc.rename_brand(sc.rename_brand("오르티카영어")) == "오르티카잉"

    # 조사 뒤에 또 한글이 오면 조사가 아니라 낱말입니다
    assert sc.rename_brand("오르티카라인업") == "오르티카잉라인업"
    assert sc.rename_brand("오르티카 영어학원") == "오르티카잉 영어학원"

    # 글·목록·표를 통째로 훑습니다
    assert sc.rename_brand({"a": ["오르티카영어", 3], "b": None}) == \
        {"a": ["오르티카잉", 3], "b": None}

    # 옛 이름이 그대로 심긴 디스크를 흉내 내 봅니다
    keep = sc.load_site()
    try:
        stale = json.loads(json.dumps(keep))
        stale["brand"] = "오르티카영어"
        stale["tagline"] = "고등영어자료는 오르티카로 정착"
        stale["policy"]["license"] = "저작권은 오르티카영어에 있으며"
        sc.save_site(stale)

        fresh = sc.load_site()
        assert fresh["brand"] == "오르티카잉"
        assert fresh["tagline"] == "고등영어자료는 오르티카잉으로 정착"
        assert fresh["policy"]["license"] == "저작권은 오르티카잉에 있으며"

        home = body(client().get("/"))
        assert "오르티카잉" in home and "오르티카영어" not in home
    finally:
        sc.save_site(keep)
    print("PASS  옛 상호는 읽을 때마다 새 상호로 (조사까지)")


def test_search_result_title_is_editable():
    """검색 결과에 뜰 제목·설명을 관리자 화면에서 정할 수 있어야 합니다."""
    import re
    home = body(client().get("/"))
    title = re.search(r"<title>(.*?)</title>", home, re.S).group(1).strip()
    assert title == "오르티카잉 — 시험에 적합한 고등영어자료", title
    assert 'property="og:title" content="오르티카잉' in home   # 카톡 공유도 같은 제목
    import re as _re
    desc = _re.search(r'name="description" content="(.*?)"', home).group(1)
    assert len(desc) <= 90, f"설명이 {len(desc)}자입니다. 검색 결과에서 잘립니다"

    a = admin()
    a.post("/admin/seo", data={"seo_title": "바꾼 제목 : 오르티카잉",
                               "seo_description": "바꾼 설명입니다.",
                               "naver": "", "google": ""}, follow_redirects=True)
    home = body(client().get("/"))
    assert "<title>바꾼 제목 : 오르티카잉</title>" in home
    assert 'name="description" content="바꾼 설명입니다."' in home
    # 관리자 화면에 미리보기가 있어야 합니다
    assert "이렇게 뜹니다" in body(a.get("/admin/seo"))
    print("PASS  검색 결과 제목·설명을 화면에서 정하기")


# ---- 올 때마다 바뀌는 자리 -------------------------------------------------
def test_notice_shows_live_now_section():
    """'지금 오르티카잉'(새 자료 · 다음 시험)는 공지 화면에 둡니다."""
    text = body(client().get("/notice"))
    assert "지금 오르티카잉" in text
    assert "새로 올라왔습니다" in text and "다음 시험까지" in text
    # 자료 올리는 일정을 약속하지 않기로 했습니다
    assert "이렇게 올립니다" not in text
    # 첫 화면은 가볍게 — 같은 자리를 두 번 두지 않습니다
    home = body(client().get("/"))
    assert "지금 오르티카잉" not in home
    # 다만 히어로의 D-day 배지는 공지의 시험 일정으로 이어져야 합니다
    assert 'href="/notice#exams"' in home
    print("PASS  공지에 '지금 오르티카잉' — 새 자료 · 다음 시험 D-day")


def test_home_previews_every_category():
    """분류마다 교재를 몇 권씩 미리 보여 주는 자리는 오르티카잉 라인업입니다."""
    text = body(client().get("/lineup"))
    assert "어떤 자료가 있나" in text
    for name in ("교과서", "모의고사", "EBS 부교재", "형광펜 독해"):
        assert name in text, name
    # 분류마다 '전체 보기' 로 이어져야 합니다
    for cid in ("textbook", "mock", "ebs", "highlighter"):
        assert f"category={cid}" in text, cid
    # 한 분류에 세 권까지만
    import re
    rows = re.findall(r'class="cat-books">(.*?)</div>\s*</div>', text, re.S)
    for row in rows:
        assert row.count('class="cat-book') <= 3
    print("PASS  라인업이 분류마다 교재를 몇 권씩 미리 보여 줌")


def test_units_follow_what_the_admin_uploaded():
    """강 체크박스는 올리신 파일대로 만들어집니다. 교재마다 강 수가 다릅니다."""
    import io as _io, zipfile, re as _re
    a = admin()

    def upload(book, units):
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for no in range(1, units + 1):
                for name in ("지문분석지", "17종 변형문제"):
                    zf.writestr(f"{no}강_{name}.pdf", b"%PDF-1.4 x")
        look = body(a.post("/admin/products/bulk",
                           data={"file": (_io.BytesIO(buf.getvalue()), "묶음.zip")},
                           content_type="multipart/form-data"))
        token = _re.search(r'name="token" value="([^"]+)"', look).group(1)
        paths = [f"{n}강_{m}.pdf" for n in range(1, units + 1)
                 for m in ("지문분석지", "17종 변형문제")]
        a.post("/admin/products/bulk/save",
               data={"token": token, "book": book, "passages": "6", "path": paths},
               follow_redirects=True)

    upload("highlighter-basic", 18)          # 올림포스처럼 18강
    upload("highlighter-master", 24)         # 수능특강처럼 24강

    def chips(slug):
        page = body(client().get(f"/books/{slug}"))
        part = page[page.index('id="unit-chips"'):]
        return part.count('class="ur-pick chip"'), page

    n18, page18 = chips("highlighter-basic")
    n24, page24 = chips("highlighter-master")
    assert n18 == 18, n18
    assert n24 == 24, n24
    assert "모두 18강" in page18 and "모두 24강" in page24
    assert "18강" in page18 and "19강" not in page18      # 18강까지만
    assert "24강" in page24

    # 강마다 두 패키지 칸이 생깁니다
    assert page18.count('class="um pkg-') == 18 * 2
    assert page24.count('class="um pkg-') == 24 * 2

    # 목록에서도 강 수가 보입니다
    lst = body(client().get("/products?category=highlighter"))
    assert "18강" in lst and "24강" in lst

    # 치우기
    catalog = sc.load_raw_catalog()
    catalog["products"] = [x for x in catalog["products"]
                           if not (x.get("book", "").startswith("highlighter-")
                                   and x.get("unit"))]
    sc.save_catalog(catalog)
    print("PASS  강 체크박스가 올린 파일대로 — 교재마다 강 수가 다름")


def test_list_hides_price_until_you_open_the_book():
    """목록에서는 값부터 보여 주지 않습니다. 교재에 들어가서 값을 봅니다."""
    text = body(client().get("/products"))
    # 무엇이 들어 있는지는 보여 줍니다
    assert 'class="bg-mats"' in text and 'class="bg-open"' in text
    assert "자세히 보기 →" in text
    # 값·담기·패키지 카드는 목록에서 사라졌습니다
    for gone in ("원부터", "패키지 2종", 'class="bg-cart"', 'class="bg-pick"',
                 'class="bg-fold"'):
        assert gone not in text, gone
    # 교재 칸을 누르면 교재 화면으로 갑니다
    assert '/books/ybm-han"' in text or "/books/ybm-han'" in text

    # 값은 교재 화면에 있습니다 (값 자체는 정가 설정에 따라 바뀝니다)
    book = body(client().get("/books/ybm-han"))
    want = next(p["price"] for p in sc.load_catalog()["products"]
                if p["slug"] == "ybm-han-analysis")
    assert f"{want:,}원" in book, want
    print("PASS  목록은 값 대신 내용 · 값은 교재 화면에서")


def test_custom_request_takes_files_by_drag_and_drop():
    """맞춤 제작 — 링크 대신 파일을 그 자리에서 올릴 수 있어야 합니다."""
    import io as _io
    form = body(client().get("/custom?mode=custom"))
    assert 'class="dropzone"' in form and "끌어다 놓기" in form
    assert 'enctype="multipart/form-data"' in form
    assert 'name="files"' in form and "multiple" in form
    # 끌어다 놓으면 고른 것과 똑같이 담기게 하는 자리
    assert "dataTransfer" in form and "add(e.dataTransfer.files)" in form
    assert 'capture="environment"' in form                # 폰에서 바로 찍기
    # '.field label{display:block}' 에 눌리지 않아야 세로로 쌓입니다
    css = body(client().get("/static/store.css"))
    assert "label.dropzone{" in css and "flex-direction:column" in css

    c = client()
    resp = c.post("/custom", data={
        "mode": "custom", "wanted": "우리 학교 기출 3회분", "name": "선생",
        "email": "drop@example.com", "agree": "1",
        "files": [(_io.BytesIO(b"%PDF-1.4 one"), "1과.pdf"),
                  (_io.BytesIO(b"\x89PNG\r\n\x1a\n"), "사진.png")],
    }, content_type="multipart/form-data")
    assert resp.status_code == 200, resp.status_code

    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'drop@example.com'").fetchone()
    detail = json.loads(row["detail_json"])
    names = detail["보내신 파일"].split(", ")
    assert len(names) == 2, names
    # 이름은 우리가 다시 붙입니다 (올려 주신 이름을 그대로 쓰지 않습니다)
    assert all(n.startswith(row["order_no"]) for n in names), names
    assert names[0].endswith(".pdf") and names[1].endswith(".png")
    for n in names:
        assert (sc.REQUEST_DIR / n).is_file()

    # 관리자만 받을 수 있고, 폴더 밖은 막습니다
    a = admin()
    got = a.get(f"/admin/requests/{names[0]}")
    assert got.status_code == 200 and got.data.startswith(b"%PDF")
    assert a.get("/admin/requests/..%2f..%2fsite.json").status_code == 404
    assert client().get(f"/admin/requests/{names[0]}").status_code in (302, 401, 403)
    assert names[0] in body(a.get("/admin/orders?kind=custom"))

    # 올릴 수 없는 형식은 반려합니다
    bad = client().post("/custom", data={
        "mode": "custom", "wanted": "x", "name": "선생",
        "email": "bad@example.com", "agree": "1",
        "files": [(_io.BytesIO(b"x"), "몰래.exe")],
    }, content_type="multipart/form-data")
    assert bad.status_code == 400 and "올리실 수 있습니다" in body(bad)

    for n in names:
        (sc.REQUEST_DIR / n).unlink(missing_ok=True)
    print("PASS  맞춤 제작 — 파일을 끌어다 놓아 보내기")


def test_made_to_order_has_its_own_way_in():
    """필생보 독학용 · 동형모의고사는 미리 안 만듭니다. 신청해서 받는 길이 있어야 합니다."""
    with store.app.app_context():
        mto = sc.made_to_order_materials()
    ids = {m["id"] for m in mto}
    assert ids == {"pilsaengbo-solo", "mocktest"}, ids
    # 미리 만들어 두지 않으므로 상품 목록에도 없어야 합니다
    sold = {x for p in sc.load_catalog()["products"] for x in (p.get("materials") or [])}
    assert not (ids & sold), ids & sold

    # 라인업에서 왜 없는지와 어떻게 받는지를 그 자리에서 알려 줍니다
    page = body(client().get("/lineup"))
    assert page.count('class="mto-box"') == len(mto)
    assert "신청을 받아 만듭니다" in page and f"{sc.MTO_DAYS}일 안에" in page
    assert "내 자료함" in page and "mode=mto" in page

    # 신청 화면은 고른 자료가 미리 체크된 채로 열립니다
    form = body(client().get("/custom?mode=mto&mat=mocktest"))
    assert "주문제작 자료 신청" in form
    assert 'value="mocktest"' in form and "checked" in form
    assert f"{sc.MTO_DAYS}일 안에 만들어 드립니다" in form

    # 무엇을 만들지 안 고르면 반려합니다
    bad = client().post("/custom", data={
        "mode": "mto", "wanted": "2026 수능특강 3강", "name": "선생",
        "email": "mto@example.com", "agree": "1"})
    assert bad.status_code == 400 and "골라 주세요" in body(bad)

    resp = client().post("/custom", data={
        "mode": "mto", "mto_pick": ["mocktest", "pilsaengbo-solo"],
        "wanted": "2026 수능특강 3~5강", "name": "선생", "phone": "010-1111-2222",
        "email": "mto@example.com", "agree": "1"})
    assert resp.status_code == 200
    done = body(resp)
    assert "주문제작 신청이 접수되었습니다" in done
    assert "동형모의고사" in done and "내 자료함" in done
    assert f"{sc.MTO_DAYS}일 안에" in done

    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'mto@example.com'").fetchone()
    assert row["kind"] == "mto" and row["product_name"] == "주문제작 자료 신청"
    detail = json.loads(row["detail_json"])
    assert "동형모의고사 2회" in detail["신청 자료"]
    assert "필생보 · 독학용" in detail["신청 자료"]
    assert sc.ORDER_KIND_LABELS["mto"] == "주문제작 자료"

    # 관리자 화면에도 뜨고, 첫 화면 할 일에 따로 셉니다 (하루 약속이라 놓치면 안 됩니다)
    a = admin()
    assert "2026 수능특강 3~5강" in body(a.get("/admin/orders?kind=mto"))
    home = body(a.get("/admin"))
    assert "만들 주문제작 자료" in home and "kind=mto" in home
    print("PASS  주문제작 자료 — 신청 → 내 자료함 → 이메일")


def test_taster_is_given_away_not_sold():
    """맛보기는 값을 치르는 것이 아니라 받아 가는 것입니다.

    무엇을 만드는지 다 보여 준 그 자리에서 손님이 바라는 것은 '한 번 받아
    보기' 이지 '한 번 사 보기' 가 아닙니다. 게다가 분석 8종 가운데 넷은
    무료 자료실에서 이미 그냥 드리고 있어, 값을 매기면 앞뒤가 안 맞습니다.
    """
    a = admin()
    # 맛보기로 표시하면 종류를 안 골라도 저장됩니다 (한 지문에 자료 전부라서)
    a.post("/admin/free/new", data={
        "slug": "taste-one-passage", "title": "맛보기 · 한 지문 전 자료",
        "summary": "지문 하나를 자료 여덟 가지로 훑어 놓았습니다",
        "gate": "email", "taste": "1", "active": "1"}, follow_redirects=True)
    item = sc.find_freebie("taste-one-passage", raw=True)
    assert item and item["taste"] and not item["kinds"]

    # 파일이 아직 없으면 라인업에 안 걸립니다 — 눌렀는데 없는 것이 가장 나쁩니다
    assert sc.taste_freebie() is None
    assert "taste-free" not in body(client().get("/lineup"))

    a.post("/admin/free/taste-one-passage/files",
           data={"files": (io.BytesIO(b"%PDF-1.4 taste"), "taste.pdf")},
           content_type="multipart/form-data", follow_redirects=True)

    # 이제 '사기 전에' 자리에 무료로 걸립니다
    page = body(client().get("/lineup"))
    assert "taste-free" in page and "맛보기 · 한 지문 전 자료" in page
    assert page.index('id="samples"') < page.index("taste-free")
    assert '/free/taste-one-passage' in page

    # 값을 치르는 자리는 아예 없어졌습니다
    assert "taste-buy" not in page and "taste-list" not in page
    assert not [x for x in sc.load_catalog()["products"] if x.get("taste")]

    # 팔던 맛보기 상품은 손님 화면 어디에도 안 뜹니다. 자료 파일은 배포해도
    # 안 덮이는 디스크에 있어서, 파일에서 지우는 것만으로는 안 내려갑니다.
    dead = next(x for x in sc.load_raw_catalog()["products"]
                if x["slug"] in sc.RETIRED_SLUGS)
    assert dead.get("active", True), "코드로 내리는 길이 실제로 막고 있는지 봅니다"
    for url in ("/lineup", "/products", "/products?category=mock", "/"):
        got = body(client().get(url))
        assert dead["slug"] not in got and dead["name"] not in got, url
    assert client().get(f"/products/{dead['slug']}").status_code == 404
    # 옛 주소로 담으려 해도 안 담깁니다
    cc = client()
    cc.post("/cart/add", data={"slug": dead["slug"]}, follow_redirects=True)
    assert "담긴 자료가 없습니다" in body(cc.get("/cart"))
    # 관리자에서는 보입니다 — 거기서 지우실 수 있어야 합니다
    assert dead["name"] in body(a.get("/admin/products"))

    # 눌러 가면 이메일을 적고 받는 자리가 열립니다
    got = client().get("/free/taste-one-passage")
    assert got.status_code == 200 and "맛보기 · 한 지문 전 자료" in body(got)
    a.post("/admin/free/taste-one-passage/delete", follow_redirects=True)
    print("PASS  맛보기는 파는 것이 아니라 받아 가는 것")


def test_sample_pdf_links_go_somewhere():
    """'자료 샘플 PDF' 를 눌렀는데 아무 일도 안 일어나면 안 됩니다."""
    home = body(client().get("/"))
    assert "lineup#samples" in home                    # 바닥글에서 가리키는 자리
    page = body(client().get("/lineup"))
    assert 'id="samples"' in page, "가리키는 자리가 없습니다"

    ready = [m for m in sc.load_materials()["materials"]
             if m.get("sample_file") and (sc.SAMPLE_DIR / m["sample_file"]).exists()]
    if ready:
        assert page.count('class="mat-sample"') >= len(ready)
    else:
        # 아직 없으면 없다고 말하고, 대신 볼 것으로 보냅니다
        assert "샘플 PDF는 준비하고 있습니다" in page or "샘플 PDF를 준비하고 있습니다" in page
        assert "무료 자료 받으러 가기" in page

    # 첫날 체크리스트가 몇 종이 비었는지 세어 줍니다
    setup = body(admin().get("/admin"))
    assert "자료 샘플 PDF 올리기" in setup
    assert "자료마다 지면 사진과 설명 채우기" in setup
    print("PASS  샘플 PDF 자리 · 빈 자료 세어 주기")


def test_all_types_are_listed_with_killers_marked():
    """'모든 경우의 수를 담았다' 는 말보다 17종을 세어 보이는 편이 셉니다.

    킬러문항이 들어 있다는 것도 말로만 하지 않고, 열일곱 중 어느 것이
    킬러인지 짚어 줍니다. 그래야 손님이 세어 보고 믿습니다.
    """
    m = sc.material_map()["variants"]
    assert len(m["types"]) == 17, len(m["types"])

    page = body(client().get("/lineup"))
    for t in m["types"]:
        assert f'class="type-chip">{t}<' in page or \
               f'class="type-chip killer">{t}<' in page, t
    assert "경우의 수" in page.split('id="variants"', 1)[1].split("</article>", 1)[0]

    # 킬러문항은 객관식이 아니라 서술형입니다 — 손으로 쓰게 하는 자리
    desc = sc.material_map()["descriptive"]
    assert desc.get("killer") and desc.get("types")
    assert not m.get("killer"), "변형문제(객관식)에 킬러가 붙었습니다"
    block = page.split('id="descriptive"', 1)[1].split("</article>", 1)[0]
    assert "killer-tag" in block and "여기가 킬러문항입니다" in block
    # 두 자료가 하는 일이 다릅니다 — 머리말이 같으면 그게 안 보입니다
    vhead = page.split('id="variants"', 1)[1].split("</article>", 1)[0]
    import re as _re
    heads = _re.findall(r'class="type-head">([^<]+)<', page)
    assert len(set(heads)) == len(heads), heads
    assert "경우의 수" not in block, "서술형까지 '경우의 수' 라고 합니다"
    assert "변별" in block
    # 어느 유형이 킬러인지 하나씩 짚지는 않습니다 — 급을 매기면 나머지가
    # 쉬워 보이고, 학교마다 어려운 자리도 다릅니다
    assert "type-chip killer" not in page, "유형에 급을 매기고 있습니다"
    for t in desc["types"]:
        assert f'class="type-chip">{t}<' in block, t
    # 변형문제 쪽에는 딱지가 안 붙습니다
    vblock = page.split('id="variants"', 1)[1].split("</article>", 1)[0]
    assert "killer-tag" not in vblock

    # 첫 화면 타일에도 딱지가 붙습니다
    assert "killer-tag" in body(client().get("/"))

    # 사는 자리에서도 보여야 합니다 — 라인업까지 들어가는 손님은 많지 않습니다
    cat2 = sc.load_catalog()
    of = [x["slug"] for mid in ["workbook", "descriptive", "variants", "wordlist", "wordtest"]
          for x in cat2["products"]
          if x.get("book") == "ybm-han" and x.get("unit") == "Lesson 1"
          and x.get("materials") == [mid]]
    cc = client()
    cc.post("/cart/add", data={"slug": ",".join(of)})
    for url in ("/books/ybm-han", "/cart", "/order?cart=1", "/products?category=textbook"):
        got = body(cc.get(url))
        assert "chip-killer" in got, url
    # 패키지 고르는 상자에는 지문 하나를 몇 문제로 훑는지 한 줄.
    # 자료 이름을 낱낱이 읊는 것보다 다 더한 수 하나가 셉니다 (변형 17 + 서술형 23)
    book = body(cc.get("/books/ybm-han"))
    assert "pp-covers" in book and "지문 하나에 <b>40문제</b>" in book
    assert "경우의 수에 킬러까지" in book
    # 문항을 못 세는 분석 패키지는 수 대신 무슨 순서인지로 말합니다.
    # '좌지문우해석' 같은 이름만 늘어놓으면 무엇을 받는지 가늠이 안 됩니다.
    box = book.split('data-kind="analysis"', 1)[1].split("</button>", 1)[0]
    line = box.split('class="pp-covers"', 1)[1]
    assert "<b>능동적 분석 독해</b>" in line, "핵심어는 굵게 — 문제 패키지의 문항 수 자리"
    assert "읽고 · 끊고" in line and "문제" not in line
    cc.post("/cart/clear")

    # 관리자에서 유형과 킬러를 고칠 수 있어야 합니다
    a = admin()
    form = body(a.get("/admin/materials/variants"))
    assert 'name="types"' in form and 'name="killer_note"' in form
    assert 'name="killers"' not in form, "유형을 하나씩 짚는 칸은 없앴습니다"
    assert "빈칸추론" in form

    # 유형을 안 적어 둔 자료는 아무 말도 안 합니다 (없는 것을 지어내지 않게)
    plain = sc.material_map()["oneline-ko"]
    assert not plain.get("types") and not plain.get("killer")
    head = page.split('id="oneline-ko"', 1)[1].split("</article>", 1)[0]
    assert "killer-tag" not in head and "type-chip" not in head
    print("PASS  유형은 낱낱이 · 킬러는 있다고만")


def test_question_count_is_spelled_out():
    """'17종 변형문제' 가 몇 문제인지 화면에 적혀 있어야 합니다.

    이름만으로는 가늠이 안 됩니다. 지문이 28개면 변형문제만 476문제입니다.
    지문 수 × 자료마다 정해 둔 지문당 문항 수로 셉니다.
    """
    mats = sc.material_map()
    assert mats["variants"]["per_passage"] == 17
    assert mats["descriptive"]["per_passage"] == 23

    # 지문 4개짜리 변형문제 = 68문제
    cat = sc.load_catalog()
    one = next(x for x in cat["products"] if x["slug"] == "ybm-han-01-variants")
    assert one["passages"] == 4
    assert sc.question_count(one) == 68

    # 문제 패키지는 든 자료를 다 더합니다 (변형 17 + 서술형 23 = 지문당 40)
    pack = next(x for x in cat["products"] if x["slug"] == "mock-2026-06-g3-problem")
    assert sc.question_count(pack) == pack["passages"] * 40

    # 지문당 문항 수를 안 적어 둔 자료만 든 상품은 0 — 아무 말도 안 합니다
    only = next(x for x in cat["products"] if x["slug"] == "mock-2026-06-g3-analysis")
    assert sc.question_count(only) == 0

    # 손님 화면에 실제로 나와야 합니다
    detail = body(client().get("/products/mock-2026-06-g3-problem"))
    assert f"{pack['passages'] * 40:,}문제" in detail
    listed = body(client().get("/products?category=mock"))
    assert f"문제 {pack['passages'] * 40:,}개" in listed
    # 라인업에는 지문 하나에 몇 문제인지
    line = body(client().get("/lineup"))
    assert "지문당 17문제" in line and "지문당 23문제" in line

    # 문제 수는 세어 주되 '문제당 얼마' 는 어디에도 안 씁니다.
    # 낱개 단가를 적어 두면 시중 문제집과 자릿수로 견주게 됩니다. 우리가 파는 것은
    # 문제 개수가 아니라 '그 학교 그 지문에서 나올 경우의 수' 라 그 견줌에서 집니다.
    assert not hasattr(sc, "won_per_question")
    for page in (detail, listed):
        assert "원꼴" not in page and "문제 하나에" not in page
    for tpl in ("cart.html", "order.html", "product.html"):
        assert "원꼴" not in (_ROOT / "store_templates" / tpl).read_text()

    # 문제 수를 못 세는 자료에는 아무 말도 안 합니다
    plain = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert "이 자료에" not in plain

    # 담기 전에 — 강 고르는 표의 문제 패키지 칸에 몇 문제인지 적혀 있어야 합니다
    grid = store.unit_grid(cat, "ybm-han")
    cell = grid["rows"][0]["cells"]["problem"]
    assert cell["questions"] == 4 * 40, cell["questions"]
    assert grid["rows"][0]["cells"]["analysis"]["questions"] == 0
    book = body(client().get("/books/ybm-han"))
    assert f'class="um-q">{cell["questions"]}문제' in book
    assert f'data-q="{cell["questions"]}"' in book        # 고르면 합계에 더해집니다
    assert "all.q ? ' · 문제 '" in book

    # 지문당 문항 수는 관리자에서 고칠 수 있어야 합니다
    form = body(admin().get("/admin/materials/variants"))
    assert 'name="per_passage"' in form and 'value="17"' in form
    print("PASS  '17종' 이 몇 문제인지 (문제당 단가는 안 씀)")


def test_home_tiles_share_one_magnification():
    """첫 화면 자료 타일은 자료마다 글씨 크기가 같아야 합니다.

    원본 지면 사진이 자료마다 모양이 다릅니다(거의 정사각인 것도, 길쭉한 한
    쪽짜리도). 그대로 걸면 어떤 타일은 확대되고 어떤 타일은 한 쪽이 통째로
    들어가 글씨가 깨알이 됩니다. 같은 비율만큼 잘라 배율을 맞춥니다.
    """
    from PIL import Image
    shapes, scales = [], []
    for m in sc.load_materials()["materials"]:
        thumb = sc.shot_thumb(m["id"])
        if not thumb:
            continue
        with Image.open(thumb) as im:
            shapes.append(round(im.width / im.height, 2))
        with Image.open(sc.shot_dir(m["id"]) / sc.shot_files(m["id"])[0]) as src:
            # 원본 가로의 몇 분의 몇이 타일에 담기는지 — 이게 곧 글씨 크기입니다
            scales.append(round(sc.SHOT_THUMB_W / (src.width * sc.SHOT_THUMB_CROP), 3))
    assert len(shapes) >= 3, "지면 사진이 있는 자료가 너무 적어 잴 수 없습니다"

    # 모양이 다 같아야 타일 줄이 가지런합니다
    assert max(shapes) - min(shapes) <= 0.01, shapes
    assert abs(shapes[0] - sc.SHOT_THUMB_RATIO) <= 0.01, shapes[0]
    # 배율도 거의 같아야 합니다 (원본 가로가 비슷하면 완전히 같아집니다)
    assert max(scales) / min(scales) <= 1.2, scales
    print("PASS  첫 화면 타일 — 자료마다 같은 모양 · 같은 배율")


def test_lineup_shows_a_slice_not_the_whole_page():
    """지면은 윗부분만 잘라 보여 주고, 아래는 옅게 지웁니다.

    통째로 펼치면 여백까지 다 드러나 밋밋하고 아래가 뚝 끊겨 보입니다.
    한 장짜리 자료만 통째로 나오던 탓에 자료마다 인상이 달랐습니다.
    """
    css = body(client().get("/static/store.css"))
    block = css.split(".mat-shots .mat-shot a{", 1)[1].split("@media", 1)[0]
    assert "overflow:hidden" in block
    assert "object-fit:cover" in block and "height:440px" in block
    # 잘린 자리를 옅게 지우는 규칙
    assert "linear-gradient(to bottom, rgba(255,255,255,0), #fff)" in block
    # 한 장뿐이라고 통째로 보여 주던 예외는 없앴습니다
    assert ".mat-shots:not(.one) .mat-shot img" not in css
    # 대신 눌러서 원본을 볼 수 있어야 합니다
    page = body(client().get("/lineup"))
    assert "눌러서 크게" in css and "/lineup/shot/" in page
    print("PASS  지면은 윗부분만 · 아래는 옅게 · 눌러서 원본")


def test_lineup_shots_upload_and_show():
    """지면 사진을 관리자에서 올리면 오르티카잉 라인업에 바로 걸려야 합니다."""
    import io as _io
    a = admin()
    png = (b"\x89PNG\r\n\x1a\n" + b"0" * 60)          # 내용은 상관없습니다
    before = sc.shot_files("analysis")          # 이미 걸려 있던 지면이 있을 수 있습니다
    resp = a.post("/admin/materials/analysis/shots",
                  data={"files": [(_io.BytesIO(png), "지면.png"),
                                  (_io.BytesIO(png), "지면2.PNG")]},
                  content_type="multipart/form-data", follow_redirects=True)
    assert resp.status_code == 200 and "2장을 올렸습니다" in body(resp)
    # 올린 순서대로, 뒤 번호를 이어 붙입니다
    now = sc.shot_files("analysis")
    added = [f for f in now if f not in before]
    assert len(added) == 2 and all(f.endswith(".png") for f in added), now
    first, second = added

    text = body(client().get("/lineup"))
    assert f"/lineup/shot/analysis/{first}" in text
    assert f"실제 자료 지면 {len(now)} / {len(now)}" in text

    pic = client().get(f"/lineup/shot/analysis/{first}")
    assert pic.status_code == 200 and pic.data.startswith(b"\x89PNG")
    # 폴더 밖 · 사진이 아닌 파일 요청은 막습니다
    assert client().get("/lineup/shot/analysis/..%2f..%2fsite.json").status_code == 404
    assert client().get("/lineup/shot/analysis/없는파일.png").status_code == 404

    # 이미지가 아닌 파일은 반려합니다
    bad = a.post("/admin/materials/analysis/shots",
                 data={"files": [(_io.BytesIO(b"x"), "몰래.exe")]},
                 content_type="multipart/form-data", follow_redirects=True)
    assert "올릴 수 없는 형식" in body(bad)

    for name in added:
        a.post(f"/admin/materials/analysis/shots/{name}/delete", follow_redirects=True)
    assert sc.shot_files("analysis") == before
    print("PASS  자료 지면 사진 올리기 → 라인업 → 지우기")


def test_mobile_filters_collapse():
    """폰에서 필터링 버튼이 접혀 있어야 첫 화면에 자료가 보입니다."""
    for path in ("/products", "/free"):
        text = body(client().get(path))
        assert 'class="filter-toggle"' in text, path
        assert 'class="filter-sets"' in text, path
    # 고른 값이 버튼에 요약돼 보여야 합니다
    # 학년은 모의고사 분류에서만 씁니다
    picked = body(client().get("/products?category=mock&grade=고1&order=price"))
    assert "고1 · 가격 낮은 순" in picked
    print("PASS  폰에서 필터링 접기 · 고른 값 요약")


def test_long_pages_have_shortcuts():
    """긴 화면에서 손가락으로 돌아다닐 수 있어야 합니다."""
    lineup = body(client().get("/lineup"))
    assert 'class="lineup-jump"' in lineup
    assert '#variants' in lineup and '#mocktest' in lineup
    assert 'class="to-top"' in body(client().get("/"))
    # 상품 화면에는 폰에서 아래에 붙는 주문 바
    detail = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert 'class="buy-bar"' in detail
    print("PASS  라인업 바로가기 · 맨 위로 · 폰 주문 바")


def test_home_counts_dday_to_next_exam():
    """다음 시험까지 며칠인지 홈에서 바로 보여야 합니다."""
    from datetime import timedelta
    data = sc.load_notices()
    # 자동 일정보다 반드시 먼저 오도록, 가장 가까운 시험보다 하루 앞에 둡니다
    nearest = min([e["dday"] for e in sc.upcoming_exams(9)] or [30])
    days = max(1, min(12, nearest - 1))
    soon = (sc.now_kst() + timedelta(days=days)).date().isoformat()
    data["exams"] = [{"date": soon, "name": "테스트 학력평가", "grades": ["고1"]},
                     {"date": (sc.now_kst() - timedelta(days=3)).date().isoformat(),
                      "name": "이미 지난 시험", "grades": ["고3"]}]
    sc.save_notices(data)

    text = body(client().get("/"))
    assert f"D-{days}" in text and "테스트 학력평가" in text
    assert "이미 지난 시험" not in text          # 지난 시험은 안 나와야 합니다
    print("PASS  다음 시험까지 D-day (지난 시험은 제외)")


def test_exam_schedule_fills_itself():
    """학평·모평·수능은 손으로 안 넣어도 해마다 저절로 채워져야 합니다."""
    data = sc.load_notices()
    data["exams"] = []                       # 넣어 둔 확정일을 모두 비웁니다
    sc.save_notices(data)

    rows = sc.exam_schedule()
    assert rows, "비워 두면 일정이 하나도 없습니다"
    assert all(not r["fixed"] for r in rows), "손 안 댄 날짜는 '예상' 이어야 합니다"
    names = {r["name"] for r in rows}
    assert "대학수학능력시험" in names and "3월 전국연합 학력평가" in names
    # 올해와 내년 두 해가 들어 있어, 연말에도 빈 화면이 안 나옵니다
    assert len({r["date"][:4] for r in rows}) >= 2

    # 규칙이 실제 시행일과 맞는지 — 2026학년도 수능은 2026-11-19(목) 입니다
    수능 = next(r for r in sc.exam_calendar(2026) if r["name"] == "대학수학능력시험")
    assert 수능["date"] == "2026-11-19", 수능

    # 화면에도 '예상' 이라고 밝히고, 언제까지 올리는지가 함께 나옵니다
    page = body(client().get("/notice"))
    assert "예상" in page and f"{sc.UPLOAD_DAYS}일 안에" in page
    assert "지문분석" in page and "문제 패키지" in page

    # 기한이 지난 시험을 '올렸다' 고 단정하지 않습니다 — 아직 약속이 살아 있는 것만
    today = sc.now_kst().date()
    for e in sc.pending_uploads(5):
        assert e["date"] < today.isoformat() and e["upload_by"] >= today, e
    print("PASS  시험 일정이 저절로 채워짐 · 예상 표시 · 업로드 기한")


def test_saving_unchanged_exams_keeps_them_automatic():
    """표를 그대로 저장해도 예상값이 확정으로 굳으면 안 됩니다."""
    data = sc.load_notices()
    data["exams"] = []
    sc.save_notices(data)
    auto = sc.exam_schedule()

    a = admin()
    form = {"exam_date": [r["date"] for r in auto],
            "exam_name": [r["name"] for r in auto]}
    for i, r in enumerate(auto):
        form[f"exam_grades_{i}"] = r["grades"]
    a.post("/admin/notices/exams", data=form, follow_redirects=True)
    assert sc.load_notices()["exams"] == [], "손 안 댄 줄까지 적어 두었습니다"

    # 한 줄만 실제 시행일로 고치면 그 줄만 확정으로 남습니다
    form["exam_date"] = [auto[0]["date"]] + [r["date"] for r in auto[1:]]
    form["exam_date"][0] = "2099-01-08"
    a.post("/admin/notices/exams", data=form, follow_redirects=True)
    saved = sc.load_notices()["exams"]
    assert len(saved) == 1 and saved[0]["date"] == "2099-01-08", saved
    print("PASS  고친 줄만 확정 · 나머지는 자동 그대로")


def test_admin_edits_exam_schedule():
    a = admin()
    resp = a.post("/admin/notices/exams", data={
        "exam_date": ["2099-05-20", ""], "exam_name": ["아주 먼 학력평가", ""],
        "exam_grades_0": ["고2", "고3"]}, follow_redirects=True)
    assert resp.status_code == 200
    saved = sc.load_notices()["exams"]
    assert saved == [{"date": "2099-05-20", "name": "아주 먼 학력평가",
                      "grades": ["고2", "고3"]}], saved
    assert any(e["name"] == "아주 먼 학력평가" and e["fixed"]
               for e in sc.exam_schedule()), "확정으로 안 들어갔습니다"
    print("PASS  관리자에서 시험 일정 고치기 → 확정으로 반영")


def test_home_updates_skip_pinned_notice():
    """맨 위 띠에 이미 뜬 고정 공지가 '새로 올라왔습니다'에 또 나오면 안 됩니다."""
    text = body(client().get("/notice"))
    assert text.count("오르티카잉 자료 판매를 시작합니다") == 1
    print("PASS  고정 공지가 '새로 올라왔습니다'에 두 번 나오지 않음")


def test_new_product_appears_in_home_updates():
    """새 자료를 등록하면 따로 공지를 쓰지 않아도 '새로 올라왔습니다'에 뜹니다."""
    a = admin()
    a.post("/admin/products/new", data={
        "slug": "fresh-item-test", "name": "새로 올린 테스트 자료",
        "category": "mock", "package": "analysis", "price": "10000",
        "subtitle": "지문 10개", "grade": "고1", "sort": "10", "active": "1",
        "materials": ["passage"]}, follow_redirects=True)
    text = body(client().get("/notice"))
    assert "새로 올린 테스트 자료" in text
    assert "새 자료" in text
    a.post("/admin/products/fresh-item-test/delete", follow_redirects=True)
    print("PASS  새 자료가 공지 없이 '새로 올라왔습니다'에 뜸")


def test_order_page_shows_what_you_are_buying():
    """주문서에서 무엇을 사는지 칩으로 한눈에 보여야 합니다."""
    text = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert "2026학년도 6월 모의평가" in text      # 교재·회차
    assert "고3" in text and "지문 28개" in text   # 학년 · 분량
    assert "지문 분석 패키지" in text
    assert "지문자료" in text and 'class="mat-chip' in text   # 들어가는 자료
    print("PASS  주문서에 교재·회차·학년 칩")


def test_manual_line_break_filter():
    """한글 줄나눔은 손으로 잡을 수 있어야 합니다."""
    with store.app.app_context():
        assert str(store.br("읽고 | 뜯어보고")) == "읽고<br>뜯어보고"
        assert str(store.br("한 줄\n두 줄")) == "한 줄<br>두 줄"
        assert str(store.br("<b>지움</b>")) == "&lt;b&gt;지움&lt;/b&gt;"   # 태그는 못 넣게
        assert str(store.br("  |  가운데  |  ")) == "가운데"

    data = sc.load_materials()
    data["intro"]["headline"] = "앞줄입니다 | 뒷줄입니다"
    sc.save_materials(data)
    text = body(client().get("/lineup"))
    assert "앞줄입니다<br>뒷줄입니다" in text
    print("PASS  줄나눔을 손으로 잡기 (| 또는 줄바꿈)")


def test_no_emoji_on_customer_pages():
    """이모지가 섞이면 손으로 만든 느낌이 사라집니다."""
    for path in ("/", "/products", "/free", "/lineup", "/guide"):
        text = body(client().get(path))
        for bad in ("✅", "📧", "🎁", "👉", "⚠️", "💡", "🧩", "📁", "🌿"):
            assert bad not in text, f"{path} 에 {bad} 가 있습니다"
    print("PASS  고객 화면에 이모지 없음")


# ---- 자동 할인 (담은 개수 하나로) ----------------------------------------
def test_count_discount():
    """할인 규칙은 하나 — 많이 담을수록 깎입니다."""
    site = sc.load_site()
    site["discount"] = {"count_enabled": True,
                        "count_tiers": [{"min": 3, "percent": 10},
                                        {"min": 6, "percent": 15},
                                        {"min": 12, "percent": 20}],
                        "max_percent": 20}
    sc.save_site(site)

    # 2개까지는 정가입니다
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    both = price["mock-2026-06-g3-analysis"] + price["mock-2026-06-g3-problem"]
    q = client().get("/order/quote?slug=mock-2026-06-g3-analysis&also=1").get_json()
    assert q["subtotal"] == both and q["rows"] == [] and q["final"] == both
    # 하나만 더 담으면 어떻게 되는지 알려 줘야 합니다
    assert q["next_tier"] == {"min": 3, "percent": 10}

    # 3개를 담으면 10%
    c = client()
    for slug in ("mock-2026-06-g3-analysis", "mock-2026-06-g3-problem",
                 "mock-2026-03-g2-analysis"):
        c.post("/cart/add", data={"slug": slug})
    q3 = c.get("/order/quote?cart=1").get_json()
    assert q3["rows"][0]["name"] == "3개 담기" and q3["rows"][0]["percent"] == 10
    assert q3["final"] == q3["subtotal"] - q3["subtotal"] * 10 // 100
    assert q3["next_tier"] == {"min": 6, "percent": 15}

    # 장바구니 화면도 '몇 개만 더' 를 알려 줍니다
    assert "3개만 더" in body(c.get("/cart"))

    # 단골 할인은 없앴습니다 — 이메일을 적어도 값이 안 바뀝니다
    with store.app.app_context():
        db = sc.get_db()
        for i in range(5):
            db.execute(
                """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                                       name, phone, email, status, created_at, updated_at)
                   VALUES (?, 'product', '지난 주문', 1, 10000, '옛단골', '010-0000-0000',
                           'regular@example.com', '발송완료', ?, ?)""",
                (f"OR-OLD-{i}", sc.stamp(), sc.stamp()))
        db.commit()
    same = client().get("/order/quote?slug=mock-2026-06-g3-analysis"
                        "&email=regular@example.com").get_json()
    assert same["final"] == same["subtotal"], "단골 할인이 아직 붙습니다"
    print("PASS  담은 개수 할인 — 규칙 하나 · 단골 할인 없음")


def test_no_loyalty_anywhere():
    """단골 할인은 화면·설정 어디에도 남아 있으면 안 됩니다."""
    for path in ("/cart", "/products", "/guide"):
        assert "단골" not in body(client().get(path)), path
    assert "discount_loyalty_enabled" not in body(admin().get("/admin/settings"))
    assert not hasattr(sc, "loyalty_tier") and not hasattr(sc, "loyalty_next")
    print("PASS  단골 할인 흔적 없음")


def test_discount_has_a_ceiling():
    """실수로 너무 깎이지 않게 상한이 있어야 합니다."""
    site = sc.load_site()
    site["discount"] = {"count_enabled": True,
                        "count_tiers": [{"min": 2, "percent": 40}],
                        "max_percent": 20}
    sc.save_site(site)
    q = client().get("/order/quote?slug=mock-2026-06-g3-analysis&also=1").get_json()
    assert q["final"] == q["subtotal"] - q["subtotal"] * 20 // 100
    print("PASS  할인 상한 (20%까지)")


def test_order_page_shows_download_when_ready():
    """계좌이체라도, 자료가 나가면 주문 확인 화면에서 바로 받을 수 있어야 합니다."""
    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "기다림",
        "phone": "010-7777-0000", "email": "wait@example.com", "agree": "1"})
    where = resp.headers["Location"]
    before = body(client().get(where))
    assert "입금 확인" in before and "받으실 자료" not in before

    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'wait@example.com'").fetchone()
    folder = sc.product_dir("mock-2026-06-g3-analysis")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "ready.pdf").write_bytes(b"%PDF-1.4 ready\n")
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)

    after = body(client().get(where))
    assert "받으실 자료" in after and "/d/" in after
    print("PASS  주문 확인 화면에서 바로 받기")


def test_speaks_to_both_audiences():
    """혼자 하는 학생과 가르치는 선생님, 둘 다에게 말을 걸어야 합니다."""
    # 첫 화면은 히어로 한 문단으로 두 쪽을 다 부릅니다
    home = body(client().get("/"))
    assert "혼자 공부하는 학생에게는" in home and "가르치는 선생님에게는" in home
    # 자세한 두 갈래 안내는 오르티카잉 라인업에 있습니다
    text = body(client().get("/lineup"))
    assert "혼자 공부하는 학생" in text and "가르치는 선생님" in text
    assert "필생보 독학용" in text          # 학생 쪽 길
    assert "학생용 · 강의용 2판본" in text   # 선생님 쪽 길
    print("PASS  히어로가 두 쪽을 부르고, 라인업이 두 갈래로 안내")


def test_analysis_tagline_updated():
    """지문분석지 한 줄 소개가 바뀌어야 합니다."""
    text = body(client().get("/lineup"))
    assert "시험에 나오는 모든 포인트를 담았습니다" in text
    assert "어디를 봐야 하는지가 지면에 그려져" not in text
    print("PASS  지문분석지 소개 문구")


def test_every_book_has_unit_checkboxes():
    """교재에 들어가면 어디서든 골라 담을 칸이 보여야 합니다."""
    catalog = sc.load_catalog()
    by_book = {}
    for p in catalog["products"]:
        if p.get("unit"):
            by_book.setdefault(p["book"], set()).add(p["unit"])

    # 교재마다 칸 수가 제각각이어야 합니다 (올린 파일대로 만들어지므로)
    counts = {b: len(u) for b, u in by_book.items()}
    assert len(set(counts.values())) > 1, counts

    words = {"mock": "문항 구간", "textbook": "단원", "ebs": "강"}
    for book in catalog["books"]:
        page = body(client().get(f"/books/{book['slug']}"))
        units = by_book.get(book["slug"])
        if not units:
            # 칸이 없으면 빈 화면 대신 이유를 말해야 합니다
            assert 'class="pick-none"' in page, book["slug"]
            assert "드립니다" in page or "팔지 않습니다" in page, book["slug"]
            continue
        word = words.get(book.get("category"), "강")
        assert f"필요한 {word}만 고르세요" in page, book["slug"]
        assert f"모두 {len(units)}" in page, (book["slug"], len(units))
        chips = page[page.index('id="unit-chips"'):]
        assert chips.count('class="ur-pick chip"') == len(units), book["slug"]

    # 낱개로 파는 것은 EBS 부교재(강)와 교과서(단원)뿐 — 모의고사는 회차가 한 묶음
    kinds = {b.get("category") for b in catalog["books"] if b["slug"] in by_book}
    assert kinds <= {"ebs", "textbook"}, kinds
    assert "mock" not in kinds

    # 모의고사는 한 회차씩 팝니다 — 문항 번호로 쪼개지 않습니다
    mock = body(client().get("/books/mock-2026-06-g3"))
    assert "한 회차씩" in mock and "18~20번" not in mock
    assert 'id="unit-chips"' not in mock and "고르세요" not in mock

    # 교과서는 단원별로 고릅니다
    textbook = body(client().get("/books/neungyule-kim"))
    assert "필요한 단원만 고르세요" in textbook and "Lesson 1" in textbook
    assert "모두 8단원" in textbook
    print("PASS  강(부교재) · 단원(교과서) 낱개 · 모의고사는 회차 한 묶음")


def test_shared_materials_are_charged_once():
    """어휘리스트·단어테스트는 두 패키지에 들지만, 둘 다 사도 한 번만 받습니다."""
    catalog = sc.load_catalog()
    pkgs = {p["id"]: p["materials"] for p in catalog["packages"]}
    assert "literal" in pkgs["analysis"], "직독직해가 지문 분석 패키지에 없습니다"
    for mid in ("wordlist", "wordtest"):
        assert mid in pkgs["analysis"] and mid in pkgs["problem"], mid

    with store.app.app_context():
        grid = store.unit_grid(catalog, "ebs-2026-tokgang-eng")
    assert grid["shared_mats"] == ["어휘리스트", "단어테스트"], grid["shared_mats"]
    row = grid["rows"][0]
    cells = row["cells"]
    naive = sum(c["price"] for c in cells.values())
    assert row["price"] < naive, "겹친 자료를 두 번 셈했습니다"

    # 겹친 자료의 값만큼 정확히 차이가 나야 합니다
    price = {p["slug"]: p["price"] for p in catalog["products"]}
    dup = sum(price[s] for s in cells["analysis"]["slugs"].split(",")
              if s in cells["problem"]["slugs"].split(","))
    assert naive - row["price"] == dup and dup > 0, (naive, row["price"], dup)

    # 장바구니에 두 칸을 다 담아도 겹친 자료는 한 줄만 들어갑니다
    c = client()
    for kind in ("analysis", "problem"):
        c.post("/cart/add", data={"slug": cells[kind]["slugs"], "next": "/cart"})
    q = c.get("/order/quote?cart=1").get_json()
    assert q["subtotal"] == row["price"], (q["subtotal"], row["price"])

    # 겹친다는 설명은 화면에 적지 않습니다 (값이 알아서 한 번만 붙으니까요)
    page = body(client().get("/books/ebs-2026-tokgang-eng"))
    assert "두 패키지에 함께 들어 있습니다" not in page
    assert "직독직해" in page and "어휘리스트" in page and "단어테스트" in page
    # 칸 이름은 몇 종이 들어가는지까지 적습니다
    assert "\u2018꼼꼼한\u2019 지문분석 8종 패키지" in page
    assert "\u2018출제예상\u2019 문제 5종 패키지" in page
    print("PASS  겹쳐 든 자료는 한 번만 담기고 한 번만 셈함")


def test_book_pick_grid():
    """자료 골라 담기 — 강 × 자료 종류 표에서 필요한 것만 담습니다."""
    import io as _io, zipfile
    a = admin()

    # 예시 자료가 든 교재를 빌려 쓰면 강 수가 바뀔 때마다 테스트가 깨집니다.
    # 이 테스트만 쓰는 교재를 세워 두고, 끝나면 지웁니다.
    BOOK = "pick-test-book"
    catalog = sc.load_raw_catalog()
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != BOOK]
    catalog["books"].append({"slug": BOOK, "name": "고르기 테스트 교재",
                             "category": "textbook", "grade": "고1", "active": True,
                             "publisher": "테스트", "sort": 900})
    # 통권 상품도 두 개 — '전 강을 한 번에' 줄이 아래에 붙는지 보려는 것입니다
    for pkg in ("analysis", "problem"):
        catalog["products"].append({
            "slug": f"{BOOK}-whole-{pkg}", "name": f"고르기 테스트 교재 전 단원 · {pkg}",
            "category": "textbook", "book": BOOK, "package": pkg,
            "materials": ["analysis" if pkg == "analysis" else "variants"],
            "passages": 20, "price": 20000, "grade": "고1", "sort": 100,
            "active": True, "format": "PDF (A4, 인쇄용)"})
    sc.save_catalog(catalog)

    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for no in (1, 2):
            for name in ("지문분석지", "17종 변형문제"):
                zf.writestr(f"{no}강_{name}.pdf", b"%PDF-1.4 x")
    look = body(a.post("/admin/products/bulk",
                       data={"file": (_io.BytesIO(buf.getvalue()), "묶음.zip")},
                       content_type="multipart/form-data"))
    import re as _re
    token = _re.search(r'name="token" value="([^"]+)"', look).group(1)
    a.post("/admin/products/bulk/save", data={
        "token": token, "book": BOOK, "passages": "10",
        "path": ["1강_지문분석지.pdf", "1강_17종 변형문제.pdf",
                 "2강_지문분석지.pdf", "2강_17종 변형문제.pdf"]}, follow_redirects=True)

    # 교재에 들어가면 강 고르기가 바로 나옵니다 (따로 들어갈 필요 없이)
    c = client()
    page = body(c.get(f"/books/{BOOK}"))
    assert "필요한 단원만 고르세요" in page      # 교과서라 '강' 이 아니라 '단원'
    assert "모두 2단원" in page
    assert "1강" in page and "2강" in page                    # 줄
    assert "3단원부터" in page and "10%" in page               # 담은 강 수 할인 안내
    # 칸은 '자료 종류' 가 아니라 패키지입니다 — 2강 × 2패키지 = 네 칸
    assert page.count('class="um pkg-') == 4

    # 강이 한눈에 보이는 체크 칩으로 나옵니다 (표를 안 펴도 고를 수 있게)
    assert "어떤 단원이 필요하세요?" in page and "어떤 패키지가 필요하세요?" in page
    chips = page[page.index('id="unit-chips"'):]
    assert chips.count('class="ur-pick chip"') == 2          # 1강 · 2강
    assert "1강" in chips and "2강" in chips
    kind_chips = page[page.index('id="kind-chips"'):page.index('id="unit-chips"')]
    assert kind_chips.count("pkg-pick") == 2                 # 분석 · 문제
    # 위가 패키지, 밑이 강 — 차례가 뒤바뀌면 안 됩니다
    assert page.index('id="kind-chips"') < page.index('id="unit-chips"')
    assert page.count('class="ps-all"') == 2                 # 줄마다 '전체 고르기'
    # 한 칸에 자료가 여럿이면 함께 담깁니다
    assert f'value="{BOOK}-01-analysis"' in page
    # 파는 단위는 패키지입니다 — 줄 안에도 패키지 칸만 (접는 표는 없습니다)
    assert "<details" not in page and "칸마다 하나씩 고르기" not in page
    assert page.count('class="um pkg-') == 4                 # 2강 × 패키지 2종
    assert 'data-kind="analysis"' in page and 'data-kind="problem"' in page
    # 자료를 낱개로 체크하게 두지 않습니다 (지문분석지만 빼는 것은 안 되니까)
    assert "data-mid=" not in page
    # 무엇이 들어 있는지는 위 패키지 칸에 적어 둡니다
    top = page[page.index('id="kind-chips"'):page.index('id="unit-chips"')]
    assert "지문분석지" in top and "17종 변형문제" in top
    # 교재 전체 상품은 강 고르기 아래에 놓입니다
    assert page.index("필요한 단원만 고르세요") < page.index("전체를 한 번에")
    # 예전 주소는 그 자리로 보내 줍니다
    moved = c.get(f"/books/{BOOK}/pick")
    assert moved.status_code == 302 and moved.headers["Location"].endswith("#pick")

    # 할인은 파일 수가 아니라 강(단원) 수로 셉니다.
    # 파일 세 개라도 두 단원이면 아직 할인이 없습니다.
    c.post("/cart/add", data={"slug": [f"{BOOK}-01-analysis", f"{BOOK}-01-variants",
                                       f"{BOOK}-02-analysis"],
                              "next": "/cart"}, follow_redirects=True)
    q = c.get("/order/quote?cart=1").get_json()
    assert q["subtotal"] == 250*10 + 400*10 + 250*10
    assert q["rows"] == [], "두 단원인데 할인이 붙었습니다"
    assert q["next_tier"] == {"min": 3, "percent": 10}
    assert "1단원만 더" in body(c.get("/cart"))

    # 이미 담은 것은 잠긴 채로 보입니다
    again = body(c.get(f"/books/{BOOK}"))
    assert again.count("checked disabled") == 3

    # 강 고르기 막대와 단어 고르기 막대는 이름이 달라야 합니다 (서로 덮어쓰지 않게)
    css = body(client().get("/static/store.css"))
    assert ".unit-bar{position:sticky; bottom:0;" in css   # 강 — 아래에 붙음
    assert ".pick-bar{position:sticky; top:0;" in css      # 단어 — 위에 붙음
    assert "unit-bar" in again
    wb = sc.load_words()["books"][0]
    words_page = body(client().get(
        f"/words/{wb['slug']}/pick?unit={wb['units'][0]['id']}"))
    assert "unit-bar" not in words_page and "pick-bar" in words_page

    # 강 단위 상품이 없는 교재는 강 고르기 대신 '왜 없는지' 를 말해 줍니다
    catalog = sc.load_raw_catalog()
    catalog["books"].append({"slug": "no-unit-book", "name": "통권만 있는 교재",
                             "category": "textbook", "grade": "고1", "active": True,
                             "sort": 901})
    sc.save_catalog(catalog)
    plain = body(client().get("/books/no-unit-book"))
    assert "만 고르세요" not in plain and "data-price=" not in plain
    assert "단원별로 나눠 팔지 않습니다" in plain     # 왜 없는지 말해 줍니다
    assert "자료 요청" in plain                     # 빈 화면으로 두지 않습니다
    catalog = sc.load_raw_catalog()
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != "no-unit-book"]
    sc.save_catalog(catalog)

    # 치우기
    catalog = sc.load_raw_catalog()
    gone = [p["slug"] for p in catalog["products"] if p.get("book") == BOOK]
    catalog["products"] = [p for p in catalog["products"] if p["slug"] not in gone]
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != BOOK]
    sc.save_catalog(catalog)
    import shutil as _sh
    for slug in gone:
        _sh.rmtree(sc.product_dir(slug), ignore_errors=True)
    print("PASS  자료 골라 담기 — 강 × 자료 표 · 줄·칸 한꺼번에 · 값 바로 계산")


def test_bulk_products_from_zip():
    """압축 하나로 상품 여러 개를 만들고, 파일까지 붙어야 합니다."""
    import io as _io, zipfile
    a = admin()

    # 예시 자료가 쓰는 교재를 빌려 쓰면 주소가 겹쳐 테스트가 흔들립니다.
    # 이 테스트만 쓰는 교재를 하나 만들고, 끝나면 지웁니다.
    BOOK = "zip-test-book"
    catalog = sc.load_raw_catalog()
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != BOOK]
    catalog["books"].append({"slug": BOOK, "name": "압축 테스트 교재",
                             "category": "ebs", "grade": "고3", "active": True,
                             "publisher": "테스트", "sort": 900})
    sc.save_catalog(catalog)

    page = body(a.get("/admin/products/bulk"))
    assert "압축 파일을 여기에 끌어다 놓으세요" in page
    assert "지문분석지" in page and "17종변형" in page      # 알아보는 이름 안내

    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("1강_지문분석지.pdf", b"%PDF-1.4 a")
        zf.writestr("1강_17종 변형문제.pdf", b"%PDF-1.4 b")
        zf.writestr("2강/지문분석지.pdf", b"%PDF-1.4 c")
        zf.writestr("Day 3 통합워크북.pdf", b"%PDF-1.4 d")
        zf.writestr("이름없는파일.pdf", b"%PDF-1.4 e")     # 못 읽는 것
        zf.writestr("메모.txt", b"x")                      # PDF 가 아닌 것

    look = body(a.post("/admin/products/bulk",
                       data={"file": (_io.BytesIO(buf.getvalue()), "자료묶음.zip")},
                       content_type="multipart/form-data"))
    assert "4개를 읽었습니다" in look and "강 3개" in look
    assert "1강" in look and "Day 3" in look
    assert "건너뛴 파일 2개" in look
    import re as _re
    token = _re.search(r'name="token" value="([^"]+)"', look).group(1)

    before = len(sc.load_raw_catalog()["products"])
    done = a.post("/admin/products/bulk/save", data={
        "token": token, "book": BOOK, "passages": "6",
        "p_1": "8",                                        # 1강만 지문 8개
        "path": ["1강_지문분석지.pdf", "1강_17종 변형문제.pdf",
                 "2강/지문분석지.pdf", "Day 3 통합워크북.pdf"],
    }, follow_redirects=True)
    assert "상품 4개를 만들고 파일 4개를 붙였습니다" in body(done)

    catalog = sc.load_raw_catalog()
    assert len(catalog["products"]) == before + 4
    made = {p["slug"]: p for p in catalog["products"]
            if p.get("book") == BOOK and p.get("passages") in (6, 8)}
    one = made[f"{BOOK}-01-analysis"]
    assert one["passages"] == 8 and one["price"] == 250 * 8       # 지문분석지 250원
    assert one["materials"] == ["analysis"] and one["package"] == "analysis"
    assert "1강 · 지문분석지" in one["name"]
    assert made[f"{BOOK}-01-variants"]["price"] == 400 * 8
    assert made[f"{BOOK}-02-analysis"]["passages"] == 6           # 기본값
    assert made[f"{BOOK}-03-workbook"]["package"] == "problem"

    # 파일이 상품 폴더에 붙었어야 합니다
    assert len(sc.product_files(f"{BOOK}-01-analysis")) == 1

    # 손님 화면에도 바로 보입니다
    page = body(client().get(f"/products/{BOOK}-01-analysis"))
    assert "1강 · 지문분석지" in page and "2,000원" in page

    # 치우기
    catalog["products"] = [p for p in catalog["products"]
                           if p["slug"] not in made]
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != BOOK]
    sc.save_catalog(catalog)
    for slug in made:
        import shutil as _sh
        _sh.rmtree(sc.product_dir(slug), ignore_errors=True)
    print("PASS  압축 하나로 상품 여러 개 만들기 (파일까지)")


def test_disk_keeps_your_files_but_refreshes_the_rest():
    """디스크를 붙여 쓸 때 — 사장님 파일은 지키고, 손 안 댄 기본값만 새로 깝니다."""
    import shutil, tempfile
    room = pathlib.Path(tempfile.mkdtemp())
    bundle, disk = room / "bundle", room / "disk"
    (bundle / "lineup" / "passage").mkdir(parents=True)
    (bundle / "lineup" / "passage" / "01.webp").write_bytes(b"A")
    (bundle / "materials.json").write_text('{"v":1}', encoding="utf-8")
    (bundle / "products.json").write_text('{"p":1}', encoding="utf-8")
    keep_bundle, keep_dir = sc.BUNDLED_DATA, sc.DATA_DIR
    try:
        sc.BUNDLED_DATA, sc.DATA_DIR = bundle, disk

        assert sc.seed_data_dir() == []                       # 첫 배포
        assert (disk / "materials.json").read_text() == '{"v":1}'

        # 이미 깔려 있는데 견줄 판이 없던 경우 (예전 방식으로 깔린 디스크)
        (disk / "materials.json").write_text('{"v":0}', encoding="utf-8")
        shutil.rmtree(disk / sc.SEED_COPY)
        assert sc.seed_data_dir() == ["materials.json"]
        assert (disk / "materials.json").read_text() == '{"v":1}', "새 판을 못 받았습니다"
        # 있던 것은 버리지 않고 남겨 둡니다
        assert (disk / sc.SEED_COPY / "materials.json.before").read_text() == '{"v":0}'

        # 저장소에서 자료 정의를 고쳐 다시 배포 — 손 안 댔으니 새 판으로
        (bundle / "materials.json").write_text('{"v":2}', encoding="utf-8")
        shutil.rmtree(bundle / "lineup" / "passage")
        (bundle / "lineup" / "oneline-ko").mkdir()
        (bundle / "lineup" / "oneline-ko" / "01.webp").write_bytes(b"A")
        assert sorted(sc.seed_data_dir()) == ["lineup", "materials.json"]
        assert (disk / "materials.json").read_text() == '{"v":2}'
        # 이름이 바뀐 지면 사진 폴더도 따라옵니다
        assert (disk / "lineup" / "oneline-ko").is_dir()
        assert not (disk / "lineup" / "passage").exists()

        # 사장님이 고치신 뒤에는 새 판이 와도 그대로 둡니다
        (disk / "materials.json").write_text('{"v":"내가 고침"}', encoding="utf-8")
        (bundle / "materials.json").write_text('{"v":3}', encoding="utf-8")
        assert sc.seed_data_dir() == []
        assert (disk / "materials.json").read_text() == '{"v":"내가 고침"}'

        # 상품·주문처럼 사장님 몫은 어떤 경우에도 안 건드립니다
        (disk / "products.json").write_text('{"내 상품":1}', encoding="utf-8")
        (bundle / "products.json").write_text('{"p":99}', encoding="utf-8")
        sc.seed_data_dir()
        assert (disk / "products.json").read_text() == '{"내 상품":1}'
        assert "products.json" in sc.YOURS and "store.db" in sc.YOURS
    finally:
        sc.BUNDLED_DATA, sc.DATA_DIR = keep_bundle, keep_dir
        shutil.rmtree(room, ignore_errors=True)
    print("PASS  디스크 — 사장님 파일은 지키고 기본값만 갱신")


def test_admin_can_reload_the_examples():
    """예시가 옛날 것으로 남으면, 관리자 화면에서 최신판으로 바꿀 수 있어야 합니다."""
    a = admin()
    catalog = sc.load_raw_catalog()
    # 직접 만드신 상품 하나를 섞어 둡니다 (이건 살아남아야 합니다)
    catalog["products"].append({"slug": "mine-keep-me", "name": "내가 만든 자료",
                                "category": "mock", "price": 9000, "active": True})
    # 예시를 옛날 것처럼 망가뜨려 둡니다
    for p in catalog["products"]:
        if p.get("sample"):
            p["price"] = 1
    sc.save_catalog(catalog)

    page = body(a.get("/admin/products"))
    assert "예시를 최신판으로 바꾸기" in page
    assert a.post("/admin/products/refresh-samples",
                  follow_redirects=True).status_code == 200

    after = sc.load_raw_catalog()
    assert any(p["slug"] == "mine-keep-me" for p in after["products"]), "내 상품이 사라졌습니다"
    junk = [p for p in after["products"] if p.get("sample") and p.get("price") == 1]
    assert not junk, "옛 예시가 남아 있습니다"
    # 자료 종류·패키지 정의도 저장소의 것으로 맞춰집니다
    assert {m for pkg in after["packages"] for m in pkg["materials"]} >= {
        "oneline-ko", "wordlist"}

    after["products"] = [p for p in after["products"] if p["slug"] != "mine-keep-me"]
    sc.save_catalog(after)
    print("PASS  예시만 최신판으로 다시 깔기")


def test_admin_pricing_is_editable():
    """자료 1종이 지문 1개당 얼마인지를 화면에서 정하고, 그 값으로 계산해야 합니다."""
    a = admin()
    text = body(a.get("/admin/pricing"))
    assert "우리 정가" in text and "자료 1종이 지문 1개당 얼마" in text
    assert "독학하는 학생" in text and "차별화된 자료를 찾는 강사" in text
    # 라인업에 있는 자료마다 칸이 나와야 합니다 (자료가 늘면 칸도 늡니다)
    for m in sc.load_materials()["materials"]:
        assert f'name="mat_{m["id"]}"' in text, m["id"]
    # 지문이 적다고 값을 더 받는 규칙은 없앴습니다
    assert "적은 묶음" not in text

    a.post("/admin/pricing", data={
        "mat_analysis": "400", "mat_pilsaengbo": "300", "mat_workbook": "500",
        "mat_descriptive": "300", "mat_variants": "400",
        "round_to": "100", "full_pack_percent": "80"}, follow_redirects=True)
    site = sc.load_site()
    cfg = sc.pricing_cfg(site)
    # 패키지 값 = 그 안에 든 자료 단가의 합 (겹쳐 든 자료도 각 패키지에 들어갑니다)
    rates = cfg["materials"]
    want = {pkg["id"]: sum(rates.get(m, 0) for m in pkg["materials"])
            for pkg in sc.package_map().values()}
    assert cfg["units"] == want, (cfg["units"], want)
    assert rates["analysis"] == 400                            # 보낸 값이 들어갔습니다
    step = cfg["round_to"]
    def rounded(n):
        return int(round(n / step) * step)
    assert sc.suggested_price(site, "analysis", 28) == rounded(want["analysis"] * 28)
    assert sc.suggested_price(site, "problem", 20) == rounded(want["problem"] * 20)
    # 지문이 적어도 값을 더 받지 않습니다 (지문당 값이 같아야 합니다)
    assert sc.suggested_price(site, "analysis", 5) == rounded(want["analysis"] * 5)
    assert sc.suggested_price(site, "없는갈래", 28) == 0

    # 손님 화면에는 단가가 새어 나가면 안 됩니다
    for path in ("/", "/products", "/products/ybm-han-analysis", "/cart"):
        page = body(client().get(path))
        assert "지문 1개당" not in page and "우리 정가" not in page, path

    # 원래대로 돌려 놓습니다
    a.post("/admin/pricing", data={
        "mat_analysis": "250", "mat_pilsaengbo": "160", "mat_workbook": "300",
        "mat_descriptive": "250", "mat_variants": "400",
        "round_to": "100", "full_pack_percent": "85"}, follow_redirects=True)
    back = sc.pricing_cfg(sc.load_site())
    assert back["materials"]["analysis"] == 250 and back["materials"]["variants"] == 400
    print("PASS  자료 1종 단가를 화면에서 정하기 · 손님에겐 안 보임")


def _set_discount(tiers=None, cap=20):
    """할인 설정을 이 테스트가 쓰는 값으로 맞춰 둡니다.
    (다른 테스트가 바꿔 놓았을 수 있어 매번 새로 깝니다)"""
    site = sc.load_site()
    site["discount"] = {"count_enabled": True, "max_percent": cap,
                        "count_tiers": tiers or [{"min": 3, "percent": 10},
                                                 {"min": 6, "percent": 15},
                                                 {"min": 12, "percent": 20}]}
    sc.save_site(site)


# ---- 장바구니 --------------------------------------------------------------
def test_mock_filters_by_year_and_month():
    """모의고사는 학년 · 시행년도 · 시행월 세 줄로 좁힐 수 있어야 합니다.

    회차가 쌓이면 '몇 년 몇 월 것' 으로 찾습니다. 교재 846개를 눈으로
    훑게 두면 안 됩니다.
    """
    import re
    page = body(client().get("/products?category=mock"))
    rows = dict(re.findall(r'<span class="filter-label">([^<]+)</span>(.*?)</div>',
                           page, re.S))
    assert set(rows) >= {"학년", "시행년도", "시행월"}, list(rows)

    years = re.findall(r'>(\d{4}년)</a>', rows["시행년도"])
    assert years[-1] == "2024년", years          # 2024년부터
    assert years == sorted(years, reverse=True)   # 최근 것이 앞에
    for m in ("3월", "6월", "9월", "10월", "수능"):
        assert f">{m}</a>" in rows["시행월"], m

    # 교재 이름에 든 것을 그대로 읽습니다 — 하나하나 적어 넣지 않아도 됩니다
    books = {b["slug"]: b for b in sc.load_catalog()["books"]}
    assert sc.exam_of(books["mock-2026-06-g3"], "year") == "2026년"
    assert sc.exam_of(books["mock-2026-06-g3"], "month") == "6월"
    assert sc.exam_of(books["mock-2026-03-g2"], "month") == "3월"
    assert sc.exam_of({"name": "2027학년도 수능"}, "month") == "수능"
    assert sc.exam_of({"name": "2027학년도 수능"}, "year") == "2027년"

    def count(url):
        got = body(client().get(url))
        m = re.search(r'교재 (\d+)권', got)
        return int(m.group(1)) if m else 0

    assert count("/products?category=mock") == 2
    assert count("/products?category=mock&month=6월") == 1
    assert count("/products?category=mock&month=3월") == 1
    assert count("/products?category=mock&month=수능") == 0
    # 세 줄을 겹쳐 걸 수 있습니다
    assert count("/products?category=mock&year=2026년&month=6월&grade=고3") == 1
    assert count("/products?category=mock&year=2026년&month=6월&grade=고2") == 0

    # 고른 것은 다른 버튼을 눌러도 따라다닙니다
    picked = body(client().get("/products?category=mock&month=6월&grade=고3"))
    assert "month=6%EC%9B%94" in picked and "grade=%EA%B3%A03" in picked
    # 갈래가 다른 분류로 옮기면 안 맞는 것은 떨어집니다
    assert "month=6%EC%9B%94" not in picked.split('>교과서</a>', 1)[0].rsplit('<a', 1)[-1]

    # 관리자에서 교재마다 따로 적어 두실 수도 있습니다
    a = admin()
    form = body(a.get("/admin/books/mock-2026-06-g3/edit"))
    assert "시행년도" in form and "시행월" in form and "이름에서 알아서" in form
    print("PASS  모의고사 — 학년 · 시행년도 · 시행월로 좁히기")


def test_subject_filter_always_shows_four():
    """교과서 과목 줄에는 공통영어1·2 · 영어1·2 가 늘 나와야 합니다.

    갈래 값을 products.json 에 적어 두었는데, 사장님이 관리자에서 분류를 한 번
    손보시면 그 값이 사라진 채로 저장됐습니다. 그러면 손님 화면에 자료가 있는
    과목 하나만 남습니다. 값을 안 적어 두었을 때도 기본값이 나와야 합니다.
    """
    want = ["공통영어1", "공통영어2", "영어1", "영어2"]

    def subjects():
        page = body(client().get("/products?category=textbook"))
        row = page.split(">과목<", 1)[1].split("</div>", 1)[0]
        return [x for x in want if f">{x}<" in row]

    assert subjects() == want, "적어 둔 값이 안 나옵니다"

    # 분류에 값을 안 적어 두었을 때 — 라이브 원반이 이 꼴이었습니다
    cat = sc.load_raw_catalog()
    kept = None
    for c in cat["categories"]:
        if c.get("id") == "textbook":
            kept = c.pop("values", None)
    sc.save_catalog(cat)
    try:
        assert subjects() == want, "값을 안 적어 두면 기본값이 나와야 합니다"
        # products.json 에 적어 두면 그 차례를 따릅니다
        cat2 = sc.load_raw_catalog()
        for c in cat2["categories"]:
            if c.get("id") == "textbook":
                c["values"] = {"subject": ["영어2", "공통영어1"]}
        sc.save_catalog(cat2)
        page = body(client().get("/products?category=textbook"))
        row = page.split(">과목<", 1)[1].split("</div>", 1)[0]
        assert row.index(">영어2<") < row.index(">공통영어1<")
    finally:
        cat = sc.load_raw_catalog()
        for c in cat["categories"]:
            if c.get("id") == "textbook":
                c["name"] = "교과서"
                c["values"] = kept if kept else None
                if not kept:
                    c.pop("values", None)
        sc.save_catalog(cat)
    assert subjects() == want
    print("PASS  교과서 과목 네 가지는 늘 나옴 (적어 두지 않아도)")


def test_cart_asks_you_to_compare_not_claims():
    """다 더한 값을 무엇과 견줄지 알려 주되, 값이 얼마라고 주장하지 않아야 합니다.

    학원비도 선생님 시간도 우리가 입증할 수 없는 값입니다. 숫자를 못 박으면
    부당표시가 되고, 학원 선생님도 우리 손님이라 때려서도 안 됩니다.
    """
    cat = sc.load_catalog()
    of = {}
    for pid, pack in {x["id"]: x for x in cat["packages"]}.items():
        of[pid] = [x["slug"] for m in pack["materials"] for x in cat["products"]
                   if x.get("book") == "ybm-han" and x.get("unit") == "Lesson 1"
                   and x.get("materials") == [m]]

    c = client()
    c.post("/cart/add", data={"slug": ",".join(of["analysis"])})
    one = body(c.get("/cart"))
    assert "worth-box" not in one, "한 묶음만 담았는데 '다 더한 값' 이 나옵니다"

    c.post("/cart/add", data={"slug": ",".join(of["problem"])})
    two = body(c.get("/cart"))
    assert "worth-box" in two
    assert "학원 한 달 수강료와 견줘 보세요" in two
    assert "자료를 찾고 만드는 시간과 견줘 보세요" in two

    # 우리가 모르는 값을 숫자로 말하면 안 됩니다
    for claim in ("학원비 3", "학원 월 ", "무조건", "100%", "최저가", "시간을 절약해 드립니다"):
        assert claim not in two, claim

    # 값이 보이는 화면에는 어디든 같은 두 줄이 붙습니다 — 한 곳에서 만들어 씁니다
    for url in ("/books/ybm-han", "/products/ybm-han-analysis"):
        page = body(client().get(url))
        assert "학원 한 달 수강료와 견줘 보세요" in page, url
        assert "자료를 찾고 만드는 시간과 견줘 보세요" in page, url
        # 그 교재 값만 나오는 화면이라 '다 더한 값' 이라고 하면 안 됩니다
        assert "다 더한" not in page and "아우른" not in page, url

    c.post("/cart/clear")
    print("PASS  다 더한 값은 견주시라고만 · 숫자로 주장하지 않음")


def test_cart_shows_packages_not_parts():
    """파는 단위는 패키지입니다. 장바구니도 낱개가 아니라 묶음으로 보여야 합니다.

    한 강을 담으면 자료 여러 종이 한꺼번에 들어갑니다. 그것을 한 줄씩 늘어놓고
    낱개로 빼게 두면, 팔지 않는 조합을 손님이 만들 수 있게 됩니다.
    """
    cat = sc.load_catalog()
    known = {x["slug"]: x for x in cat["products"]}
    packs = {x["id"]: x for x in cat["packages"]}
    book, unit = "ybm-han", "Lesson 1"
    of = {}
    for pid, pack in packs.items():
        of[pid] = [x["slug"] for m in pack["materials"]
                   for x in cat["products"]
                   if x.get("book") == book and x.get("unit") == unit
                   and x.get("materials") == [m]]
        assert len(of[pid]) == len(pack["materials"]), pid

    c = client()
    c.post("/cart/add", data={"slug": ",".join(of["analysis"])})
    page = body(c.get("/cart"))
    assert page.count('class="cart-row"') == 1, "8종이 여덟 줄로 늘어섰습니다"
    assert f"지문분석 {len(packs['analysis']['materials'])}종 패키지" in page
    assert "Lesson 1" in page
    # 담긴 자료는 딱지로 다 보입니다
    mats = {m["id"]: m["name"] for m in sc.load_materials()["materials"]}
    for mid in packs["analysis"]["materials"]:
        assert mats[mid] in page, mid

    # 두 패키지를 다 담아도 두 줄. 겹치는 자료 값은 한 번만 붙습니다
    c.post("/cart/add", data={"slug": ",".join(of["problem"])})
    page = body(c.get("/cart"))
    assert page.count('class="cart-row"') == 2, page.count('class="cart-row"')
    both = {s for pid in of for s in of[pid]}
    want = sum(known[s]["price"] for s in both)
    assert f"{want:,}원" in page
    # 겹치는 자료도 두 묶음 딱지에 모두 적힙니다 (실제로 받으시는 것이니까요)
    shared = set(packs["analysis"]["materials"]) & set(packs["problem"]["materials"])
    assert shared, "겹치는 자료가 없으면 이 시험은 뜻이 없습니다"
    for mid in shared:
        assert page.count(mats[mid]) >= 2, mid

    # 한 묶음을 빼면 그 묶음만 빠지고, 남는 묶음은 온전해야 합니다
    row = page.split('class="cart-row"', 1)[1]
    slugs = row.split('name="slug" value="', 1)[1].split('"', 1)[0]
    assert "," in slugs, "빼기가 자료 하나만 지우고 있습니다"
    c.post("/cart/remove", data={"slug": slugs})
    left = body(c.get("/cart"))
    assert left.count('class="cart-row"') == 1
    # 남은 묶음에서 겹치는 자료가 딸려 나가면 안 됩니다
    for mid in packs["problem"]["materials"]:
        assert mats[mid] in left, mid
    assert f"{sum(known[s]['price'] for s in of['problem']):,}원" in left

    # 주문서도 같은 단위로 보여 줍니다
    order = body(c.get("/order?cart=1"))
    assert order.count('class="order-item"') == 1
    assert f"문제 {len(packs['problem']['materials'])}종 패키지" in order
    c.post("/cart/clear")
    print("PASS  장바구니·주문서는 패키지 단위 · 빼기도 묶음째")


def test_cart_add_view_remove():
    """여러 회차를 담고, 빼고, 비울 수 있어야 합니다."""
    c = client()
    assert "담긴 자료가 없습니다" in body(c.get("/cart"))

    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    page = body(c.get("/cart"))
    assert "능률(김성곤)" in page and "수능특강" in page
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    a, b = price["neungyule-kim-analysis"], price["ebs-2026-tokgang-eng-analysis"]
    assert f"{a:,}원" in page and f"{b:,}원" in page
    assert f"{a + b:,}원" in page

    # 같은 것을 또 담아도 한 번만 들어갑니다
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    assert body(c.get("/cart")).count('class="cart-row"') == 2

    c.post("/cart/remove", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    left = body(c.get("/cart"))
    assert left.count('class="cart-row"') == 1 and "수능특강" not in left

    c.post("/cart/clear")
    assert "담긴 자료가 없습니다" in body(c.get("/cart"))
    print("PASS  장바구니 담기 · 빼기 · 비우기")


def test_cart_count_discount_steps():
    """담은 개수가 늘 때마다 할인 단계가 올라가야 합니다."""
    _set_discount()
    c = client()
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    q1 = c.get("/order/quote?cart=1").get_json()
    assert q1["rows"] == [], "1개인데 할인이 붙었습니다"
    assert q1["next_tier"] == {"min": 3, "percent": 10}

    c.post("/cart/add", data={"slug": "neungyule-kim-problem"})
    assert c.get("/order/quote?cart=1").get_json()["rows"] == []      # 2개도 정가

    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    q3 = c.get("/order/quote?cart=1").get_json()
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    assert q3["subtotal"] == sum(price[x] for x in (
        "neungyule-kim-analysis", "neungyule-kim-problem",
        "ebs-2026-tokgang-eng-analysis"))
    assert q3["rows"][0]["percent"] == 10
    assert q3["final"] == q3["subtotal"] - q3["subtotal"] * 10 // 100

    for slug in ("ybm-han-analysis", "ybm-han-problem", "mock-2026-06-g3-analysis"):
        c.post("/cart/add", data={"slug": slug})
    q6 = c.get("/order/quote?cart=1").get_json()
    assert q6["rows"][0]["name"] == "6개 담기" and q6["rows"][0]["percent"] == 15
    assert q6["next_tier"] == {"min": 12, "percent": 20}
    print("PASS  담은 개수가 늘면 할인 단계가 올라감")


def test_cart_nudges_to_next_step():
    """'몇 개만 더 담으면 얼마' 를 알려 줘야 더 담습니다."""
    _set_discount()
    c = client()
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    page = body(c.get("/cart"))
    assert "2개만 더" in page and "10% 할인" in page
    print("PASS  '몇 개만 더 담으면' 안내")


def test_cart_order_end_to_end():
    """장바구니로 주문하면 한 건으로 접수되고, 자료는 전부 나가야 합니다."""
    _set_discount()
    c = client()
    for slug in ("neungyule-kim-analysis", "neungyule-kim-problem"):
        c.post("/cart/add", data={"slug": slug})

    form = body(c.get("/order?cart=1"))
    assert form.count('class="order-item"') == 2
    assert "장바구니에서 고치기" in form
    assert "문제 패키지도 함께 받기" not in form      # 장바구니에서는 짝 체크박스가 없습니다

    resp = c.post("/order", data={
        "cart": "1", "name": "장바구니", "phone": "010-3333-4444",
        "email": "cart@example.com", "agree": "1"})
    assert resp.status_code == 302
    assert "담긴 자료가 없습니다" in body(c.get("/cart")), "주문 뒤에도 장바구니가 남았습니다"

    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'cart@example.com'").fetchone()
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    assert row["amount"] == (price["neungyule-kim-analysis"]
                             + price["neungyule-kim-problem"])   # 2개는 정가입니다
    assert row["product_slug"] == "neungyule-kim-analysis"
    assert row["extra_slugs"] == "neungyule-kim-problem"

    # 자료를 내보내면 두 건 모두 링크가 나가야 합니다
    for slug in ("neungyule-kim-analysis", "neungyule-kim-problem"):
        folder = sc.product_dir(slug)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "x.pdf").write_bytes(b"%PDF-1.4 x\n")
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    done = body(client().get(f"/order/done/{row['view_key']}"))
    assert done.count('href="/d/') == 2, "두 자료 모두 링크가 나오지 않았습니다"
    print("PASS  장바구니 주문 → 한 번 입금 → 자료 전부 발송")


def test_cart_shows_count_in_header():
    """딱지의 수는 장바구니에 보이는 줄 수와 같아야 합니다.

    한 강의 분석 패키지는 상품 여덟 개로 담깁니다. 그런데 담은 것은 '1강의
    패키지 하나' 입니다. 딱지에 8이 뜨면 여덟 번 담은 줄 알고 놀랍니다.
    """
    c = client()
    assert 'class="cart-count"' not in body(c.get("/"))
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    assert '<span class="cart-count">1</span>' in body(c.get("/"))
    c.post("/cart/clear")

    # 한 강 · 분석 패키지 = 상품 여덟 개 → 딱지는 1
    cat = sc.load_catalog()
    pack = next(x for x in cat["packages"] if x["id"] == "analysis")
    unit = [x["slug"] for mid in pack["materials"] for x in cat["products"]
            if x.get("book") == "ybm-han" and x.get("unit") == "Lesson 1"
            and x.get("materials") == [mid]]
    assert len(unit) == 8, unit
    c.post("/cart/add", data={"slug": ",".join(unit)})
    page = body(c.get("/"))
    assert '<span class="cart-count">1</span>' in page, "딱지가 파일 수를 세고 있습니다"
    assert body(c.get("/cart")).count('class="cr-name"') == 1

    # 같은 강에 문제 패키지까지 담으면 줄이 둘 — 딱지도 둘
    prob = next(x for x in cat["packages"] if x["id"] == "problem")
    more = [x["slug"] for mid in prob["materials"] for x in cat["products"]
            if x.get("book") == "ybm-han" and x.get("unit") == "Lesson 1"
            and x.get("materials") == [mid]]
    c.post("/cart/add", data={"slug": ",".join(more)})
    assert '<span class="cart-count">2</span>' in body(c.get("/"))
    assert body(c.get("/cart")).count('class="cr-name"') == 2
    c.post("/cart/clear")
    print("PASS  머리말 딱지는 담은 묶음 수")


def test_cart_add_only_known_products():
    """없는 주소를 넣어도 장바구니가 더러워지지 않아야 합니다."""
    c = client()
    c.post("/cart/add", data={"slug": "없는상품"})
    c.post("/cart/add", data={"slug": "../../etc/passwd"})
    assert "담긴 자료가 없습니다" in body(c.get("/cart"))
    # 바깥 주소로 돌려보내지 않습니다
    resp = c.post("/cart/add", data={"slug": "neungyule-kim-analysis",
                                     "next": "https://example.com/"})
    assert resp.headers["Location"].endswith("/cart")
    print("PASS  장바구니에 아무거나 못 담음 · 바깥으로 안 보냄")


# ---- 구매자 표시 (워터마크) ------------------------------------------------
def test_watermark_stamps_buyer_on_pdf():
    """받은 PDF 에 구매자 이메일과 주문번호가 새겨져 있어야 합니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return

    site = sc.load_site()
    site["watermark"] = {"enabled": True,
                         "footer": "{이름} · {이메일} · {주문번호} · {브랜드} 제공 · 재배포 금지",
                         "center": "{이메일}"}
    sc.save_site(site)

    slug = "ybm-han-analysis"
    folder = sc.product_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    from reportlab.pdfgen import canvas as rl_canvas
    src = folder / "본문.pdf"
    page = rl_canvas.Canvas(str(src))
    page.drawString(72, 700, "passage one")
    page.showPage()
    page.save()
    plain = src.stat().st_size

    c = client()
    resp = c.post("/order", data={
        "slug": slug, "name": "새김이", "phone": "010-8888-1111",
        "email": "mark@example.com", "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'mark@example.com'").fetchone()
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        dl = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()

    site = sc.load_site(); site["delivery"] = {"mode": "both"}; sc.save_site(site)
    got = client().get(f"/d/{dl['token']}/0")
    assert got.status_code == 200
    assert got.data.startswith(b"%PDF")
    assert len(got.data) != plain, "원본이 그대로 나왔습니다"

    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(got.data)).pages[0].extract_text()
    assert "mark@example.com" in text
    assert row["order_no"] in text
    assert "재배포 금지" in text
    assert "passage one" in text, "원래 내용이 사라졌습니다"

    # 원본 파일은 그대로여야 합니다
    assert src.stat().st_size == plain

    # 화면으로 볼 때도 같은 표시가 새겨진 그림이 나옵니다
    site["delivery"] = {"mode": "view"}; sc.save_site(site)
    view = body(client().get(f"/d/{dl['token']}/view/0"))
    assert "인쇄하기" in view and "1쪽" in view
    png = client().get(f"/d/{dl['token']}/page/0/0.png")
    assert png.status_code == 200 and png.data[:4] == b"\x89PNG"
    assert "no-store" in png.headers.get("Cache-Control", "")
    print("PASS  받은 PDF 에 구매자 표시가 새겨짐 · 화면 보기도 같은 표시")


def test_watermark_is_order_number_only():
    """기본 문구는 주문번호 하나입니다. 이름·이메일은 지면에 안 찍습니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return

    # 사장님이 아무것도 안 고치셨을 때 나가는 문구
    assert sc.WATERMARK_DEFAULTS["footer"] == "{주문번호}"
    assert sc.WATERMARK_DEFAULTS["center"] == "{주문번호}"
    # 앞선 테스트가 임시본을 고쳐 놓으므로, 실제로 배포되는 원본을 봅니다
    shipped = json.loads((_SRC / "site.json").read_text())["watermark"]
    assert shipped["footer"] == "{주문번호}" and shipped["center"] == "{주문번호}"

    site = sc.load_site()
    site["watermark"] = dict(site.get("watermark") or {}, enabled=True,
                             footer=sc.WATERMARK_DEFAULTS["footer"],
                             center=sc.WATERMARK_DEFAULTS["center"])
    site["delivery"] = {"mode": "both"}
    sc.save_site(site)

    slug = "ybm-han-analysis"
    folder = sc.product_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    from reportlab.pdfgen import canvas as rl_canvas
    page = rl_canvas.Canvas(str(folder / "본문.pdf"))
    page.drawString(72, 700, "passage one")
    page.showPage()
    page.save()

    client().post("/order", data={"slug": slug, "name": "번호만", "phone": "010-7777-2222",
                                  "email": "onlyno@example.com", "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'onlyno@example.com'").fetchone()
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        tok = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()[0]

    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(client().get(f"/d/{tok}/0").data)).pages[0].extract_text()
    assert row["order_no"] in text, "주문번호가 안 찍혔습니다"
    assert text.count(row["order_no"]) >= 2, "아래 한 줄 · 가운데 두 군데에 있어야 합니다"
    assert "onlyno@example.com" not in text, "이메일이 지면에 새겨졌습니다"
    assert "번호만" not in text, "이름이 지면에 새겨졌습니다"
    assert "passage one" in text

    # 그 번호로 주문 목록에서 누구인지 찾을 수 있어야 뜻이 있습니다
    found = body(admin().get(f"/admin/orders?q={row['order_no']}"))
    assert "onlyno@example.com" in found and "번호만" in found

    # 손님 화면에는 표시 이야기를 한 마디도 안 합니다
    site["delivery"] = {"mode": "view"}; sc.save_site(site)
    view = body(client().get(f"/d/{tok}/view/0"))
    for word in ("워터마크", "새겨", "표시 없는 판", "구매자 표시"):
        assert word not in view, word
    print("PASS  워터마크는 주문번호만 — 이름·이메일은 지면에 안 찍힘")


def test_print_only_viewer():
    """자료를 파일로 넘기지 않고 화면에서 보고 인쇄하게 합니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    a = admin()
    slug = "mock-2026-03-g2-problem"
    folder = sc.product_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    from reportlab.pdfgen import canvas as rl_canvas
    page = rl_canvas.Canvas(str(folder / "변형문제.pdf"))
    for n in ("첫 쪽", "둘째 쪽"):
        page.drawString(72, 700, n)
        page.showPage()
    page.save()
    (folder / "묶음.zip").write_bytes(b"PK\x03\x04zip")

    c = client()
    r = c.post("/order", data={"slug": slug, "name": "인쇄만", "phone": "010-3333-9999",
                               "email": "printonly@example.com", "agree": "1"})
    key = r.headers["Location"].rsplit("/", 1)[-1]
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE view_key = ?", (key,)).fetchone()
    a.post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        token = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()[0]

    # 받는 화면 — PDF 는 '열기', ZIP 은 '받기'
    page1 = body(client().get(f"/d/{token}"))
    assert "자료를 보고 인쇄하세요" in page1
    assert "화면에서 보고 인쇄" in page1 and "변형문제.pdf" in page1
    assert "묶음.zip" in page1

    names = [f["name"] for f in sc.product_files(slug)]
    pdf_i, zip_i = names.index("변형문제.pdf"), names.index("묶음.zip")

    # PDF 를 파일로 달라고 해도 보기 화면으로 돌려보냅니다
    got = client().get(f"/d/{token}/{pdf_i}")
    assert got.status_code == 302 and f"/view/{pdf_i}" in got.headers["Location"]
    # ZIP 은 화면에서 못 여니 그대로 받습니다
    assert client().get(f"/d/{token}/{zip_i}").status_code == 200

    # 보기 화면 — 쪽마다 그림
    view = body(client().get(f"/d/{token}/view/{pdf_i}"))
    assert "인쇄하기" in view and "2쪽" in view
    assert view.count(f"/d/{token}/page/{pdf_i}/") == 2
    assert 'name="robots" content="noindex' in view      # 검색에 안 걸리게

    png = client().get(f"/d/{token}/page/{pdf_i}/0.png")
    assert png.status_code == 200 and png.data[:4] == b"\x89PNG"
    assert "no-store" in png.headers.get("Cache-Control", "")
    assert client().get(f"/d/{token}/page/{pdf_i}/99.png").status_code == 404
    # 열쇠가 없으면 한 쪽도 못 봅니다
    assert client().get(f"/d/없는열쇠/page/{pdf_i}/0.png").status_code == 404
    assert client().get(f"/d/없는열쇠/view/{pdf_i}").status_code == 404

    # 카카오톡·인스타 안 브라우저는 인쇄 명령이 없습니다. 길을 알려 줍니다.
    assert "인쇄 창이 안 열리셨나요?" in view
    assert "다른 브라우저로 열기" in view
    assert "onclick=\"window.print()\"" not in view     # 눌러도 조용히 아무 일 없던 것

    # 인쇄하면 한 장에 한 쪽씩 나가야 합니다
    css = body(client().get("/static/store.css"))
    assert "@page{size:A4 portrait; margin:0;}" in css
    assert ".vpage{margin:0;" in css and "break-after:page" in css

    # 관리자 화면에서 방식을 고를 수 있습니다
    setting = body(a.get("/admin/settings"))
    assert "자료를 어떻게 내어 줄까" in setting
    assert "화면에서 보고 인쇄만" in setting and "보기 + 파일 받기 둘 다" in setting
    assert "PDF로 저장' 인쇄까지 막지는 못합니다" in setting     # 솔직하게 적어 둡니다
    print("PASS  화면에서 보고 인쇄만 (파일은 안 넘김)")


def test_watermark_can_be_turned_off():
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    site = sc.load_site()
    site["watermark"] = {"enabled": False}
    site["delivery"] = {"mode": "both"}          # 파일로 받아 보고 확인합니다
    sc.save_site(site)

    with store.app.app_context():
        dl = sc.get_db().execute(
            """SELECT d.token FROM downloads d JOIN orders o ON o.order_no = d.order_no
               WHERE o.email = 'mark@example.com'""").fetchone()
    got = client().get(f"/d/{dl['token']}/0")
    assert got.status_code == 200, got.status_code
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(got.data)).pages[0].extract_text()
    assert "mark@example.com" not in text
    site["watermark"] = {"enabled": True}
    site["delivery"] = {"mode": "view"}
    sc.save_site(site)
    print("PASS  워터마크 끄기")


def test_watermark_skips_non_pdf():
    """ZIP·한글 파일은 손대지 않아야 합니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    folder = sc.product_dir("ybm-han-analysis")
    zipped = folder / "묶음.zip"
    zipped.write_bytes(b"PK\x03\x04not-a-pdf")
    assert wm.stamp(zipped, "누구 · 무엇") is None
    print("PASS  PDF 아닌 파일은 그대로")


# ---- 부분 · 전체 가격 -----------------------------------------------------
def test_full_pack_offer_in_cart():
    """필요한 강만 사되, 여러 개 담으면 전체가 싸다고 알려 줘야 합니다."""
    c = client()
    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    one = body(c.get("/cart"))
    assert "전체를 사시면 더 쌉니다" not in one, "하나만 담았는데 전체를 권했습니다"

    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-2-analysis"})
    price = {p["slug"]: p["price"] for p in sc.load_catalog()["products"]}
    parts = price["ebs-2026-tokgang-eng-analysis"] + price["ebs-2026-tokgang-eng-2-analysis"]
    full = price["ebs-2026-tokgang-eng-all-analysis"]
    two = body(c.get("/cart"))
    assert "전체를 사시면 더 쌉니다" in two
    assert f"{parts - full:,}원" in two        # 낱개 합계 − 전강
    assert "전강(1~10강)" in two

    c.post("/cart/swap", data={"slug": "ebs-2026-tokgang-eng-all-analysis"})
    after = body(c.get("/cart"))
    assert after.count('class="cart-row"') == 1
    assert "전강(1~10강)" in after and f"{full:,}원" in after
    print("PASS  부분 여러 개 → 전체가 싸다 → 한 번에 바꾸기")


def test_part_page_points_to_full():
    """부분 상품 화면에서도 전체가 있다는 것을 알려 줘야 합니다."""
    text = body(client().get("/products/ebs-2026-tokgang-eng-analysis"))
    assert "전강(1~10강)" in text and "따로 사시는 것보다 쌉니다" in text
    # 전체 상품 화면에는 그 안내가 없어야 합니다
    full = body(client().get("/products/ebs-2026-tokgang-eng-all-analysis"))
    assert "따로 사시는 것보다 쌉니다" not in full
    print("PASS  부분 화면에서 전체 안내")


def test_full_pack_needs_to_be_cheaper():
    """전체가 부분 합계보다 비싸면 권하지 않아야 합니다."""
    catalog = sc.load_raw_catalog()
    full = next(x for x in catalog["products"]
                if x["slug"] == "ebs-2026-tokgang-eng-all-analysis")
    keep = full["price"]
    full["price"] = 99000
    sc.save_catalog(catalog)
    try:
        c = client()
        for slug in ("ebs-2026-tokgang-eng-analysis", "ebs-2026-tokgang-eng-2-analysis"):
            c.post("/cart/add", data={"slug": slug})
        assert "전체를 사시면 더 쌉니다" not in body(c.get("/cart"))
    finally:
        full["price"] = keep
        sc.save_catalog(catalog)
    print("PASS  전체가 더 비싸면 안 권함")


# ---- 개인정보는 최소로 -----------------------------------------------------
def test_contact_rules_name_and_email_required():
    """성함(입금자 확인)과 이메일(자료가 가는 곳)만 꼭 받습니다."""
    c = client()

    # 연락처는 안 적으셔도 됩니다
    ok = c.post("/order", data={
        "slug": "ybm-han-analysis", "name": "연락처없음",
        "email": "nophone@example.com", "agree": "1"})
    assert ok.status_code == 302, "연락처 없이 주문이 막혔습니다"

    # 성함은 꼭 받습니다
    noname = c.post("/order", data={
        "slug": "ybm-han-analysis", "phone": "010-1111-2222",
        "email": "noname@example.com", "agree": "1"})
    assert noname.status_code == 400
    assert "입금하신 분을 확인하는 데 씁니다" in body(noname)

    # 적으셨는데 형식이 틀리면 알려 줍니다
    weird = c.post("/order", data={
        "slug": "ybm-han-analysis", "name": "형식", "phone": "전화번호아님",
        "email": "x@y.com", "agree": "1"})
    assert weird.status_code == 400 and "숫자와" in body(weird)

    # 이메일은 여전히 꼭 받습니다
    nomail = c.post("/order", data={
        "slug": "ybm-han-analysis", "name": "메일없음", "agree": "1"})
    assert nomail.status_code == 400 and "자료를 이 주소로" in body(nomail)

    # 화면 문구도 그렇게 되어 있어야 합니다
    form = body(client().get("/order?slug=ybm-han-analysis"))
    assert "입금하신 분을 확인하는 데 씁니다" in form
    assert "적어 주시면 문제가 생겼을 때 곧바로 연락드릴 수 있습니다" in form
    assert '연락처 <span class="hint">선택</span>' in form
    print("PASS  성함·이메일은 필수 · 연락처는 선택")


def test_affiliation_is_not_collected():
    """소속은 이제 받지 않습니다."""
    for path in ("/order?slug=ybm-han-analysis", "/custom", "/submit", "/pass"):
        page = body(client().get(path))
        assert "affiliation" not in page and "소속" not in page, path

    # 보내도 저장되지 않아야 합니다
    c = client()
    c.post("/order", data={"slug": "ybm-han-analysis", "name": "소속없이",
                           "phone": "010-5555-1111",
                           "email": "noaff@example.com", "affiliation": "○○학원",
                           "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT affiliation FROM orders WHERE email = 'noaff@example.com'").fetchone()
    assert not row["affiliation"], f"소속이 저장됐습니다: {row['affiliation']}"

    # 개인정보 안내도 맞춰져 있어야 합니다
    guide = body(client().get("/guide"))
    collected = guide.split("1. 수집하는 항목과 목적")[1].split("2. 보유 기간")[0]
    assert "(선택) 소속" not in collected, "수집 항목에 소속이 남아 있습니다"
    assert "소속은 받지 않습니다" in guide
    assert "입금하신 분을 알아보려면 성함이 필요합니다" in guide
    print("PASS  소속은 받지 않음")


def test_watermark_does_not_bloat_the_file():
    """새긴 뒤 파일이 몇 배로 커지면 안 됩니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    from reportlab.pdfgen import canvas as rl
    src = sc.DATA_DIR / "bloat-test.pdf"
    page = rl.Canvas(str(src))
    for i in range(20):
        for line in range(40):
            page.drawString(60, 780 - line * 18, f"page {i} line {line} sample text here")
        page.showPage()
    page.save()
    before = src.stat().st_size
    after = len(wm.stamp(src, "홍길동 · a@b.com · OR-1", "a@b.com"))
    assert after < before * 3, f"{before} → {after} 로 너무 커졌습니다"
    src.unlink()
    print(f"PASS  새겨도 파일이 안 부풂 ({before // 1024}KB → {after // 1024}KB)")


def test_watermark_wording_is_editable():
    """워터마크 문구는 관리자가 정합니다. 자리표가 실제 값으로 바뀌어야 합니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    site = sc.load_site()
    site["watermark"] = {"enabled": True,
                         "footer": "{브랜드} · {주문번호} · 무단 배포 금지",
                         "center": "{이름}"}
    site["delivery"] = {"mode": "both"}
    sc.save_site(site)
    with store.app.app_context():
        dl = sc.get_db().execute(
            """SELECT d.token FROM downloads d JOIN orders o ON o.order_no = d.order_no
               WHERE o.email = 'mark@example.com'""").fetchone()
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(client().get(f"/d/{dl['token']}/0").data)).pages[0].extract_text()
    assert "무단 배포 금지" in text
    assert "새김이" in text                    # {이름} 이 실제 값으로
    assert "mark@example.com" not in text      # 이번 문구엔 이메일이 없습니다
    site["delivery"] = {"mode": "view"}; sc.save_site(site)
    print("PASS  워터마크 문구를 관리자가 정함")


def test_no_word_about_the_watermark():
    """손님에게는 표시 이야기를 하지 않습니다. 값을 더 받고 빼 주는 것도 없앴습니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    site = sc.load_site()
    site["watermark"] = {"enabled": True, "footer": "{주문번호}", "center": "{주문번호}"}
    site["delivery"] = {"mode": "both"}
    sc.save_site(site)

    slug = "ybm-han-analysis"
    folder = sc.product_dir(slug)
    folder.mkdir(parents=True, exist_ok=True)
    from reportlab.pdfgen import canvas as rl_canvas
    page = rl_canvas.Canvas(str(folder / "본문.pdf"))
    page.drawString(72, 700, "passage one")
    page.showPage()
    page.save()

    # 주문서 어디에도 표시 이야기가 없습니다
    form = body(client().get(f"/order?slug={slug}"))
    for word in ("워터마크", "표시 없는 판", "구매자 표시", "새겨", "옅게", "no_mark"):
        assert word not in form, word

    # 값을 더 받는 길 자체가 없습니다 — 체크를 흉내 내 보내도 금액이 안 늘어납니다
    quote = client().get(f"/order/quote?slug={slug}&nomark=1&coupon=").get_json()
    assert "extra" not in quote
    plain = client().get(f"/order/quote?slug={slug}&coupon=").get_json()
    assert quote["final"] == plain["final"]

    client().post("/order", data={"slug": slug, "no_mark": "1", "name": "몰래",
                                  "phone": "010-4444-5555", "email": "quiet@example.com",
                                  "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'quiet@example.com'").fetchone()
    want = next(p["price"] for p in sc.load_catalog()["products"] if p["slug"] == slug)
    assert row["amount"] == want, row["amount"]       # 더 붙은 값이 없습니다
    assert row["no_mark"] == 0                        # 체크를 보내도 안 먹습니다

    # 그래도 표시는 조용히 새겨집니다
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        tok = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()[0]
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(client().get(f"/d/{tok}/0").data)).pages[0].extract_text()
    assert row["order_no"] in text

    # 받는 화면 · 내 자료함에도 이야기가 없습니다
    for page_body in (body(client().get(f"/d/{tok}")), body(client().get("/locker"))):
        for word in ("워터마크", "구매자 표시", "표시 없는 판"):
            assert word not in page_body, word

    # 관리자 설정에서도 값 받는 칸이 사라졌습니다
    adm = body(admin().get("/admin/settings"))
    assert "watermark_optout_price" not in adm and "watermark_optout_enabled" not in adm
    assert "구매자 표시 (워터마크)" in adm            # 사장님께는 그대로 보입니다
    assert not hasattr(sc, "no_mark_price")

    site["delivery"] = {"mode": "view"}; sc.save_site(site)
    print("PASS  손님에게는 표시 이야기 없음 · 값 받고 빼 주기 없앰")


def test_email_typo_is_caught_once():
    """자료가 이메일로 가므로, 흔한 오타는 한 번 되물어야 합니다."""
    assert sc.email_typo("a@gmail.co") == "a@gmail.com"
    assert sc.email_typo("b@naver.con") == "b@naver.com"
    assert sc.email_typo("c@gmail.com") == ""
    assert sc.email_typo("d@school.ac.kr") == ""

    c = client()
    asked = c.post("/order", data={"slug": "ybm-han-analysis", "name": "오타",
                                   "phone": "010-2222-3333",
                                   "email": "teacher@gmail.co", "agree": "1"})
    assert asked.status_code == 400
    page = body(asked)
    assert "teacher@gmail.com" in page and "적은 주소가 맞습니다" in page

    # 맞다고 표시하면 그대로 접수됩니다
    ok = c.post("/order", data={"slug": "ybm-han-analysis", "name": "오타",
                                "phone": "010-2222-3333",
                                "email": "teacher@gmail.co", "agree": "1", "email_ok": "1"})
    assert ok.status_code == 302

    # 멀쩡한 주소는 되묻지 않습니다
    fine = c.post("/order", data={"slug": "ybm-han-analysis", "name": "정상",
                                  "phone": "010-2222-3333",
                                  "email": "fine@gmail.com", "agree": "1"})
    assert fine.status_code == 302
    print("PASS  이메일 오타 한 번 되묻기")


def test_product_form_offers_our_price():
    """상품 폼에서 우리 정가로 값을 계산해 넣을 수 있어야 합니다."""
    text = body(admin().get("/admin/products/new"))
    assert "우리 정가" in text and "계산해서 넣기" in text
    unit = sc.pricing_cfg(sc.load_site())["units"]["analysis"]
    assert f'"analysis":{unit}' in text.replace(" ", ""), unit
    print("PASS  상품 폼의 우리 정가 계산")


def run_all():
    test_uses_temp_data_only()
    test_public_pages_open()
    test_categories_include_textbook()
    test_lineup_shows_all_materials()
    test_home_reflects_lineup()
    test_notice_shows_live_now_section()
    test_home_previews_every_category()
    test_speaks_to_both_audiences()
    test_analysis_tagline_updated()
    test_new_product_appears_in_home_updates()
    test_units_follow_what_the_admin_uploaded()
    test_list_hides_price_until_you_open_the_book()
    test_custom_request_takes_files_by_drag_and_drop()
    test_made_to_order_has_its_own_way_in()
    test_taster_is_given_away_not_sold()
    test_sample_pdf_links_go_somewhere()
    test_all_types_are_listed_with_killers_marked()
    test_question_count_is_spelled_out()
    test_home_tiles_share_one_magnification()
    test_lineup_shows_a_slice_not_the_whole_page()
    test_lineup_shots_upload_and_show()
    test_mobile_filters_collapse()
    test_long_pages_have_shortcuts()
    test_home_updates_skip_pinned_notice()
    test_home_counts_dday_to_next_exam()
    test_exam_schedule_fills_itself()
    test_saving_unchanged_exams_keeps_them_automatic()
    test_admin_edits_exam_schedule()
    test_two_packages_per_book()
    test_sibling_package_cross_sell()
    test_textbook_subjects_are_the_four()
    test_material_chips_are_coloured_by_package()
    test_package_filter()
    test_products_grouped_by_book()
    test_grade_filter_and_sort()
    test_popular_order()
    test_book_page_splits_lanes()
    test_search_finds_by_publisher_and_book()
    test_share_and_branding()
    test_book_page_lists_only_its_products()
    test_home_links_every_category_and_search_word()
    test_pass_twelve_month_price()
    test_pass_preorder_discount()
    test_pass_preorder_records_promised_price()
    test_order_page_shows_what_you_are_buying()
    test_manual_line_break_filter()
    test_no_emoji_on_customer_pages()
    test_contact_rules_name_and_email_required()
    test_affiliation_is_not_collected()
    test_email_typo_is_caught_once()
    test_order_rejects_bad_input()
    test_order_saves_and_multiplies_amount()
    test_order_both_packages_at_once()
    test_order_rejects_unknown_coupon()
    test_count_discount()
    test_no_loyalty_anywhere()
    test_discount_has_a_ceiling()
    test_request_needs_no_passage()
    test_custom_request_accepted()
    test_request_requires_wanted()
    test_submit_takes_photos_by_drag_and_drop()
    test_submission_to_coupon_to_discount()
    test_submission_requires_file_or_link()
    test_mock_filters_by_year_and_month()
    test_subject_filter_always_shows_four()
    test_cart_asks_you_to_compare_not_claims()
    test_cart_shows_packages_not_parts()
    test_cart_add_view_remove()
    test_cart_count_discount_steps()
    test_cart_nudges_to_next_step()
    test_cart_shows_count_in_header()
    test_cart_add_only_known_products()
    test_order_to_download_flow()
    test_cart_order_end_to_end()
    test_full_pack_offer_in_cart()
    test_part_page_points_to_full()
    test_full_pack_needs_to_be_cheaper()
    test_order_page_shows_download_when_ready()
    test_deliver_by_external_link()
    test_watermark_stamps_buyer_on_pdf()
    test_watermark_is_order_number_only()
    test_print_only_viewer()
    test_watermark_can_be_turned_off()
    test_watermark_wording_is_editable()
    test_no_word_about_the_watermark()
    test_watermark_skips_non_pdf()
    test_watermark_does_not_bloat_the_file()
    test_download_revoke_and_limit()
    test_receipt_request_and_sales()
    test_every_admin_route_is_locked()
    test_login_blocks_repeated_guesses()
    test_admin_not_indexed_and_login_is_standalone()
    test_login_next_cannot_leave_admin()
    test_footprints_count_people_not_files()
    test_footprints_tell_where_people_come_from()
    test_footprints_show_where_people_stop()
    test_traffic_numbers_never_reach_customers()
    test_admin_traffic_screen_reads_at_a_glance()
    test_submit_page_promises_only_a_coupon()
    test_word_study_is_reachable_from_the_menu()
    test_admin_menu_is_short()
    test_admin_pages_open()
    test_bulk_products_from_zip()
    test_book_pick_grid()
    test_shared_materials_are_charged_once()
    test_every_book_has_unit_checkboxes()
    test_disk_keeps_your_files_but_refreshes_the_rest()
    test_admin_can_reload_the_examples()
    test_admin_pricing_is_editable()
    test_product_form_offers_our_price()
    test_setup_checklist_guides_first_day()
    test_admin_forms_offer_buttons_not_typing()
    test_admin_creates_product_visible_on_site()
    test_admin_edits_material_and_site_reflects()
    test_admin_product_materials_saved()
    test_admin_rejects_duplicate_slug()
    test_admin_book_and_category_flow()
    test_admin_notice_appears_on_home()
    test_admin_settings_change_reaches_customer()
    test_backup_download_and_restore()
    test_full_backup_has_orders()
    test_order_page_cannot_be_enumerated()
    test_security_headers_everywhere()
    test_public_forms_are_rate_limited()
    test_free_list_hides_items_without_files()
    test_free_open_item_downloads_without_email()
    test_free_gated_item_needs_email()
    test_free_notify_collects_email()
    test_admin_creates_free_item_end_to_end()
    test_free_kind_suggests_email_gate()
    test_seo_tags_on_public_pages()
    test_seo_verification_code_paste()
    test_page_width_uses_the_screen()
    test_brand_is_korean_for_search()
    test_old_brand_is_renamed_even_on_the_live_disk()
    test_search_result_title_is_editable()
    test_sitemap_lists_free_items()
    test_lineup_offers_sample_pdf()
    test_free_search_and_filters()
    test_policy_sections_are_filled_in()
    test_request_menu_renamed_to_jaryo()
    # 예시 데이터를 지우는 테스트는 다른 테스트가 그 상품을 쓰므로 맨 뒤에 둡니다.
    test_word_quiz()
    test_save_sheet_to_my_locker()
    test_make_screen_four_steps()
    test_wordbooks_are_grouped_by_publisher()
    test_word_counts_per_kind_and_cap()
    test_word_file_upload()
    test_sheet_heading()
    test_whole_book_upload()
    test_wordfile_table_shapes()
    test_pass_shows_what_each_plan_covers()
    test_pass_counts_passages()
    test_metrics_screen()
    test_storage_warning_when_data_would_vanish()
    test_checkup_screen()
    test_mail_to_leads_and_coupons()
    test_left_cart_reminder()
    test_pass_quota()
    test_my_locker()
    test_clear_sample_data()
    test_owner_can_hand_out_locker_link()
    test_contact_has_no_phone()
    test_contact_page()
    test_locker_sits_next_to_the_cart()
    test_email_is_not_an_id_and_the_key_can_be_changed()
    test_no_page_promises_pdf_by_email()
    test_file_comes_with_the_order_no_extra_charge()
    test_css_change_reaches_the_visitor()
    test_home_shows_real_pages_not_just_names()
    test_lineup_takes_the_home_middle()
    test_menu_has_no_duplicates()
    test_mobile_quick_bar()
    test_word_pdf_is_actually_read()
    test_passage_memorizing_reads_then_blanks()
    test_admin_puts_a_passage_in_by_pasting()
    test_admin_marks_grammar_only_after_checking()
    test_admin_writes_the_brief_as_a_flow()
    test_sample_wordbooks_are_enough_to_try_it()
    test_study_and_sheet_share_one_wordbook()
    test_word_study_screen()
    test_hidden_really_hides()
    test_policy_tables_stack_on_phone()
    test_nanumsquareround_font_is_served()
    test_file_path_traversal_blocked()
    print("\n판매 사이트 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()

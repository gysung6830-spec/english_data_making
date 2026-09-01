"""판매 사이트(store.py · store_admin.py) 오프라인 테스트.

실행: python -m tests.test_store   (또는 pytest tests/test_store.py)
API 키도, 인터넷도 필요 없습니다. 실제 데이터 대신 임시 폴더를 씁니다.

검증 항목:
  - 고객 페이지가 모두 열리는지 (교재별 페이지·공지·프리패스·시험지 나눔 포함)
  - 주문서 입력값 검증과 금액 계산
  - 교재 요청(지문 없이) / 맞춤 제작 두 경로
  - 시험지 제출 → 관리자 승인 → 쿠폰 발급 → 주문에서 할인 적용까지 한 줄로
  - 관리자 화면에서 상품·교재·분류·공지·설정을 고치면 고객 화면에 반영되는지
  - 백업 내려받기·되돌리기
  - 로그인 잠금과 파일 경로 탈출 차단
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

# 실제 store_data 를 건드리지 않도록, 복사본을 만들어 그쪽을 보게 합니다.
_TMP = Path(tempfile.mkdtemp())
_SRC = Path(__file__).resolve().parent.parent / "store_data"
shutil.copytree(_SRC, _TMP / "store_data", dirs_exist_ok=True)
os.environ["STORE_DB"] = str(_TMP / "store_data" / "store.db")
os.environ.setdefault("ADMIN_PASSWORD", "test1234")

import store_common as sc  # noqa: E402

# 파일을 쓰는 경로는 하나도 빠짐없이 임시 폴더로 돌려 놓아야 합니다.
sc.DATA_DIR = _TMP / "store_data"
sc.SAMPLE_DIR = sc.DATA_DIR / "samples"
sc.SUBMIT_DIR = sc.DATA_DIR / "submissions"
sc.DELIVER_DIR = sc.DATA_DIR / "deliverables"
sc.FREE_DIR = sc.DATA_DIR / "free"
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
        ("/lineup", "오르티카 라인업"),
        ("/samples", "무료 샘플"),
        ("/custom", "교재 요청"),
        ("/submit", "시험지"),
        ("/notice", "자료 업데이트 일정"),
        ("/pass", "프리패스"),
        ("/guide", "환불 규정"),
    ]:
        resp = c.get(path)
        assert resp.status_code == 200, f"{path} 가 열리지 않습니다"
        assert must in body(resp), f"{path} 에 '{must}' 가 없습니다"
    assert c.get("/products/없는상품").status_code == 404
    assert c.get("/books/없는교재").status_code == 404
    print("PASS  고객 페이지 열림")


def test_categories_include_textbook():
    text = body(client().get("/products"))
    for name in ("교과서", "모의고사", "EBS 부교재", "형광펜 독해"):
        assert name in text, name
    print("PASS  분류 4종(교과서 포함) 노출")


def test_lineup_shows_all_materials():
    """보내 주신 라인업 8종이 그룹별로 다 나와야 합니다."""
    text = body(client().get("/lineup"))
    for name in ("지문자료", "지문분석지", "필생보", "필생보 · 독학용", "통합 영어 워크북",
                 "서술형 대비 교재", "17종 변형문제", "동형모의고사 2회"):
        assert name in text, name
    for group in ("지문 이해", "시그니처 자료", "시험 대비"):
        assert group in text, group
    assert "필자의 생각이 보이는 영어독해" in text              # 시그니처 묶음 제목
    assert 'lineup-group dark' in text                          # 그 묶음만 진한 배경
    assert "SIGNATURE" in text and "주문제작자료" in text        # 표시
    assert "읽고 · 뜯어보고" in text                             # 머리말
    # 지문자료의 세 판형
    for v in ("원문만", "위아래 해석", "좌우 해석"):
        assert v in text, v
    print("PASS  오르티카 라인업 8종 · 묶음 · 표시 노출")


def test_home_reflects_lineup():
    text = body(client().get("/"))
    assert "읽고 · 뜯어보고" in text
    assert "17종 변형문제" in text and "/lineup#variants" in text
    assert "3종 세트" not in text     # 옛 문구가 남아 있으면 안 됩니다
    print("PASS  홈이 라인업을 반영")


def test_two_packages_per_book():
    """교재마다 '지문 분석 패키지'와 '문제 패키지' 두 개가 있어야 합니다."""
    def own(html):                      # 짝 패키지 안내 앞부분 = 이 상품의 구성
        return html.split("같은 교재의")[0]

    analysis = body(client().get("/products/mock-2026-06-g3-analysis"))
    assert "지문 분석 패키지" in analysis
    for name in ("지문자료", "지문분석지", "필생보"):
        assert name in own(analysis), name
    for name in ("통합 영어 워크북", "17종 변형문제", "서술형 대비 교재"):
        assert name not in own(analysis), f"분석 패키지에 {name} 이 섞였습니다"

    problem = body(client().get("/products/mock-2026-06-g3-problem"))
    assert "문제 패키지" in problem
    for name in ("통합 영어 워크북", "서술형 대비 교재", "17종 변형문제"):
        assert name in own(problem), name
    for name in ("지문자료", "필생보"):
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


def test_package_filter():
    """패키지로 거르면 목록 카드에 그쪽 갈래만 남아야 합니다."""
    only_analysis = body(client().get("/products?package=analysis"))
    assert "bg-pick pkg-analysis" in only_analysis
    assert "bg-pick pkg-problem" not in only_analysis

    only_problem = body(client().get("/products?package=problem"))
    assert "bg-pick pkg-problem" in only_problem
    assert "bg-pick pkg-analysis" not in only_problem
    print("PASS  목록에서 패키지로 거르기")


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
    """학년 버튼과 정렬 버튼이 실제로 걸러 주고 줄 세워야 합니다."""
    go1 = body(client().get("/products?grade=고1"))
    assert "능률(김성곤) 공통영어 1" in go1          # 고1 교재
    assert "2026 수능특강 영어" not in go1           # 고3 교재는 빠져야 합니다

    import re
    cheap = body(client().get("/products?order=price"))
    # 교재 카드마다 가장 싼 값 = 첫 번째 가격. 그 값이 오름차순이어야 합니다.
    cards = cheap.split('class="book-group"')[1:]
    firsts = [int(re.search(r'<span class="price">([\d,]+)원</span>', c)
                  .group(1).replace(",", "")) for c in cards if "price" in c]
    assert firsts == sorted(firsts), firsts
    print("PASS  학년 거르기 · 가격순 정렬")


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
        return re.findall(r"<h3><a [^>]*>([^<]+)</a></h3>", head)

    hit = names(body(client().get("/products?q=능률")))
    assert hit and all("능률" in n for n in hit), hit

    # 출판사(EBS)로도 찾아집니다
    ebs = names(body(client().get("/products?q=EBS")))
    assert ebs and all(("수능특강" in n or "수능완성" in n) for n in ebs), ebs

    # 없는 것을 치면 교재 요청으로 안내
    miss = body(client().get("/products?q=없는교재이름"))
    assert "찾은 자료가 없습니다" in miss and "교재 요청하기" in miss
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


def test_home_shows_every_category():
    text = body(client().get("/"))
    for slug in ("neungyule-kim", "mock-2026-06-g3", "ebs-2026-tokgang-eng", "highlighter-basic"):
        assert f"/books/{slug}" in text, slug
    print("PASS  홈에 모든 분류의 교재 노출")


def test_pass_twelve_month_price():
    text = body(client().get("/pass"))
    assert "220,000원" in text
    print("PASS  프리패스 12개월 220,000원")


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
    assert "22,000원" in done
    # 디지털 자료라 수량 칸은 없어야 합니다. (하나 사면 반 전체가 씁니다)
    form = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert 'name="quantity"' not in form
    assert "결제하실 금액" in form
    print("PASS  주문 저장 · 금액 표시 · 수량 칸 없음")


def test_order_both_packages_at_once():
    """두 패키지를 사려고 주문을 두 번 하게 만들면 안 됩니다."""
    form = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert "문제 패키지도 함께 받기" in form and "+27,000원" in form

    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "also": "1", "name": "둘다",
        "phone": "010-1212-3434", "email": "both@example.com", "agree": "1"})
    assert resp.status_code == 302
    done = body(c.get(resp.headers["Location"]))
    assert "49,000원" in done          # 22,000 + 27,000
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


# ---- 3. 교재 요청 / 맞춤 제작 ---------------------------------------------
def test_request_needs_no_passage():
    """지문을 하나도 주지 않아도 교재 요청이 접수되어야 합니다."""
    resp = client().post("/custom", data={
        "mode": "request", "wanted": "비상(홍민표) 공통영어1 2과",
        "name": "김선생", "phone": "01098765432", "email": "kim@example.com", "agree": "1"})
    assert resp.status_code == 200
    assert "교재 요청이 접수되었습니다" in body(resp)
    assert "따로 보내실 자료는 없습니다" in body(resp)
    print("PASS  지문 없이 교재 요청 접수")


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


# ---- 4. 시험지 제출 → 쿠폰 → 할인 (한 줄로) -------------------------------
def test_submission_to_coupon_to_discount():
    c = client()
    resp = c.post("/submit", data={
        "school": "대치고등학교", "grade": "고3", "exam_type": "중간고사",
        "exam_term": "2026년 1학기", "scope": "수능특강 1~5강",
        "file": (io.BytesIO(b"%PDF-1.4 fake"), "exam.pdf"),
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
    assert "17,000원" in body(c2.get(resp.headers["Location"]))

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
        "SELECT COUNT(*) FROM downloads").fetchone()[0] == 0, "파일 없이 링크가 나갔습니다"

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
    got = client().get(f"/d/{dl[0]}/{idx}")
    assert got.status_code == 200, got.status_code
    assert got.data.startswith(b"%PDF"), got.data[:20]
    assert sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT download_count FROM downloads WHERE token = ?", (dl[0],)).fetchone()[0] == 1

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
        "email": "academy@example.com", "affiliation": "오르티카학원", "agree": "1",
        "receipt_kind": "tax_invoice", "receipt_no": "123-45-67890"})
    assert resp.status_code == 302
    key = resp.headers["Location"].rsplit("/", 1)[-1]

    a = admin()
    conn = sc.sqlite3.connect(sc.DB_PATH)
    oid = conn.execute("SELECT id FROM orders WHERE view_key = ?", (key,)).fetchone()[0]
    a.post(f"/admin/orders/{oid}", data={"status": "입금확인"})

    page = body(a.get("/admin/sales"))
    assert "123-45-67890" in page and "세금계산서" in page
    assert "27,000원" in page                       # 문제 패키지 결제금액
    assert "24,545원" in page and "2,455원" in page  # 공급가액 · 부가세

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
    assert "오르티카 라인업" not in login       # 고객 메뉴가 딸려 나오지 않아야 함

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
                 "상품에 판매할 파일 올리기", "무료 샘플 올리기"):
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


def test_admin_pages_open():
    a = admin()
    for path, must in [
        ("/admin", "오늘 할 일"),
        ("/admin/orders", "주문 · 문의"),
        ("/admin/submissions", "시험지 제출"),
        ("/admin/coupons", "할인 쿠폰"),
        ("/admin/products", "새 상품 만들기"),
        ("/admin/books", "교재 · 분류"),
        ("/admin/sales", "월별 매출"),
        ("/admin/products/mock-2026-06-g3-analysis/files", "손님에게 보낼 파일"),
        ("/admin/materials", "오르티카 라인업"),
        ("/admin/materials/analysis", "특징 묶음 제목"),
        ("/admin/notices", "새 공지 쓰기"),
        ("/admin/settings", "입금 계좌"),
        ("/admin/backup", "백업 내려받기"),
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

    coupon = body(a.get("/admin/coupons"))
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
    resp = a.post("/admin/materials/passage", data={
        "no": "01", "name": "지문자료", "en": "Passage", "group": "understand",
        "tagline": "테스트로 바꾼 한 줄 소개", "active": "1",
        "variant_name": ["원문만", ""], "variant_desc": ["설명", ""],
        "feature_title": ["새 특징"], "feature_body": ["새 특징 설명"],
        "for_whom": "테스트 대상자"})
    assert resp.status_code == 302
    text = body(client().get("/lineup"))
    assert "테스트로 바꾼 한 줄 소개" in text and "새 특징" in text
    print("PASS  오르티카 라인업 수정 → 고객 화면 반영")


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
        "brand": "Ortica영어", "tagline": "테스트 태그라인",
        "contact_email": "real@ortica.kr", "contact_phone": "010-9999-8888",
        "contact_hours": "평일 10-19", "payment_bank_name": "국민은행",
        "payment_bank_account": "111-222-333444", "payment_bank_holder": "홍길동",
        "payment_notice": "곧 보내 드립니다",
        "business_company": "오르티카", "business_owner": "홍길동",
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


# ---- 7. 글꼴 · 보안 --------------------------------------------------------
def test_mobile_menu_exists():
    """폰에서는 메뉴가 접혀 있어야 첫 화면을 다 먹지 않습니다."""
    home = body(client().get("/"))
    assert 'class="nav-toggle"' in home and 'aria-controls="main-nav"' in home
    assert 'id="main-nav"' in home
    css = body(client().get("/static/store.css"))
    assert ".nav.open{display:flex;}" in css        # 눌렀을 때만 펼쳐짐
    assert ".nav-toggle{display:none;}" in css      # 데스크톱에선 버튼이 안 보임
    print("PASS  폰에서 접히는 메뉴")


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
    assert client().get(f"/order/done/{key[:-1]}x").status_code == 404
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

    rows = body(admin().get("/admin/leads"))
    assert "teacher@school.com" in rows and "고3 3월 학력평가 직독직해" in rows
    print("PASS  직독직해는 이메일 받고 내어 주기")


def test_free_notify_collects_email():
    c = client()
    c.post("/free/notify", data={"email": "alarm@school.com"}, follow_redirects=True)
    assert "alarm@school.com" in body(admin().get("/admin/leads"))
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

    # 종류로 거르기
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


def run_all():
    test_uses_temp_data_only()
    test_public_pages_open()
    test_categories_include_textbook()
    test_lineup_shows_all_materials()
    test_home_reflects_lineup()
    test_two_packages_per_book()
    test_sibling_package_cross_sell()
    test_package_filter()
    test_products_grouped_by_book()
    test_grade_filter_and_sort()
    test_book_page_splits_lanes()
    test_search_finds_by_publisher_and_book()
    test_share_and_branding()
    test_book_page_lists_only_its_products()
    test_home_shows_every_category()
    test_pass_twelve_month_price()
    test_order_rejects_bad_input()
    test_order_saves_and_multiplies_amount()
    test_order_both_packages_at_once()
    test_order_rejects_unknown_coupon()
    test_request_needs_no_passage()
    test_custom_request_accepted()
    test_request_requires_wanted()
    test_submission_to_coupon_to_discount()
    test_submission_requires_file_or_link()
    test_order_to_download_flow()
    test_deliver_by_external_link()
    test_download_revoke_and_limit()
    test_receipt_request_and_sales()
    test_every_admin_route_is_locked()
    test_login_blocks_repeated_guesses()
    test_admin_not_indexed_and_login_is_standalone()
    test_login_next_cannot_leave_admin()
    test_admin_pages_open()
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
    test_sitemap_lists_free_items()
    # 예시 데이터를 지우는 테스트는 다른 테스트가 그 상품을 쓰므로 맨 뒤에 둡니다.
    test_clear_sample_data()
    test_mobile_menu_exists()
    test_nanumsquareround_font_is_served()
    test_file_path_traversal_blocked()
    print("\n판매 사이트 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()

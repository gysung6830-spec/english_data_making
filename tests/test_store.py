"""판매 사이트(store.py · store_admin.py) 오프라인 테스트.

실행: python -m tests.test_store   (또는 pytest tests/test_store.py)
API 키도, 인터넷도 필요 없습니다. 실제 데이터 대신 임시 폴더를 씁니다.

검증 항목:
  - 고객 페이지가 모두 열리는지 (교재별 페이지·공지·프리패스·시험지 나눔 포함)
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
import os
import re
import shutil
import tempfile
from pathlib import Path

# 실제 store_data 를 건드리지 않도록, 복사본을 만들어 그쪽을 보게 합니다.
_TMP = Path(tempfile.mkdtemp())
_SRC = Path(__file__).resolve().parent.parent / "store_data"


def _skip_real_files(folder, names):
    """설정(JSON)만 복사하고, 실제로 파는·나눠 주는 파일은 가져오지 않습니다.

    사장님이 자료를 넣어 두시면 그게 테스트 결과를 바꿔 버립니다.
    파일이 필요한 테스트는 각자 만들어 씁니다.
    """
    here = Path(folder).name
    if here in ("free", "deliverables", "samples", "submissions", ".cache"):
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
        ("/free", "무료 자료"),
        ("/custom", "자료 요청"),
        ("/submit", "시험지"),
        ("/notice", "자료 업데이트 일정"),
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
    assert "22,000원" in done
    # 디지털 자료라 부수 개념이 없습니다. 대신 몇 번째 구매인지로 깎아 줍니다.
    form = body(client().get("/order?slug=mock-2026-06-g3-analysis"))
    assert 'name="quantity"' not in form
    assert "결제하실 금액" in form
    print("PASS  주문 저장 · 금액 표시")


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
    # 22,000 + 27,000 = 49,000 에서 묶음 할인 12% (5,880원) 가 자동으로 빠집니다
    assert "43,120원" in done
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
def test_mobile_quick_bar():
    """폰에서 메뉴를 누르지 않아도 갈 곳이 다 보여야 합니다."""
    home = body(client().get("/"))
    assert 'class="quick-bar"' in home
    # 무료 자료 · 자료 목록 · 분류 4종 · 라인업 · 프리패스 · 공지 · 안내
    track = home.split('class="qb-track"', 1)[1].split("</nav>", 1)[0]
    for word in ("무료 자료", "자료 목록", "교과서", "모의고사", "EBS 부교재",
                 "형광펜 독해", "오르티카 라인업", "프리패스", "공지", "안내"):
        assert word in track, word
    # 지금 보고 있는 자리를 표시해 줍니다
    picked = body(client().get("/products?category=mock"))
    assert 'class="on">모의고사' in picked
    # 햄버거 버튼은 없앴습니다
    assert "nav-toggle" not in home
    css = body(client().get("/static/store.css"))
    assert ".quick-bar{display:none;}" in css       # 넓은 화면에선 띠가 안 보임
    print("PASS  폰에서 카테고리 줄띠")


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
    print("PASS  무료 자료실 검색 · 학년 · 종류 · 시험 거르기")


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


def test_search_result_title_is_editable():
    """검색 결과에 뜰 제목·설명을 관리자 화면에서 정할 수 있어야 합니다."""
    import re
    home = body(client().get("/"))
    title = re.search(r"<title>(.*?)</title>", home, re.S).group(1).strip()
    assert title == "시험에 적합한 고등영어자료 : 오르티카 영어", title
    assert 'property="og:title" content="시험에 적합한' in home   # 카톡 공유도 같은 제목
    import re as _re
    desc = _re.search(r'name="description" content="(.*?)"', home).group(1)
    assert len(desc) <= 90, f"설명이 {len(desc)}자입니다. 검색 결과에서 잘립니다"

    a = admin()
    a.post("/admin/seo", data={"seo_title": "바꾼 제목 : 오르티카 영어",
                               "seo_description": "바꾼 설명입니다.",
                               "naver": "", "google": ""}, follow_redirects=True)
    home = body(client().get("/"))
    assert "<title>바꾼 제목 : 오르티카 영어</title>" in home
    assert 'name="description" content="바꾼 설명입니다."' in home
    # 관리자 화면에 미리보기가 있어야 합니다
    assert "이렇게 뜹니다" in body(a.get("/admin/seo"))
    print("PASS  검색 결과 제목·설명을 화면에서 정하기")


# ---- 올 때마다 바뀌는 자리 -------------------------------------------------
def test_notice_shows_live_now_section():
    """'지금 오르티카'(새 자료 · 다음 시험)는 공지 화면에 둡니다."""
    text = body(client().get("/notice"))
    assert "지금 오르티카" in text
    assert "새로 올라왔습니다" in text and "다음 시험까지" in text
    # 자료 올리는 일정을 약속하지 않기로 했습니다
    assert "이렇게 올립니다" not in text
    # 첫 화면은 가볍게 — 같은 자리를 두 번 두지 않습니다
    home = body(client().get("/"))
    assert "지금 오르티카" not in home
    # 다만 히어로의 D-day 배지는 공지의 시험 일정으로 이어져야 합니다
    assert 'href="/notice#exams"' in home
    print("PASS  공지에 '지금 오르티카' — 새 자료 · 다음 시험 D-day")


def test_home_previews_every_category():
    """분류마다 교재를 몇 권씩 미리 보여 주는 자리는 오르티카 라인업입니다."""
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


def test_book_groups_fold_on_phone():
    """폰에서 자료 목록이 열 화면씩 길어지지 않게, 교재를 한 칸으로 접습니다."""
    text = body(client().get("/products"))
    assert 'class="bg-fold"' in text
    # 접힌 채로도 자료 수와 최저가는 보여야 합니다
    assert "자료 2종 · 22,000원부터" in text
    css = body(client().get("/static/store.css"))
    assert ".bg-fold{display:none;}" in css                 # 넓은 화면에선 안 씀
    assert ".book-group.folded .bg-picks{display:none;}" in css
    # 자바스크립트가 꺼져 있으면 늘 펼쳐진 채여야 합니다 (접는 표시는 스크립트가 답니다)
    assert "book-group folded" not in text
    print("PASS  폰에서 교재 목록 접기")


def test_mobile_filters_collapse():
    """폰에서 거르기 버튼이 접혀 있어야 첫 화면에 자료가 보입니다."""
    for path in ("/products", "/free"):
        text = body(client().get(path))
        assert 'class="filter-toggle"' in text, path
        assert 'class="filter-sets"' in text, path
    # 고른 값이 버튼에 요약돼 보여야 합니다
    picked = body(client().get("/products?grade=고1&order=price"))
    assert "고1 · 가격 낮은 순" in picked
    print("PASS  폰에서 거르기 접기 · 고른 값 요약")


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
    soon = (sc.now_kst() + timedelta(days=12)).date().isoformat()
    data["exams"] = [{"date": soon, "name": "테스트 학력평가", "grades": ["고1"]},
                     {"date": (sc.now_kst() - timedelta(days=3)).date().isoformat(),
                      "name": "이미 지난 시험", "grades": ["고3"]}]
    sc.save_notices(data)

    text = body(client().get("/"))
    assert "D-12" in text and "테스트 학력평가" in text
    assert "이미 지난 시험" not in text          # 지난 시험은 안 나와야 합니다
    print("PASS  다음 시험까지 D-day (지난 시험은 제외)")


def test_admin_edits_exam_schedule():
    a = admin()
    resp = a.post("/admin/notices/exams", data={
        "exam_date": ["2099-05-20", ""], "exam_name": ["아주 먼 학력평가", ""],
        "exam_grades_0": ["고2", "고3"]}, follow_redirects=True)
    assert resp.status_code == 200
    saved = sc.load_notices()["exams"]
    assert saved == [{"date": "2099-05-20", "name": "아주 먼 학력평가",
                      "grades": ["고2", "고3"]}], saved
    assert "아주 먼 학력평가" in body(client().get("/"))
    print("PASS  관리자에서 시험 일정 고치기 → 홈 D-day 반영")


def test_home_updates_skip_pinned_notice():
    """맨 위 띠에 이미 뜬 고정 공지가 '새로 올라왔습니다'에 또 나오면 안 됩니다."""
    text = body(client().get("/notice"))
    assert text.count("Ortica영어 자료 판매를 시작합니다") == 1
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


# ---- 자동 할인 (묶음 · 수량) ----------------------------------------------
def test_bundle_and_loyalty_discounts():
    """함께 담거나, 이 사이트에서 여러 번 사면 값이 내려가야 합니다."""
    site = sc.load_site()
    site["discount"] = {"bundle_enabled": True, "bundle_percent": 12,
                        "loyalty_enabled": True,
                        "loyalty": [{"min": 2, "percent": 5}, {"min": 4, "percent": 10}],
                        "max_percent": 25}
    sc.save_site(site)

    q = client().get("/order/quote?slug=mock-2026-06-g3-analysis&also=1").get_json()
    assert q["subtotal"] == 49000 and q["repeat_no"] == 1
    assert q["rows"][0]["name"] == "두 패키지 함께" and q["rows"][0]["amount"] == 5880
    assert q["final"] == 43120          # 첫 구매라 단골 할인은 없습니다

    # 값을 치른 주문을 세 건 만들어 둡니다 → 이번이 4번째
    email = "regular@example.com"
    with store.app.app_context():
        db = sc.get_db()
        for i in range(3):
            db.execute(
                """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                                       name, phone, email, status, created_at, updated_at)
                   VALUES (?, 'product', '지난 주문', 1, 10000, '단골', '010-0000-0000',
                           ?, '발송완료', ?, ?)""",
                (f"OR-OLD-{i}", email, sc.stamp(), sc.stamp()))
        db.commit()

    q4 = client().get(
        f"/order/quote?slug=mock-2026-06-g3-analysis&email={email}").get_json()
    assert q4["repeat_no"] == 4
    assert q4["rows"][0]["name"] == "4번째 구매 · 단골"
    assert q4["final"] == 22000 - 2200          # 10%

    # 접수된 금액도 같아야 합니다
    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-analysis", "name": "단골",
        "phone": "010-9999-0000", "email": email, "agree": "1"})
    assert resp.status_code == 302
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = ? AND status = '입금대기'",
            (email,)).fetchone()
    assert row["amount"] == 19800
    print("PASS  묶음 할인 · 단골 할인 (몇 번째 구매인지로)")


def test_loyalty_counts_only_paid_orders():
    """주문만 넣고 안 낸 것은 단골 횟수에 안 들어가야 합니다."""
    email = "unpaid@example.com"
    c = client()
    c.post("/order", data={"slug": "mock-2026-06-g3-analysis", "name": "미납",
                           "phone": "010-1111-2222", "email": email, "agree": "1"})
    q = client().get(f"/order/quote?slug=mock-2026-06-g3-analysis&email={email}").get_json()
    assert q["repeat_no"] == 1, "입금 전 주문이 단골 횟수에 들어갔습니다"
    print("PASS  값을 치른 주문만 단골로 셈")


def test_discount_has_a_ceiling():
    """실수로 너무 깎이지 않게 상한이 있어야 합니다."""
    site = sc.load_site()
    site["discount"] = {"bundle_enabled": True, "bundle_percent": 30,
                        "loyalty_enabled": True,
                        "loyalty": [{"min": 2, "percent": 30}],
                        "max_percent": 25}
    sc.save_site(site)
    q = client().get(
        "/order/quote?slug=mock-2026-06-g3-analysis&also=1&email=regular@example.com"
    ).get_json()
    assert q["final"] == q["subtotal"] - q["subtotal"] * 25 // 100
    print("PASS  할인 상한 (겹쳐도 25%까지)")


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
    assert "혼자 공부하는 학생은" in home and "가르치는 선생님은" in home
    # 자세한 두 갈래 안내는 오르티카 라인업에 있습니다
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


def test_admin_pricing_is_editable():
    """지문 1개당 얼마인지를 관리자 화면에서 정하고, 그 값으로 계산해야 합니다."""
    a = admin()
    text = body(a.get("/admin/pricing"))
    assert "우리 정가" in text and "지문 1개당 얼마" in text
    assert "독학하는 학생" in text and "차별화된 자료를 찾는 강사" in text

    a.post("/admin/pricing", data={
        "unit_analysis": "900", "unit_problem": "1100",
        "small_under": "10", "small_multiplier_x10": "15",
        "round_to": "1000", "full_pack_percent": "80"}, follow_redirects=True)
    site = sc.load_site()
    cfg = sc.pricing_cfg(site)
    assert cfg["units"] == {"analysis": 900, "problem": 1100}
    assert sc.suggested_price(site, "analysis", 28) == 25000    # 900x28=25,200 → 천원 단위
    assert sc.suggested_price(site, "problem", 20) == 22000     # 1,100x20
    assert sc.suggested_price(site, "analysis", 5) == 7000      # 적은 묶음 1.5배
    assert sc.suggested_price(site, "없는갈래", 28) == 0

    # 손님 화면에는 단가가 새어 나가면 안 됩니다
    for path in ("/", "/products", "/products/ybm-han-analysis", "/cart"):
        page = body(client().get(path))
        assert "지문 1개당" not in page and "우리 정가" not in page, path

    # 원래대로 돌려 놓습니다
    a.post("/admin/pricing", data={
        "unit_analysis": "800", "unit_problem": "950",
        "small_under": "10", "small_multiplier_x10": "15",
        "round_to": "1000", "full_pack_percent": "85"}, follow_redirects=True)
    print("PASS  우리 정가(지문 1개당)를 화면에서 정하기 · 손님에겐 안 보임")


def _set_discount(bundle=12, loyalty=None, cap=25):
    """할인 설정을 이 테스트가 쓰는 값으로 맞춰 둡니다.
    (다른 테스트가 바꿔 놓았을 수 있어 매번 새로 깝니다)"""
    site = sc.load_site()
    site["discount"] = {"bundle_enabled": True, "bundle_percent": bundle,
                        "loyalty_enabled": bool(loyalty),
                        "loyalty": loyalty or [], "max_percent": cap}
    sc.save_site(site)


# ---- 장바구니 --------------------------------------------------------------
def test_cart_add_view_remove():
    """여러 회차를 담고, 빼고, 비울 수 있어야 합니다."""
    c = client()
    assert "담긴 자료가 없습니다" in body(c.get("/cart"))

    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    page = body(c.get("/cart"))
    assert "능률(김성곤)" in page and "수능특강" in page
    assert "26,000원" in page and "16,000원" in page
    assert "42,000원" in page          # 26,000 + 16,000

    # 같은 것을 또 담아도 한 번만 들어갑니다
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    assert body(c.get("/cart")).count('class="cart-row"') == 2

    c.post("/cart/remove", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    left = body(c.get("/cart"))
    assert left.count('class="cart-row"') == 1 and "수능특강" not in left

    c.post("/cart/clear")
    assert "담긴 자료가 없습니다" in body(c.get("/cart"))
    print("PASS  장바구니 담기 · 빼기 · 비우기")


def test_cart_bundle_discount_only_on_pairs():
    """짝이 맞는 것에만 묶음 할인이 붙어야 합니다."""
    _set_discount(bundle=12)
    c = client()
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    q1 = c.get("/order/quote?cart=1").get_json()
    assert q1["rows"] == [], "짝이 없는데 묶음 할인이 붙었습니다"

    c.post("/cart/add", data={"slug": "neungyule-kim-problem"})
    q2 = c.get("/order/quote?cart=1").get_json()
    assert q2["subtotal"] == 56000
    assert q2["rows"][0]["name"] == "두 패키지 함께" and q2["rows"][0]["amount"] == 6720
    assert q2["final"] == 49280

    # 짝이 아닌 교재를 더 담아도 묶음 할인액은 그대로입니다
    c.post("/cart/add", data={"slug": "ebs-2026-tokgang-eng-analysis"})
    q3 = c.get("/order/quote?cart=1").get_json()
    assert q3["subtotal"] == 72000
    assert q3["rows"][0]["amount"] == 6720
    print("PASS  묶음 할인은 짝이 맞는 값에만")


def test_cart_two_pairs_counted():
    """두 교재를 짝으로 담으면 '2세트' 로 세어야 합니다."""
    _set_discount(bundle=12)
    c = client()
    for slug in ("neungyule-kim-analysis", "neungyule-kim-problem",
                 "ybm-han-analysis", "ybm-han-problem"):
        c.post("/cart/add", data={"slug": slug})
    q = c.get("/order/quote?cart=1").get_json()
    assert "2세트" in q["rows"][0]["name"], q["rows"]
    assert q["subtotal"] == 56000 + 49000
    assert q["rows"][0]["amount"] == (56000 + 49000) * 12 // 100
    print("PASS  짝 두 세트 묶음 할인")


def test_cart_order_end_to_end():
    """장바구니로 주문하면 한 건으로 접수되고, 자료는 전부 나가야 합니다."""
    _set_discount(bundle=12)
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
    assert row["amount"] == 49280
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
    c = client()
    assert 'class="cart-count"' not in body(c.get("/"))
    c.post("/cart/add", data={"slug": "neungyule-kim-analysis"})
    assert '<span class="cart-count">1</span>' in body(c.get("/"))
    print("PASS  머리말에 장바구니 개수")


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
    print("PASS  받은 PDF 에 구매자 표시가 새겨짐")


def test_watermark_can_be_turned_off():
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    site = sc.load_site()
    site["watermark"] = {"enabled": False}
    sc.save_site(site)

    with store.app.app_context():
        dl = sc.get_db().execute(
            """SELECT d.token FROM downloads d JOIN orders o ON o.order_no = d.order_no
               WHERE o.email = 'mark@example.com'""").fetchone()
    got = client().get(f"/d/{dl['token']}/0")
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(got.data)).pages[0].extract_text()
    assert "mark@example.com" not in text
    site["watermark"] = {"enabled": True}
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
    two = body(c.get("/cart"))
    assert "전체를 사시면 더 쌉니다" in two
    assert "4,000원" in two                    # 16,000 x 2 - 28,000
    assert "전강(1~10강)" in two

    c.post("/cart/swap", data={"slug": "ebs-2026-tokgang-eng-all-analysis"})
    after = body(c.get("/cart"))
    assert after.count('class="cart-row"') == 1
    assert "전강(1~10강)" in after and "28,000원" in after
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
    print("PASS  워터마크 문구를 관리자가 정함")


def test_watermark_optout_costs_extra():
    """값을 더 내면 표시 없이 받을 수 있어야 합니다."""
    import store_watermark as wm
    if not wm.AVAILABLE:
        print("SKIP  워터마크 라이브러리 없음")
        return
    site = sc.load_site()
    site["watermark"] = {"enabled": True, "optout_enabled": True, "optout_price": 10000,
                         "footer": "{이메일}", "center": ""}
    sc.save_site(site)

    form = body(client().get("/order?slug=ybm-han-analysis"))
    assert "이름이 안 새겨진 판" in form and "+10,000원" in form
    q = client().get("/order/quote?slug=ybm-han-analysis&nomark=1").get_json()
    assert q["extra"] == 10000 and q["final"] == 32000

    c = client()
    c.post("/order", data={"slug": "ybm-han-analysis", "no_mark": "1", "name": "표시없이",
                           "phone": "010-4444-5555",
                           "email": "clean@example.com", "agree": "1"})
    with store.app.app_context():
        row = sc.get_db().execute(
            "SELECT * FROM orders WHERE email = 'clean@example.com'").fetchone()
    assert row["amount"] == 32000 and row["no_mark"] == 1
    admin().post(f"/admin/orders/{row['id']}/deliver", follow_redirects=True)
    with store.app.app_context():
        dl = sc.get_db().execute(
            "SELECT token FROM downloads WHERE order_no = ?", (row["order_no"],)).fetchone()
    import io as _io
    from pypdf import PdfReader
    text = PdfReader(_io.BytesIO(client().get(f"/d/{dl['token']}/0").data)).pages[0].extract_text()
    assert "clean@example.com" not in text, "값을 더 냈는데 표시가 새겨졌습니다"

    # 꺼 두면 주문서에 칸이 안 보여야 합니다
    site["watermark"]["optout_enabled"] = False
    sc.save_site(site)
    assert "이름이 안 새겨진 판" not in body(client().get("/order?slug=ybm-han-analysis"))
    print("PASS  값을 더 내면 표시 없이 받기")


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
    assert '"analysis": 800' in text.replace(" ", "").replace('"analysis":800', '"analysis": 800')
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
    test_book_groups_fold_on_phone()
    test_mobile_filters_collapse()
    test_long_pages_have_shortcuts()
    test_home_updates_skip_pinned_notice()
    test_home_counts_dday_to_next_exam()
    test_admin_edits_exam_schedule()
    test_two_packages_per_book()
    test_sibling_package_cross_sell()
    test_package_filter()
    test_products_grouped_by_book()
    test_grade_filter_and_sort()
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
    test_bundle_and_loyalty_discounts()
    test_loyalty_counts_only_paid_orders()
    test_discount_has_a_ceiling()
    test_request_needs_no_passage()
    test_custom_request_accepted()
    test_request_requires_wanted()
    test_submission_to_coupon_to_discount()
    test_submission_requires_file_or_link()
    test_cart_add_view_remove()
    test_cart_bundle_discount_only_on_pairs()
    test_cart_two_pairs_counted()
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
    test_watermark_can_be_turned_off()
    test_watermark_wording_is_editable()
    test_watermark_optout_costs_extra()
    test_watermark_skips_non_pdf()
    test_watermark_does_not_bloat_the_file()
    test_download_revoke_and_limit()
    test_receipt_request_and_sales()
    test_every_admin_route_is_locked()
    test_login_blocks_repeated_guesses()
    test_admin_not_indexed_and_login_is_standalone()
    test_login_next_cannot_leave_admin()
    test_admin_pages_open()
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
    test_search_result_title_is_editable()
    test_sitemap_lists_free_items()
    test_lineup_offers_sample_pdf()
    test_free_search_and_filters()
    test_policy_sections_are_filled_in()
    test_request_menu_renamed_to_jaryo()
    # 예시 데이터를 지우는 테스트는 다른 테스트가 그 상품을 쓰므로 맨 뒤에 둡니다.
    test_clear_sample_data()
    test_mobile_quick_bar()
    test_nanumsquareround_font_is_served()
    test_file_path_traversal_blocked()
    print("\n판매 사이트 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()

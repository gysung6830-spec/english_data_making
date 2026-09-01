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

sc.DATA_DIR = _TMP / "store_data"
sc.SAMPLE_DIR = sc.DATA_DIR / "samples"
sc.SUBMIT_DIR = sc.DATA_DIR / "submissions"
sc.DB_PATH = sc.DATA_DIR / "store.db"

import store  # noqa: E402

store.app.config["TESTING"] = True


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
        ("/", "지문 분석지"),
        ("/products", "자료 목록"),
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


def test_book_page_lists_only_its_products():
    text = body(client().get("/books/mock-2026-06-g3"))
    assert "2026학년도 6월 모의평가" in text
    assert "고3 전지문 세트" in text and "빈칸/순서/삽입 10지문" in text
    assert "3월 학력평가 · 고2 전지문" not in text.split("같은 분류의 다른 교재")[0]
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
        "slug": "mock-2026-06-g3-full", "name": "홍길동",
        "phone": "010-1234-5678", "email": "이메일아님"})
    assert resp.status_code == 400
    assert "이메일 주소를 정확히" in body(resp)
    assert "동의해 주셔야" in body(resp)
    print("PASS  잘못된 주문서 반려")


def test_order_saves_and_multiplies_amount():
    c = client()
    resp = c.post("/order", data={
        "slug": "mock-2026-06-g3-full", "quantity": "2", "name": "홍길동",
        "phone": "010-1234-5678", "email": "teacher@example.com", "agree": "1"})
    assert resp.status_code == 302
    done = c.get(resp.headers["Location"])
    assert "44,000원" in body(done)      # 22,000 x 2
    print("PASS  주문 저장 · 금액 계산")


def test_order_rejects_unknown_coupon():
    resp = client().post("/order", data={
        "slug": "mock-2026-06-g3-full", "name": "홍길동", "phone": "010-1234-5678",
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
        "slug": "mock-2026-06-g3-full", "name": "이선생", "phone": "010-3333-4444",
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


# ---- 5. 관리자 잠금 --------------------------------------------------------
def test_admin_requires_login():
    c = client()
    for path in ("/admin", "/admin/products", "/admin/settings", "/admin/backup"):
        assert c.get(path).status_code == 302, path
    assert c.post("/admin/login", data={"password": "틀린비번"}).status_code == 401
    print("PASS  관리자 페이지 잠김")


def test_admin_pages_open():
    a = admin()
    for path, must in [
        ("/admin", "오늘 할 일"),
        ("/admin/orders", "주문 · 문의"),
        ("/admin/submissions", "시험지 제출"),
        ("/admin/coupons", "할인 쿠폰"),
        ("/admin/products", "새 상품 만들기"),
        ("/admin/books", "교재 · 분류"),
        ("/admin/notices", "새 공지 쓰기"),
        ("/admin/settings", "입금 계좌"),
        ("/admin/backup", "백업 내려받기"),
    ]:
        resp = a.get(path)
        assert resp.status_code == 200, f"{path} [{resp.status_code}]"
        assert must in body(resp), f"{path} 에 '{must}' 가 없습니다"
    print("PASS  관리자 화면 전부 열림")


# ---- 6. 관리자에서 고친 내용이 고객 화면에 반영되는지 ----------------------
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


def test_admin_rejects_duplicate_slug():
    resp = admin().post("/admin/products/new", data={
        "slug": "mock-2026-06-g3-full", "name": "중복", "category": "mock", "price": "1000"})
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
def test_nanumsquareround_font_is_served():
    """모든 글자가 나눔스퀘어라운드로 나와야 합니다(외부 CDN 없이 자체 제공)."""
    css = body(client().get("/static/store.css"))
    assert "NanumSquareRound" in css
    assert "cdn.jsdelivr.net" not in css
    for weight in ("R", "B"):
        resp = client().get(f"/static/fonts/NanumSquareRound{weight}.woff")
        assert resp.status_code == 200 and resp.data[:4] == b"wOFF"
    print("PASS  나눔스퀘어라운드 글꼴 제공")


def test_file_path_traversal_blocked():
    assert client().get("/samples/..%2f..%2fstore.py").status_code == 404
    assert admin().get("/admin/submissions/file/..%2f..%2fstore.py").status_code == 404
    print("PASS  폴더 밖 파일 요청 차단")


def run_all():
    test_public_pages_open()
    test_categories_include_textbook()
    test_book_page_lists_only_its_products()
    test_home_shows_every_category()
    test_pass_twelve_month_price()
    test_order_rejects_bad_input()
    test_order_saves_and_multiplies_amount()
    test_order_rejects_unknown_coupon()
    test_request_needs_no_passage()
    test_custom_request_accepted()
    test_request_requires_wanted()
    test_submission_to_coupon_to_discount()
    test_submission_requires_file_or_link()
    test_admin_requires_login()
    test_admin_pages_open()
    test_admin_creates_product_visible_on_site()
    test_admin_rejects_duplicate_slug()
    test_admin_book_and_category_flow()
    test_admin_notice_appears_on_home()
    test_admin_settings_change_reaches_customer()
    test_backup_download_and_restore()
    test_nanumsquareround_font_is_served()
    test_file_path_traversal_blocked()
    print("\n판매 사이트 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()

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

# 파일을 쓰는 경로는 하나도 빠짐없이 임시 폴더로 돌려 놓아야 합니다.
sc.DATA_DIR = _TMP / "store_data"
sc.SAMPLE_DIR = sc.DATA_DIR / "samples"
sc.SUBMIT_DIR = sc.DATA_DIR / "submissions"
sc.DELIVER_DIR = sc.DATA_DIR / "deliverables"
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
        ("/", "지문분석지"),
        ("/products", "자료 목록"),
        ("/lineup", "자료 라인업"),
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
    print("PASS  자료 라인업 8종 · 묶음 · 표시 노출")


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
    only_analysis = body(client().get("/products?package=analysis"))
    assert "지문 분석 패키지" in only_analysis
    assert "문제 패키지" not in only_analysis.split("전체 자료")[-1]

    only_problem = body(client().get("/products?package=problem"))
    assert "문제 패키지" in only_problem
    print("PASS  목록에서 패키지로 거르기")


def test_book_page_splits_lanes():
    text = body(client().get("/books/mock-2026-06-g3"))
    assert "지문 분석 패키지" in text and "문제 패키지" in text
    assert "읽고 뜯어보는 자료" in text          # 갈래 설명
    print("PASS  교재 페이지가 두 갈래로 갈림")


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
        "slug": "mock-2026-06-g3-analysis", "quantity": "2", "name": "홍길동",
        "phone": "010-1234-5678", "email": "teacher@example.com", "agree": "1"})
    assert resp.status_code == 302
    done = c.get(resp.headers["Location"])
    assert "44,000원" in body(done)      # 22,000 x 2
    print("PASS  주문 저장 · 금액 계산")


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
    order_no = resp.headers["Location"].rsplit("/", 1)[-1]
    row = sc.sqlite3.connect(sc.DB_PATH).execute(
        "SELECT id FROM orders WHERE order_no = ?", (order_no,)).fetchone()
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
    order_no = resp.headers["Location"].rsplit("/", 1)[-1]

    a = admin()
    conn = sc.sqlite3.connect(sc.DB_PATH)
    oid = conn.execute("SELECT id FROM orders WHERE order_no = ?", (order_no,)).fetchone()[0]
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
def test_admin_requires_login():
    c = client()
    for path in ("/admin", "/admin/products", "/admin/settings", "/admin/backup",
                 "/admin/sales"):
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
        ("/admin/sales", "월별 매출"),
        ("/admin/products/mock-2026-06-g3-analysis/files", "손님에게 보낼 파일"),
        ("/admin/materials", "자료 라인업"),
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
    print("PASS  자료 라인업 수정 → 고객 화면 반영")


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


def test_uses_temp_data_only():
    """테스트가 진짜 store_data 를 건드리면 안 됩니다."""
    real = Path(__file__).resolve().parent.parent / "store_data"
    for path in (sc.DATA_DIR, sc.SAMPLE_DIR, sc.SUBMIT_DIR, sc.DELIVER_DIR, sc.DB_PATH):
        assert real not in Path(path).resolve().parents and Path(path).resolve() != real, path
    print("PASS  실제 데이터 폴더를 건드리지 않음")


def run_all():
    test_uses_temp_data_only()
    test_public_pages_open()
    test_categories_include_textbook()
    test_lineup_shows_all_materials()
    test_home_reflects_lineup()
    test_two_packages_per_book()
    test_sibling_package_cross_sell()
    test_package_filter()
    test_book_page_splits_lanes()
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
    test_order_to_download_flow()
    test_download_revoke_and_limit()
    test_receipt_request_and_sales()
    test_admin_requires_login()
    test_admin_pages_open()
    test_admin_creates_product_visible_on_site()
    test_admin_edits_material_and_site_reflects()
    test_admin_product_materials_saved()
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

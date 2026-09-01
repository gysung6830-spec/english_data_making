"""판매 사이트(store.py) 오프라인 테스트.

실행: python -m tests.test_store   (또는 pytest tests/test_store.py)
API 키도, 인터넷도 필요 없습니다. 실제 주문 DB 대신 임시 폴더를 씁니다.

검증 항목:
  - 고객 페이지가 모두 열리는지
  - 주문서 입력값 검증(이메일 형식·개인정보 동의)
  - 주문이 DB에 저장되고 금액이 수량만큼 곱해지는지
  - 맞춤 제작 문의 접수
  - 관리자 로그인·상태 변경·CSV 백업
  - 샘플 다운로드 경로 탈출 차단
"""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("ADMIN_PASSWORD", "test1234")
os.environ.setdefault("STORE_DB", os.path.join(tempfile.mkdtemp(), "store.db"))

import store  # noqa: E402  (환경변수를 먼저 정해야 해서 아래에서 import)

store.app.config["TESTING"] = True


def client():
    return store.app.test_client()


def body(resp) -> str:
    return resp.get_data(as_text=True)


# ---- 1. 고객 페이지 --------------------------------------------------------
def test_public_pages_open():
    c = client()
    for path, must in [
        ("/", "지문 분석지"),
        ("/products", "자료 목록"),
        ("/samples", "무료 샘플"),
        ("/custom", "맞춤 제작 문의"),
        ("/guide", "환불 규정"),
    ]:
        resp = c.get(path)
        assert resp.status_code == 200, f"{path} 가 열리지 않습니다"
        assert must in body(resp), f"{path} 에 '{must}' 가 없습니다"
    assert c.get("/products/없는상품").status_code == 404
    print("PASS  고객 페이지 열림")


def test_product_detail_shows_price():
    resp = client().get("/products/neungyule-kim-lesson3")
    assert "18,000원" in body(resp)
    assert "주문서 작성하기" in body(resp)
    print("PASS  상품 상세에 가격·주문 버튼 표시")


# ---- 2. 주문서 검증 --------------------------------------------------------
def test_order_rejects_bad_input():
    resp = client().post("/order", data={
        "slug": "neungyule-kim-lesson3", "name": "홍길동",
        "phone": "010-1234-5678", "email": "이메일아님",
    })
    assert resp.status_code == 400
    assert "이메일 주소를 정확히" in body(resp)
    assert "동의해 주셔야" in body(resp)   # 동의 체크 누락도 함께 걸러짐
    print("PASS  잘못된 주문서 반려")


def test_order_saves_and_multiplies_amount():
    c = client()
    resp = c.post("/order", data={
        "slug": "neungyule-kim-lesson3", "quantity": "2",
        "name": "홍길동", "phone": "010-1234-5678",
        "email": "teacher@example.com", "agree": "1",
    })
    assert resp.status_code == 302
    done = c.get(resp.headers["Location"])
    assert "36,000원" in body(done)      # 18,000 x 2
    assert "입금 계좌" in body(done)
    print("PASS  주문 저장 · 금액 계산")


def test_custom_request_accepted():
    resp = client().post("/custom", data={
        "course": "학원 자체 교재", "passage_count": "20개",
        "materials": ["분석지", "어휘 리스트"],
        "name": "김선생", "phone": "01098765432",
        "email": "kim@example.com", "agree": "1",
    })
    assert "문의가 접수되었습니다" in body(resp)
    print("PASS  맞춤 제작 문의 접수")


# ---- 3. 관리자 -------------------------------------------------------------
def test_admin_requires_login():
    c = client()
    assert c.get("/admin").status_code == 302
    assert c.post("/admin/login", data={"password": "틀린비번"}).status_code == 401
    print("PASS  관리자 페이지 잠김")


def test_admin_can_update_status():
    c = client()
    assert c.post("/admin/login", data={"password": "test1234"}).status_code == 302
    listed = c.get("/admin")
    assert "홍길동" in body(listed) and "입금대기" in body(listed)

    row = store.sqlite3.connect(store.DB_PATH).execute(
        "SELECT id FROM orders ORDER BY id LIMIT 1").fetchone()
    assert c.post(f"/admin/orders/{row[0]}",
                  data={"status": "입금확인", "admin_memo": "확인함"}).status_code == 302
    assert "확인함" in body(c.get("/admin"))
    assert "주문번호" in body(c.get("/admin/orders.csv"))
    print("PASS  관리자 상태 변경 · CSV 백업")


# ---- 4. 보안 ---------------------------------------------------------------
def test_sample_path_traversal_blocked():
    assert client().get("/samples/..%2f..%2fstore.py").status_code == 404
    print("PASS  샘플 폴더 밖 파일 요청 차단")


def run_all():
    test_public_pages_open()
    test_product_detail_shows_price()
    test_order_rejects_bad_input()
    test_order_saves_and_multiplies_amount()
    test_custom_request_accepted()
    test_admin_requires_login()
    test_admin_can_update_status()
    test_sample_path_traversal_blocked()
    print("\n판매 사이트 테스트 통과 ✅")


if __name__ == "__main__":
    run_all()

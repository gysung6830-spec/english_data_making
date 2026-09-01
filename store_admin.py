#!/usr/bin/env python3
"""관리자 화면 — 주문 처리부터 상품 등록까지 전부 여기서 합니다.

코딩을 몰라도 화면에서 클릭·입력만으로 운영할 수 있게 만든 화면입니다.
파일(JSON)을 직접 열 일이 없고, 여기서 저장하면 곧바로 고객 화면에 반영됩니다.

  /admin              오늘 할 일 대시보드
  /admin/orders       주문 · 문의 관리
  /admin/submissions  시험지 제출 검토 → 쿠폰 발급
  /admin/coupons      할인 쿠폰 발급 · 현황
  /admin/products     상품 등록 · 수정
  /admin/books        교재 · 분류 등록
  /admin/notices      공지 작성
  /admin/settings     가게 정보 · 계좌 · 프리패스 가격
  /admin/backup       백업 내려받기 · 되돌리기
"""
from __future__ import annotations

import io
import csv
import json
import os
import secrets
from datetime import timedelta

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)

import store_common as sc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 관리자 페이지 비밀번호 (환경변수). 없으면 관리자 페이지가 통째로 잠깁니다.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

MANAGED_FILES = ["site.json", "products.json", "notices.json", "materials.json"]


# ---------------------------------------------------------------------------
# 로그인
# ---------------------------------------------------------------------------
def logged_in() -> bool:
    return bool(session.get("admin"))


@admin_bp.before_request
def guard():
    """로그인 화면 말고는 전부 잠급니다."""
    if request.endpoint in ("admin.login", "admin.logout"):
        return None
    if not logged_in():
        return redirect(url_for("admin.login", next=request.path))
    return None


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD:
        return render_template("admin/login.html", locked=True, error=None)
    if request.method == "POST":
        # 한글 비밀번호나 한글 입력이 들어와도 터지지 않도록 바이트로 비교합니다.
        typed = request.form.get("password", "").encode("utf-8")
        if secrets.compare_digest(typed, ADMIN_PASSWORD.encode("utf-8")):
            session["admin"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        return render_template("admin/login.html", locked=False,
                               error="비밀번호가 맞지 않습니다."), 401
    return render_template("admin/login.html", locked=False, error=None)


@admin_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# 대시보드 — 오늘 할 일
# ---------------------------------------------------------------------------
# strict_slashes=False 를 빼면 /admin 이 /admin/ 로 한 번 더 튕깁니다.
@admin_bp.route("/", strict_slashes=False)
def dashboard():
    db = sc.get_db()
    one = lambda sql, args=(): db.execute(sql, args).fetchone()[0]  # noqa: E731

    todo = {
        "입금확인": one("SELECT COUNT(*) FROM orders WHERE kind='product' AND status='입금대기'"),
        "발송": one("SELECT COUNT(*) FROM orders WHERE kind='product' AND status='입금확인'"),
        "문의답변": one("SELECT COUNT(*) FROM orders WHERE kind IN ('request','custom','pass')"
                    " AND status='입금대기'"),
        "시험지검토": one("SELECT COUNT(*) FROM submissions WHERE status='검토대기'"),
    }
    money = {
        "대기": one("SELECT COALESCE(SUM(amount),0) FROM orders WHERE status='입금대기'"),
        "확인": one("SELECT COALESCE(SUM(amount),0) FROM orders"
                  " WHERE status IN ('입금확인','발송완료')"),
    }
    catalog = sc.load_raw_catalog()
    counts = {
        "상품": len([p for p in catalog["products"] if p.get("active", True)]),
        "교재": len([b for b in catalog["books"] if b.get("active", True)]),
        "공지": len(sc.load_notices()["notices"]),
        "자료": len(sc.material_map()),
        "쿠폰": one("SELECT COUNT(*) FROM coupons WHERE used_at IS NULL"),
    }
    recent = db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 6").fetchall()
    subs = db.execute("SELECT * FROM submissions WHERE status='검토대기'"
                      " ORDER BY id DESC LIMIT 5").fetchall()
    warnings = check_setup(sc.load_site(), catalog)
    return render_template("admin/dashboard.html", todo=todo, money=money, counts=counts,
                           recent=recent, subs=subs, warnings=warnings)


def check_setup(site: dict, catalog: dict) -> list[dict]:
    """문 열기 전에 빠뜨리기 쉬운 것을 잡아 줍니다."""
    out = []
    contact = site.get("contact", {})
    payment = site.get("payment", {})
    if "example" in contact.get("email", "") or "여기에" in contact.get("email", ""):
        out.append({"text": "문의 이메일이 아직 예시값입니다.",
                    "url": url_for("admin.settings"), "label": "가게 정보에서 고치기"})
    if "0000" in payment.get("bank_account", ""):
        out.append({"text": "입금 계좌가 아직 예시값입니다. 이대로면 돈을 못 받습니다.",
                    "url": url_for("admin.settings"), "label": "계좌 입력하기"})
    if "0000" in site.get("business", {}).get("reg_no", ""):
        out.append({"text": "사업자 정보가 예시값입니다. 온라인 판매는 표기 의무가 있습니다.",
                    "url": url_for("admin.settings"), "label": "사업자 정보 입력"})
    ready = [p for p in catalog["products"]
             if p.get("sample_file") and (sc.SAMPLE_DIR / p["sample_file"]).exists()]
    if not ready:
        out.append({"text": "무료 샘플 PDF가 하나도 없습니다. 샘플이 있어야 잘 팔립니다.",
                    "url": url_for("admin.products"), "label": "상품 목록 보기"})
    return out


# ---------------------------------------------------------------------------
# 주문 · 문의
# ---------------------------------------------------------------------------
@admin_bp.route("/orders")
def orders():
    db = sc.get_db()
    status = request.args.get("status", "")
    kind = request.args.get("kind", "")
    q = sc.clean(request.args.get("q"), 60)

    sql = "SELECT * FROM orders WHERE 1=1"
    params: list = []
    if status in sc.ORDER_STATUSES:
        sql += " AND status = ?"
        params.append(status)
    if kind in sc.ORDER_KIND_LABELS:
        sql += " AND kind = ?"
        params.append(kind)
    if q:
        sql += " AND (order_no LIKE ? OR name LIKE ? OR email LIKE ? OR phone LIKE ?"
        sql += " OR product_name LIKE ?)"
        params += [f"%{q}%"] * 5
    sql += " ORDER BY id DESC LIMIT 300"
    rows = db.execute(sql, params).fetchall()

    counts = {s: 0 for s in sc.ORDER_STATUSES}
    for row in db.execute("SELECT status, COUNT(*) c FROM orders GROUP BY status"):
        counts[row["status"]] = row["c"]
    return render_template("admin/orders.html", rows=rows, statuses=sc.ORDER_STATUSES,
                           kinds=sc.ORDER_KIND_LABELS, selected=status,
                           selected_kind=kind, q=q, counts=counts)


@admin_bp.route("/orders/<int:order_id>", methods=["POST"])
def order_update(order_id):
    status = request.form.get("status", "")
    if status not in sc.ORDER_STATUSES:
        abort(400)
    db = sc.get_db()
    db.execute("UPDATE orders SET status = ?, admin_memo = ?, updated_at = ? WHERE id = ?",
               (status, sc.clean(request.form.get("admin_memo"), 500), sc.stamp(), order_id))
    db.commit()
    flash(f"주문 상태를 '{status}' 로 바꿨습니다.", "ok")
    return redirect(request.referrer or url_for("admin.orders"))


@admin_bp.route("/orders.csv")
def orders_csv():
    """주문 내역 백업용 CSV. 무료 서버는 디스크가 초기화될 수 있으니 가끔 받아 두세요."""
    rows = sc.get_db().execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["주문번호", "종류", "상품", "수량", "결제금액", "할인", "쿠폰", "성함",
                     "연락처", "이메일", "소속", "입금자명", "요청사항", "상세", "상태",
                     "메모", "접수시각"])
    for r in rows:
        writer.writerow([r["order_no"], sc.ORDER_KIND_LABELS.get(r["kind"], r["kind"]),
                         r["product_name"], r["quantity"], r["amount"], r["discount"],
                         r["coupon_code"], r["name"], r["phone"], r["email"],
                         r["affiliation"], r["depositor"], r["message"], r["detail_json"],
                         r["status"], r["admin_memo"], r["created_at"]])
    body = ("﻿" + buf.getvalue()).encode("utf-8")  # 엑셀 한글 깨짐 방지
    return body, 200, {"Content-Type": "text/csv; charset=utf-8",
                       "Content-Disposition":
                       f'attachment; filename="ortica-orders-{sc.now_kst():%Y%m%d}.csv"'}


# ---------------------------------------------------------------------------
# 시험지 제출 → 쿠폰 발급
# ---------------------------------------------------------------------------
@admin_bp.route("/submissions")
def submissions():
    status = request.args.get("status", "")
    sql = "SELECT * FROM submissions"
    params: list = []
    if status in sc.SUBMIT_STATUSES:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT 300"
    rows = sc.get_db().execute(sql, params).fetchall()
    counts = {s: 0 for s in sc.SUBMIT_STATUSES}
    for row in sc.get_db().execute("SELECT status, COUNT(*) c FROM submissions GROUP BY status"):
        counts[row["status"]] = row["c"]
    reward = sc.load_site().get("submit_reward", {})
    return render_template("admin/submissions.html", rows=rows, statuses=sc.SUBMIT_STATUSES,
                           selected=status, counts=counts, reward=reward)


@admin_bp.route("/submissions/<int:sub_id>", methods=["POST"])
def submission_update(sub_id):
    """'승인' 을 누르면 쿠폰을 자동으로 만들어 제출자에게 메일로 보냅니다."""
    db = sc.get_db()
    row = db.execute("SELECT * FROM submissions WHERE id = ?", (sub_id,)).fetchone()
    if not row:
        abort(404)
    status = request.form.get("status", "")
    if status not in sc.SUBMIT_STATUSES:
        abort(400)
    memo = sc.clean(request.form.get("admin_memo"), 500)

    code = row["coupon_code"]
    if status == "승인" and not code:
        reward = sc.load_site().get("submit_reward", {})
        kind = reward.get("coupon_kind", "amount")
        value = int(reward.get("coupon_value", 5000))
        code = sc.issue_coupon(kind, value,
                               min_amount=int(reward.get("min_amount", 0)),
                               note=f"시험지 제출 보상 · {row['submit_no']} · {row['school']}",
                               issued_to=row["email"],
                               days_valid=int(reward.get("days_valid", 90)))
        sc.send_mail(
            "[Ortica영어] 시험지 감사합니다 — 할인 쿠폰을 보내 드립니다",
            "\n".join([f"{row['name']}님, {row['school']} 시험지 잘 받았습니다. 감사합니다.",
                       "",
                       f"할인 쿠폰 코드 : {code}",
                       coupon_desc(kind, value, int(reward.get('min_amount', 0))),
                       f"사용 기한 : {(sc.now_kst() + timedelta(days=int(reward.get('days_valid', 90)))).date()}",
                       "",
                       "주문서 아래쪽 '할인 쿠폰 코드' 칸에 넣으시면 바로 적용됩니다.",
                       "보내 주신 시험지는 동형 모의고사 제작 참고용으로만 쓰며, 원본은 재배포하지 않습니다."]),
            to_addr=row["email"])
        flash(f"쿠폰 {code} 을(를) 발급하고 {row['email']} 로 보냈습니다.", "ok")
    else:
        flash(f"상태를 '{status}' 로 바꿨습니다.", "ok")

    db.execute("""UPDATE submissions SET status=?, admin_memo=?, coupon_code=?, updated_at=?
                  WHERE id=?""", (status, memo, code, sc.stamp(), sub_id))
    db.commit()
    return redirect(request.referrer or url_for("admin.submissions"))


@admin_bp.route("/submissions/file/<path:filename>")
def submission_file(filename):
    target = (sc.SUBMIT_DIR / filename).resolve()
    if sc.SUBMIT_DIR.resolve() not in target.parents or not target.is_file():
        abort(404)
    return send_from_directory(sc.SUBMIT_DIR, filename, as_attachment=True)


def coupon_desc(kind: str, value: int, min_amount: int = 0) -> str:
    head = f"{value}% 할인" if kind == "percent" else f"{value:,}원 할인"
    return head + (f" ({min_amount:,}원 이상 주문 시)" if min_amount else "")


# ---------------------------------------------------------------------------
# 쿠폰
# ---------------------------------------------------------------------------
@admin_bp.route("/coupons", methods=["GET", "POST"])
def coupons():
    db = sc.get_db()
    if request.method == "POST":
        kind = "percent" if request.form.get("kind") == "percent" else "amount"
        value = sc.to_int(request.form.get("value"), 0)
        if value <= 0:
            flash("할인 값을 1 이상으로 넣어 주세요.", "err")
        else:
            code = sc.issue_coupon(kind, value,
                                   min_amount=sc.to_int(request.form.get("min_amount"), 0),
                                   note=sc.clean(request.form.get("note"), 200),
                                   issued_to=sc.clean(request.form.get("issued_to"), 120),
                                   days_valid=sc.to_int(request.form.get("days_valid"), 90))
            flash(f"쿠폰 {code} 을(를) 만들었습니다. 손님에게 이 코드를 알려 주세요.", "ok")
        return redirect(url_for("admin.coupons"))

    rows = db.execute("SELECT * FROM coupons ORDER BY id DESC LIMIT 300").fetchall()
    return render_template("admin/coupons.html", rows=rows, today=sc.now_kst().date().isoformat())


@admin_bp.route("/coupons/<int:coupon_id>/delete", methods=["POST"])
def coupon_delete(coupon_id):
    db = sc.get_db()
    db.execute("DELETE FROM coupons WHERE id = ? AND used_at IS NULL", (coupon_id,))
    db.commit()
    flash("쿠폰을 지웠습니다. (이미 쓴 쿠폰은 기록으로 남깁니다)", "ok")
    return redirect(url_for("admin.coupons"))


# ---------------------------------------------------------------------------
# 상품
# ---------------------------------------------------------------------------
LIST_FIELDS = ["includes", "highlights"]


def parse_lines(value: str) -> list[str]:
    """줄바꿈으로 나눠 목록으로 만듭니다. 빈 줄은 버립니다."""
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def product_from_form(form, existing: dict | None = None) -> tuple[dict, list[str]]:
    item = dict(existing or {})
    errors = []
    slug = sc.clean(form.get("slug"), 60).lower()
    if not sc.SLUG_RE.match(slug):
        errors.append("주소 이름(slug)은 영문 소문자·숫자·하이픈으로 3자 이상 적어 주세요. 예: mock-2026-09")
    item["slug"] = slug
    item["name"] = sc.clean(form.get("name"), 120)
    if not item["name"]:
        errors.append("상품 이름을 적어 주세요.")
    item["category"] = sc.clean(form.get("category"), 40)
    item["book"] = sc.clean(form.get("book"), 60)
    pkg = sc.clean(form.get("package"), 40)
    item["package"] = pkg if pkg in sc.package_map() else ""
    item["subtitle"] = sc.clean(form.get("subtitle"), 120)
    item["price"] = sc.to_int(form.get("price"), 0)
    if item["price"] < 0:
        errors.append("가격은 0 이상이어야 합니다.")
    list_price = sc.to_int(form.get("list_price"), 0)
    if list_price:
        item["list_price"] = list_price
    else:
        item.pop("list_price", None)
    item["passages"] = sc.to_int(form.get("passages"), 0)
    item["grade"] = sc.clean(form.get("grade"), 30)
    item["badge"] = sc.clean(form.get("badge"), 20)
    item["sort"] = sc.to_int(form.get("sort"), 100)
    item["active"] = bool(form.get("active"))
    item["description"] = sc.clean(form.get("description"), 2000)
    # 라인업 8종 중 이 상품에 들어가는 자료 (체크박스)
    known = set(sc.material_map())
    item["materials"] = [m for m in form.getlist("materials") if m in known]
    item["includes"] = parse_lines(form.get("includes"))
    item["highlights"] = parse_lines(form.get("highlights"))
    item["delivery"] = sc.clean(form.get("delivery"), 200)
    item["format"] = sc.clean(form.get("format"), 100)
    item["sample_file"] = sc.clean(form.get("sample_file"), 120)
    return item, errors


@admin_bp.route("/products")
def products():
    catalog = sc.load_raw_catalog()
    items = sorted(catalog["products"], key=lambda p: (p.get("sort", 100), p.get("name", "")))
    # 샘플 파일이 실제로 폴더에 있는지 미리 확인해 화면에 표시해 줍니다.
    ready = {p["sample_file"] for p in items
             if p.get("sample_file") and (sc.SAMPLE_DIR / p["sample_file"]).exists()}
    return render_template("admin/products.html", items=items, catalog=catalog,
                           sample_ready=ready)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_bp.route("/products/<slug>/edit", methods=["GET", "POST"])
def product_form(slug=None):
    catalog = sc.load_raw_catalog()
    existing = next((p for p in catalog["products"] if p.get("slug") == slug), None)
    if slug and existing is None:
        abort(404)

    if request.method == "GET":
        packages = list(sc.package_map().values())
        first = packages[0] if packages else {}
        blank = {"active": True, "sort": 100, "includes": [],
                 "package": first.get("id", ""),
                 "materials": list(first.get("materials", [])),
                 "delivery": "입금 확인 후 영업일 기준 24시간 이내 이메일 발송",
                 "format": "PDF (A4, 인쇄용)"}
        return render_template("admin/product_form.html", p=existing or blank,
                               catalog=catalog, errors=[], is_new=existing is None,
                               all_materials=list(sc.material_map().values()),
                               packages=list(sc.package_map().values()))

    item, errors = product_from_form(request.form, existing)
    clash = [p for p in catalog["products"]
             if p.get("slug") == item["slug"] and p is not existing]
    if clash:
        errors.append(f"주소 이름 '{item['slug']}' 은 이미 다른 상품이 쓰고 있습니다.")
    if errors:
        return render_template("admin/product_form.html", p=item, catalog=catalog,
                               errors=errors, is_new=existing is None,
                               all_materials=list(sc.material_map().values()),
                               packages=list(sc.package_map().values())), 400

    if existing is None:
        catalog["products"].append(item)
        flash(f"상품 '{item['name']}' 을(를) 새로 만들었습니다.", "ok")
    else:
        catalog["products"] = [item if p is existing else p for p in catalog["products"]]
        flash(f"상품 '{item['name']}' 을(를) 저장했습니다.", "ok")
    sc.save_catalog(catalog)
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<slug>/toggle", methods=["POST"])
def product_toggle(slug):
    catalog = sc.load_raw_catalog()
    for p in catalog["products"]:
        if p.get("slug") == slug:
            p["active"] = not p.get("active", True)
            sc.save_catalog(catalog)
            flash(f"'{p['name']}' 을(를) {'다시 노출' if p['active'] else '숨김'} 했습니다.", "ok")
            break
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<slug>/delete", methods=["POST"])
def product_delete(slug):
    catalog = sc.load_raw_catalog()
    before = len(catalog["products"])
    catalog["products"] = [p for p in catalog["products"] if p.get("slug") != slug]
    if len(catalog["products"]) < before:
        sc.save_catalog(catalog)
        flash("상품을 지웠습니다.", "ok")
    return redirect(url_for("admin.products"))


# ---------------------------------------------------------------------------
# 교재 · 분류
# ---------------------------------------------------------------------------
@admin_bp.route("/books")
def books():
    catalog = sc.load_raw_catalog()
    counts = {}
    for p in catalog["products"]:
        if p.get("book"):
            counts[p["book"]] = counts.get(p["book"], 0) + 1
    items = sorted(catalog["books"], key=lambda b: (b.get("sort", 100), b.get("name", "")))
    return render_template("admin/books.html", items=items, catalog=catalog, counts=counts)


@admin_bp.route("/books/new", methods=["GET", "POST"])
@admin_bp.route("/books/<slug>/edit", methods=["GET", "POST"])
def book_form(slug=None):
    catalog = sc.load_raw_catalog()
    existing = next((b for b in catalog["books"] if b.get("slug") == slug), None)
    if slug and existing is None:
        abort(404)

    if request.method == "GET":
        return render_template("admin/book_form.html", b=existing or {"active": True, "sort": 100},
                               catalog=catalog, errors=[], is_new=existing is None)

    item = dict(existing or {})
    errors = []
    item["slug"] = sc.clean(request.form.get("slug"), 60).lower()
    if not sc.SLUG_RE.match(item["slug"]):
        errors.append("주소 이름(slug)은 영문 소문자·숫자·하이픈으로 3자 이상 적어 주세요.")
    item["name"] = sc.clean(request.form.get("name"), 120)
    if not item["name"]:
        errors.append("교재 이름을 적어 주세요.")
    item["category"] = sc.clean(request.form.get("category"), 40)
    if not item["category"]:
        errors.append("분류를 골라 주세요.")
    item["publisher"] = sc.clean(request.form.get("publisher"), 60)
    item["author"] = sc.clean(request.form.get("author"), 60)
    item["grade"] = sc.clean(request.form.get("grade"), 30)
    item["sort"] = sc.to_int(request.form.get("sort"), 100)
    item["active"] = bool(request.form.get("active"))
    item["description"] = sc.clean(request.form.get("description"), 1000)

    if [b for b in catalog["books"] if b.get("slug") == item["slug"] and b is not existing]:
        errors.append(f"주소 이름 '{item['slug']}' 은 이미 다른 교재가 쓰고 있습니다.")
    if errors:
        return render_template("admin/book_form.html", b=item, catalog=catalog,
                               errors=errors, is_new=existing is None), 400

    if existing is None:
        catalog["books"].append(item)
        flash(f"교재 '{item['name']}' 을(를) 만들었습니다. 이제 여기에 상품을 넣어 주세요.", "ok")
    else:
        catalog["books"] = [item if b is existing else b for b in catalog["books"]]
        flash(f"교재 '{item['name']}' 을(를) 저장했습니다.", "ok")
    sc.save_catalog(catalog)
    return redirect(url_for("admin.books"))


@admin_bp.route("/books/<slug>/delete", methods=["POST"])
def book_delete(slug):
    catalog = sc.load_raw_catalog()
    using = [p["name"] for p in catalog["products"] if p.get("book") == slug]
    if using:
        flash(f"이 교재를 쓰는 상품이 {len(using)}개 있어 지울 수 없습니다. "
              f"먼저 상품의 교재를 바꾸거나 지워 주세요.", "err")
        return redirect(url_for("admin.books"))
    catalog["books"] = [b for b in catalog["books"] if b.get("slug") != slug]
    sc.save_catalog(catalog)
    flash("교재를 지웠습니다.", "ok")
    return redirect(url_for("admin.books"))


@admin_bp.route("/categories", methods=["POST"])
def category_save():
    """분류 추가 · 이름 변경 · 삭제를 한 번에 처리합니다."""
    catalog = sc.load_raw_catalog()
    action = request.form.get("action")

    if action == "add":
        cid = sc.clean(request.form.get("id"), 40).lower()
        name = sc.clean(request.form.get("name"), 40)
        if not sc.SLUG_RE.match(cid) or not name:
            flash("분류 아이디(영문)와 이름을 모두 제대로 적어 주세요.", "err")
        elif any(c.get("id") == cid for c in catalog["categories"]):
            flash(f"'{cid}' 분류는 이미 있습니다.", "err")
        else:
            catalog["categories"].append({"id": cid, "name": name})
            sc.save_catalog(catalog)
            flash(f"분류 '{name}' 을(를) 추가했습니다.", "ok")

    elif action == "rename":
        cid = request.form.get("id", "")
        name = sc.clean(request.form.get("name"), 40)
        for c in catalog["categories"]:
            if c.get("id") == cid and name:
                c["name"] = name
                sc.save_catalog(catalog)
                flash(f"분류 이름을 '{name}' 으로 바꿨습니다.", "ok")
                break

    elif action == "delete":
        cid = request.form.get("id", "")
        used = [b["name"] for b in catalog["books"] if b.get("category") == cid]
        used += [p["name"] for p in catalog["products"] if p.get("category") == cid]
        if used:
            flash(f"이 분류를 쓰는 항목이 {len(used)}개 있어 지울 수 없습니다.", "err")
        else:
            catalog["categories"] = [c for c in catalog["categories"] if c.get("id") != cid]
            sc.save_catalog(catalog)
            flash("분류를 지웠습니다.", "ok")

    return redirect(url_for("admin.books"))


# ---------------------------------------------------------------------------
# 자료 라인업
# ---------------------------------------------------------------------------
def parse_pairs(titles, bodies) -> list[dict]:
    """'제목 / 설명' 두 줄짜리 항목들을 모읍니다. 제목이 비면 그 줄은 버립니다."""
    out = []
    for title, body in zip(titles, bodies):
        title = sc.clean(title, 120)
        if title:
            out.append({"title": title, "body": sc.clean(body, 1200)})
    return out


@admin_bp.route("/materials")
def materials():
    data = sc.load_materials()
    used = {}
    for product in sc.load_raw_catalog()["products"]:
        for mid in product.get("materials", []):
            used[mid] = used.get(mid, 0) + 1
    return render_template("admin/materials.html", data=data, used=used,
                           packages=sc.load_raw_catalog()["packages"])


@admin_bp.route("/materials/intro", methods=["POST"])
def materials_intro():
    data = sc.load_materials()
    f = request.form
    data["intro"] = {
        "eyebrow": sc.clean(f.get("eyebrow"), 40),
        "headline": sc.clean(f.get("headline"), 200),
        "lead": sc.clean(f.get("lead"), 600),
        "signature_note": sc.clean(f.get("signature_note"), 200),
    }
    groups = []
    for gid, rng, name, theme, headline, lead in zip(
            f.getlist("group_id"), f.getlist("group_range"), f.getlist("group_name"),
            f.getlist("group_theme"), f.getlist("group_headline"), f.getlist("group_lead")):
        gid = sc.clean(gid, 40)
        if gid:
            group = {"id": gid, "range": sc.clean(rng, 20), "name": sc.clean(name, 40),
                     "headline": sc.clean(headline, 150), "lead": sc.clean(lead, 600)}
            if theme == "dark":
                group["theme"] = "dark"
            groups.append(group)
    if groups:
        data["groups"] = groups
    sc.save_materials(data)
    flash("라인업 소개와 묶음을 저장했습니다.", "ok")
    return redirect(url_for("admin.materials"))


@admin_bp.route("/materials/packages", methods=["POST"])
def packages_save():
    """판매 단위 두 갈래(지문 분석 패키지 / 문제 패키지)를 고칩니다."""
    catalog = sc.load_raw_catalog()
    known = set(sc.material_map())
    packages = []
    for i, (pid, name, short, tagline, desc) in enumerate(zip(
            request.form.getlist("pkg_id"), request.form.getlist("pkg_name"),
            request.form.getlist("pkg_short"), request.form.getlist("pkg_tagline"),
            request.form.getlist("pkg_desc"))):
        pid = sc.clean(pid, 40)
        if not pid:
            continue
        chosen = [m for m in request.form.getlist(f"pkg_materials_{pid}") if m in known]
        packages.append({"id": pid, "name": sc.clean(name, 40), "short": sc.clean(short, 10),
                         "tagline": sc.clean(tagline, 120), "desc": sc.clean(desc, 600),
                         "materials": chosen, "sort": (i + 1) * 10})
    if packages:
        catalog["packages"] = packages
        sc.save_catalog(catalog)
        flash("패키지 구성을 저장했습니다. 새로 만드는 상품에 이 자료가 기본으로 들어갑니다.", "ok")
    return redirect(url_for("admin.materials"))


@admin_bp.route("/materials/<mid>", methods=["GET", "POST"])
def material_form(mid):
    data = sc.load_materials()
    item = next((m for m in data["materials"] if m.get("id") == mid), None)
    if item is None:
        abort(404)

    if request.method == "GET":
        return render_template("admin/material_form.html", m=item, groups=data["groups"])

    f = request.form
    item["no"] = sc.clean(f.get("no"), 6)
    item["name"] = sc.clean(f.get("name"), 60) or item["name"]
    item["en"] = sc.clean(f.get("en"), 60)
    item["group"] = sc.clean(f.get("group"), 40)
    item["tagline"] = sc.clean(f.get("tagline"), 200)
    item["subline"] = sc.clean(f.get("subline"), 600)
    item["sheet_note"] = sc.clean(f.get("sheet_note"), 800)
    item["features_headline"] = sc.clean(f.get("features_headline"), 120)
    item["image"] = sc.clean(f.get("image"), 120)
    item["signature"] = bool(f.get("signature"))
    item["made_to_order"] = bool(f.get("made_to_order"))
    item["active"] = bool(f.get("active"))
    item["variants"] = [{"name": v["title"], "desc": v["body"]}
                        for v in parse_pairs(f.getlist("variant_name"),
                                             f.getlist("variant_desc"))]
    item["features"] = parse_pairs(f.getlist("feature_title"), f.getlist("feature_body"))
    item["for_whom"] = parse_lines(f.get("for_whom"))

    data["materials"] = [item if m.get("id") == mid else m for m in data["materials"]]
    sc.save_materials(data)
    flash(f"'{item['name']}' 을(를) 저장했습니다. 라인업 페이지에 바로 반영됐습니다.", "ok")
    return redirect(url_for("admin.materials"))


# ---------------------------------------------------------------------------
# 공지
# ---------------------------------------------------------------------------
@admin_bp.route("/notices")
def notices():
    return render_template("admin/notices.html", **sc.load_notices())


@admin_bp.route("/notices/save", methods=["POST"])
def notice_save():
    data = sc.load_notices()
    idx = request.form.get("index", "")
    item = {
        "date": sc.clean(request.form.get("date"), 20) or sc.now_kst().date().isoformat(),
        "tag": sc.clean(request.form.get("tag"), 20),
        "title": sc.clean(request.form.get("title"), 150),
        "body": sc.clean(request.form.get("body"), 3000),
        "pinned": bool(request.form.get("pinned")),
    }
    if not item["title"]:
        flash("공지 제목을 적어 주세요.", "err")
        return redirect(url_for("admin.notices"))

    if idx.isdigit() and int(idx) < len(data["notices"]):
        data["notices"][int(idx)] = item
        flash("공지를 고쳤습니다.", "ok")
    else:
        data["notices"].insert(0, item)
        flash("공지를 올렸습니다. 홈 맨 위에도 보입니다.", "ok")
    sc.save_notices(data)
    return redirect(url_for("admin.notices"))


@admin_bp.route("/notices/<int:index>/delete", methods=["POST"])
def notice_delete(index):
    data = sc.load_notices()
    if index < len(data["notices"]):
        data["notices"].pop(index)
        sc.save_notices(data)
        flash("공지를 지웠습니다.", "ok")
    return redirect(url_for("admin.notices"))


@admin_bp.route("/notices/schedule", methods=["POST"])
def schedule_save():
    whens = request.form.getlist("when")
    whats = request.form.getlist("what")
    data = sc.load_notices()
    data["schedule"] = [{"when": sc.clean(w, 40), "what": sc.clean(t, 200)}
                        for w, t in zip(whens, whats) if sc.clean(w, 40) and sc.clean(t, 200)]
    sc.save_notices(data)
    flash("업데이트 일정을 저장했습니다.", "ok")
    return redirect(url_for("admin.notices"))


# ---------------------------------------------------------------------------
# 가게 정보
# ---------------------------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    site = sc.load_site()
    if request.method == "GET":
        return render_template("admin/settings.html", s=site)

    f = request.form
    site["brand"] = sc.clean(f.get("brand"), 60) or site.get("brand", "Ortica영어")
    site["tagline"] = sc.clean(f.get("tagline"), 120)
    site["description"] = sc.clean(f.get("description"), 300)
    for key in ("email", "phone", "kakao_url", "kakao_label", "hours"):
        site["contact"][key] = sc.clean(f.get(f"contact_{key}"), 200)
    for key in ("bank_name", "bank_account", "bank_holder", "kakaopay_url", "notice"):
        site["payment"][key] = sc.clean(f.get(f"payment_{key}"), 300)
    for key in ("company", "owner", "reg_no", "mailorder_no", "address"):
        site["business"][key] = sc.clean(f.get(f"business_{key}"), 200)
    for key in ("refund", "license", "privacy"):
        site["policy"][key] = sc.clean(f.get(f"policy_{key}"), 1000)

    # 프리패스
    pass_cfg = site.setdefault("pass", {})
    pass_cfg["enabled"] = bool(f.get("pass_enabled"))
    pass_cfg["mode"] = "sale" if f.get("pass_mode") == "sale" else "preorder"
    pass_cfg["headline"] = sc.clean(f.get("pass_headline"), 150)
    pass_cfg["lead"] = sc.clean(f.get("pass_lead"), 400)
    pass_cfg["note"] = sc.clean(f.get("pass_note"), 500)
    plans = []
    for name, price, per, period, badge, desc in zip(
            f.getlist("plan_name"), f.getlist("plan_price"), f.getlist("plan_per_month"),
            f.getlist("plan_period"), f.getlist("plan_badge"), f.getlist("plan_desc")):
        if not sc.clean(name, 40):
            continue
        plan = {"name": sc.clean(name, 40), "price": sc.to_int(price, 0),
                "per_month": sc.to_int(per, 0), "period": sc.clean(period, 30),
                "desc": sc.clean(desc, 200)}
        if sc.clean(badge, 20):
            plan["badge"] = sc.clean(badge, 20)
        plans.append(plan)
    if plans:
        pass_cfg["plans"] = plans

    # 시험지 제출 보상
    reward = site.setdefault("submit_reward", {})
    reward["enabled"] = bool(f.get("reward_enabled"))
    reward["coupon_kind"] = "percent" if f.get("reward_kind") == "percent" else "amount"
    reward["coupon_value"] = sc.to_int(f.get("reward_value"), 5000)
    reward["min_amount"] = sc.to_int(f.get("reward_min_amount"), 0)
    reward["days_valid"] = sc.to_int(f.get("reward_days_valid"), 90)
    reward["headline"] = sc.clean(f.get("reward_headline"), 150)
    reward["lead"] = sc.clean(f.get("reward_lead"), 500)

    sc.save_site(site)
    flash("가게 정보를 저장했습니다. 사이트에 바로 반영됐습니다.", "ok")
    return redirect(url_for("admin.settings"))


# ---------------------------------------------------------------------------
# 백업 · 되돌리기
# ---------------------------------------------------------------------------
@admin_bp.route("/backup")
def backup():
    return render_template("admin/backup.html", files=MANAGED_FILES)


@admin_bp.route("/backup/download")
def backup_download():
    """설정 3개 파일을 하나로 묶어 내려받습니다."""
    bundle = {"_저장시각": sc.stamp(),
              "_안내": "관리자 화면 > 백업 에서 이 파일을 올리면 그대로 되돌릴 수 있습니다."}
    for name in MANAGED_FILES:
        bundle[name] = sc.load_json(name, {})
    body = json.dumps(bundle, ensure_ascii=False, indent=2).encode("utf-8")
    return body, 200, {"Content-Type": "application/json; charset=utf-8",
                       "Content-Disposition":
                       f'attachment; filename="ortica-backup-{sc.now_kst():%Y%m%d-%H%M}.json"'}


@admin_bp.route("/backup/restore", methods=["POST"])
def backup_restore():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("백업 파일을 골라 주세요.", "err")
        return redirect(url_for("admin.backup"))
    try:
        bundle = json.loads(upload.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        flash("백업 파일을 읽지 못했습니다. 여기서 내려받은 파일이 맞는지 확인해 주세요.", "err")
        return redirect(url_for("admin.backup"))

    restored = []
    for name in MANAGED_FILES:
        if isinstance(bundle.get(name), dict):
            sc.save_json(name, bundle[name])
            restored.append(name)
    if restored:
        flash(f"{len(restored)}개 설정을 되돌렸습니다. 사이트를 확인해 보세요.", "ok")
    else:
        flash("되돌릴 내용이 없습니다. 백업 파일이 비어 있는 것 같습니다.", "err")
    return redirect(url_for("admin.backup"))

#!/usr/bin/env python3
"""Ortica영어 - 영어 자료 판매 사이트 (고객 화면).

실행:
    pip install -r store_requirements.txt
    ADMIN_PASSWORD=원하는비번 python store.py
그다음 브라우저에서  http://localhost:5001  접속.
주문 관리는  http://localhost:5001/admin

이 파일은 고객이 보는 화면입니다.
관리자 화면은 store_admin.py, 공용 부품은 store_common.py 에 있습니다.
자료를 만드는 내부 도구(webapp.py)와는 완전히 분리되어 있어,
판매 사이트를 인터넷에 올려도 내부 도구나 API 키는 노출되지 않습니다.

바꾸고 싶은 내용은 대부분 코드가 아니라 관리자 화면에서 고칠 수 있습니다.
자세한 사용법은 STORE.md 를 보세요.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import timedelta

from flask import (Flask, abort, redirect, render_template, request,
                   send_from_directory, session, url_for)
from markupsafe import Markup, escape

import store_common as sc
from store_admin import admin_bp

# static_url_path 를 적어 주지 않으면 폴더 이름을 따라 /store_static 이 됩니다.
app = Flask(__name__, template_folder="store_templates",
            static_folder="store_static", static_url_path="/static")
app.secret_key = os.environ.get("STORE_SECRET") or secrets.token_hex(16)
app.config["JSON_AS_ASCII"] = False

# --- 로그인 쿠키 단속 -------------------------------------------------------
# HTTPONLY : 자바스크립트가 쿠키를 못 읽게 (스크립트로 훔쳐 가는 것 차단)
# SAMESITE : 다른 사이트에서 우리 관리자 주소로 몰래 요청 못 하게
# SECURE   : https 로만 쿠키를 보냄. 내 컴퓨터(http)에서 개발할 땐 꺼 둡니다.
# LIFETIME : 7일이 지나면 다시 로그인
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("STORE_HTTPS", "1") == "1"
                               and not os.environ.get("STORE_DEBUG")),
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)
# 글꼴 파일이 800KB 가까이 되므로 브라우저가 오래 캐시하도록 합니다(30일).
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 30
# 업로드 상한. 무료 서버는 메모리가 작아 큰 파일을 받으면 죽습니다.
# 더 큰 자료는 구글 드라이브 링크로 거세요(관리자 > 상품 > 파일).
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

app.register_blueprint(admin_bp)
app.teardown_appcontext(sc.close_db)


# ---------------------------------------------------------------------------
# 모든 화면이 함께 쓰는 값 / 서식
# ---------------------------------------------------------------------------
@app.after_request
def security_headers(resp):
    """모든 화면에 공통으로 거는 최소한의 방어."""
    # 브라우저가 파일 종류를 멋대로 추측하지 않게 (올린 파일이 스크립트로 실행되는 것 차단)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    # 바깥 사이트로 이동할 때 우리 주소(다운로드 열쇠가 들어 있을 수 있음)를 넘기지 않음
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # 쓰지도 않는 카메라·마이크·위치 권한을 아예 잠금
    resp.headers.setdefault("Permissions-Policy",
                            "camera=(), microphone=(), geolocation=(), payment=()")
    return resp


@app.context_processor
def inject_globals():
    site = sc.load_site()
    return {
        "site": site,
        "now": sc.now_kst(),
        "nav_categories": sc.load_catalog().get("categories", []),
        # 'pass' 는 파이썬 예약어라 템플릿에서 site.pass 로 못 씁니다. 따로 넘깁니다.
        "passcfg": site.get("pass", {}),
        "order_kinds": sc.ORDER_KIND_LABELS,
        "material_map": sc.material_map(),
        "package_map": sc.package_map(),
    }


@app.template_filter("won")
def won(value) -> str:
    """12000 -> '12,000원'"""
    try:
        return f"{int(value):,}원"
    except (TypeError, ValueError):
        return str(value)


@app.template_filter("filesize")
def filesize(value):
    return sc.human_size(int(value or 0))


@app.template_filter("br")
def br(value) -> Markup:
    """줄을 바꾸고 싶은 자리를 그대로 지켜 줍니다.

    관리자 화면에서 줄바꿈(Enter)을 넣거나 ' | ' 를 적으면 그 자리에서 줄이 바뀝니다.
    한글은 자동 줄나눔이 어색해지는 자리가 있어서, 손으로 잡을 수 있게 열어 둡니다.
    """
    text = escape((value or "").strip())
    text = text.replace("|", "\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return Markup("<br>".join(lines))


@app.template_filter("fromjson")
def fromjson(value):
    """관리자 화면에서 상세(JSON 문자열)를 표로 펼칠 때 씁니다."""
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# 홈 · 목록 · 상세
# ---------------------------------------------------------------------------
def recent_updates(catalog: dict, limit: int = 4) -> list[dict]:
    """새로 올라온 것 — 무료 자료와 새 자료에서 자동으로 모읍니다.

    따로 공지를 쓰지 않아도 자료만 올리면 이 자리가 바뀝니다.
    """
    rows = []
    for x in sc.load_freebies()["items"]:
        if sc.free_ready(x):
            rows.append({"date": x.get("date", ""), "tag": "무료",
                         "title": x.get("title", ""), "note": x.get("summary", ""),
                         "url": url_for("free_detail", slug=x["slug"]), "free": True})
    for p in catalog["products"]:
        if not p.get("added"):
            continue
        rows.append({"date": p["added"], "tag": "새 자료",
                     "title": p.get("name", ""), "note": p.get("subtitle", ""),
                     "url": url_for("product_detail", slug=p["slug"]), "free": False})
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows[:limit]


def category_preview(catalog: dict, per_category: int = 3) -> list[dict]:
    """분류마다 교재를 몇 권씩만 보여 줍니다. 첫 화면에서 전체 그림이 잡히도록."""
    out = []
    for cat in catalog.get("categories", []):
        books = sc.books_with_counts(catalog, cat.get("id", ""))
        if not books:
            continue
        out.append({"cat": cat, "books": books[:per_category], "total": len(books)})
    return out


@app.route("/")
def home():
    catalog = sc.load_catalog()
    products = catalog["products"]
    notices = sc.load_notices()["notices"]
    groups = sc.grouped_materials()
    all_materials = [m for g in groups for m in g["items"]]
    # 무료 자료 — 받을 수 있는 것만 최신 세 건
    free_items = [x for x in sc.load_freebies()["items"] if sc.free_ready(x)][:3]
    fresh = recent_updates(catalog, limit=4)
    free_ready_count = sum(1 for p in products
                           if p.get("sample_file") and (sc.SAMPLE_DIR / p["sample_file"]).exists())
    return render_template("home.html", product_count=len(products),
                           lineup_groups=groups, lineup_all=all_materials,
                           material_total=len(all_materials),
                           free_items=free_items, free_ready_count=free_ready_count,
                           exams=sc.upcoming_exams(3), fresh=fresh,
                           cat_preview=category_preview(catalog),
                           latest_notice=notices[0] if notices else None)


def group_by_book(items: list[dict], books: list[dict]) -> tuple[list[dict], list[dict]]:
    """같은 교재의 자료를 한 카드로 묶습니다.

    같은 교재가 '지문 분석'·'문제' 두 장으로 나뉘어 목록이 두 배로 길어지던 것을
    한 장에 나란히 넣어 반으로 줄입니다.
    """
    order = {p.get("id"): p.get("sort", 100) for p in sc.load_raw_catalog()["packages"]}
    bucket, loose = {}, []
    for item in items:
        slug = item.get("book")
        if slug:
            bucket.setdefault(slug, []).append(item)
        else:
            loose.append(item)
    groups = []
    for book in books:
        picked = bucket.get(book["slug"])
        if not picked:
            continue
        picked = sorted(picked, key=lambda p: order.get(p.get("package"), 999))
        groups.append({"book": book, "items": picked,
                       "from_price": min(p.get("price", 0) for p in picked),
                       "passages": max(p.get("passages", 0) for p in picked)})
    return groups, loose


PRODUCT_ORDERS = {"": "추천순", "price": "가격 낮은 순", "passages": "지문 많은 순"}


@app.route("/products")
def products():
    catalog = sc.load_catalog()
    selected = request.args.get("category", "")
    package = request.args.get("package", "")
    grade = sc.clean(request.args.get("grade"), 10)
    order = request.args.get("order", "")
    q = sc.clean(request.args.get("q"), 60)

    items = catalog["products"]
    books = sc.books_with_counts(catalog, selected)
    grades = sorted({g for p in catalog["products"] for g in (p.get("grade") or "").split("~")
                     if g.strip()})
    if selected:
        items = [p for p in items if p.get("category") == selected]
    if package:
        items = [p for p in items if p.get("package") == package]
    if grade:
        items = [p for p in items if grade in (p.get("grade") or "")]
    if q:
        # 교재 이름·출판사로도 찾히게 합니다. ("능률" 만 쳐도 그 교재 상품이 나오도록)
        needle = q.lower()
        book_hit = {b["slug"] for b in catalog["books"]
                    if needle in f"{b.get('name','')} {b.get('publisher','')} "
                                 f"{b.get('author','')}".lower()}
        items = [p for p in items
                 if needle in f"{p.get('name','')} {p.get('subtitle','')} "
                              f"{p.get('grade','')}".lower()
                 or p.get("book") in book_hit]
        books = [b for b in books
                 if needle in f"{b.get('name','')} {b.get('publisher','')} "
                              f"{b.get('author','')}".lower()]
    if order == "price":
        items = sorted(items, key=lambda p: p.get("price", 0))
    elif order == "passages":
        items = sorted(items, key=lambda p: -p.get("passages", 0))

    groups, loose = group_by_book(items, books)
    # 교재 카드끼리도 같은 기준으로 줄을 세웁니다.
    # (묶기만 하고 두면 '가격 낮은 순'을 눌러도 화면이 그대로라 눌러 본 보람이 없습니다)
    if order == "price":
        groups = sorted(groups, key=lambda g: g["from_price"])
    elif order == "passages":
        groups = sorted(groups, key=lambda g: -g["passages"])
    return render_template("products.html", items=items, books=books,
                           groups=groups, loose=loose,
                           categories=catalog.get("categories", []), selected=selected,
                           packages=catalog.get("packages", []), selected_package=package,
                           grades=grades, grade=grade,
                           orders=PRODUCT_ORDERS, order=order,
                           q=q)


def find_product(slug: str) -> dict | None:
    for product in sc.load_catalog()["products"]:
        if product.get("slug") == slug:
            return product
    return None


def find_book(slug: str) -> dict | None:
    for book in sc.load_catalog()["books"]:
        if book.get("slug") == slug:
            return book
    return None


@app.route("/products/<slug>")
def product_detail(slug):
    product = find_product(slug)
    if not product:
        abort(404)
    catalog = sc.load_catalog()
    book = next((b for b in catalog["books"] if b["slug"] == product.get("book")), None)
    # 같은 교재의 반대쪽 패키지 — 분석을 보고 있으면 문제, 문제를 보고 있으면 분석.
    sibling = next((x for x in catalog["products"]
                    if x.get("book") and x.get("book") == product.get("book")
                    and x.get("package") and x.get("package") != product.get("package")), None)
    related = [x for x in catalog["products"]
               if x.get("category") == product.get("category")
               and x.get("slug") != slug and x is not sibling][:3]
    sample_ready = bool(product.get("sample_file")
                        and (sc.SAMPLE_DIR / product["sample_file"]).exists())
    return render_template("product.html", p=product, book=book,
                           sibling=sibling, related=related, sample_ready=sample_ready)


@app.route("/books/<slug>")
def book_detail(slug):
    """교재 한 권의 전용 페이지.

    강사는 '내가 쓰는 교재 이름'으로 자료를 찾기 때문에, 교재 단위 주소를
    따로 두면 검색으로 들어오기도 쉽고 링크로 공유하기도 편합니다.
    """
    book = find_book(slug)
    if not book:
        abort(404)
    catalog = sc.load_catalog()
    items = [p for p in catalog["products"] if p.get("book") == slug]
    # 지문 분석 패키지 / 문제 패키지 순서로 갈라 놓습니다.
    lanes = []
    for pkg in catalog.get("packages", []):
        picked = [p for p in items if p.get("package") == pkg["id"]]
        if picked:
            lanes.append({**pkg, "items": picked})
    rest = [p for p in items if not p.get("package")]
    others = [b for b in sc.books_with_counts(catalog, book.get("category", ""))
              if b["slug"] != slug][:3]
    return render_template("book.html", book=book, items=items, lanes=lanes,
                           rest=rest, others=others)


@app.route("/lineup")
def lineup():
    """오르티카 라인업 — 우리가 만드는 자료 8종을 한 장에 보여 주는 페이지."""
    data = sc.load_materials()
    # 샘플 파일이 실제로 올라와 있는 자료에만 받기 버튼을 답니다.
    ready = {m["sample_file"] for m in data["materials"]
             if m.get("sample_file") and (sc.SAMPLE_DIR / m["sample_file"]).exists()}
    return render_template("lineup.html", intro=data.get("intro", {}),
                           groups=sc.grouped_materials(),
                           ready_samples=ready, sample_count=len(ready))


@app.route("/notice")
def notice():
    return render_template("notice.html", **sc.load_notices())


# ---------------------------------------------------------------------------
# 주문
# ---------------------------------------------------------------------------
@app.route("/coupon/check")
def coupon_check():
    """주문서에서 쿠폰 코드를 입력하면 즉시 확인해 주는 창구입니다."""
    amount = sc.to_int(request.args.get("amount"), 0)
    coupon, discount, note = sc.check_coupon(request.args.get("code", ""), amount)
    return {"ok": coupon is not None, "discount": discount, "message": note,
            "final": max(0, amount - discount)}


@app.route("/order", methods=["GET", "POST"])
def order():
    slug = request.values.get("slug", "")
    product = find_product(slug)
    if not product:
        abort(404)

    catalog = sc.load_catalog()
    # 같은 교재의 반대쪽 패키지 — 한 번에 같이 주문할 수 있게 합니다.
    sibling = next((x for x in catalog["products"]
                    if x.get("book") and x.get("book") == product.get("book")
                    and x.get("package") and x.get("package") != product.get("package")), None)

    book = next((b for b in catalog["books"] if b["slug"] == product.get("book")), None)

    if request.method == "GET":
        return render_template("order.html", p=product, sibling=sibling, book=book,
                               form={}, errors=[])

    if sc.too_many_submits(request, "order"):
        errors = ["잠시 뒤에 다시 시도해 주세요. 짧은 시간에 너무 많이 보내셨습니다."]
        return render_template("order.html", p=product, sibling=sibling, book=book,
                               form=request.form, errors=errors), 429

    data, errors = sc.validate_contact(request.form)
    quantity = max(1, min(99, sc.to_int(request.form.get("quantity"), 1)))
    depositor = sc.clean(request.form.get("depositor"), 50) or data["name"]

    receipt_kind = sc.clean(request.form.get("receipt_kind"), 20)
    if receipt_kind not in sc.RECEIPT_KINDS:
        receipt_kind = ""
    receipt_no = sc.clean(request.form.get("receipt_no"), 40)
    if receipt_kind and not receipt_no:
        errors.append("증빙을 받으시려면 사업자등록번호나 휴대폰 번호를 적어 주세요.")

    take_both = bool(request.form.get("also")) and sibling is not None
    unit = int(product.get("price", 0)) + (int(sibling.get("price", 0)) if take_both else 0)
    subtotal = unit * quantity
    coupon_code = sc.clean(request.form.get("coupon"), 40).upper()
    coupon, discount, coupon_note = sc.check_coupon(coupon_code, subtotal)
    if coupon_code and coupon is None:
        errors.append(coupon_note)

    if errors:
        return render_template("order.html", p=product, sibling=sibling, book=book,
                               form=request.form, errors=errors), 400

    amount = subtotal - discount
    ts = sc.stamp()
    view_key = sc.new_view_key()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, view_key, kind, product_slug, extra_slugs, product_name,
                               quantity, amount, discount, coupon_code, name, phone, email,
                               affiliation, depositor, message, receipt_kind, receipt_no,
                               status, created_at, updated_at)
           VALUES (?, ?, 'product', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, view_key, product["slug"], sibling["slug"] if take_both else None,
                    product["name"] + (" + " + sibling["name"] if take_both else ""),
                    quantity, amount, discount,
                    coupon["code"] if coupon else None, data["name"], data["phone"],
                    data["email"], data["affiliation"], depositor, data["message"],
                    receipt_kind, receipt_no, ts, ts))
    if coupon:
        sc.redeem_coupon(coupon["code"], order_no)

    sc.send_mail(
        f"[Ortica영어] 새 주문 {order_no} · {product['name']}",
        "\n".join([f"주문번호 : {order_no}",
                   f"상품     : {product['name']}"
                   + (f" + {sibling['name']}" if take_both else "") + f" x {quantity}",
                   f"주문금액 : {subtotal:,}원",
                   f"할인     : -{discount:,}원 ({coupon['code'] if coupon else '없음'})",
                   f"결제금액 : {amount:,}원",
                   f"성함     : {data['name']}",
                   f"입금자명 : {depositor}",
                   f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}",
                   f"소속     : {data['affiliation'] or '-'}",
                   f"증빙     : {sc.RECEIPT_KINDS.get(receipt_kind, '-')} {receipt_no}",
                   f"요청사항 : {data['message'] or '-'}",
                   f"접수시각 : {ts}"]))
    return redirect(url_for("order_done", key=view_key))


@app.route("/order/done/<key>")
def order_done(key):
    """주문 확인 화면.

    주소에 주문번호가 아니라 긴 열쇠를 씁니다. 주문번호(OR-260901-12345)로 열게 두면
    번호를 하나씩 바꿔 가며 남의 이름·연락처를 훔쳐볼 수 있기 때문입니다.
    """
    row = sc.get_db().execute("SELECT * FROM orders WHERE view_key = ?", (key,)).fetchone()
    if not row:
        abort(404)
    return render_template("order_done.html", o=row)


# ---------------------------------------------------------------------------
# 자료 요청 · 맞춤 제작
# ---------------------------------------------------------------------------
@app.route("/custom", methods=["GET", "POST"])
def custom():
    """한 폼에서 두 가지를 받습니다.

    request : 찾는 교재 이름만 적어 두면, 그 교재를 만든 뒤 연락드립니다. (지문 불필요)
    custom  : 내 지문을 보내 같은 형식으로 제작을 의뢰합니다.
    """
    default_mode = "request" if request.args.get("mode") != "custom" else "custom"
    if request.method == "GET":
        return render_template("custom.html", form={"mode": default_mode}, errors=[])

    mode = "custom" if request.form.get("mode") == "custom" else "request"
    if sc.too_many_submits(request, "custom"):
        return render_template("custom.html", form=request.form,
                               errors=["잠시 뒤에 다시 시도해 주세요."]), 429
    data, errors = sc.validate_contact(request.form)
    wanted = sc.clean(request.form.get("wanted"), 200)
    detail = {
        "찾는 교재": wanted,
        "학년·과정": sc.clean(request.form.get("course"), 60) or "-",
    }
    if mode == "custom":
        detail.update({
            "지문 수": sc.clean(request.form.get("passage_count"), 30) or "-",
            "원하는 자료": ", ".join(request.form.getlist("materials")) or "-",
            "희망 마감일": sc.clean(request.form.get("due"), 40) or "-",
            "지문 파일 링크": sc.clean(request.form.get("file_link"), 300) or "-",
        })
    if not wanted:
        errors.append("어떤 교재·회차를 찾으시는지 적어 주세요.")
    if errors:
        return render_template("custom.html", form=request.form, errors=errors), 400

    label = "자료 요청" if mode == "request" else "맞춤 제작 의뢰"
    ts = sc.stamp()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                               name, phone, email, affiliation, message, detail_json,
                               status, created_at, updated_at)
           VALUES (?, ?, ?, 1, 0, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, mode, label, data["name"], data["phone"], data["email"],
                    data["affiliation"], data["message"],
                    json.dumps(detail, ensure_ascii=False), ts, ts))

    sc.send_mail(
        f"[Ortica영어] {label} {order_no} · {wanted[:40]}",
        "\n".join([f"접수번호 : {order_no}", f"종류     : {label}",
                   f"성함     : {data['name']}", f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}", f"소속     : {data['affiliation'] or '-'}"]
                  + [f"{k} : {v}" for k, v in detail.items()]
                  + [f"요청사항 : {data['message'] or '-'}", f"접수시각 : {ts}"]))
    return render_template("custom_done.html", order_no=order_no, mode=mode, wanted=wanted)


# ---------------------------------------------------------------------------
# 시험지 제출 → 할인 쿠폰
# ---------------------------------------------------------------------------
SUBMIT_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".hwp", ".hwpx", ".zip"}


@app.route("/submit", methods=["GET", "POST"])
def submit():
    reward = sc.load_site().get("submit_reward", {})
    if not reward.get("enabled", True):
        abort(404)

    if request.method == "GET":
        return render_template("submit.html", reward=reward, form={}, errors=[], done=None)

    if sc.too_many_submits(request, "submit"):
        return render_template("submit.html", reward=reward, form=request.form,
                               errors=["잠시 뒤에 다시 시도해 주세요."], done=None), 429
    data, errors = sc.validate_contact(request.form)
    school = sc.clean(request.form.get("school"), 60)
    if not school:
        errors.append("학교 이름을 적어 주세요.")

    file_link = sc.clean(request.form.get("file_link"), 300)
    upload = request.files.get("file")
    saved_name = ""
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in SUBMIT_EXTS:
            errors.append("PDF · 사진(JPG/PNG) · 한글(HWP) · ZIP 파일만 올릴 수 있습니다.")
    elif not file_link:
        errors.append("시험지 파일을 올리거나, 파일이 있는 링크를 적어 주세요.")
    if not request.form.get("agree_source"):
        errors.append("시험지 출처와 이용 범위에 동의해 주셔야 접수됩니다.")

    if errors:
        return render_template("submit.html", reward=reward, form=request.form,
                               errors=errors, done=None), 400

    submit_no = sc.new_submit_no()
    while sc.get_db().execute("SELECT 1 FROM submissions WHERE submit_no = ?",
                              (submit_no,)).fetchone():
        submit_no = sc.new_submit_no()
    if upload and upload.filename:
        ext = os.path.splitext(upload.filename)[1].lower()
        sc.SUBMIT_DIR.mkdir(parents=True, exist_ok=True)
        saved_name = f"{submit_no}{ext}"
        upload.save(sc.SUBMIT_DIR / saved_name)

    ts = sc.stamp()
    db = sc.get_db()
    db.execute(
        """INSERT INTO submissions (submit_no, school, grade, exam_type, exam_term, scope,
                                    file_name, file_link, name, phone, email, message,
                                    status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'검토대기',?,?)""",
        (submit_no, school, sc.clean(request.form.get("grade"), 20),
         sc.clean(request.form.get("exam_type"), 20),
         sc.clean(request.form.get("exam_term"), 30),
         sc.clean(request.form.get("scope"), 200),
         saved_name, file_link, data["name"], data["phone"], data["email"],
         data["message"], ts, ts))
    db.commit()

    sc.send_mail(
        f"[Ortica영어] 시험지 제출 {submit_no} · {school}",
        "\n".join([f"접수번호 : {submit_no}", f"학교     : {school}",
                   f"학년     : {request.form.get('grade') or '-'}",
                   f"시험     : {request.form.get('exam_type') or '-'} "
                   f"{request.form.get('exam_term') or ''}",
                   f"범위     : {request.form.get('scope') or '-'}",
                   f"파일     : {saved_name or file_link or '-'}",
                   f"성함     : {data['name']}", f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}",
                   f"하고 싶은 말 : {data['message'] or '-'}",
                   f"접수시각 : {ts}",
                   "", "관리자 화면 > 시험지 제출 에서 확인하고 쿠폰을 발급해 주세요."]))
    return render_template("submit.html", reward=reward, form={}, errors=[], done=submit_no)


# ---------------------------------------------------------------------------
# 프리패스
# ---------------------------------------------------------------------------
@app.route("/pass", methods=["GET", "POST"])
def pass_page():
    """프리패스(무제한 이용권) 안내.

    site.json 의 pass.mode 가 'preorder' 면 가격표만 보여 주고 사전 신청을 받습니다.
    자료가 충분히 쌓인 뒤 'sale' 로 바꾸면 실제 판매 문구로 바뀝니다.
    """
    cfg = sc.load_site().get("pass", {})
    if not cfg.get("enabled"):
        abort(404)

    if request.method == "GET":
        return render_template("pass.html", cfg=cfg, form={}, errors=[], done=None)

    data, errors = sc.validate_contact(request.form)
    plan = sc.clean(request.form.get("plan"), 40)
    if plan not in [pl["name"] for pl in cfg.get("plans", [])]:
        errors.append("관심 있는 이용권을 골라 주세요.")
    if errors:
        return render_template("pass.html", cfg=cfg, form=request.form,
                               errors=errors, done=None), 400

    ts = sc.stamp()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                               name, phone, email, affiliation, message, detail_json,
                               status, created_at, updated_at)
           VALUES (?, 'pass', ?, 1, 0, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, f"프리패스 사전 신청 · {plan}", data["name"], data["phone"],
                    data["email"], data["affiliation"], data["message"],
                    json.dumps({"관심 이용권": plan}, ensure_ascii=False), ts, ts))

    sc.send_mail(
        f"[Ortica영어] 프리패스 사전 신청 {order_no} · {plan}",
        "\n".join([f"신청번호 : {order_no}", f"관심 이용권 : {plan}",
                   f"성함     : {data['name']}", f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}", f"소속     : {data['affiliation'] or '-'}",
                   f"하고 싶은 말 : {data['message'] or '-'}", f"접수시각 : {ts}"]))
    return render_template("pass.html", cfg=cfg, form={}, errors=[], done=order_no)


# ---------------------------------------------------------------------------
# 무료 자료실 — 회차마다 뿌리는 자료
# ---------------------------------------------------------------------------
def free_unlocked(slug: str) -> bool:
    """이메일을 적고 받기로 한 자료를, 그 손님이 이미 열어 두었는지."""
    return slug in (session.get("free_ok") or [])


def unlock_free(slug: str) -> None:
    opened = list(session.get("free_ok") or [])
    if slug not in opened:
        opened.append(slug)
        session["free_ok"] = opened[-40:]      # 쿠키가 무한정 커지지 않게


@app.route("/free")
def free():
    """무료 자료실 — 회차·학년으로 걸러 봅니다."""
    data = sc.load_freebies()
    grade = sc.clean(request.args.get("grade"), 10)
    kind = sc.clean(request.args.get("kind"), 20)
    exam = sc.clean(request.args.get("exam"), 60)
    q = sc.clean(request.args.get("q"), 60)

    items = [x for x in data["items"] if sc.free_ready(x)]
    # 거르기 버튼은 준비 중인 것까지 포함해 만들어 둡니다.
    grades = sorted({x.get("grade", "") for x in data["items"] if x.get("grade")})
    exams = sorted({x.get("exam", "") for x in data["items"] if x.get("exam")}, reverse=True)
    if grade:
        items = [x for x in items if x.get("grade") == grade]
    if kind in sc.FREE_KINDS:
        items = [x for x in items if kind in (x.get("kinds") or [])]
    if exam:
        items = [x for x in items if x.get("exam") == exam]
    if q:
        needle = q.lower()
        items = [x for x in items
                 if needle in f"{x.get('title','')} {x.get('summary','')} "
                              f"{x.get('exam','')} {x.get('grade','')} "
                              f"{' '.join(sc.free_kind_names(x))}".lower()]

    # 파일이 아직 안 올라온 것은 '준비 중'으로 따로 모아 둡니다.
    coming = [x for x in data["items"] if not sc.free_ready(x)]
    lineup_samples = sum(1 for m in sc.load_materials()["materials"]
                         if m.get("sample_file")
                         and (sc.SAMPLE_DIR / m["sample_file"]).exists())

    return render_template("free.html", intro=data.get("intro", {}), items=items,
                           total=len([x for x in data["items"] if sc.free_ready(x)]),
                           coming=coming, grades=grades, grade=grade, kind=kind,
                           exams=exams, exam=exam, q=q,
                           kinds=sc.FREE_KINDS, sample_count=lineup_samples)


@app.route("/free/<slug>")
def free_detail(slug):
    item = sc.find_freebie(slug)
    if item is None:
        abort(404)
    catalog = sc.load_catalog()
    related = [p for p in catalog["products"] if p.get("slug") in (item.get("related") or [])]
    return render_template(
        "free_detail.html", item=item, files=sc.free_files(slug),
        links=sc.free_links(item), kind_names=sc.free_kind_names(item),
        opened=(item.get("gate") != "email" or free_unlocked(slug)),
        related=related, errors=[], form={})


@app.route("/free/<slug>/get", methods=["POST"])
def free_get(slug):
    """이메일을 받고 내어 주는 자료 — 이메일만 적으면 바로 열립니다."""
    item = sc.find_freebie(slug)
    if item is None:
        abort(404)

    email = sc.clean(request.form.get("email"), 120)
    errors = []
    if sc.too_many_submits(request, "free"):
        errors.append("잠시 뒤에 다시 시도해 주세요. 짧은 시간에 너무 많이 보내셨습니다.")
    elif not sc.EMAIL_RE.match(email):
        errors.append("이메일 주소를 정확히 적어 주세요. 예: teacher@school.com")
    elif not request.form.get("agree"):
        errors.append("이메일 수집·이용에 동의해 주셔야 받으실 수 있습니다.")

    if errors:
        return render_template(
            "free_detail.html", item=item, files=sc.free_files(slug),
            links=sc.free_links(item), kind_names=sc.free_kind_names(item),
            opened=False, related=[], errors=errors, form=request.form), 400

    sc.add_lead(email, name=sc.clean(request.form.get("name"), 50), slug=slug,
                title=item.get("title", ""), news=bool(request.form.get("news")))
    unlock_free(slug)
    return redirect(url_for("free_detail", slug=slug))


@app.route("/free/notify", methods=["POST"])
def free_notify():
    """새 자료가 올라오면 알려 달라는 신청. 이메일 한 칸이면 끝입니다."""
    email = sc.clean(request.form.get("email"), 120)
    back = url_for("free", _anchor="notify")
    if sc.too_many_submits(request, "free") or not sc.EMAIL_RE.match(email):
        return redirect(back + "?bad=1")
    sc.add_lead(email, slug="", title="새 자료 알림 신청", news=True)
    return redirect(back + "?ok=1")


@app.route("/free/<slug>/file/<int:index>")
def free_file(slug, index):
    """무료 자료 파일 내려받기."""
    item = sc.find_freebie(slug)
    if item is None:
        abort(404)
    if item.get("gate") == "email" and not free_unlocked(slug):
        return redirect(url_for("free_detail", slug=slug))
    files = sc.free_files(slug)
    if not 0 <= index < len(files):
        abort(404)
    folder = sc.free_dir(slug)
    return send_from_directory(folder, files[index]["name"], as_attachment=True)


# ---------------------------------------------------------------------------
# 샘플 · 안내 · 기타
# ---------------------------------------------------------------------------
@app.route("/samples")
def samples():
    """예전 '무료 샘플' 목록 주소. 지금은 라인업에서 자료마다 샘플을 받습니다."""
    return redirect(url_for("lineup"), code=301)


@app.route("/samples/<path:filename>")
def sample_download(filename):
    """무료 샘플 PDF 내려받기. 폴더 밖 파일 요청은 막습니다."""
    target = (sc.SAMPLE_DIR / filename).resolve()
    if sc.SAMPLE_DIR.resolve() not in target.parents or not target.is_file():
        abort(404)
    return send_from_directory(sc.SAMPLE_DIR, filename, as_attachment=True)


# ---------------------------------------------------------------------------
# 결제 확인 후 받는 다운로드 링크
# ---------------------------------------------------------------------------
@app.route("/d/<token>")
def download_page(token):
    """메일로 보내 드린 링크. 이 주소를 아는 사람만 파일을 받을 수 있습니다."""
    row, reason = sc.check_download(token)
    if row is None:
        return render_template("download.html", d=None, files=[], links=[],
                               reason=reason), 404
    product = next((x for x in sc.load_catalog()["products"]
                    if x.get("slug") == row["product_slug"]), {})
    return render_template("download.html", d=row,
                           files=sc.product_files(row["product_slug"]),
                           links=sc.product_links(product), reason="")


@app.route("/d/<token>/<int:index>")
def download_file(token, index):
    row, _ = sc.check_download(token)
    if row is None:
        abort(404)
    files = sc.product_files(row["product_slug"])
    if not 0 <= index < len(files):
        abort(404)
    sc.count_download(token)
    return send_from_directory(sc.product_dir(row["product_slug"]),
                               files[index]["name"], as_attachment=True)


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/robots.txt")
def robots():
    """검색엔진에게 관리자 화면과 다운로드 주소는 훑지 말라고 알려 줍니다."""
    body = "\n".join([
        "User-agent: *",
        "Disallow: /admin",
        "Disallow: /d/",
        "Disallow: /order",
        "Allow: /",
        f"Sitemap: {url_for('home', _external=True).rstrip('/')}/sitemap.xml",
    ]) + "\n"
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/sitemap.xml")
def sitemap():
    """네이버·구글이 상품과 교재 페이지를 찾아가도록 목록을 내어 줍니다."""
    catalog = sc.load_catalog()
    urls = [url_for("home", _external=True), url_for("free", _external=True),
            url_for("lineup", _external=True),
            url_for("products", _external=True), url_for("samples", _external=True),
            url_for("notice", _external=True), url_for("guide", _external=True),
            url_for("custom", _external=True), url_for("submit", _external=True)]
    urls += [url_for("free_detail", slug=x["slug"], _external=True)
             for x in sc.load_freebies()["items"]]
    urls += [url_for("book_detail", slug=b["slug"], _external=True) for b in catalog["books"]]
    urls += [url_for("product_detail", slug=p["slug"], _external=True)
             for p in catalog["products"]]
    body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
            + "</urlset>\n")
    return body, 200, {"Content-Type": "application/xml; charset=utf-8"}


@app.route("/healthz")
def healthz():
    return {"ok": True}


@app.errorhandler(404)
def not_found(_exc):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(_exc):
    return render_template("404.html"), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    print(f"\n  Ortica영어 판매 사이트 → http://localhost:{port}")
    print(f"  관리자 화면          → http://localhost:{port}/admin\n  (종료: Ctrl+C)\n")
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("STORE_DEBUG")))

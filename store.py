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

import io
import json
import os
import secrets
from datetime import timedelta

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, send_from_directory, session, url_for)
from markupsafe import Markup, escape

import store_common as sc
import store_watermark as wm
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
        # 'discount' 도 예약어는 아니지만 같은 자리에 두어 화면에서 바로 씁니다.
        "discount": site.get("discount", {}),
        "cart_count": len(cart_slugs()),
        "order_kinds": sc.ORDER_KIND_LABELS,
        "inquiry_kinds": sc.INQUIRY_KINDS,
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
    free_ready_count = sum(1 for p in products
                           if p.get("sample_file") and (sc.SAMPLE_DIR / p["sample_file"]).exists())
    return render_template("home.html", product_count=len(products),
                           lineup_groups=groups, lineup_all=all_materials,
                           material_total=len(all_materials),
                           free_items=free_items, free_ready_count=free_ready_count,
                           exams=sc.upcoming_exams(3),
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
    full = sc.full_pack_for(product, catalog)
    return render_template("product.html", p=product, book=book,
                           sibling=sibling, related=related, sample_ready=sample_ready,
                           full=full, full_parts=len(full.get("covers", [])) if full else 0)


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
    shots = {m["id"]: sc.shot_files(m["id"]) for m in data["materials"] if m.get("id")}
    return render_template("lineup.html", intro=data.get("intro", {}),
                           groups=sc.grouped_materials(),
                           cat_preview=category_preview(sc.load_catalog()),
                           shots=shots,
                           ready_samples=ready, sample_count=len(ready))


@app.route("/notice")
def notice():
    """공지 · 자료 업데이트 일정. '지금 오르티카'(새 자료 · 다음 시험)도 여기 있습니다."""
    data = sc.load_notices()
    # notices.json 의 'exams' 는 원본 일정입니다. 화면에는 D-day 를 붙인 쪽을 씁니다.
    data["exams"] = sc.upcoming_exams(3)
    return render_template("notice.html", **data,
                           fresh=recent_updates(sc.load_catalog(), limit=6))


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


# ---------------------------------------------------------------------------
# 장바구니 — 여러 회차를 한 번에 담아 한 번만 입금하시도록
# ---------------------------------------------------------------------------
CART_MAX = 20


def cart_slugs() -> list[str]:
    return [x for x in (session.get("cart") or []) if isinstance(x, str)][:CART_MAX]


def save_cart(slugs: list[str]) -> None:
    seen, out = set(), []
    for slug in slugs:
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    session["cart"] = out[:CART_MAX]


def cart_items(catalog: dict | None = None) -> list[dict]:
    """장바구니에 담긴 상품을 담은 순서대로. 없어진 상품은 조용히 빠집니다."""
    catalog = catalog or sc.load_catalog()
    known = {p["slug"]: p for p in catalog["products"]}
    items = [known[slug] for slug in cart_slugs() if slug in known]
    if len(items) != len(cart_slugs()):
        save_cart([x["slug"] for x in items])
    return items


def sibling_of(product: dict, catalog: dict) -> dict | None:
    """같은 교재의 반대쪽 패키지."""
    return next((x for x in catalog["products"]
                 if x.get("book") and x.get("book") == product.get("book")
                 and x.get("package") and x.get("package") != product.get("package")), None)


def back_to(default: str) -> str:
    """돌아갈 곳. 우리 사이트 안으로만 보냅니다."""
    target = sc.clean(request.form.get("next") or request.args.get("next"), 200)
    if target.startswith("/") and not target.startswith("//"):
        return target
    return default


@app.route("/cart")
def cart():
    catalog = sc.load_catalog()
    items = cart_items(catalog)
    site = sc.load_site()
    rows, auto = sc.auto_discounts(site, items, 1)
    subtotal = sum(int(x.get("price", 0)) for x in items)
    # 짝이 안 맞는 상품에는 '반대쪽도 담으면 싸집니다' 를 권합니다
    suggest = []
    have = {x["slug"] for x in items}
    for item in items:
        mate = sibling_of(item, catalog)
        if mate and mate["slug"] not in have and mate["slug"] not in {s["slug"] for s in suggest}:
            suggest.append(mate)
    return render_template("cart.html", items=items, rows=rows, auto=auto,
                           subtotal=subtotal, final=subtotal - auto, suggest=suggest[:3],
                           full_offer=sc.full_pack_offer(items, catalog))


@app.route("/cart/add", methods=["POST"])
def cart_add():
    catalog = sc.load_catalog()
    known = {p["slug"] for p in catalog["products"]}
    slugs = cart_slugs()
    added = 0
    for slug in request.form.getlist("slug"):
        slug = sc.clean(slug, 60)
        if slug in known and slug not in slugs and len(slugs) < CART_MAX:
            slugs.append(slug)
            added += 1
    save_cart(slugs)
    if added == 1:
        name = next((p["name"] for p in catalog["products"]
                     if p["slug"] == slugs[-1]), "자료")
        flash(f"'{name}' 을(를) 담았습니다.", "cart")
    elif added > 1:
        flash(f"자료 {added}개를 담았습니다.", "cart")
    return redirect(back_to(url_for("cart")))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    slug = sc.clean(request.form.get("slug"), 60)
    save_cart([x for x in cart_slugs() if x != slug])
    return redirect(back_to(url_for("cart")))


@app.route("/cart/swap", methods=["POST"])
def cart_swap():
    """부분 상품 여러 개를 '전체' 상품 하나로 바꿔 담습니다."""
    catalog = sc.load_catalog()
    offer = sc.full_pack_offer(cart_items(catalog), catalog)
    slug = sc.clean(request.form.get("slug"), 60)
    if not offer or offer["full"]["slug"] != slug:
        return redirect(url_for("cart"))
    keep = [x for x in cart_slugs() if x not in offer["covers"]]
    save_cart(keep + [slug])
    flash(f"'{offer['full']['name']}' 하나로 바꿨습니다. "
          f"{offer['saving']:,}원 싸집니다.", "cart")
    return redirect(url_for("cart"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    session.pop("cart", None)
    return redirect(back_to(url_for("cart")))


def quote_for(items: list[dict], email: str, coupon_code: str,
              no_mark: bool = False) -> dict:
    """주문 금액을 한 곳에서 계산합니다. 화면과 접수가 같은 값을 쓰게 하려고 나눠 두었습니다."""
    site = sc.load_site()
    subtotal = sum(int(x.get("price", 0)) for x in items)
    repeat_no = sc.paid_order_count(email) + 1        # 이번이 몇 번째 구매인지
    rows, auto = sc.auto_discounts(site, items, repeat_no)
    coupon, coupon_cut, coupon_note = sc.check_coupon(coupon_code, subtotal - auto)
    extra = sc.no_mark_price(site) if no_mark else 0
    return {
        "subtotal": subtotal, "rows": rows, "auto": auto, "repeat_no": repeat_no,
        "coupon": coupon, "coupon_cut": coupon_cut, "coupon_note": coupon_note,
        "no_mark": bool(extra), "extra": extra,
        "discount": auto + coupon_cut,
        "final": subtotal - auto - coupon_cut + extra,
    }


def order_items(catalog: dict) -> tuple[list[dict], dict | None, dict | None, bool]:
    """이번 주문에 담긴 상품들.

    (담긴 상품, 낱개로 산 상품, 그 짝, 장바구니로 왔는지) 를 돌려줍니다.
    """
    if request.values.get("cart") == "1":
        return cart_items(catalog), None, None, True
    product = find_product(sc.clean(request.values.get("slug"), 60))
    if not product:
        return [], None, None, False
    sibling = sibling_of(product, catalog)
    take_both = bool(request.values.get("also")) and sibling is not None
    return ([product] + ([sibling] if take_both else []),
            product, sibling, False)


@app.route("/order/quote")
def order_quote():
    """수량·짝 패키지·쿠폰을 바꿀 때 화면에서 금액을 다시 물어봅니다."""
    catalog = sc.load_catalog()
    items, _product, _sibling, _from_cart = order_items(catalog)
    if not items:
        abort(404)
    q = quote_for(items,
                  sc.clean(request.args.get("email"), 120),
                  sc.clean(request.args.get("coupon"), 40).upper(),
                  request.args.get("nomark") == "1")
    return {
        "subtotal": q["subtotal"],
        "extra": q["extra"],
        "rows": [{"name": r["name"], "amount": r["amount"], "percent": r["percent"]}
                 for r in q["rows"]],
        "repeat_no": q["repeat_no"],
        "coupon_ok": bool(q["coupon"]),
        "coupon_cut": q["coupon_cut"],
        "coupon_note": q["coupon_note"],
        "final": q["final"],
    }


@app.route("/order", methods=["GET", "POST"])
def order():
    """주문서. 낱개 상품 하나로도, 장바구니 통째로도 옵니다."""
    catalog = sc.load_catalog()
    items, product, sibling, from_cart = order_items(catalog)
    if not items:
        if from_cart:
            return redirect(url_for("cart"))
        abort(404)
    books = {b["slug"]: b for b in catalog["books"]}

    def page(form, errors, status=200, typo=""):
        return render_template("order.html", items=items, p=product, sibling=sibling,
                               books=books, from_cart=from_cart, email_typo=typo,
                               no_mark_price=sc.no_mark_price(sc.load_site()),
                               form=form, errors=errors), status

    if request.method == "GET":
        body, _ = page({}, [])
        return body

    if sc.too_many_submits(request, "order"):
        return page(request.form,
                    ["잠시 뒤에 다시 시도해 주세요. 짧은 시간에 너무 많이 보내셨습니다."], 429)

    data, errors = sc.validate_contact(request.form)
    typo = data.get("email_typo", "")
    # 성함은 선택이라 비어 있을 수 있습니다. 입금 확인은 입금자명 → 성함 순으로 봅니다.
    depositor = sc.clean(request.form.get("depositor"), 50) or data["name"]

    receipt_kind = sc.clean(request.form.get("receipt_kind"), 20)
    if receipt_kind not in sc.RECEIPT_KINDS:
        receipt_kind = ""
    receipt_no = sc.clean(request.form.get("receipt_no"), 40)
    if receipt_kind and not receipt_no:
        errors.append("증빙을 받으시려면 사업자등록번호나 휴대폰 번호를 적어 주세요.")

    coupon_code = sc.clean(request.form.get("coupon"), 40).upper()
    no_mark = bool(request.form.get("no_mark"))
    quote = quote_for(items, data["email"], coupon_code, no_mark)
    subtotal, discount = quote["subtotal"], quote["discount"]
    coupon = quote["coupon"]
    if coupon_code and coupon is None:
        errors.append(quote["coupon_note"])

    if errors:
        return page(request.form, errors, 400, typo)

    names = " + ".join(x["name"] for x in items)
    slugs = [x["slug"] for x in items]
    amount = quote["final"]
    ts = sc.stamp()
    view_key = sc.new_view_key()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, view_key, kind, product_slug, extra_slugs, product_name,
                               quantity, amount, discount, coupon_code, name, phone, email,
                               affiliation, depositor, message, receipt_kind, receipt_no,
                               status, created_at, updated_at, no_mark)
           VALUES (?, ?, 'product', ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?, ?)""",
        lambda no: (no, view_key, slugs[0], ",".join(slugs[1:]) or None, names[:400],
                    amount, discount,
                    coupon["code"] if coupon else None, data["name"], data["phone"],
                    data["email"], data["affiliation"], depositor, data["message"],
                    receipt_kind, receipt_no, ts, ts, 1 if quote["no_mark"] else 0))
    if coupon:
        sc.redeem_coupon(coupon["code"], order_no)
    if from_cart:
        session.pop("cart", None)      # 주문이 들어갔으니 장바구니를 비웁니다

    parts = [f"{r['name']} {r['percent']}%" for r in quote["rows"]]
    if coupon:
        parts.append(f"쿠폰 {coupon['code']}")
    discount_note = " / ".join(parts) or "없음"
    sc.send_mail(
        f"[Ortica영어] 새 주문 {order_no} · {items[0]['name']}"
        + (f" 외 {len(items) - 1}건" if len(items) > 1 else ""),
        "\n".join([f"주문번호 : {order_no}",
                   f"상품     : {names}",
                   f"주문금액 : {subtotal:,}원",
                   f"할인     : -{discount:,}원 ({discount_note})",
                   f"결제금액 : {amount:,}원",
                   f"성함     : {data['name'] or '(안 적음)'}",
                   f"입금자명 : {depositor}",
                   f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}",
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
    db = sc.get_db()
    row = db.execute("SELECT * FROM orders WHERE view_key = ?", (key,)).fetchone()
    if not row:
        abort(404)
    # 자료가 나가면 이 화면에서 바로 받으실 수 있게 링크를 보여 줍니다.
    # (메일을 기다리지 않고 이 주소만 다시 열면 됩니다)
    links = db.execute(
        """SELECT token, product_name FROM downloads
           WHERE order_no = ? AND revoked_at IS NULL ORDER BY id""",
        (row["order_no"],)).fetchall()
    # 이 주소를 연 분은 본인이므로, 자료함 열쇠를 바로 내어 드립니다.
    return render_template("order_done.html", o=row, links=links,
                           locker=sc.locker_token(row["email"]))


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
                   f"성함     : {data['name'] or '(안 적음)'}", f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}"]
                  + [f"{k} : {v}" for k, v in detail.items()]
                  + [f"요청사항 : {data['message'] or '-'}", f"접수시각 : {ts}"]))
    return render_template("custom_done.html", order_no=order_no, mode=mode, wanted=wanted)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """문의하기. 급한 분은 카카오톡·이메일로, 기록이 남아야 하는 분은 이 폼으로."""
    if request.method == "GET":
        return render_template("contact.html", form={}, errors=[], done=None)

    if sc.too_many_submits(request, "contact"):
        return render_template("contact.html", form=request.form,
                               errors=["잠시 뒤에 다시 시도해 주세요."], done=None), 429

    data, errors = sc.validate_contact(request.form)
    topic = request.form.get("topic", "")
    if topic not in sc.INQUIRY_KINDS:
        topic = "etc"
    body = sc.clean(request.form.get("body"), 2000)
    if not body:
        errors.append("문의하실 내용을 적어 주세요.")
    if errors:
        return render_template("contact.html", form=request.form,
                               errors=errors, done=None), 400

    label = sc.INQUIRY_KINDS[topic]
    detail = {"문의 종류": label,
              "주문번호": sc.clean(request.form.get("order_no"), 40) or "-"}
    ts = sc.stamp()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                               name, phone, email, affiliation, message, detail_json,
                               status, created_at, updated_at)
           VALUES (?, 'inquiry', ?, 1, 0, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, f"문의 · {label}", data["name"], data["phone"], data["email"],
                    data["affiliation"], body,
                    json.dumps(detail, ensure_ascii=False), ts, ts))

    sc.send_mail(
        f"[Ortica영어] 문의 {order_no} · {label}",
        "\n".join([f"접수번호 : {order_no}", f"문의 종류 : {label}",
                    f"주문번호 : {detail['주문번호']}",
                    f"성함     : {data['name']}", f"연락처   : {data['phone'] or '-'}",
                    f"이메일   : {data['email']}", "", body, "", f"접수시각 : {ts}"]))
    return render_template("contact.html", form={}, errors=[], done=order_no)


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
                   f"성함     : {data['name'] or '(안 적음)'}", f"연락처   : {data['phone']}",
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

    # 사전 신청가를 미리 계산해 화면에 넘깁니다.
    plans = []
    for pl in cfg.get("plans", []):
        now = sc.preorder_price(cfg, pl)
        price = sc.to_int(pl.get("price"), 0)
        per = sc.to_int(pl.get("per_month"), 0)
        # 깎인 값으로 사면 월 환산도 그만큼 내려갑니다. 정가 기준 숫자를 그대로 두면 앞뒤가 맞지 않습니다.
        plans.append(dict(pl, now=now,
                          per_month_now=round(per * now / price) if price and now < price else per))
    # early = 깎아 드리는 금액. early_names = 그 할인이 붙는 요금제 이름들.
    discounted = [pl for pl in plans if pl["now"] < pl["price"]]
    early = sc.to_int(cfg.get("preorder_discount"), 0) if discounted else 0
    early_names = [pl["name"] for pl in discounted]

    if request.method == "GET":
        return render_template("pass.html", cfg=cfg, plans=plans, early=early, early_names=early_names,
                               form={}, errors=[], done=None)

    data, errors = sc.validate_contact(request.form)
    plan = sc.clean(request.form.get("plan"), 40)
    picked = next((pl for pl in plans if pl["name"] == plan), None)
    if picked is None:
        errors.append("관심 있는 이용권을 골라 주세요.")
    if errors:
        return render_template("pass.html", cfg=cfg, plans=plans, early=early, early_names=early_names,
                               form=request.form, errors=errors, done=None), 400

    ts = sc.stamp()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                               name, phone, email, affiliation, message, detail_json,
                               status, created_at, updated_at)
           VALUES (?, 'pass', ?, 1, 0, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, f"프리패스 사전 신청 · {plan}", data["name"], data["phone"],
                    data["email"], data["affiliation"], data["message"],
                    json.dumps({"관심 이용권": plan,
                                "정가": picked["price"],
                                "사전 신청가": picked["now"],
                                "약속한 할인": early}, ensure_ascii=False), ts, ts))

    sc.send_mail(
        f"[Ortica영어] 프리패스 사전 신청 {order_no} · {plan}",
        "\n".join([f"신청번호 : {order_no}",
                   f"관심 이용권 : {plan} · 사전 신청가 {picked['now']:,}원"
                   + (f" (정가 {picked['price']:,}원 − {early:,}원)" if early else ""),
                   f"성함     : {data['name'] or '(안 적음)'}", f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}",
                   f"하고 싶은 말 : {data['message'] or '-'}", f"접수시각 : {ts}"]))
    return render_template("pass.html", cfg=cfg, plans=plans, early=early, early_names=early_names,
                           form={}, errors=[], done=order_no)


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
@app.route("/lineup/shot/<mid>/<filename>")
def lineup_shot(mid, filename):
    """라인업에 거는 자료 지면 사진. 폴더 밖 파일 요청은 막습니다."""
    folder = sc.shot_dir(mid)
    target = (folder / filename).resolve()
    if not folder.is_dir() or folder.resolve() not in target.parents or not target.is_file():
        abort(404)
    if target.suffix.lower() not in sc.IMAGE_EXTS:
        abort(404)
    return send_from_directory(folder, filename, max_age=86400)


# ---------------------------------------------------------------------------
# 내 자료함 — 받은 자료를 한 곳에서 다시 받고 인쇄
# ---------------------------------------------------------------------------
def locker_rows(email: str):
    """이 이메일로 들어온 자료 주문과, 주문마다 딸린 받기 링크."""
    db = sc.get_db()
    orders = db.execute(
        """SELECT * FROM orders WHERE lower(email) = ? AND kind = 'product'
           ORDER BY id DESC""", (email.strip().lower(),)).fetchall()
    out = []
    for o in orders:
        links = db.execute(
            """SELECT token, product_name, download_count, max_downloads, expires_at
               FROM downloads WHERE order_no = ? AND revoked_at IS NULL ORDER BY id""",
            (o["order_no"],)).fetchall()
        out.append({"o": o, "links": links})
    return out


@app.route("/my", methods=["GET", "POST"])
def my_page():
    """자료함 문 앞. 이메일을 적으면 그 주소로 자료함 열쇠를 보내 드립니다."""
    if request.method == "GET":
        return render_template("my.html", form={}, errors=[], sent=False)

    if sc.too_many_submits(request, "my"):
        return render_template("my.html", form=request.form,
                               errors=["잠시 뒤에 다시 시도해 주세요."], sent=False), 429

    email = sc.clean(request.form.get("email"), 120).lower()
    if not sc.EMAIL_RE.match(email):
        return render_template("my.html", form=request.form, sent=False,
                               errors=["이메일 주소를 정확히 입력해 주세요."]), 400

    # 주문이 있을 때만 실제로 보냅니다. 화면 문구는 어느 쪽이든 같습니다 —
    # 아무 주소나 넣어 보며 "이 사람이 샀는지" 알아내지 못하게 하려는 뜻입니다.
    if locker_rows(email):
        token = sc.locker_token(email)
        link = url_for("my_locker", token=token, _external=True)
        sc.send_mail(
            f"[{sc.load_site().get('brand', 'Ortica영어')}] 내 자료함 주소",
            "\n".join(["받으신 자료를 한 곳에서 다시 받으실 수 있는 주소입니다.", "",
                        link, "",
                        "이 주소는 바뀌지 않습니다. 즐겨찾기 해 두시면 언제든 다시 여실 수 있습니다.",
                        "주소를 아는 사람은 누구나 열 수 있으니 남에게 알려 주지 마세요."]),
            to_addr=email)
    return render_template("my.html", form={}, errors=[], sent=True)


@app.route("/my/<token>")
def my_locker(token):
    """내 자료함. 주소를 아는 분만 열 수 있습니다 (비밀번호 없음)."""
    email = sc.locker_email(token)
    if not email:
        abort(404)
    rows = locker_rows(email)
    paid = sum(1 for r in rows if r["o"]["status"] in ("입금확인", "발송완료"))
    site = sc.load_site()
    tier = sc.loyalty_tier(site, paid)          # 지금 받고 계신 단골 할인
    nxt = sc.loyalty_next(site, paid)           # 한 번 더 사시면 올라가는 단계
    return render_template("my_locker.html", email=email, rows=rows,
                           paid=paid, tier=tier, nxt=nxt, token=token)


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

    name = files[index]["name"]
    path = sc.product_dir(row["product_slug"]) / name

    # 받는 그 자리에서 구매자 표시를 새깁니다. 원본 파일은 그대로 둡니다.
    stamped = watermark_for(row, path)
    if stamped is not None:
        return send_file(io.BytesIO(stamped), mimetype="application/pdf",
                         as_attachment=True, download_name=name)
    return send_from_directory(sc.product_dir(row["product_slug"]), name,
                               as_attachment=True)


def watermark_for(row, path):
    """이 주문의 구매자 표시를 새긴 PDF 바이트. 새길 수 없으면 None."""
    site = sc.load_site()
    cfg = site.get("watermark") or {}
    if not cfg.get("enabled", True):
        return None
    order = sc.get_db().execute(
        "SELECT name, no_mark, created_at FROM orders WHERE order_no = ?",
        (row["order_no"],)).fetchone()
    if order and order["no_mark"]:
        return None                    # 표시 없는 판으로 값을 더 내신 주문
    marks = {
        "이름": (order["name"] if order else "") or "",
        "이메일": row["email"] or "",
        "주문번호": row["order_no"],
        "브랜드": site.get("brand", ""),
        "날짜": (order["created_at"][:10] if order and order["created_at"] else ""),
    }
    # 문구 칸이 아예 없으면(예전 설정 파일) 기본 문구를 씁니다.
    # 관리자가 일부러 비운 경우("")는 그대로 비워 둡니다.
    footer = cfg.get("footer", sc.WATERMARK_DEFAULTS["footer"])
    center = cfg.get("center", sc.WATERMARK_DEFAULTS["center"])
    return wm.stamp(path, sc.fill_marks(footer, marks), sc.fill_marks(center, marks))


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
        "Disallow: /my/",          # 자료함 열쇠 주소는 검색에 잡히면 안 됩니다
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
            url_for("custom", _external=True), url_for("submit", _external=True),
            url_for("contact", _external=True), url_for("my_page", _external=True)]
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

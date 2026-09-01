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
                   send_from_directory, url_for)

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
# 업로드 상한 (상품 자료 ZIP · 시험지 사진)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

app.register_blueprint(admin_bp)
app.teardown_appcontext(sc.close_db)


# ---------------------------------------------------------------------------
# 모든 화면이 함께 쓰는 값 / 서식
# ---------------------------------------------------------------------------
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
@app.route("/")
def home():
    catalog = sc.load_catalog()
    products = catalog["products"]
    featured = [p for p in products if p.get("badge")][:3] or products[:3]
    notices = sc.load_notices()["notices"]
    # 홈에는 분류마다 최대 2권씩 뽑아 어느 분류도 가려지지 않게 합니다.
    picked, per_category = [], {}
    for book in sc.books_with_counts(catalog):
        key = book.get("category", "")
        if per_category.get(key, 0) >= 2:
            continue
        per_category[key] = per_category.get(key, 0) + 1
        picked.append(book)
    groups = sc.grouped_materials()
    all_materials = [m for g in groups for m in g["items"]]
    return render_template("home.html", featured=featured, product_count=len(products),
                           books=picked[:8],
                           lineup_groups=groups, lineup_all=all_materials,
                           material_total=len(all_materials),
                           latest_notice=notices[0] if notices else None)


@app.route("/products")
def products():
    catalog = sc.load_catalog()
    selected = request.args.get("category", "")
    package = request.args.get("package", "")
    items = catalog["products"]
    if selected:
        items = [p for p in items if p.get("category") == selected]
    if package:
        items = [p for p in items if p.get("package") == package]
    return render_template("products.html", items=items,
                           books=sc.books_with_counts(catalog, selected),
                           categories=catalog.get("categories", []), selected=selected,
                           packages=catalog.get("packages", []), selected_package=package)


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
    return render_template("product.html", p=product, book=book,
                           sibling=sibling, related=related)


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
    """자료 라인업 — 우리가 만드는 자료 8종을 한 장에 보여 주는 페이지."""
    data = sc.load_materials()
    return render_template("lineup.html", intro=data.get("intro", {}),
                           groups=sc.grouped_materials())


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

    if request.method == "GET":
        return render_template("order.html", p=product, sibling=sibling, form={}, errors=[])

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
        return render_template("order.html", p=product, sibling=sibling,
                               form=request.form, errors=errors), 400

    amount = subtotal - discount
    ts = sc.stamp()
    order_no = sc.insert_numbered(
        """INSERT INTO orders (order_no, kind, product_slug, extra_slugs, product_name,
                               quantity, amount, discount, coupon_code, name, phone, email,
                               affiliation, depositor, message, receipt_kind, receipt_no,
                               status, created_at, updated_at)
           VALUES (?, 'product', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        lambda no: (no, product["slug"], sibling["slug"] if take_both else None,
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
    return redirect(url_for("order_done", order_no=order_no))


@app.route("/order/done/<order_no>")
def order_done(order_no):
    row = sc.get_db().execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    if not row:
        abort(404)
    return render_template("order_done.html", o=row)


# ---------------------------------------------------------------------------
# 교재 요청 · 맞춤 제작
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

    label = "교재 요청" if mode == "request" else "맞춤 제작 의뢰"
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
# 샘플 · 안내 · 기타
# ---------------------------------------------------------------------------
@app.route("/samples")
def samples():
    catalog = sc.load_catalog()
    items = [p for p in catalog["products"] if p.get("sample_file")]
    ready = {p["sample_file"] for p in items if (sc.SAMPLE_DIR / p["sample_file"]).exists()}
    return render_template("samples.html", items=items, ready=ready)


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
        return render_template("download.html", d=None, files=[], reason=reason), 404
    files = sc.product_files(row["product_slug"])
    return render_template("download.html", d=row, files=files, reason="")


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
    urls = [url_for("home", _external=True), url_for("lineup", _external=True),
            url_for("products", _external=True), url_for("samples", _external=True),
            url_for("notice", _external=True), url_for("guide", _external=True),
            url_for("custom", _external=True), url_for("submit", _external=True)]
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

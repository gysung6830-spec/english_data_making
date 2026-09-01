#!/usr/bin/env python3
"""Ortica영어 - 영어 자료 판매 사이트.

실행:
    pip install -r store_requirements.txt
    python store.py
그다음 브라우저에서  http://localhost:5001  접속.

이 파일은 고객이 보는 '판매 사이트'입니다.
자료를 만드는 내부 도구(webapp.py)와는 완전히 분리되어 있어,
판매 사이트를 인터넷에 올려도 내부 도구나 API 키는 노출되지 않습니다.

바꾸고 싶은 내용은 대부분 코드가 아니라 아래 두 파일에 있습니다.
    store_data/site.json      가게 이름·연락처·입금 계좌·사업자 정보
    store_data/products.json  판매할 상품 목록
자세한 사용법은 STORE.md 를 보세요.
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import sqlite3
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "store_data"
SAMPLE_DIR = DATA_DIR / "samples"
DB_PATH = Path(os.environ.get("STORE_DB") or (DATA_DIR / "store.db"))

KST = timezone(timedelta(hours=9))

app = Flask(__name__, template_folder="store_templates", static_folder="store_static")
app.secret_key = os.environ.get("STORE_SECRET") or secrets.token_hex(16)
app.config["JSON_AS_ASCII"] = False

# 관리자 페이지 비밀번호 (환경변수로 지정). 없으면 관리자 페이지가 잠깁니다.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

ORDER_STATUSES = ["입금대기", "입금확인", "발송완료", "취소"]


# ---------------------------------------------------------------------------
# 설정 파일 읽기
# ---------------------------------------------------------------------------
def _load_json(name: str, fallback: dict) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:  # 설정 파일 오타로 사이트가 죽지 않게
        app.logger.error("%s 를 읽지 못했습니다: %s", name, exc)
        return fallback


def load_site() -> dict:
    site = _load_json("site.json", {})
    # 계좌번호처럼 공개하기 꺼려지는 값은 환경변수로 덮어쓸 수 있습니다.
    if os.environ.get("BANK_ACCOUNT"):
        site.setdefault("payment", {})["bank_account"] = os.environ["BANK_ACCOUNT"]
    return site


def load_catalog() -> dict:
    catalog = _load_json("products.json", {"categories": [], "products": []})
    catalog["products"] = [p for p in catalog.get("products", []) if p.get("active", True)]
    return catalog


@app.context_processor
def inject_globals():
    site = load_site()
    return {
        "site": site,
        "now": datetime.now(KST),
        "nav_categories": load_catalog().get("categories", []),
    }


@app.template_filter("fromjson")
def fromjson(value):
    """관리자 화면에서 맞춤 제작 상세(JSON 문자열)를 표로 펼칠 때 씁니다."""
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


@app.template_filter("won")
def won(value) -> str:
    """12000 -> '12,000원'"""
    try:
        return f"{int(value):,}원"
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# 주문 저장소 (SQLite)
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no      TEXT UNIQUE NOT NULL,
    kind          TEXT NOT NULL DEFAULT 'product',  -- product | custom
    product_slug  TEXT,
    product_name  TEXT,
    quantity      INTEGER NOT NULL DEFAULT 1,
    amount        INTEGER NOT NULL DEFAULT 0,
    name          TEXT NOT NULL,
    phone         TEXT NOT NULL,
    email         TEXT NOT NULL,
    affiliation   TEXT,
    depositor     TEXT,
    message       TEXT,
    detail_json   TEXT,
    status        TEXT NOT NULL DEFAULT '입금대기',
    admin_memo    TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def new_order_no() -> str:
    stamp = datetime.now(KST).strftime("%y%m%d")
    return f"OR-{stamp}-{secrets.randbelow(9000) + 1000}"


# ---------------------------------------------------------------------------
# 주문 알림 메일
# ---------------------------------------------------------------------------
def send_order_mail(subject: str, body: str) -> None:
    """주문이 들어오면 사장님 메일로 보냅니다.

    무료 서버(Render 등)는 재배포할 때 저장 공간이 초기화될 수 있어서,
    주문 내용을 메일로도 남겨 두는 것이 안전합니다.
    SMTP 환경변수가 없으면 조용히 건너뜁니다(로컬 개발 시 정상).
    """
    host = os.environ.get("SMTP_HOST")
    to_addr = os.environ.get("ORDER_EMAIL_TO")
    if not host or not to_addr:
        app.logger.info("SMTP 설정이 없어 주문 알림 메일을 건너뜁니다: %s", subject)
        return

    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    port = int(os.environ.get("SMTP_PORT", "587"))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM") or user or to_addr
    msg["To"] = to_addr
    msg.set_content(body)

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
    except Exception as exc:  # 메일이 실패해도 주문 접수는 성공시킵니다
        app.logger.error("주문 알림 메일 발송 실패: %s", exc)


# ---------------------------------------------------------------------------
# 입력값 확인
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(r"^[0-9\-\+\s]{9,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean(value: str, limit: int = 500) -> str:
    return (value or "").strip()[:limit]


def validate_contact(form) -> tuple[dict, list[str]]:
    data = {
        "name": clean(form.get("name"), 50),
        "phone": clean(form.get("phone"), 30),
        "email": clean(form.get("email"), 120),
        "affiliation": clean(form.get("affiliation"), 80),
        "message": clean(form.get("message"), 2000),
    }
    errors = []
    if not data["name"]:
        errors.append("성함을 입력해 주세요.")
    if not PHONE_RE.match(data["phone"]):
        errors.append("연락처를 숫자와 '-' 로 정확히 입력해 주세요.")
    if not EMAIL_RE.match(data["email"]):
        errors.append("자료를 받으실 이메일 주소를 정확히 입력해 주세요.")
    if not form.get("agree"):
        errors.append("개인정보 수집·이용에 동의해 주셔야 주문이 접수됩니다.")
    return data, errors


# ---------------------------------------------------------------------------
# 고객 페이지
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    catalog = load_catalog()
    products = catalog["products"]
    featured = [p for p in products if p.get("badge")][:3] or products[:3]
    return render_template("home.html", featured=featured, product_count=len(products))


@app.route("/products")
def products():
    catalog = load_catalog()
    selected = request.args.get("category", "")
    items = catalog["products"]
    if selected:
        items = [p for p in items if p.get("category") == selected]
    items = sorted(items, key=lambda p: (p.get("sort", 100), p.get("name", "")))
    return render_template(
        "products.html",
        items=items,
        categories=catalog.get("categories", []),
        selected=selected,
    )


def find_product(slug: str) -> dict | None:
    for product in load_catalog()["products"]:
        if product.get("slug") == slug:
            return product
    return None


@app.route("/products/<slug>")
def product_detail(slug):
    product = find_product(slug)
    if not product:
        abort(404)
    related = [p for p in load_catalog()["products"]
               if p.get("category") == product.get("category") and p.get("slug") != slug][:3]
    return render_template("product.html", p=product, related=related)


@app.route("/order", methods=["GET", "POST"])
def order():
    slug = request.values.get("slug", "")
    product = find_product(slug)
    if not product:
        abort(404)

    if request.method == "GET":
        return render_template("order.html", p=product, form={}, errors=[])

    data, errors = validate_contact(request.form)
    try:
        quantity = max(1, min(99, int(request.form.get("quantity", "1"))))
    except ValueError:
        quantity = 1
        errors.append("수량은 숫자로 입력해 주세요.")
    depositor = clean(request.form.get("depositor"), 50) or data["name"]

    if errors:
        return render_template("order.html", p=product, form=request.form, errors=errors), 400

    order_no = new_order_no()
    amount = int(product.get("price", 0)) * quantity
    stamp = datetime.now(KST).isoformat(timespec="seconds")
    db = get_db()
    db.execute(
        """INSERT INTO orders (order_no, kind, product_slug, product_name, quantity, amount,
                               name, phone, email, affiliation, depositor, message,
                               status, created_at, updated_at)
           VALUES (?, 'product', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        (order_no, product["slug"], product["name"], quantity, amount,
         data["name"], data["phone"], data["email"], data["affiliation"],
         depositor, data["message"], stamp, stamp),
    )
    db.commit()

    send_order_mail(
        f"[Ortica영어] 새 주문 {order_no} · {product['name']}",
        "\n".join([
            f"주문번호 : {order_no}",
            f"상품     : {product['name']} x {quantity}",
            f"금액     : {amount:,}원",
            f"성함     : {data['name']}",
            f"입금자명 : {depositor}",
            f"연락처   : {data['phone']}",
            f"이메일   : {data['email']}",
            f"소속     : {data['affiliation'] or '-'}",
            f"요청사항 : {data['message'] or '-'}",
            f"접수시각 : {stamp}",
        ]),
    )
    return redirect(url_for("order_done", order_no=order_no))


@app.route("/order/done/<order_no>")
def order_done(order_no):
    row = get_db().execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    if not row:
        abort(404)
    return render_template("order_done.html", o=row)


@app.route("/custom", methods=["GET", "POST"])
def custom():
    if request.method == "GET":
        return render_template("custom.html", form={}, errors=[])

    data, errors = validate_contact(request.form)
    detail = {
        "과정": clean(request.form.get("course"), 60),
        "지문 수": clean(request.form.get("passage_count"), 30),
        "원하는 자료": ", ".join(request.form.getlist("materials")) or "-",
        "희망 마감일": clean(request.form.get("due"), 40),
        "지문 파일 링크": clean(request.form.get("file_link"), 300),
    }
    if not detail["지문 수"]:
        errors.append("대략적인 지문 수를 알려 주세요.")
    if errors:
        return render_template("custom.html", form=request.form, errors=errors), 400

    order_no = new_order_no()
    stamp = datetime.now(KST).isoformat(timespec="seconds")
    db = get_db()
    db.execute(
        """INSERT INTO orders (order_no, kind, product_name, quantity, amount,
                               name, phone, email, affiliation, message, detail_json,
                               status, created_at, updated_at)
           VALUES (?, 'custom', '맞춤 제작 의뢰', 1, 0, ?, ?, ?, ?, ?, ?, '입금대기', ?, ?)""",
        (order_no, data["name"], data["phone"], data["email"], data["affiliation"],
         data["message"], json.dumps(detail, ensure_ascii=False), stamp, stamp),
    )
    db.commit()

    send_order_mail(
        f"[Ortica영어] 맞춤 제작 문의 {order_no} · {data['name']}",
        "\n".join([f"문의번호 : {order_no}",
                   f"성함     : {data['name']}",
                   f"연락처   : {data['phone']}",
                   f"이메일   : {data['email']}",
                   f"소속     : {data['affiliation'] or '-'}"]
                  + [f"{k:8s} : {v}" for k, v in detail.items()]
                  + [f"요청사항 : {data['message'] or '-'}", f"접수시각 : {stamp}"]),
    )
    return render_template("custom_done.html", order_no=order_no)


@app.route("/samples")
def samples():
    catalog = load_catalog()
    items = [p for p in catalog["products"] if p.get("sample_file")]
    ready = {p["sample_file"] for p in items if (SAMPLE_DIR / p["sample_file"]).exists()}
    return render_template("samples.html", items=items, ready=ready)


@app.route("/samples/<path:filename>")
def sample_download(filename):
    """무료 샘플 PDF 내려받기. 폴더 밖 파일 요청은 막습니다."""
    target = (SAMPLE_DIR / filename).resolve()
    if SAMPLE_DIR.resolve() not in target.parents or not target.is_file():
        abort(404)
    return send_from_directory(SAMPLE_DIR, filename, as_attachment=True)


@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/healthz")
def healthz():
    return {"ok": True}


@app.errorhandler(404)
def not_found(_exc):
    return render_template("404.html"), 404


# ---------------------------------------------------------------------------
# 관리자 페이지
# ---------------------------------------------------------------------------
def admin_required() -> bool:
    return bool(session.get("admin"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not ADMIN_PASSWORD:
        return render_template("admin_login.html", locked=True, error=None)
    if request.method == "POST":
        # 한글 비밀번호나 한글 입력이 들어와도 터지지 않도록 바이트로 비교합니다.
        typed = request.form.get("password", "").encode("utf-8")
        if secrets.compare_digest(typed, ADMIN_PASSWORD.encode("utf-8")):
            session["admin"] = True
            return redirect(url_for("admin_orders"))
        return render_template("admin_login.html", locked=False,
                               error="비밀번호가 맞지 않습니다."), 401
    return render_template("admin_login.html", locked=False, error=None)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


@app.route("/admin")
def admin_orders():
    if not admin_required():
        return redirect(url_for("admin_login"))
    status = request.args.get("status", "")
    sql = "SELECT * FROM orders"
    params: list = []
    if status in ORDER_STATUSES:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT 300"
    rows = get_db().execute(sql, params).fetchall()

    counts = {s: 0 for s in ORDER_STATUSES}
    for row in get_db().execute("SELECT status, COUNT(*) c FROM orders GROUP BY status"):
        counts[row["status"]] = row["c"]
    waiting_total = get_db().execute(
        "SELECT COALESCE(SUM(amount),0) s FROM orders WHERE status='입금대기'").fetchone()["s"]
    paid_total = get_db().execute(
        "SELECT COALESCE(SUM(amount),0) s FROM orders WHERE status IN ('입금확인','발송완료')"
    ).fetchone()["s"]

    return render_template("admin_orders.html", rows=rows, statuses=ORDER_STATUSES,
                           selected=status, counts=counts,
                           waiting_total=waiting_total, paid_total=paid_total)


@app.route("/admin/orders/<int:order_id>", methods=["POST"])
def admin_update(order_id):
    if not admin_required():
        abort(403)
    status = request.form.get("status", "")
    memo = clean(request.form.get("admin_memo"), 500)
    if status not in ORDER_STATUSES:
        abort(400)
    db = get_db()
    db.execute("UPDATE orders SET status = ?, admin_memo = ?, updated_at = ? WHERE id = ?",
               (status, memo, datetime.now(KST).isoformat(timespec="seconds"), order_id))
    db.commit()
    flash(f"주문 상태를 '{status}' 로 바꿨습니다.")
    return redirect(url_for("admin_orders", status=request.args.get("status", "")))


@app.route("/admin/orders.csv")
def admin_csv():
    """주문 내역 백업용 CSV. 무료 서버는 디스크가 초기화될 수 있으니 가끔 받아 두세요."""
    if not admin_required():
        abort(403)
    import csv
    import io

    rows = get_db().execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["주문번호", "종류", "상품", "수량", "금액", "성함", "연락처", "이메일",
                     "소속", "입금자명", "요청사항", "상세", "상태", "메모", "접수시각"])
    for r in rows:
        writer.writerow([r["order_no"], r["kind"], r["product_name"], r["quantity"], r["amount"],
                         r["name"], r["phone"], r["email"], r["affiliation"], r["depositor"],
                         r["message"], r["detail_json"], r["status"], r["admin_memo"],
                         r["created_at"]])
    csv_bytes = ("﻿" + buf.getvalue()).encode("utf-8")  # 엑셀 한글 깨짐 방지
    stamp = datetime.now(KST).strftime("%Y%m%d")
    return csv_bytes, 200, {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": f'attachment; filename="ortica-orders-{stamp}.csv"',
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    print(f"\n  Ortica영어 판매 사이트 → http://localhost:{port}\n  (종료: Ctrl+C)\n")
    app.run(host="0.0.0.0", port=port, debug=bool(os.environ.get("STORE_DEBUG")))

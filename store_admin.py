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
  /admin/free         무료 자료실 — 회차 자료 올리기
  /admin/leads        무료 자료 받아 가신 분 이메일 명단
  /admin/notices      공지 작성
  /admin/pricing      가격 가이드 — 얼마에 팔지 정하기
  /admin/seo          검색 등록 — 네이버 · 구글에 사이트 알리기
  /admin/settings     가게 정보 · 계좌 · 프리패스 가격
  /admin/backup       백업 내려받기 · 되돌리기
"""
from __future__ import annotations

import io
import csv
import json
import os
import re
import secrets
from datetime import datetime, timedelta

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)

import store_common as sc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 관리자 페이지 비밀번호 (환경변수). 없으면 관리자 페이지가 통째로 잠깁니다.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

MANAGED_FILES = ["site.json", "products.json", "notices.json",
                 "materials.json", "freebies.json", "words.json"]

# 비밀번호를 여러 번 틀리면 잠시 막습니다. (한 대에서 무한정 찍어 보지 못하게)
LOGIN_MAX_TRIES = 8
LOGIN_BLOCK_MINUTES = 15
_login_tries: dict[str, list] = {}


def _client_ip() -> str:
    """Render 같은 곳은 앞단을 거치므로 원래 주소가 헤더에 담겨 옵니다."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.remote_addr) or "?"


def login_blocked() -> int:
    """남은 차단 시간(분). 0이면 막히지 않은 상태입니다."""
    now = sc.now_kst()
    tries = [t for t in _login_tries.get(_client_ip(), [])
             if (now - t).total_seconds() < LOGIN_BLOCK_MINUTES * 60]
    _login_tries[_client_ip()] = tries
    if len(tries) < LOGIN_MAX_TRIES:
        return 0
    left = LOGIN_BLOCK_MINUTES * 60 - (now - tries[0]).total_seconds()
    return max(1, int(left // 60) + 1)


def note_login_failure() -> None:
    _login_tries.setdefault(_client_ip(), []).append(sc.now_kst())


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
    # 관리자 화면은 어떤 경우에도 브라우저·검색엔진이 저장하지 않게 합니다.
    return None


@admin_bp.after_request
def no_store(resp):
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    resp.headers["X-Frame-Options"] = "DENY"          # 다른 사이트에 끼워 넣지 못하게
    return resp


def safe_next(target: str) -> str:
    """로그인 뒤 돌아갈 주소. 우리 관리자 화면 안으로만 보냅니다."""
    if target and target.startswith("/admin") and "//" not in target:
        return target
    return url_for("admin.dashboard")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if not ADMIN_PASSWORD:
        return render_template("admin/login.html", locked=True, error=None, blocked=0)

    blocked = login_blocked()
    if request.method == "POST":
        if blocked:
            return render_template("admin/login.html", locked=False, blocked=blocked,
                                   error=f"비밀번호를 여러 번 틀렸습니다. {blocked}분 뒤에 다시 시도해 주세요."), 429
        # 한글 비밀번호나 한글 입력이 들어와도 터지지 않도록 바이트로 비교합니다.
        typed = request.form.get("password", "").encode("utf-8")
        if secrets.compare_digest(typed, ADMIN_PASSWORD.encode("utf-8")):
            session.clear()                      # 예전 흔적을 지우고 새로 시작
            session["admin"] = True
            session.permanent = True
            _login_tries.pop(_client_ip(), None)
            return redirect(safe_next(request.args.get("next", "")))
        note_login_failure()
        left = LOGIN_MAX_TRIES - len(_login_tries.get(_client_ip(), []))
        hint = f" ({left}번 더 틀리면 {LOGIN_BLOCK_MINUTES}분 동안 막힙니다)" if left <= 3 else ""
        return render_template("admin/login.html", locked=False, blocked=0,
                               error="비밀번호가 맞지 않습니다." + hint), 401
    return render_template("admin/login.html", locked=False, blocked=blocked, error=None)


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
        "증빙발행": one("SELECT COUNT(*) FROM orders WHERE receipt_kind IS NOT NULL"
                     " AND receipt_kind != '' AND receipt_done = 0"
                     " AND status IN ('입금확인','발송완료')"),
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
    steps = setup_steps(sc.load_site(), catalog)
    return render_template("admin/dashboard.html", todo=todo, money=money, counts=counts,
                           recent=recent, subs=subs, steps=steps,
                           done_count=sum(1 for s in steps if s["done"]),
                           sample_count=len([p for p in catalog["products"] if p.get("sample")]))


def setup_steps(site: dict, catalog: dict) -> list[dict]:
    """문을 열기까지 해야 할 일을 순서대로. 끝난 것은 체크 표시가 붙습니다."""
    contact = site.get("contact", {})
    payment = site.get("payment", {})
    business = site.get("business", {})
    products = catalog["products"]

    email_ok = bool(contact.get("email")) and not any(
        x in contact.get("email", "") for x in ("example", "여기에"))
    bank_ok = bool(payment.get("bank_account")) and "0000" not in payment["bank_account"]
    biz_ok = bool(business.get("reg_no")) and "0000" not in business["reg_no"]
    mine = [p for p in products if not p.get("sample")]
    with_files = [p for p in products if sc.has_deliverable(p)]
    with_sample = [m for m in sc.load_materials()["materials"]
                   if m.get("sample_file") and (sc.SAMPLE_DIR / m["sample_file"]).exists()]
    mail_ok = bool(os.environ.get("SMTP_HOST") and os.environ.get("ORDER_EMAIL_TO"))
    free_ready = [x for x in sc.load_freebies()["items"] if sc.free_ready(x)]
    exams_fixed = not sc.load_notices().get("_시험일정안내")
    seo_cfg = site.get("seo") or {}
    seo_ok = bool(seo_cfg.get("naver") or seo_cfg.get("google")
                  or seo_cfg.get("done_naver") or seo_cfg.get("done_google"))

    return [
        {"done": email_ok and bank_ok,
         "title": "연락처와 입금 계좌 넣기",
         "why": "계좌가 예시값이면 주문을 받아도 돈이 안 들어옵니다.",
         "url": url_for("admin.settings"), "label": "가게 정보 열기"},
        {"done": biz_ok,
         "title": "사업자 정보 넣기",
         "why": "온라인으로 팔면 상호·사업자등록번호를 화면에 적어야 합니다.",
         "url": url_for("admin.settings"), "label": "사업자 정보 열기"},
        {"done": bool(mine),
         "title": "내 상품 등록하기",
         "why": (f"지금 보이는 {len(products)}개는 제가 넣어 둔 견본입니다. 실제 자료로 바꿔 주세요."
                 if not mine else "실제 자료를 등록하셨습니다."),
         "url": url_for("admin.products"), "label": "상품 화면 열기"},
        {"done": bool(with_files),
         "title": "상품에 판매할 파일 올리기",
         "why": "이 파일이 실제로 팔리는 물건입니다. 없으면 주문이 와도 보낼 수 없습니다.",
         "url": url_for("admin.products"), "label": "상품 > 📁 파일"},
        {"done": bool(with_sample),
         "title": "자료 샘플 PDF 올리기",
         "why": "사기 전에 눈으로 봐야 지갑이 열립니다. 매출에 가장 크게 영향을 줍니다. "
                "PDF를 store_data/samples/ 에 넣고, 라인업의 자료마다 골라 주세요.",
         "url": url_for("admin.materials"), "label": "오르티카 라인업 열기"},
        {"done": mail_ok,
         "title": "주문 알림 메일 켜기",
         "why": "주문이 오면 바로 알 수 있고, 메일함이 주문 장부가 됩니다.",
         "url": url_for("admin.backup"), "label": "설정 방법 보기"},
        {"done": exams_fixed,
         "title": "시험 일정 실제 날짜로 고치기",
         "why": "홈 첫 화면의 D-day 를 이 날짜로 셉니다. 지금은 예시 날짜가 들어 있습니다.",
         "url": url_for("admin.notices"), "label": "공지 > 시험 일정"},
        {"done": bool(free_ready),
         "title": "무료 자료 한 건 올리기",
         "why": "한줄해석 하나만 올려도 검색으로 들어오는 문이 하나 생깁니다. "
                "공짜로 받아 본 분이 유료 자료를 삽니다.",
         "url": url_for("admin.free_list"), "label": "무료 자료실 열기"},
        {"done": seo_ok,
         "title": "네이버 · 구글에 사이트 등록하기",
         "why": "등록하지 않으면 검색엔진이 이 사이트가 있는 줄도 모릅니다. "
                "검색에 뜨기까지 2주~3개월 걸리니 일찍 해 두세요.",
         "url": url_for("admin.seo"), "label": "검색 등록 열기"},
    ]


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
    writer.writerow(["주문번호", "종류", "상품", "수량", "결제금액", "공급가액", "부가세",
                     "할인", "쿠폰", "증빙종류", "증빙번호", "증빙발행", "성함",
                     "연락처", "이메일", "소속", "입금자명", "요청사항", "상세", "상태",
                     "메모", "접수시각"])
    for r in rows:
        supply, vat = sc.split_vat(r["amount"])
        writer.writerow([r["order_no"], sc.ORDER_KIND_LABELS.get(r["kind"], r["kind"]),
                         r["product_name"], r["quantity"], r["amount"], supply, vat,
                         r["discount"], r["coupon_code"],
                         sc.RECEIPT_KINDS.get(r["receipt_kind"] or "", ""), r["receipt_no"],
                         "완료" if r["receipt_done"] else "", r["name"], r["phone"],
                         r["email"], r["affiliation"], r["depositor"], r["message"],
                         r["detail_json"], r["status"], r["admin_memo"], r["created_at"]])
    body = ("﻿" + buf.getvalue()).encode("utf-8")  # 엑셀 한글 깨짐 방지
    return body, 200, {"Content-Type": "text/csv; charset=utf-8",
                       "Content-Disposition":
                       f'attachment; filename="ortica-orders-{sc.now_kst():%Y%m%d}.csv"'}


# ---------------------------------------------------------------------------
# 상품 파일 · 다운로드 링크 발급
# ---------------------------------------------------------------------------
@admin_bp.route("/products/<slug>/files", methods=["GET", "POST"])
def product_files(slug):
    """손님에게 보낼 파일을 상품마다 올려 둡니다."""
    catalog = sc.load_raw_catalog()
    product = next((p for p in catalog["products"] if p.get("slug") == slug), None)
    if product is None:
        abort(404)

    if request.method == "POST":
        folder = sc.product_dir(slug)
        folder.mkdir(parents=True, exist_ok=True)
        saved = 0
        for upload in request.files.getlist("files"):
            if not upload or not upload.filename:
                continue
            name = os.path.basename(upload.filename).replace("\\", "")
            if os.path.splitext(name)[1].lower() not in sc.DELIVER_EXTS:
                flash(f"'{name}' 은 올릴 수 없는 형식입니다. PDF·ZIP·한글 파일만 됩니다.", "err")
                continue
            upload.save(folder / name)
            saved += 1
        if saved:
            flash(f"파일 {saved}개를 올렸습니다. 이제 이 상품 주문에 다운로드 링크를 낼 수 있습니다.", "ok")
        return redirect(url_for("admin.product_files", slug=slug))

    return render_template("admin/product_files.html", p=product,
                           files=sc.product_files(slug), links=sc.product_links(product))


@admin_bp.route("/products/<slug>/links", methods=["POST"])
def product_links_save(slug):
    """구글 드라이브 같은 바깥 링크를 상품에 걸어 둡니다."""
    catalog = sc.load_raw_catalog()
    product = next((p for p in catalog["products"] if p.get("slug") == slug), None)
    if product is None:
        abort(404)
    links, bad = [], 0
    for name, url in zip(request.form.getlist("link_name"), request.form.getlist("link_url")):
        url = sc.clean(url, 500)
        if not url:
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            bad += 1
            continue
        links.append({"name": sc.clean(name, 120) or "자료 받기", "url": url})
    product["file_links"] = links
    sc.save_catalog(catalog)
    if bad:
        flash(f"주소 {bad}개는 http 로 시작하지 않아 빼 두었습니다. 전체 주소를 붙여 넣어 주세요.", "err")
    else:
        flash(f"링크 {len(links)}개를 저장했습니다.", "ok")
    return redirect(url_for("admin.product_files", slug=slug))


@admin_bp.route("/products/<slug>/files/delete", methods=["POST"])
def product_file_delete(slug):
    name = os.path.basename(sc.clean(request.form.get("name"), 200))
    target = (sc.product_dir(slug) / name).resolve()
    if sc.product_dir(slug).resolve() in target.parents and target.is_file():
        target.unlink()
        flash(f"'{name}' 을 지웠습니다.", "ok")
    return redirect(url_for("admin.product_files", slug=slug))


@admin_bp.route("/orders/<int:order_id>/deliver", methods=["POST"])
def order_deliver(order_id):
    """입금이 확인된 주문에 다운로드 링크를 내고 메일로 보냅니다."""
    db = sc.get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        abort(404)
    slug = row["product_slug"]
    if not slug:
        flash("이 주문에는 상품이 없어 링크를 낼 수 없습니다.", "err")
        return redirect(request.referrer or url_for("admin.orders"))

    # 짝 패키지를 함께 사신 경우 두 상품 모두 링크를 냅니다.
    slugs = [slug] + [x for x in (row["extra_slugs"] or "").split(",") if x]
    catalog = {p["slug"]: p for p in sc.load_raw_catalog()["products"]}
    missing = [x for x in slugs if not sc.has_deliverable(catalog.get(x, {"slug": x}))]
    if missing:
        flash(f"'{catalog.get(missing[0], {}).get('name', missing[0])}' 에 손님께 내어 줄 것이 없습니다. "
              f"파일을 올리거나 자료 링크를 걸어 주세요.", "err")
        return redirect(url_for("admin.product_files", slug=missing[0]))

    links = []
    for one in slugs:
        name = catalog.get(one, {}).get("name", one)
        token = sc.issue_download(row, one, name)
        links.append(f"· {name}\n  " + url_for("download_page", token=token, _external=True))
    link = "\n".join(links)
    sent = sc.send_mail(
        f"[오르티카영어] 주문하신 자료입니다 ({row['order_no']})",
        "\n".join([f"{row['name']}님, 입금 확인했습니다. 감사합니다.", "",
                    f"주문 : {row['product_name']}",
                    "", "아래 주소로 들어가시면 자료를 받으실 수 있습니다.", link, "",
                    f"· 사용 기한 : {sc.DOWNLOAD_DAYS}일",
                    f"· 받을 수 있는 횟수 : {sc.DOWNLOAD_LIMIT}회",
                    "· 링크를 다른 분께 넘기지 말아 주세요. 구매하신 분의 수업에서만 쓰실 수 있습니다.",
                    "", "기한이 지났거나 다시 받아야 하면 편하게 문의해 주세요."]),
        to_addr=row["email"])
    db.execute("UPDATE orders SET status = '발송완료', updated_at = ? WHERE id = ?",
               (sc.stamp(), order_id))
    db.commit()
    flash(("다운로드 링크를 만들어 " + row["email"] + " 로 보냈습니다. 주문은 발송완료로 바꿨습니다.")
          if sent else
          ("다운로드 링크를 만들었습니다. 메일 설정이 없어 자동 발송은 못 했으니 "
           "아래 주소를 손님께 직접 알려 주세요: " + link), "ok")
    return redirect(request.referrer or url_for("admin.orders"))


@admin_bp.route("/downloads/<int:dl_id>/revoke", methods=["POST"])
def download_revoke(dl_id):
    db = sc.get_db()
    db.execute("UPDATE downloads SET revoked_at = ? WHERE id = ?", (sc.stamp(), dl_id))
    db.commit()
    flash("링크를 막았습니다. 이제 그 주소로는 받을 수 없습니다.", "ok")
    return redirect(request.referrer or url_for("admin.orders"))


# ---------------------------------------------------------------------------
# 매출 · 세금
# ---------------------------------------------------------------------------
@admin_bp.route("/sales")
def sales():
    """월별 매출과 증빙 발행 대기 목록. 종합소득세·부가세 신고 때 그대로 씁니다."""
    db = sc.get_db()
    rows = db.execute(
        """SELECT substr(created_at, 1, 7) AS ym, COUNT(*) AS cnt,
                  COALESCE(SUM(amount), 0) AS total,
                  COALESCE(SUM(discount), 0) AS discount
           FROM orders WHERE status IN ('입금확인', '발송완료')
           GROUP BY ym ORDER BY ym DESC""").fetchall()
    months = []
    for r in rows:
        supply, vat = sc.split_vat(r["total"])
        months.append({"ym": r["ym"], "cnt": r["cnt"], "total": r["total"],
                       "discount": r["discount"], "supply": supply, "vat": vat})
    pending = db.execute(
        """SELECT * FROM orders
           WHERE receipt_kind IS NOT NULL AND receipt_kind != '' AND receipt_done = 0
             AND status IN ('입금확인', '발송완료')
           ORDER BY id DESC""").fetchall()
    return render_template("admin/sales.html", months=months, pending=pending,
                           receipt_kinds=sc.RECEIPT_KINDS)


@admin_bp.route("/orders/<int:order_id>/receipt", methods=["POST"])
def order_receipt_done(order_id):
    db = sc.get_db()
    db.execute("UPDATE orders SET receipt_done = 1, updated_at = ? WHERE id = ?",
               (sc.stamp(), order_id))
    db.commit()
    flash("증빙 발행 완료로 표시했습니다.", "ok")
    return redirect(request.referrer or url_for("admin.sales"))


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
            "[오르티카영어] 시험지 감사합니다 — 할인 쿠폰을 보내 드립니다",
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
    # 이 상품이 대신하는 '부분' 상품들. (전권·전회차 상품에만 적습니다)
    known = {p.get("slug") for p in sc.load_raw_catalog()["products"]}
    item["covers"] = [x for x in form.getlist("covers")
                      if x in known and x != item["slug"]]
    # 만든 날짜 — 홈의 '새로 올라왔습니다' 에 이 순서로 나옵니다.
    item.setdefault("added", sc.now_kst().date().isoformat())
    return item, errors


@admin_bp.route("/products")
def products():
    catalog = sc.load_raw_catalog()
    items = sorted(catalog["products"], key=lambda p: (p.get("sort", 100), p.get("name", "")))
    # 샘플 파일이 실제로 폴더에 있는지 미리 확인해 화면에 표시해 줍니다.
    ready = {p["sample_file"] for p in items
             if p.get("sample_file") and (sc.SAMPLE_DIR / p["sample_file"]).exists()}
    counts = {x["slug"]: len(sc.product_files(x["slug"])) + len(sc.product_links(x))
              for x in items if x.get("slug")}
    return render_template("admin/products.html", items=items, catalog=catalog,
                           sample_ready=ready, file_counts=counts,
                           sample_count=len([x for x in items if x.get("sample")]))


def form_hints(catalog: dict) -> dict:
    """상품 폼에서 이름·주소를 자동으로 만들 때 쓰는 표."""
    return {
        "books": {b["slug"]: {"name": b.get("name", ""), "grade": b.get("grade", ""),
                              "category": b.get("category", "")}
                  for b in catalog["books"]},
        "packages": {p["id"]: {"name": p.get("name", ""), "short": p.get("short", ""),
                               "desc": p.get("desc", ""),
                               "materials": p.get("materials", []),
                               "count": len(p.get("materials", []))}
                     for p in catalog["packages"]},
    }


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
                               packages=list(sc.package_map().values()),
                               sample_files=[f.name for f in sorted(sc.SAMPLE_DIR.glob("*"))
                                             if f.is_file() and not f.name.startswith(".")],
                               pricing=sc.pricing_cfg(sc.load_site()),
                               hints=form_hints(catalog))

    item, errors = product_from_form(request.form, existing)
    clash = [p for p in catalog["products"]
             if p.get("slug") == item["slug"] and p is not existing]
    if clash:
        errors.append(f"주소 이름 '{item['slug']}' 은 이미 다른 상품이 쓰고 있습니다.")
    if errors:
        return render_template("admin/product_form.html", p=item, catalog=catalog,
                               errors=errors, is_new=existing is None,
                               all_materials=list(sc.material_map().values()),
                               packages=list(sc.package_map().values()),
                               sample_files=[f.name for f in sorted(sc.SAMPLE_DIR.glob("*"))
                                             if f.is_file() and not f.name.startswith(".")],
                               pricing=sc.pricing_cfg(sc.load_site()),
                               hints=form_hints(catalog)), 400

    if existing is None:
        catalog["products"].append(item)
        flash(f"상품 '{item['name']}' 을(를) 새로 만들었습니다.", "ok")
    else:
        catalog["products"] = [item if p is existing else p for p in catalog["products"]]
        flash(f"상품 '{item['name']}' 을(를) 저장했습니다.", "ok")
    sc.save_catalog(catalog)
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/bulk", methods=["GET", "POST"])
def products_bulk():
    """압축 파일 하나로 상품 여러 개를 한 번에 만듭니다.

    안에 든 PDF 이름에서 '몇 강' 과 '무슨 자료' 인지 읽고, 지문 수 × 자료 단가로
    값을 계산해 상품을 만들고 파일까지 붙입니다. 저장 전에 미리 보여 드립니다.
    """
    catalog = sc.load_raw_catalog()
    site = sc.load_site()
    books = [b for b in catalog["books"] if b.get("active", True) is not False]
    mats = sc.material_map()

    if request.method == "GET":
        return render_template("admin/products_bulk.html", books=books, mats=mats,
                               rows=None, cfg=sc.pricing_cfg(site))

    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("압축 파일(.zip)을 골라 주세요.", "err")
        return redirect(url_for("admin.products_bulk"))
    if not upload.filename.lower().endswith(".zip"):
        flash("압축 파일(.zip)만 올릴 수 있습니다.", "err")
        return redirect(url_for("admin.products_bulk"))

    blob = upload.read()
    rows, skipped = sc.read_zip_products(blob)
    if not rows:
        flash("압축 안에서 만들 수 있는 파일을 찾지 못했습니다. "
              "파일 이름에 '3강'·'지문분석지' 처럼 강과 자료가 들어가야 합니다.", "err")
        return render_template("admin/products_bulk.html", books=books, mats=mats,
                               rows=None, skipped=skipped, cfg=sc.pricing_cfg(site))

    # 압축은 한 번만 올리고, 미리보기에서 저장할 때 다시 씁니다
    sc.BULK_DIR.mkdir(parents=True, exist_ok=True)
    keep = sc.BULK_DIR / f"{sc.new_view_key()}.zip"
    keep.write_bytes(blob)

    units = sorted({(r["no"], r["unit"]) for r in rows})
    return render_template("admin/products_bulk.html", books=books, mats=mats,
                           rows=rows, skipped=skipped, units=units,
                           token=keep.stem, file_name=upload.filename,
                           cfg=sc.pricing_cfg(site))


@admin_bp.route("/products/bulk/save", methods=["POST"])
def products_bulk_save():
    """미리보기에서 확인한 대로 상품을 만들고 파일을 붙입니다."""
    import zipfile

    token = re.sub(r"[^A-Za-z0-9_\-]", "", request.form.get("token", ""))[:80]
    kept = sc.BULK_DIR / f"{token}.zip"
    if not token or not kept.is_file():
        flash("올리신 압축 파일을 찾지 못했습니다. 다시 올려 주세요.", "err")
        return redirect(url_for("admin.products_bulk"))

    catalog = sc.load_raw_catalog()
    site = sc.load_site()
    book = next((b for b in catalog["books"] if b.get("slug") == request.form.get("book")), None)
    if book is None:
        flash("어느 교재의 자료인지 골라 주세요.", "err")
        return redirect(url_for("admin.products_bulk"))

    rates = sc.pricing_cfg(site).get("materials") or {}
    mats = sc.material_map()
    packages = sc.package_map()
    of_package = {m: pid for pid, pkg in packages.items() for m in (pkg.get("materials") or [])}
    taken = {p.get("slug") for p in catalog["products"]}
    default_passages = max(1, sc.to_int(request.form.get("passages"), 6))

    made, files, failed = [], 0, []
    with zipfile.ZipFile(kept) as zf:
        for path in request.form.getlist("path"):
            no, unit = sc.guess_unit(path)
            mid = sc.guess_material(os.path.basename(path))
            if not unit or mid not in mats:
                continue
            # 강마다 지문 수를 따로 적으셨으면 그것을 씁니다
            passages = max(1, sc.to_int(request.form.get(f"p_{no}"), default_passages))
            slug = sc.unique_slug(f"{book['slug']}-{no:02d}-{mid}", taken)
            taken.add(slug)

            item = {
                "slug": slug,
                "name": f"{book['name']} {unit} · {mats[mid]['name']}",
                "subtitle": f"{unit} · 지문 {passages}개",
                "unit": unit,            # 골라 담기 화면에서 줄을 이 이름으로 묶습니다
                "unit_no": no,
                "category": book.get("category", ""),
                "book": book["slug"],
                "package": of_package.get(mid, ""),
                "materials": [mid],
                "passages": passages,
                "price": int(round(rates.get(mid, 0) * passages / 100) * 100),
                "grade": book.get("grade", ""),
                "sort": 100 + no,
                "active": True,
                "delivery": "입금 확인 후 영업일 기준 24시간 이내 이메일 발송",
                "format": "PDF (A4, 인쇄용)",
                "includes": [], "highlights": [], "covers": [],
            }
            catalog["products"].append(item)
            made.append(item)
            try:                                   # 파일을 상품 폴더에 붙입니다
                folder = sc.product_dir(slug)
                folder.mkdir(parents=True, exist_ok=True)
                (folder / sc.safe_filename(os.path.basename(path))).write_bytes(zf.read(path))
                files += 1
            except Exception as exc:
                failed.append(f"{path} — {exc}")

    if not made:
        flash("만들 상품을 고르지 않으셨습니다.", "err")
        return redirect(url_for("admin.products_bulk"))

    sc.save_catalog(catalog)
    kept.unlink(missing_ok=True)
    note = f"상품 {len(made)}개를 만들고 파일 {files}개를 붙였습니다."
    if failed:
        note += f" 파일 {len(failed)}개는 붙이지 못했습니다 — {failed[0]}"
    flash(note, "ok" if not failed else "err")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/clear-samples", methods=["POST"])
def clear_samples():
    """제가 넣어 둔 예시 상품·교재를 한 번에 지웁니다. 직접 만드신 것은 그대로 둡니다."""
    catalog = sc.load_raw_catalog()
    gone_p = len([p for p in catalog["products"] if p.get("sample")])
    gone_b = len([b for b in catalog["books"] if b.get("sample")])
    catalog["products"] = [p for p in catalog["products"] if not p.get("sample")]
    catalog["books"] = [b for b in catalog["books"] if not b.get("sample")]
    sc.save_catalog(catalog)
    flash(f"예시 상품 {gone_p}개와 예시 교재 {gone_b}개를 지웠습니다. "
          f"이제 실제 자료를 등록해 주세요.", "ok")
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
    return render_template("admin/books.html", items=items, catalog=catalog, counts=counts,
                           splits=sc.CATEGORY_SPLITS)


@admin_bp.route("/books/new", methods=["GET", "POST"])
@admin_bp.route("/books/<slug>/edit", methods=["GET", "POST"])
def book_form(slug=None):
    catalog = sc.load_raw_catalog()
    existing = next((b for b in catalog["books"] if b.get("slug") == slug), None)
    if slug and existing is None:
        abort(404)

    if request.method == "GET":
        return render_template("admin/book_form.html", b=existing or {"active": True, "sort": 100},
                               catalog=catalog, errors=[], is_new=existing is None,
                               subject_hints=sc.SUBJECT_HINTS)

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
    item["subject"] = sc.clean(request.form.get("subject"), 30)
    item["sort"] = sc.to_int(request.form.get("sort"), 100)
    item["active"] = bool(request.form.get("active"))
    item["description"] = sc.clean(request.form.get("description"), 1000)

    if [b for b in catalog["books"] if b.get("slug") == item["slug"] and b is not existing]:
        errors.append(f"주소 이름 '{item['slug']}' 은 이미 다른 교재가 쓰고 있습니다.")
    if errors:
        return render_template("admin/book_form.html", b=item, catalog=catalog,
                               errors=errors, is_new=existing is None,
                               subject_hints=sc.SUBJECT_HINTS), 400

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
            split = request.form.get("split", "")
            catalog["categories"].append(
                {"id": cid, "name": name,
                 "split": split if split in sc.CATEGORY_SPLITS else ""})
            sc.save_catalog(catalog)
            flash(f"분류 '{name}' 을(를) 추가했습니다.", "ok")

    elif action == "rename":
        cid = request.form.get("id", "")
        name = sc.clean(request.form.get("name"), 40)
        split = request.form.get("split", "")
        split = split if split in sc.CATEGORY_SPLITS else ""
        for c in catalog["categories"]:
            if c.get("id") == cid and name:
                c["name"] = name
                # 이 분류 안을 무엇으로 한 번 더 가를지. 없으면 그 줄이 안 나옵니다
                c["split"] = split
                c.pop("by_grade", None)
                sc.save_catalog(catalog)
                flash(f"분류 '{name}' 을(를) 저장했습니다."
                      + (f" 손님 화면에 {sc.CATEGORY_SPLITS[split]} 거르기가 나옵니다."
                         if split else " 안을 더 가르지 않습니다."), "ok")
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
# 오르티카 라인업
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
    data["intro"].update({
        "eyebrow": sc.clean(f.get("eyebrow"), 40),
        "headline": sc.clean(f.get("headline"), 200),
        "lead": sc.clean(f.get("lead"), 600),
        "signature_note": sc.clean(f.get("signature_note"), 200),
    })
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

    sample_files = [f.name for f in sorted(sc.SAMPLE_DIR.glob("*"))
                    if f.is_file() and not f.name.startswith(".")]
    if request.method == "GET":
        return render_template("admin/material_form.html", m=item, groups=data["groups"],
                               sample_files=sample_files)

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
    item["sample_file"] = sc.clean(f.get("sample_file"), 120)
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


@admin_bp.route("/materials/<mid>/shots", methods=["GET", "POST"])
def material_shots(mid):
    """자료 지면 사진 올리기. 여기서 올리면 오르티카 라인업에 바로 걸립니다."""
    data = sc.load_materials()
    item = next((m for m in data["materials"] if m.get("id") == mid), None)
    if item is None:
        abort(404)

    if request.method == "POST":
        folder = sc.shot_dir(mid)
        folder.mkdir(parents=True, exist_ok=True)
        saved = 0
        # 올린 순서대로 번호를 붙입니다. 라인업에는 이름 순으로 걸립니다.
        start = len(sc.shot_files(mid)) + 1
        for upload in request.files.getlist("files"):
            if not upload or not upload.filename:
                continue
            raw = os.path.basename(upload.filename).replace("\\", "")
            ext = os.path.splitext(raw)[1].lower()
            if ext not in sc.IMAGE_EXTS:
                flash(f"'{raw}' 은 올릴 수 없는 형식입니다. PNG·JPG·WEBP 만 됩니다.", "err")
                continue
            upload.save(folder / f"{start + saved:02d}{ext}")
            saved += 1
        if saved:
            flash(f"지면 사진 {saved}장을 올렸습니다. 오르티카 라인업에 바로 걸렸습니다.", "ok")
        return redirect(url_for("admin.material_shots", mid=mid))

    return render_template("admin/material_shots.html", m=item, files=sc.shot_files(mid))


@admin_bp.route("/materials/<mid>/shots/<filename>/delete", methods=["POST"])
def material_shot_delete(mid, filename):
    folder = sc.shot_dir(mid)
    target = (folder / filename).resolve()
    if folder.is_dir() and folder.resolve() in target.parents and target.is_file():
        target.unlink()
        flash(f"'{filename}' 을 지웠습니다.", "ok")
    return redirect(url_for("admin.material_shots", mid=mid))


# ---------------------------------------------------------------------------
# 단어장 — 교재 단어를 강 단위로 담아 둡니다
# ---------------------------------------------------------------------------
@admin_bp.route("/words")
def words_list():
    data = sc.load_raw_words()
    books = sorted(data["books"], key=lambda b: (b.get("sort", 100), b.get("name", "")))
    return render_template("admin/words.html", books=books,
                           counts={b["slug"]: sc.word_count(b) for b in books})


@admin_bp.route("/words/new", methods=["POST"])
def words_new():
    data = sc.load_raw_words()
    name = sc.clean(request.form.get("name"), 120)
    if not name:
        flash("단어장 이름을 적어 주세요. 예: 워드마스터 수능2000", "err")
        return redirect(url_for("admin.words_list"))
    if any(b.get("name") == name for b in data["books"]):
        flash("같은 이름의 단어장이 이미 있습니다.", "err")
        return redirect(url_for("admin.words_list"))
    slug = sc.wordbook_slug(name, {b.get("slug") for b in data["books"]})
    data["books"].append({"slug": slug, "name": name,
                          "publisher": sc.clean(request.form.get("publisher"), 60),
                          "sort": sc.to_int(request.form.get("sort"), 100),
                          "active": True, "units": []})
    sc.save_words(data)
    flash(f"'{name}' 단어장을 만들었습니다. 이제 강마다 단어를 넣어 주세요.", "ok")
    return redirect(url_for("admin.words_book", slug=slug))


@admin_bp.route("/words/<slug>", methods=["GET", "POST"])
def words_book(slug):
    """단어장 하나 — 정보 고치기와 강 추가."""
    data = sc.load_raw_words()
    book = next((b for b in data["books"] if b.get("slug") == slug), None)
    if book is None:
        abort(404)

    if request.method == "POST":
        f = request.form
        book["name"] = sc.clean(f.get("name"), 120) or book["name"]
        book["publisher"] = sc.clean(f.get("publisher"), 60)
        book["sort"] = sc.to_int(f.get("sort"), 100)
        book["active"] = bool(f.get("active"))
        sc.save_words(data)
        flash("단어장 정보를 저장했습니다.", "ok")
        return redirect(url_for("admin.words_book", slug=slug))

    return render_template("admin/words_book.html", b=book,
                           total=sc.word_count(book))


@admin_bp.route("/words/<slug>/upload", methods=["POST"])
def words_upload(slug):
    """엑셀 · CSV · PDF 를 올리면 읽어서 미리보기로 넘깁니다.

    바로 저장하지 않습니다. 파일마다 모양이 달라 잘못 읽히는 줄이 있게 마련이라,
    사람이 눈으로 확인하고 고친 뒤 저장하도록 한 단계를 둡니다.
    """
    data = sc.load_raw_words()
    book = next((b for b in data["books"] if b.get("slug") == slug), None)
    if book is None:
        abort(404)

    upload = request.files.get("file")
    if not upload or not upload.filename:
        flash("올릴 파일을 골라 주세요.", "err")
        return redirect(url_for("admin.words_book", slug=slug))
    name = os.path.basename(upload.filename).replace("\\", "")
    if os.path.splitext(name)[1].lower() not in sc.WORD_FILE_EXTS:
        flash(f"'{name}' 은 올릴 수 없는 형식입니다. 엑셀·CSV·PDF·텍스트만 됩니다.", "err")
        return redirect(url_for("admin.words_book", slug=slug))

    text, note = sc.read_wordfile(name, upload.read())
    if not text.strip():
        flash(note or "파일에서 단어를 찾지 못했습니다.", "err")
        return redirect(url_for("admin.words_book", slug=slug))

    blocks = sc.parse_unit_blocks(text)
    if not blocks:
        flash("파일에서 단어를 찾지 못했습니다. 왼쪽이 영어, 오른쪽이 뜻인지 봐 주세요.", "err")
        return redirect(url_for("admin.words_book", slug=slug))

    lines, bad = [], []
    for blk in blocks:
        if blk["name"]:
            lines.append(f"## {blk['name']}")
        lines += [f"{w['en']}\t{w['ko']}" for w in blk["words"]]
        bad += blk["bad"]
    found = sum(len(b["words"]) for b in blocks)
    named = [b for b in blocks if b["name"]]
    return render_template("admin/words_preview.html", b=book, note=note, file_name=name,
                           text="\n".join(lines), blocks=blocks, named=len(named),
                           found=found, bad=bad,
                           unit_name=sc.clean(request.form.get("unit_name"), 60))


@admin_bp.route("/words/<slug>/unit", methods=["POST"])
def words_unit_save(slug):
    """단어를 강에 넣습니다. 있으면 덮어쓰고, 없으면 새로 만듭니다.

    글 안에 '## Day 47' 같은 표시가 있으면 그 자리에서 강을 나눠 한꺼번에 넣습니다.
    표시가 없으면 위에 적으신 강 이름 하나에 통째로 넣습니다.
    """
    data = sc.load_raw_words()
    book = next((b for b in data["books"] if b.get("slug") == slug), None)
    if book is None:
        abort(404)

    text = request.form.get("words", "")
    blocks = sc.parse_unit_blocks(text)
    if not blocks:
        flash("단어를 읽지 못했습니다. 한 줄에 하나씩, 영어와 뜻을 탭이나 쉼표로 나눠 주세요.", "err")
        return redirect(url_for("admin.words_book", slug=slug))

    typed = sc.clean(request.form.get("unit_name"), 60)
    if len(blocks) == 1 and not blocks[0]["name"]:
        if not typed:
            flash("강 이름을 적어 주세요. 예: Day 47 · 1강 · Unit 3", "err")
            return redirect(url_for("admin.words_book", slug=slug))
        blocks[0]["name"] = typed

    saved, bad = [], []
    for blk in blocks:
        uname = blk["name"] or typed
        if not uname:
            continue
        # 같은 이름으로 다시 넣으면 그 강을 덮어씁니다
        same = next((u for u in book["units"] if u.get("name") == uname), None)
        unit = same
        if unit is None:
            unit = {"id": sc.unit_id_from(uname, {u.get("id") for u in book["units"]}),
                    "name": uname, "words": []}
            book["units"].append(unit)
        unit["name"] = uname
        unit["words"] = blk["words"]
        saved.append((uname, len(blk["words"])))
        bad += blk["bad"]

    book["units"].sort(key=lambda u: u.get("id", ""))
    sc.save_words(data)

    if len(saved) == 1:
        note = f"'{saved[0][0]}' 에 단어 {saved[0][1]}개를 넣었습니다."
    else:
        total = sum(n for _, n in saved)
        note = (f"강 {len(saved)}개 · 단어 {total}개를 넣었습니다 — "
                + ", ".join(f"{u}({n})" for u, n in saved[:6])
                + (" …" if len(saved) > 6 else ""))
    if bad:
        note += f" 읽지 못한 줄 {len(bad)}개는 건너뛰었습니다 — {', '.join(bad[:3])}"
    flash(note, "ok" if not bad else "err")
    return redirect(url_for("admin.words_book", slug=slug))


@admin_bp.route("/words/<slug>/unit/<uid>/delete", methods=["POST"])
def words_unit_delete(slug, uid):
    data = sc.load_raw_words()
    book = next((b for b in data["books"] if b.get("slug") == slug), None)
    if book is None:
        abort(404)
    book["units"] = [u for u in book["units"] if u.get("id") != uid]
    sc.save_words(data)
    flash(f"'{uid}' 강을 지웠습니다.", "ok")
    return redirect(url_for("admin.words_book", slug=slug))


@admin_bp.route("/words/<slug>/delete", methods=["POST"])
def words_delete(slug):
    data = sc.load_raw_words()
    data["books"] = [b for b in data["books"] if b.get("slug") != slug]
    sc.save_words(data)
    flash("단어장을 지웠습니다.", "ok")
    return redirect(url_for("admin.words_list"))


# ---------------------------------------------------------------------------
# 공지
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 무료 자료실 — 회차마다 뿌리는 자료 올리기
# ---------------------------------------------------------------------------
@admin_bp.route("/free")
def free_list():
    data = sc.load_raw_freebies()
    items = sorted(data["items"], key=lambda x: (x.get("date", ""), x.get("slug", "")),
                   reverse=True)
    ready = {x["slug"]: len(sc.free_files(x["slug"])) + len(sc.free_links(x))
             for x in items if x.get("slug")}
    leads = sc.get_db().execute("SELECT COUNT(*) AS n FROM leads").fetchone()["n"]
    return render_template("admin/free.html", items=items, ready=ready,
                           kinds=sc.FREE_KINDS, intro=data.get("intro", {}),
                           lead_count=leads,
                           sample_count=len([x for x in items if x.get("sample")]))


@admin_bp.route("/free/intro", methods=["POST"])
def free_intro():
    data = sc.load_raw_freebies()
    data["intro"] = {
        "eyebrow": sc.clean(request.form.get("eyebrow"), 40),
        "headline": sc.clean(request.form.get("headline"), 120),
        "lead": sc.clean(request.form.get("lead"), 400),
        "note": sc.clean(request.form.get("note"), 300),
    }
    sc.save_freebies(data)
    flash("무료 자료실 머리말을 저장했습니다.", "ok")
    return redirect(url_for("admin.free_list"))


def freebie_from_form(form, existing: dict | None = None) -> tuple[dict, list[str]]:
    item = dict(existing or {})
    errors = []
    slug = sc.clean(form.get("slug"), 60).lower()
    if not sc.SLUG_RE.match(slug):
        errors.append("주소 이름(slug)은 영문 소문자·숫자·하이픈으로 3자 이상 적어 주세요. "
                      "예: 2026-03-goh1-oneline")
    item["slug"] = slug
    item["title"] = sc.clean(form.get("title"), 120)
    if not item["title"]:
        errors.append("자료 이름을 적어 주세요.")
    item["summary"] = sc.clean(form.get("summary"), 200)
    item["grade"] = sc.clean(form.get("grade"), 20)
    item["exam"] = sc.clean(form.get("exam"), 60)
    item["kinds"] = [k for k in form.getlist("kinds") if k in sc.FREE_KINDS]
    if not item["kinds"]:
        errors.append("어떤 형식의 자료인지 하나 이상 골라 주세요.")
    gate = sc.clean(form.get("gate"), 10)
    item["gate"] = gate if gate in ("open", "email") else sc.suggested_gate(item["kinds"])
    item["date"] = sc.clean(form.get("date"), 10) or sc.now_kst().date().isoformat()
    item["body"] = sc.clean(form.get("body"), 3000)
    item["image"] = sc.clean(form.get("image"), 120)
    known = {p.get("slug") for p in sc.load_raw_catalog()["products"]}
    item["related"] = [x for x in form.getlist("related") if x in known]
    item["active"] = bool(form.get("active"))
    return item, errors


@admin_bp.route("/free/new", methods=["GET", "POST"])
@admin_bp.route("/free/<slug>/edit", methods=["GET", "POST"])
def free_form(slug=None):
    data = sc.load_raw_freebies()
    existing = next((x for x in data["items"] if x.get("slug") == slug), None)
    if slug and existing is None:
        abort(404)
    catalog = sc.load_raw_catalog()

    def page(item, errors, status=200):
        return render_template("admin/free_form.html", x=item, errors=errors,
                               is_new=existing is None, kinds=sc.FREE_KINDS,
                               gated=sc.FREE_KINDS_GATED,
                               products=catalog["products"],
                               shots=[f.name for f in sorted((sc.ROOT / "store_static" / "free").glob("*"))
                                      if f.is_file() and not f.name.startswith(".")]), status

    if request.method == "GET":
        blank = {"active": True, "gate": "open", "kinds": [], "related": [],
                 "date": sc.now_kst().date().isoformat()}
        body, _ = page(existing or blank, [])
        return body

    item, errors = freebie_from_form(request.form, existing)
    if [x for x in data["items"] if x.get("slug") == item["slug"] and x is not existing]:
        errors.append(f"주소 이름 '{item['slug']}' 은 이미 다른 자료가 쓰고 있습니다.")
    if errors:
        return page(item, errors, 400)

    if existing is None:
        data["items"].append(item)
        flash(f"무료 자료 '{item['title']}' 을(를) 만들었습니다. 이제 파일을 올려 주세요.", "ok")
        sc.save_freebies(data)
        return redirect(url_for("admin.free_files", slug=item["slug"]))

    data["items"] = [item if x is existing else x for x in data["items"]]
    sc.save_freebies(data)
    flash(f"무료 자료 '{item['title']}' 을(를) 저장했습니다.", "ok")
    return redirect(url_for("admin.free_list"))


@admin_bp.route("/free/<slug>/files", methods=["GET", "POST"])
def free_files(slug):
    """무료로 내어 줄 파일을 올립니다."""
    item = sc.find_freebie(slug, raw=True)
    if item is None:
        abort(404)

    if request.method == "POST":
        folder = sc.free_dir(slug)
        folder.mkdir(parents=True, exist_ok=True)
        saved = 0
        for upload in request.files.getlist("files"):
            if not upload or not upload.filename:
                continue
            name = os.path.basename(upload.filename).replace("\\", "")
            if os.path.splitext(name)[1].lower() not in sc.DELIVER_EXTS:
                flash(f"'{name}' 은 올릴 수 없는 형식입니다. PDF·ZIP·한글 파일만 됩니다.", "err")
                continue
            upload.save(folder / name)
            saved += 1
        if saved:
            flash(f"파일 {saved}개를 올렸습니다. 이제 손님이 받으실 수 있습니다.", "ok")
        return redirect(url_for("admin.free_files", slug=slug))

    return render_template("admin/free_files.html", x=item, files=sc.free_files(slug),
                           links=sc.free_links(item))


@admin_bp.route("/free/<slug>/links", methods=["POST"])
def free_links_save(slug):
    data = sc.load_raw_freebies()
    item = next((x for x in data["items"] if x.get("slug") == slug), None)
    if item is None:
        abort(404)
    links, bad = [], 0
    for name, url in zip(request.form.getlist("link_name"), request.form.getlist("link_url")):
        url = sc.clean(url, 500)
        if not url:
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            bad += 1
            continue
        links.append({"name": sc.clean(name, 120) or "자료 받기", "url": url})
    item["file_links"] = links
    sc.save_freebies(data)
    flash(f"주소 {bad}개는 http 로 시작하지 않아 빼 두었습니다." if bad
          else f"링크 {len(links)}개를 저장했습니다.", "err" if bad else "ok")
    return redirect(url_for("admin.free_files", slug=slug))


@admin_bp.route("/free/<slug>/files/delete", methods=["POST"])
def free_file_delete(slug):
    name = os.path.basename(sc.clean(request.form.get("name"), 200))
    target = (sc.free_dir(slug) / name).resolve()
    if sc.free_dir(slug).resolve() in target.parents and target.is_file():
        target.unlink()
        flash(f"'{name}' 을 지웠습니다.", "ok")
    return redirect(url_for("admin.free_files", slug=slug))


@admin_bp.route("/free/<slug>/toggle", methods=["POST"])
def free_toggle(slug):
    data = sc.load_raw_freebies()
    for x in data["items"]:
        if x.get("slug") == slug:
            x["active"] = not x.get("active", True)
            sc.save_freebies(data)
            flash(f"'{x.get('title')}' 을(를) "
                  f"{'보이게' if x['active'] else '숨김으로'} 바꿨습니다.", "ok")
            break
    return redirect(url_for("admin.free_list"))


@admin_bp.route("/free/<slug>/delete", methods=["POST"])
def free_delete(slug):
    data = sc.load_raw_freebies()
    gone = next((x for x in data["items"] if x.get("slug") == slug), None)
    data["items"] = [x for x in data["items"] if x.get("slug") != slug]
    sc.save_freebies(data)
    if gone:
        flash(f"'{gone.get('title')}' 을(를) 지웠습니다. 올린 파일은 그대로 남아 있습니다.", "ok")
    return redirect(url_for("admin.free_list"))


@admin_bp.route("/free/clear-samples", methods=["POST"])
def free_clear_samples():
    data = sc.load_raw_freebies()
    gone = len([x for x in data["items"] if x.get("sample")])
    data["items"] = [x for x in data["items"] if not x.get("sample")]
    sc.save_freebies(data)
    flash(f"예시 무료 자료 {gone}개를 지웠습니다.", "ok")
    return redirect(url_for("admin.free_list"))


# ---------------------------------------------------------------------------
# 프리패스 — 내어 주기 · 남은 지문 보기 · 끊기
# ---------------------------------------------------------------------------
@admin_bp.route("/passes")
def passes():
    db = sc.get_db()
    rows = db.execute("SELECT * FROM passes ORDER BY id DESC LIMIT 300").fetchall()
    used = {r["pass_id"]: r["n"] for r in db.execute(
        "SELECT pass_id, COUNT(*) AS n FROM pass_uses GROUP BY pass_id").fetchall()}
    cfg = sc.load_site().get("pass") or {}
    return render_template("admin/passes.html", rows=rows, used=used,
                           plans=cfg.get("plans") or [], now=sc.stamp())


@admin_bp.route("/passes/new", methods=["POST"])
def pass_new():
    """값을 받으신 분께 프리패스를 내어 줍니다."""
    email = sc.clean(request.form.get("email"), 120).lower()
    if not sc.EMAIL_RE.match(email):
        flash("이메일을 정확히 적어 주세요.", "err")
        return redirect(url_for("admin.passes"))
    quota = max(1, sc.to_int(request.form.get("quota"), 0))
    days = max(1, sc.to_int(request.form.get("days"), 365))
    plan = sc.clean(request.form.get("plan"), 60) or "프리패스"
    sc.grant_pass(email, plan, quota, days,
                  order_no=sc.clean(request.form.get("order_no"), 40),
                  note=sc.clean(request.form.get("note"), 300))
    site = sc.load_site()
    sc.send_mail(
        f"[{site.get('brand', '오르티카영어')}] 프리패스가 열렸습니다",
        "\n".join([f"{plan} 이용권을 열어 드렸습니다.",
                    f"쓰실 수 있는 지문 : {quota:,}개",
                    f"이용 기간 : 오늘부터 {days}일",
                    "",
                    "자료 화면에서 '프리패스로 받기' 를 누르고 이 이메일을 적으시면",
                    "바로 받으실 수 있습니다.",
                    f"남은 지문은 내 자료함에서 보실 수 있습니다 — "
                    f"{url_for('my_locker', token=sc.locker_token(email), _external=True)}"]),
        to_addr=email)
    flash(f"{email} 님께 {plan}({quota:,}지문 · {days}일) 을 열어 드렸습니다. "
          "안내 메일도 보냈습니다.", "ok")
    return redirect(url_for("admin.passes"))


@admin_bp.route("/passes/<int:pass_id>", methods=["POST"])
def pass_update(pass_id):
    """지문 늘려 주기 · 기간 늘리기 · 끊기."""
    db = sc.get_db()
    row = db.execute("SELECT * FROM passes WHERE id = ?", (pass_id,)).fetchone()
    if row is None:
        abort(404)
    action = request.form.get("action")

    if action == "revoke":
        db.execute("UPDATE passes SET revoked_at = ? WHERE id = ?", (sc.stamp(), pass_id))
        flash("이용권을 끊었습니다. 더 이상 자료를 받을 수 없습니다.", "ok")
    elif action == "restore":
        db.execute("UPDATE passes SET revoked_at = NULL WHERE id = ?", (pass_id,))
        flash("이용권을 다시 살렸습니다.", "ok")
    elif action == "add":
        more = max(0, sc.to_int(request.form.get("more_quota"), 0))
        days = max(0, sc.to_int(request.form.get("more_days"), 0))
        if more:
            db.execute("UPDATE passes SET quota = quota + ? WHERE id = ?", (more, pass_id))
        if days:
            ends = max(row["ends_at"], sc.stamp())
            new_end = (datetime.fromisoformat(ends)
                       + timedelta(days=days)).isoformat(timespec="seconds")
            db.execute("UPDATE passes SET ends_at = ? WHERE id = ?", (new_end, pass_id))
        flash(f"지문 {more:,}개, 기간 {days}일을 더해 드렸습니다.", "ok")
    db.commit()
    return redirect(url_for("admin.passes"))


# ---------------------------------------------------------------------------
# 안내 메일 — 명단에 보내기 · 쿠폰 뿌리기 · 장바구니 되살리기
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 지표 — 잘 되고 있는지 숫자로 보기
# ---------------------------------------------------------------------------
@admin_bp.route("/metrics")
def metrics():
    """단위당 평균 몇 명이 사는지. 우리가 목표로 삼은 숫자입니다."""
    db = sc.get_db()
    catalog = sc.load_catalog()
    site = sc.load_site()
    sold = sc.sold_counts()

    live = [p for p in catalog["products"] if p.get("active", True)]
    units = len(live)
    buys = sum(sold.values())
    avg = buys / units if units else 0

    # 자료 하나를 만드는 데 드는 값 — 가격 가이드의 단가에서 거꾸로 셉니다
    cost_p = sc.to_int(site.get("costs", {}).get("per_passage"), 3889)
    passages = sum(sc.to_int(p.get("passages"), 0) for p in live)
    make_cost = passages * cost_p

    money = db.execute(
        """SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt
           FROM orders WHERE status IN ('입금확인', '발송완료')""").fetchone()
    net = int(money["total"] * 0.88)          # 부가세·카드 수수료를 뺀 실수령
    need = (make_cost / (0.88 * (sum(p.get("price", 0) for p in live) or 1))
            if make_cost else 0)

    # 자료별 순위
    by_slug = {p["slug"]: p for p in live}
    rank = sorted(((by_slug[k], v) for k, v in sold.items() if k in by_slug),
                  key=lambda x: -x[1])[:20]
    never = [p for p in live if not sold.get(p["slug"])]

    months = db.execute(
        """SELECT substr(created_at, 1, 7) AS ym, COUNT(*) AS cnt,
                  COALESCE(SUM(amount), 0) AS total
           FROM orders WHERE status IN ('입금확인', '발송완료')
           GROUP BY ym ORDER BY ym DESC LIMIT 12""").fetchall()
    leads = db.execute("SELECT COUNT(DISTINCT lower(email)) AS n FROM leads").fetchone()["n"]
    buyers = db.execute(
        """SELECT COUNT(DISTINCT lower(email)) AS n FROM orders
           WHERE status IN ('입금확인', '발송완료')""").fetchone()["n"]
    passes = db.execute(
        "SELECT COUNT(*) AS n FROM passes WHERE revoked_at IS NULL AND ends_at >= ?",
        (sc.stamp(),)).fetchone()["n"]

    return render_template(
        "admin/metrics.html", units=units, buys=buys, avg=avg, passages=passages,
        cost_p=cost_p, make_cost=make_cost, gross=money["total"], orders=money["cnt"],
        net=net, need=need, rank=rank, never=never, months=months,
        leads=leads, buyers=buyers, passes=passes,
        turn=(leads and buyers / leads * 100) or 0)


# ---------------------------------------------------------------------------
# 빠진 것 점검 — 손님이 살 수 없는 상품 찾아내기
# ---------------------------------------------------------------------------
@admin_bp.route("/checkup")
def checkup():
    """상품 수가 많아지면 눈으로 못 찾습니다. 빠진 것을 한 화면에 모읍니다."""
    catalog = sc.load_raw_catalog()
    site = sc.load_site()
    live = [p for p in catalog["products"] if p.get("active", True)]
    books = {b["slug"]: b for b in catalog["books"]}
    shots = {m["id"]: sc.shot_files(m["id"]) for m in sc.load_materials()["materials"]}

    groups = [
        {"key": "nofile", "name": "받을 파일이 없는 상품", "hurt": True,
         "why": "손님이 사도 내어 줄 것이 없습니다. 값을 받고 못 드립니다.",
         "items": [p for p in live if not sc.has_deliverable(p)]},
        {"key": "noprice", "name": "값이 0원인 상품", "hurt": True,
         "why": "공짜로 나갑니다. 값을 넣어 주세요.",
         "items": [p for p in live if sc.to_int(p.get("price"), 0) <= 0]},
        {"key": "nobook", "name": "교재가 없는 상품", "hurt": True,
         "why": "자료 목록에서 묶이지 않아 따로 떨어져 보입니다.",
         "items": [p for p in live if not books.get(p.get("book") or "")]},
        {"key": "nopassage", "name": "지문 수가 없는 상품", "hurt": False,
         "why": "값 계산과 프리패스 차감이 어긋납니다.",
         "items": [p for p in live if sc.to_int(p.get("passages"), 0) <= 0]},
        {"key": "nosample", "name": "샘플 PDF 가 없는 상품", "hurt": False,
         "why": "미리 볼 것이 없으면 잘 안 삽니다.",
         "items": [p for p in live
                   if not (p.get("sample_file")
                           and (sc.SAMPLE_DIR / p["sample_file"]).exists())]},
        {"key": "nodesc", "name": "설명이 없는 상품", "hurt": False,
         "why": "검색에도 안 걸리고, 무엇인지 알 수 없습니다.",
         "items": [p for p in live if len(p.get("description") or "") < 20]},
    ]
    for g in groups:
        g["items"] = g["items"][:60]

    # 자료 지면 사진이 없는 라인업 자료
    no_shot = [m for m in sc.load_materials()["materials"]
               if m.get("active", True) and not shots.get(m["id"])]
    # 아직 예시값 그대로인 가게 정보
    biz = site.get("business") or {}
    contact = site.get("contact") or {}
    payment = site.get("payment") or {}
    todo = []
    for label, val, bad in (
        ("대표자 이름", biz.get("owner"), "대표자명"),
        ("사업자등록번호", biz.get("reg_no"), "000-00-00000"),
        ("통신판매업 신고번호", biz.get("mailorder_no"), "제0000-지역-0000호"),
        ("사업장 주소", biz.get("address"), "사업장 주소"),
        ("이메일", contact.get("email"), "여기에_이메일@example.com"),
        ("전화번호", contact.get("phone"), "010-0000-0000"),
        ("입금 계좌", payment.get("bank_account"), ""),
    ):
        if not val or val == bad:
            todo.append(label)

    total = sum(len(g["items"]) for g in groups) + len(no_shot) + len(todo)
    store = sc.storage_report()
    if store["on_server"] and not store["safe"]:
        total += 1                      # 자료가 날아갈 상태면 '빠진 것' 하나로 셉니다
    return render_template("admin/checkup.html", groups=groups, no_shot=no_shot,
                           todo=todo, total=total, live=len(live), store=store)


@admin_bp.route("/mail")
def mail_page():
    db = sc.get_db()
    news = len(sc.lead_emails(only_news=True))
    everyone = len(sc.lead_emails(only_news=False))
    left = sc.carts_to_remind()
    past = db.execute("SELECT * FROM mailouts ORDER BY id DESC LIMIT 30").fetchall()
    catalog = sc.load_catalog()
    known = {p["slug"]: p for p in catalog["products"]}
    rows = []
    for r in left:
        picked = [known[x] for x in (r["slugs"] or "").split(",") if x in known]
        rows.append({"r": r, "items": picked})
    return render_template("admin/mail.html", news=news, everyone=everyone,
                           left=rows, past=past, kinds=sc.MAIL_KINDS,
                           ready=sc.mail_ready(), site=sc.load_site())


@admin_bp.route("/mail/news", methods=["POST"])
def mail_news():
    """이메일 명단에 소식·새 자료를 알립니다."""
    if not sc.mail_ready():
        flash("메일 설정(SMTP)이 없어 한 통도 나가지 않습니다. "
              "배포하실 때 SMTP_HOST · SMTP_USER · SMTP_PASS 를 넣어 주세요.", "err")
        return redirect(url_for("admin.mail_page"))
    subject = sc.clean(request.form.get("subject"), 150)
    body = sc.clean(request.form.get("body"), 4000)
    if not subject or not body:
        flash("제목과 내용을 모두 적어 주세요.", "err")
        return redirect(url_for("admin.mail_page"))

    site = sc.load_site()
    only = request.form.get("who") != "all"
    to_list = sc.lead_emails(only_news=only)
    if not to_list:
        flash("보낼 곳이 없습니다. 무료 자료실로 이메일이 쌓이면 여기서 보내실 수 있습니다.", "err")
        return redirect(url_for("admin.mail_page"))

    if request.form.get("test") == "1":       # 나에게만 한 통 보내 보기
        to_list = [sc.clean(request.form.get("test_to"), 120).lower()]
        if not sc.EMAIL_RE.match(to_list[0]):
            flash("시험 삼아 보낼 이메일을 적어 주세요.", "err")
            return redirect(url_for("admin.mail_page"))

    tail = ("\n\n---\n"
            f"{site.get('brand', '오르티카영어')}\n"
            f"{url_for('home', _external=True)}\n"
            "이 메일이 필요 없으시면 회신 주시면 명단에서 빼 드리겠습니다.")

    sent, failed = sc.send_batch("news", subject, lambda _a: body + tail, to_list,
                                 note=("시험 발송" if request.form.get("test") == "1"
                                       else f"{'소식 받기 신청자' if only else '전체'}"))
    flash(f"{sent}통 보냈습니다." + (f" {failed}통은 실패했습니다." if failed else ""),
          "ok" if not failed else "err")
    return redirect(url_for("admin.mail_page"))


@admin_bp.route("/mail/coupon", methods=["POST"])
def mail_coupon():
    """명단에 쿠폰을 한 번에 뿌립니다. 사람마다 다른 번호가 나갑니다."""
    if not sc.mail_ready():
        flash("메일 설정(SMTP)이 없어 한 통도 나가지 않습니다. "
              "배포하실 때 SMTP_HOST · SMTP_USER · SMTP_PASS 를 넣어 주세요.", "err")
        return redirect(url_for("admin.mail_page"))
    kind = "percent" if request.form.get("kind") == "percent" else "amount"
    value = max(1, sc.to_int(request.form.get("value"), 0))
    days = max(1, sc.to_int(request.form.get("days"), 30))
    min_amount = max(0, sc.to_int(request.form.get("min_amount"), 0))
    note = sc.clean(request.form.get("note"), 100) or "정기 쿠폰"
    subject = sc.clean(request.form.get("subject"), 150) or f"[{note}] 할인 쿠폰을 보내 드립니다"
    intro = sc.clean(request.form.get("body"), 3000)

    to_list = sc.lead_emails(only_news=request.form.get("who") != "all")
    if not to_list:
        flash("보낼 곳이 없습니다.", "err")
        return redirect(url_for("admin.mail_page"))
    if len(to_list) > 2000:
        flash("한 번에 2,000명까지 보낼 수 있습니다.", "err")
        return redirect(url_for("admin.mail_page"))

    site = sc.load_site()
    label = f"{value}%" if kind == "percent" else f"{value:,}원"

    made_for: dict[str, str] = {}     # 누구에게 어떤 번호를 만들었는지

    def body_for(addr: str) -> str:
        code = sc.issue_coupon(kind, value, min_amount=min_amount, note=note,
                               issued_to=addr, days_valid=days)
        made_for[addr] = code
        lines = [intro, "", f"쿠폰 번호 : {code}", f"할인 : {label}"]
        if min_amount:
            lines.append(f"{min_amount:,}원 이상 주문에 쓰실 수 있습니다.")
        lines += [f"쓰실 수 있는 기간 : 오늘부터 {days}일",
                  "", "주문서 맨 아래 '할인 쿠폰' 칸에 번호를 넣으시면 됩니다.",
                  url_for("products", _external=True),
                  "", "---", site.get("brand", "오르티카영어")]
        return "\n".join(x for x in lines if x is not None)

    def drop(addr: str) -> None:
        """못 보낸 쿠폰은 도로 지웁니다. 손에 없는 번호가 쌓이면 안 됩니다."""
        code = made_for.pop(addr, "")
        if code:
            db = sc.get_db()
            db.execute("DELETE FROM coupons WHERE code = ? AND used_at IS NULL", (code,))
            db.commit()

    sent, failed = sc.send_batch("coupon", subject, body_for, to_list,
                                 note=f"{note} · {label} · {days}일", on_fail=drop)
    flash(f"쿠폰 {sent}장을 보냈습니다."
          + (f" {failed}장은 못 보내서 도로 지웠습니다." if failed else ""),
          "ok" if not failed else "err")
    return redirect(url_for("admin.mail_page"))


@admin_bp.route("/mail/cart", methods=["POST"])
def mail_cart():
    """담아만 두고 안 사신 분들께 한 번만 알려 드립니다."""
    if not sc.mail_ready():
        flash("메일 설정(SMTP)이 없어 한 통도 나가지 않습니다. "
              "배포하실 때 SMTP_HOST · SMTP_USER · SMTP_PASS 를 넣어 주세요.", "err")
        return redirect(url_for("admin.mail_page"))
    rows = sc.carts_to_remind(sc.to_int(request.form.get("hours"), 24))
    if not rows:
        flash("알려 드릴 분이 없습니다.", "err")
        return redirect(url_for("admin.mail_page"))

    site = sc.load_site()
    catalog = sc.load_catalog()
    known = {p["slug"]: p for p in catalog["products"]}
    body_of = {}
    for r in rows:
        picked = [known[x]["name"] for x in (r["slugs"] or "").split(",") if x in known]
        body_of[r["email"]] = "\n".join([
            "장바구니에 담아 두신 자료가 있습니다.", "",
            *[f"· {n}" for n in picked[:10]],
            "", f"예상 금액 {sc.to_int(r['amount'], 0):,}원",
            "", "아래 주소에서 이어서 주문하실 수 있습니다.",
            url_for("products", _external=True),
            "", "---", site.get("brand", "오르티카영어")])

    sent, failed = sc.send_batch(
        "cart", "장바구니에 담아 두신 자료가 있습니다",
        lambda addr: body_of.get(addr, ""), list(body_of), note=f"{len(rows)}명")
    db = sc.get_db()
    db.executemany("UPDATE carts_left SET reminded_at = ? WHERE email = ?",
                   [(sc.stamp(), e) for e in body_of])
    db.commit()
    flash(f"{sent}분께 알려 드렸습니다." + (f" {failed}통 실패." if failed else ""),
          "ok" if not failed else "err")
    return redirect(url_for("admin.mail_page"))


@admin_bp.route("/leads")
def leads():
    """무료 자료를 받아 가시며 남긴 이메일 명단."""
    rows = sc.lead_rows(500)
    news = [r for r in rows if r["news"]]
    return render_template("admin/leads.html", rows=rows, news_count=len(news))


@admin_bp.route("/leads.csv")
def leads_csv():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["이메일", "성함", "받아 간 자료", "알림 신청", "남긴 날짜"])
    for r in sc.lead_rows(5000):
        writer.writerow([r["email"], r["name"] or "", r["title"] or "",
                         "예" if r["news"] else "", r["created_at"]])
    data = "\ufeff" + buf.getvalue()      # 엑셀에서 한글이 깨지지 않게
    return data, 200, {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=ortica-emails.csv",
    }


@admin_bp.route("/notices")
def notices():
    data = sc.load_notices()
    return render_template("admin/notices.html",
                           exam_note=bool(data.get("_시험일정안내")), **data)


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


@admin_bp.route("/notices/exams", methods=["POST"])
def exams_save():
    """시험 일정 — 홈의 'D-day' 는 여기 날짜로 셉니다."""
    data = sc.load_notices()
    rows = []
    for i, (date, name) in enumerate(zip(request.form.getlist("exam_date"),
                                         request.form.getlist("exam_name"))):
        date = sc.clean(date, 10)
        name = sc.clean(name, 60)
        if not date or not name:
            continue
        grades = [g for g in request.form.getlist(f"exam_grades_{i}")
                  if g in ("고1", "고2", "고3")]
        rows.append({"date": date, "name": name, "grades": grades})
    rows.sort(key=lambda r: r["date"])
    data["exams"] = rows
    data.pop("_시험일정안내", None)      # 예시 안내문은 한 번 저장하면 지웁니다
    sc.save_notices(data)
    flash(f"시험 일정 {len(rows)}개를 저장했습니다. 홈의 D-day 가 바로 바뀝니다.", "ok")
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
        return render_template("admin/settings.html", s=site,
                           delivery_modes=sc.DELIVERY_MODES)

    f = request.form
    site["brand"] = sc.clean(f.get("brand"), 60) or site.get("brand", "오르티카영어")
    site["brand_en"] = sc.clean(f.get("brand_en"), 40) or site.get("brand_en", "Ortica")
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
    pass_cfg["preorder_discount"] = max(0, sc.to_int(f.get("pass_preorder_discount"), 0))
    plans = []
    for name, price, per, period, quota, early, badge, desc in zip(
            f.getlist("plan_name"), f.getlist("plan_price"), f.getlist("plan_per_month"),
            f.getlist("plan_period"), f.getlist("plan_passages"), f.getlist("plan_early"),
            f.getlist("plan_badge"), f.getlist("plan_desc")):
        if not sc.clean(name, 40):
            continue
        plan = {"name": sc.clean(name, 40), "price": sc.to_int(price, 0),
                "per_month": sc.to_int(per, 0), "period": sc.clean(period, 30),
                "passages": max(0, sc.to_int(quota, 0)),
                "early": early == "1", "desc": sc.clean(desc, 200)}
        if sc.clean(badge, 20):
            plan["badge"] = sc.clean(badge, 20)
        plans.append(plan)
    if plans:
        pass_cfg["plans"] = plans

    # 구매자 표시 (워터마크)
    mark = site.setdefault("watermark", {})
    mark["enabled"] = bool(f.get("watermark_enabled"))
    mark["footer"] = sc.clean(f.get("watermark_footer"), 200)
    mark["center"] = sc.clean(f.get("watermark_center"), 80)
    # '값을 더 내면 표시 없이' 는 없앴습니다. 손님에게 표시 이야기를 아예 안 합니다.
    for gone in ("optout_enabled", "optout_price", "optout_max"):
        mark.pop(gone, None)

    # 자료를 어떻게 내어 줄지 — 화면 인쇄 / 파일 받기
    dv = site.setdefault("delivery", {})
    mode = f.get("delivery_mode", "view")
    dv["mode"] = mode if mode in sc.DELIVERY_MODES else "view"
    dv["note"] = sc.clean(f.get("delivery_note"), 400)

    # 자동 할인 — 담은 개수 하나뿐입니다 (단골 할인은 없앴습니다)
    disc = site.setdefault("discount", {})
    disc["count_enabled"] = bool(f.get("discount_count_enabled"))
    tiers = []
    for need, pct in zip(f.getlist("count_min"), f.getlist("count_percent")):
        need, pct = sc.to_int(need, 0), sc.to_int(pct, 0)
        if need >= 2 and 0 < pct <= 50:
            tiers.append({"min": need, "percent": pct})
    disc["count_tiers"] = sorted(tiers, key=lambda t: t["min"])
    disc["max_percent"] = max(0, min(70, sc.to_int(f.get("discount_max_percent"), 20)))
    for gone in ("bundle_enabled", "bundle_percent", "loyalty_enabled", "loyalty"):
        disc.pop(gone, None)

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
# ---------------------------------------------------------------------------
# 검색 등록 — 네이버 · 구글에 사이트를 알리기
# ---------------------------------------------------------------------------
VERIFY_RE = re.compile(r'content\s*=\s*["\']([^"\']+)["\']')


def verify_code(raw: str) -> str:
    """붙여 넣은 값에서 확인 코드만 뽑아냅니다.

    네이버·구글이 주는 것은 <meta ... content="코드"> 통째입니다.
    통째로 붙여 넣으셔도 되고, 코드만 붙여 넣으셔도 되게 합니다.
    """
    raw = sc.clean(raw, 400)
    found = VERIFY_RE.search(raw)
    code = (found.group(1) if found else raw).strip()
    return re.sub(r"[^A-Za-z0-9_\-\.]", "", code)[:120]


@admin_bp.route("/seo", methods=["GET", "POST"])
def seo():
    site = sc.load_site()
    if request.method == "POST":
        seo_cfg = dict(site.get("seo") or {})
        # 검색 결과에 뜨는 제목·설명.
        # 폼에 그 칸이 없을 때(다른 화면에서 저장할 때)는 지우지 않고 그대로 둡니다.
        if "seo_title" in request.form:
            seo_cfg["title"] = sc.clean(request.form.get("seo_title"), 70)
        if "seo_description" in request.form:
            seo_cfg["description"] = sc.clean(request.form.get("seo_description"), 200)
        seo_cfg["naver"] = verify_code(request.form.get("naver"))
        seo_cfg["google"] = verify_code(request.form.get("google"))
        seo_cfg["done_naver"] = bool(request.form.get("done_naver"))
        seo_cfg["done_google"] = bool(request.form.get("done_google"))
        seo_cfg["done_daum"] = bool(request.form.get("done_daum"))
        site["seo"] = seo_cfg
        sc.save_site(site)
        flash("검색 등록 정보를 저장했습니다.", "ok")
        return redirect(url_for("admin.seo"))

    catalog = sc.load_catalog()
    freebies = sc.load_freebies()["items"]
    page_count = (9 + len(catalog["products"]) + len(catalog["books"])
                  + len([x for x in freebies if x.get("active", True)]))
    return render_template("admin/seo.html", seo=site.get("seo") or {},
                           home_url=url_for("home", _external=True).rstrip("/"),
                           page_count=page_count,
                           free_count=len(freebies))


# ---------------------------------------------------------------------------
# 가격 가이드 — 얼마에 팔지 정할 때 보는 화면
# ---------------------------------------------------------------------------
def per_passage_rows(catalog: dict, site: dict) -> list[dict]:
    """상품마다 '지문 하나에 얼마인지' 를 뽑습니다. 우리 정가와 얼마나 벌어졌는지 봅니다."""
    units = sc.pricing_cfg(site)["units"]
    rows = []
    for item in catalog["products"]:
        passages = sc.to_int(item.get("passages"), 0)
        price = sc.to_int(item.get("price"), 0)
        if passages <= 0 or price <= 0:
            continue
        unit = price // passages
        want = units.get(item.get("package"), 0)
        should = sc.suggested_price(site, item.get("package", ""), passages)
        gap = price - should if should else 0
        rows.append({"name": item.get("name", ""), "slug": item.get("slug", ""),
                     "package": item.get("package", ""), "passages": passages,
                     "price": price, "unit": unit, "want": want,
                     "should": should, "gap": gap,
                     # 전권·전회차 상품은 일부러 싸게 잡는 것이라 '벌어졌다' 고 보지 않습니다
                     "is_full": bool(item.get("covers")),
                     "sample": bool(item.get("sample"))})
    return sorted(rows, key=lambda r: (r["package"], -abs(r["gap"])))


@admin_bp.route("/pricing", methods=["GET", "POST"])
def pricing():
    site = sc.load_site()
    catalog = sc.load_raw_catalog()
    packages = list(sc.package_map().values())

    # 패키지에 든 자료 목록 (지문 분석 3종 · 문제 3종)
    mats = {m.get("id"): m for m in (sc.load_materials().get("materials") or [])}

    if request.method == "POST":
        cfg = sc.pricing_cfg(site)
        # 자료 1종마다 지문당 단가를 받고, 패키지 값은 그 합으로 자동 계산합니다
        rates = dict(cfg.get("materials") or {})
        for mid in mats:
            got = request.form.get(f"mat_{mid}")
            if got is not None:
                rates[mid] = max(0, min(100000, sc.to_int(got, 0)))
        cfg["materials"] = rates
        cfg["units"] = {pkg["id"]: sum(rates.get(m, 0) for m in (pkg.get("materials") or []))
                        for pkg in packages}
        cfg["round_to"] = max(1, min(10000, sc.to_int(request.form.get("round_to"), 100)))
        cfg["full_pack_percent"] = max(50, min(100,
                                               sc.to_int(request.form.get("full_pack_percent"), 85)))
        site["pricing"] = cfg
        sc.save_site(site)
        flash("우리 정가를 저장했습니다. 상품 만들 때 이 값으로 계산해 드립니다.", "ok")
        return redirect(url_for("admin.pricing"))

    rows = per_passage_rows(catalog, site)
    off = [r for r in rows
           if r["should"] and abs(r["gap"]) >= 1000 and not r["is_full"]]
    return render_template("admin/pricing.html", rows=rows, off=off,
                           cfg=sc.pricing_cfg(site), packages=packages,
                           mats=mats, package_map=sc.package_map(), site=site)


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


@admin_bp.route("/backup/full")
def backup_full():
    """전부 담은 백업 — 설정 · 주문 내역 · 이메일 명단 · 주문 장부 원본을 한 묶음으로.

    설정만 받아 두면 주문이 날아갑니다. 주문은 되돌릴 수 없는 기록이라 함께 담습니다.
    """
    import zipfile
    stamp = f"{sc.now_kst():%Y%m%d-%H%M}"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in MANAGED_FILES:
            z.writestr(f"설정/{name}",
                       json.dumps(sc.load_json(name, {}), ensure_ascii=False, indent=2))
        z.writestr("주문내역.csv", orders_csv()[0])
        z.writestr("이메일명단.csv", leads_csv()[0])
        if sc.DB_PATH.exists():                       # 장부 원본 (되살릴 때 이것만 있으면 됩니다)
            z.write(sc.DB_PATH, "store.db")
        z.writestr("읽어주세요.txt",
                   f"오르티카 영어 전체 백업 · {sc.stamp()}\n\n"
                   "· 설정/ 안의 파일들 → 관리자 > 백업 에서 '되돌리기'로 올리면 복구됩니다.\n"
                   "  (되돌리기는 json 파일 하나를 받으므로, 관리자 > 백업 의 '설정만 받기'로\n"
                   "   받은 파일을 쓰시는 편이 간단합니다.)\n"
                   "· 주문내역.csv → 엑셀로 바로 열립니다.\n"
                   "· store.db → 주문 장부 원본입니다. 서버가 초기화됐을 때 이 파일을\n"
                   "  store_data/ 에 그대로 넣으면 주문이 모두 살아납니다.\n\n"
                   "이 묶음에 들어 있지 않은 것: 무료 자료실에 올린 PDF, 상품 전달 파일,\n"
                   "라인업 지면 사진. 원본을 컴퓨터에 갖고 계신 파일들입니다.\n")
    return buf.getvalue(), 200, {
        "Content-Type": "application/zip",
        "Content-Disposition": f'attachment; filename="ortica-backup-{stamp}.zip"'}


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

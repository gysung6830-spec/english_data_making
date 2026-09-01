#!/usr/bin/env python3
"""판매 사이트의 공용 부품 — 설정 파일 읽기/쓰기, 주문 DB, 쿠폰, 메일.

고객 화면(store.py)과 관리자 화면(store_admin.py)이 함께 씁니다.
여기만 이해하면 데이터가 어디에 어떻게 쌓이는지 다 알 수 있습니다.

  store_data/site.json      가게 정보 (연락처·계좌·사업자·프리패스 가격)
  store_data/products.json  분류 · 교재 · 상품
  store_data/notices.json   공지 · 업데이트 일정
  store_data/store.db       주문 · 쿠폰 · 시험지 제출 (SQLite)
  store_data/freebies.json  무료 자료실 (한줄해석 · 한줄영어 · 좌지문우해석 …)
  store_data/submissions/   올려 주신 시험지 파일
"""
from __future__ import annotations

import json
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import current_app, g

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "store_data"
SAMPLE_DIR = DATA_DIR / "samples"
SUBMIT_DIR = DATA_DIR / "submissions"
DELIVER_DIR = DATA_DIR / "deliverables"   # 상품별로 손님에게 보낼 파일
FREE_DIR = DATA_DIR / "free"              # 무료 자료실에 올린 파일
DB_PATH = Path(os.environ.get("STORE_DB") or (DATA_DIR / "store.db"))

KST = timezone(timedelta(hours=9))

ORDER_STATUSES = ["입금대기", "입금확인", "발송완료", "취소"]
SUBMIT_STATUSES = ["검토대기", "승인", "반려"]
ORDER_KIND_LABELS = {"product": "자료 주문", "custom": "맞춤 제작",
                     "request": "자료 요청", "pass": "프리패스"}

# 세금 신고에 필요한 증빙 종류
RECEIPT_KINDS = {
    "": "필요 없음",
    "cash_personal": "현금영수증 (소득공제·개인)",
    "cash_business": "현금영수증 (지출증빙·사업자)",
    "tax_invoice": "세금계산서 (사업자)",
}

DOWNLOAD_DAYS = 30      # 다운로드 링크가 살아 있는 기간
DOWNLOAD_LIMIT = 20     # 한 링크로 받을 수 있는 횟수


def now_kst() -> datetime:
    return datetime.now(KST)


def stamp() -> str:
    return now_kst().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# 설정 파일 읽기 / 쓰기
# ---------------------------------------------------------------------------
def load_json(name: str, fallback: dict) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return json.loads(json.dumps(fallback))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:  # 설정 파일 오타로 사이트가 죽지 않게
        try:
            current_app.logger.error("%s 를 읽지 못했습니다: %s", name, exc)
        except RuntimeError:
            pass
        return json.loads(json.dumps(fallback))


def save_json(name: str, data: dict) -> None:
    """중간에 멈춰도 파일이 깨지지 않도록 임시 파일에 쓴 뒤 바꿔치기합니다."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


SITE_FALLBACK = {"brand": "Ortica영어", "contact": {}, "payment": {},
                 "business": {}, "policy": {}, "pass": {}}
CATALOG_FALLBACK = {"categories": [], "packages": [], "books": [], "products": []}
NOTICE_FALLBACK = {"schedule": [], "notices": [], "exams": []}


def load_site() -> dict:
    site = load_json("site.json", SITE_FALLBACK)
    for key in ("contact", "payment", "business", "policy", "pass"):
        site.setdefault(key, {})
    # 계좌번호처럼 공개하기 꺼려지는 값은 환경변수로 덮어쓸 수 있습니다.
    if os.environ.get("BANK_ACCOUNT"):
        site["payment"]["bank_account"] = os.environ["BANK_ACCOUNT"]
    return site


def save_site(site: dict) -> None:
    save_json("site.json", site)


def load_raw_catalog() -> dict:
    """숨긴 항목까지 전부. 관리자 화면에서 씁니다."""
    catalog = load_json("products.json", CATALOG_FALLBACK)
    for key in ("categories", "packages", "books", "products"):
        catalog.setdefault(key, [])
    catalog["packages"] = sorted(catalog["packages"], key=lambda x: x.get("sort", 100))
    return catalog


def save_catalog(catalog: dict) -> None:
    save_json("products.json", catalog)


def load_catalog() -> dict:
    """고객에게 보여 줄 것만. 숨김(active=false) 항목은 빠집니다."""
    catalog = load_raw_catalog()
    catalog["products"] = sorted(
        [p for p in catalog["products"] if p.get("active", True)],
        key=lambda p: (p.get("sort", 100), p.get("name", "")),
    )
    catalog["books"] = sorted(
        [b for b in catalog["books"] if b.get("active", True)],
        key=lambda b: (b.get("sort", 100), b.get("name", "")),
    )
    return catalog


MATERIALS_FALLBACK = {"intro": {}, "groups": [], "materials": []}


def load_materials() -> dict:
    """오르티카 라인업(지문자료 · 지문분석지 · 워크북 …)."""
    data = load_json("materials.json", MATERIALS_FALLBACK)
    for key in ("groups", "materials"):
        data.setdefault(key, [])
    data.setdefault("intro", {})
    return data


def save_materials(data: dict) -> None:
    save_json("materials.json", data)


def material_map() -> dict:
    """상품에 붙은 자료 id 를 이름으로 바꿀 때 씁니다."""
    return {m["id"]: m for m in load_materials()["materials"] if m.get("active", True)}


def grouped_materials() -> list[dict]:
    """그룹마다 그 그룹의 자료를 담아 돌려줍니다. 라인업 페이지가 이 모양으로 그립니다."""
    data = load_materials()
    items = [m for m in data["materials"] if m.get("active", True)]
    out = []
    for group in data["groups"]:
        picked = [m for m in items if m.get("group") == group.get("id")]
        if picked:
            out.append({**group, "items": picked})
    orphan = [m for m in items if m.get("group") not in {g.get("id") for g in data["groups"]}]
    if orphan:
        out.append({"id": "", "range": "", "name": "그 밖의 자료",
                    "headline": "", "lead": "", "items": orphan})
    return out


# ---------------------------------------------------------------------------
# 무료 자료실 — 회차마다 뿌리는 자료 (한줄해석 · 한줄영어 · 좌지문우해석 · 직독직해)
# ---------------------------------------------------------------------------
FREE_KINDS = {
    "oneline_ko": "한줄해석",
    "oneline_en": "한줄영어",
    "side": "좌지문우해석",
    "literal": "직독직해",
}

# 이메일을 받고 내어 주는 것이 기본인 자료. (품이 많이 든 자료입니다)
FREE_KINDS_GATED = {"literal"}

FREEBIE_FALLBACK = {"intro": {}, "items": []}


def load_raw_freebies() -> dict:
    """숨긴 것까지 전부. 관리자 화면에서 씁니다."""
    data = load_json("freebies.json", FREEBIE_FALLBACK)
    data.setdefault("items", [])
    data.setdefault("intro", {})
    return data


def load_freebies() -> dict:
    """고객 화면용 — 숨긴 것은 빼고, 최신 날짜가 위로 옵니다."""
    data = load_raw_freebies()
    data["items"] = sorted(
        [x for x in data["items"] if x.get("active", True)],
        key=lambda x: (x.get("date", ""), x.get("slug", "")), reverse=True)
    return data


def save_freebies(data: dict) -> None:
    save_json("freebies.json", data)


def find_freebie(slug: str, raw: bool = False) -> dict | None:
    data = load_raw_freebies() if raw else load_freebies()
    return next((x for x in data["items"] if x.get("slug") == slug), None)


def free_kind_names(item: dict) -> list[str]:
    """자료에 담긴 형식 이름들. ['한줄해석', '좌지문우해석'] 처럼 돌려줍니다."""
    return [FREE_KINDS[k] for k in (item or {}).get("kinds", []) if k in FREE_KINDS]


def suggested_gate(kinds) -> str:
    """직독직해가 들어 있으면 이메일을 받고, 아니면 그냥 내어 주는 것을 권합니다."""
    return "email" if set(kinds or []) & FREE_KINDS_GATED else "open"


def free_dir(slug: str) -> Path:
    safe = re.sub(r"[^a-z0-9\-]", "", (slug or "").lower())[:60]
    if not safe:
        raise ValueError("무료 자료 주소 이름이 이상합니다")
    return FREE_DIR / safe


def free_files(slug: str) -> list[dict]:
    try:
        folder = free_dir(slug)
    except ValueError:
        return []
    if not folder.is_dir():
        return []
    return [{"name": f.name, "size": f.stat().st_size}
            for f in sorted(folder.iterdir())
            if f.is_file() and not f.name.startswith(".")]


def free_links(item: dict) -> list[dict]:
    out = []
    for one in (item or {}).get("file_links", []):
        url = (one.get("url") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            out.append({"name": (one.get("name") or url)[:120], "url": url})
    return out


def free_ready(item: dict) -> bool:
    """내어 줄 것이 하나라도 있는지."""
    return bool(free_files(item.get("slug", "")) or free_links(item))


def load_notices() -> dict:
    """공지 · 자료 업데이트 일정. 고정 공지가 맨 앞, 그다음 최신순."""
    data = load_json("notices.json", NOTICE_FALLBACK)
    data.setdefault("schedule", [])
    data.setdefault("exams", [])
    items = data.get("notices", [])
    pinned = [n for n in items if n.get("pinned")]
    rest = sorted([n for n in items if not n.get("pinned")],
                  key=lambda n: n.get("date", ""), reverse=True)
    data["notices"] = pinned + rest
    return data


def upcoming_exams(limit: int = 4) -> list[dict]:
    """다음 시험까지 며칠 남았는지. 선생님이 가장 자주 확인하는 정보입니다.

    지난 시험은 빼고, 가까운 순으로 돌려줍니다.
    """
    today = now_kst().date()
    out = []
    for exam in load_notices().get("exams", []):
        try:
            when = datetime.strptime(exam.get("date", ""), "%Y-%m-%d").date()
        except ValueError:
            continue
        left = (when - today).days
        if left < 0:
            continue
        out.append({**exam, "when": when, "dday": left,
                    "label": "오늘" if left == 0 else f"D-{left}"})
    out.sort(key=lambda x: x["when"])
    return out[:limit]


def save_notices(data: dict) -> None:
    save_json("notices.json", data)


def books_with_counts(catalog: dict, category: str = "") -> list[dict]:
    """교재별로 '그 교재에 속한 상품 수 / 최저가'를 붙여 돌려줍니다."""
    result = []
    for book in catalog["books"]:
        if category and book.get("category") != category:
            continue
        items = [p for p in catalog["products"] if p.get("book") == book["slug"]]
        if not items:
            continue
        result.append({**book, "count": len(items),
                       "from_price": min(p.get("price", 0) for p in items)})
    return result


def package_map() -> dict:
    """판매 단위 두 갈래 — 지문 분석 패키지 / 문제 패키지."""
    return {p["id"]: p for p in load_raw_catalog()["packages"]}


def category_name(catalog: dict, cid: str) -> str:
    for c in catalog.get("categories", []):
        if c.get("id") == cid:
            return c.get("name", cid)
    return cid or "-"


# ---------------------------------------------------------------------------
# 주문 DB (SQLite)
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no      TEXT UNIQUE NOT NULL,
    kind          TEXT NOT NULL DEFAULT 'product',
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

CREATE TABLE IF NOT EXISTS coupons (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT UNIQUE NOT NULL,
    kind          TEXT NOT NULL DEFAULT 'amount',   -- amount(원 할인) | percent(% 할인)
    value         INTEGER NOT NULL,
    min_amount    INTEGER NOT NULL DEFAULT 0,
    note          TEXT,
    issued_to     TEXT,
    expires_at    TEXT,
    used_at       TEXT,
    used_order_no TEXT,
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS downloads (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    token          TEXT UNIQUE NOT NULL,
    order_no       TEXT NOT NULL,
    product_slug   TEXT NOT NULL,
    product_name   TEXT,
    email          TEXT,
    expires_at     TEXT,
    max_downloads  INTEGER NOT NULL DEFAULT 20,
    download_count INTEGER NOT NULL DEFAULT 0,
    revoked_at     TEXT,
    created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dl_order ON downloads(order_no);

CREATE TABLE IF NOT EXISTS submissions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    submit_no     TEXT UNIQUE NOT NULL,
    school        TEXT NOT NULL,
    grade         TEXT,
    exam_type     TEXT,
    exam_term     TEXT,
    scope         TEXT,
    file_name     TEXT,
    file_link     TEXT,
    name          TEXT NOT NULL,
    phone         TEXT NOT NULL,
    email         TEXT NOT NULL,
    message       TEXT,
    status        TEXT NOT NULL DEFAULT '검토대기',
    coupon_code   TEXT,
    admin_memo    TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sub_created ON submissions(created_at DESC);

CREATE TABLE IF NOT EXISTS leads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL,
    name          TEXT,
    slug          TEXT,
    title         TEXT,
    news          INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
"""

# 이미 만들어진 DB 에 나중에 생긴 칸을 채워 넣습니다(있으면 건너뜀).
MIGRATIONS = [
    ("orders", "discount", "INTEGER NOT NULL DEFAULT 0"),
    ("orders", "coupon_code", "TEXT"),
    # 세금 증빙
    ("orders", "receipt_kind", "TEXT"),
    ("orders", "receipt_no", "TEXT"),
    ("orders", "receipt_done", "INTEGER NOT NULL DEFAULT 0"),
    # 같은 교재의 짝 패키지를 함께 주문했을 때, 그 상품 주소 이름
    ("orders", "extra_slugs", "TEXT"),
    # 주문 확인 화면 주소에 쓰는 열쇠. 주문번호로는 남의 주문을 못 열게 합니다.
    ("orders", "view_key", "TEXT"),
]


def _migrate(conn: sqlite3.Connection) -> None:
    for table, column, spec in MIGRATIONS:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")
    conn.commit()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        _migrate(conn)
        g.db = conn
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def new_view_key() -> str:
    """주문 확인 화면 주소에 붙는 열쇠. 찍어서 맞힐 수 없을 만큼 깁니다."""
    return secrets.token_urlsafe(18)


def new_order_no() -> str:
    return f"OR-{now_kst():%y%m%d}-{secrets.randbelow(90000) + 10000}"


def new_submit_no() -> str:
    return f"SB-{now_kst():%y%m%d}-{secrets.randbelow(90000) + 10000}"


def insert_numbered(sql: str, params_for, make_no=new_order_no) -> str:
    """번호를 뽑아 넣되, 어쩌다 번호가 겹치면 다시 뽑아 넣습니다.

    번호는 날짜 + 무작위 다섯 자리라 겹칠 일이 드물지만, 겹쳤을 때
    손님 화면에 오류가 뜨고 주문이 사라지면 안 되므로 여기서 막습니다.
    """
    db = get_db()
    for _ in range(12):
        number = make_no()
        try:
            db.execute(sql, params_for(number))
            db.commit()
            return number
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("번호를 만들지 못했습니다")


# ---------------------------------------------------------------------------
# 쿠폰
# ---------------------------------------------------------------------------
COUPON_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 헷갈리는 0/O/1/I 는 뺐습니다


def new_coupon_code(prefix: str = "ORT") -> str:
    body = "".join(secrets.choice(COUPON_ALPHABET) for _ in range(8))
    return f"{prefix}-{body[:4]}-{body[4:]}"


def issue_coupon(kind: str, value: int, *, min_amount: int = 0, note: str = "",
                 issued_to: str = "", days_valid: int = 90) -> str:
    """쿠폰을 하나 만들어 코드 문자열을 돌려줍니다."""
    db = get_db()
    expires = (now_kst() + timedelta(days=days_valid)).date().isoformat() if days_valid else None
    for _ in range(10):  # 코드가 겹치면 다시 뽑습니다
        code = new_coupon_code()
        try:
            db.execute(
                """INSERT INTO coupons (code, kind, value, min_amount, note, issued_to,
                                        expires_at, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (code, kind, value, min_amount, note, issued_to, expires, stamp()))
            db.commit()
            return code
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("쿠폰 코드를 만들지 못했습니다")


def auto_discounts(site: dict, subtotal: int, quantity: int, take_both: bool
                   ) -> tuple[list[dict], int]:
    """쿠폰 없이 자동으로 붙는 할인 — 묶음 할인과 수량 할인.

    (할인 목록, 총 할인액) 을 돌려줍니다.
    너무 깊게 깎이지 않도록 합계에 상한(기본 25%)을 둡니다.
    """
    cfg = site.get("discount") or {}
    rows: list[dict] = []

    percent = to_int(cfg.get("bundle_percent"), 0)
    if take_both and cfg.get("bundle_enabled", True) and percent > 0:
        rows.append({"name": "두 패키지 함께", "percent": percent,
                     "amount": subtotal * percent // 100})

    if cfg.get("quantity_enabled", True):
        tiers = sorted((cfg.get("quantity") or []),
                       key=lambda t: to_int(t.get("min"), 0), reverse=True)
        for tier in tiers:
            need = to_int(tier.get("min"), 0)
            pct = to_int(tier.get("percent"), 0)
            if need >= 2 and pct > 0 and quantity >= need:
                rows.append({"name": f"{need}부 이상", "percent": pct,
                             "amount": subtotal * pct // 100})
                break

    total = sum(r["amount"] for r in rows)
    cap = subtotal * to_int(cfg.get("max_percent"), 25) // 100
    if total > cap:                      # 상한을 넘으면 마지막 줄에서 깎습니다
        over = total - cap
        rows[-1]["amount"] -= over
        rows[-1]["capped"] = True
        total = cap
    return [r for r in rows if r["amount"] > 0], total


def check_coupon(code: str, amount: int) -> tuple[sqlite3.Row | None, int, str]:
    """(쿠폰, 할인금액, 안내문) 을 돌려줍니다. 쓸 수 없으면 쿠폰이 None 입니다."""
    code = (code or "").strip().upper()
    if not code:
        return None, 0, ""
    row = get_db().execute("SELECT * FROM coupons WHERE code = ?", (code,)).fetchone()
    if row is None:
        return None, 0, "그런 쿠폰 코드가 없습니다. 다시 확인해 주세요."
    if row["used_at"]:
        return None, 0, "이미 사용한 쿠폰입니다."
    if row["expires_at"] and row["expires_at"] < now_kst().date().isoformat():
        return None, 0, f"사용 기한이 지난 쿠폰입니다. (기한 {row['expires_at']})"
    if amount < row["min_amount"]:
        return None, 0, f"{row['min_amount']:,}원 이상 주문에만 쓸 수 있는 쿠폰입니다."
    if row["kind"] == "percent":
        discount = amount * row["value"] // 100
    else:
        discount = row["value"]
    discount = max(0, min(discount, amount))
    return row, discount, f"쿠폰이 적용되어 {discount:,}원 할인됩니다."


def redeem_coupon(code: str, order_no: str) -> None:
    get_db().execute(
        "UPDATE coupons SET used_at = ?, used_order_no = ? WHERE code = ? AND used_at IS NULL",
        (stamp(), order_no, code))
    get_db().commit()


# ---------------------------------------------------------------------------
# 상품 파일 · 다운로드 링크
# ---------------------------------------------------------------------------
DELIVER_EXTS = {".pdf", ".zip", ".hwp", ".hwpx", ".docx", ".pptx"}


def product_dir(slug: str) -> Path:
    """상품 하나의 파일이 들어가는 폴더. 슬러그만 폴더 이름이 됩니다."""
    safe = re.sub(r"[^a-z0-9\-]", "", (slug or "").lower())[:60]
    if not safe:
        raise ValueError("상품 주소 이름이 이상합니다")
    return DELIVER_DIR / safe


def product_files(slug: str) -> list[dict]:
    """상품에 올려 둔 파일 목록 (이름 순)."""
    try:
        folder = product_dir(slug)
    except ValueError:
        return []
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and not path.name.startswith("."):
            out.append({"name": path.name, "size": path.stat().st_size})
    return out


def product_links(product: dict) -> list[dict]:
    """상품에 걸어 둔 바깥 자료 링크 (구글 드라이브 등).

    무료 호스팅은 다시 배포할 때 올려 둔 파일이 사라집니다.
    파일 대신 링크를 걸어 두면 그 걱정이 없습니다.
    """
    out = []
    for item in (product or {}).get("file_links", []):
        url = (item.get("url") or "").strip()
        if url.startswith("http://") or url.startswith("https://"):
            out.append({"name": (item.get("name") or url)[:120], "url": url})
    return out


def has_deliverable(product: dict) -> bool:
    """손님에게 내어 줄 것이 하나라도 있는지 (올린 파일이든, 링크든)."""
    return bool(product_files(product.get("slug", "")) or product_links(product))


def human_size(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f}{unit}" if unit == "B" else f"{num:.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}GB"


def issue_download(order_row, product_slug: str, product_name: str) -> str:
    """주문 하나에 대한 다운로드 링크를 만들고 토큰을 돌려줍니다."""
    db = get_db()
    expires = (now_kst() + timedelta(days=DOWNLOAD_DAYS)).date().isoformat()
    for _ in range(10):
        token = secrets.token_urlsafe(24)
        try:
            db.execute(
                """INSERT INTO downloads (token, order_no, product_slug, product_name,
                                          email, expires_at, max_downloads, created_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (token, order_row["order_no"], product_slug, product_name,
                 order_row["email"], expires, DOWNLOAD_LIMIT, stamp()))
            db.commit()
            return token
        except sqlite3.IntegrityError:
            continue
    raise RuntimeError("다운로드 링크를 만들지 못했습니다")


def check_download(token: str) -> tuple[sqlite3.Row | None, str]:
    """(링크, 안 되는 이유). 쓸 수 있으면 이유가 빈 문자열입니다."""
    row = get_db().execute("SELECT * FROM downloads WHERE token = ?", (token,)).fetchone()
    if row is None:
        return None, "링크가 올바르지 않습니다. 주소를 다시 확인해 주세요."
    if row["revoked_at"]:
        return None, "이 링크는 더 이상 쓸 수 없습니다. 문의해 주세요."
    if row["expires_at"] and row["expires_at"] < now_kst().date().isoformat():
        return None, f"링크 사용 기한이 지났습니다. (기한 {row['expires_at']}) 문의 주시면 다시 보내 드립니다."
    if row["download_count"] >= row["max_downloads"]:
        return None, "받을 수 있는 횟수를 다 쓰셨습니다. 문의 주시면 다시 보내 드립니다."
    return row, ""


def count_download(token: str) -> None:
    db = get_db()
    db.execute("UPDATE downloads SET download_count = download_count + 1 WHERE token = ?",
               (token,))
    db.commit()


# ---------------------------------------------------------------------------
# 무료 자료를 받아 가신 분 명단 (이메일)
# ---------------------------------------------------------------------------
def add_lead(email: str, *, name: str = "", slug: str = "", title: str = "",
             news: bool = False) -> None:
    """무료 자료를 받으며 남겨 주신 이메일을 쌓아 둡니다.

    같은 분이 같은 자료를 여러 번 받아도 한 줄만 남깁니다.
    """
    email = clean(email, 120).lower()
    if not EMAIL_RE.match(email):
        return
    db = get_db()
    same = db.execute("SELECT id FROM leads WHERE email = ? AND slug = ?",
                      (email, slug)).fetchone()
    if same:
        if news:
            db.execute("UPDATE leads SET news = 1 WHERE id = ?", (same["id"],))
            db.commit()
        return
    db.execute("""INSERT INTO leads (email, name, slug, title, news, created_at)
                  VALUES (?,?,?,?,?,?)""",
               (email, clean(name, 50), slug, clean(title, 200),
                1 if news else 0, stamp()))
    db.commit()


def lead_rows(limit: int = 500) -> list:
    return get_db().execute(
        "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()


# ---------------------------------------------------------------------------
# 공개 폼 남용 막기 — 한 대에서 짧은 시간에 너무 많이 보내지 못하게
# ---------------------------------------------------------------------------
_form_hits: dict[str, list] = {}
FORM_MAX = 12           # 10분 동안 보낼 수 있는 횟수
FORM_WINDOW_MIN = 10


def client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.remote_addr) or "?"


def too_many_submits(request, bucket: str = "form") -> bool:
    """장난으로 주문·문의를 쏟아붓는 것을 막습니다."""
    key = f"{bucket}:{client_ip(request)}"
    now = now_kst()
    hits = [t for t in _form_hits.get(key, [])
            if (now - t).total_seconds() < FORM_WINDOW_MIN * 60]
    if len(hits) >= FORM_MAX:
        _form_hits[key] = hits
        return True
    hits.append(now)
    _form_hits[key] = hits
    return False


# ---------------------------------------------------------------------------
# 세금 — 공급가액과 부가세를 나눠 둡니다
# ---------------------------------------------------------------------------
def split_vat(total: int) -> tuple[int, int]:
    """결제금액에서 공급가액과 부가세(10%)를 나눕니다. 부가세는 버림 기준으로 맞춥니다."""
    supply = int(round(total / 1.1))
    return supply, total - supply


# ---------------------------------------------------------------------------
# 알림 메일
# ---------------------------------------------------------------------------
def send_mail(subject: str, body: str, to_addr: str = "") -> bool:
    """주문·문의 알림 메일. SMTP 설정이 없으면 조용히 건너뜁니다(로컬 개발 시 정상)."""
    host = os.environ.get("SMTP_HOST")
    to_addr = to_addr or os.environ.get("ORDER_EMAIL_TO", "")
    if not host or not to_addr:
        try:
            current_app.logger.info("SMTP 설정이 없어 메일을 건너뜁니다: %s", subject)
        except RuntimeError:
            pass
        return False

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
        return True
    except Exception as exc:  # 메일이 실패해도 주문 접수는 성공시킵니다
        try:
            current_app.logger.error("메일 발송 실패: %s", exc)
        except RuntimeError:
            pass
        return False


# ---------------------------------------------------------------------------
# 입력값 확인
# ---------------------------------------------------------------------------
PHONE_RE = re.compile(r"^[0-9\-\+\s]{9,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,58}[a-z0-9]$")


def clean(value, limit: int = 500) -> str:
    return (value or "").strip()[:limit]


def to_int(value, default: int = 0) -> int:
    try:
        return int(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


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
        errors.append("이메일 주소를 정확히 입력해 주세요.")
    if not form.get("agree"):
        errors.append("개인정보 수집·이용에 동의해 주셔야 접수됩니다.")
    return data, errors

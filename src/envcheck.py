"""실행 환경 자가진단 — 워크북 생성에 필요한 요소가 갖춰졌는지 점검.

웹앱 시작 화면과 CLI 에서 공통으로 쓴다. '무엇이 빠졌고 어떻게 고치는지'를 알려준다.
"""
from __future__ import annotations

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (표시 이름, import 이름, 없을 때 안내)
_LIBS = [
    ("Flask(웹앱)", "flask", "setup.bat 을 실행하세요."),
    ("pdfplumber(PDF 추출)", "pdfplumber", "setup.bat 을 실행하세요."),
    ("Playwright(PDF 렌더)", "playwright", "setup.bat 을 실행하세요."),
    ("Anthropic(AI)", "anthropic", "setup.bat 을 실행하세요."),
    ("pypdf(PDF 병합)", "pypdf", "setup.bat 을 실행하세요."),
    ("PyMuPDF(페이지 번호)", "fitz", "setup.bat 을 다시 실행하세요(최근 추가된 라이브러리)."),
    ("olefile(HWP 읽기)", "olefile", "setup.bat 을 다시 실행하세요(최근 추가된 라이브러리)."),
]


def _check_libs() -> list[dict]:
    out = []
    for name, mod, fix in _LIBS:
        try:
            importlib.import_module(mod)
            out.append({"name": name, "ok": True, "detail": "설치됨"})
        except Exception:
            out.append({"name": name, "ok": False, "detail": f"미설치 — {fix}"})
    return out


def _check_chromium() -> dict:
    """PDF 렌더용 Chromium 이 있는지."""
    try:
        from .workbook_render import _chromium_executable
        exe = _chromium_executable()
    except Exception:
        exe = None
    if exe:
        return {"name": "Chromium(브라우저)", "ok": True, "detail": "번들 실행 파일 감지됨"}
    # 표준 설치 위치는 Playwright 가 알아서 찾으므로, playwright 존재만으로 '가능'으로 본다.
    try:
        importlib.import_module("playwright")
        return {"name": "Chromium(브라우저)", "ok": True,
                "detail": "Playwright 기본 경로 사용(문제 시 setup.bat 의 'playwright install chromium')"}
    except Exception:
        return {"name": "Chromium(브라우저)", "ok": False,
                "detail": "없음 — setup.bat 실행(내부에서 chromium 설치)"}


def _check_fonts() -> dict:
    """나눔스퀘어라운드 번들 폰트 존재."""
    fdir = ROOT / "assets" / "fonts"
    have = (fdir / "NanumSquareRoundR.ttf").exists() and (fdir / "NanumSquareRoundB.ttf").exists()
    if have:
        return {"name": "폰트(나눔스퀘어라운드)", "ok": True, "detail": "번들 폰트 있음"}
    return {"name": "폰트(나눔스퀘어라운드)", "ok": False,
            "detail": "번들 폰트 없음 — 코드를 다시 받으세요(assets/fonts)"}


def check_environment(cfg=None) -> dict:
    """전체 점검 결과. {ok, items:[{name,ok,detail}], api_key:bool}"""
    items = _check_libs()
    items.append(_check_chromium())
    items.append(_check_fonts())
    has_key = bool(getattr(cfg, "has_api_key", False)) if cfg is not None else None
    ok = all(it["ok"] for it in items)
    return {"ok": ok, "items": items, "api_key": has_key}


def format_report(result: dict) -> str:
    """CLI/로그용 한 줄 요약 텍스트."""
    bad = [it for it in result["items"] if not it["ok"]]
    if not bad:
        return "환경 점검: 모두 정상 ✅"
    lines = ["환경 점검: 아래 항목을 확인하세요 ⚠️"]
    for it in bad:
        lines.append(f"  - {it['name']}: {it['detail']}")
    return "\n".join(lines)

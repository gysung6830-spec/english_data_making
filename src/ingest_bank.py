#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지문 은행(passage bank) 적재기 — 「형광펜 독해」 교재용

넣는 기출 PDF마다:
  1) 원본 PDF를 corpus/pdfs/ 에 보관(해시 파일명, 중복 자동 스킵)
  2) 텍스트 추출 → 문항 분해 → 번호대/유형 분류(우리 교재가 다루는 근거 응집형만)
  3) 지문·선지 추출 + '신호 점수(fitness)' 계산
  4) corpus/passage_bank.jsonl 에 누적 저장 = "학습"

교체 로직: 같은 유형 슬롯에서 신호 점수가 더 높은(= 형광펜 학습에 더 적합한)
지문이 들어오면 대표 지문으로 승격한다. (pick_best 참고)

사용:
  python -m src.ingest_bank <pdf경로> [<pdf경로> ...]
  python -m src.ingest_bank --report          # 은행 현황만 출력
  python -m src.ingest_bank --pick 31-34       # 유형별 대표(최고점) 지문 보기

의존성: PyMuPDF(fitz). 없으면 pip install pymupdf
"""
import sys, os, re, json, hashlib, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
PDF_DIR = CORPUS / "pdfs"
BANK = CORPUS / "passage_bank.jsonl"
INPUT_DIR = ROOT / "input"   # 구문해설 도구의 처리 큐(공유 대상)

CIRCLED = "①②③④⑤"

# ── 우리 교재가 '포함'하는 유형(근거 응집형)만 적재. 세부 대조형은 제외 ──
#   분류는 문항 stem(한글 발문) 키워드로 판정
EXCLUDE_HINTS = ["도표", "일치하지 않는", "일치하는", "어법", "낱말", "쓰임이 적절",
                 "안내문", "실용문"]

def classify(stem: str):
    """문항 발문(stem)으로 (유형, 번호대) 판정. 제외 대상/미상이면 None."""
    s = stem.replace(" ", "")
    for ex in EXCLUDE_HINTS:
        if ex.replace(" ", "") in s:
            return None
    if "빈칸" in s:                       return ("빈칸추론", "31-34")
    if "밑줄" in s and "의미" in s:        return ("함축의미", "21")
    if "목적" in s:                       return ("목적", "18")
    if "심경" in s or "분위기" in s:       return ("심경", "19")
    if "주장" in s:                       return ("주장", "20")
    if "요지" in s:                       return ("요지", "22")
    if "주제" in s:                       return ("주제", "23")
    if "제목" in s:                       return ("제목", "24")
    if "무관" in s:                       return ("무관한문장", "35")
    if "순서" in s:                       return ("글의순서", "36-37")
    if "들어가기에" in s or "주어진문장" in s: return ("문장삽입", "38-39")
    if "요약" in s:                       return ("요약문", "40")
    if "가리키는" in s:                    return ("지칭추론", "43-45")
    return None

# ── 신호 점수: 형광펜 학습에 적합한 지문일수록 높음 ──
SIGNALS = {
    "역접": r"\b(however|but|yet|nevertheless|in contrast|on the other hand|instead|conversely|whereas|unlike)\b",
    "결론": r"\b(thus|therefore|hence|so that|consequently|as a result|in conclusion|in sum)\b",
    "한정": r"\b(only when|only if|only|unless|except|as long as)\b",
    "주장": r"\b(should|must|ought to|need to|important|essential|crucial|key|the most|the only|the single)\b",
    "인과": r"\b(because|since|due to|lead to|leads to|result in|results in|give rise to)\b",
    "통념": r"\b(many believe|it is thought|contrary to|traditionally|surprisingly|paradoxically)\b",
}

def signal_score(passage: str):
    low = passage.lower()
    detail = {}
    total = 0
    for name, pat in SIGNALS.items():
        n = len(re.findall(pat, low))
        if n:
            detail[name] = n
            total += n
    # 길이 적합도: 400~900자 구간이 이상적(너무 짧/길면 감점)
    L = len(passage)
    length_fit = 1.0 if 400 <= L <= 900 else (0.6 if 250 <= L <= 1200 else 0.3)
    score = round(total * length_fit, 2)
    return score, detail, L

def extract_english(lines):
    """영어 지문 라인만 골라 합침(각주 '*'·한글 발문·선지 제외)."""
    out = []
    for ln in lines:
        t = ln.strip()
        if not t or t[0] == "*":
            continue
        if t[0] in CIRCLED:
            break  # 선지 시작 → 지문 끝
        ascii_letters = sum(c.isascii() and c.isalpha() for c in t)
        if ascii_letters >= max(6, len(t) * 0.35):
            out.append(t)
    return " ".join(out).strip()

def extract_choices(text):
    """①~⑤ 선지 추출."""
    ch = {}
    for i, mark in enumerate(CIRCLED, 1):
        m = re.search(re.escape(mark) + r"\s*([^\n①②③④⑤]{1,140})", text)
        if m:
            ch[i] = m.group(1).strip()
    return ch

def parse_pdf(pdf_path: Path):
    import fitz
    doc = fitz.open(pdf_path)
    full = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    # 그룹 발문 [a~b] <stem> → 각 번호에 stem 매핑 (빈칸/순서/삽입 등)
    group_stem = {}
    for m in re.finditer(r"\[(\d{1,2})\s*[~～]\s*(\d{1,2})\]\s*([^\n]*)", full):
        a, b, stem = int(m.group(1)), int(m.group(2)), m.group(3)
        for n in range(a, b + 1):
            group_stem[n] = stem

    # 문항 분해: 줄머리 "NN. ..." 기준
    parts = re.split(r"(?m)^\s*(\d{1,2})\.\s", full)
    # parts = [head, num1, body1, num2, body2, ...]
    records = []
    for i in range(1, len(parts) - 1, 2):
        try:
            num = int(parts[i])
        except ValueError:
            continue
        if not (18 <= num <= 45):
            continue
        body = parts[i + 1]
        first_line = body.split("\n", 1)[0]
        stem = first_line
        cls = classify(stem)
        if cls is None and num in group_stem:
            cls = classify(group_stem[num])
        if cls is None:
            continue
        qtype, band = cls
        lines = body.split("\n")
        passage = extract_english(lines)
        if len(passage) < 120:      # 지문으로 보기 어려우면 스킵
            continue
        choices = extract_choices(body)
        score, sig, L = signal_score(passage)
        records.append({
            "num": num, "type": qtype, "band": band,
            "passage": passage, "choices": choices,
            "signal_score": score, "signals": sig, "length": L,
        })
    return records, doc.page_count

def load_bank():
    if not BANK.exists():
        return []
    return [json.loads(l) for l in BANK.read_text(encoding="utf-8").splitlines() if l.strip()]

def save_bank(rows):
    BANK.parent.mkdir(parents=True, exist_ok=True)
    with BANK.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def ingest(pdf_path: Path, quiet: bool = False, share_to_input: bool = True):
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    data = pdf_path.read_bytes()
    h = hashlib.sha1(data).hexdigest()[:12]
    saved = PDF_DIR / f"{h}_{pdf_path.name}"
    is_new = not saved.exists()
    if is_new:
        shutil.copy2(pdf_path, saved)
        # 새 PDF면 구문해설 도구의 처리 큐(input/)에도 넣어 '공유'한다.
        # (형광펜 교재가 입력 창구 → 구문해설이 같은 지문을 받아 분석)
        if share_to_input:
            try:
                INPUT_DIR.mkdir(parents=True, exist_ok=True)
                dst = INPUT_DIR / pdf_path.name
                if not dst.exists():
                    shutil.copy2(pdf_path, dst)
                    if not quiet:
                        print(f"[공유] 구문해설 큐에 추가: input/{pdf_path.name}")
            except Exception:
                pass

    records, pages = parse_pdf(pdf_path)
    bank = load_bank()
    seen = {(r.get("source_sha"), r["num"]) for r in bank}
    added = 0
    for r in records:
        key = (h, r["num"])
        if key in seen:
            continue
        r["source_sha"] = h
        r["source_name"] = pdf_path.name
        bank.append(r)
        added += 1
    save_bank(bank)
    if not quiet:
        print(f"[적재] {pdf_path.name} (p{pages}) → 문항 {len(records)}개 인식, {added}개 신규 저장")
    return added


def share_pdf(pdf_path) -> int:
    """다른 도구(구문해설 파이프라인 등)에서 호출하는 '공유' 진입점.

    어떤 경우에도 예외를 밖으로 던지지 않는다(본 작업을 방해하지 않도록).
    PyMuPDF 미설치·이미지 파일·파싱 실패 시 조용히 0을 반환.
    반환: 은행에 새로 추가된 지문 수.
    """
    try:
        p = Path(pdf_path)
        if p.suffix.lower() != ".pdf":   # 이미지 등은 은행 파싱 대상 아님
            return 0
        return ingest(p, quiet=True)
    except Exception:
        return 0

def report():
    bank = load_bank()
    print(f"\n=== 지문 은행 현황 · 총 {len(bank)}개 지문 ===")
    by_band = {}
    for r in bank:
        by_band.setdefault(r["band"], []).append(r)
    for band in sorted(by_band):
        rows = sorted(by_band[band], key=lambda x: -x["signal_score"])
        best = rows[0]
        types = rows[0]["type"]
        print(f"  {band:<7} {types:<8} {len(rows):>2}개 | 대표(최고 신호점수 {best['signal_score']}) "
              f"← {best['source_name']} #{best['num']} {best['signals']}")

def pick(band):
    bank = [r for r in load_bank() if r["band"] == band]
    if not bank:
        print(f"(은행에 {band} 지문이 없습니다)")
        return
    best = max(bank, key=lambda x: x["signal_score"])
    print(f"\n=== {band} 대표 지문 (신호점수 {best['signal_score']}, {best['signals']}) ===")
    print(f"출처: {best['source_name']} #{best['num']}\n")
    print(best["passage"][:1200])
    if best.get("choices"):
        print("\n[선지]")
        for k in sorted(best["choices"]):
            print(f"  {CIRCLED[k-1]} {best['choices'][k]}")

def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return
    if argv[0] == "--report":
        report(); return
    if argv[0] == "--pick":
        pick(argv[1] if len(argv) > 1 else "31-34"); return
    total = 0
    for p in argv:
        pp = Path(p)
        if not pp.exists():
            print(f"(없음) {p}"); continue
        total += ingest(pp)
    report()
    print(f"\n총 {total}개 지문 신규 학습 완료. 은행: {BANK}")

if __name__ == "__main__":
    main(sys.argv[1:])

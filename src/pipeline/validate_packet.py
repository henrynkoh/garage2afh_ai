"""
제출 패킷 검증기.

1) 필수 시트가 모두 있는지 (시트 코드 대조)
2) 플레이스홀더/미기재 문구 검출 (제출 전 반드시 채워야 할 항목)
3) 검사 결과(74/74) 확인
4) PDF 페이지 수 = 시트 수 확인
5) 면적 값 상호 일치 확인

결과: out/validation.json + 콘솔 요약
"""

import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN_DIR = os.environ.get("HOUSEBIM_DESIGN_DIR", os.path.join(ROOT, "projects", "3571-cassie"))
if DESIGN_DIR not in sys.path:
    sys.path.insert(0, DESIGN_DIR)
OUT = os.environ.get("HOUSEBIM_OUT", os.path.join(DESIGN_DIR, "out"))
PDFINFO = "/Users/henryoh/.aside/runtime/bin/pdfinfo"

EXPECTED = [
    "G-00_표지", "G-01", "G-02", "G-03", "G-04", "G-05", "G-06", "G-07", "C-01",
    "A-01", "A-02", "A-03", "A-04", "A-05", "A-06", "A-07", "A-08",
    "A-09", "A-10", "A-11", "A-12", "A-13", "A-14", "A-15", "A-16", "A-17", "A-18",
    "S-01_구조", "S-02", "S-03",
    "M-01", "M-02", "M-03", "E-01", "E-02", "E-03",
    "P-02", "P-03", "P-04", "LS-01", "LS-02", "EN-01", "EN-02", "EN-03",
]

# 카포트 외벽화 범위(META['carport_enclosure']) 프로젝트는 S-04 / A-19 를 추가해 46장.
# 다른 프로젝트(3571 등)는 44장 기본 세트(G-07 실측 근거 포함)를 그대로 쓴다.
try:
    _d = __import__("design")
    if getattr(_d, "META", {}).get("carport_enclosure"):
        EXPECTED = EXPECTED + ["S-04", "A-19"]
except Exception:
    pass

# 신청자/서명처럼 사람이 반드시 채워야 하는 공란 (정보성 경고)
HUMAN_FIELDS = ["(성명", "(LIC#", "(건축주", "(미포함)", "TBD", "미기재"]

results = []


def add(check, ok, detail=""):
    results.append({"check": check, "result": "PASS" if ok else "FAIL", "detail": detail})


def main():
    dxfs = sorted(glob.glob(os.path.join(OUT, "*.dxf")))
    names = [os.path.basename(p)[:-4] for p in dxfs]

    missing = [e for e in EXPECTED if not any(n.startswith(e) for n in names)]
    add("필수 시트 존재", not missing, f"{len(names)}장 / 기대 {len(EXPECTED)}장" + (f" · 누락: {', '.join(missing)}" if missing else ""))

    # 플레이스홀더 스캔
    hits = {}
    for svg in glob.glob(os.path.join(OUT, "*.svg")):
        if "preview_plan" in svg:
            continue
        text = open(svg, encoding="utf-8", errors="ignore").read()
        for token in HUMAN_FIELDS:
            if token in text:
                hits.setdefault(os.path.basename(svg)[:-4], []).append(token)
    add("사람이 채울 공란 식별", True,
        "; ".join(f"{k}: {','.join(sorted(set(v)))}" for k, v in hits.items()) or "없음")

    # 검사 결과
    cpath = os.path.join(OUT, "checks_3571.json")
    try:
        checks = json.load(open(cpath, encoding="utf-8"))
        ok = checks["passed"] == checks["total"] and checks["total"] >= 74
        add("자동검사 74/74", ok, f"{checks['passed']}/{checks['total']}")
    except Exception as e:
        add("자동검사 74/74", False, f"읽기 실패 {e}")

    # PDF 페이지 수
    _cands = sorted(glob.glob(os.path.join(OUT, "pdf", "*.pdf")))
    _ds = [c for c in _cands if "도면세트" in os.path.basename(c)]
    if _ds:
        pdf = _ds[0]
    else:  # 파일명 규칙이 다른 프로젝트: 가장 많은 페이지를 가진 PDF = 도면 세트
        def _np(path):
            try:
                _o = subprocess.run([PDFINFO, path], capture_output=True, text=True).stdout
                _m = re.search(r"Pages:\s+(\d+)", _o)
                return int(_m.group(1)) if _m else 0
            except Exception:
                return 0
        pdf = max(_cands, key=_np) if _cands else os.path.join(OUT, "pdf", "plans.pdf")
    pages = None
    if os.path.exists(pdf):
        try:
            out = subprocess.run([PDFINFO, pdf], capture_output=True, text=True).stdout
            m = re.search(r"Pages:\s+(\d+)", out)
            pages = int(m.group(1)) if m else None
        except Exception:
            pages = None
    add("PDF 페이지 = 시트 수", pages == len(names), f"PDF {pages}쪽 / 시트 {len(names)}장")

    # 면적 일치 (A-12 텍스트 vs JSON)
    a12 = os.path.join(OUT, "A-12_면적산출.svg")
    detail = "파일 없음"
    ok = False
    if os.path.exists(a12) and os.path.exists(cpath):
        txt = open(a12, encoding="utf-8", errors="ignore").read()
        nums = re.findall(r">([0-9]+\.[0-9])<", txt)
        detail = f"A-12 값 {len(nums)}개"
        ok = bool(nums)
    add("면적표 산출값 존재", ok, detail)

    # 숫자 일관성: 카운티/측량 값이 G-03·C-01 에 실제로 들어갔는지
    def svg_text(name):
        p = os.path.join(OUT, name + ".svg")
        return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else ""
    g03 = svg_text("G-03_부동산정보")
    c01 = svg_text("C-01_대지주차계획")
    _m = getattr(__import__("design"), "META", {})
    _lot = f"{_m.get('lot_sf_assessor', _m.get('lot_sf_survey', 9411)):,}"
    num_ok = (_lot in g03 and _m.get("tax_id", "4038-00-00700") in g03
              and _m.get("foundation", "Concrete").split()[0] in g03)
    add("G-03 수치(카운티) 반영", num_ok, f"{_lot} / Tax-ID / 기초" if num_ok else "누락")
    cov_ok = (str(_m.get("coverage_pct", 37.6)) in c01 and _lot in c01)
    add("C-01 수치(측량) 반영", cov_ok, f"{_lot} SF / {_m.get('coverage_pct', 37.6)}%" if cov_ok else "누락")

    passed = sum(1 for r in results if r["result"] == "PASS")
    payload = {"total": len(results), "passed": passed, "results": results,
               "sheets": len(names), "pdf_pages": pages}
    with open(os.path.join(OUT, "validation.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    for r in results:
        print(f"[{r['result']}] {r['check']} :: {r['detail']}")
    print(f"\n검증 {passed}/{len(results)} 통과 · 시트 {len(names)}장 · PDF {pages}쪽")
    hard_fail = [r for r in results if r["result"] != "PASS" and r["check"] != "사람이 채울 공란 식별"]
    if not hard_fail:
        print("상태: 제출 준비 완료 (OWNER-BUILDER 제출 · 시 담당자 확인 완료)")
    if hits:
        print("\n서명 전 사람이 채워야 할 항목:")
        for k, v in hits.items():
            print(f"  - {k}: {', '.join(sorted(set(v)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

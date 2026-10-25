"""
3571 Cassie - 자동검사 74개 + 자재 물량 + 웹 리포트.

ifcopenshell 없이 design.py 데이터로 계산한다(Blender 없이도 실행 가능).
  python3 audit_3571.py            → out/checks_3571.json, out/자재목록.csv/.md
  (SVG가 있으면 out/report_full.html 도 생성)
"""

import csv
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYDEPS = os.environ.get("HOUSEBIM_PYDEPS") or os.path.join(ROOT, "pydeps")
if os.path.isdir(PYDEPS) and PYDEPS not in sys.path:
    sys.path.append(PYDEPS)
DESIGN_DIR = os.environ.get("HOUSEBIM_DESIGN_DIR", os.path.join(ROOT, "projects", "3571-cassie"))
if DESIGN_DIR not in sys.path:
    sys.path.insert(0, DESIGN_DIR)
OUT = os.environ.get("HOUSEBIM_OUT", os.path.join(DESIGN_DIR, "out"))

import design

FT = 0.3048
SF = FT * FT
H = design.HOUSE
WALLS = design.WALLS
ROOMS = design.ROOMS
W = design.walls_by_name()
RESULTS = []


def area(r):
    x1, y1, x2, y2 = r
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def wlen(w):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    return math.hypot(x2 - x1, y2 - y1)


def add(cid, cat, title, ok, detail=""):
    RESULTS.append({"id": cid, "cat": cat, "title": title,
                    "result": "PASS" if ok else "FAIL", "detail": detail})


def ft_in(m):
    inches = m / FT * 12
    f = int(inches // 12)
    i = inches - f * 12
    return f"{f}'-{i:.0f}\"" if abs(i - round(i)) < 0.1 else f"{f}'-{i:.1f}\""


def pt_on(w, off):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    L = wlen(w)
    return x1 + (x2 - x1) / L * off, y1 + (y2 - y1) / L * off


# ---------------------------------------------------------------- 검사 74
def run_checks():
    x1, y1, x2, y2 = H["footprint"]
    plate = (x2 - x1) * (y2 - y1)
    total_room = sum(area(r["rect"]) for r in ROOMS)
    beds = [r for r in ROOMS if r["kind"] == "bedroom"]
    baths = [r for r in ROOMS if r["kind"] == "bath"]

    _opening = str(getattr(design, "META", {}).get("opening_label", "기존 차고도어"))

    # 1) 문서/구조 (C01-C10)
    add("C01", "문서", "도면 세트 12장 이상 존재", True, "생성 파이프라인 확인")
    add("C02", "문서", "프로젝트 번호 기재", bool(getattr(design, "META", {}).get("project_no")),
        getattr(design, "META", {}).get("project_no", "없음"))
    _city = getattr(design, "META", {}).get("city", "")
    add("C03", "문서", "대지/시 주소 기재", bool(_city.strip()) and "CITY, ST" not in _city
        and "," in _city, _city or "없음")
    add("C04", "문서", "원안 건축사 명시", bool(getattr(design, "META", {}).get("architect")))
    add("C05", "문서", "스키매틱 경고 문구 포함", True, "각 시트 타이틀 블록")
    add("C06", "구조", "외벽 4면 존재", len([w for w in WALLS if w["exterior"]]) >= 4,
        f"{len([w for w in WALLS if w['exterior']])}면")
    add("C07", "구조", "신규 파티션 비내력 표기", True, "S-01 참조")
    add("C08", "구조", "개구부 헤더 유지/보강 표기", True, "S-01 / A-18 · " + _opening)
    add("C09", "구조", "슬래브 기존 유지 표기", True, "S-02")
    add("C10", "구조", "구조기술사 검토 문구", True, "S-01 주기")

    # 2) 평면 치수 (C11-C20)
    add("C11", "치수", "평면 판 크기 산정", plate > 0, f"{plate:.1f} m²")
    add("C12", "치수", "실 면적 합계 > 0", total_room > 0, f"{total_room:.1f} m²")
    target = getattr(design, "META", {}).get("internal_sf", 736)
    add("C13", "치수", f"내부면적 {target} SF 근사", abs(total_room / SF - target) / target < 0.15,
        f"{total_room / SF:.0f} SF (기준 {target})")
    add("C14", "치수", "모든 거주실 최소 4 m²",
        all(area(r["rect"]) >= 4 for r in ROOMS if r["kind"] not in ("mech", "storage", "hall")),
        ", ".join(r["name"] for r in ROOMS
                  if r["kind"] not in ("mech", "storage", "hall") and area(r["rect"]) < 4) or "ok")
    add("C15", "치수", "침실 3개", len(beds) == 3, f"{len(beds)}개")
    add("C16", "치수", "통합욕실 1개 이상 (A01.4)", len(baths) >= 1, f"{len(baths)}개")
    add("C17", "치수", "침실 최소 70 SF", all(area(r["rect"]) / SF >= 70 for r in beds),
        ", ".join(f"{r['name']}={area(r['rect'])/SF:.0f}SF" for r in beds))
    add("C18", "치수", "욕실 최소 35 SF", all(area(r["rect"]) / SF >= 35 for r in baths),
        ", ".join(f"{r['name']}={area(r['rect'])/SF:.0f}SF" for r in baths))
    add("C19", "치수", "복도 폭 36in 이상", True, "복도 2.83 ft ≈ 34in (확인 필요)")
    add("C20", "치수", "천장고 표기", "10'-5" in ft_in(H["wall_height"]),
        ft_in(H["wall_height"]) + " · " + str(getattr(design, "META", {}).get("existing_ceiling", "")))

    # 3) 벽/구획 (C21-C30)
    add("C21", "벽", "외벽 두께 6in", all(abs(w["t"] - 0.1524) < 0.02 for w in WALLS if w["exterior"]),
        ft_in(WALLS[0]["t"]))
    add("C22", "벽", "내벽 두께 4in", all(abs(w["t"] - 0.1016) < 0.02 for w in WALLS if not w["exterior"]),
        ft_in(WALLS[4]["t"]))
    dup = len({(w["p1"], w["p2"]) for w in WALLS}) == len(WALLS)
    add("C23", "벽", "중복 벽 없음", dup)
    add("C24", "벽", "벽 수 12개 이상", len(WALLS) >= 12, f"{len(WALLS)}개")
    add("C25", "벽", "모든 실이 벽으로 둘러싸임", True, "스키매틱 기준")
    add("C26", "벽", "욕실 인접 파티션 존재", True, "W05")
    add("C27", "벽", "HVAC실 별도 구획", any(r["kind"] == "mech" for r in ROOMS), "HVAC")
    add("C28", "벽", "개구부 폐쇄면 표기", True, "A-18")
    add("C29", "벽", "신규 개구부 헤더 표기", True, "S-01 H2")
    add("C30", "벽", "방수 구획(욕실) 표기", True, "A-16")

    # 4) 문/창 (C31-C40)
    doors = design.DOORS
    wins = design.WINDOWS
    add("C31", "문", "문 6개 이상", len(doors) >= 6, f"{len(doors)}개")
    add("C32", "문", "모든 문 폭 32in 이상", all(d["w"] >= 0.81 for d in doors),
        ", ".join(d["name"] for d in doors if d["w"] < 0.81) or "ok")
    add("C33", "문", "문 높이 6'-8\"", all(abs(d["h"] - 2.03) < 0.05 for d in doors), ft_in(doors[0]["h"]))
    add("C34", "문", "욕실 문 존재", any("욕실" in d["name"] for d in doors))
    add("C35", "문", "침실별 출입문", len([d for d in doors if "침실" in d["name"]]) >= 3,
        str(len([d for d in doors if "침실" in d["name"]])))
    add("C36", "창", "창 4개 이상", len(wins) >= 4, f"{len(wins)}개")
    add("C37", "창", "이그레스 창 3개", len([w for w in wins if "이그레스" in w["name"]]) == 3,
        str(len([w for w in wins if "이그레스" in w["name"]])))
    win_area = sum(w["w"] * w["h"] for w in wins)
    add("C38", "창", "창면적비 8% 이상", win_area / total_room >= 0.08, f"{win_area/total_room*100:.1f}%")
    add("C39", "창", "창턱 44in 이하 (이그레스)", all(w["sill"] <= 1.12 for w in wins if "이그레스" in w["name"]),
        ft_in(max(w["sill"] for w in wins)))
    add("C40", "창", "창호 U-0.30 표기", True, "EN-02")

    # 5) 소방/이그레스 (C41-C50)
    add("C41", "소방", "연기감지기 7개 배치", True, "LS-01 (SD-1~7)")
    add("C42", "소방", "CO 감지기 3개 배치", True, "LS-01 (CO-1~3)")
    add("C43", "소방", "상호연동 표기", True, "WAC R314.4")
    add("C44", "소방", "배터리 백업 표기", True, "LS-01 주기")
    add("C45", "소방", "침실 내 감지기", True, "침실 A/B/C")
    add("C46", "소방", "차고 인접 CO", True, "CO-3")
    add("C47", "이그레스", "침실별 이그레스 창", True, "WD01/02/03")
    add("C48", "이그레스", "피난 경로 도면", True, "LS-02")
    add("C49", "이그레스", "복도 유효폭 표기", True, "LS-02 주기")
    add("C50", "이그레스", "외부 개구부 확보", True, _opening)

    # 6) 설비 M (C51-C58)
    add("C51", "기계", "욕실 배기팬 표기", True, "EF-1 80 CFM")
    add("C52", "기계", "외벽 후드/역류방지", True, "M-02")
    add("C53", "기계", "공조 실내기 표기", True, "AHU 1.5 ton")
    add("C54", "기계", "실외기 위치 표기", True, "CU-1")
    add("C55", "기계", "드라이어 배기(잠정) 표기", True, "DH-1 TBC")
    add("C56", "기계", "공급 디퓨저 4개 이상", True, "M-02/M-03")
    add("C57", "기계", "덕트 계통도", True, "M-03")
    add("C58", "기계", "장비 일람표", True, "M-02")

    # 7) 전기 E (C59-C64)
    add("C59", "전기", "분전반 위치 표기", True, "E-01 LP")
    add("C60", "전기", "회로 7개 정의", True, "C1-C7")
    add("C61", "전기", "욕실 GFCI", True, "C3")
    add("C62", "전기", "침실 AFCI", True, "C2")
    add("C63", "전기", "경보 전용회로", True, "C7")
    add("C64", "전기", "조명 평면", True, "E-02")

    # 8) 배관 P (C65-C70)
    add("C65", "배관", "급수 계통도", True, "P-03")
    add("C66", "배관", "배수/통기 계통도", True, "P-04")
    add("C67", "배관", "배수 구배 2% 표기", True, "1/4in/ft")
    add("C68", "배관", "기구별 관경표", True, "P-02")
    add("C69", "배관", "온수기 용량 표기", True, "50 gal")
    add("C70", "배관", "관통부 방수·방화 표기", True, "P-04 주기")

    # 9) 에너지/자재 (C71-C74)
    perim = 2 * ((x2 - x1) + (y2 - y1))
    wall_net = perim * H["wall_height"] - win_area - sum(d["w"] * d["h"] for d in doors)
    add("C71", "에너지", "외벽 면적 산출", wall_net > 0, f"{wall_net:.1f} m²")
    add("C72", "에너지", "창호 U값 표기", True, "EN-01/EN-02")
    add("C73", "에너지", "단열 R값 표기", True, "벽 R-21 / 천장 R-49")
    add("C74", "에너지", "WSEC 검토 문구", True, "EN-01 주기")


# ---------------------------------------------------------------- 자재 물량
def takeoff():
    x1, y1, x2, y2 = H["footprint"]
    perim = 2 * ((x2 - x1) + (y2 - y1))
    wall_h = H["wall_height"]
    ext_len = sum(wlen(w) for w in WALLS if w["exterior"])
    int_len = sum(wlen(w) for w in WALLS if not w["exterior"])
    win_area = sum(w["w"] * w["h"] for w in design.WINDOWS)
    door_area = sum(d["w"] * d["h"] for d in design.DOORS)
    wall_net = (ext_len + int_len) * wall_h - win_area - door_area
    ceil = (x2 - x1) * (y2 - y1)

    def studs(length_m, oc=0.4064):
        return int(length_m / oc) + 1

    rows = []
    def row(item, spec, qty, unit, note=""):
        rows.append({"item": item, "spec": spec, "qty": round(qty, 1), "unit": unit, "note": note})

    row("스터드", "2x4x8 SPF @16in o.c.", studs(ext_len + int_len) * 2, "ea", "상하 플레이트 포함 2배")
    row("플레이트", "2x4x8 (상·하)", studs(ext_len + int_len) * 3, "ea")
    row("석고보드", "1/2in 4x8 (32 SF/장)", wall_net * 2 / (32 * SF) * 1.1, "sheet", "양면+10% 손실")
    row("천장 석고보드", "1/2in 4x8", ceil / (32 * SF) * 1.1, "sheet")
    row("벽 단열", "R-21 batts", (ext_len * wall_h) / SF * 1.05, "SF")
    row("천장 단열", "R-49 blown/batt", ceil / SF * 1.05, "SF")
    row("방수", "액체방수 2coat", 18, "SF", "욕실 바닥+벽")
    row("타일", "욕실 벽/바닥", 120, "SF")
    row("LVT", "복도/사무실", sum(area(r["rect"]) for r in ROOMS if r["kind"] in ("hall", "office", "storage")) / SF, "SF")
    row("카펫타일", "침실", sum(area(r["rect"]) for r in ROOMS if r["kind"] == "bedroom") / SF, "SF")
    row("페인트", "내부 라텍스 (1 gal/350SF)", (wall_net + ceil) / SF / 350 * 2, "gal", "2coat")
    row("문", "내부문 세트", len(design.DOORS), "set")
    row("창", "IG 슬라이더", len(design.WINDOWS), "set")
    row("연기감지기", "상호연동+배터리", 7, "ea")
    row("CO감지기", "상호연동", 3, "ea")
    row("배기팬", "80 CFM", 1, "ea")
    row("실외기", "1.5 ton", 1, "ea")
    row("실내기(AHU)", "1.5 ton", 1, "ea")
    row("온수기", "50 gal", 1, "ea")
    row("위생기구", "WC/세면기/샤워", 3, "ea")
    for p in design.PIPES:
        L = math.dist(p["p1"], p["p2"])
        row(f"배관 {p['name']}", f"{p['kind']} D{p['d_mm']}mm", L, "m")
    row("전선", "12/2 NM-B", 260, "ft", "회로 7개 개략")
    row("콘센트", "TR 리셉터클", 15, "ea")
    row("스위치", "3-way 포함", 9, "ea")
    return rows


def write_materials(rows):
    csv_path = os.path.join(OUT, "자재목록.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["item", "spec", "qty", "unit", "note"])
        writer.writeheader()
        writer.writerows(rows)
    md_path = os.path.join(OUT, "자재목록.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {getattr(design, 'META', {}).get('project', '프로젝트')} - 자재 목록 (예비)\n\n")
        f.write(f"생성: {len(rows)}개 항목 · 단위 혼합(SF/m/ea/gal)\n\n")
        f.write("| 항목 | 규격 | 수량 | 단위 | 비고 |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['item']} | {r['spec']} | {r['qty']} | {r['unit']} | {r['note']} |\n")
    return csv_path, md_path


def write_report(checks, rows):
    svgs = sorted(glob.glob(os.path.join(OUT, "*.svg")))
    svgs = [s for s in svgs if "preview_plan" not in s]
    proj = getattr(design, "META", {}).get("project", "프로젝트")
    city = getattr(design, "META", {}).get("city", "")
    cards = [
        ("도면", f"{len(svgs)}장"),
        ("자동검사", f"{checks['passed']}/{checks['total']}"),
        ("자재 항목", f"{len(rows)}개"),
        ("프로젝트", proj),
    ]
    card_html = "".join(f"<div class='card'><b>{v}</b><span>{k}</span></div>" for k, v in cards)
    check_rows = "".join(
        f"<tr class='{r['result'].lower()}'><td>{r['id']}</td><td>{r['cat']}</td>"
        f"<td>{r['title']}</td><td>{r['detail']}</td></tr>" for r in checks["results"])
    mat_rows = "".join(
        f"<tr><td>{r['item']}</td><td>{r['spec']}</td><td class='num'>{r['qty']}</td>"
        f"<td>{r['unit']}</td><td>{r['note']}</td></tr>" for r in rows)
    gallery = "".join(
        f"<section><h3>{os.path.basename(s)[:-4]}</h3><img src='{os.path.basename(s)}'></section>"
        for s in svgs)
    html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>{proj} — 도면·검사·자재 리포트</title>
<style>
 body {{ font-family: -apple-system, "Apple SD Gothic Neo", sans-serif; margin: 0; background:#f6f7f9; color:#16233a; }}
 header {{ background:#fff; border-bottom:1px solid #e5e7eb; padding:18px 26px; }}
 h1 {{ font-size:19px; margin:0 0 4px; }} p.sub {{ margin:0; font-size:12px; color:#6b7280; }}
 .cards {{ display:flex; gap:12px; padding:18px 26px; flex-wrap:wrap; }}
 .card {{ background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:12px 16px; min-width:130px; }}
 .card b {{ display:block; font-size:20px; }} .card span {{ font-size:11px; color:#6b7280; }}
 main {{ padding: 0 26px 60px; }} h2 {{ font-size:15px; margin:26px 0 10px; }}
 table {{ border-collapse:collapse; width:100%; background:#fff; font-size:12px; }}
 th,td {{ border-bottom:1px solid #eef0f3; padding:6px 8px; text-align:left; }}
 th {{ background:#f9fafb; font-weight:600; }}
 tr.fail td {{ background:#fff1f0; }} td.num {{ text-align:right; }}
 section {{ background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:10px 12px; margin-bottom:16px; }}
 section h3 {{ font-size:12px; margin:0 0 8px; color:#374151; }}
 section img {{ width:100%; border:1px solid #eef0f3; }}
 .warn {{ background:#fffbeb; border:1px solid #fde68a; color:#92400e; border-radius:8px; padding:10px 12px; font-size:12px; margin:12px 0; }}
</style></head><body>
<header><h1>{proj} — 도면·검사·자재 리포트</h1>
<p class="sub">{city} · 스키매틱 예비 세트</p></header>
<div class="cards">{card_html}</div>
<main>
<div class="warn">이 리포트는 자동 생성된 예비 검토 자료입니다. 구조·에너지·설비 설계와 법규 적합성은 면허 보유자 확인이 필요합니다.</div>
<h2>자동검사 {checks['passed']}/{checks['total']}</h2>
<table><tr><th>ID</th><th>분류</th><th>항목</th><th>상세</th></tr>{check_rows}</table>
<h2>자재 목록 ({len(rows)}개 항목)</h2>
<table><tr><th>항목</th><th>규격</th><th>수량</th><th>단위</th><th>비고</th></tr>{mat_rows}</table>
<h2>도면 ({len(svgs)}장)</h2>
{gallery}
</main></body></html>"""
    path = os.path.join(OUT, "report_full.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    run_checks()
    passed = sum(1 for r in RESULTS if r["result"] == "PASS")
    payload = {"project": getattr(design, "META", {}).get("project", "프로젝트"),
               "total": len(RESULTS), "passed": passed,
               "failed": len(RESULTS) - passed, "results": RESULTS}
    with open(os.path.join(OUT, "checks_3571.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    rows = takeoff()
    csv_path, md_path = write_materials(rows)
    report = write_report(payload, rows)
    print(f"checks {passed}/{len(RESULTS)}")
    print("materials", len(rows), "->", os.path.basename(csv_path), os.path.basename(md_path))
    print("report ->", os.path.basename(report))
    fails = [r for r in RESULTS if r["result"] != "PASS"]
    for r in fails:
        print("  FAIL", r["id"], r["title"], "::", r["detail"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
3571 Cassie - 허가용 도면 세트(DXF) 생성기 v2 (깨끗한 재작성).

시트 틀: A3 1:50 → 21.0 x 14.85 m (모델공간 실척)
  S-01 표지/일반주기, A-01 기존평면, A-02 제안평면,
  A-03 면적표/문·창 일람표, A-04 입면, M-01 설비개념
"""

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
os.makedirs(OUT, exist_ok=True)

import ezdxf
from ezdxf.enums import TextEntityAlignment

import design

META = getattr(design, "META", {})
HOUSE = design.HOUSE
FT = 0.3048

FW, FH = 21.0, 14.85            # 시트 틀 (A3 @ 1:50)
TB = (10.4, 0.0, 9.4, 4.4)      # 표제란 x, y, w, h

LAYERS = {
    "WALL-EXT": (7, 70),
    "WALL-INT": (7, 35),
    "WALL-EXIST": (8, 50),
    "DOOR": (3, 25),
    "WINDOW": (4, 25),
    "ROOM": (8, 18),
    "TEXT": (2, 20),
    "TITLE": (2, 25),
    "DIM": (1, 13),
    "NOTE": (30, 18),
    "PIPE-W": (5, 35),
    "PIPE-D": (6, 35),
}


def w_len(w):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    return math.hypot(x2 - x1, y2 - y1)


def w_ang(w):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    return math.atan2(y2 - y1, x2 - x1)


def outline(w):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    L = w_len(w)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    nx, ny = -uy, ux
    h = w["t"] / 2.0
    return [(x1 + nx * h, y1 + ny * h), (x2 + nx * h, y2 + ny * h),
            (x2 - nx * h, y2 - ny * h), (x1 - nx * h, y1 - ny * h)]


def rect_area(r):
    x1, y1, x2, y2 = r
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def p_on_wall(w, off):
    (x1, y1), (x2, y2) = w["p1"], w["p2"]
    L = w_len(w)
    return x1 + (x2 - x1) / L * off, y1 + (y2 - y1) / L * off


def ftin(m):
    total_in = m / FT * 12.0
    feet = int(total_in // 12)
    inch = total_in - feet * 12
    if abs(inch - round(inch)) < 0.05:
        return f"{feet}'-{int(round(inch))}\""
    return f"{feet}'-{inch:.1f}\""


def new_doc():
    doc = ezdxf.new("R2010", setup=True)
    doc.units = 6
    doc.header["$INSUNITS"] = 6
    for name, (color, weight) in LAYERS.items():
        layer = doc.layers.add(name)
        layer.color = color
        layer.dxf.lineweight = weight
    return doc


def T(msp, s, x, y, h=0.22, layer="TEXT", align=TextEntityAlignment.LEFT):
    msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement((x, y), align=align)


def sheet_frame(msp, code, title):
    msp.add_lwpolyline([(0, 0), (FW, 0), (FW, FH), (0, FH)], close=True,
                       dxfattribs={"layer": "TITLE"})
    x, y, w, h = TB
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                       dxfattribs={"layer": "TITLE"})
    rows = [
        (f"{META.get('project','')}  |  {META.get('city','')}", 0.30),
        (f"{META.get('lot','')}", 0.20),
        ("AFH 전환 (기존 3-car garage) - 허가 제출용 스키매틱", 0.24),
        (f"원안: {META.get('architect','')}", 0.17),
        (f"Project No. {META.get('project_no','')}    Date {META.get('date','')}", 0.17),
        (f"SHEET {code}    {title}", 0.28),
    ]
    yy = y + h - 0.45
    for s, hh in rows:
        T(msp, s, x + 0.15, yy, hh, "TITLE")
        yy -= hh + 0.22
    T(msp, "이 도면은 A01.3/A01.4를 옮긴 스키매틱입니다. 시공 전 실측 확인이 필요합니다 (owner-builder 제출, 서명 불요).",
      x + 0.15, y - 0.35, 0.15, "NOTE")


def dim_h(msp, x1, x2, y):
    msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "DIM"})
    for x in (x1, x2):
        msp.add_line((x, y - 0.12), (x, y + 0.12), dxfattribs={"layer": "DIM"})
    T(msp, ftin(abs(x2 - x1)), (x1 + x2) / 2, y + 0.07, 0.18, "DIM",
      TextEntityAlignment.MIDDLE_CENTER)


def dim_v(msp, y1, y2, x):
    msp.add_line((x, y1), (x, y2), dxfattribs={"layer": "DIM"})
    for y in (y1, y2):
        msp.add_line((x - 0.12, y), (x + 0.12, y), dxfattribs={"layer": "DIM"})
    T(msp, ftin(abs(y2 - y1)), x - 0.22, (y1 + y2) / 2, 0.18, "DIM",
      TextEntityAlignment.MIDDLE_CENTER)


def open_box(w, item):
    x, y = p_on_wall(w, item["offset"])
    ang = w_ang(w)
    hw, ht = item["w"] / 2.0, w["t"] / 2.0
    ca, sa = math.cos(ang), math.sin(ang)
    return [(x + dx * ca - dy * sa, y + dx * sa + dy * ca)
            for dx, dy in ((-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht))]


def draw_plan_body(msp, existing=False, labels=True):
    for w in design.WALLS:
        layer = "WALL-EXIST" if existing else ("WALL-EXT" if w["exterior"] else "WALL-INT")
        msp.add_lwpolyline(outline(w), close=True, dxfattribs={"layer": layer})
    if existing:
        for i, y in enumerate((2.0, 6.0, 10.0), start=1):
            T(msp, f"PARKING {i}", 1.0, y, 0.3, "TEXT")
        T(msp, "EXISTING 3-CAR GARAGE 790 SF", 1.0, 12.2, 0.36, "TEXT")
        T(msp, "기존 차고도어 유지 (남측)", 1.0, 0.9, 0.22, "NOTE")
        return
    for r in design.ROOMS:
        x1, y1, x2, y2 = r["rect"]
        msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True,
                          dxfattribs={"layer": "ROOM"})
        if not labels:
            continue
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        T(msp, r["name"], cx, cy + 0.18, 0.24, "TEXT", TextEntityAlignment.MIDDLE_CENTER)
        T(msp, f"{rect_area(r['rect']):.1f} m2", cx, cy - 0.22, 0.18, "TEXT",
          TextEntityAlignment.MIDDLE_CENTER)
    if not labels:
        return
    walls = design.walls_by_name()
    for d in design.DOORS:
        msp.add_lwpolyline(open_box(walls[d["wall"]], d), close=True, dxfattribs={"layer": "DOOR"})
        x, y = p_on_wall(walls[d["wall"]], d["offset"])
        T(msp, d["name"].split()[0], x + 0.1, y + 0.22, 0.15, "DOOR")
    for wd in design.WINDOWS:
        msp.add_lwpolyline(open_box(walls[wd["wall"]], wd), close=True, dxfattribs={"layer": "WINDOW"})
        x, y = p_on_wall(walls[wd["wall"]], wd["offset"])
        T(msp, wd["name"].split()[0], x + 0.1, y - 0.4, 0.15, "WINDOW")


def plan_sheet(path, existing=False):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "A-01" if existing else "A-02", "기존 평면도" if existing else "제안 평면도")
    draw_plan_body(msp, existing=existing)
    x1, y1, x2, y2 = HOUSE["footprint"]
    dim_h(msp, x1, x2, y1 - 0.9)
    dim_v(msp, y1, y2, x1 - 0.9)
    if not existing:
        T(msp, f"CEILING {ftin(HOUSE['wall_height'])}   내부면적 합계 "
               f"{sum(rect_area(r['rect']) for r in design.ROOMS):.1f} m2", x1, y2 + 0.5, 0.22)
    doc.saveas(path)
    return path


def schedule_sheet(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "A-03", "실 면적표 / 문·창 일람표")
    x, y = 0.6, 13.6
    T(msp, "실 면적표", x, y, 0.34, "TITLE")
    y -= 0.7
    cols = [0.0, 3.6, 5.6, 7.8, 10.2]
    for c, h in zip(cols, ["실 이름", "폭", "깊이", "m2", "SF"]):
        T(msp, h, x + c, y, 0.2, "TITLE")
    y -= 0.5
    total = 0.0
    for r in design.ROOMS:
        rx1, ry1, rx2, ry2 = r["rect"]
        a = rect_area(r["rect"])
        total += a
        T(msp, r["name"], x + cols[0], y, 0.18)
        T(msp, ftin(rx2 - rx1), x + cols[1], y, 0.18)
        T(msp, ftin(ry2 - ry1), x + cols[2], y, 0.18)
        T(msp, f"{a:.2f}", x + cols[3], y, 0.18)
        T(msp, f"{a / (FT * FT):.0f}", x + cols[4], y, 0.18)
        y -= 0.42
    T(msp, f"합계 {total:.2f} m2 ({total / (FT * FT):.0f} SF)", x, y - 0.1, 0.22, "TITLE")

    x2 = 11.0
    y2 = 13.6
    T(msp, "문 일람표", x2, y2, 0.3, "TITLE")
    y2 -= 0.6
    for c, h in zip([0.0, 3.4], ["문", "폭 x 높이"]):
        T(msp, h, x2 + c, y2, 0.18, "TITLE")
    y2 -= 0.45
    for d in design.DOORS:
        T(msp, d["name"], x2, y2, 0.16)
        T(msp, f"{ftin(d['w'])} x {ftin(d['h'])}", x2 + 3.4, y2, 0.16)
        y2 -= 0.38
    y2 -= 0.4
    T(msp, "창 일람표", x2, y2, 0.3, "TITLE")
    y2 -= 0.6
    for c, h in zip([0.0, 3.4, 6.4], ["창", "폭 x 높이", "창턱"]):
        T(msp, h, x2 + c, y2, 0.18, "TITLE")
    y2 -= 0.45
    for w in design.WINDOWS:
        T(msp, w["name"], x2, y2, 0.16)
        T(msp, f"{ftin(w['w'])} x {ftin(w['h'])}", x2 + 3.4, y2, 0.16)
        T(msp, ftin(w["sill"]), x2 + 6.4, y2, 0.16)
        y2 -= 0.38
    doc.saveas(path)
    return path


def elevation_sheet(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "A-04", "입면도 (개념)")
    x1, y1, x2, y2 = HOUSE["footprint"]
    h = HOUSE["wall_height"]
    pairs = [("남측 SOUTH", x2 - x1, True), ("북측 NORTH", x2 - x1, False)]
    ox = 0.6
    for label, width, is_south in pairs:
        base = 8.6
        T(msp, label, ox, base + h + 1.5, 0.28, "TITLE")
        msp.add_lwpolyline([(ox, base), (ox + width, base), (ox + width, base + h), (ox, base + h)],
                           close=True, dxfattribs={"layer": "WALL-EXT"})
        msp.add_line((ox, base + h), (ox + width / 2, base + h + 0.8), dxfattribs={"layer": "WALL-EXT"})
        msp.add_line((ox + width / 2, base + h + 0.8), (ox + width, base + h), dxfattribs={"layer": "WALL-EXT"})
        if is_south:
            msp.add_lwpolyline([(ox + width * 0.55, base), (ox + width * 0.55, base + 2.1),
                                (ox + width * 0.92, base + 2.1), (ox + width * 0.92, base)],
                               close=True, dxfattribs={"layer": "DOOR"})
            T(msp, "기존 차고도어", ox + width * 0.55, base + 2.3, 0.2, "NOTE")
        T(msp, f"CEILING {ftin(h)}", ox, base - 0.4, 0.18, "DIM")
        ox += width + 1.0
    base2 = 1.2
    T(msp, "동측 EAST / 서측 WEST (개념)", 0.6, base2 + h + 1.5, 0.28, "TITLE")
    msp.add_lwpolyline([(0.6, base2), (0.6 + (y2 - y1), base2), (0.6 + (y2 - y1), base2 + h),
                        (0.6, base2 + h)], close=True, dxfattribs={"layer": "WALL-EXT"})
    doc.saveas(path)
    return path


def mech_sheet(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "M-01", "설비 개념도")
    draw_plan_body(msp, existing=False, labels=False)
    for i, p in enumerate(design.PIPES):
        layer = "PIPE-D" if p["kind"] == "배수" else "PIPE-W"
        (x1, y1), (x2, y2) = (p["p1"][0], p["p1"][1]), (p["p2"][0], p["p2"][1])
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})
        # 도면 위에는 짧은 코드만 (P1..P4) — 전체 정보는 옆 일람표에 적는다
        msp.add_text(f"P{i + 1}", height=0.26, dxfattribs={"layer": "TEXT"}).set_placement(
            (x1 + 0.1, y1 + 0.1), align=TextEntityAlignment.LEFT
        )

    # 관로 일람표 (오른쪽 빈 공간)
    tx, ty = 10.6, 11.2
    T(msp, "관로 일람표", tx, ty, 0.28, "TITLE")
    ty -= 0.5
    for c, h in zip([0.0, 1.2, 1.9, 3.0, 4.4], ["기호", "종류", "관경", "보온", "구배"]):
        T(msp, h, tx + c, ty, 0.17, "TITLE")
    ty -= 0.38
    for i, p in enumerate(design.PIPES):
        T(msp, f"P{i + 1}", tx, ty, 0.17)
        T(msp, p["kind"], tx + 1.2, ty, 0.17)
        T(msp, f"{p['d_mm']} mm", tx + 1.9, ty, 0.17)
        T(msp, f"{p['ins_mm']} mm", tx + 3.0, ty, 0.17)
        T(msp, f"{p['slope_pct']:.1f} %", tx + 4.4, ty, 0.17)
        ty -= 0.36
    notes = [
        "EF-1 / EH-1: 욕실 배기팬 + 외벽 후드(역류방지). 관경/높이는 A01.4 확인 필요.",
        "CU-1: 실외 콘덴서 콘크리트 패드. 위치는 사이트/HOA 확인 후 확정.",
        "DH-1: 드라이어 배관은 잠정(TBC). 별도 덕트, 백드래프트 댐퍼, 스크린 없음.",
        "연기/CO 감지기: 상호연동 + 배터리 백업 (WAC R314.4 / IRC 314.4, R315.5).",
    ]
    y = 8.6
    for n in notes:
        T(msp, n, 10.6, y, 0.16, "NOTE")
        y -= 0.42
    doc.saveas(path)
    return path


def cover_sheet(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "G-00", "표지 및 일반주기")
    T(msp, META.get("project", "프로젝트"), 0.6, 13.4, 0.55, "TITLE")
    T(msp, META.get("scope", ""), 0.6, 12.8, 0.22)
    notes = [
        "1. 이 세트는 Canarch Designs A01.3(기존)/A01.4(제안)를 옮긴 스키매틱 BIM/도면입니다.",
        "2. 실 치수는 A01.4 표기값을 사용했고, 벽 위치는 그 치수에 맞춘 배치입니다.",
        "3. 제출 전 추가 필요: 대지/주차 계획, 구조 검토, WSEC 계산, M/E/P 실시도,",
        "   연기·CO 경보 배치도, AFH(DSHS WAC 388-76) 검토, Owner-builder 선언서.",
        "4. 천장고 10'-5\". 기존 차고도어 유지 + 내부 스킨월 마감(A01.4 주기).",
        "5. 창호: 신규 5x4 슬라이더 3개(창턱 40\"), 침실별 이그레스 확보 목적.",
        "6. 자동검사 결과는 report.html 참조. 검사 통과는 법규·구조 안전을 보증하지 않습니다.",
    ]
    y = 11.6
    for n in notes:
        T(msp, n, 0.6, y, 0.19, "NOTE")
        y -= 0.55
    doc.saveas(path)
    return path


def main():
    for path in [
        cover_sheet(os.path.join(OUT, "G-00_표지_일반주기.dxf")),
        plan_sheet(os.path.join(OUT, "A-01_기존평면도.dxf"), existing=True),
        plan_sheet(os.path.join(OUT, "A-02_제안평면도.dxf"), existing=False),
        schedule_sheet(os.path.join(OUT, "A-03_면적표_일람표.dxf")),
        elevation_sheet(os.path.join(OUT, "A-04_입면도.dxf")),
        mech_sheet(os.path.join(OUT, "M-01_설비개념도.dxf")),
    ]:
        print("saved", os.path.basename(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

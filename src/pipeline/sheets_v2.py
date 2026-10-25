"""
3571 Cassie - 허가용 도면 세트(DXF) 생성기 v2 (깨끗한 재작성).

시트 틀: A3 1:50 → 21.0 x 14.85 m (모델공간 실척)
  S-01 표지/일반주기, A-01 기존평면, A-02 제안평면,
  A-03 면적표/문·창 일람표, A-04 입면, M-01 설비개념
"""

import math
import os
import re
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


def bedroom_names():
    """ROOMS 에서 kind=='bedroom' 인 실 이름 목록 (시트 문구가 프로그램을 따라가도록)."""
    try:
        return [r["name"] for r in design.ROOMS if r.get("kind") == "bedroom" and r.get("name")]
    except Exception:
        return []


def bed_count():
    """침실 개수 = ROOMS 의 bedroom 실 수. 하드코딩 금지."""
    return len(bedroom_names())


def bed_label():
    """ROOMS 의 침실 이름을 묶은 표기 - 2침실이면 '침실A/B', 3침실이면 '침실A/B/C'."""
    names = bedroom_names()
    if not names:
        return "침실"
    if all(n.startswith("침실") for n in names):
        return "침실" + "/".join((n[2:].strip() or "?") for n in names)
    return " / ".join(names)


def egress_window_count():
    """이그레스 창 개수 = WINDOWS 이름에 '이그레스' 가 들어간 창 수."""
    try:
        return sum(1 for w in design.WINDOWS if "이그레스" in w["name"])
    except Exception:
        return 0

FW, FH = 21.0, 14.85            # 시트 틀 (A3 @ 1:50)
TB = (10.4, 0.0, 9.4, 4.4)      # 표제란 x, y, w, h
TXT_K = 1.35                    # SVG 렌더 폰트 크기 = 1.35 x TEXT height
FRAME_XMAX = 20.90              # 오른쪽 한계 (틀 21.0 에서 10 cm 안쪽)
WH_KO = ("가스 온수기가 차고 내부에 설치 — 거주공간 전환 시 이전 또는 "
         "연소공기·격리 조치 필요 (IRC M1307 / G2408)")

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


def text_w(s, h, k=TXT_K):
    """렌더 폭 추정 (m). SVG 는 font-size = 1.35*h 로 그리므로 글자당 1.35*h 로 본다."""
    return len(str(s)) * h * k


def fit_h(s, h, x, xmax=FRAME_XMAX, k=TXT_K, min_h=0.09):
    """(x, h) 에서 틀을 넘지 않는 최대 높이. 넘치지 않으면 h 그대로."""
    avail = max(0.5, xmax - x)
    return round(max(min_h, min(h, avail / (max(len(str(s)), 1) * k))), 3)


def wrap(s, n):
    """공백 기준 줄바꿈. 각 줄 <= n 자, 공백이 드문 한글은 강제 분할."""
    out, cur = [], ""
    for word in str(s).split(" "):
        cand = (cur + " " + word) if cur else word
        if len(cand) <= n:
            cur = cand
            continue
        if cur:
            out.append(cur)
        while len(word) > n:
            out.append(word[:n])
            word = word[n:]
        cur = word
    if cur:
        out.append(cur)
    return out or [""]


def wrap_notes(lines, n, indent="   "):
    """주기 목록을 n 자로 접는다. 이어지는 줄은 들여쓰기."""
    out = []
    for line in lines:
        parts = wrap(line, n)
        out.append(parts[0])
        for cont in parts[1:]:
            out.append(indent + cont)
    return out


def source_short(n=27):
    """디스클레이머용 짧은 출처 표기 (괄호 설명 제거 후 n 자로 자름)."""
    s = META.get("source_drawings", "A01.3/A01.4")
    s = " ".join(re.sub(r"\s*\([^)]*\)", "", str(s)).split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def water_heater_in_garage():
    """META['water_heater'] 가 차고 내 설치를 말하면 True (차고/garage 키워드)."""
    wh = str(META.get("water_heater") or "")
    return bool(wh.strip()) and ("차고" in wh or "garage" in wh.lower())


def water_heater_note():
    """차고 내 온수기 주기 문구. 해당 없으면 None."""
    return WH_KO if water_heater_in_garage() else None


def ftin(m):
    total_in = m / FT * 12.0
    # 반올림으로 12인치가 되면 다음 피트로 올린다 (21'-12" -> 22'-0")
    total_in = round(total_in * 20) / 20.0
    feet = int(total_in // 12)
    inch = total_in - feet * 12
    if abs(inch - round(inch)) < 0.05:
        inch = round(inch)
        if inch >= 12:
            feet, inch = feet + 1, 0
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
    """텍스트 한 줄. 틀 오른쪽을 넘으면 높이를 줄여 안쪽에 넣는다 (측정 기반)."""
    h = fit_h(s, h, x)
    msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement((x, y), align=align)


def sheet_frame(msp, code, title):
    msp.add_lwpolyline([(0, 0), (FW, 0), (FW, FH), (0, FH)], close=True,
                       dxfattribs={"layer": "TITLE"})
    x, y, w, h = TB
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                       dxfattribs={"layer": "TITLE"})
    # 1행: 시/주소가 project 안에 이미 들어 있으면 중복 표기하지 않는다 (폭 절약)
    _pj, _city = META.get("project", ""), META.get("city", "")
    head = _pj if (_city and _city in _pj) else f"{_pj}  |  {_city}"
    rows = [
        (head, 0.30),
        (f"{META.get('lot','')}", 0.20),
        (f"AFH 전환 ({META.get('existing_use_short', '기존 3-car garage')}) - 허가 제출용 스키매틱", 0.24),
        (f"원안: {META.get('architect','')}", 0.17),
        (f"Project No. {META.get('project_no','')}    Date {META.get('date','')}", 0.17),
        (f"SHEET {code}    {title}", 0.28),
    ]
    yy = y + h - 0.45
    for s, hh in rows:
        # 폭에 맞춰 높이를 줄인다 (T() 안에서도 한 번 더 확인)
        T(msp, s, x + 0.15, yy, min(hh, fit_h(s, hh, x + 0.15)), "TITLE")
        yy -= hh + 0.22
    # 디스클레이머: 2줄로 접어 표제란 안쪽에 넣는다 (2줄 x 45자, 높이 0.14)
    d_h = 0.14
    d1 = f"이 도면은 {source_short()} 기반 스키매틱입니다."
    d2 = "시공 전 실측 확인 필요. owner-builder 제출, 서명 불요."
    if max(text_w(d1, d_h), text_w(d2, d_h) + 0.15) > FRAME_XMAX - x:
        d_h = 0.12          # 그래도 넘치면 한 단계 더 줄인다
    T(msp, d1, x, y - 0.42, d_h, "NOTE")
    T(msp, d2, x + 0.15, y - 0.66, d_h, "NOTE")


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
        T(msp, META.get("existing_garage_label", "EXISTING 3-CAR GARAGE 790 SF"), 1.0, 12.2, 0.28, "TEXT")
        T(msp, META.get("existing_garage_label_line", "기존 차고도어 유지 (남측)"), 1.0, 0.9, 0.22, "NOTE")
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
            T(msp, META.get("opening_label", "기존 차고도어"), ox + width * 0.55, base + 2.3, 0.2, "NOTE")
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
        "EF-1 / EH-1: 욕실 배기팬 + 외벽 후드(역류방지). 관경/높이는 설계자 확인 필요.",
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
        f"1. 이 세트는 {META.get('source_drawings', 'Canarch Designs A01.3(기존)/A01.4(제안)')} 기반 스키매틱 BIM/도면입니다.",
        f"2. 실 치수는 {META.get('dim_source', 'A01.4 표기값')}을 사용했고, 벽 위치는 그 치수에 맞춘 배치입니다.",
        "3. 제출 전 추가 필요: 대지/주차 계획, 구조 검토, WSEC 계산, M/E/P 실시도,",
        "   연기·CO 경보 배치도, AFH(DSHS WAC 388-76) 검토, Owner-builder 선언서.",
        "4. " + META.get("ceiling_note", "천장고 10'-5\".") + " " + META.get("opening_note", "기존 차고도어 유지 + 내부 스킨월 마감(A01.4 주기)") + ".",
        f"5. 창호: 신규 5x4 슬라이더 {egress_window_count()}개(창턱 40\"), 침실별 이그레스 확보 목적.",
        "6. 자동검사 결과는 report.html 참조. 검사 통과는 법규·구조 안전을 보증하지 않습니다.",
    ]
    y = 11.6
    for n in wrap_notes(notes, 74, "   "):
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
"""
3571 Cassie - 허가용 도면 세트(DXF) 생성기 v2 (깨끗한 재작성).

시트 틀: A3 1:50 → 21.0 x 14.85 m (모델공간 실척)
  S-01 표지/일반주기, A-01 기존평면, A-02 제안평면,
  A-03 면적표/문·창 일람표, A-04 입면, M-01 설비개념
"""

import math
import os
import re
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
TXT_K = 1.35                    # SVG 렌더 폰트 크기 = 1.35 x TEXT height
FRAME_XMAX = 20.90              # 오른쪽 한계 (틀 21.0 에서 10 cm 안쪽)
WH_KO = ("가스 온수기가 차고 내부에 설치 — 거주공간 전환 시 이전 또는 "
         "연소공기·격리 조치 필요 (IRC M1307 / G2408)")

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


def text_w(s, h, k=TXT_K):
    """렌더 폭 추정 (m). SVG 는 font-size = 1.35*h 로 그리므로 글자당 1.35*h 로 본다."""
    return len(str(s)) * h * k


def fit_h(s, h, x, xmax=FRAME_XMAX, k=TXT_K, min_h=0.09):
    """(x, h) 에서 틀을 넘지 않는 최대 높이. 넘치지 않으면 h 그대로."""
    avail = max(0.5, xmax - x)
    return round(max(min_h, min(h, avail / (max(len(str(s)), 1) * k))), 3)


def wrap(s, n):
    """공백 기준 줄바꿈. 각 줄 <= n 자, 공백이 드문 한글은 강제 분할."""
    out, cur = [], ""
    for word in str(s).split(" "):
        cand = (cur + " " + word) if cur else word
        if len(cand) <= n:
            cur = cand
            continue
        if cur:
            out.append(cur)
        while len(word) > n:
            out.append(word[:n])
            word = word[n:]
        cur = word
    if cur:
        out.append(cur)
    return out or [""]


def wrap_notes(lines, n, indent="   "):
    """주기 목록을 n 자로 접는다. 이어지는 줄은 들여쓰기."""
    out = []
    for line in lines:
        parts = wrap(line, n)
        out.append(parts[0])
        for cont in parts[1:]:
            out.append(indent + cont)
    return out


def source_short(n=27):
    """디스클레이머용 짧은 출처 표기 (괄호 설명 제거 후 n 자로 자름)."""
    s = META.get("source_drawings", "A01.3/A01.4")
    s = " ".join(re.sub(r"\s*\([^)]*\)", "", str(s)).split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def water_heater_in_garage():
    """META['water_heater'] 가 차고 내 설치를 말하면 True (차고/garage 키워드)."""
    wh = str(META.get("water_heater") or "")
    return bool(wh.strip()) and ("차고" in wh or "garage" in wh.lower())


def water_heater_note():
    """차고 내 온수기 주기 문구. 해당 없으면 None."""
    return WH_KO if water_heater_in_garage() else None


def ftin(m):
    total_in = m / FT * 12.0
    # 반올림으로 12인치가 되면 다음 피트로 올린다 (21'-12" -> 22'-0")
    total_in = round(total_in * 20) / 20.0
    feet = int(total_in // 12)
    inch = total_in - feet * 12
    if abs(inch - round(inch)) < 0.05:
        inch = round(inch)
        if inch >= 12:
            feet, inch = feet + 1, 0
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
    """텍스트 한 줄. 틀 오른쪽을 넘으면 높이를 줄여 안쪽에 넣는다 (측정 기반)."""
    h = fit_h(s, h, x)
    msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement((x, y), align=align)


def sheet_frame(msp, code, title):
    msp.add_lwpolyline([(0, 0), (FW, 0), (FW, FH), (0, FH)], close=True,
                       dxfattribs={"layer": "TITLE"})
    x, y, w, h = TB
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                       dxfattribs={"layer": "TITLE"})
    # 1행: 시/주소가 project 안에 이미 들어 있으면 중복 표기하지 않는다 (폭 절약)
    _pj, _city = META.get("project", ""), META.get("city", "")
    head = _pj if (_city and _city in _pj) else f"{_pj}  |  {_city}"
    rows = [
        (head, 0.30),
        (f"{META.get('lot','')}", 0.20),
        (f"AFH 전환 ({META.get('existing_use_short', '기존 3-car garage')}) - 허가 제출용 스키매틱", 0.24),
        (f"원안: {META.get('architect','')}", 0.17),
        (f"Project No. {META.get('project_no','')}    Date {META.get('date','')}", 0.17),
        (f"SHEET {code}    {title}", 0.28),
    ]
    yy = y + h - 0.45
    for s, hh in rows:
        # 폭에 맞춰 높이를 줄인다 (T() 안에서도 한 번 더 확인)
        T(msp, s, x + 0.15, yy, min(hh, fit_h(s, hh, x + 0.15)), "TITLE")
        yy -= hh + 0.22
    # 디스클레이머: 2줄로 접어 표제란 안쪽에 넣는다 (2줄 x 45자, 높이 0.14)
    d_h = 0.14
    d1 = f"이 도면은 {source_short()} 기반 스키매틱입니다."
    d2 = "시공 전 실측 확인 필요. owner-builder 제출, 서명 불요."
    if max(text_w(d1, d_h), text_w(d2, d_h) + 0.15) > FRAME_XMAX - x:
        d_h = 0.12          # 그래도 넘치면 한 단계 더 줄인다
    T(msp, d1, x, y - 0.42, d_h, "NOTE")
    T(msp, d2, x + 0.15, y - 0.66, d_h, "NOTE")


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
        T(msp, META.get("existing_garage_label", "EXISTING 3-CAR GARAGE 790 SF"), 1.0, 12.2, 0.28, "TEXT")
        T(msp, META.get("existing_garage_label_line", "기존 차고도어 유지 (남측)"), 1.0, 0.9, 0.22, "NOTE")
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
            T(msp, META.get("opening_label", "기존 차고도어"), ox + width * 0.55, base + 2.3, 0.2, "NOTE")
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
        "EF-1 / EH-1: 욕실 배기팬 + 외벽 후드(역류방지). 관경/높이는 설계자 확인 필요.",
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
        f"1. 이 세트는 {META.get('source_drawings', 'Canarch Designs A01.3(기존)/A01.4(제안)')} 기반 스키매틱 BIM/도면입니다.",
        f"2. 실 치수는 {META.get('dim_source', 'A01.4 표기값')}을 사용했고, 벽 위치는 그 치수에 맞춘 배치입니다.",
        "3. 제출 전 추가 필요: 대지/주차 계획, 구조 검토, WSEC 계산, M/E/P 실시도,",
        "   연기·CO 경보 배치도, AFH(DSHS WAC 388-76) 검토, Owner-builder 선언서.",
        "4. " + META.get("ceiling_note", "천장고 10'-5\".") + " " + META.get("opening_note", "기존 차고도어 유지 + 내부 스킨월 마감(A01.4 주기)") + ".",
        "5. 창호: 신규 5x4 슬라이더 3개(창턱 40\"), 침실별 이그레스 확보 목적.",
        "6. 자동검사 결과는 report.html 참조. 검사 통과는 법규·구조 안전을 보증하지 않습니다.",
    ]
    y = 11.6
    for n in wrap_notes(notes, 74, "   "):
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

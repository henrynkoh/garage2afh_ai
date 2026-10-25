"""
3571 Cassie - 허가 보강 시트 6장 (좌표 수정판, v2).

평면 위 심볼은 모두 피트 좌표로 적고 pt()로 미터 변환한다.
표/주기는 시트 공간(미터)에 그린다.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYDEPS = os.environ.get("HOUSEBIM_PYDEPS") or os.path.join(ROOT, "pydeps")
if os.path.isdir(PYDEPS) and PYDEPS not in sys.path:
    sys.path.append(PYDEPS)
DESIGN_DIR = os.environ.get("HOUSEBIM_DESIGN_DIR", os.path.join(ROOT, "projects", "3571-cassie"))
if DESIGN_DIR not in sys.path:
    sys.path.insert(0, DESIGN_DIR)

import sheets_v2 as base
from sheets_v2 import HOUSE, T, ftin, new_doc, outline, rect_area, sheet_frame
import design

FT = 0.3048
OUT = base.OUT
META = design.META


def pt(x_ft, y_ft):
    return (x_ft * FT, y_ft * FT)


def tag(msp, s, x_m, y_m, layer="TEXT", h=0.15):
    T(msp, s, x_m, y_m, h, layer)


def plan(msp):
    base.draw_plan_body(msp, existing=False, labels=True)


def note_block(msp, lines, x_m=10.8, y_m=9.6, step=0.42, h=0.14):
    y = y_m
    for line in lines:
        tag(msp, line, x_m, y, "NOTE", h)
        y -= step
    return y


def sched(msp, rows, x_m=10.8, y_m=12.4, cols=None, step=0.4, h=0.14):
    cols = cols or [0.0, 1.4, 3.6, 6.4]
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            T(msp, val, x_m + cols[c], y_m - r * step, h, "TITLE" if r == 0 else "TEXT")


# ------------------------------------------------------------------ LS-01
def sheet_life_safety(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "LS-01", "연기·CO 경보 배치도")
    plan(msp)

    smokes = [("SD-1", 4.0, 6.0), ("SD-2", 16.0, 6.0), ("SD-3", 7.5, 14.5),
              ("SD-4", 22.0, 14.5), ("SD-5", 11.0, 21.5), ("SD-6", 24.5, 21.5),
              ("SD-7", 8.0, 22.0)]
    for name, fx, fy in smokes:
        msp.add_circle(pt(fx, fy), 0.11, dxfattribs={"layer": "NOTE"})
        tag(msp, name, pt(fx, fy)[0] - 0.16, pt(fx, fy)[1] + 0.14, "NOTE", 0.11)

    cos = [("CO-1", 7.5, 15.6), ("CO-2", 22.0, 15.6), ("CO-3", 26.0, 3.0)]
    for name, fx, fy in cos:
        x, y = pt(fx, fy)
        msp.add_lwpolyline([(x - 0.1, y - 0.1), (x + 0.1, y - 0.1),
                            (x + 0.1, y + 0.1), (x - 0.1, y + 0.1)],
                           close=True, dxfattribs={"layer": "DOOR"})
        tag(msp, name, x - 0.16, y + 0.14, "DOOR", 0.11)

    note_block(msp, [
        "SD = 연기감지기 / CO = 일산화탄소 감지기 (전부 상호연동)",
        "SD: 침실 내부 + 침실 출입구 인접 + 복도 (IRC R314.3)",
        "CO: 취침구역 인접 + 차고 인접 구역 (IRC R315.5)",
        "전원: 상시전원 + 배터리 백업(정전 7일), WAC R314.4",
        "감지기: 조명/팬에서 3ft 이격, 벽-천장 모서리 12in 이내",
        "이그레스 창: 침실A/B/C (순개구부 5.7 sqft 이상 확인)",
    ], y_m=9.4)
    doc.saveas(path)
    return path


# ------------------------------------------------------------------ M-02
def sheet_mechanical(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "M-02", "기계 설비 평면")
    plan(msp)

    # EF-1 욕실 배기 → 서측 외벽 후드
    msp.add_circle(pt(2.4, 6.0), 0.1, dxfattribs={"layer": "PIPE-W"})
    tag(msp, "EF-1", pt(2.4, 6.0)[0] - 0.05, pt(2.4, 6.0)[1] + 0.18, "PIPE-W", 0.12)
    msp.add_line(pt(2.4, 6.0), pt(0.4, 6.0), dxfattribs={"layer": "PIPE-W"})
    tag(msp, "hood", pt(0.4, 6.0)[0] - 0.35, pt(0.4, 6.0)[1] - 0.2, "PIPE-W", 0.11)

    # CU-1 콘덴서 (동측 외부)
    x, y = pt(32.6, 8.0)
    msp.add_lwpolyline([(x - 0.35, y - 0.35), (x + 0.35, y - 0.35),
                        (x + 0.35, y + 0.35), (x - 0.35, y + 0.35)],
                       close=True, dxfattribs={"layer": "DOOR"})
    tag(msp, "CU-1", x - 0.16, y - 0.05, "DOOR", 0.12)

    # 냉매 배관: CU-1 → 남측 → 서측 → HVAC 실내기
    msp.add_line(pt(32.6, 8.0), pt(2.3, 8.0), dxfattribs={"layer": "PIPE-W"})
    msp.add_line(pt(2.3, 8.0), pt(2.3, 18.4), dxfattribs={"layer": "PIPE-W"})
    tag(msp, "refrigerant", pt(12.0, 8.0)[0], pt(12.0, 8.0)[1] + 0.12, "PIPE-W", 0.11)

    # AHU (HVAC closet)
    xa, ya = pt(2.3, 18.4)
    msp.add_lwpolyline([(xa - 0.35, ya - 0.25), (xa + 0.35, ya - 0.25),
                        (xa + 0.35, ya + 0.25), (xa - 0.35, ya + 0.25)],
                       close=True, dxfattribs={"layer": "WALL-INT"})
    tag(msp, "AHU", xa - 0.1, ya - 0.05, "TEXT", 0.11)

    # 공급 디퓨저
    for fx, fy in [(16.0, 6.0), (8.0, 6.0), (11.0, 21.0), (24.5, 21.0), (26.0, 6.0)]:
        dx, dy = pt(fx, fy)
        msp.add_lwpolyline([(dx - 0.12, dy - 0.08), (dx + 0.12, dy - 0.08),
                            (dx + 0.12, dy + 0.08), (dx - 0.12, dy + 0.08)],
                           close=True, dxfattribs={"layer": "WINDOW"})

    # DH-1 드라이어 (잠정) 남측 벽
    msp.add_circle(pt(8.0, 1.2), 0.1, dxfattribs={"layer": "PIPE-D"})
    tag(msp, "DH-1", pt(8.0, 1.2)[0] - 0.1, pt(8.0, 1.2)[1] + 0.16, "PIPE-D", 0.11)

    sched(msp, [
        ("기호", "설비", "사양", "비고"),
        ("EF-1", "욕실 배기팬", "80 CFM", "후드+역류방지"),
        ("AHU", "실내기", "1.5 ton", "냉매 R-454B"),
        ("CU-1", "실외기", "1.5 ton", "패드 이격 확인"),
        ("DH-1", "드라이어", "4in 덕트", "위치 TBC"),
    ], y_m=12.6)
    note_block(msp, [
        "장비 용량은 예비안. 최종 선정·경로는 기계설비 설계자 확정.",
        "욕실 배기: 덕트 최단, 외벽 후드 높이는 설계자 확인.",
        "전기 히트펌프 가정(연소기기 없음) — CO는 차고 인접 기준.",
    ], y_m=9.4)
    doc.saveas(path)
    return path


# ------------------------------------------------------------------ E-01
def sheet_electrical(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "E-01", "전기 설비 평면")
    plan(msp)

    xp, yp = pt(3.0, 14.5)
    msp.add_lwpolyline([(xp - 0.2, yp - 0.15), (xp + 0.2, yp - 0.15),
                        (xp + 0.2, yp + 0.15), (xp - 0.2, yp + 0.15)],
                       close=True, dxfattribs={"layer": "DOOR"})
    tag(msp, "LP", xp - 0.07, yp - 0.05, "DOOR", 0.11)

    for fx, fy in [(1.0, 3.0), (1.0, 8.0), (1.0, 24.0), (6.0, 1.0), (10.0, 1.0),
                   (15.0, 1.0), (20.0, 1.0), (26.0, 1.0), (28.0, 6.0),
                   (7.0, 26.0), (12.0, 26.0), (20.0, 26.0), (26.0, 26.0),
                   (18.0, 15.5), (29.0, 15.5)]:
        msp.add_circle(pt(fx, fy), 0.07, dxfattribs={"layer": "NOTE"})

    for fx, fy in [(3.0, 6.0), (8.0, 6.0), (16.0, 6.0), (26.0, 6.0),
                   (8.0, 14.6), (20.0, 14.6), (11.0, 21.5), (24.5, 21.5)]:
        x, y = pt(fx, fy)
        msp.add_line((x - 0.14, y - 0.14), (x + 0.14, y + 0.14), dxfattribs={"layer": "DOOR"})
        msp.add_line((x - 0.14, y + 0.14), (x + 0.14, y - 0.14), dxfattribs={"layer": "DOOR"})

    sched(msp, [
        ("회로", "용도", "차단기", "비고"),
        ("C1", "조명 (거실/복도)", "15A", "LED"),
        ("C2", "침실 조명·콘센트", "20A", "AFCI"),
        ("C3", "욕실", "20A", "GFCI"),
        ("C4", "사무실 콘센트", "20A", "AFCI"),
        ("C5", "AHU / CU-1", "30A", "전용"),
        ("C6", "온수기", "30A", "전용"),
        ("C7", "연기·CO 경보", "15A", "상호연동"),
    ], y_m=12.6, cols=[0.0, 1.2, 4.0, 6.4], step=0.38)
    note_block(msp, [
        "○ 콘센트 (6ft 이내 간격, IRC E3901.2) / ✕ 조명",
        "욕실 GFCI, 침실 AFCI (IRC E3902)",
        "연기·CO는 상호연동 배선 + 배터리 백업",
        "회로 구성은 예비안 — 전기설계자 확정 필요",
    ], y_m=8.6)
    doc.saveas(path)
    return path


# ------------------------------------------------------------------ P-02
def sheet_plumbing(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "P-02", "급배수 평면")
    plan(msp)

    # 급수: 계량기(서측) → 온수기 → 욕실
    msp.add_line(pt(0.3, 6.0), pt(2.3, 6.0), dxfattribs={"layer": "PIPE-W"})
    msp.add_line(pt(2.3, 6.0), pt(2.3, 18.0), dxfattribs={"layer": "PIPE-W"})
    tag(msp, "급수 3/4in", pt(0.5, 6.3)[0], pt(0.5, 6.3)[1], "PIPE-W", 0.11)

    xw, yw = pt(2.3, 18.0)
    msp.add_lwpolyline([(xw - 0.25, yw - 0.25), (xw + 0.25, yw - 0.25),
                        (xw + 0.25, yw + 0.25), (xw - 0.25, yw + 0.25)],
                       close=True, dxfattribs={"layer": "PIPE-W"})
    tag(msp, "WH 50gal", xw - 0.22, yw + 0.34, "PIPE-W", 0.11)

    # 욕실 기구
    for name, fx, fy in [("WC", 2.0, 9.0), ("WHB", 2.0, 6.5), ("SH", 2.0, 4.0)]:
        msp.add_circle(pt(fx, fy), 0.1, dxfattribs={"layer": "PIPE-D"})
        tag(msp, name, pt(fx, fy)[0] + 0.14, pt(fx, fy)[1] - 0.04, "PIPE-D", 0.11)

    # 배수: 욕실 → 남측 → 외부
    msp.add_line(pt(2.0, 3.0), pt(2.0, 1.2), dxfattribs={"layer": "PIPE-D"})
    msp.add_line(pt(2.0, 1.2), pt(14.0, 1.2), dxfattribs={"layer": "PIPE-D"})
    tag(msp, "배수 3in, 1/4in/ft", pt(5.0, 1.4)[0], pt(5.0, 1.4)[1], "PIPE-D", 0.11)

    sched(msp, [
        ("기구", "수량", "급수", "배수"),
        ("WC", "1", "1/2in", "3in"),
        ("세면기", "1", "3/8in", "1-1/2in"),
        ("샤워", "1", "1/2in", "2in"),
        ("온수기", "1", "3/4in", "—"),
    ], y_m=12.4)
    note_block(msp, [
        "급수 3/4in → 온수기 → 욕실 분기(1/2in, 3/8in)",
        "배수 3in 주관, 구배 1/4in/ft(2%), 통기 2in (IRC P3103)",
        "관경·기구단위는 예비안. 배관설계자 확정 필요.",
    ], y_m=9.0)
    doc.saveas(path)
    return path


# ------------------------------------------------------------------ S-01
def sheet_structural(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "S-01", "구조 계획도 (예비)")
    base.draw_plan_body(msp, existing=False, labels=False)

    for w in design.WALLS:
        if w["exterior"]:
            msp.add_lwpolyline(outline(w), close=True, dxfattribs={"layer": "WALL-EXT"})

    # 개구부 헤더 표시 (차고도어 또는 카포트 오픈 페이스 - META)
    msp.add_line(pt(21.5, 0.0), pt(31.0, 0.0), dxfattribs={"layer": "DOOR"})
    tag(msp, META.get("opening_label", "기존 차고도어 개구부"), pt(22.0, 0.6)[0], pt(22.0, 0.6)[1], "DOOR", 0.11)
    tag(msp, "기존 외벽(유지) / 신규 파티션(비내력 2x4)", pt(0.4, 27.4)[0], pt(0.4, 27.4)[1], "NOTE", 0.12)

    sched(msp, [
        ("부재", "위치", "예비 단면", "비고"),
        ("헤더 H1", META.get("opening_label", "차고도어 개구부"), "2-1.75x11.875 LVL", "EOR 확인"),
        ("헤더 H2", "침실C/복도", "2x10 DF#2", "비내력"),
        ("스터드", "신규 파티션", "2x4 @16 o.c.", "8ft"),
        ("슬래브", META.get("slab_label", "기존 차고 바닥"), "기존 유지", "레벨·균열"),
        ("앵커", "신규 벽 하부", "1/2in @48in", "슬래브 천공"),
    ], y_m=12.2, cols=[0.0, 1.6, 3.8, 6.6], step=0.4)
    note_block(msp, [
        "예비 구조 계획입니다. 시 담당자 확인에 따라 구조기술사 서명 없이 제출하며, 요청 시 하중 검토를 보완합니다.",
        "기존 슬래브 두께·철근 상태는 현장 확인 필요(거실 마감 하중).",
        "신규 파티션은 비내력으로 계획, 개구부 신설 시 하중 경로 EOR 확인.",
    ], y_m=9.4)
    doc.saveas(path)
    return path


# ------------------------------------------------------------------ EN-01
def sheet_energy(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "EN-01", "WSEC 외피 요약 (예비)")

    x1, y1, x2, y2 = HOUSE["footprint"]
    h = HOUSE["wall_height"]
    perim = 2 * ((x2 - x1) + (y2 - y1))
    gross = perim * h
    win = sum(w["w"] * w["h"] for w in design.WINDOWS)
    door = sum(d["w"] * d["h"] for d in design.DOORS)
    wall_net = max(0.0, gross - win - door)
    ceil = (x2 - x1) * (y2 - y1)

    rows = [
        ("부위", "면적(m2)", "면적(sf)", "가정 U", "비고"),
        ("외벽(순)", f"{wall_net:.1f}", f"{wall_net / (FT * FT):.0f}", "0.048", "R-21"),
        ("천장", f"{ceil:.1f}", f"{ceil / (FT * FT):.0f}", "0.020", "R-49"),
        ("바닥", f"{ceil:.1f}", f"{ceil / (FT * FT):.0f}", "0.055", "슬래브"),
        ("창호", f"{win:.1f}", f"{win / (FT * FT):.0f}", "0.30", "U-0.30"),
        ("문", f"{door:.1f}", f"{door / (FT * FT):.0f}", "0.20", "내부문"),
    ]
    sched(msp, rows, x_m=0.8, y_m=12.6, cols=[0.0, 2.6, 5.2, 7.4, 9.4], step=0.46, h=0.16)

    ua = wall_net * 0.048 + ceil * 0.020 + ceil * 0.055 + win * 0.30 + door * 0.20
    T(msp, f"UA 합계 ≈ {ua:.1f} W/K (예비 개산, 침투·열교 제외)", 0.8, 9.6, 0.22, "TITLE")

    note_block(msp, [
        "1) WSEC 2021(워싱턴) 주거 외피·창호·기밀 기준 충족 확인 필요",
        "2) 창호 U-0.30 이하, SHGC 지역 상한 확인 (Zone 5 marine)",
        "3) 외벽 R-21 + 외장 단열 또는 R-13+ci 대안 검토",
        "4) 천장 R-49, 슬래브 주변 단열, 관통부 기밀(블로우도어 테스트)",
        "5) 정식 컴플라이언스는 WSEC 툴/에너지 분석가 검토로 확정",
        "6) 환기: 욕실 80 CFM, 주방 후드, 전체 환기 1대 (VIAQ)",
        "이 표는 예비 개산이며 WSEC 컴플라이언스 문서가 아닙니다.",
    ], x_m=0.8, y_m=8.8, step=0.44, h=0.15)
    doc.saveas(path)
    return path


def main():
    for p in [
        sheet_life_safety(os.path.join(OUT, "LS-01_연기CO경보.dxf")),
        sheet_mechanical(os.path.join(OUT, "M-02_기계설비평면.dxf")),
        sheet_electrical(os.path.join(OUT, "E-01_전기설비평면.dxf")),
        sheet_plumbing(os.path.join(OUT, "P-02_급배수평면.dxf")),
        sheet_structural(os.path.join(OUT, "S-01_구조계획도.dxf")),
        sheet_energy(os.path.join(OUT, "EN-01_에너지요약.dxf")),
    ]:
        print("saved", os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())

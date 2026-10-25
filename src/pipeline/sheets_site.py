"""
C-01 대지·주차 계획 (owner-builder 제출용, 스키매틱).

META 값만으로 대지/건물/주차를 그린다 (원래 3571 Cassie 전용 하드코딩이었다).
  lot_sf, coverage_pct, lot_sf_survey/lot_sf_assessor, ground_floor_sf, parking_spaces
  house_label, parking_label, site_notes  ← 없으면 3571 기본값을 쓴다
측량도 없이 작성한 개념 도면이므로, 실제 세트백·경계는 측량도로 확인해야 한다.
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
from sheets_v2 import HOUSE, T, ftin, new_doc, sheet_frame
from sheets_v2 import wrap_notes
import design

FT = 0.3048
META = design.META
OUT = base.OUT

S = 0.25        # 1:200 (시트는 1:50 기준)

# 대지: 면적은 META, 형상은 0.65 비율의 개념 사각형 (측량도 없음)
LOT_SF = float(META.get("lot_sf") or 9411)
LOT_W = META.get("lot_w_ft") or round((LOT_SF * 0.65) ** 0.5, 1)
LOT_D = META.get("lot_d_ft") or round(LOT_SF / LOT_W, 1)
N_PARK = int(META.get("parking_spaces", 3))
GROUND = float(META.get("ground_floor_sf") or 1160)
HOUSE_LABEL = META.get("house_label", "기존 주택 (2층, 2,621 SF)")
PARK_LABEL = META.get("parking_label", "기존 진입로 / 주차 3면 (유지)")


def mm(v_ft):
    """피트 → 모델공간 미터(1:200 반영)."""
    return v_ft * FT * S


def note(msp, lines, x=10.8, y=12.6, step=0.42, h=0.14):
    yy = y
    for line in lines:
        T(msp, line, x, yy, h, "NOTE")
        yy -= step
    return yy


def main_sheet(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "C-01", "대지·주차 계획 (1:200)")

    # 대지 경계
    msp.add_lwpolyline([(0, 0), (mm(LOT_W), 0), (mm(LOT_W), mm(LOT_D)), (0, mm(LOT_D))],
                       close=True, dxfattribs={"layer": "DIM"})
    T(msp, f"LOT {META.get('lot_sf_assessor', META.get('lot_sf_survey', 9357)):,} SF "
           f"(카운티) · 피복률 {META.get('coverage_pct', 37.6)}% · 1:200",
      0.0, mm(LOT_D) + 0.22, 0.17, "DIM")

    # 기존 주택 (지상층 footprint 개념)
    hw = round((GROUND * 0.9) ** 0.5, 1)
    hd = round(GROUND / hw, 1)
    hx = 8.0
    hy = min(max(6.0, round(LOT_D * 0.22, 1)), round(LOT_D - hd - 6, 1))
    msp.add_lwpolyline([(mm(hx), mm(hy)), (mm(hx + hw), mm(hy)),
                        (mm(hx + hw), mm(hy + hd)), (mm(hx), mm(hy + hd))],
                       close=True, dxfattribs={"layer": "WALL-EXT"})
    T(msp, HOUSE_LABEL, mm(hx + 2), mm(hy + hd / 2), 0.16, "TEXT")
    T(msp, "AFH 범위: " + META.get("existing_use_short", "기존 차고"),
      mm(hx + 2), mm(hy + hd / 2 - 4), 0.13, "TEXT")

    # 진입로 / 주차면
    msp.add_lwpolyline([(mm(hx), 0.2), (mm(hx), mm(hy))], dxfattribs={"layer": "ROOM"})
    msp.add_lwpolyline([(mm(hx + 12), 0.2), (mm(hx + 12), mm(hy))], dxfattribs={"layer": "ROOM"})
    stall = min(9.0, max(4.0, (hy - 2.4) / max(1, N_PARK)))
    for i in range(N_PARK):
        y0 = 1.2 + i * stall
        msp.add_lwpolyline([(mm(hx + 0.5), mm(y0)), (mm(hx + 11.5), mm(y0)),
                            (mm(hx + 11.5), mm(min(y0 + stall - 1.0, hy - 0.5))),
                            (mm(hx + 0.5), mm(min(y0 + stall - 1.0, hy - 0.5)))],
                           close=True, dxfattribs={"layer": "DOOR"})
        T(msp, f"P{i+1}", mm(hx + 1), mm(y0 + stall / 2), 0.12, "DOOR")
    T(msp, PARK_LABEL, mm(hx), -0.45, 0.16, "TEXT")

    msp.add_line((mm(hx + hw + 2), mm(10)), (mm(LOT_W - 3), mm(10)), dxfattribs={"layer": "DIM"})
    T(msp, "전면 세트백 (측량도 확인)", mm(hx + hw + 3), mm(10) + 0.12, 0.13, "NOTE")
    T(msp, "측면 세트백", 0.0, mm(LOT_D / 2), 0.13, "NOTE")

    note(msp, wrap_notes(META.get("site_notes") or [
        "1. 근거: 측량도 L2-25T2-3R (2015, J. Kerzie Hoyles LLC), 시 접수 2016-03-02.",
        "2. 측량도 표지: 대지 9,357 SF, 구조물 2,824 SF, 진입로 1,706 SF, 피복률 37.6%.",
        "3. 카운티 세무기록: 대지 9,411 SF, LT 7. 측량도 표지는 LOT 1 → 번호 상이(확인 필요).",
        "4. Zoning은 측량도 표기(R4R)를 기재. 현행 조례 확인 필요.",
        "5. 주차 3면 유지. 공사 범위는 건물 내부로 대지 형질 변경 없음.",
    ], 50, "   "), x=10.8, y=10.2, step=0.40)
    doc.saveas(path)
    return path


if __name__ == "__main__":
    print("saved", os.path.basename(main_sheet(os.path.join(OUT, "C-01_대지주차계획.dxf"))))

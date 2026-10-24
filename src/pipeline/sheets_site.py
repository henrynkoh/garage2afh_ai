"""
C-01 대지·주차 계획 (owner-builder 제출용, 스키매틱).

공적 기록 기반: 대지 9,408 SF, 기존 주택(2층, 2,621 SF), 기존 3-car driveway.
측량도(plat/survey) 없이 작성한 개념 도면이므로, 실제 세트백·경계는 측량도로 확인해야 한다.
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
import design

FT = 0.3048
META = design.META
OUT = base.OUT

LOT_W = 78.0   # ft (개념)
LOT_D = 120.0  # ft (개념) → 9,360 SF ≈ 기록 9,408 SF
S = 0.25       # 1:200 으로 축소 (시트는 1:50 기준)


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
    T(msp, f"LOT {META.get('lot_sf_survey', 9357):,} SF (측량) · 피복률 {META.get('coverage_pct', 37.6)}% · 1:200",
      0.0, mm(LOT_D) + 0.22, 0.17, "DIM")

    # 기존 주택 (지상층 footprint 개념 40' x 35')
    hx, hy, hw, hd = 8.0, 30.0, 40.0, 35.0
    msp.add_lwpolyline([(mm(hx), mm(hy)), (mm(hx + hw), mm(hy)),
                        (mm(hx + hw), mm(hy + hd)), (mm(hx), mm(hy + hd))],
                       close=True, dxfattribs={"layer": "WALL-EXT"})
    T(msp, "기존 주택 (2층, 2,621 SF)", mm(hx + 2), mm(hy + hd / 2), 0.16, "TEXT")
    T(msp, "AFH 전환부: 기존 차고", mm(hx + 2), mm(hy + hd / 2 - 4), 0.13, "TEXT")

    # 진입로 / 주차 3면
    msp.add_lwpolyline([(mm(hx), 0.2), (mm(hx), mm(hy))], dxfattribs={"layer": "ROOM"})
    msp.add_lwpolyline([(mm(hx + 12), 0.2), (mm(hx + 12), mm(hy))], dxfattribs={"layer": "ROOM"})
    for i in range(3):
        y0 = 3 + i * 9
        msp.add_lwpolyline([(mm(hx + 0.5), mm(y0)), (mm(hx + 11.5), mm(y0)),
                            (mm(hx + 11.5), mm(y0 + 8)), (mm(hx + 0.5), mm(y0 + 8))],
                           close=True, dxfattribs={"layer": "DOOR"})
        T(msp, f"P{i+1}", mm(hx + 1), mm(y0 + 3.4), 0.12, "DOOR")
    T(msp, "기존 진입로 / 주차 3면 (유지)", mm(hx), -0.45, 0.16, "TEXT")

    msp.add_line((mm(hx + hw + 2), mm(10)), (mm(LOT_W - 3), mm(10)), dxfattribs={"layer": "DIM"})
    T(msp, "전면 세트백 (측량도 확인)", mm(hx + hw + 3), mm(10) + 0.12, 0.13, "NOTE")
    T(msp, "측면 세트백", 0.0, mm(60), 0.13, "NOTE")


    note(msp, [
        "1. 근거: 측량도 L2-25T2-3R (2015, J. Kerzie Hoyles LLC), 시 접수 2016-03-02.",
        "2. 측량도 표지: 대지 9,357 SF, 구조물 2,824 SF, 진입로 1,706 SF, 피복률 37.6%.",
        "3. 카운티 세무기록: 대지 9,411 SF, LT 7. 측량도 표지는 LOT 1 → 번호 상이(확인 필요).",
        "4. Zoning은 측량도 표기(R4R)를 기재. 현행 조례 확인 필요.",
        "5. 주차 3면 유지. 공사 범위는 건물 내부로 대지 형질 변경 없음.",
    ], y=9.0)
    doc.saveas(path)
    return path


if __name__ == "__main__":
    print("saved", os.path.basename(main_sheet(os.path.join(OUT, "C-01_대지주차계획.dxf"))))

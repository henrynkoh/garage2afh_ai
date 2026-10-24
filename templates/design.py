"""
DESIGN TEMPLATE - single source of truth for one garage-to-AFH conversion.

THIS FILE IS THE SINGLE SOURCE OF TRUTH. Every sheet, every automated check,
the material takeoff and the budget read their numbers from here. If a number
is wrong on a drawing, fix it here - never edit the DXF, the SVG or the PDF.
The only other source of truth is the county/survey record, which this file
must copy verbatim (and any mismatch must be logged on G-06, the coordination
log).

Workflow:
    g2a.py new "<address>" --parcel <parcel> --lot-sf <sf>   # copies this file
    edit projects/<slug>/design.py                           # rooms, walls, openings
    g2a.py build <slug> && g2a.py bind <slug> && g2a.py check <slug>

Placeholders below (PROJECT ADDRESS / CITY, ST ZIP / 00000000000 / lot_sf 0)
are replaced by `g2a.py new`. Anything still reading like a placeholder is
treated as a hard fail by the validator.
"""
"""
3571 Cassie Dr SW - 차고 → AFH 전환 (Tumwater, WA) 설계 데이터

출처: Canarch Designs A01.4 "Ground Floor Plan - New" (OCT 2026, project CMN/25/122)
       + A01.3 "Ground Floor Plan - Before"

이 파일은 A01.4 의 방 이름/치수를 옮긴 스키매틱 모델입니다.
- 방 크기는 도면에 적힌 치수(예: BATH 12'-10" x 5', BEDROOM A 12'-10" x 9'-7")를 사용했습니다.
- 벽 위치는 그 치수들이 맞물리도록 배치한 것이므로, 시공 전 A01.4 원본과 실측 확인이 필요합니다.
- 단위: 미터(m). 좌표: 남서쪽 모서리 (0,0), X=동, Y=북.
"""

FT = 0.3048


def ft(*parts):
    """(피트, 인치) → 미터. ft(12, 10) == 12'-10" """
    feet = parts[0]
    inches = parts[1] if len(parts) > 1 else 0
    return round((feet + inches / 12.0) * FT, 4)


META = {
    "project": "PROJECT ADDRESS",
    "city": "CITY, ST ZIP",
    "lot": "LOT 0, SUBDIVISION NAME · Tax-ID 0000-00-00000",
    "legal": "SECTION 28 TOWNSHIP 18 RANGE 2W QUARTER NE SE & SE SE PLAT CHAPPAREL LANDING DIVISION 2 LT 7 DOCUMENT 4490930",
    "scope": "기존 3-car garage → AFH 거주구역 전환 (침실 3 + 통합욕실)",
    "architect": "Canarch Designs (Caleb Mongare) - A01.3 / A01.4",
    "project_no": "CMN/25/122",
    "date": "OCT 2026",
    "ceiling": ft(10, 5),
    "existing_garage_sf": 790,
    "internal_sf": 736,
    "parcel": "00000000000",
    "tax_id": "0000-00-00000",
    "lot_sf": 0,
    "lot_acres": 0.216,
    "lot_sf_survey": 9357,
    "coverage_pct": 37.6,
    "structure_sf_survey": 2824,
    "driveway_sf_survey": 1706,
    "zoning": "R4R (측량도 표기 - 시 확인 필요)",
    "survey": "L2-25T2-3R · J. Kerzie Hoyles LLC (253-371-6400) · 7/30/15 · City received 2016-03-02",
    "year_built": 2016,
    "existing_structure_sf": 2621,
    "gross_sf": 3411,
    "ground_floor_sf": 1160,
    "stories": 2,
    "beds": 4,
    "baths": "2 full + 1 half (MLS 2.5)",
    "foundation": "Concrete",
    "roof": "Gable / Composition Shingle",
    "exterior": "Wood Siding",
    "heating": "Heat pump + gas fireplace (1)",
    "water_heater": "Gas, 기존 위치 차고 내 (전환 시 이전 필요)",
    "utilities": "PSE 전기 / City of Tumwater 상·하수도",
    "hoa": "$900/yr (Chapparel Landing)",
    "mls": "NWMLS 2404943",
}

HOUSE = {
    "name": "3571 Cassie Dr SW - AFH 변환",
    "wall_height": ft(10, 5),
    "ext_wall_t": ft(0, 6),
    "int_wall_t": ft(0, 4),
    "slab_depth": 0.15,
    "footprint": (0.0, 0.0, ft(31, 4), ft(26, 10)),
}

# 벽: 중심선 + 두께
WALLS = [
    {"name": "W01 남측 외벽", "p1": (0.0, 0.0), "p2": (ft(31, 4), 0.0), "t": ft(0, 6), "exterior": True},
    {"name": "W02 북측 외벽", "p1": (0.0, ft(26, 10)), "p2": (ft(31, 4), ft(26, 10)), "t": ft(0, 6), "exterior": True},
    {"name": "W03 서측 외벽(기존주택 접합)", "p1": (0.0, 0.0), "p2": (0.0, ft(26, 10)), "t": ft(0, 6), "exterior": True},
    {"name": "W04 동측 외벽", "p1": (ft(31, 4), 0.0), "p2": (ft(31, 4), ft(26, 10)), "t": ft(0, 6), "exterior": True},
    # 남측 실 구획
    {"name": "W05 욕실/사무실", "p1": (ft(5, 0), 0.0), "p2": (ft(5, 0), ft(12, 10)), "t": ft(0, 4), "exterior": False},
    {"name": "W06 사무실/침실A", "p1": (ft(11, 4), 0.0), "p2": (ft(11, 4), ft(12, 10)), "t": ft(0, 4), "exterior": False},
    {"name": "W07 침실A 동측", "p1": (ft(21, 3), 0.0), "p2": (ft(21, 3), ft(12, 10)), "t": ft(0, 4), "exterior": False},
    {"name": "W08 남측블록/복도", "p1": (0.0, ft(12, 10)), "p2": (ft(31, 4), ft(12, 10)), "t": ft(0, 4), "exterior": False},
    # 북측 침실 구획
    {"name": "W09 복도/북측실", "p1": (0.0, ft(16, 4)), "p2": (ft(31, 4), ft(16, 4)), "t": ft(0, 4), "exterior": False},
    {"name": "W10 침실B/침실C", "p1": (ft(18, 0), ft(16, 4)), "p2": (ft(18, 0), ft(26, 10)), "t": ft(0, 4), "exterior": False},
    {"name": "W11 HVAC/침실B", "p1": (ft(4, 6), ft(16, 4)), "p2": (ft(4, 6), ft(20, 6)), "t": ft(0, 4), "exterior": False},
    {"name": "W12 HVAC 남측", "p1": (0.0, ft(20, 6)), "p2": (ft(4, 6), ft(20, 6)), "t": ft(0, 4), "exterior": False},
]

ROOMS = [
    {"name": "욕실", "rect": (ft(0, 3), ft(0, 3), ft(4, 9), ft(12, 7)), "kind": "bath"},
    {"name": "사무실/수납", "rect": (ft(5, 2), ft(0, 3), ft(11, 2), ft(12, 7)), "kind": "office"},
    {"name": "침실A", "rect": (ft(11, 6), ft(0, 3), ft(21, 1), ft(12, 7)), "kind": "bedroom"},
    {"name": "현관/창고", "rect": (ft(21, 5), ft(0, 3), ft(31, 1), ft(12, 7)), "kind": "storage"},
    {"name": "복도", "rect": (ft(0, 3), ft(13, 0), ft(31, 1), ft(16, 2)), "kind": "hall"},
    {"name": "HVAC", "rect": (ft(0, 3), ft(16, 6), ft(4, 4), ft(20, 4)), "kind": "mech"},
    {"name": "침실B", "rect": (ft(4, 8), ft(16, 6), ft(17, 10), ft(26, 7)), "kind": "bedroom"},
    {"name": "침실C", "rect": (ft(18, 2), ft(16, 6), ft(31, 1), ft(26, 7)), "kind": "bedroom"},
]

DOORS = [
    {"name": "D01 욕실", "wall": "W05 욕실/사무실", "offset": ft(9, 0), "w": ft(2, 8), "h": ft(6, 8)},
    {"name": "D02 사무실", "wall": "W06 사무실/침실A", "offset": ft(9, 0), "w": ft(2, 8), "h": ft(6, 8)},
    {"name": "D03 침실A", "wall": "W07 침실A 동측", "offset": ft(4, 0), "w": ft(3, 0), "h": ft(6, 8)},
    {"name": "D04 침실B", "wall": "W09 복도/북측실", "offset": ft(10, 0), "w": ft(3, 0), "h": ft(6, 8)},
    {"name": "D05 침실C", "wall": "W09 복도/북측실", "offset": ft(24, 0), "w": ft(3, 0), "h": ft(6, 8)},
    {"name": "D06 기존주택 연결", "wall": "W03 서측 외벽(기존주택 접합)", "offset": ft(8, 0), "w": ft(3, 0), "h": ft(6, 8)},
]

WINDOWS = [
    {"name": "WD01 침실A 이그레스", "wall": "W01 남측 외벽", "offset": ft(16, 0), "w": ft(5, 0), "h": ft(4, 0), "sill": ft(3, 4)},
    {"name": "WD02 침실B 이그레스", "wall": "W04 동측 외벽", "offset": ft(8, 0), "w": ft(5, 0), "h": ft(4, 0), "sill": ft(3, 4)},
    {"name": "WD03 침실C 이그레스", "wall": "W02 북측 외벽", "offset": ft(24, 0), "w": ft(5, 0), "h": ft(4, 0), "sill": ft(3, 4)},
    {"name": "WD04 욕실 창", "wall": "W02 북측 외벽", "offset": ft(2, 0), "w": ft(2, 0), "h": ft(2, 0), "sill": ft(5, 0)},
]

# 배관/설비: A01.4 키노트 기준 (P01 급수, P02 배수, P03 냉매, P04 배기)
PIPES = [
    {"name": "P01 급수", "kind": "급수", "p1": (ft(2, 0), ft(2, 0), ft(8, 0)), "p2": (ft(28, 0), ft(2, 0), ft(8, 0)),
     "d_mm": 20, "ins_mm": 20, "slope_pct": 0.0},
    {"name": "P02 배수", "kind": "배수", "p1": (ft(3, 0), ft(1, 0), 0.3), "p2": (ft(3, 0), ft(12, 0), 0.3),
     "d_mm": 75, "ins_mm": 0, "slope_pct": 2.0},
    {"name": "P03 냉매(CU-1)", "kind": "냉매", "p1": (ft(29, 0), ft(0, 0), ft(8, 0)), "p2": (ft(26, 0), ft(18, 0), ft(9, 6)),
     "d_mm": 16, "ins_mm": 13, "slope_pct": 0.0},
    {"name": "P04 욕실 배기(EF-1)", "kind": "배기", "p1": (ft(2, 0), ft(6, 0), ft(9, 8)), "p2": (ft(2, 0), ft(3, 0), ft(9, 8)),
     "d_mm": 100, "ins_mm": 0, "slope_pct": 0.0},
]

PIPE_FIX = {}


def walls_by_name():
    return {w["name"]: w for w in WALLS}

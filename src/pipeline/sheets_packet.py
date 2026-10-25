"""
3571 Cassie - 허가 제출 패킷 시트 4장.

  G-03 부동산/건물 정보 (Zillow·공적 기록 기반)
  G-04 허가 신청 데이터 시트 (City of Tumwater 양식 항목)
  G-05 제출 체크리스트 (항목 → 시트 매핑)
  EN-03 WSEC 외피 성능 요약 (제출용 표)

모두 예비 문서이며, 서명·날인 전에는 제출본이 아니다.
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
from sheets_v2 import HOUSE, T, ftin, new_doc, rect_area, sheet_frame
from sheets_v2 import water_heater_note, wrap_notes
import design

FT = 0.3048
META = design.META
OUT = base.OUT


def note(msp, lines, x=0.8, y=12.8, step=0.42, h=0.15):
    yy = y
    for line in lines:
        T(msp, line, x, yy, h, "NOTE")
        yy -= step
    return yy


def table(msp, rows, x=0.8, y=12.8, cols=None, step=0.4, h=0.14):
    cols = cols or [0.0, 3.0, 6.2, 9.4]
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            T(msp, str(val), x + cols[c], y - r * step, h, "TITLE" if r == 0 else "TEXT")


def g03_property(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "G-03", "부동산·건물 정보 (public record)")
    rows = [
        ("항목", "값", "출처"),
        ("주소", META["project"] + ", " + META["city"], "카운티"),
        ("Parcel / Tax-ID", f"{META['parcel']} / {META['tax_id']}", "카운티 세무기록"),
        ("대지면적", f"{META['lot_sf']:,} SF ({META['lot_acres']} ac)", "카운티 기록"),
        (META.get("lot_second_label", "대지면적(측량)"), f"{META.get('lot_sf_survey', 0):,} SF", "측량도/카운티"),
        ("피복률", f"{META['coverage_pct']} %", META.get("coverage_source", "측량도")),
        ("Zoning", META["zoning"], META.get("zoning_source", "측량도")),
        ("준공연도", str(META["year_built"]), "카운티 기록"),
        ("연면적", f"{META['existing_structure_sf']:,} living / {META['gross_sf']:,} gross", "카운티 기록"),
        ("1층 면적", f"{META['ground_floor_sf']:,} SF", "카운티 기록"),
        ("침실/욕실", f"{META['beds']} bd / {META['baths']}", "카운티 기록"),
        ("기초", META["foundation"], "카운티 기록"),
        ("지붕/외벽", f"{META['roof']} / {META['exterior']}", "카운티 기록"),
        ("난방", META["heating"], "카운티 기록"),
        ("온수기", META["water_heater"], "MLS"),
        ("주차/차고", META.get("parking", "Attached built-in, 790 SF (전환 대상)"), "Zillow + 카운티 assessor"),
        ("상하수도", META.get("utilities", "PSE 전기 / City of Tumwater 상·하수도"), "카운티 assessor"),
        ("HOA", META.get("hoa", "$900/yr (Chapparel Landing)"), "MLS/Zillow"),
        ("과세가/연세액", f"${META.get('assessed_value', 0):,} / ${META.get('annual_tax', 0):,}", "카운티 세무기록"),
        ("측량도", META.get("survey", "L2-25T2-3R (2015, J.K. Hoyles)"), META.get("survey_source", "측량도/카운티")),
    ]
    table(msp, rows, x=0.8, y=12.9, cols=[0.0, 5.4, 12.4], step=0.38, h=0.14)
    note(msp, META.get("g03_notes") or [
        "주의: Zillow/MLS 값은 참고용이며, 허가 신청에는 카운티 assessor 기록과 실측이 우선합니다.",
        "기존 온수기가 가스식이고 차고 내부에 설치되어 있어, 차고를 거주공간으로 전환할 경우",
        "이전 설치 또는 연소공기·격리 조치가 필요합니다 (IRC M1307 / G2408 검토).",
    ], y=4.6, step=0.5)
    doc.saveas(path); return path


def g04_application(path):
    doc = new_doc(); msp = doc.modelspace()
    _jur = META.get("jurisdiction", "City of Tumwater")
    sheet_frame(msp, "G-04", f"허가 신청 데이터 - {_jur}")
    fields = [
        ("Permit type", "Residential Alteration / Change of Use (AFH)"),
        ("Project address", f"{META['project']}, {META['city']}"),
        ("Legal", META.get("legal", "SEC 28 T18 R2W NE SE & SE SE PLAT CHAPPAREL LANDING DIV 2 LT 7 DOC 4490930")),
        ("Parcel / Tax-ID", f"{META['parcel']} / {META['tax_id']}"),
        ("Zoning", META["zoning"]),
        ("Lot / coverage", f"{META['lot_sf']:,} SF · {META['coverage_pct']}% ({META.get('coverage_basis', '측량')})"),
        ("Existing ground floor", f"{META['ground_floor_sf']:,} SF of {META['existing_structure_sf']:,} SF living"),
        ("Scope", META["scope"]),
        ("Existing use", META.get("existing_use", "3-car garage (non-habitable)")),
        ("Proposed use", META.get("proposed_use") or
         f"AFH 거주공간 - 침실 {base.bed_count()} + 통합욕실 {sum(1 for r in design.ROOMS if r.get('kind') == 'bath')}"),
        ("Area changed", META.get("area_changed")
         or f"{META['existing_garage_sf']} SF (garage) → {META['internal_sf']} SF (habitable)"),
        ("Construction value", "$ (건축주 기재)"),
        ("Applicant / Owner", "(성명·연락처 기재)"),
        ("Contractor", "(LIC# 기재)"),
        ("Owner-builder", "본인 소유·직접 시공 (WA RCW 18.27.090 면제)"),
        ("Project no.", META["project_no"]),
        ("Code year", "2021 IRC + WA amendments, 2021 WSEC"),
    ]
    fields = fields + [tuple(r) for r in (META.get("g04_extra") or [])]  # 범위 각주 행 (META-driven)
    foots = [str(s) for s in (META.get("g04_footnote") or [])]
    # 각주를 넣을 때는 표 행 간격을 줄여 프레임 안에 함께 넣는다
    step = min(0.72, (12.9 - 5.2) / max(1, len(fields))) if foots else 0.72
    y = 12.9
    for label, value in fields:
        T(msp, label, 0.8, y, 0.15, "TITLE")
        T(msp, value, 5.0, y, 0.15, "TEXT")
        msp.add_line((0.8, y - 0.12), (19.6, y - 0.12), dxfattribs={"layer": "DIM"})
        y -= step
    if foots:
        fy = 4.4
        for s in foots:
            T(msp, s, 0.8, fy, 0.15, "NOTE")
            fy -= 0.42
        T(msp, "서명: 건축주 ______________________   날짜 __________", 0.8, 2.7, 0.18, "TEXT")
        T(msp, "(이 시트는 신청 양식 항목을 정리한 것으로, 시 공식 양식 제출이 별도로 필요합니다.)",
          0.8, 2.1, 0.14, "NOTE")
    else:
        T(msp, "서명: 건축주 ______________________   날짜 __________", 0.8, 1.9, 0.18, "TEXT")
        T(msp, "(이 시트는 신청 양식 항목을 정리한 것으로, 시 공식 양식 제출이 별도로 필요합니다.)",
          0.8, 1.3, 0.14, "NOTE")
    doc.saveas(path); return path


def g05_checklist(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "G-05", "제출 체크리스트")
    rows = [
        ("항목", "본 세트 위치", "상태"),
        ("허가 신청서", "G-04 + 시 공식 양식", "작성 필요"),
        ("대지/주차 계획", "C-01", "포함(개념)"),
        ("기존/제안 평면", "A-01, A-02, A-05", "포함"),
        ("면적 산출", "A-12", "포함"),
        ("입면/단면", "A-04, A-13, A-14", "개념 수준"),
        ("구조 계획", "S-01, S-02, S-03" + (", S-04" if META.get("carport_enclosure") else ""),
         "EOR 검토 필요"),
        *([("주택 재구성 계획", "A-19", "개념 · 실측 필요")] if META.get("carport_enclosure") else []),
        ("기계/전기/배관", "M-01~03, E-01~03, P-02~04", "설계자 확정 필요"),
        ("소방(연기/CO)", "LS-01", "포함"),
        ("이그레스", "LS-02", "포함"),
        ("에너지(WSEC)", "EN-01, EN-02, EN-03", "분석가 검토 필요"),
        ("문/창 일람표", "A-09, A-10", "포함"),
        ("자재 목록", "자재목록.csv", "예비"),
        ("AFH 라이선스 서류", "(DSHS 별도)", "별도 제출"),
        ("Owner-builder 선언서", "G-04 + 시 양식", "첨부"),
    ]
    table(msp, rows, x=0.8, y=12.9, cols=[0.0, 7.6, 12.8], step=0.46, h=0.15)
    note(msp, [
        "1. 상태가 '필요'인 항목은 면허 보유자 또는 시 공식 양식으로 보완해야 합니다.",
        "2. 본 세트는 예비 도면이며, 날인 없는 제출은 반려됩니다.",
    ], y=5.6, step=0.5)
    doc.saveas(path); return path


def en03_wsec(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "EN-03", "WSEC 외피 성능 요약 (제출용 표)")
    x1, y1, x2, y2 = HOUSE["footprint"]
    h = HOUSE["wall_height"]
    perim = 2 * ((x2 - x1) + (y2 - y1))
    win = sum(w["w"] * w["h"] for w in design.WINDOWS)
    door = sum(d["w"] * d["h"] for d in design.DOORS)
    wall_net = max(0.0, perim * h - win - door)
    ceil = (x2 - x1) * (y2 - y1)
    rows = [
        ("구성", "면적(SF)", "목표 R/U", "비고"),
        ("외벽 (순)", f"{wall_net/(FT*FT):.0f}", "R-21 + ci", "2x6 + 외장단열"),
        ("천장", f"{ceil/(FT*FT):.0f}", "R-49", "기존 지붕 장선"),
        ("바닥(슬래브)", f"{ceil/(FT*FT):.0f}", "R-10 주변", "기존 슬래브"),
        ("창호", f"{win/(FT*FT):.0f}", "U-0.30", "IG/Argon"),
        ("문", f"{door/(FT*FT):.0f}", "U-0.20", "내부문 위주"),
    ]
    table(msp, rows, x=0.8, y=12.6, cols=[0.0, 4.0, 7.4, 10.6], step=0.46, h=0.15)
    note(msp, [
        "1. WSEC 2021 주거용: 위 조합은 프리스크립티브 경로의 '목표' 값입니다.",
        "2. 정식 컴플라이언스는 WSEC 컴플라이언스 툴 또는 에너지 분석가 계산서로 제출해야 합니다.",
        "3. 기밀: 블로우도어 테스트 결과(ACH50)를 시트에 기재해야 합니다.",
        "4. 환기(VIAQ): 욕실 80 CFM / 전체 환기 1대 — M-02, M-03 참조.",
        "5. 이 표는 계산서가 아닌 요약이며, 수치 확정은 분석가 업무입니다.",
    ], y=9.4, step=0.5)
    doc.saveas(path); return path


def g06_coordination(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "G-06", "조정(Discrepancy) 로그")
    disc = META.get("discrepancies") or [
        ("Lot 번호", "카운티 LT 7 / 측량표지 LOT 1", "카운티·시 확인"),
        ("대지면적", "카운티 9,411 / 측량 9,357", "피복률은 측량 기준"),
        ("Zoning", "측량표기 R4R (현행 조례 확인)", "시 조닝 확인"),
        ("기초", "MLS Block / 카운티 Concrete", "현장 확인"),
        ("1층 면적", "카운티 1,160 / A01.4 736 SF", "A01.4 기준 설계"),
        ("가스 온수기", "차고 내부 설치 (MLS)", "이전/격리 계획"),
        ("AFH 라이선스", "건축 허가와 별개 (DSHS)", "별도 진행"),
        ("차고도어", "유지 + 내부 스킨월 (A01.4)", "구조 영향 없음"),
    ]
    rows = [("#", "항목", "출처 간 차이", "처리")] + \
        [(str(i), a, b, c) for i, (a, b, c) in enumerate(disc, start=1)]
    _step = min(0.5, (12.9 - 9.6) / max(1, len(rows)))  # 주기 블록(y=7.6)과 겹치지 않게
    table(msp, rows, x=0.8, y=12.9, cols=[0.0, 0.7, 2.6, 7.6], step=_step, h=0.12)
    notes = [
        "이 표는 제출 전 해소해야 할 상충 항목 기록입니다.",
        "확인 전까지 도면의 legal/zoning 표기는 카운티 기록을 따릅니다.",
    ]
    # META['water_heater'] 가 차고 내 설치를 말할 때만 로그에 한 줄 추가 (META-driven)
    _wh = water_heater_note()
    if _wh:
        notes.insert(1, _wh)
    note(msp, wrap_notes(notes, 80, "   "), y=7.6, step=0.45)
    doc.saveas(path); return path


def main():
    for p in [
        g03_property(os.path.join(OUT, "G-03_부동산정보.dxf")),
        g04_application(os.path.join(OUT, "G-04_신청데이터.dxf")),
        g05_checklist(os.path.join(OUT, "G-05_제출체크리스트.dxf")),
        g06_coordination(os.path.join(OUT, "G-06_조정로그.dxf")),
        en03_wsec(os.path.join(OUT, "EN-03_WSEC요약.dxf")),
    ]:
        print("saved", os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())

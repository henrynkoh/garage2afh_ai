"""
3571 Cassie - 전체 도면 세트(32장) 중 추가 20장 생성기.

기존 12장: S-01표지(표지), A-01..A-04, S-01구조, M-01, M-02, E-01, P-02, LS-01, EN-01
추가 20장:
  G-01 일반주기/코드요약   G-02 범례/시트목록
  S-02 기초·슬래브         S-03 지붕·천장장선
  A-05 치수평면            A-06 마감평면        A-07 반사천장(RCP)
  A-08 가구배치            A-09 문일람표        A-10 창일람표
  A-11 마감일람표          A-12 면적산출        A-13 단면 A-A
  A-14 단면 B-B            A-15 외벽상세        A-16 욕실상세
  A-17 지붕·처마상세       A-18 차고도어 스킨월상세
  E-02 조명평면            E-03 동력·장비결선
  P-03 급수계통도          P-04 배수·통기계통도
  M-03 덕트·환기계통도      LS-02 이그레스·피난경로
  EN-02 창호 성능표
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

import sheets_v2 as base
from sheets_v2 import HOUSE, T, ftin, new_doc, outline, p_on_wall, rect_area, sheet_frame
from sheets_v2 import water_heater_note, wrap_notes
import design

FT = 0.3048
OUT = base.OUT
W = design.walls_by_name()
META = design.META


def pt(fx, fy):
    return (fx * FT, fy * FT)


def plan(msp, labels=True):
    base.draw_plan_body(msp, existing=False, labels=labels)


def note(msp, lines, x=10.8, y=12.6, step=0.4, h=0.14, layer="NOTE"):
    for line in lines:
        T(msp, line, x, y, h, layer)
        y -= step
    return y


def table(msp, rows, x=10.8, y=12.6, cols=None, step=0.4, h=0.14):
    cols = cols or [0.0, 2.0, 4.6, 7.0]
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            T(msp, str(val), x + cols[c], y - r * step, h, "TITLE" if r == 0 else "TEXT")


def dimstring(msp, x1, y1, x2, y2, label, h=0.12):
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "DIM"})
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    T(msp, label, mx, my + 0.06, h, "DIM")


def detail_layers(msp, x0, y0, layers, width_label="LAYERS"):
    """수직 단면 레이어 다이어그램: layers = [(이름, 두께mm), ...]"""
    T(msp, width_label, x0, y0 + 0.55, 0.18, "TITLE")
    x = x0
    total = sum(t for _n, t in layers)
    for name, t in layers:
        w = 2.4 * t / max(total, 1)
        msp.add_lwpolyline([(x, y0), (x + w, y0), (x + w, y0 + 1.6), (x, y0 + 1.6)],
                           close=True, dxfattribs={"layer": "WALL-INT"})
        T(msp, name, x + 0.02, y0 - 0.22, 0.11, "TEXT")
        T(msp, f"{t}mm", x + 0.02, y0 - 0.38, 0.1, "DIM")
        x += w


# --------------------------------------------------------------- G-01 / G-02
def g01_general_notes(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "G-01", "일반주기 및 코드 요약")
    lines = [
        f"1. 적용 코드: 2021 IRC (WA 개정), 2021 WSEC, {design.META.get('jurisdiction', 'Tumwater')} 시 조례, WAC 388-76(AFH)",
        f"2. 이 세트는 {design.META.get('source_drawings', 'Canarch Designs A01.3/A01.4')} 기반 스키매틱이며 시공용이 아님",
        "3. 모든 치수는 공적기록과 현장 실측으로 확인 후 사용",
        "4. 구조: " + META.get("structure_note", "기존 외벽 유지, 신규 파티션 비내력. 헤더·개구부는 구조기술사 확인"),
        "5. 소방: 연기/CO 상호연동 + 배터리 백업 (WAC R314.4, IRC R314.3/R315.5)",
        "6. 이그레스: 침실 3개소 이그레스 창 확보 (IRC R310, 순개구부 5.7 sqft)",
        "7. 에너지: WSEC 2021 외피 성능(EN-01 참조), 기밀 테스트 별도",
        "8. 설비: M/E/P 는 예비안. 최종 관경·용량은 해당 설계자 확정",
        "9. AFH: 침실 면적·문폭·화장실 접근성은 DSHS 라이선스 기준 별도 검토",
        "10. Own-builder 제출 (시 담당자 확인: 건축사·구조기술사 서명 불요)",
    ]
    # META['water_heater'] 가 차고 내 설치를 말할 때만 주기를 추가한다 (META-driven)
    _wh = water_heater_note()
    if _wh:
        lines.append(f"11. {_wh}")
    note(msp, wrap_notes(lines, 74, "    "), x=0.8, y=12.8, step=0.62, h=0.19)
    T(msp, "이 도면 세트는 예비 검토용입니다.", 0.8, 5.4, 0.22, "TITLE")
    doc.saveas(path); return path


def g02_legend(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "G-02", "범례 및 시트 목록")
    rows = [
        ("SHEET", "제목"),
        ("G-00", "표지"), ("G-01", "일반주기"), ("G-02", "범례/목록"),
        ("A-01", "기존 평면"), ("A-02", "제안 평면"), ("A-05", "치수 평면"),
        ("A-06", "마감 평면"), ("A-07", "반사천장"), ("A-08", "가구 배치"),
        ("A-13", "단면 A-A"), ("A-14", "단면 B-B"), ("A-15..18", META.get("a18_title_kr", "상세 4종")),
        ("S-01", "구조 계획"), ("S-02", "기초/슬래브"), ("S-03", "지붕/장선"),
        ("M-01", "설비 개념"), ("M-02", "기계 평면"), ("M-03", "덕트 계통"),
        ("E-01", "전기 평면"), ("E-02", "조명 평면"), ("E-03", "동력 결선"),
        ("P-02", "급배수 평면"), ("P-03", "급수 계통"), ("P-04", "배수/통기"),
        ("LS-01", "연기/CO"), ("LS-02", "이그레스"),
        ("EN-01", "외피 요약"), ("EN-02", "창호 성능"),
    ]
    if META.get("carport_enclosure"):
        rows += [("S-04", "카포트 외벽화 구조"), ("A-19", "기존 1층 재구성")]
    table(msp, rows, x=0.8, y=13.4, cols=[0, 2.2], step=0.36, h=0.15)
    T(msp, "범례", 10.8, 13.4, 0.22, "TITLE")
    legend = [
        ("실선 = 신규 벽", "DOOR"),
        ("파선 = 기존 벽", "WALL-EXIST"),
        ("○ = 콘센트", "NOTE"),
        ("✕ = 조명", "DOOR"),
        ("SD/CO = 감지기", "NOTE"),
        ("P1..P4 = 관로", "PIPE-W"),
    ]
    y = 12.8
    for text, layer in legend:
        msp.add_line((10.8, y + 0.06), (11.6, y + 0.06), dxfattribs={"layer": layer})
        T(msp, text, 11.8, y, 0.14, "TEXT")
        y -= 0.44
    doc.saveas(path); return path


# --------------------------------------------------------------- S-02 / S-03
def s02_foundation(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "S-02", "기초·슬래브 계획 (예비)")
    plan(msp, labels=False)
    x1, y1, x2, y2 = HOUSE["footprint"]
    msp.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True,
                       dxfattribs={"layer": "DIM"})
    note(msp, design.META.get("s02_notes") or [
        "1. 기존 차고 슬래브 유지 (두께·철근 상태 현장 확인)",
        "2. 신규 파티션 하부: 1/2in 앵커 @48in, 슬래브 천공 후 에폭시 정착",
        "3. 바닥 마감: 기존 슬래브 위 방습·단열·마감층 (상세 A-15 참조)",
        "4. 배수 구배: 기존 바닥 레벨 확인 후 필요 시 자평 시멘트",
        "5. 기초 신설 없음(기존 건물 내부 개조)",
    ], x=10.8, y=12.6, step=0.5)
    doc.saveas(path); return path


def s03_roof(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "S-03", "지붕·천장장선 계획 (예비)")
    plan(msp, labels=False)
    for x in range(2, 31, 4):
        msp.add_line(pt(x, 0.5), pt(x, 26.3), dxfattribs={"layer": "WALL-INT"})
    note(msp, design.META.get("s03_notes") or [
        "1. 기존 지붕 구조 유지 (트러스/서까래 현장 확인)",
        "2. 천장 장선: 기존 구조에 매달기, 신규 하중 없음",
        "3. 신규 파티션 상부: 천장 장선 사이 블로킹",
        "4. 천장 단열 R-49 (EN-01), 관통부 기밀 테이프",
        "5. 지붕 하중 경로는 기존 외벽 유지 — EOR 확인",
    ], x=10.8, y=12.6, step=0.5)
    doc.saveas(path); return path


# --------------------------------------------------------------- A-05..A-08
def a05_dimension(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-05", "치수 평면도")
    plan(msp)
    for room in design.ROOMS:
        x1, y1, x2, y2 = room["rect"]
        T(msp, ftin(x2 - x1), (x1 + x2) / 2, y1 - 0.25, 0.13, "DIM")
        T(msp, ftin(y2 - y1), x1 - 0.35, (y1 + y2) / 2, 0.13, "DIM")
    x1, y1, x2, y2 = HOUSE["footprint"]
    dimstring(msp, x1, y1 - 0.9, x2, y1 - 0.9, ftin(x2 - x1), 0.16)
    dimstring(msp, x1 - 0.9, y1, x1 - 0.9, y2, ftin(y2 - y1), 0.16)
    doc.saveas(path); return path


def a06_finish(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-06", "마감 평면도")
    plan(msp)
    finish = {"bath": "CT", "bedroom": "CPT", "hall": "LVT", "office": "LVT",
              "living": "LVT", "kitchen": "CT", "dining": "LVT", "storage": "SEAL",
              "mech": "SEAL"}
    for room in design.ROOMS:
        x1, y1, x2, y2 = room["rect"]
        code = finish.get(room["kind"], "LVT")
        T(msp, code, (x1 + x2) / 2, (y1 + y2) / 2 - 0.45, 0.2, "TEXT")
    table(msp, [
        ("코드", "마감", "적용"),
        ("CPT", "카펫 타일", "침실"),
        ("LVT", "비닐 타일", "복도/사무실"),
        ("CT", "세라믹 타일", "욕실"),
        ("SEAL", "실링", "수납/기계"),
        ("PT", "페인트", "전체 벽/천장"),
    ], x=10.8, y=12.4, cols=[0, 1.4, 4.0], step=0.4)
    doc.saveas(path); return path


def a07_rcp(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-07", "반사천장 평면도 (RCP)")
    plan(msp, labels=False)
    for room in design.ROOMS:
        x1, y1, x2, y2 = room["rect"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        msp.add_lwpolyline([(cx - 0.3, cy), (cx + 0.3, cy)], dxfattribs={"layer": "DOOR"})
        msp.add_lwpolyline([(cx, cy - 0.3), (cx, cy + 0.3)], dxfattribs={"layer": "DOOR"})
        T(msp, "2x4 LED", cx + 0.35, cy - 0.05, 0.12, "TEXT")
    note(msp, [
        "1. 천장고: 10'-5\" (설계 기준), 마감 후 실내고 확인",
        "2. 신규 파티션은 천장까지 (방음·차음)",
        "3. LED 2x4 패널, 조광 가능, 난연 등급",
        "4. 욕실: 방습 천장재 + 배기팬(EF-1)",
    ], x=10.8, y=12.4, step=0.46)
    doc.saveas(path); return path


def a08_furniture(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-08", "가구·설비 배치도")
    plan(msp)
    beds = [("침실A", 3.0, 3.0), ("침실B", 2.0, 2.4), ("침실C", 2.6, 2.2)]
    for name, w_ft, h_ft in beds:
        room = next(r for r in design.ROOMS if r["name"] == name)
        x1, y1, x2, y2 = room["rect"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        w, h = w_ft * FT / 2, h_ft * FT / 2
        msp.add_lwpolyline([(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)],
                           close=True, dxfattribs={"layer": "WINDOW"})
        T(msp, "Twin bed", cx - 0.3, cy, 0.11, "TEXT")
    note(msp, [
        "AFH 가구 기준: 침실당 침대 1 + 옷장 1 (DSHS WAC 388-76 검토)",
        "욕실: 접근 가능한 샤워(의자·잡이) 확보 권장",
        "복도 유효폭 36in 이상 유지 (가구 배치 후 확인)",
    ], x=10.8, y=12.4, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- A-09..A-12
def a09_doors(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-09", "문 일람표")
    rows = [("MARK", "위치", "폭x높이", "타입")]
    for d in design.DOORS:
        rows.append((d["name"].split()[0], d["wall"].split()[0], f"{ftin(d['w'])}x{ftin(d['h'])}", "HM/단열"))
    table(msp, rows, x=0.8, y=13.0, cols=[0, 1.6, 4.4, 7.6], step=0.42, h=0.15)
    note(msp, ["내부문: 2'-8\" / 3'-0\" (AFH 통과폭 WAC 388-76-10715 검토)",
               "이그레스 문: 3'-0\" x 6'-8\", 32in 순폭 확인"], x=0.8, y=8.0, step=0.45)
    doc.saveas(path); return path


def a10_windows(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-10", "창 일람표")
    rows = [("MARK", "위치", "크기", "창턱", "유리")]
    for w in design.WINDOWS:
        rows.append((w["name"].split()[0], w["wall"].split()[0],
                     f"{ftin(w['w'])}x{ftin(w['h'])}", ftin(w["sill"]), "Insul. IG"))
    table(msp, rows, x=0.8, y=13.0, cols=[0, 1.5, 4.0, 7.0, 9.2], step=0.42, h=0.15)
    note(msp, ["이그레스 창: 순개구부 5.7 sqft, 최소 20in x 24in, 바닥 44in 이하 (IRC R310)",
               "창호 성능은 EN-02 참조 (U-0.30 이하)"], x=0.8, y=8.4, step=0.45)
    doc.saveas(path); return path


def a11_finish_schedule(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-11", "마감 일람표")
    rows = [
        ("실", "바닥", "벽", "천장"),
        ("침실 A/B/C", "CPT", "PT + GWB", "PT + GWB"),
        ("욕실", "CT", "CT + 방수", "방습 PT"),
        ("복도", "LVT", "PT + GWB", "PT + GWB"),
        ("사무실/수납", "LVT", "PT + GWB", "PT + GWB"),
        ("HVAC", "SEAL", "GWB", "GWB"),
    ]
    table(msp, rows, x=0.8, y=13.0, cols=[0, 3.0, 6.0, 9.4], step=0.44, h=0.15)
    note(msp, ["욕실 방수: 바닥 전체 + 벽 1.2m 이상, 샤워부 1.8m",
               "모든 GWB 이음부 테이프·퍼티, 나사 피치 12in"], x=0.8, y=8.6, step=0.45)
    doc.saveas(path); return path


def a12_area_summary(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-12", "면적 산출 (Net/Gross)")
    total = sum(rect_area(r["rect"]) for r in design.ROOMS)
    x1, y1, x2, y2 = HOUSE["footprint"]
    gross = (x2 - x1) * (y2 - y1)
    rows = [("항목", "m2", "SF")]
    rows.append(("Gross (외곽)", f"{gross:.1f}", f"{gross/(FT*FT):.0f}"))
    rows.append(("Net (실 합계)", f"{total:.1f}", f"{total/(FT*FT):.0f}"))
    rows.append(("차이(벽체 등)", f"{gross-total:.1f}", f"{(gross-total)/(FT*FT):.0f}"))
    for room in design.ROOMS:
        a = rect_area(room["rect"])
        rows.append((room["name"], f"{a:.2f}", f"{a/(FT*FT):.0f}"))
    table(msp, rows, x=0.8, y=13.2, cols=[0, 4.0, 6.6], step=0.36, h=0.14)
    note(msp, [f"설계 기준 내부면적 {design.META.get('internal_sf', 736)} SF 와 대조 필요",
               "AFH 침실 최소 면적 기준은 DSHS 규정 확인"], x=10.8, y=12.6, step=0.5)
    doc.saveas(path); return path


# --------------------------------------------------------------- A-13..A-14
def section_sheet(path, code, title, cut_y_ft):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, code, title)
    x1, y1, x2, y2 = HOUSE["footprint"]
    h = HOUSE["wall_height"]
    base_y = 2.2
    msp.add_line((0.8, base_y), (0.8 + (x2 - x1), base_y), dxfattribs={"layer": "WALL-EXT"})
    msp.add_lwpolyline([(0.8, base_y), (0.8, base_y + h), (0.8 + (x2 - x1), base_y + h),
                        (0.8 + (x2 - x1), base_y)], dxfattribs={"layer": "WALL-EXT"})
    msp.add_line((0.8, base_y + h), (0.8 + (x2 - x1) / 2, base_y + h + 0.85),
                 dxfattribs={"layer": "WALL-EXT"})
    msp.add_line((0.8 + (x2 - x1) / 2, base_y + h + 0.85), (0.8 + (x2 - x1), base_y + h),
                 dxfattribs={"layer": "WALL-EXT"})
    for w in design.WALLS:
        if abs(w["p1"][1] - cut_y_ft * FT) < 0.35 or abs(w["p2"][1] - cut_y_ft * FT) < 0.35:
            xpos = 0.8 + w["p1"][0] * FT
            msp.add_line((xpos, base_y), (xpos, base_y + h), dxfattribs={"layer": "WALL-INT"})
    T(msp, f"CEILING {ftin(h)}", 0.8, base_y + h + 1.05, 0.18, "DIM")
    T(msp, f"단면 위치: y = {cut_y_ft:.1f} ft", 0.8, base_y - 0.6, 0.18, "NOTE")
    note(msp, ["1. 천장고 10'-5\" (설계 기준)", "2. 지붕 구조는 기존 유지",
               "3. 천장 단열 R-49 (EN-01)", "4. 벽체 구성은 A-15 상세 참조"],
         x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- A-15..A-18
def a15_wall_detail(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-15", "외벽·바닥 상세 (전형)")
    detail_layers(msp, 0.8, 8.0, [("EXT", 25), ("WRB", 5), ("OSB", 12), ("STUD+R21", 140), ("GWB", 16)],
                  "외벽 (수직 단면)")
    detail_layers(msp, 0.8, 3.0, [("SLAB", 100), ("VAPOR", 1), ("RIGID R-10", 50), ("FINISH", 20)],
                  "바닥 (기존 슬래브 위)")
    note(msp, ["1. 외벽 R-21 이상 (WSEC), 외장 단열 검토", "2. 기밀: 모든 관통부 실란트",
               "3. 방수: 욕실 바닥·벽체 방수층 상향 1.2m", "4. 슬래브 단열로 바닥 냉기 차단"],
         x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


def a16_bath_detail(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-16", "욕실 상세 (방수·기구)")
    x0, y0 = 0.8, 3.2
    msp.add_lwpolyline([(x0, y0), (x0 + 3.2, y0), (x0 + 3.2, y0 + 2.4), (x0, y0 + 2.4)],
                       close=True, dxfattribs={"layer": "WALL-EXT"})
    msp.add_lwpolyline([(x0 + 0.1, y0 + 0.1), (x0 + 3.1, y0 + 0.1), (x0 + 3.1, y0 + 2.3),
                        (x0 + 0.1, y0 + 2.3)], close=True, dxfattribs={"layer": "DOOR"})
    T(msp, "방수층 (바닥+벽 1.2m, 샤워 1.8m)", x0, y0 - 0.45, 0.13, "NOTE")
    T(msp, "SH", x0 + 0.8, y0 + 1.7, 0.16, "TEXT")
    T(msp, "WC", x0 + 0.8, y0 + 0.7, 0.16, "TEXT")
    T(msp, "WHB", x0 + 2.3, y0 + 0.7, 0.16, "TEXT")
    note(msp, ["1. 접이식 샤워 의자·잡이 설치 권장 (AFH 접근성)",
               "2. 배수 2in, 구배 1/4in/ft", "3. 환기 EF-1 80 CFM (M-02)",
               "4. 미끄럼 방지 타일 (COF 0.6 이상)"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


def a17_roof_detail(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-17", "지붕·처마 상세 (전형)")
    detail_layers(msp, 0.8, 7.4, [("SHINGLE", 10), ("UNDERLAY", 2), ("SHEATH", 15),
                                  ("RAFTER+R49", 300), ("GWB", 16)], "지붕 (수직 단면)")
    msp.add_line((0.8, 4.2), (6.0, 5.0), dxfattribs={"layer": "WALL-EXT"})
    T(msp, "처마: 통기·드립에지·빗물받이", 0.8, 3.6, 0.14, "NOTE")
    note(msp, ["1. 기존 지붕 구조 유지, 신규 관통부 플래싱", "2. 천장 단열 R-49 + 방습",
               "3. 처마 통기 확보 (막힘 없도록)", "4. 지붕 관통 배기 후드 역류방지"],
         x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


def a18_carport_opening(path):
    """카포트 개구부 폐쇄 상세 (carport opening closure) - 외벽화 프로젝트 전용."""
    doc = new_doc(); msp = doc.modelspace()
    CP = getattr(design, "CARPORT", {})
    w = CP.get("width_ft", 20.0) * FT
    H = CP.get("wall_h_ft", 8.0) * FT

    sheet_frame(msp, "A-18", META.get("a18_title_kr", "카포트 개구부 폐쇄 상세") + " (opening closure)")

    # ---------------- 입면 1:50 (좌상)
    ex, ey = 0.9, 9.5
    T(msp, "입면 1:50 · 폐쇄되는 기존 오픈 페이스 (정면)", ex, ey + H + 0.78, 0.18, "TITLE")
    msp.add_lwpolyline([(ex, ey), (ex + w, ey), (ex + w, ey + H), (ex, ey + H)],
                       close=True, dxfattribs={"layer": "WALL-EXT"})
    for px, nm in ((ex, "P-1"), (ex + w - 0.2, "P-2")):
        msp.add_lwpolyline([(px, ey), (px + 0.2, ey), (px + 0.2, ey + H), (px, ey + H)],
                           close=True, dxfattribs={"layer": "WALL-EXIST"})
        T(msp, nm, px + 0.03, ey - 0.24, 0.11, "WALL-EXIST")
    msp.add_line((ex + 0.2, ey + H - 0.3), (ex + w - 0.2, ey + H - 0.3), dxfattribs={"layer": "DOOR"})
    T(msp, "H-1 기존 개구부 헤더 (EOR 확인)", ex + 0.55, ey + H - 0.52, 0.115, "DOOR")
    T(msp, "기존 fascia + head flashing", ex + 0.55, ey + H + 0.18, 0.115, "NOTE")

    msp.add_lwpolyline([(ex + 0.55, ey), (ex + 1.46, ey), (ex + 1.46, ey + 2.03),
                        (ex + 0.55, ey + 2.03)], close=True, dxfattribs={"layer": "DOOR"})
    T(msp, "D-1 3'-0\"x6'-8\"", ex + 0.5, ey - 0.5, 0.11, "DOOR")
    msp.add_lwpolyline([(ex + 2.5, ey + 0.95), (ex + 4.02, ey + 0.95), (ex + 4.02, ey + 2.17),
                        (ex + 2.5, ey + 2.17)], close=True, dxfattribs={"layer": "WINDOW"})
    T(msp, "WD-1 5'-0\"x4'-0\" (sill 3'-4\")", ex + 2.45, ey - 0.5, 0.11, "WINDOW")

    msp.add_line((ex, ey - 0.78), (ex + w, ey - 0.78), dxfattribs={"layer": "DIM"})
    T(msp, f"{CP.get('width_ft', 20.0):.0f}'-0\" (가정)", ex + w / 2 - 0.5, ey - 0.74, 0.11, "DIM")
    msp.add_line((ex + w + 0.42, ey), (ex + w + 0.42, ey + H), dxfattribs={"layer": "DIM"})
    T(msp, f"{CP.get('wall_h_ft', 8.0):.0f}'-0\"", ex + w + 0.5, ey + H / 2, 0.11, "DIM")

    # ---------------- 수직 단면 (좌하)
    sx, sy = 0.9, 3.4
    T(msp, "수직 단면 (벽체 · 슬래브 단부 · 신규 기초) 1:20 개념", sx, sy + 4.55, 0.17, "TITLE")
    msp.add_line((sx - 0.3, sy), (sx + 5.0, sy), dxfattribs={"layer": "WALL-EXT"})
    msp.add_lwpolyline([(sx - 0.3, sy), (sx + 2.0, sy), (sx + 2.0, sy + 0.45), (sx - 0.3, sy + 0.45)],
                       close=True, dxfattribs={"layer": "WALL-EXIST"})
    T(msp, "기존 카포트 슬래브 (비단열 · conditioned 기초 아님)", sx - 0.28, sy - 0.32, 0.105, "NOTE")
    msp.add_lwpolyline([(sx + 2.0, sy - 0.7), (sx + 2.7, sy - 0.7), (sx + 2.7, sy + 0.45),
                        (sx + 2.0, sy + 0.45)], close=True, dxfattribs={"layer": "WALL-INT"})
    T(msp, "F-1 신규 테두리 기초", sx + 0.85, sy - 0.92, 0.105, "WALL-INT")
    msp.add_lwpolyline([(sx + 2.0, sy + 0.45), (sx + 2.35, sy + 0.45), (sx + 2.35, sy + 3.0),
                        (sx + 2.0, sy + 3.0)], close=True, dxfattribs={"layer": "WALL-EXT"})
    T(msp, "신규 외벽: siding + WRB + OSB + 2x6 R-21 + GWB", sx + 2.55, sy + 1.72, 0.105, "TEXT")
    T(msp, "PL-1 상부 플레이트", sx + 2.55, sy + 3.18, 0.105, "DOOR")
    msp.add_lwpolyline([(sx + 2.0, sy + 3.05), (sx + 2.35, sy + 3.05), (sx + 2.35, sy + 3.35),
                        (sx + 2.0, sy + 3.35)], close=True, dxfattribs={"layer": "DOOR"})
    # 기존 지붕 / fascia
    msp.add_line((sx + 2.0, sy + 3.45), (sx - 0.3, sy + 3.85), dxfattribs={"layer": "WALL-EXIST"})
    msp.add_line((sx + 2.0, sy + 3.6), (sx - 0.3, sy + 4.0), dxfattribs={"layer": "WALL-EXIST"})
    T(msp, "기존 지붕 / fascia (유지)", sx - 0.28, sy + 4.02, 0.105, "WALL-EXIST")
    msp.add_lwpolyline([(sx + 1.95, sy + 3.47), (sx + 2.05, sy + 3.4), (sx + 2.35, sy + 3.44),
                        (sx + 2.35, sy + 3.35)], close=True, dxfattribs={"layer": "NOTE"})
    T(msp, "FL-1 head / tie-in 플래싱 + 역물매 차단", sx + 2.55, sy + 3.72, 0.105, "NOTE")
    # 내부 바닥 조립
    msp.add_lwpolyline([(sx - 0.3, sy + 0.45), (sx + 2.0, sy + 0.45), (sx + 2.0, sy + 0.62),
                        (sx - 0.3, sy + 0.62)], close=True, dxfattribs={"layer": "ROOM"})
    T(msp, "SL-1 단열 슬래브(상부 R-10) + 마감 / 올린 마루", sx - 0.28, sy + 1.05, 0.105, "TEXT")
    T(msp, "D-1 문턱: 외부 지표 +4in 이상 (또는 배수 턱)", sx - 0.28, sy + 1.42, 0.105, "NOTE")
    msp.add_line((sx + 2.75, sy + 0.25), (sx + 3.6, sy + 0.05), dxfattribs={"layer": "DIM"})
    T(msp, "슬래브 단부 배수 2% · 집수구 · 지표수 역류 차단", sx + 2.75, sy - 0.2, 0.1, "DIM")

    # ---------------- 주기 (우상)
    note(msp, [
        "1. 기존 오픈 페이스를 신규 외벽으로 폐쇄한다. 기존 지붕은 유지하고 개구부 상부 헤더 H-1 과",
        "   기둥 P-1/P-2 로 지지한다 (기존 부재 상태 확인 후 유지 또는 보강 - EOR 판단).",
        "2. " + CP.get("flashing", ""),
        "3. " + CP.get("drainage", ""),
        "4. " + CP.get("slab_note", ""),
        "5. 벽체: 2x6 R-21 + 외장 단열 검토(WSEC) · WRB 연속 · sill seal · 관통부 실란트.",
        "6. D-1 은 단열 외부문, WD-1 은 침실이 아니므로 이그레스 요건 비적용.",
    ], x=10.6, y=13.8, step=0.44, h=0.115)

    # ---------------- 조립 표 2종
    T(msp, "신규 외벽 조립 (외 → 내)", 10.6, 10.45, 0.16, "TITLE")
    table(msp, [("층", "재료", "비고"),
                ("1", "steel siding", "기존과 동일"),
                ("2", "WRB + 플래싱", "연속"),
                ("3", "7/16 OSB", "구조 패널"),
                ("4", "2x6 stud R-21", "@16 o.c."),
                ("5", "1/2 GWB", "-")],
          x=10.6, y=10.18, cols=[0.0, 1.2, 3.6], step=0.3, h=0.1)

    T(msp, "바닥 조립 (기존 슬래브 위)", 15.6, 10.45, 0.16, "TITLE")
    table(msp, [("층", "재료", "비고"),
                ("1", "기존 슬래브", "비단열"),
                ("2", "방습층", "-"),
                ("3", "R-10 rigid", "주변부"),
                ("4", "sleeper/마감", "또는 올린 마루")],
          x=15.6, y=10.18, cols=[0.0, 1.3, 3.4], step=0.3, h=0.1)

    T(msp, "시공 순서: ① 기초·피어 → ② 개구부 헤더/기둥 확인 → ③ 외벽 골조 → ④ 지붕·플래싱 → ⑤ 단열·기밀 → ⑥ 마감·창호",
      10.6, 8.1, 0.115, "NOTE")
    T(msp, "※ 예비 개념도이며 구조·에너지 적합성은 EOR/분석가 확인이 필요하다.", 10.6, 7.8, 0.11, "NOTE")
    doc.saveas(path); return path


def a18_garage_detail(path):
    # 카포트 외벽화 프로젝트는 개구부 폐쇄 상세로 대체된다 (META 플래그)
    if META.get("carport_enclosure"):
        return a18_carport_opening(path)
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "A-18", "차고도어 스킨월 상세")
    x0, y0 = 0.8, 4.0
    msp.add_lwpolyline([(x0, y0), (x0 + 0.6, y0), (x0 + 0.6, y0 + 7.0), (x0, y0 + 7.0)],
                       close=True, dxfattribs={"layer": "DOOR"})
    T(msp, "기존 차고도어 (유지)", x0 + 0.7, y0 + 4.6, 0.15, "TEXT")
    msp.add_lwpolyline([(x0 + 0.75, y0), (x0 + 0.95, y0), (x0 + 0.95, y0 + 7.0), (x0 + 0.75, y0 + 7.0)],
                       close=True, dxfattribs={"layer": "WALL-INT"})
    T(msp, "스킨월 2x4 + R-21 + GWB (내부)", x0 + 1.05, y0 + 3.4, 0.14, "TEXT")
    T(msp, "상부 헤더 H1 (S-01) 유지", x0 + 1.05, y0 + 5.2, 0.14, "NOTE")
    note(msp, ["1. 도어는 구조적으로 유지하되 내부에서 단열·마감",
               "2. 스킨월 하부 방수·기밀 (외부 습기 차단)",
               "3. 도어 트랙·스프링 상태 점검 (기존 부재)",
               "4. 필요 시 헤더 보강 — EOR 판단"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- E-02 / E-03
def e02_lighting(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "E-02", "전기 조명 평면")
    plan(msp)
    for room in design.ROOMS:
        x1, y1, x2, y2 = room["rect"]
        n = 2 if rect_area(room["rect"]) > 6 else 1
        for k in range(n):
            cx = x1 + (x2 - x1) * (k + 1) / (n + 1)
            cy = (y1 + y2) / 2
            msp.add_line((cx - 0.14, cy - 0.14), (cx + 0.14, cy + 0.14), dxfattribs={"layer": "DOOR"})
            msp.add_line((cx - 0.14, cy + 0.14), (cx + 0.14, cy - 0.14), dxfattribs={"layer": "DOOR"})
    table(msp, [("회로", "부하", "수량"), ("C1", "복도/거실 LED", "6"), ("C2", "침실 LED", "5"),
                ("C3", "욕실·방습", "2"), ("C4", "사무실", "2")],
          x=10.8, y=12.4, cols=[0, 1.4, 4.0], step=0.4)
    doc.saveas(path); return path


def e03_power(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "E-03", "전기 동력·장비 결선도")
    x0, y0 = 0.8, 9.0
    for i, label in enumerate(["LP 200A", "C5 AHU/CU-1", "C6 WH", "C7 경보"]):
        msp.add_lwpolyline([(x0, y0 - i * 1.6), (x0 + 2.6, y0 - i * 1.6),
                            (x0 + 2.6, y0 - i * 1.6 + 0.9), (x0, y0 - i * 1.6 + 0.9)],
                           close=True, dxfattribs={"layer": "DOOR"})
        T(msp, label, x0 + 0.12, y0 - i * 1.6 + 0.32, 0.15, "TEXT")
    for i in range(3):
        msp.add_line((x0 + 1.3, y0 - i * 1.6), (x0 + 1.3, y0 - (i + 1) * 1.6 + 0.9),
                     dxfattribs={"layer": "DOOR"})
    note(msp, ["1. 분전반 200A (기존 용량 확인)", "2. AHU/CU-1 30A 전용, 차단기·과전류 보호",
               "3. 온수기 30A 전용", "4. 경보 회로는 상호연동 + 배터리 백업",
               "5. 결선도는 예비안 — 전기설계자 확정"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- P-03 / P-04
def p03_supply_diagram(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "P-03", "급수 계통도 (개략)")
    x0, y0 = 1.0, 10.0
    nodes = [("METER", 0.0), ("WH", 3.2), ("BATH", 6.4), ("FIXTURES", 9.6)]
    for i, (name, dx) in enumerate(nodes):
        msp.add_lwpolyline([(x0 + dx, y0), (x0 + dx + 2.2, y0), (x0 + dx + 2.2, y0 + 1.4),
                            (x0 + dx, y0 + 1.4)], close=True, dxfattribs={"layer": "PIPE-W"})
        T(msp, name, x0 + dx + 0.15, y0 + 0.5, 0.15, "PIPE-W")
        if i < len(nodes) - 1:
            msp.add_line((x0 + dx + 2.2, y0 + 0.7), (x0 + dx + 3.2, y0 + 0.7),
                         dxfattribs={"layer": "PIPE-W"})
    note(msp, ["1. 계량기 → 온수기(50gal) → 욕실 → 기구", "2. 관경: 3/4in 주관, 1/2in 분기, 3/8in 세면기",
               "3. 온수 대기 배관 최소화 (에너지)", "4. 진공방지기·압력계 옥내 설치 검토"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


def p04_drain_diagram(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "P-04", "배수·통기 계통도 (개략)")
    x0, y0 = 1.0, 10.0
    for i, (name, dx) in enumerate([("WC 3in", 0.0), ("LAV 1.5in", 3.0), ("SH 2in", 6.0), ("MAIN 3in", 9.0)]):
        msp.add_lwpolyline([(x0 + dx, y0), (x0 + dx + 2.2, y0), (x0 + dx + 2.2, y0 + 1.2),
                            (x0 + dx, y0 + 1.2)], close=True, dxfattribs={"layer": "PIPE-D"})
        T(msp, name, x0 + dx + 0.1, y0 + 0.45, 0.14, "PIPE-D")
        if i < 3:
            msp.add_line((x0 + dx + 2.2, y0 + 0.6), (x0 + dx + 3.0, y0 + 0.6), dxfattribs={"layer": "PIPE-D"})
    msp.add_line((x0 + 10.0, y0 + 1.2), (x0 + 10.0, y0 + 3.2), dxfattribs={"layer": "PIPE-D"})
    T(msp, "VENT 2in", x0 + 10.2, y0 + 2.2, 0.13, "PIPE-D")
    note(msp, ["1. 구배 1/4in/ft (2%) 이상", "2. 통기 2in, 각 기구 트랩 통기",
               "3. 주관 3in, 건물 외부 연결부 확인", "4. 배관 관통부 방화·방수 실링"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- M-03
def m03_duct(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "M-03", "덕트·환기 계통도")
    plan(msp, labels=False)
    msp.add_line(pt(2.4, 6.0), pt(0.4, 6.0), dxfattribs={"layer": "PIPE-W"})
    msp.add_line(pt(2.3, 18.4), pt(2.3, 8.0), dxfattribs={"layer": "PIPE-W"})
    msp.add_line(pt(2.3, 8.0), pt(32.6, 8.0), dxfattribs={"layer": "PIPE-W"})
    for fx, fy in [(8.0, 6.0), (16.0, 6.0), (11.0, 21.0), (24.5, 21.0)]:
        x, y = pt(fx, fy)
        msp.add_lwpolyline([(x - 0.1, y - 0.06), (x + 0.1, y - 0.06),
                            (x + 0.1, y + 0.06), (x - 0.1, y + 0.06)],
                           close=True, dxfattribs={"layer": "WINDOW"})
    note(msp, ["1. EF-1: 욕실 80 CFM, 외벽 후드", "2. AHU → 공급 4개소 + 리턴 2개소",
               "3. 덕트 방청·보온, 소음 25 NR 이하 목표", "4. 드라이어(DH-1)는 별도 4in 덕트 (TBC)"],
         x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- LS-02
def ls02_egress(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "LS-02", "이그레스·피난 경로")
    plan(msp)
    for w in design.WINDOWS:
        if "이그레스" in w["name"]:
            wall = W[w["wall"]]
            x, y = p_on_wall(wall, w["offset"])
            msp.add_circle((x, y), 0.22, dxfattribs={"layer": "DOOR"})
            T(msp, "EGRESS", x - 0.3, y + 0.28, 0.13, "DOOR")
    msp.add_line(pt(2.0, 2.0), pt(2.0, 15.0), dxfattribs={"layer": "DIM"})
    msp.add_line(pt(2.0, 15.0), pt(28.0, 15.0), dxfattribs={"layer": "DIM"})
    T(msp, "피난 경로 (복도 → 외부)", pt(10.0, 15.6)[0], pt(10.0, 15.6)[1], 0.13, "DIM")
    note(msp, ["1. 침실 3개소 이그레스 창 (순개구부 5.7 sqft, IRC R310)",
               "2. 복도 유효폭 36in 이상 유지", "3. 문 개구부 32in 순폭 (R311.2)",
               "4. 경보는 LS-01 참조"], x=10.8, y=12.6, step=0.46)
    doc.saveas(path); return path


# --------------------------------------------------------------- EN-02
def en02_window_perf(path):
    doc = new_doc(); msp = doc.modelspace()
    sheet_frame(msp, "EN-02", "창호 에너지 성능표")
    rows = [("MARK", "크기", "U", "SHGC", "VT", "비고")]
    for w in design.WINDOWS:
        rows.append((w["name"].split()[0], f"{ftin(w['w'])}x{ftin(w['h'])}", "0.30", "0.25", "0.45", "IG/Argon"))
    table(msp, rows, x=0.8, y=13.0, cols=[0, 1.6, 4.6, 6.0, 7.4, 9.0], step=0.42, h=0.15)
    note(msp, ["1. WSEC 2021 주거 창호: U-0.30 이하, SHGC 상한 확인",
               "2. 이그레스 창은 개폐 가능 타입 (slider/casement)",
               "3. 창호 성능값은 제조사 인증서로 확인 필요",
               "4. 설치 상세: 플래싱·에어실링 — A-15 참조"], x=0.8, y=8.4, step=0.46)
    doc.saveas(path); return path


def main():
    made = [
        g01_general_notes(os.path.join(OUT, "G-01_일반주기.dxf")),
        g02_legend(os.path.join(OUT, "G-02_범례_목록.dxf")),
        s02_foundation(os.path.join(OUT, "S-02_기초슬래브.dxf")),
        s03_roof(os.path.join(OUT, "S-03_지붕장선.dxf")),
        a05_dimension(os.path.join(OUT, "A-05_치수평면.dxf")),
        a06_finish(os.path.join(OUT, "A-06_마감평면.dxf")),
        a07_rcp(os.path.join(OUT, "A-07_반사천장.dxf")),
        a08_furniture(os.path.join(OUT, "A-08_가구배치.dxf")),
        a09_doors(os.path.join(OUT, "A-09_문일람표.dxf")),
        a10_windows(os.path.join(OUT, "A-10_창일람표.dxf")),
        a11_finish_schedule(os.path.join(OUT, "A-11_마감일람표.dxf")),
        a12_area_summary(os.path.join(OUT, "A-12_면적산출.dxf")),
        section_sheet(os.path.join(OUT, "A-13_단면AA.dxf"), "A-13", "단면 A-A", 14.0),
        section_sheet(os.path.join(OUT, "A-14_단면BB.dxf"), "A-14", "단면 B-B", 21.0),
        a15_wall_detail(os.path.join(OUT, "A-15_외벽상세.dxf")),
        a16_bath_detail(os.path.join(OUT, "A-16_욕실상세.dxf")),
        a17_roof_detail(os.path.join(OUT, "A-17_지붕상세.dxf")),
        a18_garage_detail(os.path.join(OUT, "A-18_%s.dxf" % design.META.get("a18_slug", "차고도어상세"))),
        e02_lighting(os.path.join(OUT, "E-02_조명평면.dxf")),
        e03_power(os.path.join(OUT, "E-03_동력결선.dxf")),
        p03_supply_diagram(os.path.join(OUT, "P-03_급수계통도.dxf")),
        p04_drain_diagram(os.path.join(OUT, "P-04_배수통기.dxf")),
        m03_duct(os.path.join(OUT, "M-03_덕트계통.dxf")),
        ls02_egress(os.path.join(OUT, "LS-02_이그레스.dxf")),
        en02_window_perf(os.path.join(OUT, "EN-02_창호성능.dxf")),
    ]
    for p in made:
        print("saved", os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())

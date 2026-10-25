"""
카포트 외벽화 프로젝트 전용 시트 2장 (META['carport_enclosure'] 일 때만 생성).

  S-04  신규 외벽·지붕 구조 (카포트 외벽화)
        - 신규 테두리 스터드 벽, 상부 플레이트 ↔ 기존 fascia 결속
        - 외벽화 구역 위 신규 박공/lean-to 지붕 골조, tie-in 플래싱
        - 신규 지붕 하중이 기존 구조로 전달되지 않는다는 주기
  A-19  기존 주택 재구성 계획 (3 침실 + 욕실)
        - 기존 1층(1,877 SF) 실 용도 변경 개념도, 신규 욕실 위치, 복도 폭, 이그레스 창
        - 기존 vs 제안 실 용도 표

다른 프로젝트(3571 등)는 META 플래그가 없으므로 아무 시트도 만들지 않는다.
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

from sheets_v2 import T, new_doc, sheet_frame
import design

FT = 0.3048
OUT = os.environ.get("HOUSEBIM_OUT", os.path.join(DESIGN_DIR, "out"))
META = design.META
CARPORT = getattr(design, "CARPORT", {})
MAIN_FLOOR = getattr(design, "MAIN_FLOOR", {})


def main_floor_beds():
    """MAIN_FLOOR['rooms'] 의 kind=='bedroom' 실 목록 - A-19 문구가 프로그램을 따라가도록."""
    return [r for r in MAIN_FLOOR.get("rooms", []) if r[3] == "bedroom"]


def main_floor_bed_count():
    return len(main_floor_beds())


# ------------------------------------------------------------------ helpers
def line(msp, x1, y1, x2, y2, layer="WALL-EXT"):
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer})


def rect(msp, x, y, w, h, layer="WALL-EXT"):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                       close=True, dxfattribs={"layer": layer})


def box(msp, x, y, w, h):
    msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                       close=True, dxfattribs={"layer": "TITLE"})


def dashed(msp, x1, y1, x2, y2, layer="WALL-EXIST", n=14, duty=0.55):
    for i in range(n):
        t0 = i / n
        t1 = t0 + duty / n
        line(msp, x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
             x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1, layer)


def notes(msp, lines, x=0.9, y=12.6, step=0.42, h=0.15, layer="NOTE"):
    yy = y
    for s in lines:
        T(msp, s, x, yy, h, layer)
        yy -= step
    return yy


def table(msp, rows, x, y, cols, step=0.4, h=0.14):
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            T(msp, str(val), x + cols[c], y - r * step, h, "TITLE" if r == 0 else "TEXT")


# ------------------------------------------------------------------ S-04
def s04_enclosure_structure(path):
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "S-04", "신규 외벽·지붕 구조 (카포트 외벽화)")

    w = CARPORT.get("width_ft", 20.0) * FT
    d = CARPORT.get("depth_ft", 20.0) * FT

    # ---------------- 계획도 1:50 (좌상)
    x0, y0 = 0.9, 7.4
    T(msp, "계획도 (PLAN) 1:50 · 400 SF 가정 20'x20'", x0, y0 + d + 0.62, 0.19, "TITLE")
    T(msp, "실선 = 신규 / 파선 = 기존", x0, y0 + d + 0.40, 0.12, "NOTE")

    dashed(msp, x0, y0 + d, x0 + w, y0 + d, "WALL-EXIST", n=16)   # 기존 주택 외벽
    dashed(msp, x0, y0, x0 + w, y0, "WALL-EXIST", n=16)           # 기존 슬래브 단부
    # 신규 외벽 3면 (서/남/동) - 2선 표기
    for off in (0.0, 0.09):
        line(msp, x0 + off, y0 + off, x0 + off, y0 + d, "WALL-EXT")
        line(msp, x0 + w - off, y0 + off, x0 + w - off, y0 + d, "WALL-EXT")
    line(msp, x0, y0, x0 + w, y0, "WALL-EXT")
    line(msp, x0 + 0.09, y0 + 0.09, x0 + w - 0.09, y0 + 0.09, "WALL-EXT")

    # 개구부 기둥
    for cx in (x0, x0 + w - 0.26):
        rect(msp, cx, y0 - 0.02, 0.26, 0.26, "DOOR")
    # 신규 출입문 / 창 (남측 개구부 폐쇄면)
    rect(msp, x0 + 0.55, y0 - 0.02, 0.95, 0.2, "DOOR")
    rect(msp, x0 + 2.6, y0 - 0.02, 1.55, 0.2, "WINDOW")

    # 지시선 라벨 (도면 밖으로)
    T(msp, "W-2 카포트 개구부 폐쇄 외벽", x0 + w * 0.02, y0 + 0.30, 0.11, "TEXT")
    line(msp, x0 + w * 0.62, y0 + 0.52, x0 + w * 0.62, y0 + 0.14, "NOTE")
    T(msp, "H-1 헤더 (기존 개구부)", x0 + w * 0.55, y0 + 0.56, 0.11, "DOOR")
    line(msp, x0 + 3.0, y0 + 0.95, x0 + 3.37, y0 + 0.22, "WINDOW")
    T(msp, "WD-1 창", x0 + 3.05, y0 + 0.99, 0.11, "WINDOW")
    line(msp, x0 + 0.4, y0 - 0.55, x0 + 0.9, y0 - 0.08, "DOOR")
    T(msp, "D-1 문", x0 + 0.1, y0 - 0.68, 0.11, "DOOR")

    T(msp, "기존 카포트 슬래브 400 SF (유지 · 두께 UNKNOWN)", x0, y0 - 1.02, 0.12, "TEXT")
    T(msp, "P-1 / P-2 기존 기둥 (6x6 PT 신규 또는 보강)", x0, y0 - 1.30, 0.11, "DOOR")
    T(msp, "기존 주택 외벽 · fascia (하중 미전가)", x0 + 0.15, y0 + d - 0.32, 0.115, "NOTE")

    line(msp, x0, y0 + d + 0.20, x0 + w, y0 + d + 0.20, "DIM")
    T(msp, f"{CARPORT.get('width_ft', 20.0):.0f}'-0\" (가정)", x0 + w / 2 - 0.55, y0 + d + 0.25, 0.115, "DIM")
    line(msp, x0 - 0.42, y0, x0 - 0.42, y0 + d, "DIM")
    T(msp, f"{CARPORT.get('depth_ft', 20.0):.0f}'-0\"", x0 - 1.35, y0 + d / 2, 0.12, "DIM")

    # ---------------- 단면 A-A 1:50 (좌하)
    sy = 2.6
    sx = 1.45
    T(msp, "단면 A-A 1:50 · 신규 지붕 하중은 신규 기둥/벽 → 신규 기초로", sx, sy - 1.28, 0.17, "TITLE")
    line(msp, sx - 0.4, sy, sx + w + 0.9, sy, "WALL-EXT")            # 지면
    rect(msp, sx, sy, w, 0.18, "WALL-EXIST")                          # 기존 슬래브
    rect(msp, sx - 0.4, sy, 0.34, 2.55, "WALL-EXIST")                 # 기존 주택 외벽
    T(msp, "기존 주택", 0.15, sy + 2.62, 0.11, "NOTE")
    rect(msp, sx + w - 0.18, sy, 0.18, 2.3, "WALL-EXT")               # 신규 외벽
    rect(msp, sx + w - 0.18, sy - 0.6, 0.36, 0.6, "WALL-INT")         # 신규 테두리 기초
    # 신규 지붕 (기존 fascia -> 신규 벽 상부)
    line(msp, sx - 0.06, sy + 2.5, sx + w - 0.10, sy + 2.3, "WALL-EXT")
    line(msp, sx - 0.06, sy + 2.66, sx + w - 0.10, sy + 2.46, "WALL-EXT")
    T(msp, "신규 지붕 골조 (lean-to / 박공)", sx + 2.9, sy + 1.95, 0.105, "WALL-EXT")
    # 상부 플레이트 결속
    rect(msp, sx - 0.06, sy + 2.30, 0.5, 0.16, "DOOR")
    T(msp, "PL-1 상부 플레이트 + fascia 띠장 결속", sx + 0.62, sy + 2.86, 0.105, "DOOR")
    msp.add_lwpolyline([(sx - 0.08, sy + 2.50), (sx + 0.3, sy + 2.53), (sx + 0.3, sy + 2.42)],
                       close=True, dxfattribs={"layer": "NOTE"})
    T(msp, "FL-1 tie-in 플래싱 + head flashing", sx + 0.62, sy + 2.68, 0.105, "NOTE")
    T(msp, "F-1 신규 테두리 기초 / 피어", sx + w + 0.04, sy - 0.78, 0.1, "WALL-INT")
    line(msp, sx + w + 0.18, sy - 0.02, sx + w + 0.5, sy - 0.16, "DIM")
    T(msp, "배수 구배 2% + 집수구", sx + w - 2.6, sy - 0.34, 0.1, "DIM")
    T(msp, "기존 카포트 슬래브 (비단열 · conditioned 기초 아님)", sx + 0.05, sy - 0.42, 0.11, "NOTE")

    # ---------------- 부재 일람 (우상)
    tx = 7.9
    T(msp, "신규 부재 일람 (예비 · EOR 확인)", tx, 13.85, 0.19, "TITLE")
    table(msp, [
        ("부재", "위치", "예비 단면", "비고"),
        ("W-1..W-3 벽", "서/남/동 신규 외벽", CARPORT.get("stud", "2x6 @ 16 o.c."), "하부 PT 실"),
        ("PL-1 상부판", "신규 벽 상부", "2x6 + 띠장(ledger)", "볼트 @24in"),
        ("P-1 / P-2 기둥", "기존 개구부 양측", CARPORT.get("post", "6x6 PT"), "기초 앵커"),
        ("H-1 헤더", "기존 개구부", "2-1.75x11.875 LVL", "EOR 확인"),
        ("R-1 지붕 골조", "외벽화 구역 상부", "lean-to / 박공", "신규 벽 위"),
        ("F-1 기초", "신규 외벽 하부", "12in 폭 · 동결심도", "슬래브 미사용"),
        ("SL-1 바닥", "거주 바닥", "R-10 + 마감", "또는 올린 마루"),
    ], tx, 13.35, cols=[0.0, 2.5, 5.4, 8.6], step=0.40, h=0.12)

    # ---------------- 주기 (우중)
    notes(msp, [
        "1. 구조 형식: " + META.get("structure_type", "Freestanding enclosure on new foundation"),
        "2. 신규 지붕 하중 → 신규 벽·기둥 → 신규 기초. 기존 주택 지붕·벽체로 전가하지 않는다.",
        "3. 기존 개구부 헤더 H-1 은 기존 부재 확인 후 유지 또는 보강 (EOR 판단).",
        "4. " + CARPORT.get("top_plate", ""),
        "5. " + CARPORT.get("flashing", ""),
        "6. " + CARPORT.get("drainage", ""),
        "7. " + CARPORT.get("slab_note", ""),
        "8. 기존 슬래브 두께·철근·기둥 위치·처마고는 미확인 (실측 선행). 400 SF 정방형은 가정.",
    ], x=tx, y=9.95, step=0.42, h=0.115)

    # ---------------- 접합 상세 3종 (우하)
    dy = 4.55
    T(msp, "접합 상세 (개념 · 축척 없음)", tx, dy + 1.80, 0.17, "TITLE")
    for i, (lab, sub) in enumerate([
        ("DET-1 상부 플레이트 ↔ fascia", "띠장 볼트 + 앵글"),
        ("DET-2 지붕 ↔ 기존 외벽 플래싱", "tie-in · 역물매 차단"),
        ("DET-3 슬래브 단부 배수", "외벽 밖 배수"),
    ]):
        bx = tx + i * 4.15
        box(msp, bx, dy, 3.7, 1.55)
        T(msp, lab, bx + 0.1, dy + 1.62, 0.11, "TEXT")
        T(msp, sub, bx + 0.1, dy + 1.4, 0.1, "NOTE")
        if i == 0:
            rect(msp, bx + 0.3, dy + 0.2, 0.7, 1.0, "WALL-EXIST")
            rect(msp, bx + 1.0, dy + 0.2, 0.3, 1.0, "WALL-EXT")
            line(msp, bx + 0.95, dy + 0.85, bx + 1.9, dy + 0.85, "DOOR")
            T(msp, "볼트", bx + 1.35, dy + 0.95, 0.09, "DOOR")
        elif i == 1:
            line(msp, bx + 0.3, dy + 1.05, bx + 2.9, dy + 0.75, "WALL-EXT")
            line(msp, bx + 0.3, dy + 0.25, bx + 0.42, dy + 1.08, "WALL-EXIST")
            msp.add_lwpolyline([(bx + 0.38, dy + 1.12), (bx + 1.0, dy + 1.0), (bx + 1.0, dy + 0.9)],
                               close=True, dxfattribs={"layer": "NOTE"})
            T(msp, "플래싱", bx + 1.1, dy + 1.0, 0.09, "NOTE")
        else:
            line(msp, bx + 0.3, dy + 0.6, bx + 2.9, dy + 0.6, "WALL-EXT")
            line(msp, bx + 2.1, dy + 1.15, bx + 2.85, dy + 0.65, "DIM")
            T(msp, "2%", bx + 1.5, dy + 0.3, 0.09, "DIM")

    doc.saveas(path)
    return path


# ------------------------------------------------------------------ A-19
def a19_main_floor(path):
    from ezdxf.enums import TextEntityAlignment as TEA
    doc = new_doc()
    msp = doc.modelspace()
    sheet_frame(msp, "A-19", f"기존 주택 재구성 계획 ({main_floor_bed_count()} 침실 + 욕실)")

    rooms = MAIN_FLOOR.get("rooms", [])
    env_w, env_d = MAIN_FLOOR.get("envelope_ft", (46.0, 40.8))
    S = 0.55
    x0, y0 = 1.0, 6.6

    def X(fx):
        return x0 + fx * FT * S

    def Y(fy):
        return y0 + fy * FT * S

    box(msp, X(0), Y(0), env_w * FT * S, env_d * FT * S)

    for code, ex, pr, kind, rx, ry, rw, rd in rooms:
        msp.add_lwpolyline([(X(rx), Y(ry)), (X(rx + rw), Y(ry)), (X(rx + rw), Y(ry + rd)),
                            (X(rx), Y(ry + rd))], close=True, dxfattribs={"layer": "ROOM"})
        cx, cy = X(rx + rw / 2), Y(ry + rd / 2)
        short = pr.split("(")[0].strip()
        wm = rw * FT * S
        label = f"{code} {short}" if wm > 1.15 else code
        hh = 0.10 if wm > 1.5 else (0.085 if wm > 1.15 else 0.08)
        T(msp, label, cx, cy + 0.10, hh, "TEXT", TEA.MIDDLE_CENTER)
        T(msp, f"{rw*rd:.0f} SF", cx, cy - 0.065, 0.075 if wm <= 1.15 else 0.085,
          "DIM", TEA.MIDDLE_CENTER)

    # 복도 유효폭
    hx = X(env_w * 0.62)
    msp.add_line((hx, Y(22.4)), (hx, Y(26.0)), dxfattribs={"layer": "DIM"})
    T(msp, "복도 43in 가정", X(env_w * 0.30), Y(24.2) - 0.05, 0.095, "DIM")

    # 이그레스 창
    for code, room, side, action, fx, fy in MAIN_FLOOR.get("egress", []):
        mx, my = X(fx), Y(fy)
        msp.add_line((mx - 0.24, my - 0.06), (mx + 0.24, my - 0.06), dxfattribs={"layer": "WINDOW"})
        msp.add_line((mx, my + 0.1), (mx, my - 0.22), dxfattribs={"layer": "WINDOW"})
        T(msp, code, mx - 0.07, my + 0.14, 0.1, "WINDOW")

    T(msp, "기존 1층 1,877 SF · 개념도 (SCHEMATIC, NTS ≈1:100)", x0, Y(env_d) + 0.36, 0.18, "TITLE")
    T(msp, "/".join(e[0] for e in MAIN_FLOOR.get("egress", [])) + " = 침실 이그레스 창 (IRC R310)", x0, Y(env_d) + 0.16, 0.11, "WINDOW")

    notes(msp, [
        "1. 면적 가정: 지상층 1,877 SF (카운티). 개념 외피 46'-0\" x 40'-10\" = 1,876.8 SF.",
        "2. 실 치수는 벽 중심선 기준 가정값 - 합계가 1,876.8 SF 로 카운티 면적과 일치.",
        "3. 기존 천장고 " + META.get("existing_ceiling", "8 ft (ASSUMED - UNKNOWN)"),
        "4. " + MAIN_FLOOR.get("corridor_note", ""),
        "5. 신규 욕실: " + MAIN_FLOOR.get("new_bath", ""),
        f"6. 이그레스: 침실 {main_floor_bed_count()}개소 · 순개구부 5.7 SF 이상 · 창턱 44in 이하 (IRC R310).",
        "7. 기존 벽·창 위치, 내력벽 여부, 배관 위치는 미확인 - 실측 후 확정.",
        "8. 위 실 배치는 개념 가정이며 실측값이 아니다 (형상·벽 위치·창 위치 확인 필요).",
    ], x=1.0, y=5.9, step=0.42, h=0.105)

    # 우측 표
    tx, ty = 9.5, 13.70
    T(msp, "기존 vs 제안 실 용도 (Existing / Proposed room use)", tx, ty + 0.42, 0.18, "TITLE")
    rows = [("CODE", "기존 용도", "SF", "제안 용도 (AFH)", "비고")]
    for code, ex, pr, kind, rx, ry, rw, rd in rooms:
        note = ""
        if kind == "bedroom":
            note = "침실 · 이그레스"
        elif code == "R6":
            note = "신규 욕실"
        elif kind == "bath":
            note = "개보수"
        elif code == "R11":
            note = "카포트 연결문"
        elif code == "R13":
            note = "문서·약품"
        rows.append((code, ex, f"{rw*rd:.0f}", pr, note))
    tot = sum(r[6] * r[7] for r in rooms)
    rows.append(("계", "지상층 (assessor)", f"{MAIN_FLOOR.get('gross_sf', 1877):,}", "동일 (증축 없음)", ""))
    table(msp, rows, tx, ty, cols=[0.0, 1.7, 4.9, 6.0, 9.9], step=0.355, h=0.115)
    yy = ty - 0.355 * (len(rows) + 1)
    T(msp, f"실 사각형 합계 {tot:.1f} SF / 카운티 지상층 {MAIN_FLOOR.get('gross_sf', 1877):,} SF "
           f"({'일치' if abs(tot - MAIN_FLOOR.get('gross_sf', 1877)) < 2 else '불일치'})",
      tx, yy - 0.05, 0.115, "DIM")
    _mb = main_floor_beds()
    T(msp, f"침실 {len(_mb)}개소 합계 {sum(r[6]*r[7] for r in _mb):.0f} SF "
           f"({' + '.join(f'{r[6]*r[7]:.0f}' for r in _mb)} SF, 최소 70 SF 충족)", tx, yy - 0.38, 0.115, "DIM")
    T(msp, "AFH 라이선스(DSHS/WAC 388-76) 요건은 건축 허가와 별개로 검토",
      tx, yy - 0.71, 0.115, "NOTE")

    doc.saveas(path)
    return path


def main():
    if not META.get("carport_enclosure"):
        print("carport_enclosure 플래그 없음 - S-04 / A-19 생성 안 함")
        return 0
    made = [
        s04_enclosure_structure(os.path.join(OUT, "S-04_카포트외벽구조.dxf")),
        a19_main_floor(os.path.join(OUT, "A-19_기존주택재구성.dxf")),
    ]
    for p in made:
        print("saved", os.path.basename(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Changelog

## 0.6.0 — 2026-10-25 — intake stage (`g2a.py intake`), evidence sheet G-07, 44 sheets

### What changed

The pipeline started every address from a template `design.py`. It now has a first stage that
starts from what an operator actually has on site: the walk-through video, the photos taken with
it, and the dimensions spoken into that video once they are transcribed to text. This is the
workflow of the video *실측 영상을 챗GPT에 넣었더니… 도면과 3D까지* (뽁숑이의 AI 스케치업,
`0EX2GDVJGB4`): measurement footage + a spoken description in, plans out.

| Piece | Detail |
|---|---|
| `src/pipeline/intake.py` (new) | reads `projects/<id>/intake/`, writes `measurements.json`, `evidence.json`, `design_rooms.py`; exit 1 when no line parses |
| `sheets_packet.py` | new `g07_measurement()` → `G-07_실측근거.dxf`, one row per parsed measurement and per evidence file |
| `validate_packet.py` | `G-07` added to `EXPECTED` (standard 44, carport branch 46) |
| `g2a.py` | `intake` subcommand; needs no `design.py`, so footage can be processed the day it arrives |
| sheet count | **43 → 44** (standard), **45 → 46** (carport branch): `G-07` sits right after `G-06` |

### Accepted dimension lines

```
침실A 12'-10" x 9'-7"     피트-인치
침실B 12'10" x 9'7"       피트-인치 (구분자 없음)
수납 8' x 5'              피트만
욕실 3.6m x 2.4m          미터
거실 3600 x 2400 mm       밀리미터 (줄 끝 단위)
주방 360 x 240 cm         센티미터
Bedroom A 12'10" x 9'7"   영어 실 이름
```

Output rows are `{room, w_m, d_m, area_m2, source:"notes.txt:3", raw, unit}`; the plate is the
declared footprint from `META`/`meta.json` when present, otherwise the room-area sum plus 12 %
circulation in a rectangle with aspect 1.0–1.6. A line with no unit (`차고 12 x 9`) or half a
pair (`복도 11'-2" x ?`) is reported as a warning, never guessed.

**Transcription stays outside the app.** The video is only hashed as evidence; the spoken numbers
arrive as `transcript.txt`/`notes.txt`. `evidence.json` records `file`, `kind`, `bytes`, `sha256`
and, for images, `width_px`/`height_px` through PIL.

### Measured on the rebuilt projects

`projects/_intake-selftest` (synthetic fixture, 6 good lines + 2 bad, 2 placeholder PNGs, no video):

| Quantity | Result |
|---|---|
| parsed | 6 rooms, 52.488 m² / 565 SF |
| plate | 9.05 × 6.50 m = 58.83 m² (633 SF), aspect 1.39, `basis=room-sum` |
| warnings | 2 — `notes.txt:9` 치수 쌍이 아님, `notes.txt:10` 단위 불명 |
| exit code | 0 |

`projects/3515-hawthorne-pl` (real, no `intake/` folder, so the empty path is exercised):

| Gate | Before | After |
|---|---|---|
| DXF / SVG | 43 / 43 | **44 / 44** |
| audit | 74/74 | **74/74** |
| validator | 7/7 | **7/7** (시트 44장 · PDF 44쪽) |
| master PDF | 47 pages | **48 pages** |
| page size | A3 only | A3 only, one size 1191.12 × 841.92 pt |
| blank / dark | 0 / 0 | **0 / 0** (18 dpi pixel scan) |
| splits | 30 / 8 / 5 | **30 / 9 / 5** |
| text-bbox gate | rc=0 | rc=0, max x 18.924, min y −0.980 |
| G-07 | — | page 8 of the drawing set, prints `실측 자료 없음 (설계 기준값 사용)` |

The same sheet with evidence present was rendered from `_intake-selftest`'s `intake/` against the
3515 design: 6 measurement rows (`notes.txt:3 · 36697b32`), 2 photo rows (`100x80 px · b78aa1ac`),
1 transcript row, and the warning count on the sheet.

### Known residual

`design_rooms.py` tiles the plate by room area; a room whose measured aspect does not fit its tile
is stretched to keep the area (the measured w/d stay in `MEASURED`). Wall, door and window
positions are still hand work — the scaffold is a starting point, not a design.

All notable pipeline changes. Dates are the day the change was rebuilt and verified on
real projects (3571 Cassie Dr SW, 7504 32nd Ave SE, 1713 Winterwood Dr).

## 0.5.0 — 2026-10-24 — LS-01 egress sentence derives from ROOMS; all six projects regenerated

### The defect

`sheets_permit2.sheet_life_safety` printed the 3571 reference program as a literal:

```
"이그레스 창: 침실A/B/C (순개구부 5.7 sqft 이상 확인)"
```

On a 2-bedroom program the LS-01 (연기·CO) sheet named `침실A/B/C` — three egress windows on a
plan that draws `WD01 침실A` and `WD02 침실B`. This is the residual recorded as *Known residual*
under 0.4.0. Like the 0.4.0 defects it survives every gate: `audit_3571.py` checks the model and
`text_bbox.py` only measures against the frame, so only the rendered PDF shows it.

### The fix — one derivation, shared by every sheet that names bedrooms

`sheets_v2.py` now owns the program-read helper set:

```
def bedroom_names():
    """ROOMS 에서 kind=='bedroom' 인 실 이름 목록"""
    return [r["name"] for r in design.ROOMS if r.get("kind") == "bedroom" and r.get("name")]

def bed_count():
    return len(bedroom_names())

def bed_label():
    """2침실이면 '침실A/B', 3침실이면 '침실A/B/C'"""

def egress_window_count():
    """WINDOWS 이름에 '이그레스' 가 들어간 창 수"""
```

LS-01 now prints `이그레스 창: {bed_label()} {bed_count()}개소 (순개구부 5.7 sqft 이상 확인)`,
so the sentence carries both the names and the count of the project's own bedrooms.

### Same class, fixed in the same pass (grep of `src/pipeline/` for literal bedroom names)

| file | line | before | after |
|---|---|---|---|
| `sheets_permit2.py` | 94 | `이그레스 창: 침실A/B/C (…삭제 확인)` literal | `f"이그레스 창: {base.bed_label()} {base.bed_count()}개소 …"` |
| `sheets_3571_full.py` | 36-38 | `_beds()` local counter | delegates to `base.bed_count()` |
| `sheets_3571_full.py` | 298 | A-11 마감 일람표 row `침실 A/B/C` | `base.bed_label()` |
| `sheets_carport.py` | 36-42 | none | `main_floor_beds()` / `main_floor_bed_count()` read `MAIN_FLOOR['rooms']` |
| `sheets_carport.py` | 218 | A-19 title `계획 (3 침실 + 욕실)` | `계획 ({main_floor_bed_count()} 침실 + 욕실)` |
| `sheets_carport.py` | 258 | `E1/E2/E3 = 침실 이그레스 창` | codes joined from `MAIN_FLOOR['egress']` |
| `sheets_carport.py` | 266 | `6. 이그레스: 침실 3개소 …` | `침실 {main_floor_bed_count()}개소` |
| `sheets_carport.py` | 295-297 | `침실 3개소 합계 … (207 + 148 + 148 SF …)` | count and per-room SF list computed from the bedroom rows |
| `audit_3571.py` | 106-114 | none | `bed_label()` from `ROOMS` |
| `audit_3571.py` | 274 | C45 detail `침실 A/B/C` | `bed_label()` |
| `audit_3571.py` | 276-277 | C47 detail `WD01/02/03` | ids of the actual egress windows |
| `sheets_packet.py` | 96 | G-04 default `AFH 거주공간 - 침실 3 + 통합욕실 1` | count from `ROOMS` (`bed_count()` / bath count) |
| `sheets_v2.py` | 447 | G-00 item 5 `신규 5x4 슬라이더 3개` | `egress_window_count()` |

`grep -rn "침실C\|침실A/B/C\|침실 3개소" src/pipeline/*.py` now returns only the two docstrings
of `bed_label()` that spell the example output; no sheet or audit string carries a bedroom name or
bedroom count as a literal.

### All six projects regenerated under 0.5.0

Build → A3 HTML → Playwright print (fresh tab per file, `preferCSSPageSize`) → `trim_blank.py` →
bind → `g2a.py check`. Nothing was reused from the previous version: every DXF, SVG, sheet PDF and
master PDF below was produced by this run.

| project | program | sheets | audit | validator | master | page size | blank/dark @18 dpi | LS-01 egress sentence |
|---|---|---|---|---|---|---|---|---|
| 3571-cassie | 3 bed / 736 SF | 43 | 74/74 | 7/7 | 71 p | A3 only | 0 / 0 | `침실A/B/C 3개소` |
| 7504-32nd-ave-se | carport + 3 bed main floor | 45 | 74/74 | 7/7 | 49 p | A3 only | 0 / 0 | `침실A/B/C 3개소` |
| 1713-winterwood-dr | 3 bed / 720 SF | 43 | 74/74 | 7/7 | 47 p | A3 only | 0 / 0 | `침실A/B/C 3개소` |
| 133-jalyn-st | 2 bed / 528 SF | 43 | 74/74 | 7/7 | 47 p | A3 only | 0 / 0 | `침실A/B 2개소` |
| 3515-hawthorne-pl | 2 bed / 440 SF | 43 | 74/74 | 7/7 | 47 p | A3 only | 0 / 0 | `침실A/B 2개소` |
| 7021-southwick-ct | 2 bed / 505 SF | 43 | 74/74 | 7/7 | 47 p | A3 only | 0 / 0 | `침실A/B 2개소` |

Every master page is 1191.12 × 841.92 pt (one distinct size per file), no FAIL line in any audit
run, validator hard fails 0, and the trailing Chromium blank page was dropped from all 21 rendered
PDFs (44→43, 46→45, 2→1, 3→2). The 3571 master keeps its Letter→A3 normalisation for appendix
B/C/D and lands at 71 pages; its index stays 2 pages by design.

## 0.4.0 — 2026-10-24 — sheet text derives from the program (G-01 spacing, egress count, S-01 label)

Three defects found while building 7021 Southwick Ct SW. All three are the same class: a sheet
string that was correct for the 3571 Cassie reference program was written as a literal, so every
smaller or larger program printed a sentence that did not describe it.

### 1. G-01 note spacing was fixed at 0.62 and the notes ran through the footer

`g01_general_notes` placed the note lines with `step=0.62` from `y=12.8` regardless of how many
lines the wrapped block produced. The 11 notes of 3571 fit; on 7021 the `structure_note` alone
wrapped to 15 lines and the block crossed the footer line `이 도면 세트는 예비 검토용입니다.`
at `y=5.4` — while `text_bbox.py` still passed, because a text block overlapping another text
block stays inside the frame. Text-on-text is invisible to a frame gate.

```
_lines = wrap_notes(lines, 74, "    ")
_step  = min(0.62, (12.8 - 6.0) / max(len(_lines), 1))   # 12.8 top → 6.0 hard floor
note(msp, _lines, x=0.8, y=12.8, step=_step, h=0.19)
```

The step now shrinks with the line count and never drops below the footer (11 wrapped lines →
0.618, 15 → 0.453). Measured on the two rebuilt projects: 133 11 note lines, every consecutive
baseline gap 0.618, last note 1.218 above the footer; 3515 12 lines, gap 0.567, last note 1.167
above the footer, against a 0.19 text height and a 0.22 footer height.

### 2. G-01 / LS-02 printed `침실 3개소` on 2-bedroom projects

Both egress sentences were literals (`"6. 이그레스: 침실 3개소 ..."` on G-01, `"1. 침실 3개소 ..."`
on LS-02). A new helper reads the program instead:

```
def _beds():
    """design.ROOMS 의 bedroom 실 수"""
    return sum(1 for r in design.ROOMS if r.get("kind") == "bedroom")
```

`A-08` had the same problem one level down: it built `[(침실A …), (침실B …), (침실C …)]` and
looked each room up by name, so a 2-bedroom program raised `StopIteration`. It now iterates the
bedroom rooms from `design.ROOMS` and cycles a bed-size table, so bed count follows the program.

### 3. S-01 schedule row said `침실C/복도` on a 2-bedroom program

The header row is the wall the header actually lands in. It is now read off `design.WALLS`:

| project | before | after (this rebuild) |
|---|---|---|
| 133-jalyn-st (2 bed) | 침실C/복도 (literal) | `W05 침실A·B/복도` |
| 3515-hawthorne-pl (2 bed) | 침실C/복도 (literal) | `W05 침실A·B/복도` |

`_door_wall_label()` walks `design.WALLS` and returns the first non-exterior wall whose name
contains `침실` (falling back to `내벽/복도`), so the row names the wall that actually carries the
header instead of a bedroom letter that may not exist.

`META = design.META` in `sheets_permit2.py` had also been left as `META = design.METAMETA =
design.META` by an earlier in-place edit; restored to the plain assignment (byte-identical sheets
before and after — all 43 SVGs unchanged).

### Stale text impact: 3515 Hawthorne Pl already shipped with a wrong egress count

3515 is a 2-bedroom program (440 SF attached garage, plate 22'-0" × 20'-0", egress windows WD01
침실A / WD02 침실B) and its master package was generated under 0.3.0, so `G-01` item 6 and `LS-02`
item 1 read `침실 3개소` — a package that tells the AHJ there are three egress windows where the
set draws two. 133 Jalyn St (528 SF detached garage, also 2 bedrooms) carried the same sentence.
A stale-text defect survives every gate this pipeline has: `audit_3571.py` checks the model, not
the prose, and `text_bbox.py` only measures against the frame, so the only detector is reading
the rendered PDF. Both projects were rebuilt and re-rendered for this version.

### Also in this push (found on the same rebuild pass)

- `sheets_v2.ftin` carries a rounded 12 inches into the next foot (`21'-12"` → `22'-0"`).
- `sheets_packet.g04_application` takes META-driven extra rows and footnotes (`g04_extra`,
  `g04_footnote`) and shrinks the row step to keep them inside the frame; the G-04 title is
  `허가 신청 데이터 - {jurisdiction}` instead of a parenthesised city.
- `sheets_packet.g06_coordination` shrinks the discrepancy-table step so a long log stops short
  of the note block at `y=7.6`.
- `validate_packet.py` picks the drawing-set PDF by name when the `도면세트` convention is used,
  otherwise by page count, so projects with address-named PDFs validate too.

### Rebuilt and re-verified (this version)

| project | program | sheets | audit | validator | master | A3 only | blank/dark @18dpi | egress sentence | `침실 3개소` | G-01 overlap |
|---|---|---|---|---|---|---|---|---|---|---|
| 133-jalyn-st | 2 bed / 528 SF detached | 43 | 74/74 (C20 WARN) | 7/7 | 47 p | yes | 0 / 0 | `침실 2개소` | 0 | 0 pairs |
| 3515-hawthorne-pl | 2 bed / 440 SF attached | 43 | 74/74 (C20 WARN) | 7/7 | 47 p | yes | 0 / 0 | `침실 2개소` | 0 | 0 pairs |

Overlap measured with ezdxf: every `TEXT` inside the 0..21.0 × 0..14.85 frame, pairwise bbox
intersection on both axes → 0 pairs; per-column consecutive baseline gaps ≥ the smaller text
height (worst ratio 2.98× the required minimum).

### Known residual (not fixed here)

`sheets_permit2.sheet_life_safety` (LS-01 연기·CO) still writes `이그레스 창: 침실A/B/C …` as a
literal, so both 2-bedroom projects say A/B/C on a two-bedroom plan. It is the same class as the
three fixes above and needs a `_beds()`-style label; it is not in this version because fixing it
means rebuilding every project again.

## 0.3.0 — 2026-10-24 — program-aware audit (checks derive from design.py)

### The defect

`audit_3571.py` carried the 3571 Cassie reference program as literal expectations:
3 bedrooms, 736 SF internal, 12+ walls, 6+ doors, exactly 3 egress windows, "10'-5""
encoded as a substring test and a mandatory HVAC room. A legitimately smaller program
therefore failed checks that are not code violations. On the real 133 Jalyn St project
(2 bedrooms, 528 SF detached garage conversion, third AFH bedroom in the existing house)
the audit scored **67/74** with 7 failures that were all reference-program mismatches:
C15 침실 3개, C20 천장고 10'-5", C24 벽 12개 이상, C27 HVAC실, C31 문 6개 이상,
C35 침실별 출입문 3개, C37 이그레스 창 3개. Only C15/C35/C37 were even arguably about the
smaller program; the rest were pure hardcoding.

### The fix — every expectation is derived from the project's own design.py

| check | before | after |
|---|---|---|
| C15 침실 | `len(beds) == 3` | label `침실 N개 (설계 기준)`; `N == ROOMS kind=='bedroom'`, cross-checked against the bedroom count declared in META (`scope_kr` / `scope` / `proposed_use`) |
| C20 천장고 | `"10'-5\"" in ft_in(wall_height)` | `wall_height` vs `META['ceiling']` (declared design basis); with no measured ceiling (`existing_ceiling_measured`) the check passes WARN-style with detail `설계 기준값 (현장 실측 필요)` instead of FAIL |
| C21/C22 벽 두께 | detail from `WALLS[0]` / `WALLS[4]` | first exterior / first interior wall, `내벽 없음` when a program has none |
| C24 벽 | `len(WALLS) >= 12` | `len(WALLS)` (label only) + every ROOM must be bounded on 4 sides by wall segments within 0.15 m (`bounding_walls()`) |
| C25 실 중복 | always PASS (`스키매틱 기준`) | room rectangles must not overlap (area double counting) |
| C26 욕실 파티션 | always PASS | bathroom must have at least one bounding wall (detail names it) |
| C27 HVAC실 | mech room mandatory | if ROOMS has `kind=='mech'`, that room must be ≥1 m² and enclosed on ≥3 sides; if the program has no separate mech room the detail is `n/a (설계에 별도 기계실 없음)` |
| C31 문 | `len(DOORS) >= 6` | label `문 N개 (설계 기준)`; every door must resolve a host wall in `WALLS` |
| C32 문 폭 | ≥0.81 m, offenders by name | unchanged rule, detail now shows each offender's width in inches |
| C35 침실 출입문 | `>= 3` | `>= len(beds)` |
| C36 창 | `len(WINDOWS) >= 4` | `>= len(beds) + 1` |
| C37 이그레스 창 | `== 3` | `== len(beds)` |
| C39 창턱 | `max(sill)` over all windows | `max(sill)` over egress windows only, 0.0 default |
| C13 면적 | `META['internal_sf']` default 736 | `META['internal_sf']`, else 95% of the plate |

Egress area (C38, C41-C47), smoke/CO (C41-C44), MEP (C51-C70), energy (C71-C74) and
provenance (C01-C10) checks are untouched. Total stays at 74 checks; `warn: true` on a
PASS row renders an amber row in `report_full.html` and is counted as passed.

### Proof that a smaller program is no longer punished, and defects still fail

Rejected-defect injections (each one applied to a copy of `design.py`, then the audit run):

| inject | result |
|---|---|
| baseline 133 (2 bed / 528 SF, no injection) | 74/74, only C20 WARN (설계 기준값) |
| delete the 침실B ROOM (META declares 2) | C15 FAIL (1 bedroom vs declared 2) |
| wall_height 9'-0" vs META ceiling 8'-0" | C20 FAIL |
| delete wall W08 (욕실/수납) | C24 FAIL (room unbounded) |
| move 복도 rect onto 침실A | C25 FAIL (overlap) |
| door D04 hosted on a non-existent wall | C31 FAIL |
| bathroom door 2'-0" wide | C32 FAIL |
| drop 2 windows (3 required) | C36 FAIL |
| relabel WD02 without "이그레스" | C37 FAIL |
| 1713: move HVAC room off its walls | C27 FAIL |

### Rebuilt and re-verified on all four projects (this version)

| project | program | sheets | audit | validator | master | A3 only | blank/dark @18dpi | text-bbox |
|---|---|---|---|---|---|---|---|---|
| 133-jalyn-st | 2 bed / 528 SF | 43 | 67/74 → **74/74** | 7/7 | 47 p | yes | 0 / 0 | ok |
| 1713-winterwood-dr | 3 bed / 720 SF | 43 | 74/74 → **74/74** | 7/7 | 47 p | yes | 0 / 0 | ok |
| 7504-32nd-ave-se | carport enclosure | 45 | 74/74 → **74/74** | 7/7 | 49 p | yes | 0 / 0 | ok |
| 3571-cassie | 3 bed / 736 SF | 43 | 74/74 → **74/74** | 7/7 | 71 p | yes | 0 / 0 | ok |

PDFs were re-rendered (A3 landscape, `preferCSSPageSize`), no trailing blank page was
produced, and the 3571 appendix B/C/D Letter sources stay Letter until the binder's
documented Letter→A3 normalisation, so the bound masters contain A3 pages only.

## 2026-10-24 — META-driven sets, carport branch, frame-safe footer

### Jurisdiction and provenance are META-driven (no hardcoded Tumwater / 3571)

Every sheet now reads its city, jurisdiction, parcel, tax id, legal description, source
drawings and code year from `design.META`. What used to be literal 3571 strings is a
`.get()` default, so a second and third property could run through the same code path
without editing the generator:

- `sheets_packet.g04_application` — sheet title `허가 신청 데이터 ({META['jurisdiction']})`,
  legal / parcel / zoning / coverage rows from META.
- `sheets_site.C-01` — lot area, coverage, parking count, house and parking labels and the
  site note block all come from META (`site_notes`, `house_label`, `parking_label`,
  `parking_spaces`, `lot_sf_*`), drawing scale stays 1:200.
- `sheets_3571_full.g01_general_notes` — applicable code line and source-drawing line from
  META (`jurisdiction`, `source_drawings`).
- `sheets_v2.sheet_frame` — title-block rows and the footer disclaimer from META.
- `audit_3571.py` / `validate_packet.py` — city, project number, internal area, parcel and
  tax id are read from META instead of asserted as 3571 constants.

### Carport-enclosure branch: S-04 + A-19

New `src/pipeline/sheets_carport.py`. When `META['carport_enclosure']` is true the set is
45 sheets instead of 43:

- **S-04 카포트 외벽화 구조** — new perimeter stud walls, top plate tied to the existing
  fascia, new gable / lean-to roof framing, tie-in flashing, and the note that new roof
  load must not be carried by the existing structure.
- **A-19 기존 주택 재구성** — main-floor reconfiguration concept (3 bedrooms, bath,
  corridor width, egress windows) with an existing-vs-proposed room-use table.

`g2a.py build` always runs the generator; with the flag absent it prints
`carport_enclosure 플래그 없음 - S-04 / A-19 생성 안 함` and writes nothing, so 3571 and
1713 stay at 43 sheets. `validate_packet.EXPECTED` appends `S-04`, `A-19` only when the
flag is set.

### Footer disclaimer wrapped and sized inside the frame

The disclaimer used to be one line at height 0.15 starting at x = 10.4 in a frame that ends
at x = 21.0, so it ran past the right frame edge on every sheet (measured worst x = 23.45 m
on 3571, 24.35 m on 7504, 26.79 m on 1713 — the overflow was the title-block rows and the
disclaimer together).

Now:

- the disclaimer is two lines of ≤ 45 characters, height 0.14, at `y0-0.42` and `y0-0.66`,
  left aligned at `x0` with the second line indented 0.15, dropping to 0.12 only if the
  measured width still exceeds the frame;
- every `TEXT` goes through `sheets_v2.T()`, which shrinks the height with
  `fit_h()` when the estimated render width (`1.35 × height × characters`, the SVG
  font-size factor) would cross `x = 20.90`;
- long note blocks (cover notes, C-01 site notes, G-01 general notes, the G-06 log note)
  are wrapped with `wrap()` / `wrap_notes()` instead of running off the sheet;
- title-block row 1 no longer prints the city twice when `META['project']` already
  contains it.

Verified with `src/tools/text_bbox.py` (ezdxf text bbox per sheet):

| project | before max(x) / min(y) | after max(x) / min(y) |
|---|---|---|
| 3571-cassie | 23.45 / -0.98 | 18.46 / -0.98 |
| 7504-32nd-ave-se | 24.35 / -0.98 | 20.44 / -0.98 |
| 1713-winterwood-dr | 26.79 / -0.98 | 18.46 / -0.98 |

Gate: `max(x) ≤ 20.95`, `min(y) ≥ -1.55`. `g2a.py build` now runs `text_bbox.py --assert`
as a hard stage, so a future sheet that spills fails the build instead of shipping.

### META-gated water-heater note

When `META['water_heater']` contains `차고` or `garage`, G-01 general notes gains item 11
and G-06 (discrepancy log) gains a line:

> 가스 온수기가 차고 내부에 설치 — 거주공간 전환 시 이전 또는 연소공기·격리 조치 필요 (IRC M1307 / G2408)

Appears on 3571-cassie and 1713-winterwood-dr, absent on 7504-32nd-ave-se (its META says
`미확인`, carport, no garage). Implemented once in `sheets_v2.water_heater_note()` and
called from `sheets_3571_full.g01_general_notes` and `sheets_packet.g06_coordination`.

### Tooling added

- `src/tools/text_bbox.py` — ezdxf bbox audit of every TEXT/MTEXT on every sheet;
  `--assert` exits 1 on a frame violation.
- `src/tools/pdf_check.py` — page count, distinct page sizes, blank (pixel std < 1.0) and
  dark (mean < 5) pages at 18 dpi.
- `src/tools/trim_blank.py` — drops Chromium's trailing blank page from a rendered PDF.
- `src/tools/sheets_to_a3_html.py` — SVG sheet folder to A3 landscape print HTML.

### Rebuilt and verified

| project | sheets | set PDF | master PDF | audit | validator | text bbox |
|---|---|---|---|---|---|---|
| 3571-cassie | 43 | 43 pp, A3 | 71 pp, A3 | 74/74 | 7/7 | pass |
| 7504-32nd-ave-se | 45 | 45 pp, A3 | 49 pp, A3 | 74/74 | 7/7 | pass |
| 1713-winterwood-dr | 43 | 43 pp, A3 | 47 pp, A3 | 74/74 | 7/7 | pass |

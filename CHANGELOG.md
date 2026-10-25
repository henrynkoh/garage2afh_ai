# Changelog

All notable pipeline changes. Dates are the day the change was rebuilt and verified on
real projects (3571 Cassie Dr SW, 7504 32nd Ave SE, 1713 Winterwood Dr).

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

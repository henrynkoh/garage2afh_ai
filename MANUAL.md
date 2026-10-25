# Operator manual

Everything an operator needs: install it, run it, read what it prints, know what stops the
build, and know when the package is actually done.

---

## 1. Install

```bash
git clone https://github.com/henrynkoh/garage2afh_ai.git
cd garage2afh_ai
python3 -m pip install --target pydeps ezdxf pypdf openpyxl numpy
```

Why `--target pydeps`: the CLI puts `pydeps/` on `PYTHONPATH` for every child stage and never
inherits yours, so the build behaves the same on a laptop, a locked-down office machine, and a
CI runner. `numpy` is not optional — `ezdxf` imports it, and its absence is the single most
common "it worked yesterday" breakage (see §7, failure 0).

Requirements: Python 3.11+ (3.13 tested), `ezdxf` 1.4.x, `pypdf`, `openpyxl` (budget sheet
import only), `pdfinfo`/`pdftoppm` (poppler) for page counting, optional Blender 4.x/5.x if you
want IFC export.

Verify the install without building anything:

```bash
python3 g2a.py --help
python3 -c "import sys; sys.path.insert(0,'pydeps'); import ezdxf; print(ezdxf.__version__)"
```

### When your Python cannot import `ezdxf`

Some interpreters (Blender's bundled Python, a frozen runtime, a venv with no numpy) are the
only ones that work on a given machine. Point the CLI at the interpreter that *can* import
`ezdxf` instead of fighting it:

```bash
export G2A_PYTHON=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
export HOUSEBIM_PYDEPS=$HOME/Documents/HouseBIM/pydeps   # where ezdxf/pypdf actually live
```

`G2A_PYTHON` is used for every child stage (`g2a.py` itself stays on whatever Python started
it). `HOUSEBIM_PYDEPS` overrides the default `<repo>/pydeps`. The CLI strips `PYTHONHOME` and
`VIRTUAL_ENV` from the child environment on purpose: a child interpreter must load its own
standard library or it will fail with `ModuleNotFoundError: No module named '_csv'`.

---

## 2. Every command, with flags and expected output

### `g2a.py new`

```bash
python3 g2a.py new "<address>" --parcel <parcel> --lot-sf <sf> [--lot TEXT] [--tax-id ID]
                   [--city "CITY, ST ZIP"] [--slug SLUG] [--force]
```

| Flag | Meaning |
|---|---|
| `address` (positional) | full address; the city is everything after the first comma unless `--city` is given |
| `--parcel` | required, county parcel number, 10–11 digits, digits only |
| `--lot-sf` | lot size in square feet, from the survey (integer) |
| `--lot` | legal description text for META `lot` |
| `--tax-id` | dashed form of the parcel (`4038-00-00700`); defaults to `--parcel` |
| `--city` | overrides the city parsed from the address |
| `--slug` | folder name; defaults to a slug of the address (`123-jane-doe-st-tumwater-wa-98512`) |
| `--force` | overwrite an existing `projects/<slug>/design.py` |

Expected output:

```
[new] /Users/you/garage2afh_ai/projects/3571-cassie-drive-sw/design.py
      project='3571 Cassie Drive SW, Tumwater WA 98512' city='Tumwater WA 98512' parcel=40380000700 lot_sf=9411
      next: edit META + WALLS/ROOMS, then g2a.py build 3571-cassie-drive-sw
```

It writes `projects/<slug>/design.py` (template copy with META rewritten) and
`projects/<slug>/meta.json`. It does **not** create `out/` — `build` does.

### `g2a.py intake`

```bash
python3 g2a.py intake <slug>
```

Reads `projects/<slug>/intake/` and turns what the operator actually has on site into the
numbers the pipeline needs. It runs **before** `build` and does not need `design.py`.

| Put in `intake/` | What it is |
|---|---|
| `*.jpg`, `*.jpeg`, `*.png`, `*.heic` | site photos (hashed, never interpreted) |
| `*.mp4`, `*.mov` | measurement video (hashed, **never interpreted**) |
| `notes.txt`, `transcript.txt` | the spoken measurements, already transcribed to text |
| `measurements.json` | optional; rows a human typed, kept ahead of the transcript |

**Transcription is an operator/AI step outside this app.** Record the walk-through, transcribe
the audio somewhere else (phone dictation, a speech model), and paste the result into
`transcript.txt`. The app parses that text and hashes the video as evidence only.

Accepted dimension lines (one room per line, Korean or English room names):

```
침실A 12'-10" x 9'-7"        피트-인치
침실B 12'10" x 9'7"          피트-인치, 구분자 없음
수납 8' x 5'                 피트만
욕실 3.6m x 2.4m             미터
거실 3600 x 2400 mm          밀리미터 (단위가 줄 끝에 한 번)
주방 360 x 240 cm            센티미터
Bedroom A 12'10" x 9'7"      영어 실 이름
```

A blank line or a `#` comment closes a block; if the file holds several measurement blocks
(first pass, second pass) the largest one by floor area is used and the rest are listed as
alternatives. Lines that cannot be parsed are reported, never guessed.

Writes three files:

| File | Contents |
|---|---|
| `intake/measurements.json` | `rooms:[{room, w_m, d_m, area_m2, source:"notes.txt:3"}]`, `plate`, `warnings`, `sets` |
| `intake/evidence.json` | one row per photo/video/text: `file`, `kind`, `bytes`, `sha256`, and `width_px`/`height_px` for images |
| `intake/design_rooms.py` | the `ROOMS` draft to paste into `design.py`, plus the measured dimensions with their source line |

The plate is the declared footprint from `META`/`meta.json` when one exists (`footprint_m`,
`plate_ft`, `garage_ft`, `garage_sf`), otherwise the room area sum plus 12 % circulation in a
rectangle with an aspect between 1.0 and 1.6. `design_rooms.py` tiles that plate by room area
so every room stays inside it; wall/door/window positions are left for you.

Expected output (real run, `projects/_intake-selftest`, 6 lines + 2 bad lines):

```
[intake] /path/projects/_intake-selftest/intake
[intake] rc=0
   실측 인테이크 · _intake-selftest · 2026-10-25 00:29
   #    실(room)                    가로m     세로m      면적m2     면적SF  출처
   1    침실A                      3.912   2.921    11.426    123.0  notes.txt:3
   ...
   합계 6실                                          52.488    565.0
   플레이트 9.05 x 6.50 m = 58.83 m2 (633 SF) · 종횡비 1.39 · basis=room-sum
   경고 2건:
     - notes.txt:9  치수 쌍이 아님 (W x D 형식 필요) :: 복도 11'-2" x ?
     - notes.txt:10  단위 불명 (예: 12 x 9 - ft/m 표기 필요) :: 차고 12 x 9
```

Exit codes: **0** at least one measurement line parsed, **1** nothing parsed (evidence is still
written). The parsed dimensions land on sheet `G-07 실측 근거` at the next `build`.

### `g2a.py build`

```bash
python3 g2a.py build <slug> [--clean]
```

`--clean` deletes `out/*.dxf`, `out/*.svg` and `out/pdf/*.pdf` before building. Use it whenever
a sheet was renamed or a sheet was deleted from the register, otherwise the old file stays and
you get a duplicate sheet number or a stale page in the PDF.

Runs, in order, each as its own process:

| # | Stage | Writes |
|---|---|---|
| 1 | `sheets_v2.py` | `G-00`, `A-01`, `A-02`, `A-03`, `A-04`, `M-01` |
| 2 | `sheets_permit2.py` | `LS-01`, `M-02`, `E-01`, `P-02`, `S-01`, `EN-01` |
| 3 | `sheets_3571_full.py` | `G-01`, `G-02`, `S-02`, `S-03`, `A-05`…`A-18` (14), `E-02`, `E-03`, `P-03`, `P-04`, `M-03`, `LS-02`, `EN-02` (25 sheets) |
| 4 | `sheets_packet.py` | `G-03`, `G-04`, `G-05`, `G-06`, `G-07`, `EN-03` |
| 5 | `sheets_site.py` | `C-01` |
| 6 | `tools/dxf_to_svg.py <out>` | one `.svg` per `.dxf` (44 of each) |
| 7 | `audit_3571.py` | `checks_3571.json`, `자재목록.csv`, `자재목록.md`, `report_full.html` |

Expected output (abridged):

```
[sheets_v2] rc=0
   saved G-00_표지_일반주기.dxf
   saved A-01_기존평면도.dxf
   ...
[audit_3571] rc=0
   checks 74/74
   materials 27 -> 자재목록.csv 자재목록.md
   report -> report_full.html
[build] done · dxf=44 svg=44
```

A non-zero `rc=` on any stage is a gate failure, even when later stages still print `rc=0`:
`build` ORs the exit codes and returns non-zero overall.

### `g2a.py bind`

```bash
python3 g2a.py bind <slug> [--binder path/to/bind_master.py]
```

Refreshes the packet/application sheets (`G-03`…`G-07`, `EN-03`), regenerates every SVG (the
appendix index page links to them), then runs the project's binder to assemble the master PDF.

Binder discovery order: `--binder`, then `HOUSEBIM_BIND`, then `projects/<slug>/bind_master.py`,
then `projects/<slug>/out/appendix/bind_master.py`. With no binder it prints:

```
[bind] no binder found -> packet sheets + index built, master PDF not assembled
       pass one explicitly: g2a.py bind <slug> --binder <path/to/bind_master.py>
```

That is not a bug: page normalisation is project-specific (A3 landscape at 1191.12 × 841.92 pt,
letter pages scaled and centred, link annotations mapped through the same matrix), so the
binder lives next to the project, not in the pipeline. A binder must be idempotent and must
write both `out/appendix/` and `out/submit/`.

### `g2a.py check`

```bash
python3 g2a.py check <slug>     # exit 0 clean, exit 1 on a hard fail
```

Runs `validate_packet.py`, then re-reads `out/validation.json` and applies the hard-fail rule:
every `FAIL` counts except `사람이 채울 공란 식별` (a human-field warning, informational by
design — the applicant signs, the machine does not).

Expected output:

```
[validate_packet] rc=0
   [PASS] 필수 시트 존재 :: 44장 / 기대 44장
   [PASS] 사람이 채울 공란 식별 :: G-04_신청데이터: (LIC#,(건축주,(성명
   [PASS] 자동검사 74/74 :: 74/74
   [PASS] PDF 페이지 = 시트 수 :: PDF 44쪽 / 시트 44장
   [PASS] 면적표 산출값 존재 :: A-12 값 3개
   [PASS] G-03 수치(카운티) 반영 :: 9,411 / Tax-ID / Concrete
   [PASS] C-01 수치(측량) 반영 :: 9,357 SF / 37.6%
[check] 7/7 passed · hard fails=0
```

The rule is equality, not "at least": the PDF at `out/pdf/<slug>-도면세트.pdf` must have exactly
as many pages as there are sheets on disk. A 72-page master package (44 sheets + 28 appendix
pages) fails this gate until the binder and the validator agree on what "the sheet set" means
(see §5, failure 2).

### `g2a.py status`

```bash
python3 g2a.py status [slug]
```

One row per project (all projects when `slug` is omitted):

```
3571-cassie-drive-sw          dxf=44  svg=44  audit=74/74 validate=7/7 pdf=44
```

Read it left to right: sheets exist, previews exist, audit is complete, validator is complete,
PDF page count. `-` means the JSON has not been written yet.

---

## 3. File layout

```
g2a.py                     CLI: new / build / bind / check / status
src/pipeline/
  sheets_v2.py             core architectural sheets, and the shared drawing library
  sheets_permit2.py        life safety, mechanical, electrical, plumbing, structural, energy
  sheets_3571_full.py      the remaining A/E/P/M/S/EN detail sheets
  sheets_packet.py         application packet: property info, application data, checklist, log, intake evidence
  sheets_site.py           site and parking plan
  intake.py                measurement intake: dims -> measurements.json, evidence.json, design_rooms.py
  audit_3571.py            74 automated checks + takeoff + HTML report
  validate_packet.py       submission validator (7 checks) -> validation.json
src/tools/
  dxf_to_svg.py            DXF -> SVG previews, standard library + ezdxf only
templates/design.py        single source of truth, placeholders for a new project
projects/<slug>/
  intake/                  photos + measurement video + transcribed dims (g2a.py intake reads it)
  design.py                this project's single source of truth
  meta.json                machine-readable copy of the META values (status, tooling)
  bind_master.py           optional per-project binder
  out/                     generated: DXF, SVG, checks_3571.json, 자재목록.*, report_full.html
  out/pdf/                 the A3 sheet-set PDF
  out/appendix/            appendix blocks + index
  out/submit/              address-named files, exactly what goes to the portal
pydeps/                    pip --target dependencies (never commit)
```

Everything under `out/` is regenerable. Deleting it costs 2.8 seconds of compute and zero
judgement. Nothing outside `design.py` and `bind_master.py` should ever be edited by hand.

---

## 4. What each gate checks, and what makes it hard-fail

### Gate A — sheet register (`validate_packet.py`, check 1)

Compares the expected 44 sheet codes (`G-07` included) against the `.dxf` files on disk by prefix.
**Hard-fail:** fewer than 44 files, or a sheet with an unexpected code, or two files whose names
both start with the same code (`A-03_면적표_일람표.dxf` and `A-03_면적표.dxf`).

### Gate B — human fields (check 2)

Scans every SVG for `(성명`, `(LIC#`, `(건축주`, `(미포함)`, `TBD`, `미기재`.
**Never hard-fails** — it produces the list of fields the applicant must fill before signing.
Treat the list as a task, not as a pass.

### Gate C — automated audit (check 3, and `g2a.py build`)

Reads `checks_3571.json` and requires `passed == total` and `total >= 74`.
**Hard-fail:** any check FAIL, or a stale JSON from an earlier build (delete `out/` and rebuild).

Honest limits of the audit: of the 74 checks, **46 assert documentation presence** (the note or
symbol was drawn — the code asserts `True` because the sheet text is generated by the same
pipeline) and **28 compute from the model** (room count, areas, wall thickness, door widths,
window areas, egress count). Both kinds are useful, but only the computed 28 can catch a design
error; the asserted 46 catch a *missing* annotation. Do not report the score as if all 74 were
geometric proofs.

### Gate D — PDF page count (check 4)

Counts pages with `pdfinfo` and compares to the sheet count.
**Hard-fail:** no PDF at `out/pdf/<slug>-도면세트.pdf`, or `Pages:` missing from `pdfinfo`
output, or a page count that disagrees with the register. If `pdfinfo` is not on the path the
code expects, the page count comes back `None` and this gate fails with `PDF None쪽` — that is a
broken tool, not a broken package.

### Gate E — area values exist (check 5)

Requires at least one decimal value in `A-12_면적산출.svg`.
**Hard-fail:** `A-12` not generated, or generated with no numbers (an empty area schedule).

### Gates F and G — source numbers actually landed (checks 6, 7)

`G-03_부동산정보.svg` must contain the county lot size, the tax-ID and the foundation type;
`C-01_대지주차계획.svg` must contain the survey lot size and the coverage percentage.

**These two checks are project-specific on purpose** — they are the anti-copy-paste gate. The
shipped code asserts the 3571 values (`9,411`, `4038-00-00700`, `Concrete`, `9,357`, `37.6`),
which is why copying `design.py` from a previous project fails here instead of passing quietly.
For a new project, edit those two assertions in `src/pipeline/validate_packet.py` (the `num_ok`
and `cov_ok` lines) to the new project's county/survey numbers. Same for the PDF path on the
line above them and for `PDFINFO` at the top of the file.

---

## 5. The five most common failures, and the fix

### Failure 1 — unit/scale collision

Symptom: a dimension reads 16'-0" where the plan says 5'-3", or the takeoff says `157.1 sheet`
of 32 SF drywall for a wall area that is obviously 10× too big, or a sheet plots at 1:100 while
its title block says 1:50.

Cause: two of feet/metres/inches/mm met in one expression, or a room rectangle was entered in
inches into a file whose `ft()` helper returns metres.

Fix, in order:

1. `grep -n "FT\b\|0.3048\|ft(" projects/<slug>/design.py` — every length in `design.py` must
   come from `ft(feet, inches)`; never write a raw number in metres or inches.
2. Check the room areas: `A-12_면적산출` sums to the internal SF in META within 15 % (audit
   `C13`). If the sum is 10.76× or 0.0929× the target, you mixed SF and m².
3. Check the takeoff unit column for a single row family: quantity units are SF, m, ea, sheet,
   gal — a wall row in `m` next to a wall row in `SF` is the same defect one level up.
4. Rebuild with `--clean` so no sheet from the bad build survives.

### Failure 2 — stale PDF

Symptom: `check` reports `PDF 70쪽 / 시트 44장`, or the PDF shows yesterday's `A-03`, or the
validator passes a package that a human can see is wrong.

Cause: the `.dxf`/`.svg` were rebuilt but the sheet PDF and master PDF were not; or the binder
ran before the sheets.

Fix:

```bash
python3 g2a.py build <slug> --clean       # regenerate every sheet, delete stale outputs
# re-render the A3 sheet PDF from out/*.svg (QCAD export, or print the gallery in
# out/report_full.html to PDF), then:
python3 g2a.py bind <slug> --binder projects/<slug>/bind_master.py
python3 g2a.py check <slug>
```

Rule: the PDF is a build product of the sheets, never a file you keep between builds. If the
page count and the register disagree, the PDF is wrong by definition.

### Failure 3 — asserted total

Symptom: the budget sheet total is `$48,500` and no cell contains a formula; or `A-03` says
`736 SF` while `A-12` line items sum to `712.4 SF`.

Cause: a number was typed as a target (a bid, a quote, a hope) and then printed as if derived.

Fix:

1. Every total is `Σ(qty × unit price)`. If a line has no quantity from `자재목록.csv`, it is a
   placeholder, not a line item — mark it `(미포함)` so the validator lists it.
2. Cross-check the two area numbers: `A-03` (schedule) must equal `A-12` (computed). If they
   differ, `A-03` reads META and `A-12` reads the model — fix the model or fix META, then
   rebuild; never edit the sheet.
3. Declared ceiling vs priced total: if the total exceeds the ceiling, the fix is scope, not
   arithmetic.

### Failure 4 — blank page

Symptom: a sheet exists, has a title block, and is empty inside; or the PDF has a white page.

Cause: the sheet function ran with an empty collection (no doors, no windows, no rooms of that
kind) and drew only the frame; or the SVG was converted from a DXF written before the geometry.

Fix:

1. Open the `.svg` and look for the `<text>` of the expected content, not just the frame.
2. Empty collection is usually an upstream model problem: `C31` (≥6 doors), `C36` (≥4 windows),
   `C27` (HVAC room) failing tells you which collection is empty.
3. If the sheet is populated in DXF but blank in SVG, the SVG is stale — rerun
   `tools/dxf_to_svg.py <out>`.
4. A page that is blank only in the PDF means the binder appended a placeholder for a missing
   block PDF. Never let the binder invent pages; drop the block and let the page count fail.

### Failure 5 — duplicate sheet number

Symptom: validator reports 45 files for 44 expected sheets, or a reviewer sees two `A-03`s, or
the index lists a sheet twice.

Cause: a sheet was renamed (`S-01_표지` → `G-00_표지`) and the old file stayed in `out/`; or two
generator modules both draw the same code.

Fix:

```bash
python3 g2a.py build <slug> --clean
ls projects/<slug>/out/*.dxf | sed 's/.*\///' | cut -c1-4 | sort | uniq -d   # must print nothing
```

Then grep the pipeline for the duplicated code: `grep -rn "A-03" src/pipeline/`. One code, one
owning module. If a rename is permanent, delete the old file from the register in
`validate_packet.py` **and** from the owning module in the same commit.

---

## 6. Definition of done

A package is done when all of these are true, in this order, and none of them is a judgement
call:

1. `g2a.py status <slug>` shows `dxf=44 svg=44 audit=74/74 validate=7/7` and a PDF page count.
2. No `FAIL` in `validation.json` except `사람이 채울 공란 식별`.
3. The human-field list is either empty or written into the submission email to the applicant.
4. Every discrepancy between county and survey numbers appears on `G-06` with the chosen value.
5. The budget total is a formula over `자재목록.csv` lines, and it is ≤ the declared ceiling.
6. The master PDF is one page size, has no blank page, and its page count equals the register
   plus the appendix blocks.
7. `out/submit/` contains only address-named files, matching the portal naming rule.
8. A second person (the auditor) has read `checks_3571.json` and `validation.json` and signed.
9. `design.py` contains no `PROJECT ADDRESS`, `00000000000`, `CITY, ST ZIP` or `TBD`.

Until 1–9 hold, the package is a draft. A draft sent to a jurisdiction costs more than a day
of checking.

---

## 7. Troubleshooting quick table

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'numpy'` | `ezdxf` needs numpy, interpreter lacks it | `pip install --target pydeps numpy`, or set `G2A_PYTHON` to an interpreter that has it |
| `ModuleNotFoundError: No module named '_csv'` / `'_opcode'` | child interpreter loaded a foreign stdlib (`PYTHONHOME`) | the CLI already strips it; if you run a stage by hand, `unset PYTHONHOME VIRTUAL_ENV` |
| `no project at ...` | slug typo, or `design.py` missing | `g2a.py status` lists real slugs |
| `PDF None쪽` | `pdfinfo` not at the path in `validate_packet.py`, or no PDF yet | run `bind`, or fix `PDFINFO` to your `pdfinfo` |
| `G-03 수치(카운티) 반영 :: 누락` | new project with 3571 assertions still in the validator | edit `num_ok` / `cov_ok` in `validate_packet.py` |
| `[bind] no binder found` | project has no `bind_master.py` | pass `--binder`, or place `bind_master.py` in the project |
| audit 73/74 after a rename | stale `checks_3571.json` | `build --clean` |
| Korean sheet names show as `????.csv` in some tools | the filename is UTF-8; the tool is not | open with a UTF-8-aware viewer; do not rename the files |

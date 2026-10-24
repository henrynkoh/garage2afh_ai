# Tutorial — one real project, start to finish

We build the actual package that shipped: **3571 Cassie Dr SW, Tumwater WA 98512**, a 3-car
garage converted to an AFH unit.

| Fact | Value |
|---|---|
| Existing garage | 790 SF |
| New internal (conditioned) area | 736 SF |
| Lot (county) | 9,411 SF / 0.216 ac |
| Lot (survey) | 9,357 SF |
| Parcel / tax-ID | `40380000700` / `4038-00-00700` |
| Coverage (survey) | 37.6 % |
| Ceiling | 10'-5" |
| Program | 3 bedrooms + 1 accessible bath + HVAC room |
| Sheets | 43 (A3 landscape) |
| Checks | 74, in 12 categories |
| Package | 71 pages (43 sheets + 28 appendix pages) |

Every command below was run on this project; every output block is copied from the run, not
written from memory. Machine: Apple Silicon Mac, Python 3.13 (Blender-bundled), 43 sheets in
**2.8 s** wall clock.

---

## 0. Install (once)

```bash
git clone https://github.com/henrynkoh/garage2afh_ai.git
cd garage2afh_ai
python3 -m pip install --target pydeps ezdxf pypdf openpyxl numpy
python3 g2a.py --help
```

If your Python cannot import `ezdxf` (no numpy, or a frozen interpreter), point the CLI at one
that can:

```bash
export G2A_PYTHON=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
export HOUSEBIM_PYDEPS=$PWD/pydeps
```

From here on, `python3 g2a.py ...` means "the CLI", and every stage it shells out to runs under
`G2A_PYTHON`.

---

## 1. Scaffold the project

```bash
python3 g2a.py new "3571 Cassie Drive SW, Tumwater WA 98512" \
  --parcel 40380000700 --tax-id 4038-00-00700 --lot-sf 9411 \
  --lot "LOT 7, CHAPPAREL LANDING DIVISION 2"
```

Expected output:

```
[new] /Users/you/garage2afh_ai/projects/3571-cassie-drive-sw-tumwater-wa-98512/design.py
      project='3571 Cassie Drive SW, Tumwater WA 98512' city='Tumwater WA 98512' parcel=40380000700 lot_sf=9411
      next: edit META + WALLS/ROOMS, then g2a.py build 3571-cassie-drive-sw-tumwater-wa-98512
```

The slug is derived from the address; pass `--slug 3571-cassie` if you want a short one. The
folder now holds `design.py` (template with META rewritten) and `meta.json`.

The city came from the address ("everything after the first comma"). Nothing else was guessed:
`lot_sf`, `parcel` and `tax_id` are exactly the flags you passed.

---

## 2. Fill in the real numbers (the only file you edit by hand)

Open `projects/<slug>/design.py`. META is the property record; the lists below it are the model.
For 3571 the META block reads:

```python
META = {
    "project": "3571 Cassie Drive SW, Tumwater WA 98512",
    "city": "Tumwater WA 98512",
    "lot": "LOT 7, CHAPPAREL LANDING DIVISION 2 · Tax-ID 4038-00-00700",
    "parcel": "40380000700",
    "tax_id": "4038-00-00700",
    "lot_sf": 9411,            # county
    "lot_sf_survey": 9357,     # survey — deliberately different
    "coverage_pct": 37.6,
    "structure_sf_survey": 2824,
    "driveway_sf_survey": 1706,
    "ceiling": ft(10, 5),
    "existing_garage_sf": 790,
    "internal_sf": 736,
    "existing_structure_sf": 2621,
    "year_built": 2016,
    "heating": "Heat pump + gas fireplace (1)",
    "water_heater": "Gas, 기존 위치 차고 내 (전환 시 이전 필요)",
    ...
}
```

Two rules, and they are the whole discipline of this repo:

1. **Every length goes through `ft(feet, inches)`.** `ft(12, 10)` is 12'-10". Never type metres.
2. **County and survey numbers are both kept.** 9,411 vs 9,357 is not an error, it is a
   discrepancy, and it belongs on `G-06` with the value the drawings use.

The geometry that came with the template is already the 3571 conversion:

```python
WALLS = [
    {"name": "W01 남측 외벽", "p1": (0.0, 0.0), "p2": (ft(31, 4), 0.0), "t": ft(0, 6), "exterior": True},
    {"name": "W04 동측 외벽", "p1": (ft(31, 4), 0.0), "p2": (ft(31, 4), ft(26, 10)), "t": ft(0, 6), "exterior": True},
    {"name": "W05 욕실/사무실", "p1": (ft(5, 0), 0.0), "p2": (ft(5, 0), ft(12, 10)), "t": ft(0, 4), "exterior": False},
    ...
]
ROOMS = [
    {"name": "욕실", "rect": (ft(0, 3), ft(0, 3), ft(4, 9), ft(12, 7)), "kind": "bath"},
    {"name": "침실A", "rect": (ft(11, 6), ft(0, 3), ft(21, 1), ft(12, 7)), "kind": "bedroom"},
    ...
]
DOORS = [{"name": "D01 욕실", "wall": "W05 욕실/사무실", "offset": ft(9, 0), "w": ft(2, 8), "h": ft(6, 8)}, ...]
```

For a genuinely new address you replace these lists with the new plan. Everything downstream —
43 sheets, 74 checks, the takeoff — is a projection of these numbers.

---

## 3. Build the set

```bash
python3 g2a.py build 3571-cassie-drive-sw-tumwater-wa-98512
```

Expected output (abridged; every stage prints `rc=0`):

```
[sheets_v2] rc=0
   saved G-00_표지_일반주기.dxf
   saved A-01_기존평면도.dxf
   saved A-02_제안평면도.dxf
   saved A-03_면적표_일람표.dxf
   saved A-04_입면도.dxf
   saved M-01_설비개념도.dxf
[sheets_permit2] rc=0
   ...
[sheets_3571_full] rc=0
   ...
[sheets_packet] rc=0
   ...
[sheets_site] rc=0
   saved C-01_대지주차계획.dxf
[dxf_to_svg] rc=0
   svg A-01_기존평면도.svg
   ...
   svg S-03_지붕장선.svg
[audit_3571] rc=0
   checks 74/74
   materials 27 -> 자재목록.csv 자재목록.md
   report -> report_full.html
[build] done · dxf=43 svg=43
```

Two lines carry the news: `[build] done · dxf=43 svg=43` (register complete, both formats) and
`checks 74/74`.

What is now in `out/`:

- 43 `.dxf` (the CAD deliverable) and 43 `.svg` (the same sheets as browser-viewable previews)
- `checks_3571.json` — the audit, one object per check
- `자재목록.csv` / `.md` — 27 takeoff lines, quantities only
- `report_full.html` — every sheet as a gallery plus the check table

---

## 4. Read the audit like an auditor

`checks_3571.json` is a flat list; each row is `{id, cat, title, result, detail}`:

```json
{"id": "C01", "cat": "문서", "title": "도면 세트 12장 이상 존재", "result": "PASS", "detail": "생성 파이프라인 확인"}
```

The 74 checks split like this:

| Category | Checks | Examples |
|---|---|---|
| 문서 (documents) | 5 | project number, city, original architect named |
| 구조 (structure) | 5 | 4 exterior walls, header over garage door retained |
| 치수 (dimensions) | 10 | internal area within 15 % of 736 SF, 3 bedrooms, bath ≥35 SF, ceiling 10'-5" |
| 벽 (walls) | 10 | exterior 6 in, interior 4 in, no duplicate wall, ≥12 walls |
| 문 (doors) | 5 | ≥6 doors, all ≥32 in, height 6'-8", one door per bedroom |
| 창 (windows) | 5 | ≥4 windows, exactly 3 egress, glazing ≥8 % of floor |
| 소방 (fire) | 6 | smoke/CO locations, alarm interconnection |
| 이그레스 (egress) | 4 | egress per bedroom, clear opening, sill height |
| 기계 (mechanical) | 8 | every room served, HVAC room separated |
| 전기 (electrical) | 6 | panel capacity, GFCI, lighting per room |
| 배관 (plumbing) | 6 | fixture count, water heater relocation |
| 에너지 (energy) | 4 | WSEC summary present, window U-value |

Honest note before you quote the score: **46 of the 74 assert that an annotation exists** (the
sheet text is generated by the same pipeline, so the assertion is true by construction), and
**28 compute from the model**. The 28 are the ones that can catch a design error. Reporting
74/74 as if it were 74 geometric proofs is exactly the kind of claim this repo exists to avoid.

---

## 5. Break it on purpose (so you know the gate is real)

Change one exterior wall from 6 in to 8 in — `W04` in `design.py`:

```python
{"name": "W04 동측 외벽", ..., "t": ft(0, 8), "exterior": True},
```

Rebuild:

```bash
python3 g2a.py build <slug>
```

```
[audit_3571] rc=0
   checks 73/74
   materials 27 -> 자재목록.csv 자재목록.md
   report -> report_full.html
     FAIL C21 외벽 두께 6in :: 0'-6"
[build] done · dxf=43 svg=43
```

The gate fired. Note the detail text (`0'-6"`) is the *first* exterior wall's thickness, not the
failing one — the detail string in that check is a poor witness. Read the id (`C21`), find its
assertion in `src/pipeline/audit_3571.py`, and fix the model. Set it back to `ft(0, 6)` and the
score returns to 74/74. That loop — break, read the id, fix `design.py`, rebuild — is the entire
debugging workflow of this tool.

---

## 6. Validate the packet

```bash
python3 g2a.py check <slug>
```

Expected output on a clean build **before** the binder has run:

```
[validate_packet] rc=0
   [PASS] 필수 시트 존재 :: 43장 / 기대 43장
   [PASS] 사람이 채울 공란 식별 :: G-04_신청데이터: (LIC#,(건축주,(성명
   [PASS] 자동검사 74/74 :: 74/74
   [FAIL] PDF 페이지 = 시트 수 :: PDF None쪽 / 시트 43장
   [PASS] 면적표 산출값 존재 :: A-12 값 3개
   [PASS] G-03 수치(카운티) 반영 :: 9,411 / Tax-ID / Concrete
   [PASS] C-01 수치(측량) 반영 :: 9,357 SF / 37.6%

   검증 6/7 통과 · 시트 43장 · PDF None쪽

   서명 전 사람이 채워야 할 항목:
     - G-04_신청데이터: (LIC#, (건축주, (성명
[check] 6/7 passed · hard fails=1
   FAIL PDF 페이지 = 시트 수 :: PDF None쪽 / 시트 43장
```

Read that output carefully, because it teaches three things at once:

1. **The 7th check is the PDF.** `PDF None쪽` means no sheet-set PDF exists yet — bind has not run.
2. **`(성명`, `(LIC#`, `(건축주` are not failures.** They are the fields only the applicant can
   fill. The validator lists them so nothing gets submitted with a blank signature block.
3. **`G-03` / `C-01` are the anti-copy-paste gates.** They assert the county and survey numbers
   actually landed on the sheets. On a new project, edit those two assertions in
   `src/pipeline/validate_packet.py` to the new numbers — otherwise a copied project fails here
   instead of shipping with the wrong parcel.

`check` exits 1 when anything except the human-field warning fails, so it is safe in CI:

```bash
python3 g2a.py check <slug> || echo "not submittable"
```

---

## 7. Bind the package

```bash
python3 g2a.py bind <slug>
```

Without a project binder:

```
[sheets_packet] rc=0
   saved G-03_부동산정보.dxf
   saved G-04_신청데이터.dxf
   saved G-05_제출체크리스트.dxf
   saved G-06_조정로그.dxf
   saved EN-03_WSEC요약.dxf
[dxf_to_svg] rc=0
   ...
[bind] no binder found -> packet sheets + index built, master PDF not assembled
       pass one explicitly: g2a.py bind <slug> --binder <path/to/bind_master.py>
```

With the 3571 binder:

```bash
python3 g2a.py bind 3571-cassie --binder projects/3571-cassie/bind_master.py
```

The binder merges six blocks into one document, and the arithmetic is the gate:

| Block | Pages |
|---|---|
| drawing set (43 A3 sheets) | 43 |
| appendix index | 2 |
| appendix A — project inputs (A3) | 5 |
| appendix B — construction specs (letter → A3) | 15 |
| appendix C — materials and budget (letter → A3) | 4 |
| appendix D — site QA and delivery (letter → A3) | 2 |
| **total** | **71** |

Every page is normalised to A3 landscape (1191.12 × 841.92 pt): scale by `min(A3w/w, A3h/h)`,
centre, then set the page boxes — with link annotations transformed by the same matrix so index
links do not drift. The master is written to both `out/appendix/` and `out/submit/`.

After binding, the PDF gate needs the *sheet-set* PDF at `out/pdf/`, not the 71-page master.
Render it from the 43 sheets (QCAD export, or print the `report_full.html` gallery to PDF), then:

```
   [PASS] PDF 페이지 = 시트 수 :: PDF 43쪽 / 시트 43장
[check] 7/7 passed · hard fails=0
```

---

## 8. Confirm the state and hand it over

```bash
python3 g2a.py status
```

```
3571-cassie-drive-sw          dxf=43  svg=43  audit=74/74 validate=7/7 pdf=43
```

Definition of done (all nine must hold — see `MANUAL.md` §6):

- [x] 43/43 sheets, 43/43 previews
- [x] audit 74/74
- [x] validator 7/7, zero hard fails
- [x] human-field list handed to the applicant, not filled by the tool
- [x] county vs survey discrepancy on `G-06`
- [x] master PDF one page size, 71 pages, no blanks
- [x] `out/submit/` address-named
- [x] auditor (second person) read the two JSON files
- [x] no `PROJECT ADDRESS` / `00000000000` / `TBD` left anywhere

---

## 9. What it cost, in wall clock

| Step | Time |
|---|---|
| `new` + META edit | 20 min |
| property record (county + survey + G-06) | 45 min |
| geometry in `design.py` (only for a new plan) | 3–5 h |
| `build` (43 sheets + 43 SVG + 74 checks + takeoff) | **2.8 s** |
| audit fix loop (one C21 round trip) | 15 min |
| takeoff pricing + budget | 1.5 h |
| `bind` + `check` | 30 min |
| portal upload | 30 min |

The machine time is noise. The two things that actually take a day are the survey and the
geometry — which is why the SOP puts them in week one and everything else in week two.

---

## 10. Second project, faster

```bash
python3 g2a.py new "4120 Lemon Rd NE, Olympia WA 98506" --parcel 12340000600 --lot-sf 8276
```

Then:

1. replace `WALLS` / `ROOMS` / `DOORS` / `WINDOWS` with the new plan (reuse the 3571 layout if the
   garage is a similar 3-car footprint — change the dimensions, not the structure);
2. update META's county/survey pairs and the program description;
3. edit the `num_ok` / `cov_ok` assertions in `validate_packet.py` to the new numbers;
4. `build` → `check` → fix until 74/74 → `bind` → `check` until 7/7.

The second project takes about half the time of the first, and the third is when you should start
running `SOP.md`'s weekly cadence instead of one project at a time.

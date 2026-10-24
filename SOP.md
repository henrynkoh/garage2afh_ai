# SOP — the routine business pattern

One address per run. The same nine stages, the same gates, every time. A single
conversion is a project; fifty conversions is a factory, and a factory only works if
the gate that stopped you last time is the gate that stops you next time.

Two facts this SOP assumes (both measured on the 3571 Cassie Dr SW package):

- a full rebuild of the drawing set takes **2.8 s** of machine time (43 DXF, 43 SVG,
  74 checks, 27 takeoff lines) — so compute is never the bottleneck, review is;
- the audit is **74 checks in 12 categories** and the validator is **7 checks**; those
  numbers are the opportunity count for the DPMO in section 5.

---

## 1. The nine stages

| # | Stage | Input | Output (file / sheet) | Gate — pass condition | Hard fail | Owner | Typical |
|---|-------|-------|-----------------------|-----------------------|-----------|-------|---------|
| 1 | Intake | address, parcel, lot size, photos/sketches, county record | `projects/<slug>/design.py`, `meta.json`, `input/` | address + parcel + lot_sf + existing garage SF captured; no placeholder string left in META | `PROJECT ADDRESS` / `00000000000` / `lot_sf 0` still present | Operator | 20 min |
| 2 | Property record | county assessor page, plat/survey, MLS sheet | `G-03` property info, `C-01` site/parking, `G-06` coordination log | every county-vs-survey difference written on `G-06` with a chosen value | two sources disagree and nobody chose | Operator + surveyor | 45 min |
| 3 | Design model | `design.py` (WALLS, ROOMS, DOORS, WINDOWS, PIPES) | the model itself: rooms closed, walls paired, openings hosted | audit `C06` exterior walls ≥4, `C15` 3 bedrooms, `C21/C22` wall thickness, `C23` no duplicate wall, `C24` ≥12 walls | room not closed / duplicate wall / bedroom count ≠ program | Design lead | 3–5 h |
| 4 | Drawing set | design model | 43 sheets: `G-00…G-06`, `C-01`, `A-01…A-18`, `S-01…S-03`, `M-01…M-03`, `E-01…E-03`, `P-02…P-04`, `LS-01/02`, `EN-01…EN-03` (DXF + SVG) | sheet files on disk = sheet register, 1:1, no duplicate sheet number | 42 or 44 files, or two sheets claiming `A-03` | Operator (machine) + review | 5 min + 1 h review |
| 5 | MEP + life safety | design model, appliance list, fixture schedule | `M-01…M-03`, `E-01…E-03`, `P-02…P-04`, `LS-01` smoke/CO, `LS-02` egress | every room served by heat + light; egress window per bedroom; smoke/CO locations shown | room with no supply, bedroom with no egress window | Design lead | 45 min |
| 6 | Automated audit | sheets + model + design.py | `checks_3571.json`, `자재목록.csv/.md`, `report_full.html` | 74/74, or every failure named and explained in writing | any FAIL left unexplained, or score reported as 73/74 silently | Auditor (not the designer) | 20 min + fix loop |
| 7 | Takeoff + budget | audit quantities, supplier quotes | `자재목록.csv` (27 lines, quantity only), budget sheet | every line priced; total computed as Σ(qty × unit price); total ≤ declared ceiling | a total typed in by hand that no formula produces | Estimator | 1.5 h |
| 8 | Bind + index | sheet PDFs, appendix A–D | `appendix/00_appendix_index.pdf`, block PDFs, master package PDF | one page size (A3 landscape), page count = sheet count + appendix pages, 0 blank pages | 70 pages in the PDF for 71 blocks, or a letter page inside an A3 set | Operator | 30 min |
| 9 | Submit | master PDF, application form | address-named PDFs in `out/submit/`, portal receipt | validator PASS (human-field warnings allowed, everything else clean) | portal naming rule broken, or validator FAIL on sheet count / PDF pages / area numbers | Applicant (owner-builder) | 30 min |

Elapsed for one conversion: **3–5 business days**, of which ~1.5 days is human work. Machine
time is seconds; the calendar time is the jurisdiction and the survey.

### What each stage refuses to hand over

- Stage 1 refuses to hand over a project whose META still reads like the template.
- Stage 2 refuses to hide a disagreement. `9,411 SF` (county) vs `9,357 SF` (survey) is not
  a rounding problem, it is a decision — one column on `G-06` says which number the drawings use.
- Stage 4 refuses to hand over a set where the register says 43 and the folder says 42.
- Stage 6 refuses to be run by the person who drew the sheet. The auditor signs the JSON.
- Stage 7 refuses an asserted total. A number with no formula behind it is a defect class
  (see section 5), not a budget.
- Stage 8 refuses a package with more than one page size.

---

## 2. Intake checklist (what to collect before you spend a dollar)

Ask the seller/owner for all of it in one message; missing items are the cheapest defect
you will ever fix.

**Identity of the property**
- [ ] Street address exactly as the county writes it (middle initials, `Dr SW` vs `Drive SW`)
- [ ] Parcel number (10 digits in Thurston County: `40380000700`) and tax-ID form (`4038-00-00700`)
- [ ] Legal description: lot, block, plat name, recording number, section/township/range
- [ ] Lot size from the **survey**, and separately from the **county** — record both
- [ ] Zoning code from the city, and the city's own confirmation (not the survey's note)

**The building as it stands**
- [ ] Year built, stories, gross SF, ground-floor SF, existing structure SF
- [ ] Garage: SF, door type and width, ceiling height, slab condition, whether the slab is
      stepped or has a curb, and where the water heater / furnace / electrical panel sit
- [ ] Roof structure over the garage (truss vs stick, span, insulation R-value)
- [ ] Foundation type, and whether the garage slab is 4 in or thicker at the door threshold
- [ ] Heating fuel and equipment, water heater make/model/age, panel amperage and spare slots
- [ ] Sewer vs septic, water service size, and the gas meter location

**Paper**
- [ ] Deed or title showing current owner names as they will sign
- [ ] Plat map / survey (PDF, with the surveyor's stamp and phone number)
- [ ] Previous permits pulled on the property (any unpermitted work is a schedule risk)
- [ ] HOA covenants + architectural review contact (AFH use may be restricted)
- [ ] Photos: 4 exterior sides, every garage wall from inside, the panel, the water heater,
      the attic/roof structure, and the driveway approach
- [ ] Owner-builder eligibility: will the owner sign the affidavit and occupy the unit?

**Program (what the room must become)**
- [ ] Bedroom count and which one is the caregiver room
- [ ] Bathroom count and whether the tub is required (aging-in-place vs AFH licensing)
- [ ] Kitchenette yes/no, and whether a second cooking appliance is allowed by the AHJ
- [ ] Accessibility: 36 in doors, 60 in turning circle, roll-in shower, ramp/landing
- [ ] Target move-in date, which sets the whole schedule backwards

Anything you cannot get, write down as an open item on `G-06` **on day one**, not on the day
the plan reviewer asks.

---

## 3. Weekly cadence for a portfolio of addresses

A five-address week. Keep the batch shape identical every week so the DPMO in section 5 is
comparable.

| Day | Block | Work | Output per address |
|-----|-------|------|--------------------|
| Mon AM | Intake batch | all 5 addresses get `g2a.py new` + intake calls + missing-item email | `design.py`, `meta.json`, 5 open-item lists |
| Mon PM | Property record | county + survey pull for all 5, `G-06` written | `G-03`, `C-01`, discrepancy rows |
| Tue | Design models | 2 addresses in the morning, 2 in the afternoon, 1 buffer | 5 edited `design.py` |
| Wed AM | Build + audit | `g2a.py build` all 5, triage failures by class | `checks_3571.json` ×5 |
| Wed PM | MEP/life safety review | human read of M-*/E-*/P-*/LS-* against the model | signed sheet set |
| Thu AM | Takeoff + budget | price the 27-line takeoff, compare against ceiling | budget sheet ×5 |
| Thu PM | Bind + index | `g2a.py bind`, `g2a.py check` | master PDF ×5 |
| Fri AM | Submit | portal upload, receipts filed, `g2a.py status` archived | receipt ×5 |
| Fri PM | Review | DPMO, top defect class, one new control (section 5) | one control committed to this SOP |

Rules that make the cadence hold:

1. **Batch by stage, not by project.** Switching tools costs more than switching files.
2. **Never let a project skip a gate to catch the Friday batch.** A skipped gate comes back as
   a plan-review correction, which costs a week, not an hour.
3. **One address, one `design.py`.** Never copy a previous project's file and edit it in place
   without running `g2a.py check` — the copy still carries the previous parcel number.
4. **`g2a.py status` is the standup.** If the row does not show `audit=74/74 validate=7/7`, that
   project is not ready, no matter what the calendar says.

---

## 4. Roles (small team, four hats)

| Hat | Holds | Cannot do |
|---|---|---|
| Operator | CLI, sheet build, binder, portal upload | sign the audit |
| Design lead | `design.py`, MEP/life safety intent | audit their own model |
| Auditor | `checks_3571.json`, `validation.json` | edit the sheets they audit |
| Applicant (owner) | application form, affidavit, signature, fee | be replaced by a machine |

One person may wear two hats on a small job, but never the design + audit pair.

---

## 5. The five-project Six Sigma review (every five projects, 45 minutes)

Do this on Friday of a five-project week. Three questions only.

### 5.1 DPMO trend

Opportunities per project = **124 gate events** (43 sheets + 74 checks + 7 validator checks).
A defect is a gate event that failed at least once during the project, even if it was fixed
before submission — you are measuring the process, not the final PDF.

```
DPMO = defects / (projects × 124) × 1,000,000
```

Worked example, one project (3571, measured 2026-10-24 on a clean rebuild): 43/43 sheets,
74/74 checks, 6/7 validator (the PDF gate failed because the binder had not run yet)
→ 1 defect / 124 opportunities → **DPMO ≈ 8,065**.

| Batch | Projects | Defects | Opportunities | DPMO | Sigma-ish |
|---|---|---|---|---|---|
| W1 | 5 | (fill) | 620 | | |
| W2 | 5 | | 620 | | |
| W3 | 5 | | 620 | | |
| W4 | 5 | | 620 | | |

The trend matters, not the absolute number: DPMO that goes down because gates got stricter is
still down only if defects were *prevented*, not *renamed*.

### 5.2 Top defect class

Tally every defect by **class**, not by project. The five classes this pipeline actually
produces, in the order they bit us:

1. **unit/scale collision** — SF vs m, 1:100 vs 1:50, inches vs mm in one takeoff column
2. **stale artifact** — a PDF or SVG from the previous build still sitting in `out/`
3. **asserted total** — a budget or area number typed in, not computed
4. **blank page** — a sheet that was rendered but had nothing on it
5. **duplicate sheet number** — two files claiming `A-03` after a sheet was renamed

Write the ranking for the batch, then take the top class only. Fixing two half-way is how a
process stops improving.

### 5.3 One control to add

A control is a change to the *process*, not a reminder to be careful. It must be cheap,
automatic, and refuse to pass. Examples that qualify:

- add the check to `src/pipeline/validate_packet.py` so it fails the build, not the reviewer
- add a `--clean` step to the Tuesday build script if stale artifacts are the top class
- make the budget sheet read `자재목록.csv` so no total can be typed by hand

Then record it in this SOP in the same week:

```
<date> · batch W<n> · DPMO <x> · top class <name> · control added <what, where>
```

A control that is not in the repo did not happen. If the same class is the top defect two
batches in a row, the process is telling you the control was a reminder, not a control.

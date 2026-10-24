# REA + Six Sigma: how garage2AFH was reverse-engineered

## 1. REA — what was actually reverse engineered

The source artifact was a delivered package for 3571 Cassie Dr SW (Tumwater WA):
71 pages = 43 drawing sheets + 2-page index + 4 appendices, plus 74 audit checks and a
27-line material takeoff. It was produced by ad-hoc sessions, so the first job was to
decompose it rather than describe it.

**Ingredient list recovered from the artifact**

| Layer | What it really is | Reusable? |
|---|---|---|
| Inputs | 2 hand sketches, 3 record images, 1 listing page | yes — normalise to `design.py` + `input/` |
| Geometry model | walls / rooms / doors / windows / pipes as data, not drawing | yes — the single source of truth |
| Drawing generator | deterministic sheet builders (title block, plans, schedules, details) | yes |
| Code layer | sheet-level notes quoting IRC/WSEC clauses | yes, as text templates |
| Audit | 74 rule checks over the model + PDF facts | yes |
| Numbers layer | area, coverage, envelope, takeoff | yes, but each needs a declared source |
| Binding | index page, appendices, page-size normalisation | yes |
| Human gate | signature, owner-builder declaration, budget decision | no — stays human |

**The three things that broke every ad-hoc attempt**

1. **Unit collisions** — sheet frame drawn in A3 centimetres against geometry in metres;
   a site plan at 1:50 clipped a 120 ft lot. Fix: one scale constant per sheet family,
   asserted at build time.
2. **Silent stale artifacts** — the PDF was validated against the *previous* run's page
   count, so a stale PDF passed while a new sheet was missing. Fix: the build emits a
   manifest, the validator compares manifest to disk to PDF.
3. **Asserted numbers** — the budget PDF said $27,711.09 while the line items summed to
   $28,962.50. Fix: totals are computed from line items at build time; an asserted total
   is a defect, not a fact.

## 2. Six Sigma — DMAIC on the document pipeline

**Define.** Critical-to-quality characteristics (CTQs), measured per package:

| CTQ | Definition | Target |
|---|---|---|
| Sheet completeness | sheets present / sheets in register | 1.000 |
| Page uniformity | distinct page sizes in bound PDF | 1 |
| Blank page rate | blank or dark pages / total pages | 0 |
| Number integrity | figures with a declared source / figures | 1.000 |
| Audit pass rate | checks passed / checks run | ≥ 0.99 |
| Rework loops | build→fix cycles before submission | ≤ 2 |

**Measure.** Defect = any unit that fails a CTQ at the gate. In the 3571 run, measured
defects before the fixes:

| Defect class | Count | Where it was caught |
|---|---|---|
| Stale PDF vs sheet set | 3 runs | validator (page count) |
| Unit/scale collision | 2 (sheet frame, site plan) | visual render check |
| Duplicate sheet number | 1 (S-01 used twice) | sheet-register check |
| Asserted budget vs line items | 1 ($1,251.41 gap) | takeoff recomputation |
| Blank pages from HEIC conversion | 2 | brightness scan |
| Mixed page sizes in master | 26 pages | page-size set check |

**Analyse.** Every defect traced to one of three root causes:

1. *no single source of truth* (numbers typed into PDFs instead of derived)
2. *no artifact provenance* (validators inspected whatever file was on disk)
3. *no render gate* (visual defects invisible to text-only checks)

**Improve.** Four mechanisms, now built into the app:

- `manifest.json` per run: every sheet, page count, size, hash
- build-time derivation: areas from rooms, takeoff from line items, coverage from lot
- three-level gate: schema (data) → render (pixels) → bind (pages/sizes)
- explicit `HUMAN_FIELDS` list so signature/declaration gaps are visible, not hidden

**Control.** The routine: `g2a check` exits non-zero on any hard fail, so a package
cannot be "remembered as done". DPMO is tracked per run in `run_log.csv`
(defects per million document units) and reviewed every 5 projects.

## 3. DPMO model used by the app

```
units       = sheets + appendix pages
defects     = failed gate items (same definitions as the CTQ table)
DPMO        = defects / units * 1_000_000
```

Reference point from the 3571 run: **before** controls, 9 defects over 112 units
(43 sheets + 69 appendix/index pages) ≈ **80,357 DPMO**; **after** the four mechanisms,
0 hard-gate defects at submission time (the remaining open items are human-gate items:
applicant fields, owner-builder declaration, budget decision).

## 4. What is deliberately not automated

- licensed judgement (structural adequacy, energy compliance calculations)
- signatures and owner-builder declarations
- authority-having-jurisdiction decisions (what the city will accept)
- any number whose source is unknown — it is flagged, never invented

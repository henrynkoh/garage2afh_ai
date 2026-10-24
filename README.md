# garage2AFH — AI remodeling package generator

Turn one property (address + a few photos/sketches) into a complete garage-to-AFH
conversion package: 43-sheet drawing set, 74 automated checks, material takeoff,
code/coordination log, appendices, and a single bound PDF ready for the city portal.

This is a reverse-engineered, Six-Sigma-structured rebuild of the ad-hoc pipeline that
produced the 3571 Cassie Dr SW package (71 pages, Tumwater WA).

```
property inputs  ->  design model  ->  drawings + IFC + checks  ->  package + appendix  ->  submit PDFs
   (5 min)            (design.py)        (automated)                (bound, indexed)      (address-named)
```

## Why it exists

One-off AI work does not repeat. This app captures the repeatable part:

- **REA (reverse engineer anything)** — the working artifact is decomposed into its
  ingredients (inputs, transforms, gates) and rebuilt as a parameterised system.
  See `docs/rea-six-sigma.md`.
- **Six Sigma / DMAIC** — every stage has a measurable gate. DPMO is tracked on the
  document pipeline itself (pages, placeholders, mismatched numbers), not on vibes.
- **Routine business pattern** — the same 9-stage SOP is reused for every new address.
  See `SOP.md`.

## The 9-stage SOP (one address per run)

| # | Stage | Output | Gate (must pass) |
|---|---|---|---|
| 1 | Intake | `projects/<id>/design.py`, `input/` | address, parcel, lot, existing area captured |
| 2 | Property record | `G-03`, `C-01` | county + survey values reconciled or logged |
| 3 | Design model | `WALLS/ROOMS/DOORS/WINDOWS/PIPES` | all rooms closed, no duplicate walls |
| 4 | Drawing set | 43 DXF→SVG sheets | sheet count = register |
| 5 | MEP + life safety | `M/E/P/LS` sheets | every room served, egress per bedroom |
| 6 | Automated audit | `checks_<id>.json` | 74/74 (or explained fails) |
| 7 | Takeoff + budget | `자재목록.csv`, budget sheet | priced total ≤ declared ceiling |
| 8 | Bind + index | appendix A–D, master PDF | one page size, 0 blank pages |
| 9 | Submit | address-named PDFs | validator 7/7, portal naming rule |

## Quickstart (5 minutes)

```bash
# 1. clone
git clone https://github.com/henrynkoh/garage2afh_ai.git
cd garage2afh_ai

# 2. create a project from the template
python3 g2a.py new "123 Jane Doe St, Tumwater WA 98512" --parcel 40380000700 --lot-sf 9411

# 3. edit the design
$EDITOR projects/123-jane-doe-st/design.py     # walls, rooms, openings, pipes

# 4. build everything
python3 g2a.py build 123-jane-doe-st           # sheets, SVG, audit, takeoff, report
python3 g2a.py bind   123-jane-doe-st          # index + master PDF
python3 g2a.py check  123-jane-doe-st          # validator, exit 1 on hard fail
```

## What "complete" means (definition of done)

- drawing register matches the files on disk, 1:1
- every sheet is A3 landscape and none is blank
- audit score reported with every failure named, never silently waived
- every number that differs between sources is listed on a discrepancy sheet
- budget total is computed from line items, not asserted
- applicant fields that only a human can sign are flagged, not faked

## Repository layout

```
g2a.py                  CLI (new / build / bind / check / status)
src/pipeline/           sheet generators, audit, validator, binder
templates/design.py     annotated design template
docs/rea-six-sigma.md   reverse-engineering + DMAIC analysis
docs/marketing-ads.md   ads for 8 channels + email
SOP.md                  the routine business pattern
MANUAL.md               full operator manual
TUTORIAL.md             guided first project
index.html              landing page (GitHub Pages ready)
```

## Requirements

- macOS or Linux, Python 3.11+
- `ezdxf`, `pypdf`, `openpyxl` (pip)
- optional: Blender 4.x/5.x for IFC export (`--ifc`)

## Licence

MIT. Generated drawings are engineering drafts, not stamped instruments; the operator
remains responsible for code compliance in the authority having jurisdiction.

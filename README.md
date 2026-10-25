# garage2AFH — AI remodeling package generator

Turn one property (address + a few photos/sketches) into a complete garage-to-AFH
conversion package: 44-sheet drawing set, 74 automated checks, material takeoff,
code/coordination log, appendices, and a single bound PDF ready for the city portal.

This is a reverse-engineered, Six-Sigma-structured rebuild of the ad-hoc pipeline that
produced the 3571 Cassie Dr SW package (71 pages, Tumwater WA).

```
property inputs  ->  design model  ->  drawings + IFC + checks  ->  package + appendix  ->  submit PDFs
   (5 min)            (design.py)        (automated)                (bound, indexed)      (address-named)
```

## 라이브 주소

- 랜딩: https://henrynkoh.github.io/garage2afh_ai/
- 문서 전체 보기: https://henrynkoh.github.io/garage2afh_ai/package.html
- 저장소: https://github.com/henrynkoh/garage2afh_ai

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
| 1 | Intake (실측) | `intake/measurements.json`, `intake/evidence.json`, `intake/design_rooms.py` | photos + measurement video + transcribed dimensions (notes.txt/transcript.txt) parsed into room dims, every file hashed; ≥1 measurement line, every unread line named |
| 2 | Property record | `G-03`, `C-01` | county + survey values reconciled or logged |
| 3 | Design model | `WALLS/ROOMS/DOORS/WINDOWS/PIPES` | all rooms closed, no duplicate walls |
| 4 | Drawing set | 44 DXF→SVG sheets | sheet count = register |
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

# 3. (optional) start from the site: photos + measurement video + transcribed dims
#    mkdir -p projects/123-jane-doe-st/intake && cp <photos|*.mp4|transcript.txt> there
python3 g2a.py intake 123-jane-doe-st   # -> measurements.json, evidence.json, design_rooms.py

# 4. edit the design
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
g2a.py                  CLI (new / intake / build / bind / check / status)
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

## Changelog

Pipeline changes are recorded in [CHANGELOG.md](CHANGELOG.md) — newest first, with the
measured before/after numbers for every rebuild. Latest entry: the intake stage
(`g2a.py intake`, photos + measurement video + transcribed dimensions), evidence sheet G-07,
and the 43 → 44 sheet count it brings.

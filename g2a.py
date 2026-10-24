#!/usr/bin/env python3
"""garage2AFH - one property in, one submission package out.
    g2a.py new "<address>" --parcel P --lot-sf N   scaffold projects/<slug>/design.py
    g2a.py build <slug> [--clean]                  sheets + SVG + audit + takeoff
    g2a.py bind  <slug> [--binder PATH]            packet + index + master PDF
    g2a.py check <slug>                            validator; exit 1 on hard fail
    g2a.py status [slug]                           state of one or all projects
This CLI imports nothing from the pipeline: each stage runs as its own child process with
HOUSEBIM_DESIGN_DIR and HOUSEBIM_OUT exported (the original HouseBIM contract), so a broken
stage cannot corrupt the next one and one bad project cannot touch another.
"""
import argparse, glob, json, os, re, subprocess, sys
REPO = os.path.dirname(os.path.abspath(__file__))
PIPE, TOOLS = os.path.join(REPO, "src", "pipeline"), os.path.join(REPO, "src", "tools")
TPL, PROJECTS = os.path.join(REPO, "templates", "design.py"), os.path.join(REPO, "projects")
SHEETS = ["sheets_v2.py", "sheets_permit2.py", "sheets_3571_full.py", "sheets_packet.py", "sheets_site.py"]
HUMAN = "사람이 채울 공란 식별"
def py(): return os.environ.get("G2A_PYTHON") or sys.executable  # interpreter that can import ezdxf + numpy
def env_for(d):
    out = os.path.join(d, "out"); os.makedirs(out, exist_ok=True)
    e = dict(os.environ); e["HOUSEBIM_DESIGN_DIR"], e["HOUSEBIM_OUT"] = d, out
    e.setdefault("HOUSEBIM_PYDEPS", os.path.join(REPO, "pydeps"))
    e["PYTHONPATH"] = e["HOUSEBIM_PYDEPS"]  # isolated on purpose: never inherit a foreign PYTHONPATH
    e.pop("PYTHONHOME", None); e.pop("VIRTUAL_ENV", None)  # child interpreter must use its own stdlib
    return e, out
def stage(script, d, args=(), tools=False):
    cmd = [py(), os.path.join(TOOLS if tools else PIPE, script), *args]
    r = subprocess.run(cmd, env=env_for(d)[0], capture_output=True, text=True)
    print(f"[{script[:-3]}] rc={r.returncode}")
    for line in (r.stdout + r.stderr).strip().splitlines()[-40:]:
        print("   " + line)
    return r.returncode
def resolve(name):
    d = name if os.path.isdir(name) else os.path.join(PROJECTS, name)  # slug or explicit path
    if not os.path.isfile(os.path.join(d, "design.py")):
        sys.exit(f"no project at {d} - run: g2a.py new \"<address>\" --parcel P --lot-sf N")
    return d
def cmd_new(a):
    slug = a.slug or re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", a.address.lower())).strip("-")[:60]
    d = os.path.join(PROJECTS, slug); p = os.path.join(d, "design.py")  # slug: 123-jane-doe-st-...
    if os.path.exists(p) and not a.force:
        sys.exit(f"{p} exists; pass --force to overwrite")
    os.makedirs(d, exist_ok=True)
    city = a.city or (a.address.split(",", 1)[1].strip() if "," in a.address else "CITY, ST ZIP")
    t = open(TPL, encoding="utf-8").read()
    for k, v in [("project", a.address), ("city", city), ("parcel", a.parcel), ("tax_id", a.tax_id or a.parcel),
                 ("lot", a.lot or "LOT 0, SUBDIVISION NAME"), ("lot_sf", a.lot_sf)]:
        t = re.sub(r'"%s": .*' % k, '"%s": %s,' % (k, json.dumps(v, ensure_ascii=False)), t, count=1)
    open(p, "w", encoding="utf-8").write(t)
    json.dump({"slug": slug, "project": a.address, "city": city, "parcel": a.parcel, "lot": a.lot or "",
               "lot_sf": a.lot_sf}, open(os.path.join(d, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[new] {p}\n      project={a.address!r} city={city!r} parcel={a.parcel} lot_sf={a.lot_sf}"
          f"\n      next: edit META + WALLS/ROOMS, then g2a.py build {slug}")
def cmd_build(a):
    d = resolve(a.slug); out, rc = env_for(d)[1], 0
    if a.clean:
        for f in glob.glob(os.path.join(out, "*.dxf")) + glob.glob(os.path.join(out, "*.svg")) \
                + glob.glob(os.path.join(out, "pdf", "*.pdf")):
            os.remove(f)
        print("[clean] removed stale dxf/svg/pdf")
    for s in SHEETS:
        rc |= stage(s, d)
    rc |= stage("dxf_to_svg.py", d, [out], tools=True) | stage("audit_3571.py", d)
    print("[build] done · dxf=%d svg=%d" % (len(glob.glob(os.path.join(out, "*.dxf"))),
                                            len(glob.glob(os.path.join(out, "*.svg")))))
    return rc
def cmd_bind(a):
    d = resolve(a.slug); out, rc = env_for(d)[1], 0
    rc |= stage("sheets_packet.py", d) | stage("dxf_to_svg.py", d, [out], tools=True)
    cand = (os.path.join(d, "bind_master.py"), os.path.join(out, "appendix", "bind_master.py"))
    binder = a.binder or os.environ.get("HOUSEBIM_BIND") or next((q for q in cand if os.path.exists(q)), None)
    if not binder:
        print("[bind] no binder found -> packet sheets + index built, master PDF not assembled"
              f"\n       pass one explicitly: g2a.py bind {a.slug} --binder <path/to/bind_master.py>")
        return rc
    r = subprocess.run([py(), binder], env=env_for(d)[0], capture_output=True, text=True)
    print(f"[bind_master] rc={r.returncode}")
    for line in (r.stdout + r.stderr).strip().splitlines()[-40:]:
        print("   " + line)
    return rc | r.returncode
def cmd_check(a):
    d = resolve(a.slug); out = env_for(d)[1]
    stage("validate_packet.py", d)
    if not os.path.exists(p := os.path.join(out, "validation.json")):  # written every run
        print("[check] HARD FAIL: validation.json missing")
        return 1
    v = json.load(open(p, encoding="utf-8"))
    hard = [r for r in v["results"] if r["result"] != "PASS" and r["check"] != HUMAN]
    print(f"[check] {v['passed']}/{v['total']} passed · hard fails={len(hard)}")
    for r in hard:
        print(f"   FAIL {r['check']} :: {r['detail']}")
    return 1 if hard else 0
def cmd_status(a):
    found = glob.glob(os.path.join(PROJECTS, "*", "design.py"))
    slugs = [a.slug] if a.slug else sorted(os.path.basename(os.path.dirname(f)) for f in found)
    for s in slugs:
        out, ln = env_for(resolve(s))[1], None
        ld = lambda n: json.load(open(os.path.join(out, n), encoding="utf-8")) if os.path.exists(os.path.join(out, n)) else {}
        chk, val = ld("checks_3571.json"), ld("validation.json")
        nx, ns = len(glob.glob(os.path.join(out, "*.dxf"))), len(glob.glob(os.path.join(out, "*.svg")))
        print(f"{s:<30} dxf={nx:<3} svg={ns:<3} "
              f"audit={chk.get('passed', '-')}/{chk.get('total', '-')} "
              f"validate={val.get('passed', '-')}/{val.get('total', '-')} pdf={val.get('pdf_pages', '-')}")
    return 0
if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="g2a", description="garage2AFH package generator")
    sp = ap.add_subparsers(dest="cmd", required=True)  # new | build | bind | check | status
    n = sp.add_parser("new", help="scaffold projects/<slug>/design.py")
    n.add_argument("address"); n.add_argument("--parcel", required=True); n.add_argument("--lot-sf", type=int, default=0)
    n.add_argument("--lot"); n.add_argument("--tax-id"); n.add_argument("--city"); n.add_argument("--slug")
    n.add_argument("--force", action="store_true", help="overwrite an existing project")
    for name, h in (("build", "sheets, SVG, audit, takeoff"), ("bind", "packet + index + PDF"),
                    ("check", "validate; exit 1 on hard fail")):
        sp.add_parser(name, help=h).add_argument("slug")
    sp.choices["build"].add_argument("--clean", action="store_true", help="delete stale dxf/svg/pdf first")
    sp.choices["bind"].add_argument("--binder", help="path to the project bind_master.py")
    sp.add_parser("status", help="state of one or all projects").add_argument("slug", nargs="?")
    a = ap.parse_args()
    sys.exit({"new": cmd_new, "build": cmd_build, "bind": cmd_bind, "check": cmd_check, "status": cmd_status}[a.cmd](a) or 0)

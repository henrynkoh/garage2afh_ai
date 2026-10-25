#!/usr/bin/env python3
"""garage2AFH - one property in, one submission package out.
    g2a.py new "<address>" --parcel P --lot-sf N   scaffold projects/<slug>/design.py
    g2a.py intake <slug>                           parse intake/ (photos+video+transcript) -> measurements.json
    g2a.py build <slug> [--clean]                  sheets + SVG + audit + takeoff
    g2a.py bind  <slug> [--binder PATH]            packet + index + master PDF
    g2a.py check <slug>                            validator; exit 1 on hard fail
    g2a.py status [slug]                           state of one or all projects
    g2a.py publish-index [--extra PATH]            projects.json + README count + index.html count + upload plan
This CLI imports nothing from the pipeline: each stage runs as its own child process with
HOUSEBIM_DESIGN_DIR and HOUSEBIM_OUT exported (the original HouseBIM contract), so a broken
stage cannot corrupt the next one and one bad project cannot touch another.
"""
import argparse, glob, json, os, re, subprocess, sys, time
REPO = os.path.dirname(os.path.abspath(__file__))
PIPE, TOOLS = os.path.join(REPO, "src", "pipeline"), os.path.join(REPO, "src", "tools")
TPL, PROJECTS = os.path.join(REPO, "templates", "design.py"), os.path.join(REPO, "projects")
SHEETS = ["sheets_v2.py", "sheets_permit2.py", "sheets_3571_full.py", "sheets_packet.py", "sheets_site.py",
          "sheets_carport.py"]
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
def project_dir(name):
    """intake 는 design.py 없이도 돌아야 한다 (실측만 먼저 들어오는 경우)."""
    d = name if os.path.isdir(name) else os.path.join(PROJECTS, name)
    if not os.path.isdir(d):
        sys.exit(f"no project folder at {d} - run: g2a.py new \"<address>\" --parcel P --lot-sf N")
    return d
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
def cmd_intake(a):
    d = project_dir(a.slug)
    print(f"[intake] {os.path.join(d, 'intake')}")
    return stage("intake.py", d)   # rc=1 when not a single measurement line parsed
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
    rc |= stage("text_bbox.py", d, [out, "--assert", "--quiet"], tools=True)  # 틀 밖으로 나간 텍스트 = 하드 실패
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
# ---------------------------------------------------------------- publish-index
# The gallery (projects.html) never builds: it fetches projects.json at runtime.
# publish-index is the only thing that writes that file, so a new project appears on
# the gallery after "publish-index + PDF upload", never by hand-editing HTML.
GALLERY_ROOT = "docs/projects"                    # where the master PDFs live on the site
GALLERY_BUTTON = "전체 프로젝트 보기"


def _load_design(d):
    """design.py 를 그대로 실행해 META/ROOMS 를 얻는다 (ast 로는 ft() 호출을 못 읽는다)."""
    g = {"__name__": "design", "__file__": os.path.join(d, "design.py")}
    with open(os.path.join(d, "design.py"), encoding="utf-8") as f:
        exec(compile(f.read(), g["__file__"], "exec"), g)
    return g.get("META", {}), g.get("ROOMS", [])


def _pdf_pages(path):
    """페이지 수: pypdf 있으면 정확히, 없으면 /Type /Page 객체를 센다."""
    try:
        from pypdf import PdfReader
        return len(PdfReader(path).pages)
    except Exception:
        raw = open(path, "rb").read()
        return raw.count(b"/Type /Page") - raw.count(b"/Type /Pages")


def _master_pdf(d):
    """out/submit 의 마스터(PDF 하나로 묶은包)를 고른다: 이름 우선, 없으면 가장 큰 PDF."""
    sub = os.path.join(d, "out", "submit")
    cand = sorted(glob.glob(os.path.join(sub, "*Master Package*.pdf")))
    if not cand:
        cand = sorted(glob.glob(os.path.join(sub, "*.pdf")), key=os.path.getsize, reverse=True)
    if not cand:
        cand = sorted(glob.glob(os.path.join(d, "out", "pdf", "*.pdf")))
    return cand[0] if cand else None


def _garage_type(meta):
    st = (meta.get("structure_type") or "").lower()
    if meta.get("carport_enclosure") or "carport" in st:
        return "carport", meta.get("carport_sf") or 0
    if "detached" in st:
        return "detached", meta.get("existing_garage_sf") or 0
    return "attached", meta.get("existing_garage_sf") or 0


def _zoning(z):
    """조닝 코드만 남긴다. 미확인 표기는 한 가지로 통일한다."""
    z = re.split(r" \(|\s-\s", str(z or ""))[0].strip()
    return z if z and z.upper() not in ("UNKNOWN", "N/A", "NONE") else "미확인"


def _program(meta, beds):
    if meta.get("carport_enclosure"):
        return "카포트 외벽화"
    return "%d침실" % beds if beds else "미확인"


def _branch_note(meta, gtype, gsf, beds, alt):
    if meta.get("carport_enclosure"):
        return "카포트 외벽화 분기 (S-04 / A-19 가 A-18 을 대체)" + alt
    if meta.get("branch"):
        return meta["branch"] + alt
    if gtype == "detached":
        return "%d침실 프로그램 · detached %s SF 차고%s" % (beds, gsf, alt)
    return "%d침실 프로그램 · attached %s SF 차고%s" % (beds, gsf, alt)


def _gallery_entry(d):
    """프로젝트 하나 -> (entry, missing[])"""
    slug = os.path.basename(os.path.normpath(d))
    meta, rooms, missing, warns = {}, [], [], []
    if os.path.exists(os.path.join(d, "design.py")):
        try:
            meta, rooms = _load_design(d)
        except Exception as e:
            missing.append("design.py 실행 실패: %s" % e)
    else:
        missing.append("design.py 없음")
    mj = os.path.join(d, "meta.json")
    if os.path.exists(mj):                       # meta.json 은 부분 사본: META 가 이긴다
        try:
            for k, v in json.load(open(mj, encoding="utf-8")).items():
                meta.setdefault(k, v)
        except Exception:
            warns.append("meta.json 파싱 실패")
    out = os.path.join(d, "out")
    val, chk = {}, {}
    if os.path.exists(vp := os.path.join(out, "validation.json")):
        val = json.load(open(vp, encoding="utf-8"))
    else:
        missing.append("out/validation.json 없음 (시트 수 미검증)")
    if os.path.exists(cp := os.path.join(out, "checks_3571.json")):
        chk = json.load(open(cp, encoding="utf-8"))
    pdf = _master_pdf(d)
    if not pdf:
        missing.append("out/submit 마스터 PDF 없음")
    pages = _pdf_pages(pdf) if pdf else (val.get("pdf_pages") or 0)
    if pdf and val and pages < (val.get("pdf_pages") or 0):   # fewer pages than the drawing set = real defect
        warns.append("마스터 PDF %d쪽 < 도면집 %s쪽 (바인딩 누락)" % (pages, val.get("pdf_pages")))
    beds = len([r for r in rooms if r.get("kind") == "bedroom"])
    gtype, gsf = _garage_type(meta)
    built = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(pdf))) if pdf else time.strftime("%Y-%m-%d")
    alt = ""
    m = re.search(r"\((\d{4})[^)]*\)", meta.get("structure_type") or "")
    if m and str(m.group(1)) != str(meta.get("year_built")):
        alt = " · 차고 %s년" % m.group(1)
    e = {
        "slug": slug,
        "address": re.sub(r",\s*[^,]*\bWA\b.*$", "", meta.get("project") or meta.get("address") or slug).strip(),
        "city": meta.get("city", ""),
        "jurisdiction": meta.get("jurisdiction") or ("City of " + str(meta.get("city", "")).split(",")[0]
                                                    if meta.get("city") else "미확인"),
        "zoning": _zoning(meta.get("zoning")),
        "parcel": meta.get("parcel", ""),
        "year_built": meta.get("year_built") or 0,
        "garage_type": gtype,
        "garage_sf": gsf,
        "program": _program(meta, beds),
        "sheets": val.get("sheets") or meta.get("sheets") or 0,
        "pages": pages or meta.get("master_pages") or 0,
        "audit": "%s/%s" % (chk.get("passed", "-"), chk.get("total", "-")) if chk else "",
        "branch_note": _branch_note(meta, gtype, gsf, beds, alt),
        "pdf": "%s/%s/%s" % (GALLERY_ROOT, slug, os.path.basename(pdf)) if pdf else "",
        "built": built,
    }
    for k in ("city", "sheets", "pages", "parcel", "year_built"):
        if not e[k]:
            missing.append("%s 값 없음" % k)
    if not e["audit"] or e["audit"].startswith("-"):
        missing.append("자동검사 결과 없음 (out/checks_3571.json)")
    return e, missing + ["[warn] " + w for w in warns]


def cmd_publish_index(a):
    dirs = sorted(d for d in glob.glob(os.path.join(PROJECTS, "*"))
                  if os.path.isdir(d) and os.path.exists(os.path.join(d, "design.py")))
    extras = []
    for x in a.extra or []:
        if os.path.isdir(x) and os.path.exists(os.path.join(x, "design.py")):
            extras.append(x)
        else:
            print("[publish-index] --extra %r 는 design.py 가 있는 폴더가 아님" % x)
    rows, missing_map = [], {}
    for d in dirs + extras:
        e, miss = _gallery_entry(d)
        if not e["pdf"] and not e["sheets"]:
            print("[publish-index] skip %s (빌드 산출물 없음)" % e["slug"])
            continue
        pv = _master_pdf(d)
        e["_ts"] = os.path.getmtime(pv) if pv else 0
        e["_src"] = pv or ""
        rows.append(e)
        if miss:
            missing_map[e["slug"]] = miss
    rows.sort(key=lambda r: (r["built"], r["_ts"]), reverse=True)     # newest build first
    for r in rows:
        r.pop("_ts", None)
        r.pop("_src", None)
    gp = os.path.join(REPO, "projects.json")
    with open(gp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("[publish-index] projects.json  %d projects" % len(rows))
    print("  %-24s %-14s %-7s %-6s %-8s %-11s %s" % ("slug", "program", "sheets", "pages", "audit", "built", "pdf"))
    for r in rows:
        print("  %-24s %-14s %-7s %-6s %-8s %-11s %s"
              % (r["slug"], r["program"], r["sheets"], r["pages"], r["audit"], r["built"],
                 os.path.basename(r["pdf"]) if r["pdf"] else "PDF 미업로드"))
    tot_s = sum(r["sheets"] for r in rows)
    tot_p = sum(r["pages"] for r in rows)
    print("  %-24s %-14s %-7s %-6s" % ("TOTAL", "%d projects" % len(rows), tot_s, tot_p))
    if missing_map:
        print("\n[publish-index] missing / warnings")
        for s, ms in sorted(missing_map.items()):
            for m in ms:
                print("  %-24s %s" % (s, m))
    else:
        print("\n[publish-index] missing: 없음 (모든 프로젝트 완비)")

    rp = os.path.join(REPO, "README.md")
    if os.path.exists(rp):
        txt = open(rp, encoding="utf-8").read()
        line = "▶ **[%s (%d개) — 완성된 패키지 모음](https://henrynkoh.github.io/garage2afh_ai/projects.html)**" % (GALLERY_BUTTON, len(rows))
        new, n = re.subn(r"^▶ \*\*\[" + GALLERY_BUTTON + r" \(\d+개\).*$", lambda _: line, txt, flags=re.M)
        if n == 0 and "## 라이브 주소" in new:      # first run: land it just above "## Why it exists"
            i, j = new.index("## 라이브 주소"), new.find("\n## ", new.index("## 라이브 주소") + 1)
            j = len(new) if j < 0 else j
            new = new[:j].rstrip("\n") + "\n\n" + line + "\n" + new[j:]
            n = 1
        if n:
            open(rp, "w", encoding="utf-8").write(new)
        print("[publish-index] README button  %s" % ("count = %d" % len(rows) if n else "line not found"))

    ip = os.path.join(REPO, "index.html")          # static fallback for the landing-page button
    if os.path.exists(ip):
        txt = open(ip, encoding="utf-8").read()
        new, n = re.subn(r"(<span data-count>\()\d+",
                         lambda m: "%s%d" % (m.group(1), len(rows)), txt)
        if n:
            open(ip, "w", encoding="utf-8").write(new)
        print("[publish-index] index.html button  %s" % ("count = %d" % len(rows) if n else "data-count span not found"))

    plan = os.path.join(REPO, GALLERY_ROOT, "UPLOAD-PLAN.md")
    os.makedirs(os.path.dirname(plan), exist_ok=True)
    L = ["# 마스터 PDF 업로드 계획", "",
         "`python3 g2a.py publish-index` 가 만든 목록입니다. 손으로 고치지 마세요.",
         "GitHub 웹 UI: **Add file → Upload files**, 폴더마다 한 번씩 올립니다.", "",
         "| # | slug | 올릴 파일 (repo 경로) | 원본 | 크기 | 쪽 |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        root = next((x for x in dirs + extras
                     if os.path.basename(os.path.normpath(x)) == r["slug"]), None)
        src = _master_pdf(root) if root else ""
        size = "%.1f MB" % (os.path.getsize(src) / 1048576.0) if src else "-"
        src = os.path.relpath(src, root) if src else "(없음)"
        L.append("| %d | %s | `%s` | `%s` | %s | %s |"
                 % (i, r["slug"], r["pdf"] or "(없음)", src or "(없음)", size, r["pages"]))
    L += ["", "합계: %d 프로젝트 · %d장 · %d쪽 · %s ~ %s"
          % (len(rows), tot_s, tot_p, rows[-1]["built"] if rows else "-", rows[0]["built"] if rows else "-"), ""]
    if missing_map:
        L += ["## 빠진 것", ""]
        for s, ms in sorted(missing_map.items()):
            L += ["- **%s**" % s] + ["  - " + m for m in ms]
        L += [""]
    else:
        L += ["## 빠진 것", "", "없음.", ""]
    L += ["업로드 뒤 확인:", "", "```",
          "curl -sI <raw pdf url> | head -1     # 200",
          "```", ""]
    with open(plan, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("[publish-index] upload plan  %s" % os.path.relpath(plan, REPO))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="g2a", description="garage2AFH package generator")
    sp = ap.add_subparsers(dest="cmd", required=True)  # new | build | bind | check | status
    n = sp.add_parser("new", help="scaffold projects/<slug>/design.py")
    n.add_argument("address"); n.add_argument("--parcel", required=True); n.add_argument("--lot-sf", type=int, default=0)
    n.add_argument("--lot"); n.add_argument("--tax-id"); n.add_argument("--city"); n.add_argument("--slug")
    n.add_argument("--force", action="store_true", help="overwrite an existing project")
    for name, h in (("intake", "parse intake/ measurements + evidence"),
                    ("build", "sheets, SVG, audit, takeoff"), ("bind", "packet + index + PDF"),
                    ("check", "validate; exit 1 on hard fail")):
        sp.add_parser(name, help=h).add_argument("slug")
    sp.choices["build"].add_argument("--clean", action="store_true", help="delete stale dxf/svg/pdf first")
    sp.choices["bind"].add_argument("--binder", help="path to the project bind_master.py")
    sp.add_parser("status", help="state of one or all projects").add_argument("slug", nargs="?")
    pi = sp.add_parser("publish-index", help="rewrite projects.json + README/index.html counts + upload plan")
    pi.add_argument("--extra", action="append", metavar="PATH",
                    help="project folder outside projects/ (repeatable), e.g. ../HouseBIM/projects/3571-cassie")
    a = ap.parse_args()
    sys.exit({"new": cmd_new, "intake": cmd_intake, "build": cmd_build, "bind": cmd_bind,
              "check": cmd_check, "status": cmd_status, "publish-index": cmd_publish_index}[a.cmd](a) or 0)

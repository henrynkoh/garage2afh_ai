"""
PDF 세트 검증: 페이지 수 · 페이지 크기 종류 · 빈/검은 페이지 (18 dpi 픽셀 측정).

A3 가로 = 1191.12 x 841.92 pt. 빈 페이지 = 픽셀 표준편차 < 1.0, 검은 페이지 = 평균 < 5.

사용:
  python3 src/tools/pdf_check.py <pdf 폴더>
"""

import io
import os
import re
import subprocess
import sys
import tempfile

PDFINFO = "/Users/henryoh/.aside/runtime/bin/pdfinfo"
PDFTOPPM = "/Users/henryoh/.aside/runtime/bin/pdftoppm"
TARGET = (1191.12, 841.92)
DPI = 18


def pgm_pixels(raw):
    fields, i = [], 0
    while len(fields) < 4 and i < len(raw):
        if raw[i:i + 1].isspace():
            i += 1
            continue
        j = i
        while j < len(raw) and not raw[j:j + 1].isspace():
            j += 1
        fields.append(raw[i:j])
        i = j
    w, h = int(fields[1]), int(fields[2])
    i += 1
    return raw[i:i + w * h]


def info(path):
    out = subprocess.run([PDFINFO, "-f", "1", "-l", "999", path],
                         capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    pages = int(m.group(1)) if m else 0
    sizes = re.findall(r"Page\s+\d+ size:\s+([\d.]+) x ([\d.]+) pts", out)
    return pages, sizes


def scan(path):
    tmp = tempfile.mkdtemp()
    subprocess.run([PDFTOPPM, "-r", str(DPI), "-gray", path, os.path.join(tmp, "p")],
                   capture_output=True)
    rows = []
    for name in sorted(os.listdir(tmp)):
        px = pgm_pixels(io.open(os.path.join(tmp, name), "rb").read())
        n = len(px) or 1
        mean = sum(px) / n
        var = sum((v - mean) ** 2 for v in px) / n
        rows.append((mean, var ** 0.5))
    return rows


def check(path):
    pages, sizes = info(path)
    uniq = sorted({(round(float(w), 2), round(float(h), 2)) for w, h in sizes})
    off = [i for i, (w, h) in enumerate(sizes, 1)
           if abs(float(w) - TARGET[0]) > 0.01 or abs(float(h) - TARGET[1]) > 0.01]
    rows = scan(path)
    blank = [i for i, (_m, sd) in enumerate(rows, 1) if sd < 1.0]
    dark = [i for i, (m, _sd) in enumerate(rows, 1) if m < 5]
    return {"file": os.path.basename(path), "pages": pages, "sizes": uniq, "off_a3": off,
            "blank": blank, "dark": dark,
            "min_mean": min((r[0] for r in rows), default=0.0)}


if __name__ == "__main__":
    folder = sys.argv[1]
    bad = 0
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".pdf"):
            continue
        r = check(os.path.join(folder, name))
        ok = (not r["off_a3"]) and (not r["blank"]) and (not r["dark"]) and len(r["sizes"]) == 1
        bad += 0 if ok else 1
        print("%-56s pages %2d · size %s · off-A3 %s · blank %s · dark %s · min-mean %.1f %s"
              % (r["file"], r["pages"], r["sizes"], r["off_a3"] or "none",
                 r["blank"] or "none", r["dark"] or "none", r["min_mean"], "ok" if ok else "CHECK"))
    print("ALL OK" if not bad else "ISSUES %d" % bad)
    sys.exit(0 if not bad else 1)

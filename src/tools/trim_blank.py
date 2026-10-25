"""
렌더된 PDF 에서 완전히 빈 페이지를 제거한다 (픽셀 검증).

Chromium 인쇄는 마지막 page-break 컨테이너 뒤에 빈 페이지 1장을 더 만든다.
빈 페이지 = 18 dpi 렌더 픽셀이 균일(std < 1.0). 그 외 페이지는 손대지 않는다.

사용:
  python3 src/tools/trim_blank.py <pdf> <기대 페이지 수> [--dry]
"""

import io
import os
import re
import subprocess
import sys
import tempfile

from pypdf import PdfReader, PdfWriter

PDFINFO = "/Users/henryoh/.aside/runtime/bin/pdfinfo"
PDFTOPPM = "/Users/henryoh/.aside/runtime/bin/pdftoppm"
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
    _magic, w, h, mx = fields[0], int(fields[1]), int(fields[2]), int(fields[3])
    i += 1
    return raw[i:i + w * h]


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


def trim(path, expect, dry=False):
    rows = scan(path)
    blank = [i for i, (_m, sd) in enumerate(rows, 1) if sd < 1.0]
    rdr = PdfReader(path)
    w = PdfWriter()
    for i, p in enumerate(rdr.pages):
        if (i + 1) in blank:
            continue
        w.add_page(p)
    kept = len(w.pages)
    print("%-58s %2d -> %2d (want %2d) %-8s dropped=%s"
          % (os.path.basename(path), len(rows), kept, expect,
             "ok" if kept == expect else "MISMATCH", blank or "none"))
    if not dry and blank and kept == expect:
        tmp = path + ".tmp"
        with open(tmp, "wb") as fh:
            w.write(fh)
        os.replace(tmp, path)
    return kept == expect


if __name__ == "__main__":
    p = sys.argv[1]
    want = int(sys.argv[2])
    sys.exit(0 if trim(p, want, "--dry" in sys.argv) else 1)

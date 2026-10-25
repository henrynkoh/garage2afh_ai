"""
시트 SVG → A3 가로 인쇄용 HTML (프로젝트 공통).

out/ 의 SVG(시트)를 시트 코드 순서로 한 페이지씩 배치한 HTML 을 만든다.
Playwright 로 A3 landscape PDF 로 인쇄하는 용도 (한 파일 = 새 탭 1개).

사용:
  python3 src/tools/sheets_to_a3_html.py <out 폴더> <출력 html> [제목]
"""

import base64
import glob
import io
import os
import sys

ORDER = ["G", "C", "A", "S", "M", "E", "P", "LS", "EN"]

CSS = """
@page { size: A3 landscape; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
.page { width: 419mm; height: 296mm; page-break-after: always; overflow: hidden;
        display: flex; align-items: center; justify-content: center; background: #fff; }
.page:last-child { page-break-after: avoid; }
.page img { width: 100%; height: 100%; object-fit: contain; }
"""


def sheet_key(path):
    name = os.path.basename(path)[:-4]
    code = name.split("_")[0]
    pre = "LS" if code.startswith("LS") else code.split("-")[0]
    return (ORDER.index(pre) if pre in ORDER else 99, name)


def sheets(folder):
    files = [p for p in glob.glob(os.path.join(folder, "*.svg")) if "preview_plan" not in p]
    return sorted(files, key=sheet_key)


def img_tag(path):
    b64 = base64.b64encode(io.open(path, "rb").read()).decode()
    return '<img src="data:image/svg+xml;base64,%s">' % b64


def build(folder, out_html, title):
    files = sheets(folder)
    body = "".join("<div class='page'>%s</div>" % img_tag(f) for f in files)
    html = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>%s</title>'
            '<style>%s</style></head><body>%s</body></html>' % (title, CSS, body))
    io.open(out_html, "w", encoding="utf-8").write(html)
    return files


if __name__ == "__main__":
    folder = sys.argv[1]
    out_html = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "pdf", "plans.html")
    title = sys.argv[3] if len(sys.argv) > 3 else "drawing set"
    made = build(folder, out_html, title)
    print("sheets %d -> %s" % (len(made), out_html))

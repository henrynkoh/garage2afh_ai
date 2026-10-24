"""
DXF → SVG 변환기 (도면 미리보기용, 표준 라이브러리 + ezdxf만 사용).

CAD 없이 브라우저에서 도면을 확인하거나, 인쇄해서 PDF로 저장할 수 있게 만든다.

사용:
  PYTHONPATH=<pydeps> python3 tools/dxf_to_svg.py <dxf 폴더>
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYDEPS = os.environ.get("HOUSEBIM_PYDEPS") or os.path.join(ROOT, "pydeps")
if os.path.isdir(PYDEPS) and PYDEPS not in sys.path:
    sys.path.append(PYDEPS)

import ezdxf

LAYER_COLOR = {
    "WALL-EXT": "#111827",
    "WALL-INT": "#374151",
    "WALL-EXIST": "#6b7280",
    "DOOR": "#2563eb",
    "WINDOW": "#0891b2",
    "ROOM": "#9ca3af",
    "TEXT": "#111827",
    "TITLE": "#111827",
    "DIM": "#b91c1c",
    "NOTE": "#7c3aed",
    "PIPE-W": "#2563eb",
    "PIPE-D": "#be185d",
}


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def convert(dxf_path, svg_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    xs, ys = [], []
    shapes = []
    texts = []
    for e in msp:
        t = e.dxftype()
        layer = e.dxf.layer if e.dxf.hasattr("layer") else "0"
        color = LAYER_COLOR.get(layer, "#111827")
        if t == "LWPOLYLINE":
            pts = [(p[0], p[1]) for p in e.get_points()]
            if e.closed:
                pts = pts + [pts[0]]
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts]
            d = " ".join(f"{'M' if i == 0 else 'L'}{x:.3f},{y:.3f}" for i, (x, y) in enumerate(pts))
            w = 0.05 if layer.startswith("WALL") else 0.02
            shapes.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}"/>')
        elif t == "LINE":
            s, en = e.dxf.start, e.dxf.end
            xs += [s.x, en.x]
            ys += [s.y, en.y]
            shapes.append(
                f'<line x1="{s.x:.3f}" y1="{s.y:.3f}" x2="{en.x:.3f}" y2="{en.y:.3f}" '
                f'stroke="{color}" stroke-width="0.02"/>'
            )
        elif t in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            h = getattr(e.dxf, "height", 0.25) or 0.25
            txt = e.dxf.text if t == "TEXT" else e.text
            xs.append(p.x)
            ys.append(p.y)
            texts.append(
                f'<text x="{p.x:.3f}" y="{-p.y:.3f}" font-size="{h * 1.35:.3f}" '
                f'font-family="Helvetica, Arial, sans-serif" fill="{color}">{esc(txt)}</text>'
            )

    if not xs:
        return None
    x0, x1 = min(xs) - 1, max(xs) + 1
    y0, y1 = min(ys) - 1, max(ys) + 1
    w, hgt = x1 - x0, y1 - y0
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {-y1:.2f} {w:.2f} {hgt:.2f}" '
        f'width="{int(w * 20)}" height="{int(hgt * 20)}">'
        f'<rect x="{x0:.2f}" y="{-y1:.2f}" width="{w:.2f}" height="{hgt:.2f}" fill="#ffffff"/>'
        f'<g transform="scale(1,-1)">'
        + "".join(shapes)
        + "</g>"
        + "".join(texts)
        + "</svg>"
    )
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return svg_path


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "projects", "3571-cassie", "out")
    made = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(".dxf"):
            out = os.path.join(folder, os.path.splitext(name)[0] + ".svg")
            if convert(os.path.join(folder, name), out):
                made.append(os.path.basename(out))
    for m in made:
        print("svg", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())

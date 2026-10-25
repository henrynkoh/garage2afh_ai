"""
TEXT bbox 감사 (측정으로 확인, 눈으로 확인하지 않음).

A3 틀은 0..21.0 x 0..14.85 m (모델공간 실척, 1:50). 표제란은 x=10.4, 폭 9.2 m.
TEXT/MTEXT 엔티티의 bbox 를 ezdxf 로 계산해 다음을 만족하는지 검사한다.

    max(x) <= 20.95   (틀 오른쪽 + 여유 5 cm)
    min(y) >= -1.55   (틀 아래 주기 영역 허용 범위)

사용:
  python3 src/tools/text_bbox.py <dxf 폴더> [--assert] [--quiet]
  --assert  : 기준 위반 시 exit 1
  --quiet   : 요약만 출력

ezdxf bbox 는 폰트 파일이 없으면 글자당 1.0 em 로 넓게 잡는다(한글은 실제와 거의 같고,
라틴 문자는 실제보다 넓게 잡힌다). 즉 보수적(넉넉한) 추정이다.
"""

import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYDEPS = os.environ.get("HOUSEBIM_PYDEPS") or os.path.join(ROOT, "pydeps")
if os.path.isdir(PYDEPS) and PYDEPS not in sys.path:
    sys.path.append(PYDEPS)

import ezdxf
from ezdxf import bbox

XMAX = 20.95
YMIN = -1.55


def text_bbox(entities, cache):
    """(extmin, extmax, entity) 리스트. bbox 계산 불가 엔티티는 건너뛴다."""
    out = []
    for e in entities:
        if e.dxftype() not in ("TEXT", "MTEXT"):
            continue
        try:
            b = bbox.extents([e], cache=cache)
        except Exception:
            continue
        if not b.has_data:
            continue
        out.append((b.extmin, b.extmax, e))
    return out


def label(e):
    s = e.dxf.text if e.dxftype() == "TEXT" else e.text
    s = " ".join(str(s).split())
    return (s[:70] + "...") if len(s) > 70 else s


def audit(path):
    doc = ezdxf.readfile(path)
    cache = bbox.Cache()
    boxes = text_bbox(doc.modelspace(), cache)
    if not boxes:
        return {"file": os.path.basename(path), "texts": 0, "maxx": None, "miny": None,
                "over_x": [], "under_y": []}
    maxx = max(b[1].x for b in boxes)
    miny = min(b[0].y for b in boxes)
    wx = max(boxes, key=lambda b: b[1].x)
    wy = min(boxes, key=lambda b: b[0].y)
    return {
        "file": os.path.basename(path),
        "texts": len(boxes),
        "maxx": maxx, "miny": miny,
        "worst_x": (label(wx[2]), round(wx[1].x, 3)),
        "worst_y": (label(wy[2]), round(wy[0].y, 3)),
        "over_x": [(label(b[2]), round(b[1].x, 3)) for b in boxes if b[1].x > XMAX],
        "under_y": [(label(b[2]), round(b[0].y, 3)) for b in boxes if b[0].y < YMIN],
    }


def main(argv):
    folder = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "."
    do_assert = "--assert" in argv
    quiet = "--quiet" in argv
    files = sorted(glob.glob(os.path.join(folder, "*.dxf")))
    if not files:
        print("DXF 없음:", folder)
        return 2
    gmax_x, gmin_y = None, None
    worst = {"x": None, "y": None}
    bad_x = bad_y = 0
    for f in files:
        r = audit(f)
        if r["maxx"] is None:
            continue
        if gmax_x is None or r["maxx"] > gmax_x:
            gmax_x, worst["x"] = r["maxx"], (r["file"],) + tuple(r["worst_x"])
        if gmin_y is None or r["miny"] < gmin_y:
            gmin_y, worst["y"] = r["miny"], (r["file"],) + tuple(r["worst_y"])
        if r["over_x"]:
            bad_x += 1
        if r["under_y"]:
            bad_y += 1
        if not quiet and (r["over_x"] or r["under_y"]):
            for txt, x in r["over_x"]:
                print(f"  OVER-X {x:7.3f}  {r['file'][:-4]}  {txt}")
            for txt, y in r["under_y"]:
                print(f"  UNDER-Y {y:7.3f} {r['file'][:-4]}  {txt}")
    print(f"{os.path.basename(os.path.abspath(folder))}: DXF {len(files)}장 · "
          f"max(x)={gmax_x:.3f} (한도 {XMAX}) · min(y)={gmin_y:.3f} (한도 {YMIN})")
    print(f"  worst x: {worst['x']}")
    print(f"  worst y: {worst['y']}")
    print(f"  위반 시트: over-x {bad_x}장 · under-y {bad_y}장")
    ok = gmax_x <= XMAX and gmin_y >= YMIN
    if do_assert and not ok:
        print("ASSERT FAIL: 텍스트가 틀을 벗어남")
        return 1
    print("ASSERT OK" if ok else "ASSERT FAIL")
    return 0 if ok or not do_assert else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

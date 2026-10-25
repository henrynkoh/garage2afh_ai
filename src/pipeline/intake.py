#!/usr/bin/env python3
"""intake.py - 실측 인테이크 단계 (사진 + 실측 영상 + 음성 전사 치수).

프로젝트 폴더의 intake/ 를 읽어 ⑴ 정규화 치수 JSON, ⑵ 근거 파일 해시 목록,
⑶ design.py 의 ROOMS 에 붙일 초안을 만든다.

입력 (projects/<id>/intake/ - 있는 것만 쓰면 된다)
  *.jpg *.jpeg *.png *.heic    현장 사진
  *.mp4 *.mov                  실측 영상 (증거로만 기록 - 전사는 앱 외부 단계)
  notes.txt / transcript.txt   음성으로 말한 실측을 전사한 텍스트
  measurements.json            (선택) 운영자가 직접 넣은 치수 - 이미 있으면 보존

출력
  intake/measurements.json     {rooms:[{room,w_m,d_m,source}], plate, warnings}
  intake/evidence.json         파일별 name / bytes / sha256 / (이미지) 픽셀 크기
  intake/design_rooms.py       design.py 의 ROOMS 목록에 그대로 붙이는 초안

지원 치수 표기 (한 줄에 하나)
  12'-10" x 9'-7"     피트-인치
  12'10" x 9'7"       피트-인치 (구분자 없음)
  12' x 9'            피트만
  3.6m x 2.4m         미터
  3600 x 2400 mm      밀리미터 (단위가 줄 끝에 한 번)
  360cm x 240cm       센티미터
  침실A 12'-10" x 9'-7" / Bedroom A 12'10" x 9'7"   실 이름 + 치수 (한/영)

영상 전사는 이 앱의 일이 아니다: 촬영 → (앱 밖) 음성 전사 → transcript.txt →
이 스크립트. 영상 파일은 출처 증거로만 해시·기록한다.

사용:
  python3 src/pipeline/intake.py projects/<id> [--circulation 0.12] [--quiet]
  (HOUSEBIM_DESIGN_DIR 가 있으면 인자 없이 실행 가능)
종료 코드: 0 = 치수 파싱 성공, 1 = 치수 한 줄도 못 읽음
"""

import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime

FT = 0.3048
IN = FT / 12.0
PHOTO_EXT = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".m4v")
TEXT_NAMES = ("notes.txt", "transcript.txt")
CIRCULATION_DEFAULT = 0.12      # 실 면적 합 → 플레이트 (복도·벽체 여유)
MIN_ASPECT, MAX_ASPECT = 1.0, 1.6


# ---------------------------------------------------------------- 단위 / 토큰
_NUM = r"\d+(?:[.,]\d+)?"
TOKEN_RE = re.compile(
    _NUM + r"(?:"
    r"\s*['\u2019\u2032]\s*-?\s*" + _NUM + r"\s*(?:\"|\u201d|\u2033|'')?"   # 12'-10"  12'10"
    r"|\s*['\u2019\u2032]\s*(?:\"|\u201d|\u2033|'')?"                        # 12'
    r"|\s*(?:\"|\u201d|\u2033)"                                              # 10"
    r"|\s*(?:mm|cm|ft|feet|foot|inch|inches|in|m)\b"                         # 3600mm
    r"|\s*(?:밀리미터|센티미터|미터|피트|인치)"
    r")?",
    re.I,
)
SEP_RE = re.compile(r"^\s*(?:x|\u00d7|\*|by|\uacf1\ud558\uae30)\s*$", re.I)
FOOT_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*['\u2019\u2032]\s*-?\s*(\d+(?:[.,]\d+)?)?\s*(?:\"|\u201d|\u2033|'')?\s*$")
INCH_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:\"|\u201d|\u2033|in|inch|inches|\uc778\uce58)\s*$", re.I)
MM_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:mm|\ubc00\ub9ac\ubbf8\ud130|\ubc00\ub9ac)\s*$", re.I)
CM_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:cm|\uc13c\ud2f0\ubbf8\ud130|\uc13c\ud2f0)\s*$", re.I)
M_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:m|meter|meters|metre|metres|\ubbf8\ud130)\s*$", re.I)
FT_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(?:ft|feet|foot|\ud53c\ud2b8)\s*$", re.I)
BARE_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*$")
HINT_PATTERNS = (
    ("mm", re.compile(r"\bmm\b|\ubc00\ub9ac", re.I)),
    ("cm", re.compile(r"\bcm\b|\uc13c\ud2f0", re.I)),
    ("ft", re.compile(r"\bft\b|\bfeet\b|\bfoot\b|\ud53c\ud2b8", re.I)),
    ("m", re.compile(r"(?<![a-z])\bm\b|\ubbf8\ud130", re.I)),
)
KIND_HINTS = (
    ("bedroom", ("\uce68\uc2e4", "\uc548\ubc29", "bed", "bedroom")),
    ("bath", ("\uc695\uc2e4", "\ud654\uc7a5\uc2e4", "bath", "shower", "wc")),
    ("kitchen", ("\uc8fc\ubc29", "\ubd80\uc5c9", "kitchen")),
    ("living", ("\uac70\uc2e4", "living", "family", "lounge")),
    ("dining", ("\uc2dd\ub2f9", "dining")),
    ("hall", ("\ubcf5\ub3c4", "hall", "corridor", "landing")),
    ("storage", ("\uc218\ub0a9", "\ucc3d\uace0", "\uae30\uacc4", "storage", "closet", "pantry", "mech")),
    ("laundry", ("\uc138\ud0c1", "laundry", "utility")),
    ("garage", ("\ucc28\uace0", "garage", "carport")),
    ("office", ("\uc11c\uc7ac", "\uc0ac\ubb34", "office", "study", "den")),
)


def _to_float(s):
    """'3,600' -> 3600.0, '3.6' -> 3.6. 쉼표는 천단위 구분으로 본다."""
    s = str(s).strip()
    if re.search(r",\d{3}(?!\d)", s):
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    return float(s)


def token_to_m(tok, hint=None):
    """길이 토큰 → (미터, 표기단위) 또는 (None, '') - 해석 불가."""
    t = str(tok).strip()
    m = FOOT_RE.match(t)
    if m:
        feet = _to_float(m.group(1))
        inch = _to_float(m.group(2)) if m.group(2) else 0.0
        return (feet + inch / 12.0) * FT, "ft"
    m = INCH_RE.match(t)
    if m:
        return _to_float(m.group(1)) * IN, "in"
    m = MM_RE.match(t)
    if m:
        return _to_float(m.group(1)) / 1000.0, "mm"
    m = CM_RE.match(t)
    if m:
        return _to_float(m.group(1)) / 100.0, "cm"
    m = M_RE.match(t)
    if m:
        return _to_float(m.group(1)), "m"
    m = FT_RE.match(t)
    if m:
        return _to_float(m.group(1)) * FT, "ft"
    m = BARE_RE.match(t)
    if m:
        v = _to_float(m.group(1))
        if hint == "mm":
            return v / 1000.0, "mm"
        if hint == "cm":
            return v / 100.0, "cm"
        if hint == "ft":
            return v * FT, "ft"
        if hint == "m":
            return v, "m"
        if v >= 100:                    # 단위 없는 큰 수 = 밀리미터로 본다 (가정)
            return v / 1000.0, "mm?"
        return None, ""                 # 12 x 9 같은 애매한 수는 추측하지 않는다
    return None, ""


def line_hint(line):
    for unit, pat in HINT_PATTERNS:
        if pat.search(line):
            return unit
    return None


def room_name(line, first_start, tail_start, tail_end):
    """치수 앞 텍스트를 실 이름으로. 없으면 치수 뒤 텍스트, 그래도 없으면 미지정."""
    head = line[:first_start].strip(" \t-\u2013\u2014\u2022*\u00b7|:：[]()")
    head = re.sub(r"^\d+[).]\s*", "", head).strip()
    if head and re.search(r"[A-Za-z\uac00-\ud7a3]", head):
        return head
    tail = line[tail_end:].strip(" \t-\u2013\u2014\u2022*\u00b7|:：[]()")
    tail = re.split(r"[(\[]", tail)[0].strip()
    if tail and re.search(r"[A-Za-z\uac00-\ud7a3]", tail) and not re.search(r"\d", tail[:2]):
        return tail
    return "\ubb38\uc11c \ubbf8\uc9c0\uc815"    # "문서 미지정"


def kind_of(name):
    low = str(name).lower()
    for kind, words in KIND_HINTS:
        if any(w in low for w in words):
            return kind
    return "room"


def parse_line(line):
    """한 줄 → dict(room, w_m, d_m, raw) 또는 None. 실패 이유는 parse_line_error()."""
    toks = list(TOKEN_RE.finditer(line))
    if not toks:
        return None, "\uce58\uc218 \uc5c6\uc74c"                     # 치수 없음
    hint = line_hint(line)
    for i in range(len(toks) - 1):
        a, b = toks[i], toks[i + 1]
        if not SEP_RE.match(line[a.end():b.start()]):
            continue
        wa, ua = token_to_m(a.group(0), hint)
        wb, ub = token_to_m(b.group(0), hint)
        if wa is None or wb is None:
            return None, "\ub2e8\uc704 \ubd88\uba85 (\uc608: 12 x 9 - ft/m \ud45c\uae30 \ud544\uc694)"  # 단위 불명
        if wa <= 0.3 or wb <= 0.3 or wa > 60 or wb > 60:
            return None, "\ubc94\uc704 \ubc16 \uac12 (0.3~60 m)"
        if wa < wb:                                   # 긴 쪽을 가로(w)로 둔다
            wa, wb, ua, ub = wb, wa, ub, ua
        return {
            "room": room_name(line, a.start(), a.end(), b.end()),
            "w_m": round(wa, 3),
            "d_m": round(wb, 3),
            "area_m2": round(wa * wb, 3),
            "raw": " ".join(line.split()),
            "unit": ua if ua == ub else "%s/%s" % (ua, ub),
        }, ""
    return None, "\uce58\uc218 \uc30d\uc774 \uc544\ub2d8 (W x D \ud615\uc2dd \ud544\uc694)"      # 1개만 있음


# ---------------------------------------------------------------- 파일 수집
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _pil():
    """PIL 을 찾는다. 없으면 Aside 런타임 site-packages 를 한 번 시도한다."""
    try:
        from PIL import Image  # noqa: F401
        import PIL
        return PIL.Image
    except Exception:
        pass
    for cand in (os.environ.get("G2A_PIL_PATH"),
                 "/Users/henryoh/.aside/runtime/python/venv/lib/python3.13/site-packages"):
        if cand and os.path.isdir(cand) and cand not in sys.path:
            sys.path.append(cand)
            try:
                from PIL import Image
                return Image
            except Exception:
                continue
    return None


def image_size(path):
    """(width, height, format) 또는 (None, None, None) - 읽기 실패는 조용히 넘긴다."""
    Image = _pil()
    if Image is not None:
        try:
            with Image.open(path) as im:
                return im.width, im.height, im.format
        except Exception:
            pass
    if path.lower().endswith(".png"):                  # PIL 없이도 PNG 헤더는 읽는다
        try:
            with open(path, "rb") as fh:
                head = fh.read(33)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"), "PNG"
        except Exception:
            pass
    return None, None, None


def collect_files(d):
    photos, videos, texts = [], [], []
    for p in sorted(glob.glob(os.path.join(d, "*"))):
        if not os.path.isfile(p):
            continue
        low = os.path.basename(p).lower()
        if low in TEXT_NAMES:
            texts.append(p)
        elif low.endswith(PHOTO_EXT):
            photos.append(p)
        elif low.endswith(VIDEO_EXT):
            videos.append(p)
    return photos, videos, texts


# ---------------------------------------------------------------- 플레이트
def declared_footprint(proj_dir):
    """META 에 선언된 플레이트. {"w","d","area","basis"} 중 아는 값만. meta.json → design.META 순."""
    got = {}
    cands = []
    mj = os.path.join(proj_dir, "meta.json")
    if os.path.isfile(mj):
        try:
            cands.append(json.load(open(mj, encoding="utf-8")))
        except Exception:
            pass
    if os.path.isfile(os.path.join(proj_dir, "design.py")):
        sys.path.insert(0, proj_dir)
        try:
            import design
            cands.append(getattr(design, "META", {}) or {})
        except Exception:
            pass
        finally:
            if proj_dir in sys.path:
                sys.path.remove(proj_dir)
    for c in cands:
        for k in ("footprint_m", "plate_m", "footprint_ft", "plate_ft", "garage_ft"):
            v = c.get(k)
            f = FT if k.endswith("_ft") else 1.0
            if isinstance(v, (list, tuple)) and len(v) == 2:
                got.setdefault("w", float(v[0]) * f)
                got.setdefault("d", float(v[1]) * f)
                got.setdefault("basis", "META:%s" % k)
            elif isinstance(v, (list, tuple)) and len(v) == 4:   # (x0,y0,x1,y1)
                got.setdefault("w", (float(v[2]) - float(v[0])) * f)
                got.setdefault("d", (float(v[3]) - float(v[1])) * f)
                got.setdefault("basis", "META:%s" % k)
        for k in ("garage_sf", "existing_garage_sf", "plate_sf"):
            if isinstance(c.get(k), (int, float)) and c.get(k) > 0:
                got.setdefault("area", float(c[k]) * FT * FT)
                got.setdefault("area_basis", "META:%s" % k)
    return got


def make_plate(rooms, declared, circulation):
    """선언된 footprint 가 있으면 그것, 없으면 실 면적 합 + 여유로 종횡비 1.0~1.6 사각형."""
    area_rooms = sum(r["area_m2"] for r in rooms)
    if declared.get("w") and declared.get("d"):
        w, d = declared["w"], declared["d"]
        basis = declared.get("basis", "META:footprint")
        circ_used = 0.0
    else:
        area = declared.get("area") or area_rooms * (1.0 + circulation)
        basis = declared.get("area_basis", "room-sum")
        circ_used = 0.0 if declared.get("area") else circulation
        aspect = min(MAX_ASPECT, max(MIN_ASPECT, 1.4))      # 1.0~1.6 안의 실용적인 비
        w = round((area * aspect) ** 0.5 / 0.05) * 0.05
        d = round((area / max(w, 0.05)) / 0.05) * 0.05
        if w < d:
            w, d = d, w
    w, d = round(w, 2), round(d, 2)
    if w < d:
        w, d = d, w
    plate = {
        "w_m": w, "d_m": d, "area_m2": round(w * d, 3),
        "area_sf": round(w * d / (FT * FT), 1),
        "aspect": round(w / d, 3),
        "basis": basis,
        "area_rooms_m2": round(area_rooms, 3),
        "circulation_pct": circ_used,
    }
    warnings = []
    if plate["aspect"] < MIN_ASPECT or plate["aspect"] > MAX_ASPECT:
        warnings.append({"source": "plate", "text": "%s %.2f x %.2f m" % (basis, w, d),
                         "reason": "\uc885\ud6a1\ube44 %.2f \u2192 1.0~1.6 \ubc16 (\ud655\uc778 \ud544\uc694)" % plate["aspect"]})
    if declared.get("area"):
        declared_area = declared["area"]
        plate["declared_area_m2"] = round(declared_area, 3)
        if area_rooms > declared_area * 1.15:
            warnings.append({"source": "META", "text": "\uc120\uc5b8 \ud50c\ub808\uc774\ud2b8 %.1f m2" % declared_area,
                             "reason": "\uc2e4 \uba74\uc801 \ud569\uacc4 %.1f m2 \uac00 \uc120\uc5b8\uac12\ubcf4\ub2e4 15% \uc774\uc0c1 \ud07c" % area_rooms})
    return plate, warnings


def pack_rooms(rooms, plate_w, plate_d, gap=0.05):
    """단순 패킹: 플레이트를 실 면적 비율로 재귀 분할(guillotine)한 뒤,
    각 칸 안에 실측 가로/세로 비율을 유지한 사각형을 앉힌다.
    -> 실은 절대 잘리거나 0 에 가깝게 줄지 않고, 칸이 남으면 여백으로 남는다."""
    total = sum(r["area_m2"] for r in rooms) or 1.0
    margin = gap / 2.0

    def split(items, box):
        if len(items) == 1:
            return [(items[0], box)]
        area_all = sum(r["area_m2"] for r in items)
        acc, cut = 0.0, len(items) - 1
        for i, r in enumerate(items[:-1]):
            acc += r["area_m2"]
            if acc >= area_all / 2.0:
                cut = i + 1
                break
        left, right = items[:cut], items[cut:]
        la = sum(r["area_m2"] for r in left)
        frac = la / area_all if area_all else 0.5
        x0, y0, x1, y1 = box
        if (x1 - x0) >= (y1 - y0):                       # 긴 축으로 자른다
            xm = x0 + (x1 - x0) * frac
            return split(left, (x0, y0, xm, y1)) + split(right, (xm, y0, x1, y1))
        ym = y0 + (y1 - y0) * frac
        return split(left, (x0, y0, x1, ym)) + split(right, (x0, ym, x1, y1))

    order = sorted(rooms, key=lambda r: (-r["area_m2"], r["room"]))
    placed, distorted = [], []
    for r, (x0, y0, x1, y1) in split(order, (margin, margin, plate_w - margin, plate_d - margin)):
        bw, bh = x1 - x0 - 2 * margin, y1 - y0 - 2 * margin
        ratio = r["w_m"] / r["d_m"]
        w, d = bw, bw / ratio
        if d > bh:
            d, w = bh, bh * ratio
        w, d = min(w, bw), min(d, bh)
        r2 = dict(r)
        if r["area_m2"] and w * d < 0.85 * r["area_m2"]:
            # 형상(비율)을 지키면 면적이 크게 줄어드는 칸: 칸을 채운다.
            # 면적이 설계 기준이므로 면적을 지키고, 형상은 도면에서 확정한다.
            w, d = bw, bh
            distorted.append(r["room"])
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        rect = (round(cx - w / 2.0, 3), round(cy - d / 2.0, 3),
                round(cx + w / 2.0, 3), round(cy + d / 2.0, 3))
        r2["rect"] = rect
        r2["fitted_w_m"], r2["fitted_d_m"] = round(w, 3), round(d, 3)
        r2["fitted_area_m2"] = round(w * d, 3)
        placed.append(r2)
    return placed, distorted


# ---------------------------------------------------------------- 산출물
ROOMS_TPL = '''"""design_rooms.py - {slug} 실측 인테이크 초안 ({stamp} 자동 생성).

출처: {sources}
플레이트: {pw:.2f} x {pd:.2f} m ({pa:.1f} m2 / {psf:.0f} SF, basis={basis})
실 면적 합: {ra:.1f} m2 ({rsf:.0f} SF) · 복도/벽체 여유 {circ:.0%}

쓰는 방법
  1) design.py 의 ROOMS = [ ... ] 안에 아래 ROOMS 를 붙여넣는다.
  2) WALLS/DOORS/WINDOWS 는 실 경계를 보고 손으로 확정한다 (이 파일은 초안이다).
  3) 값은 실측 전사에서 온 것이므로, 도면에 쓰기 전에 현장에서 한 번 더 확인한다.

주의: 이 초안의 좌표는 플레이트를 실 면적 비율로 분할한 결과다 (면적 비율 유지).
      벽 두께·문 위치·창 위치는 정해지지 않았다.
      치수를 고치면 intake 를 다시 돌리지 말고 design.py 에서 직접 고친다 (원본은 measurements.json).
"""
FT = 0.3048

PLATE = {{"w_m": {pw}, "d_m": {pd}, "area_m2": {pa}}}

# 실측 그대로의 치수 (출처 포함)
MEASURED = [
{measured}]

# design.py 의 ROOMS 에 붙일 초안 (rect = x0, y0, x1, y1 [m])
ROOMS = [
{rows}]
'''


def write_rooms_file(path, slug, rooms_placed, plate, sources, stamp, overflow):
    measured = "".join(
        '    {{"name": {n!r}, "w_m": {w}, "d_m": {d}, "area_m2": {a}, "source": {s!r}}},\n'.format(
            n=r["room"], w=r["w_m"], d=r["d_m"], a=r["area_m2"], s=r["source"])
        for r in rooms_placed)
    rows = "".join(
        '    {{"name": {n!r}, "rect": ({x}, {y}, {x1}, {y1}), "kind": {k!r}}},\n'.format(
            n=r["room"], x=r["rect"][0], y=r["rect"][1], x1=r["rect"][2], y1=r["rect"][3],
            k=kind_of(r["room"]))
        for r in rooms_placed)
    body = ROOMS_TPL.format(
        slug=slug, stamp=stamp, sources=", ".join(sources) or "-",
        pw=plate["w_m"], pd=plate["d_m"], pa=plate["area_m2"], psf=plate["area_sf"],
        basis=plate["basis"], ra=plate["area_rooms_m2"],
        rsf=plate["area_rooms_m2"] / (FT * FT), circ=plate.get("circulation_pct", 0.0),
        measured=measured, rows=rows) if rows else "ROOMS = []\n"
    if overflow:
        body += "\n# 주의: 일부 실은 분할 칸에 맞춰 형상을 늘렸다 (면적·비율은 유지).\n"
        body += "#       침실/욕실의 실제 가로·세로는 MEASURED 값으로 도면에서 확정하라.\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


def read_text(path):
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return open(path, encoding=enc).read()
        except UnicodeDecodeError:
            continue
    return open(path, encoding="utf-8", errors="ignore").read()


def parse_texts(texts):
    """텍스트 파일들 → (rooms, warnings, blocks). 빈 줄/주석 줄이 블록 경계."""
    rooms, warnings, blocks = [], [], []
    block = []
    for path in texts:
        name = os.path.basename(path)
        for no, raw in enumerate(read_text(path).splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                if block:
                    blocks.append(block)
                    block = []
                continue
            row, why = parse_line(line)
            if row:
                row["source"] = "%s:%d" % (name, no)
                row["line"] = no
                row["file"] = name
                block.append(row)
                rooms.append(row)
            else:
                warnings.append({"source": "%s:%d" % (name, no),
                                 "text": " ".join(line.split())[:120], "reason": why})
    if block:
        blocks.append(block)
    return rooms, warnings, blocks


def pick_largest_set(blocks):
    """여러 실측 블록(1차/2차 촬영)이 있으면 면적 합이 가장 큰 블록을 쓴다."""
    if not blocks:
        return None, 0, []
    tot = [sum(r["area_m2"] for r in b) for b in blocks]
    best = max(range(len(blocks)), key=lambda i: tot[i])
    return blocks[best], best + 1, tot


def print_table(rows, plate, warnings, files_note):
    print("\n%-4s %-22s %7s %7s %9s %8s  %s" % ("#", "실(room)", "가로m", "세로m", "면적m2", "면적SF", "출처"))
    print("-" * 96)
    for i, r in enumerate(rows, 1):
        print("%-4d %-22s %7.3f %7.3f %9.3f %8.1f  %s"
              % (i, r["room"][:22], r["w_m"], r["d_m"], r["area_m2"], r["area_m2"] / (FT * FT), r["source"]))
    print("-" * 96)
    tot = sum(r["area_m2"] for r in rows)
    print("%-27s %7s %7s %9.3f %8.1f" % ("합계 %d실" % len(rows), "", "", tot, tot / (FT * FT)))
    print("\n플레이트 %0.2f x %0.2f m = %0.2f m2 (%0.0f SF) · 종횡비 %0.2f · basis=%s"
          % (plate["w_m"], plate["d_m"], plate["area_m2"], plate["area_sf"], plate["aspect"], plate["basis"]))
    if warnings:
        print("경고 %d건:" % len(warnings))
        for w in warnings:
            print("  - %s  %s :: %s" % (w["source"], w["reason"], w["text"]))
    else:
        print("경고 없음")
    print(files_note)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    quiet = "--quiet" in argv
    argv = [a for a in argv if a != "--quiet"]
    circ = CIRCULATION_DEFAULT
    if "--circulation" in argv:
        i = argv.index("--circulation")
        try:
            circ = float(argv[i + 1])
        except (IndexError, ValueError):
            print("--circulation 값이 숫자가 아니다", file=sys.stderr)
            return 1
        del argv[i:i + 2]
    proj = argv[0] if argv else os.environ.get("HOUSEBIM_DESIGN_DIR", "")
    if not proj:
        print("프로젝트 경로가 없다: intake.py <projects/<id>>", file=sys.stderr)
        return 1
    proj = os.path.abspath(proj)
    proj = os.path.dirname(proj) if os.path.basename(proj) == "intake" else proj
    if not os.path.isdir(proj):
        print("프로젝트 폴더가 없다: " + proj, file=sys.stderr)
        return 1
    intake_dir = os.path.join(proj, "intake")
    slug = os.path.basename(proj)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if os.path.isdir(intake_dir):
        photos, videos, texts = collect_files(intake_dir)
    else:
        os.makedirs(intake_dir, exist_ok=True)
        photos, videos, texts = [], [], []
        print("[intake] intake/ 폴더가 없어 새로 만들었다 - 사진/영상/전사문을 넣고 다시 실행")
    if not (photos or videos or texts):
        print("[intake] intake/ 가 비어 있다: 사진(jpg/png/heic)·영상(mp4/mov)·notes.txt/transcript.txt 중 하나 필요")

    rooms, warnings, blocks = parse_texts(texts)
    best, set_index, set_tot = pick_largest_set(blocks)
    out_rooms = list(best) if best else []
    if len(blocks) > 1:
        warnings.append({"source": "intake", "text": "%d개 실측 블록" % len(blocks),
                         "reason": "면적 최대 블록(#%d)을 채택, 나머지 %d블록은 참고"
                                   % (set_index, len(blocks) - 1)})

    # 이미 있는 measurements.json: 운영자가 직접 넣은 행(source=measurements.json)은 보존
    mpath = os.path.join(intake_dir, "measurements.json")
    declared_rooms = []
    if os.path.isfile(mpath):
        try:
            old = json.load(open(mpath, encoding="utf-8"))
            for r in old.get("rooms", []):
                if str(r.get("source", "")).startswith("measurements.json") and r.get("room"):
                    declared_rooms.append(r)
        except Exception:
            warnings.append({"source": "measurements.json", "text": "읽기 실패", "reason": "JSON 파싱 오류 - 무시하고 새로 쓴다"})
    names = {r["room"] for r in out_rooms}
    for r in declared_rooms:                      # 손으로 넣은 행이 전사보다 우선
        if r["room"] in names:
            out_rooms = [x for x in out_rooms if x["room"] != r["room"]]
        out_rooms.append(r)

    evidence_files = []
    for p in photos + videos + texts:
        name = os.path.basename(p)
        kind = "photo" if p in photos else ("video" if p in videos else "text")
        row = {"file": name, "kind": kind, "bytes": os.path.getsize(p), "sha256": sha256_of(p)}
        if kind == "photo":
            w, h, fmt = image_size(p)
            row.update({"width_px": w, "height_px": h, "format": fmt})
            if w is None:
                warnings.append({"source": name, "text": name,
                                 "reason": "픽셀 크기 읽기 실패 (HEIC 이거나 손상)"})
        evidence_files.append(row)

    evidence = {
        "project": slug,
        "generated": stamp,
        "intake_dir": os.path.relpath(intake_dir, proj),
        "counts": {"photo": len(photos), "video": len(videos), "text": len(texts)},
        "files": evidence_files,
        "video_note": "영상은 출처 증거로만 기록한다. 음성 전사(transcription)는 앱 외부 단계이며, "
                      "결과는 notes.txt/transcript.txt 로 들어온다.",
    }
    json.dump(evidence, open(os.path.join(intake_dir, "evidence.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    if not out_rooms:
        print("\n[intake] 치수 한 줄도 파싱하지 못했다 - notes.txt/transcript.txt 를 확인하라")
        for w in warnings:
            print("  - %s :: %s :: %s" % (w["source"], w["reason"], w["text"]))
        print("[intake] 증거 기록만 남겼다: %s" % os.path.join(intake_dir, "evidence.json"))
        return 1

    _decl = declared_footprint(proj)
    plate, plate_warn = make_plate(out_rooms, _decl, circ)
    warnings.extend(plate_warn)
    placed, distorted = pack_rooms(out_rooms, plate["w_m"], plate["d_m"])
    # 플레이트는 규칙(실 면적 합 + 여유, 종횡비 1.0~1.6)대로 정하고, 패킹은 그 안에서만 한다.
    plate["packed_layout"] = "guillotine"
    plate["packing_adjusted_rooms"] = distorted
    plate["packed_area_m2"] = round(sum(r.get("fitted_area_m2", 0) for r in placed), 3)

    payload = {
        "project": slug,
        "generated": stamp,
        "sources": [os.path.basename(p) for p in texts],
        "rooms": [{"room": r["room"], "w_m": r["w_m"], "d_m": r["d_m"],
                   "area_m2": r["area_m2"], "source": r["source"],
                   "raw": r.get("raw", ""), "unit": r.get("unit", ""), "set": set_index}
                  for r in out_rooms],
        "total_area_m2": round(sum(r["area_m2"] for r in out_rooms), 3),
        "total_area_sf": round(sum(r["area_m2"] for r in out_rooms) / (FT * FT), 1),
        "plate": plate,
        "sets": [{"index": i + 1, "rooms": len(b), "area_m2": round(t, 3)} for i, (b, t) in enumerate(zip(blocks, set_tot))],
        "chosen_set": set_index,
        "warnings": warnings,
        "evidence": {"photo": len(photos), "video": len(videos), "text": len(texts)},
    }
    json.dump(payload, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_rooms_file(os.path.join(intake_dir, "design_rooms.py"), slug, placed, plate,
                     payload["sources"], stamp, bool(distorted))

    if not quiet:
        print("실측 인테이크 · %s · %s" % (slug, stamp))
        print_table(out_rooms, plate, warnings,
                    "증거: 사진 %d · 영상 %d · 텍스트 %d → intake/evidence.json"
                    % (len(photos), len(videos), len(texts)))
        print("출력: intake/measurements.json · intake/design_rooms.py · intake/evidence.json")
        if videos:
            print("영상 %d개는 증거로만 해시했다 - 전사(음성→텍스트)는 앱 외부에서 하고 "
                  "결과를 transcript.txt 로 넣어라." % len(videos))
    return 0


if __name__ == "__main__":
    sys.exit(main())

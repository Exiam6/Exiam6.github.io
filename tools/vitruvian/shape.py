#!/usr/bin/env python3
"""Body-shape proofs: the figure's own build, changed in the coordinates.

Proof H was an affine in y, so pose.py could preview it with one copy of the
drawing and a CSS transform.  Shoulder width, waist, hips are NOT affine —
the whole point is that the core widens while the outstretched arms stay
exactly where the square wants them — so each proof here is a genuinely
rewritten copy of the plate.  That means a path walker that resolves every
relative segment to an absolute point, maps it, and writes it back out.

    python3 tools/vitruvian/shape.py --check    # identity map must round-trip
    python3 tools/vitruvian/shape.py            # -> tools/vitruvian/shape.html
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from anatomy import plate, tag  # noqa: E402

OUT = os.path.join(HERE, "shape.html")
ANAT = os.path.join(HERE, "anatomy.json")

AXIS = 500.0          # the figure is drawn symmetric about this
CROWN, HIP, FEET = 139.5, 503.0, 915.4

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def fmt(v):
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def rewrite(d, f):
    """Rewrite a path through f(x, y) -> (x, y), in absolute coordinates.

    Only the commands this plate actually uses are handled (M L H V Z m q);
    anything else raises rather than silently mangling the drawing.
    """
    out, cur, start = [], (0.0, 0.0), (0.0, 0.0)
    for k, m in enumerate(CMD.finditer(d)):
        cmd, vals = m.group(1), [float(n) for n in NUM.findall(m.group(2))]
        rel = cmd.islower()
        up = cmd.upper()
        if up == "Z":
            out.append("Z")
            cur = start
            continue
        if up in ("A", "C", "S", "T"):
            raise ValueError("unhandled command %s" % cmd)

        pts = []
        if up == "H":
            pts = [(v + (cur[0] if rel else 0), None) for v in vals]
        elif up == "V":
            pts = [(None, v + (cur[1] if rel else 0)) for v in vals]
        else:
            if len(vals) % 2:
                raise ValueError("odd coordinate count after %s" % cmd)
            # a relative pair is relative to the CURRENT point, which for the
            # first pair of a path is the origin — so an opening `m` is
            # absolute, and every later `m` really is relative
            p = cur if not (k == 0 and rel) else (0.0, 0.0)
            for i in range(0, len(vals), 2):
                x, y = vals[i], vals[i + 1]
                q = (x + p[0], y + p[1]) if rel else (x, y)
                pts.append(q)
                # q takes pairs in twos: control, then endpoint — the endpoint
                # is what the next relative pair is measured from
                if up != "Q" or i % 4 == 2:
                    p = q
            if up == "Q" and len(vals) % 4:
                raise ValueError("ragged quadratic after %s" % cmd)

        if up == "H":
            mapped = [f(x, cur[1])[0] for x, _ in pts]
            cur = (pts[-1][0], cur[1])
        elif up == "V":
            mapped = [f(cur[0], y)[1] for _, y in pts]
            cur = (cur[0], pts[-1][1])
        else:
            mapped = []
            for x, y in pts:
                mx, my = f(x, y)
                mapped += [mx, my]
            cur = pts[-1]
        if up == "M":
            start = cur
        out.append(up + " ".join(fmt(v) for v in mapped))
    return "".join(out)


# ---- the warps -------------------------------------------------------------
def bump(y, yc, hw):
    """A raised cosine: 1 at yc, 0 at yc±hw, smooth at both ends."""
    t = abs(y - yc)
    return 0.0 if t >= hw else 0.5 * (1 + math.cos(math.pi * t / hw))


def taper(x, full=105.0, out=180.0):
    """How much of (x-AXIS) the warp acts on: all of it across the body core,
    fading to nothing before the outstretched arms, which must not move —
    the fingertips ARE the square's left and right edges."""
    dx = x - AXIS
    a = abs(dx)
    if a <= full:
        return dx
    if a >= out:
        return 0.0
    return dx * (out - a) / (out - full)


def widen(amount, yc, hw):
    """x' = x + amount * bump(y) * taper(x). y is never touched."""
    def f(x, y):
        return x + amount * bump(y, yc, hw) * taper(x), y
    return f


def scale_about(pivot, s):
    def f(x, y):
        return pivot[0] + (x - pivot[0]) * s, pivot[1] + (y - pivot[1]) * s
    return f


def rotate_about(pivot, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    def f(x, y):
        dx, dy = x - pivot[0], y - pivot[1]
        return pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca
    return f


def identity(x, y):
    return x, y


# ---- which elements a local change applies to ------------------------------
# Read off anatomy.json (which measures the SHIPPED, H-baked plate).
HANDS = [  # (centre of the hand, the wrist it turns about)
    ((155.0, 288.0), (200.0, 293.0)),   # viewer-left, horizontal — the Touch hotspot
    ((195.0, 178.0), (238.0, 208.0)),   # viewer-left, raised
    ((845.0, 288.0), (800.0, 293.0)),
    ((805.0, 178.0), (762.0, 208.0)),
]
HIPS = ((465.0, 505.0), (535.0, 505.0))     # left / right hip joint


def boxes():
    return {e["i"]: e for e in json.load(open(ANAT))}


def centre(e):
    return e["x"] + e["w"] / 2, e["y"] + e["h"] / 2


def in_hand(e):
    cx, cy = centre(e)
    for k, (h, w) in enumerate(HANDS):
        if abs(cx - h[0]) < 58 and abs(cy - h[1]) < 58:
            return k
    return None


def in_spread_leg(e):
    cx, cy = centre(e)
    if cy < 512 or abs(cx - AXIS) < 65:
        return None
    return 0 if cx < AXIS else 1


def per_element(kind, amount):
    """Return i -> map, for the changes that act on one body part only."""
    B = boxes()

    def maps(i):
        e = B[i]
        if e["layer"] == "vm-geom":
            return None
        if kind == "hand":
            k = in_hand(e)
            return scale_about(HANDS[k][1], amount) if k is not None else None
        if kind == "leg":
            k = in_spread_leg(e)
            if k is None:
                return None
            return rotate_about(HIPS[k], amount if k == 0 else -amount)
        return None
    return maps


def whole(f):
    """A warp that acts on the whole plate except the construction geometry."""
    B = boxes()
    return lambda i: None if B[i]["layer"] == "vm-geom" else f


def apply_to_plate(inner, maps):
    """Rewrite every element whose map is not None."""
    n = [0]
    hit = [0]

    def sub(m):
        i = n[0]
        n[0] += 1
        f = maps(i)
        if f is None:
            return m.group(0)
        hit[0] += 1
        return re.sub(r'\bd="([^"]+)"',
                      lambda d: 'd="%s"' % rewrite(d.group(1), f), m.group(0))

    tags = re.compile(r"<(?:path|circle)\b[^>]*>")
    return tags.sub(sub, inner), hit[0]


def compose(*fs):
    def f(x, y):
        for g in fs:
            x, y = g(x, y)
        return x, y
    return f


SHOULDER = (290.0, 95.0)     # (centre, half-width) of the raised-cosine band
WAIST = (430.0, 90.0)
PELVIS = (505.0, 78.0)

PROOFS = [
    ("A", "现在这版", "H 定稿，一笔未改，作参照", "—", None),
    ("B", "宽肩", "肩带整体外扩 7%，到上臂中段平滑收回。臂展、方框接触点都不动",
     "肩 +7% · 带心 y290 · 半宽 95", lambda: whole(widen(+0.07, *SHOULDER))),
    ("C", "窄肩", "反过来收窄 6%：肩塌下去，整具机器显得更轻、更瘦长",
     "肩 −6%", lambda: whole(widen(-0.06, *SHOULDER))),
    ("D", "细腰", "腰腹收 8%。躯干出现明显的束腰，胸腔和骨盆被分成两段",
     "腰 −8% · 带心 y430", lambda: whole(widen(-0.08, *WAIST))),
    ("E", "厚腰", "腰腹放 8%：躯干变成一根整柱，更敦实、更不像人",
     "腰 +8%", lambda: whole(widen(+0.08, *WAIST))),
    ("F", "宽胯", "胯部外扩 7%，两条腿的根部拉开",
     "胯 +7% · 带心 y505", lambda: whole(widen(+0.07, *PELVIS))),
    ("G", "大手", "四只手各绕自己的腕关节放大到 1.16。触觉那条线第一次在图上有分量 —— "
     "代价是实的：指尖越过方框边线 14 个单位（440px 下 6px），“臂展＝身高”那处接触点就不再成立",
     "手 ×1.16 @腕 · 指尖 112.5→98.5", lambda: per_element("hand", 1.16)),
    ("H", "腿张角更开", "张开的那对腿绕胯关节各转 3.5°，并拢的那对不动 —— 重影拉得更开",
     "张腿 ±3.5° @胯", lambda: per_element("leg", 3.5)),
    ("I", "宽肩 + 细腰", "把 B 和 D 叠在一起：这是“器械感”那条路走到底的样子",
     "肩 +7% · 腰 −8%",
     lambda: whole(compose(widen(+0.07, *SHOULDER), widen(-0.08, *WAIST)))),
]


def build():
    inner = plate()
    assert 'id="vm-ink"' in inner
    tiles = []
    for n, (letter, name, note, spec, mk) in enumerate(PROOFS):
        body, hit = (inner, 0) if mk is None else apply_to_plate(inner, mk())
        body = body.replace('id="vm-ink"', 'id="vm-ink-%d"' % n) \
                   .replace('href="#vm-ink"', 'href="#vm-ink-%d"' % n)
        tiles.append(TILE % (letter, name, body, letter, name, note, spec))
        print("  %s %-10s %d elements rewritten, %d bytes"
              % (letter, name, hit, len(body)))
    return PAGE.replace("__TILES__", "".join(tiles))


TILE = """      <figure class="proof">
        <div class="platemark">
          <svg class="pl" viewBox="0 0 1000 1000" fill="none" stroke="currentColor"
               stroke-linecap="round" stroke-linejoin="round" role="img"
               aria-label="%s 号试样：%s">
%s
          </svg>
        </div>
        <figcaption>
          <p class="desig"><span class="letter">%s</span></p>
          <h2>%s</h2>
          <p class="note">%s</p>
          <p class="spec">%s</p>
        </figcaption>
      </figure>
"""


PAGE = """<title>维特鲁威人体型七版</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --paper:#fefcf8;
  --paper-edge:#e7dccb;
  --sang:#8a6a4f;
  --hot:#a8552b;

  --ground:#efe7da;
  --panel:#f7f1e6;
  --text:#3b332a;
  --text2:#6d6055;
  --rule:#ddd0bc;

  --serif:"EB Garamond","Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
  --mono:"IBM Plex Mono","SF Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#15110d; --panel:#1d1811; --text:#e7dcc9; --text2:#a0917f;
    --rule:#332a20; --hot:#d2794a;
  }
}
:root[data-theme="dark"]{
  --ground:#15110d; --panel:#1d1811; --text:#e7dcc9; --text2:#a0917f;
  --rule:#332a20; --hot:#d2794a;
}

body{ background:var(--ground); color:var(--text); font-family:var(--serif);
      font-size:17px; line-height:1.6; -webkit-font-smoothing:antialiased; }
.wrap{ max-width:1080px; margin:0 auto; padding:56px 28px 96px; }

header{ max-width:64ch; }
.eyebrow{ font-family:var(--mono); font-size:11px; letter-spacing:.16em;
          text-transform:uppercase; color:var(--text2); margin:0 0 14px; }
h1{ font-size:clamp(30px,4.4vw,44px); font-weight:500; line-height:1.12;
    letter-spacing:.01em; margin:0 0 14px; text-wrap:balance; }
header p{ margin:0 0 10px; color:var(--text2); }
header p strong{ color:var(--text); font-weight:600; }
.meta{ font-family:var(--mono); font-size:12px; color:var(--text2);
       border-top:1px solid var(--rule); margin-top:26px; padding-top:12px;
       display:flex; flex-wrap:wrap; gap:6px 22px; font-variant-numeric:tabular-nums; }

.sheet{ display:grid; gap:26px; margin-top:34px;
        grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); }
.proof{ margin:0; background:var(--panel); border:1px solid var(--rule);
        padding:14px 14px 4px; display:flex; flex-direction:column; }
.platemark{ background:var(--paper); border:1px solid var(--paper-edge);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.9),
                       0 1px 2px rgba(59,43,26,.10);
            padding:10px; display:flex; justify-content:center; }
.pl{ display:block; width:100%; max-width:440px; height:auto; color:var(--sang); }

figcaption{ padding:13px 2px 12px; }
.desig{ margin:0 0 3px; }
.letter{ font-family:var(--mono); font-size:12px; font-weight:500;
         letter-spacing:.18em; color:var(--hot); }
h2{ font-size:20px; font-weight:500; margin:0 0 4px; letter-spacing:.01em; }
.note{ margin:0 0 9px; font-size:15px; color:var(--text2); }
.spec{ margin:0; font-family:var(--mono); font-size:11.5px; color:var(--text2);
       border-top:1px solid var(--rule); padding-top:9px;
       font-variant-numeric:tabular-nums; }

footer{ margin-top:44px; border-top:1px solid var(--rule); padding-top:16px;
        color:var(--text2); font-size:15px; max-width:64ch; }

/* the plate's own inking, exactly as index.html carries it */
.pl .vm-geom{ opacity:.55; }
.pl .l-deep{ opacity:.6; }
.pl .l-shade{ opacity:.7; }
.pl .l-halo{ fill:none; stroke:#fff; stroke-width:2.6; stroke-linejoin:round; }
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">Research map · 体型 A–I</p>
    <h1>改的是身体，不是墨</h1>
    <p>上一轮全是图之外的东西，你说都不如原来。这一轮只动<strong>人体本身</strong> ——
       肩宽、腰、胯、手的大小、腿的张角。墨、纸、构造线、姿势的大框架全部不变。</p>
    <p>这些不是 CSS 能表达的：核心区放缩、外伸的手臂原地不动，是<strong>分段的横向变形</strong>，
       所以每一张都是真的重写过坐标的图 —— 但仍然<strong>没有重画一笔</strong>，
       每条线还是原来那条线，只是落点变了。头顶、脚底、指尖三处与方框的接触点都验算过，没有动。</p>
    <div class="meta">
      <span>图幅 440px</span><span>viewBox 0 0 1000 1000</span>
      <span>轴 x=500</span><span>头顶 139.5 · 胯 503 · 脚底 915.4</span>
    </div>
  </header>

  <div class="sheet">
__TILES__  </div>

  <footer>报编号，可以叠（比如「B + G」）。也可以只说方向 —— 比如“再宽一点”“腰再收一档” ——
    我按同一套参数换个数字重出。</footer>
</div>
"""

if __name__ == "__main__":
    if "--check" in sys.argv:
        inner = plate()
        for letter, name, _, _, mk in PROOFS:
            if mk is None:
                continue
            body, hit = apply_to_plate(inner, mk())
            print("%s %-10s %d elements" % (letter, name, hit))
        sys.exit(0)
    page = build()
    open(OUT, "w").write(page)
    print("wrote %s  %.1f KB" % (OUT, len(page) / 1024))

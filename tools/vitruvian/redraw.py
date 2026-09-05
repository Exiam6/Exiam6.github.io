#!/usr/bin/env python3
"""Redraw a few strokes of the plate — the first time anything here is DRAWN.

Every earlier round moved coordinates that were already on the page.  This one
deletes elements and puts new ones in their place, using pen.py, which speaks
the plate's own vocabulary: contours are closed variable-width ribbons (an
outer and an inner loop, filled even-odd), values are discrete hatch strokes,
joints are pinned rings.  Nothing else about the figure changes — the H
proportions stay exactly as bake.py left them.

    python3 tools/vitruvian/redraw.py --crops   # close looks, before/after
    python3 tools/vitruvian/redraw.py           # -> tools/vitruvian/redraw.html
"""
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pen  # noqa: E402
from anatomy import plate  # noqa: E402

ANAT = os.path.join(HERE, "anatomy.json")
BAKED = os.path.join(HERE, "baked.svgfrag")        # the plate BEFORE any redraw
ANAT_BAKED = os.path.join(HERE, "anatomy_baked.json")
AXIS = 500.0
GROUND = 915.4        # the square's bottom line — the feet stand on it

ELEMS = re.compile(r"<(?:path|circle)\b[^>]*>")


USE_LIVE = False      # set while --apply works on index.html as it stands now


def base_plate():
    """The plate these redraws were authored against.

    Once --apply has run, index.html is no longer that plate: the elements the
    sheet deletes are gone and every index below them has shifted.  So the
    proof sheet rebuilds from the H-baked copy bake.py left behind, which is
    exactly the state the redraws were measured on.
    """
    html = open(os.path.join(HERE, "..", "..", "index.html")).read()
    if 'data-redraw=' in html and not USE_LIVE:
        return open(BAKED).read()
    return plate()


def anat_path():
    """Boxes for whichever plate base_plate() returns."""
    html = open(os.path.join(HERE, "..", "..", "index.html")).read()
    if 'data-redraw=' not in html or USE_LIVE:
        return ANAT           # anatomy.json always measures index.html as it is
    if not os.path.exists(ANAT_BAKED):
        import anatomy
        anatomy.SCRATCH = os.environ.get("SCRATCH", "/tmp")
        tagged, count = anatomy.tag(open(BAKED).read())
        rows = anatomy.measure(tagged, count)
        json.dump([{"i": r[0], "layer": r[1], "x": r[2], "y": r[3],
                    "w": r[4], "h": r[5]} for r in rows], open(ANAT_BAKED, "w"))
        print("measured the pre-redraw plate -> %s (%d elements)"
              % (os.path.basename(ANAT_BAKED), len(rows)))
    return ANAT_BAKED


def boxes():
    return {e["i"]: e for e in json.load(open(anat_path()))}


def in_box(B, x0, x1, y0, y1):
    """Every element whose bounding box lies WHOLLY inside the box.

    Wholly, not centred: a contour that continues out of the region — the
    shin running into the foot, say — must survive, or the redraw tears the
    drawing open somewhere the eye will find it.
    """
    return {i for i, e in B.items()
            if e["layer"] != "vm-geom" and e["x"] >= x0 and e["x"] + e["w"] <= x1
            and e["y"] >= y0 and e["y"] + e["h"] <= y1}


def both_sides(B, x0, x1, y0, y1):
    """The box and its mirror about the body axis — a redraw stays symmetric."""
    return in_box(B, x0, x1, y0, y1) | in_box(B, 2 * AXIS - x1, 2 * AXIS - x0, y0, y1)


class Splice:
    """Delete elements by index, add new ones into the layer groups."""

    def __init__(self, inner):
        self.inner = inner
        self.drop = set()
        self.add = {"l-deep": [], "l-shade": [], "l-mech": [], "l-ink": []}

    def draw(self, pen_obj):
        for layer, cls in ((pen_obj.DEEP, "l-deep"), (pen_obj.HATCH, "l-shade"),
                           (pen_obj.MECH, "l-mech"), (pen_obj.INK, "l-ink")):
            self.add[cls] += layer.paths

    def render(self):
        n = [0]

        def sub(m):
            i = n[0]
            n[0] += 1
            return "" if i in self.drop else m.group(0)

        out = ELEMS.sub(sub, self.inner)
        for cls, paths in self.add.items():
            if not paths:
                continue
            # the layer groups are siblings; append just before each one closes
            pat = re.compile(r'(<g class="%s"[^>]*>)(.*?)(</g>)' % cls, re.S)
            m = pat.search(out)
            assert m, "layer %s not found" % cls
            out = out[:m.end(2)] + "\n" + "\n".join(paths) + out[m.end(2):]
        return out


# ---- 1. the feet of the spread legs ---------------------------------------
# The old foot was a single closed loop: the shin's end swelled into a paddle
# and stopped.  No ankle, no sole, no toe — at 440px it reads as an oar.
FOOT_BOX = (225.0, 305.0, 815.0, 925.0)     # hatch, mech, and the paddle itself
SHIN_END = (277.0, 863.0)                   # where the shin's contour closes


def mirror(pts):
    return [(2 * AXIS - x, y) for x, y in pts]


def foot(P, side=1):
    """One spread-leg foot, in profile.  side=1 is the viewer's left.

    Drawn the way the plate draws every other limb: ONE open contour whose two
    ends are buried inside the shin's own fill, so there is no seam to hide —
    the same trick the old paddle used, only now the line bends at the ankle
    instead of running on and stopping.
    """
    def X(pts):
        return pts if side == 1 else mirror(pts)

    # instep down to the toe, along the sole, up the heel — ends buried at y843
    # the sole sits so that the contour's OUTER edge lands on the ground line,
    # not its centre — the old paddle bottomed out at 920.1 and so must this
    edge = [(266, 843), (261, 862), (252, 880), (243, 895), (236, 905),
            (233, 912), (241, 916), (254, 917), (267, 916), (277, 911),
            (283, 901), (288, 881), (290, 862), (289, 843)]
    pen.ribbon(pen.spline(X(edge)), 6.1, P.INK, taper=False, shade=1, amp=0.4)

    # the ankle: a pinned ring, the joint the knees and elbows already use,
    # sitting exactly where the contour's two ends run into the shin
    A = X([(278.0, 848.0)])[0]
    pen.circle(A, 11.5, 5.4, P.INK)
    pen.hatch(pen.circle_pts(A, 8.0), 42, 3.4, 1.9, P.DEEP)

    # where the toes break off — one short stroke, square to the sole
    pen.ribbon(pen.spline(X([(238, 904), (240, 910), (241, 914)])), 2.9, P.INK,
               taper=False, amp=0.2)

    # a little value under the instep: straight strokes, no bow — a bowed
    # hatch at this size reads as a row of arrowheads, not as shading
    pen.hatch(X([(249, 884), (261, 872), (276, 880), (271, 898), (255, 897)]),
              58, 6.4, 1.8, P.HATCH)


def redraw_feet(sp):
    B = boxes()
    sp.drop |= both_sides(B, *FOOT_BOX)
    P = pen.Pen()
    foot(P, +1)
    foot(P, -1)
    sp.draw(P)
    return "两只张开的脚：踝关节改成与膝、肘同一种销钉圆环，脚掌给了脚背、脚底和一条趾线，踩在方框底线上"


# ---- 2. the pin inside the right hip's ring --------------------------------
# The ring is fine — it is the same pinned joint the knees use.  What sat
# inside it was a crude lozenge that read as a cylinder poking out of the hip.
HIP_PIN_BOX = (538.0, 559.0, 487.0, 506.0)
HIP_RING = (548.5, 496.0)


def redraw_hip(sp):
    B = boxes()
    sp.drop |= in_box(B, *HIP_PIN_BOX)
    P = pen.Pen()
    pen.circle(HIP_RING, 6.2, 3.0, P.INK)          # the boss
    pen.ribbon(pen.spline([(541.5, 490.5), (548.5, 496.0), (555.5, 501.5)]),
               2.2, P.MECH, taper=False, amp=0.2)   # and its axle
    sp.draw(P)
    return "右胯那根突出的圆柱换成销钉座：环内一个同心的轴套加一根轴线，和膝、肘同一种词汇"


# ---- 3. the exposed half of the spine --------------------------------------
# Five vertebrae, no two the same size, and the gaps run 34, 35, 37, 23 — at
# 440px the column reads as a bag of beans rather than as a spine.
SPINE_DROP = [461, 462, 463, 464, 465]
SPINE_X = 487.5


def redraw_spine(sp):
    sp.drop |= set(SPINE_DROP)
    P = pen.Pen()
    # six positions keep the rhythm the redraw set, but only the top four are
    # drawn: below that the abdomen's shell is closed over the spine, so those
    # vertebrae cannot be seen from outside the cavity
    top, bot, n, shown = 336.0, 466.0, 6, 4
    for k in range(shown):
        y = top + (bot - top) * k / (n - 1)
        pen.ellipse((SPINE_X, y), 15.5, 8.2, 0.0, 4.2, P.INK)
        pen.ribbon(pen.spline([(SPINE_X - 5, y), (SPINE_X + 5, y)]),
                   1.8, P.MECH, taper=False, amp=0.15)
    sp.draw(P)
    return ("露出来的那半根脊椎：五节大小不一、间距 34/35/37/23，改成等大等距，露出四节，"
            "每节中间一根销；最下面两节被腹腔的壳挡住，不再画出来")


# ---- 4. the fingers --------------------------------------------------------
# Four blunt bars of equal width per hand.  Rather than author twenty new
# fingers by hand, each old contour is MEASURED — its own axis, length and
# width — and redrawn as the same finger with a taper and a knuckle, so all
# four hands keep their spread, their reach, and their fingertips.  The
# fingertips matter: the middle one IS the square's left edge.
HAND_BOXES = [(105.0, 210.0, 250.0, 332.0), (132.0, 252.0, 128.0, 228.0)]

NUMPAIR = re.compile(r"(-?\d+(?:\.\d+)?)[ ,]+(-?\d+(?:\.\d+)?)")


def path_points(el):
    d = re.search(r'\bd="([^"]+)"', el).group(1)
    return [(float(a), float(b)) for a, b in NUMPAIR.findall(d.replace("L", " ")
                                                             .replace("M", " ")
                                                             .replace("Z", " "))]


def principal(pts):
    """Mean, unit long axis, and the half-extents along and across it."""
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts) / n
    syy = sum((p[1] - my) ** 2 for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts) / n
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    u = (math.cos(th), math.sin(th))
    v = (-u[1], u[0])
    ts = [(p[0] - mx) * u[0] + (p[1] - my) * u[1] for p in pts]
    ws = [(p[0] - mx) * v[0] + (p[1] - my) * v[1] for p in pts]
    return (mx, my), u, v, (min(ts), max(ts)), max(abs(min(ws)), abs(max(ws)))


def digit(P, root, tip, hr, ht, w=4.3):
    """One finger: an open contour that runs into the palm at both ends."""
    ux = tip[0] - root[0]
    uy = tip[1] - root[1]
    ln = math.hypot(ux, uy) or 1.0
    u = (ux / ln, uy / ln)
    v = (-u[1], u[0])
    top, bot = [], []
    for k in range(9):
        s = k / 8.0
        h = hr + (ht - hr) * (s ** 0.85)
        p = (root[0] + u[0] * ln * s, root[1] + u[1] * ln * s)
        top.append((p[0] + v[0] * h, p[1] + v[1] * h))
        bot.append((p[0] - v[0] * h, p[1] - v[1] * h))
    # the fingertip: a half turn from the +v edge, through the direction of
    # travel, to the -v edge.  Sweeping out and back on the SAME side folds
    # the contour into a zigzag, which is what the first attempt did.
    cap = [(tip[0] + ht * (math.cos(a) * v[0] + math.sin(a) * u[0]),
            tip[1] + ht * (math.cos(a) * v[1] + math.sin(a) * u[1]))
           for a in (0.42, 0.84, 1.26, 1.5708, 1.88, 2.30, 2.72)]
    pen.ribbon(pen.spline(top + cap + bot[::-1]), w, P.INK, taper=False,
               shade=1, amp=0.3)
    # one short crease inside the finger, well clear of both edges: a stroke
    # that reaches the contour reads as a rung, not as a knuckle
    k = (root[0] + u[0] * ln * 0.34, root[1] + u[1] * ln * 0.34)
    pen.ribbon(pen.spline([(k[0] + v[0] * hr * .45, k[1] + v[1] * hr * .45),
                           (k[0] - v[0] * hr * .45, k[1] - v[1] * hr * .45)]),
               1.5, P.MECH, taper=False, amp=0.1)


def finger_ids(B, els):
    out = []
    for x0, x1, y0, y1 in HAND_BOXES:
        for bx in ((x0, x1), (2 * AXIS - x1, 2 * AXIS - x0)):
            for i in in_box(B, bx[0], bx[1], y0, y1):
                e = B[i]
                if e["layer"] != "l-ink":
                    continue
                _, _, _, (t0, t1), hw = principal(path_points(els[i]))
                if t1 - t0 > 34 and hw > 3 and (t1 - t0) / (2 * hw) > 1.9:
                    out.append(i)
    return out


def redraw_hands(sp):
    B = boxes()
    els = ELEMS.findall(sp.inner)
    ids = finger_ids(B, els)
    sp.drop |= set(ids)
    P = pen.Pen()
    for i in ids:
        c, u, v, (t0, t1), hw = principal(path_points(els[i]))
        a = (c[0] + u[0] * t0, c[1] + u[1] * t0)
        b = (c[0] + u[0] * t1, c[1] + u[1] * t1)
        # the root is the end nearer the middle of the figure
        far = lambda p: (p[0] - AXIS) ** 2 + (p[1] - 500.0) ** 2
        root, tip = (a, b) if far(a) < far(b) else (b, a)
        d = math.hypot(tip[0] - root[0], tip[1] - root[1]) or 1.0
        ux, uy = (tip[0] - root[0]) / d, (tip[1] - root[1]) / d
        root = (root[0] - ux * 3.0, root[1] - uy * 3.0)      # bury it in the palm
        # the tip measured off the old outline is its OUTER edge; the new
        # contour adds a cap of ht and half a pen width on top of whatever
        # point it is given, so pull the centre back by exactly that much —
        # otherwise every fingertip creeps past the square's edge
        ht = hw * 0.78
        back = ht + 4.3 / 2 - 1.0        # the pen's own wobble eats about a unit
        digit(P, root, (tip[0] - ux * back, tip[1] - uy * back), hw * 1.0, ht)
    sp.draw(P)
    return ("四只手的手指：每根都按原来的轴线、长度和落点重画，加了从指根到指尖的收笔和一道指节纹 —— "
            "中指的指尖仍然落在方框左右边线上，%d 根" % len(ids))


PROOFS = [
    ("B", "脚", redraw_feet, "已采用"),
    ("C", "胯", redraw_hip, "已采用"),
    ("D", "脊椎", redraw_spine, "已采用"),
    ("E", "手指", redraw_hands, "未采用"),
]


def variant(fns, seed=11):
    random.seed(seed)                       # the pen wobbles; keep it repeatable
    sp = Splice(base_plate())
    notes = [fn(sp) for fn in fns]
    return sp.render(), notes, len(sp.drop), sum(len(v) for v in sp.add.values())


def ids(body, n):
    """Each tile carries a full copy of the plate, so the halo's target id
    has to be unique per tile or every clone renders the first tile's ink."""
    return body.replace('id="vm-ink"', 'id="vm-ink-%d"' % n) \
               .replace('href="#vm-ink"', 'href="#vm-ink-%d"' % n)


def build_sheet():
    tiles = []
    body = base_plate()
    tiles.append(TILE % ("A", "重画之前", ids(body, 0), "A", "", "重画之前",
                         "一笔没重画，作参照", "删 0 · 增 0"))
    for n, (letter, name, fn, tag_) in enumerate(PROOFS, 1):
        body, notes, drop, add = variant([fn])
        mark = ('<span class="tag tag--%s">%s</span>'
                % ("yes" if tag_ == "已采用" else "no", tag_)) if tag_ else ""
        tiles.append(TILE % (letter, name, ids(body, n), letter, mark, name,
                             notes[0], "删 %d 个元素 · 增 %d 笔" % (drop, add)))
    body, notes, drop, add = variant([p[2] for p in PROOFS])
    tiles.append(TILE % ("F", "四处一起", ids(body, len(PROOFS) + 1), "F", "",
                         "四处一起", "把 B–E 全叠上，包括没被采用的 C 和 E",
                         "删 %d 个元素 · 增 %d 笔" % (drop, add)))
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
          <p class="desig"><span class="letter">%s</span>%s</p>
          <h2>%s</h2>
          <p class="note">%s</p>
          <p class="spec">%s</p>
        </figcaption>
      </figure>
"""


PAGE = """<title>维特鲁威人重画四处</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --paper:#fefcf8; --paper-edge:#e7dccb; --sang:#8a6a4f; --hot:#a8552b;
  --ground:#efe7da; --panel:#f7f1e6; --text:#3b332a; --text2:#6d6055; --rule:#ddd0bc;
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
            box-shadow:inset 0 1px 0 rgba(255,255,255,.9), 0 1px 2px rgba(59,43,26,.10);
            padding:10px; display:flex; justify-content:center; }
.pl{ display:block; width:100%; max-width:440px; height:auto; color:var(--sang); }
figcaption{ padding:13px 2px 12px; }
.desig{ margin:0 0 3px; }
.desig{ display:flex; align-items:center; gap:9px; }
.letter{ font-family:var(--mono); font-size:12px; font-weight:500;
         letter-spacing:.18em; color:var(--hot); }
.tag{ font-family:var(--mono); font-size:10px; letter-spacing:.1em;
      padding:2px 7px; border:1px solid var(--hot); color:var(--hot); }
.tag--no{ border-color:var(--rule); color:var(--text2); }
h2{ font-size:20px; font-weight:500; margin:0 0 4px; letter-spacing:.01em; }
.note{ margin:0 0 9px; font-size:15px; color:var(--text2); }
.spec{ margin:0; font-family:var(--mono); font-size:11.5px; color:var(--text2);
       border-top:1px solid var(--rule); padding-top:9px;
       font-variant-numeric:tabular-nums; }
footer{ margin-top:44px; border-top:1px solid var(--rule); padding-top:16px;
        color:var(--text2); font-size:15px; max-width:64ch; }
.pl .vm-geom{ opacity:.55; }
.pl .l-deep{ opacity:.6; }
.pl .l-shade{ opacity:.7; }
.pl .l-halo{ fill:none; stroke:#fff; stroke-width:2.6; stroke-linejoin:round; }
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">Research map · 重画 A–F</p>
    <h1>这一轮真的动了笔</h1>
    <p>体型保持 <strong>H</strong> 不动。前面每一轮都只是搬动已经在纸上的线，这一轮是<strong>删掉一些笔、
       补上另一些</strong> —— 用的还是这块版自己的词汇：轮廓是变宽度的闭合带，明暗是一根根排线，
       关节是带销的圆环。</p>
    <p>每张只改一处，<strong>F</strong> 是四处一起。还是按主页真实的 440px 出图。</p>
    <p><strong>B</strong> 和 <strong>D</strong> 已经按你的意见改定并进了 index.html：脚的轮廓笔宽
       从 5.2 加到 6.1，脊椎最下面两节被腹腔的壳挡住、不再画出来（六个位置只露四节）。
       <strong>C</strong> 也已采用；只有 <strong>E</strong>（手指）按你的意思不动，留在这里作记录。</p>
    <div class="meta">
      <span>图幅 440px</span><span>viewBox 0 0 1000 1000</span>
      <span>笔法沿用 tools/vitruvian/pen.py</span>
    </div>
  </header>

  <div class="sheet">
__TILES__  </div>

  <footer>线上文件已是 B + C + D：删 19 个元素、增 32 笔。接触点验过 ——
    指尖 x=112.5 精确落在方框左边线，头顶 137.6 不变，脚底 920.5（加粗的笔自己占了 0.4 个单位）。</footer>
</div>
"""

BY_LETTER = {"B": redraw_feet, "C": redraw_hip, "D": redraw_spine,
             "E": redraw_hands}


def apply_to_index(letters):
    """Splice the chosen redraws into index.html — each letter at most once.

    Everything here selects elements GEOMETRICALLY, so a second round can be
    applied on top of a first: what it must not use is the pre-redraw boxes,
    since those indices moved when the first round deleted elements.  Hence
    USE_LIVE — apply always reads index.html and anatomy.json as they stand.
    """
    global USE_LIVE
    USE_LIVE = True
    idx = os.path.join(HERE, "..", "..", "index.html")
    html = open(idx).read()
    m = re.search(r'<svg class="rm-fig__svg"[^>]*>', html)
    assert m, "figure not found"
    done = re.search(r'data-redraw="([^"]*)"', m.group(0))
    done = done.group(1) if done else ""
    dup = [c for c in letters if c in done]
    if dup:
        sys.exit("index.html already carries %s — nothing done" % ",".join(dup))

    body, notes, drop, add = variant([BY_LETTER[c] for c in letters])
    inner = plate()
    assert inner in html
    # the marker goes AFTER the class attribute: plate() and bake.py both
    # match on `<svg class="rm-fig__svg"`, and putting anything in front of
    # that silently breaks every tool in this directory
    mark = "".join(sorted(set(done + letters)))
    tag_ = (re.sub(r'data-redraw="[^"]*"', 'data-redraw="%s"' % mark, m.group(0))
            if done else
            m.group(0).replace('class="rm-fig__svg" ',
                               'class="rm-fig__svg" data-redraw="%s" ' % mark, 1))
    html = html.replace(m.group(0), tag_, 1)
    open(idx, "w").write(html.replace(inner, body, 1))
    print("wrote index.html — %d elements removed, %d strokes added" % (drop, add))
    for n in notes:
        print("  -", n)


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply_to_index(sys.argv[sys.argv.index("--apply") + 1].upper())
        sys.exit(0)
    if "--crops" in sys.argv:
        body, notes, drop, add = variant([p[2] for p in PROOFS])
        open(os.path.join(HERE, "redraw.svgfrag"), "w").write(body)
        print("dropped %d, added %d" % (drop, add))
        for n in notes:
            print("  -", n)
        sys.exit(0)
    page = build_sheet()
    open(os.path.join(HERE, "redraw.html"), "w").write(page)
    print("wrote redraw.html  %.1f KB" % (len(page) / 1024))

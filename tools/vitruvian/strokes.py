#!/usr/bin/env python3
"""Ten treatments of the MARK-MAKING, borrowed from other drawing traditions.

Nothing here moves the figure or redraws a part: every option changes how the
existing lines are laid down.  Two structural facts about this plate make most
of them one transform deep:

  * a contour is a closed BAND — an outer loop and an inner loop filled
    even-odd.  Drop the inner loop and the limb becomes a solid mass (the
    woodcut); stroke the band instead of filling it and every contour splits
    into two hairlines (the engineering drawing).
  * value is never a wash: it is discrete hatch strokes, each a short
    `m .. q ..` run.  Rotate each of those about its own centre and the plate
    acquires the strict 45° section hatch of a technical drawing; replace each
    with a row of zero-length segments and it becomes stipple.

    python3 tools/vitruvian/strokes.py      # -> tools/vitruvian/strokes.html
"""
import json
import math
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from anatomy import plate  # noqa: E402

OUT = os.path.join(HERE, "strokes.html")
ANAT = os.path.join(HERE, "anatomy.json")

NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")
ELEMS = re.compile(r"<(?:path|circle)\b[^>]*>")


def fmt(v):
    s = "%.1f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def subpaths(d):
    """[(points, closed)] in absolute coordinates, preserving quadratics as
    their endpoints only — every curve in this plate is a 2-4 unit hatch
    wiggle, so the control point is decoration at the scale we work at."""
    out, pts, cur, start, closed = [], [], (0.0, 0.0), (0.0, 0.0), False
    for k, m in enumerate(CMD.finditer(d)):
        cmd, vals = m.group(1), [float(n) for n in NUM.findall(m.group(2))]
        rel, up = cmd.islower(), cmd.upper()
        if up == "Z":
            if pts:
                out.append((pts, True))
            pts, cur = [], start
            continue
        if up in ("H", "V"):
            for v in vals:
                cur = ((v + (cur[0] if rel else 0), cur[1]) if up == "H"
                       else (cur[0], v + (cur[1] if rel else 0)))
                pts.append(cur)
            continue
        base = cur if not (k == 0 and rel) else (0.0, 0.0)
        step = 4 if up == "Q" else 2
        for i in range(0, len(vals), step):
            end = (vals[i + step - 2], vals[i + step - 1])
            p = (end[0] + base[0], end[1] + base[1]) if rel else end
            # ONLY the first pair after an M is a moveto; every pair after it
            # is an implicit lineto.  pen.py writes whole polygons that way
            # ("M100 200 105 210 ... Z"), so treating each pair as a new
            # subpath quietly deletes everything this project has drawn.
            if up == "M" and i == 0:
                if pts:
                    out.append((pts, False))
                    pts = []
                start = p
            pts.append(p)
            base = cur = p
    if pts:
        out.append((pts, False))
    return out


def emit(sub):
    parts = []
    for pts, closed in sub:
        if len(pts) < 2:
            continue
        parts.append("M" + "L".join("%s %s" % (fmt(x), fmt(y)) for x, y in pts)
                     + ("Z" if closed else ""))
    return "".join(parts)


# ---- the transforms --------------------------------------------------------
def simplify(pts, eps):
    """Douglas-Peucker: the fewest vertices that stay within eps of the line."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    worst, wi = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        dist = (abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / n if n
                else math.hypot(p[0] - a[0], p[1] - a[1]))
        if dist > worst:
            worst, wi = dist, i
    if worst <= eps:
        return [a, b]
    return simplify(pts[:wi + 1], eps)[:-1] + simplify(pts[wi:], eps)


def chaikin(pts, closed, rounds=2):
    for _ in range(rounds):
        out = []
        seq = pts + [pts[0]] if closed else pts
        for a, b in zip(seq, seq[1:]):
            out.append((a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25))
            out.append((a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75))
        pts = out
    return pts


def tremor(pts, amp, wave=17.0):
    out, s = [], 0.0
    ph = random.random() * 6.283
    for i, p in enumerate(pts):
        if i:
            s += math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        k = amp * (math.sin(s / wave + ph) + 0.5 * math.sin(s / (wave * 2.7) + ph * 2))
        out.append((p[0] + nx * k, p[1] + ny * k))
    return out


def realign(pts, deg):
    """Turn one hatch stroke about its own centre onto a fixed angle, keeping
    its length — the discipline of a section hatch, from the same pen."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    a, b = pts[0], pts[-1]
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    u = (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
    return [(cx - u[0] * ln / 2, cy - u[1] * ln / 2),
            (cx + u[0] * ln / 2, cy + u[1] * ln / 2)]


def stipple(pts, step=3.4):
    """A run of dots along the stroke.  A zero-length segment under
    stroke-linecap:round IS a dot, so this stays one path."""
    out, carry = [], 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        t = carry
        while t < seg:
            f = t / seg if seg else 0
            p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            out.append(([p, p], False))
            t += step
        carry = t - seg
    return out


HATCH = ("l-deep", "l-shade")


def layers():
    return {e["i"]: e["layer"] for e in json.load(open(ANAT))}


def transform(inner, fn):
    """Rewrite each element through fn(layer, subpaths) -> subpaths or None."""
    L = layers()
    n = [0]

    def sub(m):
        i = n[0]
        n[0] += 1
        el = m.group(0)
        layer = L.get(i, "")
        if layer == "vm-geom" or ' d="' not in el:
            return el
        d = re.search(r'\bd="([^"]+)"', el).group(1)
        new = fn(layer, subpaths(d))
        if new is None:
            return el
        return re.sub(r'\bd="([^"]+)"', lambda _: 'd="%s"' % emit(new), el)

    return ELEMS.sub(sub, inner)


def each(sub, f, layers_=None):
    return [(f(pts, closed), closed) for pts, closed in sub] if layers_ is None \
        else sub


# ---- the ten treatments ----------------------------------------------------
def t_facet(layer, sub):
    return [(simplify(pts, 5.0), c) for pts, c in sub]


def t_solid(layer, sub):
    return sub[:1] if layer == "l-ink" else sub          # drop the inner loop


def t_section(layer, sub):
    if layer not in HATCH:
        return sub
    return [(realign(pts, 45.0), False) for pts, c in sub if len(pts) > 1]


def t_stipple(layer, sub):
    if layer not in HATCH:
        return sub
    out = []
    for pts, c in sub:
        out += stipple(pts)
    return out


def t_tremor(layer, sub):
    return [(tremor(pts, 1.7), c) for pts, c in sub]


def t_smooth(layer, sub):
    out = []
    for pts, c in sub:
        p = simplify(pts, 1.4)
        out.append((chaikin(p, c) if len(p) > 3 else p, c))
    return out


def t_none(layer, sub):
    return sub


PROOFS = [
    ("A", "现在这版", None, "", "线上这一版，作参照", "—"),
    ("B", "构成主义 · 折线化", t_facet, "",
     "每条轮廓用 Douglas-Peucker 压到 5 个单位的容差内：曲线全部塌成折线，"
     "人形变成一台由平面和棱切出来的机器。罗琴科画机械的办法",
     "全部轮廓 · 容差 5"),
    ("C", "技术制图 · 双线", t_smooth, "st-wire",
     "不再填充轮廓带，改成描它的边 —— 每条轮廓于是裂成两根等宽发丝线，"
     "明暗全部关掉，手抖也先压掉（不然描边会把两条抖动的边都画出来，像涂鸦）。"
     "这是 ГОСТ 那套工程图的读法：只有尺寸，没有光",
     "l-ink 描边 1.1 · 先平滑 · 无明暗"),
    ("E", "剖面线 · 严格 45°", t_section, "",
     "每一根排线绕自己的中点转到 45°，长度不变。手绘的乱向排线变成制图规范里的剖面线 —— "
     "同一支笔，换一套纪律",
     "l-deep/l-shade 全部 → 45°"),
    ("F", "点刻", t_stipple, "",
     "排线换成沿原路径排布的点，间距 3.4。铜版点刻的做法，灰阶来自密度而不是线",
     "排线 → 点 · 步长 3.4"),
    ("I", "蚀刻 · 颤笔", t_tremor, "",
     "所有线沿法线加一层振幅 1.7 的低频抖动。铜版蚀刻针在蜡上走过的那种不稳",
     "全部线 · 振幅 1.7"),
    ("J", "流线 · 平滑", t_smooth, "",
     "反过来：先把手抖压掉（容差 1.4），再 Chaikin 磨两轮。线变得工业、连续，"
     "装饰艺术那种流线感",
     "容差 1.4 + Chaikin ×2"),
    ("K", "透视机壳", t_smooth, "st-ghost",
     "外壳退成发丝线，机构层反过来提到最前、上满墨。像隔着玻璃看里面的机器",
     "l-ink 描边 · l-mech 加重"),
]


def build():
    inner = plate()
    tiles = []
    for n, (letter, name, fn, cls, note, spec) in enumerate(PROOFS):
        random.seed(23)                       # tremor must be repeatable
        body = inner if fn is None else transform(inner, fn)
        body = body.replace('id="vm-ink"', 'id="vm-ink-%d"' % n) \
                   .replace('href="#vm-ink"', 'href="#vm-ink-%d"' % n)
        esc = lambda t: t.replace('"', "&quot;")
        tiles.append(TILE % (cls, letter, esc(name), body, letter, name))
        print("  %s %-16s %d bytes" % (letter, name, len(body)))
    return PAGE.replace("__TILES__", "".join(tiles))


TILE = """      <figure class="proof">
        <div class="platemark">
          <svg class="pl %s" viewBox="106 132 790 794" fill="none" stroke="currentColor"
               stroke-linecap="round" stroke-linejoin="round" role="img"
               aria-label="%s 号试样：%s">
%s
          </svg>
          <figcaption><span class="letter">%s</span>%s</figcaption>
        </div>
      </figure>
"""

PAGE = """<title>维特鲁威人笔法</title>
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
*{ box-sizing:border-box; }
html,body{ height:100%; }
body{ margin:0; background:var(--rule); color:var(--text); font-family:var(--serif);
      -webkit-font-smoothing:antialiased; overflow:hidden; }

/* ---- ten plates, five across, filling the window ------------------
   No header, no page margin, and the viewBox is cropped to the square the
   figure is inscribed in — the drawing never uses the corners of the 1000
   unit box, and giving that margin back makes the body itself about a fifth
   larger in the same screen.  The 1px grid gap IS the rule between plates. */
.sheet{ height:100%; display:grid; gap:1px; background:var(--rule);
        grid-template-columns:repeat(4,1fr); grid-template-rows:repeat(2,1fr); }
.proof{ margin:0; min-width:0; min-height:0; display:flex; }
.platemark{ position:relative; flex:1 1 auto; min-width:0; min-height:0;
            background:var(--paper); display:flex;
            align-items:center; justify-content:center; overflow:hidden; }
.pl{ display:block; width:100%; height:auto; max-height:100%; color:var(--sang); }
figcaption{ position:absolute; left:8px; top:6px; display:flex; align-items:baseline;
            gap:6px; font-size:13px; color:var(--text2); pointer-events:none;
            text-shadow:0 0 3px var(--paper), 0 0 3px var(--paper); }
.letter{ font-family:var(--mono); font-size:11px; font-weight:500;
         letter-spacing:.14em; color:var(--hot); }

@media (max-width:1100px){
  body{ overflow:auto; }
  .sheet{ height:auto; grid-template-columns:repeat(2,1fr); grid-template-rows:none; }
  .platemark{ aspect-ratio:1; }
}

/* the plate's own inking, as index.html carries it */
.pl .vm-geom{ opacity:.55; }
.pl .l-deep{ opacity:.6; }
.pl .l-shade{ opacity:.7; }
.pl .l-halo{ fill:none; stroke:#fff; stroke-width:2.6; stroke-linejoin:round; }

/* ---- the treatments that are a way of INKING, not of drawing ---- */
/* C — stroke the ribbon instead of filling it: two hairlines per contour */
.st-wire .l-ink path{ fill:none; stroke:currentColor; stroke-width:1.1; }
.st-wire .l-deep, .st-wire .l-shade{ display:none; }
.st-wire .l-mech path{ fill:none; stroke:currentColor; stroke-width:1.1; }
.st-wire .l-halo{ display:none; }
.st-wire .vm-geom{ opacity:.75; }

/* D — solid masses: the halo would only outline them again */
.st-solid .l-deep, .st-solid .l-shade{ display:none; }
.st-solid .l-halo{ display:none; }



/* K — shells to hairline, works to full ink */
.st-ghost .l-ink path{ fill:none; stroke:currentColor; stroke-width:1; }
.st-ghost .l-halo{ display:none; }
.st-ghost .l-deep{ opacity:.18; }
.st-ghost .l-shade{ opacity:.22; }
.st-ghost .l-mech{ opacity:1; }
.st-ghost .l-mech path{ stroke-width:2.4; }
</style>

<div class="sheet">
__TILES__</div>
"""

if __name__ == "__main__":
    page = build()
    open(OUT, "w").write(page)
    print("wrote %s  %.1f KB" % (OUT, len(page) / 1024))

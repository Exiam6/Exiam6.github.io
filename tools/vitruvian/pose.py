#!/usr/bin/env python3
"""Build the proportion-proof sheet: the same drawing, the figure moved.

Nothing is redrawn.  Every element of the plate is classified into one of
three regions by the bounding boxes anatomy.py measured, and each region is
transformed by a CSS custom property — so, exactly as in proofs.py, one copy
of the drawing renders every variant through <use>.

The vertical moves use a piecewise-linear remap that is CONTINUOUS at the
hip: lengthening the legs about the feet line moves the hip up, and the
upper body is compressed about the crown by precisely the amount that lands
it on the same hip.  The crown stays on the square's top line and the feet
stay on its bottom line, so the Vitruvian contacts survive; an element that
straddles the seam is displaced by ~2 units at most (0.9px at 440px).

    python3 tools/vitruvian/pose.py     # -> tools/vitruvian/pose.html
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from anatomy import plate, tag, ELEM  # noqa: E402  (same indexing as anatomy.json)

OUT = os.path.join(HERE, "pose.html")
ANAT = os.path.join(HERE, "anatomy.json")

# ---- the canon, read off the plate -----------------------------------------
CROWN = 139.5     # top of the head — sits on the square's top line
HIP = 515.0       # where the thigh paths begin
FEET = 915.4      # the square's bottom line
NECK = (500.0, 252.0)   # the neck joint: pivot for everything head-shaped


def regions():
    """index -> 'head' | 'upper' | 'lower' | None (the canon geometry)."""
    out = {}
    for e in json.load(open(ANAT)):
        if e["layer"] == "vm-geom":
            continue                      # the square and circle never move
        cx, cy = e["x"] + e["w"] / 2, e["y"] + e["h"] / 2
        if cy < 248 and 430 < cx < 570:
            out[e["i"]] = "head"          # a tight cluster, x458-542 y139-254
        else:
            out[e["i"]] = "upper" if cy < HIP else "lower"
    return out


def classify(inner, reg):
    """Replace each data-i with the region class it belongs to."""
    def sub(m):
        r = reg.get(int(m.group(1)))
        return ' class="r-%s"' % r if r else ""
    return re.sub(r' data-i="(\d+)"', sub, inner)


# ---- transforms, with the pivot baked into a translate ---------------------
# transform-origin is 0 0 everywhere so that the head's transform can be
# composed onto the upper body's without the two origins fighting.
def scale_y(s, pivot):
    return "translate(0px,%.3fpx) scaleY(%.5f)" % (pivot * (1 - s), s)


def scale_x(s, pivot=500.0):
    return "translate(%.3fpx,0px) scaleX(%.5f)" % (pivot * (1 - s), s)


def scale_at(s, pt):
    return "translate(%.3fpx,%.3fpx) scale(%.5f)" % (pt[0] * (1 - s), pt[1] * (1 - s), s)


def rotate_at(deg, pt):
    return "translate(%.1fpx,%.1fpx) rotate(%.2fdeg) translate(%.1fpx,%.1fpx)" % (
        pt[0], pt[1], deg, -pt[0], -pt[1])


def legs(s_low):
    """Legs by s_low about the feet; upper body compensates about the crown."""
    hip = FEET - (FEET - HIP) * s_low
    s_up = (hip - CROWN) / (HIP - CROWN)
    return {"lower": scale_y(s_low, FEET), "upper": scale_y(s_up, CROWN)}, hip, s_up


# ---- the proofs ------------------------------------------------------------
def build_proofs():
    P = []

    def add(letter, name, note, tvars, spec, tag_=None, tagtext=None):
        P.append((letter, name, note, tvars, spec, tag_, tagtext))

    add("A", "现在这版", "人形一笔没动，作参照", {}, "—", "line", "基准")

    v, hip, s_up = legs(1.03)
    add("H", "腿长一档", "腿加长 3%，上身等量压缩，头顶和脚底仍贴着方框",
        v, "腿 ×1.03 · 上身 ×%.3f · 胯 %.0f→%.0f" % (s_up, HIP, hip))

    v, hip, s_up = legs(1.06)
    add("I", "腿长两档", "同样的做法推到 6%，机械感更强、更不像人",
        v, "腿 ×1.06 · 上身 ×%.3f · 胯 %.0f→%.0f" % (s_up, HIP, hip))

    v, hip, s_up = legs(0.97)
    add("M", "上身长一档", "反方向：躯干拉长 3%，腿相应收短，更敦实",
        v, "腿 ×0.97 · 上身 ×%.3f · 胯 %.0f→%.0f" % (s_up, HIP, hip))

    add("J", "头小一圈", "头整体缩到 0.88，绕颈关节缩；头顶会离开方框顶线约 14",
        {"head": scale_at(0.88, NECK)}, "头 ×0.88 @颈")

    add("K", "头窄一圈", "只压横向，头顶和脖子的接点都不动 —— 最保守的一版",
        {"head": scale_x(0.88)}, "头 ×0.88 仅横向")

    add("L", "头微侧", "绕颈关节转 4°，自动机偏头看向左手；纵向几乎不掉",
        {"head": rotate_at(-4, NECK)}, "头 转 −4° @颈")

    v, hip, s_up = legs(1.04)
    v = dict(v, head=scale_at(0.90, NECK))
    add("N", "头小 + 腿长", "两个方向叠在一起，最远离人体、最像器械的一版",
        v, "腿 ×1.04 · 上身 ×%.3f · 头 ×0.90" % s_up)

    return P


ALIAS = {"head": "--t-head", "upper": "--t-upper", "lower": "--t-lower"}


def tile(letter, name, note, tvars, spec, tag_, tagtext):
    style = "; ".join("%s:%s" % (ALIAS[k], v) for k, v in tvars.items())
    tagmark = ('<span class="tag tag--%s">%s</span>' % (tag_, tagtext)) if tag_ else ""
    return """      <figure class="proof">
        <div class="platemark">
          <svg class="pl" viewBox="0 0 1000 1000" style="%s" role="img"
               aria-label="%s 号试样：%s">
            <use href="#plate"/>
          </svg>
        </div>
        <figcaption>
          <p class="desig"><span class="letter">%s</span>%s</p>
          <h2>%s</h2>
          <p class="note">%s</p>
          <p class="spec">%s</p>
        </figcaption>
      </figure>
""" % (style, letter, name, letter, tagmark, name, note, spec)


PAGE = """<title>维特鲁威人体态七版</title>
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

header{ max-width:62ch; }
.eyebrow{ font-family:var(--mono); font-size:11px; letter-spacing:.16em;
          text-transform:uppercase; color:var(--text2); margin:0 0 14px; }
h1{ font-size:clamp(30px,4.4vw,44px); font-weight:500; line-height:1.12;
    letter-spacing:.01em; margin:0 0 14px; text-wrap:balance; }
header p{ margin:0 0 10px; color:var(--text2); }
header p strong{ color:var(--text); font-weight:600; }
.meta{ font-family:var(--mono); font-size:12px; color:var(--text2);
       border-top:1px solid var(--rule); margin-top:26px; padding-top:12px;
       display:flex; flex-wrap:wrap; gap:6px 22px; font-variant-numeric:tabular-nums; }

/* two up at most: judged at the 440px the homepage actually draws it at */
.sheet{ display:grid; gap:26px; margin-top:34px;
        grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); }
.proof{ margin:0; background:var(--panel); border:1px solid var(--rule);
        padding:14px 14px 4px; display:flex; flex-direction:column; }
.platemark{ background:var(--paper); border:1px solid var(--paper-edge);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.9),
                       0 1px 2px rgba(59,43,26,.10);
            padding:16px 10px; display:flex; justify-content:center; }
.pl{ display:block; width:100%; max-width:440px; height:auto; color:var(--sang); }

figcaption{ padding:13px 2px 12px; }
.desig{ display:flex; align-items:center; gap:9px; margin:0 0 3px; }
.letter{ font-family:var(--mono); font-size:12px; font-weight:500;
         letter-spacing:.18em; color:var(--hot); }
.tag{ font-family:var(--mono); font-size:10px; letter-spacing:.1em;
      text-transform:uppercase; padding:2px 7px; border:1px solid var(--hot);
      color:var(--hot); }
h2{ font-size:20px; font-weight:500; margin:0 0 4px; letter-spacing:.01em; }
.note{ margin:0 0 9px; font-size:15px; color:var(--text2); }
.spec{ margin:0; font-family:var(--mono); font-size:11.5px; color:var(--text2);
       border-top:1px solid var(--rule); padding-top:9px;
       font-variant-numeric:tabular-nums; }

footer{ margin-top:44px; border-top:1px solid var(--rule); padding-top:16px;
        color:var(--text2); font-size:15px; max-width:62ch; }

/* ---- the inking: the two tweaks already accepted, held constant --------- */
.vm-geom{ opacity:.55; }
.l-deep{ opacity:.6; }
.l-shade{ opacity:.7; }
.l-halo{ fill:none; stroke:#fff; stroke-width:2.6; stroke-linejoin:round; }

/* ---- the moving parts --------------------------------------------------
   Pivots are baked into each translate, so transform-origin stays at 0 0 and
   the head's own move composes cleanly onto whatever the upper body is doing. */
.r-upper, .r-lower, .r-head{ transform-box:view-box; transform-origin:0 0; }
.r-upper{ transform:var(--t-upper,translate(0px)); }
.r-lower{ transform:var(--t-lower,translate(0px)); }
.r-head { transform:var(--t-upper,translate(0px)) var(--t-head,translate(0px)); }
</style>

<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<g id="plate" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
__PLATE__
</g></defs></svg>

<div class="wrap">
  <header>
    <p class="eyebrow">Research map · 试样 H–N</p>
    <h1>同一张画，人形动一点</h1>
    <p>还是<strong>一笔没重画</strong>：每条线都是原图的线，只是整块整块地挪。
       上墨方式全部固定成你已经收下的那一版（淡排线 + 光晕），所以这一轮唯一的变量是人形本身。</p>
    <p>纵向的几版用了一个<strong>在胯部连续的分段缩放</strong>：腿绕脚底线加长多少，
       上身就绕头顶线等量压回去 —— 所以头顶仍然贴着方框顶线，脚底仍然贴着底线，
       维特鲁威的那几个接触点没有被破坏。</p>
    <div class="meta">
      <span>图幅 440px</span><span>头顶 y139.5</span><span>胯 y515</span>
      <span>脚底 y915.4</span><span>颈关节 500,252</span>
    </div>
  </header>

  <div class="sheet">
__TILES__  </div>

  <footer>老规矩，报编号，也可以拼：比如「K 的头 + H 的腿」。选定后我直接改 index.html。</footer>
</div>
"""

if __name__ == "__main__":
    inner, count = tag(plate())
    assert "<path class=" not in inner, "an element already carries a class"
    reg = regions()
    inner = classify(inner, reg)
    proofs = build_proofs()
    page = PAGE.replace("__PLATE__", inner).replace(
        "__TILES__", "".join(tile(*p) for p in proofs))
    open(OUT, "w").write(page)

    n = {}
    for r in reg.values():
        n[r] = n.get(r, 0) + 1
    print("wrote %s  %d bytes  %d proofs" % (OUT, len(page), len(proofs)))
    print("regions: " + ", ".join("%s %d" % kv for kv in sorted(n.items())))
    # seam check: both maps must agree at the hip, and stay close either side
    for s_low in (1.03, 1.06, 0.97):
        v, hip, s_up = legs(s_low)
        def up(y): return CROWN + (y - CROWN) * s_up
        def lo(y): return FEET - (FEET - y) * s_low
        print("  legs x%.2f -> hip %.1f | seam err at hip %.3f, "
              "40 above %.2f, 40 below %.2f"
              % (s_low, hip, abs(up(HIP) - lo(HIP)),
                 abs(up(HIP - 40) - lo(HIP - 40)), abs(up(HIP + 40) - lo(HIP + 40))))

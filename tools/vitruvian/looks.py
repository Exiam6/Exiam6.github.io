#!/usr/bin/env python3
"""Build the sheet of NON-geometric options: same drawing, same pose.

Everything here leaves the figure exactly where bake.py put it (proof H) and
changes something else — what is shown, what colour the works are inked in,
what the plate sits on, and what the plate does when you point at it.

The plate is lifted verbatim out of index.html into <defs> and pulled once
per option with <use>, as in proofs.py.  Two additions:

  * every element also carries a REGION class (r-legs / r-head / r-hand) and
    a LAYER class (k-deep / k-shade / k-mech / k-ink), so an option can
    address "the deep hatching in the legs" without an ancestor selector —
    those do not cross the <use> shadow boundary, compound ones on the
    element itself do.
  * the interactive options are driven from OUTSIDE the clone by setting a
    custom property on the host <svg>, which does inherit inward.

    python3 tools/vitruvian/looks.py     # -> tools/vitruvian/looks.html
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from anatomy import plate, tag  # noqa: E402

OUT = os.path.join(HERE, "looks.html")
ANAT = os.path.join(HERE, "anatomy.json")
HIP = 503.0                      # the BAKED frame — anatomy.json now measures the
HAND = (164.0, 292.0)            # shipped plate, and the hotspot moved with it


def classes():
    """index -> the classes that element gets in the defs copy."""
    out = {}
    for e in json.load(open(ANAT)):
        if e["layer"] == "vm-geom":
            out[e["i"]] = "g-circle" if e["w"] > 900 else "g-square"
            continue
        cx, cy = e["x"] + e["w"] / 2, e["y"] + e["h"] / 2
        c = ["k-" + e["layer"].split("-")[1]]
        if cy > HIP:
            c.append("r-legs")
        if cy < 248 and 430 < cx < 570:
            c.append("r-head")
        if abs(cx - HAND[0]) < 70 and abs(cy - HAND[1]) < 70:
            c.append("r-hand")
        out[e["i"]] = " ".join(c)
    return out


def annotate(inner, cls):
    n = [0]

    def sub(m):
        i = n[0]
        n[0] += 1
        return '%s class="%s"' % (m.group(0), cls[i])

    return re.sub(r"<(?:path|circle)\b", sub, inner)


# ---- the options -----------------------------------------------------------
# every tile is the deployed look plus ONE change
SECTIONS = [
    ("取舍 —— 把已经画好的线关掉一些", [
        ("B", "构造线虚线",
         "方与圆改成虚线：它们退成“辅助线”，人形不再被两条实线框住",
         "构造线 虚线 6/5",
         dict(geomdash="6 5")),
        ("C", "只留圆",
         "去掉方框。少一个矩形，四角一空，整幅立刻松下来 —— 但也丢掉了“身高＝臂展”那半个论证",
         "方框 display:none",
         dict(square="none")),
        ("D", "景深",
         "腿部的深浅排线各压到三成，头和手保持满墨。视线自己往两个标注点走，不必加任何提示",
         "r-legs 深 .3 · 浅 .45",
         dict(legdeep=".3", legshade=".45")),
    ]),
    ("分版 —— 机构层单独上一版墨", [
        ("E", "机构冷版",
         "打开的壳里换一种冷墨。“外面是壳、里面是机器”这件事，现在不靠线密度也说得清",
         "机构墨 #46626d",
         dict(mechink="#46626d")),
        ("F", "机构深版",
         "同色系压到近黑。剖开处像是陷进去的暗部，比换色保守得多",
         "机构墨 #4a2f18",
         dict(mechink="#4a2f18")),
    ]),
    ("纸与版面家具 —— 图之外的东西", [
        ("G", "纸纹 · 压痕 · 定位十字",
         "纸上加极细的纹，四角打定位十字，外面一圈压痕框。图一笔没改，但它开始像一张印品",
         "纸纹 .055 · 压痕框 · 四角十字",
         {}, "furniture"),
        ("H", "图注",
         "左下角图版号，右下角图名。铜版画的边注习惯，也顺便把这幅图从“插画”推向“图版”",
         "TAV. I · RESEARCH MAP",
         {}, "caption"),
    ]),
    ("交互 —— 图会回应人", [
        ("I", "热点联动",
         "把鼠标放到下面两个词上（手机上点一下）：对应的那一区墨色跟着亮起来。标注和解剖第一次真的接上了",
         "r-hand 42 元素 · r-head 22 元素",
         {}, "link"),
        ("J", "上墨动画",
         "首屏按 深排线 → 浅排线 → 机构 → 轮廓 的顺序上墨，1.2 秒。点“重放”再看一次",
         "四道墨 · 1.2s · 可关",
         {}, "anim"),
    ]),
]

REF = dict(geom=".55", geomdash="none", square="inline", deep=".6", shade=".7",
           mech="1", mechink="#8a6a4f", halo="2.6", legdeep="1", legshade="1",
           anim="0s")

OVERLAY = {
    "furniture": """<span class="reg reg--tl"></span><span class="reg reg--tr"></span>
          <span class="reg reg--bl"></span><span class="reg reg--br"></span>""",
    "caption": """<span class="cap cap--l">TAV. I</span>
          <span class="cap cap--r">RESEARCH MAP</span>""",
}

AFTER = {
    "link": """        <div class="hlbar">
          <button type="button" class="hl hl--hand">Touch</button>
          <button type="button" class="hl hl--head">Spatial Intelligence</button>
        </div>
""",
    "anim": """        <div class="hlbar"><button type="button" class="hl replay">重放</button></div>
""",
}


def tile(letter, name, note, spec, delta, kind=None):
    v = dict(REF)
    v.update(delta)
    if kind == "anim":
        v["anim"] = "1.2s"
    style = "; ".join("--%s:%s" % (k, val) for k, val in v.items())
    return """      <figure class="proof%s">
        <div class="platemark">
          <svg class="pl" viewBox="0 0 1000 1000" style="%s" role="img"
               aria-label="%s 号试样：%s">
            <use href="#plate"/>
          </svg>
          %s
        </div>
%s        <figcaption>
          <p class="desig"><span class="letter">%s</span></p>
          <h2>%s</h2>
          <p class="note">%s</p>
          <p class="spec">%s</p>
        </figcaption>
      </figure>
""" % (" pr--" + kind if kind else "", style, letter, name,
       OVERLAY.get(kind, ""), AFTER.get(kind, ""), letter, name, note, spec)


def build():
    inner = plate()
    assert 'id="vm-ink"' in inner and 'class="l-halo"' in inner
    _, count = tag(inner)
    cls = classes()
    assert len(cls) == count, "anatomy.json has %d of %d elements" % (len(cls), count)
    marked = annotate(inner, cls)

    tiles = [tile("A", "现在这版", "H 已经烘进坐标里的那一版，作参照。下面每一张只改一件事",
                  "腿 ×1.03 · 上身 ×0.968 · 排线 .6/.7 · 光晕 2.6", {})]
    for head, opts in SECTIONS:
        tiles.append('      <h3 class="sec">%s</h3>\n' % head)
        tiles += [tile(*o) for o in opts]
    return PAGE.replace("__PLATE__", marked).replace("__TILES__", "".join(tiles))


PAGE = """<title>维特鲁威人版面选项</title>
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

/* two up at most: judged at the 440px the homepage actually draws it at */
.sheet{ display:grid; gap:26px 26px; margin-top:34px;
        grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); }
.sec{ grid-column:1/-1; margin:26px 0 -8px; font-size:14px; font-weight:500;
      font-family:var(--mono); letter-spacing:.04em; color:var(--text2);
      border-top:1px solid var(--rule); padding-top:14px; }
.proof{ margin:0; background:var(--panel); border:1px solid var(--rule);
        padding:14px 14px 4px; display:flex; flex-direction:column; }
.platemark{ position:relative; background:var(--paper); border:1px solid var(--paper-edge);
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

/* ---- G: the paper itself ---------------------------------------- */
.pr--furniture .platemark{
  background-color:var(--paper);
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.055'/%3E%3C/svg%3E");
  padding:22px;
  box-shadow:inset 0 0 0 1px rgba(138,106,79,.16),
             inset 0 0 0 11px rgba(255,255,255,0),
             inset 0 0 0 12px rgba(138,106,79,.13),   /* the platemark line */
             inset 0 1px 0 rgba(255,255,255,.9),
             0 1px 3px rgba(59,43,26,.13);
}
.reg{ position:absolute; width:13px; height:13px; opacity:.5;
      background:
        linear-gradient(var(--sang),var(--sang)) center/1px 100% no-repeat,
        linear-gradient(var(--sang),var(--sang)) center/100% 1px no-repeat; }
.reg--tl{ left:4px;  top:4px; }
.reg--tr{ right:4px; top:4px; }
.reg--bl{ left:4px;  bottom:4px; }
.reg--br{ right:4px; bottom:4px; }

/* ---- H: plate furniture ----------------------------------------- */
.pr--caption .platemark{ padding:10px 10px 30px; }
.cap{ position:absolute; bottom:9px; font-family:var(--serif); font-size:11.5px;
      letter-spacing:.14em; color:var(--sang); opacity:.75; }
.cap--l{ left:14px; font-variant:small-caps; }
.cap--r{ right:14px; font-style:italic; letter-spacing:.1em; }

/* ---- I + J: the strip under the plate --------------------------- */
.hlbar{ display:flex; gap:8px; margin-top:10px; }
.hl{ font:inherit; font-size:13px; font-style:italic; color:var(--sang);
     background:none; border:1px solid var(--rule); padding:4px 11px;
     cursor:pointer; transition:color .2s, border-color .2s; }
.hl:hover, .hl:focus-visible{ color:var(--hot); border-color:var(--hot); }

/* the clone cannot be reached by an ancestor selector, so the hover is
   translated into a custom property on the host <svg>, which inherits in */
.pr--link:has(.hl--hand:hover)  .pl,
.pr--link:has(.hl--hand:focus)  .pl{ --handink:var(--hot); --handhalo:5; }
.pr--link:has(.hl--head:hover)  .pl,
.pr--link:has(.hl--head:focus)  .pl{ --headink:var(--hot); --headhalo:5; }

footer{ margin-top:44px; border-top:1px solid var(--rule); padding-top:16px;
        color:var(--text2); font-size:15px; max-width:64ch; }

/* ---- the parameterised plate ------------------------------------
   These selectors match the ORIGINAL elements inside <defs>; their computed
   style rides into every <use> clone, where the custom properties resolve
   per tile.  Region and layer classes are compounded on the element itself
   (.r-legs.k-deep), never written as an ancestor selector — an ancestor
   outside the clone would not match. */
.vm-geom{ opacity:var(--geom,.55); stroke-dasharray:var(--geomdash,none); }
.g-square{ display:var(--square,inline); }
.l-deep{ opacity:var(--deep,.6); }
.l-shade{ opacity:var(--shade,.7); }
.l-mech{ opacity:var(--mech,1); color:var(--mechink,#8a6a4f); }
.l-halo{ fill:none; stroke:#fff; stroke-width:var(--halo,2.6); stroke-linejoin:round; }

.r-legs.k-deep{ opacity:var(--legdeep,1); }
.r-legs.k-shade{ opacity:var(--legshade,1); }
.r-hand{ color:var(--handink,inherit); }
.r-head{ color:var(--headink,inherit); }

/* four inking passes, in the order a plate is actually worked up */
@keyframes ink{ from{ opacity:0 } }
.l-deep, .l-shade, .l-mech, .l-ink{
  animation:ink var(--anim,0s) ease-out both;
}
.l-shade{ animation-delay:calc(var(--anim,0s) * .28); }
.l-mech { animation-delay:calc(var(--anim,0s) * .56); }
.l-ink  { animation-delay:calc(var(--anim,0s) * .84); }
@media (prefers-reduced-motion:reduce){
  .l-deep,.l-shade,.l-mech,.l-ink{ animation:none; }
}
</style>

<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<g id="plate" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
__PLATE__
</g></defs></svg>

<div class="wrap">
  <header>
    <p class="eyebrow">Research map · 版面选项 A–J</p>
    <h1>不动人形，还能改的九件事</h1>
    <p>比例已经按 <strong>H</strong> 烘进坐标里了 —— 下面每一张都是那张图，
       一笔没有重画。变的是<strong>显什么、机构用哪版墨、纸和边注、以及图会不会回应人</strong>。</p>
    <p><strong>I</strong> 和 <strong>J</strong> 要动手：I 把鼠标放到两个词上，J 点“重放”。</p>
    <div class="meta">
      <span>图幅 440px</span><span>viewBox 0 0 1000 1000</span>
      <span>纸 #fefcf8</span><span>基准墨 #8a6a4f</span>
      <span>腿 ×1.03 · 上身 ×0.968</span>
    </div>
  </header>

  <div class="sheet">
__TILES__  </div>

  <footer>报编号就行，可以多选、也可以叠着要（比如「D + E + G」）。选定后我直接改 index.html，
    并按老规矩截图给你看整幅。</footer>
</div>

<script>
document.querySelectorAll('.replay').forEach(function(b){
  b.addEventListener('click', function(){
    var svg = b.closest('.proof').querySelector('.pl');
    svg.style.setProperty('--anim','0s');
    svg.getBoundingClientRect();                 // force the restart
    requestAnimationFrame(function(){ svg.style.setProperty('--anim','1.2s'); });
  });
});
/* touch: no hover, so a tap latches the highlight */
document.querySelectorAll('.pr--link .hl').forEach(function(b){
  b.addEventListener('click', function(){
    var svg = b.closest('.proof').querySelector('.pl');
    var hand = b.classList.contains('hl--hand');
    var on = svg.dataset.lit !== (hand ? 'hand' : 'head');
    svg.style.setProperty('--handink', on && hand ? 'var(--hot)' : 'inherit');
    svg.style.setProperty('--headink', on && !hand ? 'var(--hot)' : 'inherit');
    svg.dataset.lit = on ? (hand ? 'hand' : 'head') : '';
  });
});
</script>
"""

if __name__ == "__main__":
    page = build()
    open(OUT, "w").write(page)
    print("wrote %s  %d bytes" % (OUT, len(page)))

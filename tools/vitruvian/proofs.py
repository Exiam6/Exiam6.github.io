#!/usr/bin/env python3
"""Build the ink-proof comparison sheet.

The figure itself is never redrawn: the plate is lifted verbatim out of
index.html, dropped into <defs> once, and pulled N times with <use>.  Each
pull only sets CSS custom properties, which inherit into the use-element
shadow tree, so every proof is the same drawing under a different inking.

    python3 tools/vitruvian/proofs.py            # -> tools/vitruvian/proofs.html
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "..", "..", "index.html")
OUT = os.path.join(HERE, "proofs.html")

# ---- lift the plate out of index.html --------------------------------------
html = open(IDX).read()
m = re.search(r'<svg class="rm-fig__svg".*?>(.*?)</svg>', html, re.S)
assert m, "figure not found in index.html"
inner = m.group(1)
assert 'id="vm-ink"' in inner and 'class="l-halo"' in inner

# ---- the proofs ------------------------------------------------------------
# vars: geom deep shade mech ink mechink halo bold
REF = dict(geom=".55", deep="1", shade="1", mech="1",
           ink="#8a6a4f", mechink="#8a6a4f", halo="0", bold="0")

PROOFS = [
    ("A", "现部署版", "line", "线上",
     "此刻线上的那一版，作参照", {}),
    ("B", "淡排线 + 光晕", "work", "工作区",
     "排线压到 .6/.7，轮廓下垫一圈纸白",
     dict(deep=".6", shade=".7", halo="2.6")),
    ("C", "只加光晕", None, None,
     "排线保持满墨，只把轮廓从排线里托出来",
     dict(halo="2.6")),
    ("D", "重墨", None, None,
     "墨色压深一档，构造线相应减弱",
     dict(ink="#6f5137", mechink="#6f5137", geom=".45")),
    ("E", "粗轮廓", None, None,
     "轮廓外描 .9，笔头更钝、更沉",
     dict(bold=".9", deep=".8", shade=".85", halo="1.6")),
    ("F", "机构优先", None, None,
     "机构墨色独立压深，排线退到一半",
     dict(mechink="#6b4526", deep=".45", shade=".5", halo="2.6", geom=".5")),
    ("G", "淡构造线", None, None,
     "方与圆退到 .26，人形自己主导整幅",
     dict(geom=".26", ink="#7d5c42", deep=".85", shade=".9", halo="2.0")),
]

ALIAS = {"geom": "构造线", "deep": "深排线", "shade": "浅排线", "mech": "机构",
         "ink": "墨", "mechink": "机构墨", "halo": "光晕", "bold": "外描"}


def tile(letter, name, tag, tagtext, note, delta):
    v = dict(REF)
    v.update(delta)
    style = "; ".join("--%s:%s" % (k, val) for k, val in v.items())
    spec = " · ".join("%s %s" % (ALIAS[k], delta[k]) for k in delta) or "—"
    tagmark = ('<span class="tag tag--%s">%s</span>' % (tag, tagtext)) if tag else ""
    return """      <figure class="proof">
        <div class="platemark">
          <svg class="pl" viewBox="0 0 1000 1000" style="%s" role="img"
               aria-label="%s 号试样：%s">
            <use href="#plate"/><use href="#vm-ink" class="l-bold"/>
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


tiles = "".join(tile(*p) for p in PROOFS)

PAGE = """<title>Vitruvian Ink Proofs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  /* the plate's own inks, and a warm paper the proofs are always pulled on */
  --paper:#fefcf8;
  --paper-edge:#e7dccb;
  --sang:#8a6a4f;
  --mark:#744e30;
  --hot:#a8552b;

  --ground:#efe7da;          /* the sheet the proofs are laid out on */
  --panel:#f7f1e6;
  --text:#3b332a;
  --text2:#6d6055;
  --rule:#ddd0bc;

  --serif:"EB Garamond","Songti SC","Noto Serif CJK SC","Source Han Serif SC",Georgia,serif;
  --mono:"IBM Plex Mono","SF Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#15110d; --panel:#1d1811; --text:#e7dcc9; --text2:#a0917f; --rule:#332a20;
    --hot:#d2794a;
  }
}
:root[data-theme="dark"]{
  --ground:#15110d; --panel:#1d1811; --text:#e7dcc9; --text2:#a0917f; --rule:#332a20;
  --hot:#d2794a;
}

body{ background:var(--ground); color:var(--text); font-family:var(--serif);
      font-size:17px; line-height:1.6; -webkit-font-smoothing:antialiased; }
.wrap{ max-width:1080px; margin:0 auto; padding:56px 28px 96px; }

/* ---- docket ---------------------------------------------------- */
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

/* ---- the proofs ------------------------------------------------- */
/* two up at most: every proof has to be judged at the 440px it will
   actually be drawn at on the homepage */
.sheet{ display:grid; gap:26px; margin-top:34px;
        grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); }
.proof{ margin:0; background:var(--panel); border:1px solid var(--rule);
        padding:14px 14px 4px; display:flex; flex-direction:column; }
/* an engraving carries a plate mark: the embossed rectangle the copper
   pressed into the sheet, a little outside the image */
.platemark{ background:var(--paper); border:1px solid var(--paper-edge);
            box-shadow:inset 0 1px 0 rgba(255,255,255,.9),
                       0 1px 2px rgba(59,43,26,.10);
            padding:16px 10px; display:flex; justify-content:center; }
.pl{ display:block; width:100%; max-width:440px; height:auto; color:var(--ink,#8a6a4f); }

figcaption{ padding:13px 2px 12px; }
.desig{ display:flex; align-items:center; gap:9px; margin:0 0 3px; }
.letter{ font-family:var(--mono); font-size:12px; font-weight:500;
         letter-spacing:.18em; color:var(--hot); }
.tag{ font-family:var(--mono); font-size:10px; letter-spacing:.1em;
      text-transform:uppercase; padding:2px 7px; border:1px solid var(--rule);
      color:var(--text2); }
.tag--line{ border-color:var(--hot); color:var(--hot); }
h2{ font-size:20px; font-weight:500; margin:0 0 4px; letter-spacing:.01em; }
.note{ margin:0 0 9px; font-size:15px; color:var(--text2); }
.spec{ margin:0; font-family:var(--mono); font-size:11.5px; color:var(--text2);
       border-top:1px solid var(--rule); padding-top:9px;
       font-variant-numeric:tabular-nums; }

footer{ margin-top:44px; border-top:1px solid var(--rule); padding-top:16px;
        color:var(--text2); font-size:15px; max-width:62ch; }

/* ---- the parameterised plate ------------------------------------
   These selectors match the ORIGINAL elements inside <defs>; their
   computed style is carried into every <use> clone, where the custom
   properties resolve per proof. */
.vm-geom{ opacity:var(--geom,.55); }
.l-deep{ opacity:var(--deep,1); }
.l-shade{ opacity:var(--shade,1); }
.l-mech{ opacity:var(--mech,1); color:var(--mechink,#8a6a4f); }
.l-halo{ fill:none; stroke:#fff; stroke-width:var(--halo,0); stroke-linejoin:round; }
.l-bold{ fill:none; stroke:currentColor; stroke-width:var(--bold,0);
         stroke-linejoin:round; }
</style>

<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<g id="plate" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
__PLATE__
</g></defs></svg>

<div class="wrap">
  <header>
    <p class="eyebrow">Research map · 试样 A–G</p>
    <h1>同一块版，七种上墨</h1>
    <p>人形一笔没动 —— 全部是<strong>现部署的那张图</strong>，只改墨色、排线深浅、轮廓外描和构造线。
       每张都按主页真实尺寸 440px 出图，直接看整幅，不看局部。</p>
    <p><strong>A</strong> 是此刻线上的版本，<strong>B</strong> 是刚被我退回去的工作区版本，两张都留在这里作参照。</p>
    <div class="meta">
      <span>图幅 440px</span><span>viewBox 0 0 1000 1000</span>
      <span>纸 #fefcf8</span><span>基准墨 #8a6a4f</span>
    </div>
  </header>

  <div class="sheet">
__TILES__  </div>

  <footer>报一个编号就行；也可以拆着要，比如「D 的墨 + C 的光晕」。选定后我直接改 index.html。</footer>
</div>
"""

page = PAGE.replace("__PLATE__", inner).replace("__TILES__", tiles)
open(OUT, "w").write(page)
print("wrote", OUT, len(page), "bytes,", len(PROOFS), "proofs")

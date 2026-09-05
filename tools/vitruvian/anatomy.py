#!/usr/bin/env python3
"""Measure the plate: one bounding box per drawn element.

The figure's groups are INK layers (l-deep, l-shade, l-mech, l-ink), not body
parts, so a limb can only be addressed geometrically.  Rather than write a
path-data parser, this tags every element with data-i, loads the plate in
headless Chrome and reads getBBox() back through --dump-dom, which uses the
browser's own path parser.

    python3 tools/vitruvian/anatomy.py     # -> tools/vitruvian/anatomy.json

NOTE: the committed anatomy.json measures the plate as it was BEFORE
bake.py wrote proof H into the coordinates.  Everything downstream
(pose.py regions, bake.py, looks.py) classifies elements in that frame,
which is fine — the bake is monotonic in y, so an element that was a leg
is still a leg — but do not read these boxes as the plate's current
geometry, and do not re-run this script over the baked plate without
knowing that is what you want.
"""
import html as html_mod
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "..", "..", "index.html")
OUT = os.path.join(HERE, "anatomy.json")
SCRATCH = os.environ.get("SCRATCH", "/tmp")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ELEM = re.compile(r"<(path|circle|ellipse|rect|line|polyline|polygon)\b")


def plate():
    html = open(IDX).read()
    m = re.search(r'<svg class="rm-fig__svg".*?>(.*?)</svg>', html, re.S)
    assert m, "figure not found in index.html"
    return m.group(1)


def tag(inner):
    """Give every drawn element a stable index."""
    n = [0]

    def sub(m):
        i = n[0]
        n[0] += 1
        return "%s data-i=\"%d\"" % (m.group(0), i)

    return ELEM.sub(sub, inner), n[0]


def measure(tagged, count):
    probe = """<svg id="s" viewBox="0 0 1000 1000" fill="none" stroke="#000"
     stroke-linecap="round" stroke-linejoin="round" width="1000" height="1000">
%s
</svg>
<script>
var out = [];
document.querySelectorAll('#s [data-i]').forEach(function(el){
  var b = el.getBBox(), g = el.closest('g[class]');
  out.push([ +el.dataset.i, g ? g.getAttribute('class') : '',
             Math.round(b.x*10)/10, Math.round(b.y*10)/10,
             Math.round(b.width*10)/10, Math.round(b.height*10)/10 ]);
});
var p = document.createElement('pre');
p.id = 'bboxes';
p.textContent = 'BBOX_JSON:' + JSON.stringify(out) + ':END';
document.body.appendChild(p);
</script>""" % tagged
    path = os.path.join(SCRATCH, "_probe.html")
    open(path, "w").write(probe)
    dom = subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=4000",
         "--dump-dom", "file://" + path],
        capture_output=True, text=True).stdout
    # the dumped DOM also contains the <script> source, where this same marker
    # appears around the un-evaluated expression — so take the match that parses
    rows = None
    for cand in re.findall(r"BBOX_JSON:(.*?):END", dom, re.S):
        try:
            rows = json.loads(html_mod.unescape(cand))  # textContent is escaped
            break
        except json.JSONDecodeError:
            continue
    if rows is None:
        sys.exit("Chrome returned no bboxes (dom %d bytes)" % len(dom))
    assert len(rows) == count, "measured %d of %d elements" % (len(rows), count)
    return rows


if __name__ == "__main__":
    tagged, count = tag(plate())
    rows = measure(tagged, count)
    data = [{"i": r[0], "layer": r[1], "x": r[2], "y": r[3], "w": r[4], "h": r[5]}
            for r in rows]
    json.dump(data, open(OUT, "w"))

    # a coarse census, so the caller can see what is separable
    big = sorted(data, key=lambda d: -(d["w"] * d["h"]))[:12]
    print("%d elements measured -> %s" % (len(data), OUT))
    print("\nlargest elements (a path spanning two regions cannot be moved alone):")
    for d in big:
        print("  i=%-5d %-9s x %6.1f y %6.1f  w %6.1f h %6.1f"
              % (d["i"], d["layer"], d["x"], d["y"], d["w"], d["h"]))
    bands = {}
    for d in data:
        bands.setdefault(int((d["y"] + d["h"] / 2) // 100) * 100, []).append(d)
    print("\nelements by vertical band (y of centre):")
    for k in sorted(bands):
        print("  %4d-%4d  %4d elements" % (k, k + 99, len(bands[k])))

#!/usr/bin/env python3
"""Check the baked plate element by element, with the browser's path parser.

Every element's box must land exactly where the y-affine says it should:
    y' = s*y + c,  h' = s*h,  x and w untouched.
Anything the parser got wrong — a missed relative segment, a mis-paired
number — shows up here as a box in the wrong place.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anatomy                                  # noqa: E402
from anatomy import tag                         # noqa: E402
from pose import regions                        # noqa: E402
from bake import variant                        # noqa: E402

anatomy.SCRATCH = os.environ.get("SCRATCH", "/tmp")
FRAG = os.path.join(HERE, "baked.svgfrag")

maps, hip, s_up = variant("H")
reg = regions()
before = {d["i"]: d for d in json.load(open(os.path.join(HERE, "anatomy.json")))}

tagged, count = tag(open(FRAG).read())
rows = anatomy.measure(tagged, count)

worst = (0, None)
bad = []
for i, layer, x, y, w, h in rows:
    b = before[i]
    r = reg.get(i)
    s, c = maps[r] if r else (1.0, 0.0)
    ey, eh, ex, ew = b["y"] * s + c, b["h"] * s, b["x"], b["w"]
    err = max(abs(y - ey), abs(h - eh), abs(x - ex), abs(w - ew))
    if err > worst[0]:
        worst = (err, (i, layer, (x, y, w, h), (ex, ey, ew, eh)))
    if err > 0.35:                              # 0.35 unit = 0.15px at 440
        bad.append((i, layer, err))

print("%d elements re-measured" % len(rows))
print("worst box error %.3f units (%.3f px at 440) at i=%s %s\n  got %s\n  want %s"
      % (worst[0], worst[0] * 0.44, worst[1][0], worst[1][1], worst[1][2], worst[1][3]))
print("elements off by more than 0.35 units: %d" % len(bad))
for i, layer, err in bad[:10]:
    print("   i=%-5d %-8s %.2f" % (i, layer, err))

held = [i for i in before if reg.get(i) is None]
print("held (vm-geom): %s" % held)
print("canon after bake: crown %.2f  feet %.2f"
      % (min(r[2 + 1] for r in rows), max(r[2 + 1] + r[2 + 3] for r in rows)))

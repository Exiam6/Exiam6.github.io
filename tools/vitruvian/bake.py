#!/usr/bin/env python3
"""Bake a chosen pose proof into index.html as real coordinates.

The proof sheet moves whole regions with a CSS transform on a <use> clone.
That is a proofing mechanism, not something to ship: it would leave the
homepage's plate depending on transform-origin, on region classes threaded
through the layers, and on the halo <use> resolving the same transform in a
shadow tree.  So the accepted variant is written into the path data instead
and the classes disappear.

Proof H: legs x1.03 about the feet line, the upper body compressed about the
crown by exactly the amount that lands it on the moved hip.  Both maps are
y-only affines, y' = s*y + c, so a path is transformed by rewriting every
y number in it: absolute y by s*y + c, relative dy by s*dy.  Stroke widths
are NOT touched, so unlike the CSS proof the pen keeps a uniform weight
(a scaleY would have thinned every horizontal hatch by 3%).

    python3 tools/vitruvian/bake.py H            # -> rewrites index.html
    python3 tools/vitruvian/bake.py H --dry-run
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from anatomy import plate, tag, ELEM          # noqa: E402
from pose import CROWN, HIP, FEET, regions, legs   # noqa: E402

IDX = os.path.join(HERE, "..", "..", "index.html")

# the accepted proofs, as {region: (scale, offset)} y-affines
def variant(letter):
    if letter != "H":
        sys.exit("only H is baked by this script; add the map for %s first" % letter)
    v, hip, s_up = legs(1.03)
    return {"lower": (1.03, FEET * (1 - 1.03)),
            "upper": (s_up, CROWN * (1 - s_up)),
            "head": (s_up, CROWN * (1 - s_up))}, hip, s_up


NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)")


def fmt(v):
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def remap_d(d, s, c):
    """Rewrite every y in a path. Absolute: s*y+c. Relative: s*dy.

    One catch, and it is the whole reason this is verified: a path that OPENS
    with a lowercase `m` is relative to the origin, i.e. absolute.  Only that
    very first pair — later `m`s in the same path (these hatch clusters are
    full of them) really are relative to the current point.
    """
    out = []
    for k, m in enumerate(CMD.finditer(d)):
        cmd, body = m.group(1), m.group(2)
        first = (k == 0)
        nums = NUM.findall(body)
        if cmd in "Zz":
            out.append(cmd)
            continue
        if cmd in "Aa":
            sys.exit("arc command in path data — the pair rule does not hold")
        vals = [float(n) for n in nums]
        if cmd in "Hh":                       # x only
            pass
        elif cmd in "Vv":                     # y only
            vals = [v * s + (c if cmd == "V" else 0) for v in vals]
        else:                                 # every command left takes x,y pairs
            if len(vals) % 2:
                sys.exit("odd coordinate count after %s" % cmd)
            up = cmd.isupper()
            vals = [v * s + (c if (up or (first and i == 1)) else 0) if i % 2
                    else v for i, v in enumerate(vals)]
        out.append(cmd + " ".join(fmt(v) for v in vals))
    return "".join(out)


def bake(inner, reg, maps):
    """Walk the elements in document order, rewriting the ones that move."""
    n = [0]
    moved = [0]

    def sub(m):
        i = n[0]
        n[0] += 1
        el = m.group(0)
        r = reg.get(i)
        if r is None:                          # vm-geom: the canon never moves
            return el
        s, c = maps[r]
        moved[0] += 1
        return re.sub(r'\bd="([^"]+)"',
                      lambda d: 'd="%s"' % remap_d(d.group(1), s, c), el)

    # one element = one tag; every drawn element in this plate is self-closing
    tags = re.compile(r"<(?:path|circle|ellipse|rect|line|polyline|polygon)\b[^>]*>")
    return tags.sub(sub, inner), n[0], moved[0]


if __name__ == "__main__":
    letter = (sys.argv[1] if len(sys.argv) > 1 else "H").upper()
    dry = "--dry-run" in sys.argv
    maps, hip, s_up = variant(letter)

    html = open(IDX).read()
    inner = plate()
    reg = regions()
    tagged, count = tag(inner)
    assert len(reg) + sum(1 for _ in ELEM.finditer(inner)) - count == len(reg), "index skew"

    baked, seen, moved = bake(inner, reg, maps)
    assert seen == count, "walked %d of %d elements" % (seen, count)

    print("proof %s: legs x1.03 about y=%.1f, upper x%.5f about y=%.1f, hip %.0f -> %.0f"
          % (letter, FEET, s_up, CROWN, HIP, hip))
    print("  %d elements moved, %d held (the construction square and circle)"
          % (moved, seen - moved))
    for name, (s, c) in maps.items():
        print("  %-6s y' = %.5f*y %+.4f" % (name, s, c))
    print("  check: crown %.3f  hip(up) %.3f  hip(low) %.3f  feet %.3f"
          % (CROWN * maps["upper"][0] + maps["upper"][1],
             HIP * maps["upper"][0] + maps["upper"][1],
             HIP * maps["lower"][0] + maps["lower"][1],
             FEET * maps["lower"][0] + maps["lower"][1]))
    print("  plate %d -> %d bytes" % (len(inner), len(baked)))

    if dry:
        open(os.path.join(HERE, "baked.svgfrag"), "w").write(baked)
        sys.exit(0)
    assert inner in html, "plate not found verbatim in index.html"
    # the bake is NOT idempotent — a second run would apply the affine twice,
    # and the result looks plausible enough to ship by mistake.  Mark the svg.
    m = re.search(r'<svg class="rm-fig__svg"[^>]*>', html)
    if m and 'data-pose=' in m.group(0):
        sys.exit("index.html already carries a baked pose (%s) — nothing done"
                 % re.search(r'data-pose="([^"]*)"', m.group(0)).group(1))
    html = html.replace('<svg class="rm-fig__svg" viewBox',
                        '<svg class="rm-fig__svg" data-pose="%s" viewBox' % letter, 1)
    open(IDX, "w").write(html.replace(inner, baked, 1))
    print("  wrote %s" % os.path.normpath(IDX))

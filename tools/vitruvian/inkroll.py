#!/usr/bin/env python3
"""Ship the stroke treatments to the homepage as code, not as eight drawings.

Eight copies of the plate would be ~1.3 MB on a page whose whole point is that
it is one file.  Instead the transforms move into ~5 KB of JavaScript that
rewrites the path data in place, once, before first paint: the page still
carries exactly one drawing and picks how to ink it on each visit.

    python3 tools/vitruvian/inkroll.py            # splice into index.html
    python3 tools/vitruvian/inkroll.py --remove   # take it back out
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "..", "..", "index.html")

MARK_A = "<!-- INKROLL:start -->"
MARK_B = "<!-- INKROLL:end -->"

CSS = """
/* ---- 1c. THE INKING ROLL -----------------------------------------
   The figure is drawn once and inked differently on each visit: seven
   treatments plus the plate as drawn, chosen at random by the script below
   the figure.  Two of them are a way of INKING rather than of drawing, so
   they live here as CSS; the other five rewrite path data.
   Force one with ?ink=B (A B C E F I J K). */
.rm-fig__svg.ink-wire .l-ink path{ fill:none; stroke:currentColor; stroke-width:1.1; }
.rm-fig__svg.ink-wire .l-mech path{ fill:none; stroke:currentColor; stroke-width:1.1; }
.rm-fig__svg.ink-wire .l-deep, .rm-fig__svg.ink-wire .l-shade{ display:none; }
.rm-fig__svg.ink-wire .l-halo{ display:none; }
.rm-fig__svg.ink-wire .vm-geom{ opacity:.75; }
.rm-fig__svg.ink-ghost .l-ink path{ fill:none; stroke:currentColor; stroke-width:1; }
.rm-fig__svg.ink-ghost .l-halo{ display:none; }
.rm-fig__svg.ink-ghost .l-deep{ opacity:.18; }
.rm-fig__svg.ink-ghost .l-shade{ opacity:.22; }
.rm-fig__svg.ink-ghost .l-mech path{ stroke-width:2.4; }
"""

JS = r"""
<script>
/* The inking roll.  Runs here, straight after the figure and before the page
   paints, so the plate is never seen in one treatment and then another.
   Every transform below works on the plate's own vocabulary: contours are
   closed bands, value is discrete hatch strokes. */
(function () {
  var svg = document.querySelector('.rm-fig__svg');
  if (!svg) return;

  var CMD = /([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)/g;
  var NUM = /[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?/g;

  /* Only the FIRST pair after an M is a moveto — the rest are implicit
     linetos, which is how the feet and the spine are written. */
  function parse(d) {
    var out = [], pts = [], cur = [0, 0], start = [0, 0], m, k = 0;
    CMD.lastIndex = 0;
    while ((m = CMD.exec(d))) {
      var cmd = m[1], up = cmd.toUpperCase(), rel = cmd !== up;
      var vals = (m[2].match(NUM) || []).map(Number);
      if (up === 'Z') { if (pts.length) out.push([pts, true]); pts = []; cur = start; k++; continue; }
      if (up === 'H' || up === 'V') {
        for (var h = 0; h < vals.length; h++) {
          cur = up === 'H' ? [vals[h] + (rel ? cur[0] : 0), cur[1]]
                           : [cur[0], vals[h] + (rel ? cur[1] : 0)];
          pts.push(cur);
        }
        k++; continue;
      }
      var base = (k === 0 && rel) ? [0, 0] : cur, step = up === 'Q' ? 4 : 2;
      for (var i = 0; i + step <= vals.length; i += step) {
        var x = vals[i + step - 2], y = vals[i + step - 1];
        var p = rel ? [x + base[0], y + base[1]] : [x, y];
        if (up === 'M' && i === 0) {
          if (pts.length) { out.push([pts, false]); pts = []; }
          start = p;
        }
        pts.push(p);
        base = cur = p;
      }
      k++;
    }
    if (pts.length) out.push([pts, false]);
    return out;
  }

  function n(v) { return (Math.round(v * 10) / 10).toString(); }
  function emit(subs) {
    var s = '';
    for (var i = 0; i < subs.length; i++) {
      var pts = subs[i][0];
      if (pts.length < 2) continue;
      s += 'M';
      for (var j = 0; j < pts.length; j++) s += (j ? 'L' : '') + n(pts[j][0]) + ' ' + n(pts[j][1]);
      if (subs[i][1]) s += 'Z';
    }
    return s;
  }

  function simplify(pts, eps) {
    if (pts.length < 3) return pts;
    var a = pts[0], b = pts[pts.length - 1];
    var dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy);
    var worst = -1, wi = 0;
    for (var i = 1; i < pts.length - 1; i++) {
      var p = pts[i];
      var d = len ? Math.abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / len
                  : Math.hypot(p[0] - a[0], p[1] - a[1]);
      if (d > worst) { worst = d; wi = i; }
    }
    if (worst <= eps) return [a, b];
    return simplify(pts.slice(0, wi + 1), eps).slice(0, -1).concat(simplify(pts.slice(wi), eps));
  }

  function chaikin(pts, closed, rounds) {
    for (var r = 0; r < rounds; r++) {
      var seq = closed ? pts.concat([pts[0]]) : pts, out = [];
      for (var i = 0; i < seq.length - 1; i++) {
        var a = seq[i], b = seq[i + 1];
        out.push([a[0] * .75 + b[0] * .25, a[1] * .75 + b[1] * .25]);
        out.push([a[0] * .25 + b[0] * .75, a[1] * .25 + b[1] * .75]);
      }
      pts = out;
    }
    return pts;
  }

  function tremor(pts, amp) {
    var out = [], s = 0, ph = Math.random() * 6.283;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (i) s += Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]);
      var a = pts[Math.max(i - 1, 0)], b = pts[Math.min(i + 1, pts.length - 1)];
      var dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
      var k = amp * (Math.sin(s / 17 + ph) + .5 * Math.sin(s / 46 + ph * 2));
      out.push([p[0] + (-dy / L) * k, p[1] + (dx / L) * k]);
    }
    return out;
  }

  function realign(pts, deg) {
    var cx = 0, cy = 0;
    for (var i = 0; i < pts.length; i++) { cx += pts[i][0]; cy += pts[i][1]; }
    cx /= pts.length; cy /= pts.length;
    var a = pts[0], b = pts[pts.length - 1];
    var L = Math.hypot(b[0] - a[0], b[1] - a[1]) / 2;
    var u = [Math.cos(deg * Math.PI / 180), Math.sin(deg * Math.PI / 180)];
    return [[cx - u[0] * L, cy - u[1] * L], [cx + u[0] * L, cy + u[1] * L]];
  }

  function stipple(pts, step) {
    var out = [], carry = 0;
    for (var i = 0; i < pts.length - 1; i++) {
      var a = pts[i], b = pts[i + 1], seg = Math.hypot(b[0] - a[0], b[1] - a[1]), t = carry;
      while (t < seg) {
        var f = seg ? t / seg : 0;
        var p = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
        out.push([[p, p], false]);
        t += step;
      }
      carry = t - seg;
    }
    return out;
  }

  var HATCH = { 'l-deep': 1, 'l-shade': 1 };
  var TREATMENTS = {
    A: null,
    B: { all: function (s) { return s.map(function (x) { return [simplify(x[0], 5), x[1]]; }); } },
    C: { all: smoothAll, cls: 'ink-wire' },
    E: { hatch: function (s) {
           return s.filter(function (x) { return x[0].length > 1; })
                   .map(function (x) { return [realign(x[0], 45), false]; }); } },
    F: { hatch: function (s) {
           var o = []; s.forEach(function (x) { o = o.concat(stipple(x[0], 3.4)); }); return o; } },
    I: { all: function (s) { return s.map(function (x) { return [tremor(x[0], 1.7), x[1]]; }); } },
    J: { all: smoothAll },
    K: { all: smoothAll, cls: 'ink-ghost' }
  };
  function smoothAll(s) {
    return s.map(function (x) {
      var p = simplify(x[0], 1.4);
      return [p.length > 3 ? chaikin(p, x[1], 2) : p, x[1]];
    });
  }

  var KEYS = Object.keys(TREATMENTS);
  var forced = (location.search.match(/[?&]ink=([A-K])/i) || [])[1];
  var key = forced ? forced.toUpperCase() : KEYS[Math.floor(Math.random() * KEYS.length)];
  var t = TREATMENTS[key];
  svg.setAttribute('data-ink', key);
  if (!t) return;
  if (t.cls) svg.classList.add(t.cls);

  var groups = svg.querySelectorAll('g[class]');
  for (var g = 0; g < groups.length; g++) {
    var layer = groups[g].getAttribute('class');
    if (layer === 'vm-geom') continue;               /* the canon never changes */
    var fn = t.all || (HATCH[layer] ? t.hatch : null);
    if (!fn) continue;
    var paths = groups[g].children;
    for (var i = 0; i < paths.length; i++) {
      var d = paths[i].getAttribute('d');
      if (d) paths[i].setAttribute('d', emit(fn(parse(d))));
    }
  }
})();
</script>
"""


def splice():
    html = open(IDX).read()
    if MARK_A in html:
        sys.exit("index.html already carries the inking roll — nothing done")

    anchor = ".rm-fig__svg .vm-body{ opacity:1; }"
    assert anchor in html, "figure stylesheet not found"
    html = html.replace(anchor, anchor + "\n" + CSS.strip(), 1)

    m = re.search(r'(<svg class="rm-fig__svg".*?</svg>)', html, re.S)
    assert m, "figure not found"
    html = html[:m.end()] + "\n" + MARK_A + JS.rstrip() + "\n" + MARK_B + html[m.end():]
    open(IDX, "w").write(html)
    print("spliced the inking roll into index.html (+%d bytes)" % (len(CSS) + len(JS)))


def remove():
    html = open(IDX).read()
    if MARK_A not in html:
        sys.exit("no inking roll in index.html")
    html = re.sub(re.escape(MARK_A) + ".*?" + re.escape(MARK_B), "", html, flags=re.S)
    html = html.replace("\n" + CSS.strip(), "")
    open(IDX, "w").write(html)
    print("removed")


if __name__ == "__main__":
    remove() if "--remove" in sys.argv else splice()

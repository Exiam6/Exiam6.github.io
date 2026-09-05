import re, os, json
S = os.path.dirname(os.path.abspath(__file__))
old = open(os.path.join(S, "original.svg")).read().replace('class="rm-fig__svg" ', '')

REGIONS = {
  "head":      (452,138,548,302),
  "hand_L":    (100,258,222,338),
  "hand_R":    (778,258,900,338),
  "hand_UL":   (118,128,232,222),
  "hand_UR":   (768,128,882,222),
  "feet_stand":(398,856,602,922),
  "foot_L":    (205,828,305,922),
  "foot_R":    (695,828,795,922),
  "chest_open":(400,300,500,485),
  "chest_shell":(500,300,600,485),
}
TOL = 4

def path_points(d):
    """Absolute points of a path d (M/L absolute ribbons, or m/q relative hatch)."""
    pts = []; x = y = 0.0; sx = sy = 0.0
    tokens = re.findall(r'[MmLlQqZz]|-?\d+\.?\d*', d)
    i = 0; cmd = None
    while i < len(tokens):
        t = tokens[i]
        if t in "MmLlQqZz": cmd = t; i += 1
        if cmd in "Zz":
            continue
        if cmd == "M": x, y = float(tokens[i]), float(tokens[i+1]); i += 2; pts.append((x,y)); cmd = "L"
        elif cmd == "m": x += float(tokens[i]); y += float(tokens[i+1]); i += 2; pts.append((x,y)); cmd = "l"
        elif cmd == "L": x, y = float(tokens[i]), float(tokens[i+1]); i += 2; pts.append((x,y))
        elif cmd == "l": x += float(tokens[i]); y += float(tokens[i+1]); i += 2; pts.append((x,y))
        elif cmd == "Q": x, y = float(tokens[i+2]), float(tokens[i+3]); i += 4; pts.append((x,y))
        elif cmd == "q": x += float(tokens[i+2]); y += float(tokens[i+3]); i += 4; pts.append((x,y))
        else: i += 1
    return pts

layers = {}
for m in re.finditer(r'<g class="(l-[a-z]+)"[^>]*>(.*?)</g>', old, re.S):
    name, body = m.group(1), m.group(2)
    paths = re.findall(r'<path [^>]*/>', body)
    layers[name] = paths

def bbox(p):
    d = re.search(r' d="([^"]*)"', p).group(1)
    pts = path_points(d)
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    return (min(xs), min(ys), max(xs), max(ys))

assign = {}   # (layer, index) -> region
for name, paths in layers.items():
    for i, p in enumerate(paths):
        b = bbox(p)
        for r, (x0,y0,x1,y1) in REGIONS.items():
            if b[0] >= x0-TOL and b[1] >= y0-TOL and b[2] <= x1+TOL and b[3] <= y1+TOL:
                assign[(name,i)] = r; break

counts = {}
for (name,i), r in assign.items():
    counts.setdefault(r, {}).setdefault(name, 0); counts[r][name] += 1
print(json.dumps(counts, indent=1))

def rebuild(keep):
    out = old
    for name, paths in layers.items():
        kept = [p for i, p in enumerate(paths) if keep(name, i)]
        out = re.sub(r'(<g class="%s"[^>]*>)(.*?)(</g>)' % name, lambda m: m.group(1) + "\n" + "\n".join(kept) + "\n" + m.group(3), out, count=1, flags=re.S)
    return out

if __name__ == "__main__":
  stripped = rebuild(lambda n, i: (n,i) not in assign)
  removed  = rebuild(lambda n, i: (n,i) in assign)
  open(os.path.join(S, "stripped.svg"), "w").write(stripped)
  open(os.path.join(S, "removed.svg"), "w").write(removed)
  json.dump({"%s:%d" % k: v for k, v in assign.items()}, open(os.path.join(S, "assign.json"), "w"))
  # region boxes overlay for the check render
  boxes = "".join('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="#2a7" stroke-width="1"/>' % (x0,y0,x1-x0,y1-y0) for (x0,y0,x1,y1) in REGIONS.values())
  open(os.path.join(S, "check.html"), "w").write('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#fff;display:flex}svg{width:700px;height:700px;color:#8a6a4f;display:block}.vm-geom{opacity:.55}</style></head><body>%s%s</body></html>' % (
      stripped.replace('</svg>', boxes + '</svg>'), removed))

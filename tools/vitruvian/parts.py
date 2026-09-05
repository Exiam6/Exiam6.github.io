import sys, os, re, math, random, json, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pen import *
import pen
with contextlib.redirect_stdout(io.StringIO()):
    import analyze
random.seed(7)

# ------------------------------------------------------------ base figure
REG = {   # (x0,y0,x1,y1, mode)   mode: bbox = whole path inside; small = centroid inside & bbox < 130
  "head":       (452,138,548,302, "bbox"),
  "hand_L":     (100,255,224,340, "small"),
  "hand_R":     (776,255,900,340, "small"),
  "hand_UL":    (118,128,246,226, "small"),
  "hand_UR":    (754,128,882,226, "small"),
  "feet_stand": (398,856,602,922, "bbox"),
  "foot_L":     (205,828,305,922, "bbox"),
  "foot_R":     (695,828,795,922, "bbox"),
  "chest_open": (396,280,496,490, "small"),
  "chest_shell":(504,280,600,490, "small"),
}
layers, bbox = analyze.layers, analyze.bbox
def region_of(p):
    b = bbox(p); cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2; big = max(b[2]-b[0], b[3]-b[1])
    for r, (x0,y0,x1,y1,mode) in REG.items():
        if mode == "bbox" and b[0] >= x0-4 and b[1] >= y0-4 and b[2] <= x1+4 and b[3] <= y1+4: return r
        if mode == "small" and x0 <= cx <= x1 and y0 <= cy <= y1 and big < 130: return r
    return None

removed = {}   # region -> {layer: [paths]}
base = {}      # layer -> [paths]
for name, paths in layers.items():
    for p in paths:
        r = region_of(p)
        if r: removed.setdefault(r, {}).setdefault(name, []).append(p)
        else: base.setdefault(name, []).append(p)
ORDER = ["l-deep", "l-mech", "l-shade", "l-ink"]
HEADER = re.search(r'<svg.*?<g fill="currentColor" stroke="none">', analyze.old, re.S).group(0)
HEADER = HEADER.replace('class="rm-fig__svg" ', '')

def group_html(cls, per_layer, gid):
    out = ['<g class="part %s">' % cls]
    for ln in ORDER:
        ps = per_layer.get(ln, [])
        if not ps: continue
        if ln == "l-ink":
            out.append('<use href="#%s" class="l-halo"/>' % gid)
            out.append('<g class="l-ink" id="%s">%s</g>' % (gid, "\n".join(ps)))
        else:
            out.append('<g class="%s">%s</g>' % (ln, "\n".join(ps)))
    out.append('</g>')
    return "\n".join(out)

# ------------------------------------------------------------ pen parts
class P:
    def __init__(self):
        self.deep = Layer("l-deep"); self.shade = Layer("l-shade"); self.mech = Layer("l-mech"); self.ink = Layer("l-ink")
    def html(self, cls, gid):
        return group_html(cls, {"l-deep": self.deep.paths, "l-shade": self.shade.paths, "l-mech": self.mech.paths, "l-ink": self.ink.paths}, gid)

INKW, SEAMW, MECHW, HATW = 4.8, 2.2, 2.6, 1.7

# ---------------- head
HEAD_TOP, HEAD_BOT, HEAD_CX = 140.5, 262.0, 500.0
def head_capsule(p, light=False):
    T = HEAD_TOP
    dome = [(500, T+1), (531, T+8), (543, T+38), (542, T+72), (537, T+96), (523, T+116), (506, T+121),
            (494, T+121), (477, T+116), (463, T+96), (458, T+72), (457, T+38), (469, T+8)]
    curve(dome, INKW, p.ink, closed=True, shade=1, amp=0.55)
    # neck: short cylinder with two rings, partly behind the shoulder rim
    line((483, T+120), (484, T+150), INKW*0.8, p.ink, taper=False)
    line((517, T+120), (516, T+150), INKW*0.8, p.ink, taper=False)
    ellipse((500, T+127), 17, 4.5, 0, SEAMW, p.ink)
    ellipse((500, T+141), 16.5, 4.5, 0, SEAMW, p.ink)
    hatch([(486, T+122), (500, T+122), (500, T+150), (487, T+150)], HATCH_ANG, 5.0, HATW, p.shade)
    # shading on the shadow side of the dome
    if light:
        for rr in (26, 33, 40):
            arc((500, T+58), rr, -0.55, 0.95, HATW, p.shade, amp=0.2)
        hatch([(524, T+60), (541, T+56), (540, T+80), (532, T+102), (520, T+117), (506, T+121), (510, T+98), (520, T+80)], HATCH_ANG, 7.5, HATW, p.shade, bow=0.1)
        return dome
    for rr in (16, 23, 30, 37):
        arc((500, T+58), rr, -0.9, 1.0, HATW, p.shade, amp=0.2)
    hatch([(514, T+8), (542, T+40), (541, T+74), (535, T+98), (522, T+116), (506, T+121), (509, T+86), (518, T+34)], HATCH_ANG, 6.0, HATW, p.shade)
    hatch([(500, T+108), (536, T+98), (523, T+116), (506, T+121), (494, T+121), (478, T+116)], 20, 4.6, HATW, p.deep)
    return dome

def head_D():   # faceless: the bare capsule, light shading, neck only
    p = P(); head_capsule(p, light=True)
    return p

def head_E():   # faceless with one hairline seam from crown to chin
    p = P(); T = HEAD_TOP; head_capsule(p, light=True)
    curve([(500, T+3), (501, T+40), (501, T+80), (500, T+119)], SEAMW*0.75, p.ink, amp=0.35)
    return p

def head_A():   # visor band + ear pucks + cranial seam + jaw seam
    p = P(); T = HEAD_TOP; head_capsule(p)
    vy = T + 52
    curve([(459, vy-3), (500, vy-10), (541, vy-3)], INKW*0.72, p.ink, amp=0.3)
    curve([(461, vy+11), (500, vy+4), (539, vy+11)], INKW*0.65, p.ink, amp=0.3)
    visor = [(460, vy-3), (500, vy-9), (540, vy-3), (538, vy+10), (500, vy+4), (462, vy+10)]
    hatch(visor, 62, 3.4, HATW, p.deep); hatch(visor, -20, 4.6, HATW*0.85, p.deep)
    curve([(500, T+3), (503, T+20), (503, vy-12)], SEAMW*0.8, p.ink, amp=0.3)
    for x in (459, 541):
        circle((x, T+60), 7.5, INKW*0.62, p.ink); circle((x, T+60), 3.0, SEAMW*0.7, p.ink, shade=0)
    curve([(467, T+100), (500, T+107), (533, T+100)], SEAMW*0.8, p.ink, amp=0.3)
    return p

def head_B():   # one round lens + a thin slit below + ear pucks
    p = P(); T = HEAD_TOP; head_capsule(p)
    c = (500, T+54)
    circle(c, 15, INKW*0.75, p.ink); circle(c, 8.5, SEAMW, p.ink, shade=0); circle(c, 3.2, SEAMW, p.ink, shade=0)
    arc(c, 11.5, 0.3, 2.4, HATW, p.deep, amp=0.15); arc(c, 13.2, 0.1, 2.6, HATW, p.deep, amp=0.15)
    curve([(468, T+84), (500, T+79), (532, T+84)], INKW*0.55, p.ink, amp=0.3)
    hatch([(469, T+84), (500, T+79), (531, T+84), (530, T+89), (500, T+84), (470, T+89)], 60, 3.2, HATW, p.deep)
    curve([(500, T+3), (503, T+20), (503, T+38)], SEAMW*0.8, p.ink, amp=0.3)
    for x in (459, 541):
        circle((x, T+62), 7.0, INKW*0.62, p.ink); circle((x, T+62), 2.8, SEAMW*0.7, p.ink, shade=0)
    return p

def head_C():   # two-part helmet: cranium cap + jaw plate, visor slit at the seam
    p = P(); T = HEAD_TOP; head_capsule(p)
    sy = T + 66
    curve([(458, sy-4), (480, sy+2), (500, sy+4), (520, sy+2), (542, sy-4)], INKW*0.8, p.ink, amp=0.35)
    curve([(460, sy+12), (500, sy+18), (540, sy+12)], INKW*0.7, p.ink, amp=0.35)
    slit = [(460, sy-3), (500, sy+4), (540, sy-3), (539, sy+12), (500, sy+17), (461, sy+12)]
    hatch(slit, 62, 3.4, HATW, p.deep); hatch(slit, -25, 5.0, HATW*0.85, p.deep)
    curve([(500, T+3), (500, T+34), (500, sy-2)], SEAMW*0.8, p.ink, amp=0.3)
    curve([(470, T+104), (500, T+110), (530, T+104)], SEAMW*0.8, p.ink, amp=0.3)
    for x in (459, 541):
        circle((x, T+50), 6.5, INKW*0.6, p.ink); circle((x, T+50), 2.6, SEAMW*0.7, p.ink, shade=0)
    return p

# ---------------- hands
WR = {"L": ((212, 298), (-1, 0.0)), "R": ((788, 298), (1, 0.0)),
      "UL": ((240, 204), N((-0.846, -0.533))), "UR": ((760, 204), N((0.846, -0.533)))}
HAND_LEN = {"L": 94, "R": 94, "UL": 96, "UR": 96}

def hand_geom(Wr, u, ln):
    n = perp(u); up = n if n[1] < 0 else M(n, -1)
    def Pl(x, y): return V(V(Wr, M(u, x)), M(up, -y))
    palm = [Pl(9, -15), Pl(26, -22), Pl(46, -20), Pl(52, 0), Pl(46, 20), Pl(26, 22), Pl(9, 15)]
    mid = ln - 50
    fingers = [((47, -15), -13, mid*0.92), ((50, -5), -4, mid), ((49, 5), 5, mid*0.92), ((44, 15), 14, mid*0.76)]
    thumb = ((18, -14), -52, 34)
    return Pl, palm, fingers, thumb, up

def finger_dir(u, up, ang):
    a = math.radians(ang)
    return N(V(M(u, math.cos(a)), M(up, -math.sin(a))))

def hand_A(p, key):    # articulated shell hand
    Wr, u = WR[key]; Pl, palm, fingers, thumb, up = hand_geom(Wr, u, HAND_LEN[key])
    circle(Wr, 11, INKW*0.8, p.ink); circle(Wr, 4.5, SEAMW*0.8, p.ink, shade=0)
    curve(palm, INKW*0.85, p.ink, closed=True, shade=1, amp=0.5)
    curve([Pl(33, -18), Pl(38, 0), Pl(33, 18)], SEAMW*0.8, p.ink, amp=0.4)
    hatch([Pl(24, 1), Pl(47, 3), Pl(45, 19), Pl(25, 21)], HATCH_ANG, 5.0, HATW, p.shade, bow=0.1)
    for (bx, by), ang, ln in fingers + [thumb]:
        base = Pl(bx, by); fu = finger_dir(u, up, ang); fn = perp(fu)
        segs = (0.44, 0.31, 0.25) if ln > 36 else (0.55, 0.45)
        q0 = base; w0 = 11.5
        for i, f in enumerate(segs):
            q1 = V(q0, M(fu, ln*f)); w1 = w0 - 1.4
            sgn = 1 if D(fn, LIGHT) > 0 else -1
            line(V(q0, M(fn, sgn*w0/2)), V(q1, M(fn, sgn*w1/2)), INKW*0.62, p.ink, amp=0.25, taper=False)
            line(V(q0, M(fn, -sgn*w0/2)), V(q1, M(fn, -sgn*w1/2)), INKW*0.45, p.ink, amp=0.25, taper=False)
            if i == len(segs)-1:
                arc(q1, w1/2, math.atan2(fu[1], fu[0]) - 1.57, math.atan2(fu[1], fu[0]) + 1.57, INKW*0.5, p.ink, amp=0.1)
            if i > 0: circle(q0, 2.4, SEAMW*0.65, p.ink, shade=0)
            q0, w0 = q1, w1

def hand_B(p, key):    # Leonardo alternation: shell on L and UR, skeleton rods on R and UL
    if key in ("L", "UR"): return hand_A(p, key)
    Wr, u = WR[key]; Pl, palm, fingers, thumb, up = hand_geom(Wr, u, HAND_LEN[key])
    circle(Wr, 11, INKW*0.6, p.ink, shade=0); circle(Wr, 4.5, SEAMW*0.8, p.ink, shade=0)
    curve(palm, INKW*0.55, p.ink, closed=True, amp=0.5)
    hatch(palm, HATCH_ANG, 5.5, HATW*0.9, p.shade)
    for y0, y1 in ((0, -4), (5, 12), (-5, -13)):
        line(Pl(13, y0), Pl(46, y1), MECHW*0.8, p.mech, taper=False)
    circle(Pl(18, 0), 4.0, SEAMW*0.7, p.ink, shade=0)
    for (bx, by), ang, ln in fingers + [thumb]:
        base = Pl(bx, by); fu = finger_dir(u, up, ang)
        segs = (0.44, 0.31, 0.25) if ln > 36 else (0.55, 0.45)
        q0 = base
        for i, f in enumerate(segs):
            q1 = V(q0, M(fu, ln*f))
            line(q0, q1, MECHW, p.mech, amp=0.25, taper=False)
            circle(q0, 2.9, SEAMW*0.7, p.ink, shade=0)
            if i == len(segs)-1: circle(q1, 2.0, SEAMW*0.6, p.ink, shade=0)
            q0 = q1

def hand_C(p, key):    # glove: tapered fingers, one knuckle seam, no joint rings
    Wr, u = WR[key]; Pl, palm, fingers, thumb, up = hand_geom(Wr, u, HAND_LEN[key])
    circle(Wr, 11, INKW*0.9, p.ink); circle(Wr, 4.5, SEAMW*0.8, p.ink, shade=0)
    curve(palm, INKW, p.ink, closed=True, shade=1, amp=0.5)
    hatch([Pl(24, 1), Pl(47, 3), Pl(45, 19), Pl(25, 21)], HATCH_ANG, 5.0, HATW, p.shade, bow=0.1)
    for (bx, by), ang, ln in fingers + [thumb]:
        base = Pl(bx, by); fu = finger_dir(u, up, ang); fn = perp(fu)
        tip = V(base, M(fu, ln)); w0, w1 = 11.5, 7.6
        sgn = 1 if D(fn, LIGHT) > 0 else -1
        e1 = spline([V(base, M(fn, sgn*w0/2)), V(lerp(base, tip, .5), M(fn, sgn*(w0+w1)/4*1.06)), V(tip, M(fn, sgn*w1/2))], step=6)
        e2 = spline([V(base, M(fn, -sgn*w0/2)), V(lerp(base, tip, .5), M(fn, -sgn*(w0+w1)/4*1.06)), V(tip, M(fn, -sgn*w1/2))], step=6)
        ribbon(e1, INKW, p.ink, amp=0.3, taper=False); ribbon(e2, INKW*0.85, p.ink, amp=0.3, taper=False)
        arc(tip, w1/2, math.atan2(fu[1], fu[0]) - 1.57, math.atan2(fu[1], fu[0]) + 1.57, INKW*0.9, p.ink, amp=0.1)
        k = V(base, M(fu, ln*0.46))
        line(V(k, M(fn, w0*0.4)), V(k, M(fn, -w0*0.4)), SEAMW*0.7, p.ink, amp=0.1)
        hatch([V(base, M(fn, sgn*w0/2)), V(tip, M(fn, sgn*w1/2)), V(tip, M(fn, sgn*w1/6)), V(base, M(fn, sgn*w0/6))], HATCH_ANG, 3.6, HATW*0.8, p.shade)

def hands(fn):
    p = P()
    for k in ("L", "R", "UL", "UR"): fn(p, k)
    return p

# ---------------- feet
ANK = {"SL": ((474, 863), -1, 0.0, 52), "SR": ((528, 863), 1, 0.0, 52),
       "XL": ((272, 858), -1, math.radians(28), 60), "XR": ((728, 858), 1, math.radians(-28), 60)}

def foot_shape(A, out, sole):
    def Pf(x, y): return (A[0] + out*x, A[1] + y)
    outline = [Pf(-12, 9), Pf(-19, 18), Pf(-17, sole-2), Pf(-8, sole), Pf(48, sole), Pf(72, sole-1),
               Pf(82, sole-6), Pf(77, sole-15), Pf(60, sole-20), Pf(38, sole-20), Pf(22, sole-16),
               Pf(14, sole-19), Pf(11, 9)]
    return Pf, outline

def rotate_paths(p, A, ang):
    if not ang: return
    for lay in (p.deep, p.shade, p.mech, p.ink):
        new = []
        for pth in lay.paths:
            def rp(m):
                x, y = rot((float(m.group(1)), float(m.group(2))), A, ang)
                return "%.1f %.1f" % (x, y)
            new.append(re.sub(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", rp, pth).replace(" -", "-"))
        lay.paths = new

def foot_A(p, key):    # boot: toe cap, sole plate, ankle ball
    A, out, ang, sole = ANK[key]; Pf, outline = foot_shape(A, out, sole)
    q = P()
    curve(outline, INKW*0.95, q.ink, closed=True, shade=1, amp=0.55)
    circle(A, 11, INKW*0.8, q.ink); circle(A, 4.5, SEAMW*0.8, q.ink, shade=0)
    curve([Pf(52, sole-19), Pf(56, sole-9), Pf(52, sole)], SEAMW*0.85, q.ink, amp=0.3)
    line(Pf(-10, sole-3), Pf(76, sole-3), SEAMW*0.7, q.ink)
    hatch([Pf(-4, sole-14), Pf(52, sole-17), Pf(78, sole-6), Pf(-4, sole-2)], HATCH_ANG if out < 0 else 180-HATCH_ANG, 5.6, HATW, q.shade, bow=0.08)
    hatch([Pf(18, sole-15), Pf(52, sole-17), Pf(78, sole-7), Pf(30, sole-3)], HATCH_ANG+60 if out < 0 else 120-HATCH_ANG, 7.5, HATW*0.85, q.deep)
    rotate_paths(q, A, ang)
    for a, b in ((p.deep, q.deep), (p.shade, q.shade), (p.mech, q.mech), (p.ink, q.ink)): a.paths += b.paths

def foot_B(p, key):    # split toe plates, ankle cuff
    A, out, ang, sole = ANK[key]; Pf, outline = foot_shape(A, out, sole)
    q = P()
    curve(outline, INKW*0.95, q.ink, closed=True, shade=1, amp=0.55)
    line(Pf(-14, 10), Pf(-14, 22), SEAMW, q.ink); line(Pf(12, 10), Pf(12, 22), SEAMW, q.ink)
    curve([Pf(-16, 22), Pf(0, 26), Pf(13, 22)], SEAMW*0.9, q.ink, amp=0.3)
    curve([Pf(56, sole-20), Pf(59, sole-9), Pf(56, sole)], SEAMW*0.85, q.ink, amp=0.3)
    curve([Pf(34, sole-20), Pf(37, sole-9), Pf(34, sole)], SEAMW*0.85, q.ink, amp=0.3)
    line(Pf(-10, sole-3), Pf(76, sole-3), SEAMW*0.7, q.ink)
    hatch([Pf(-4, sole-14), Pf(34, sole-17), Pf(58, sole-5), Pf(-4, sole-2)], HATCH_ANG if out < 0 else 180-HATCH_ANG, 5.6, HATW, q.shade, bow=0.08)
    hatch([Pf(60, sole-18), Pf(80, sole-9), Pf(78, sole-2), Pf(60, sole-2)], HATCH_ANG if out < 0 else 180-HATCH_ANG, 5.0, HATW, q.deep)
    rotate_paths(q, A, ang)
    for a, b in ((p.deep, q.deep), (p.shade, q.shade), (p.mech, q.mech), (p.ink, q.ink)): a.paths += b.paths

def foot_C(p, key):    # rounded shoe, ankle ring only
    A, out, ang, sole = ANK[key]
    def Pf(x, y): return (A[0] + out*x, A[1] + y)
    q = P()
    outline = [Pf(-10, 12), Pf(-16, sole-8), Pf(-6, sole), Pf(42, sole), Pf(70, sole-2), Pf(80, sole-9),
               Pf(73, sole-19), Pf(52, sole-23), Pf(28, sole-21), Pf(14, sole-14), Pf(11, 12)]
    curve(outline, INKW*0.95, q.ink, closed=True, shade=1, amp=0.6)
    ellipse(A, 14, 5, 0, SEAMW, q.ink)
    hatch([Pf(-4, sole-12), Pf(36, sole-19), Pf(74, sole-8), Pf(-4, sole-2)], HATCH_ANG if out < 0 else 180-HATCH_ANG, 5.6, HATW, q.shade, bow=0.1)
    rotate_paths(q, A, ang)
    for a, b in ((p.deep, q.deep), (p.shade, q.shade), (p.mech, q.mech), (p.ink, q.ink)): a.paths += b.paths

def feet(fn):
    p = P()
    for k in ("SL", "SR", "XL", "XR"): fn(p, k)
    return p

# ---------------- chest: opened viewer-left, shell viewer-right
# The cavity wall is read off the original's left torso contour ribbon, so
# nothing drawn here can cross the shell: wall_x(y) is the inner edge + margin.
_wall_pts = []
for _p in base.get("l-ink", []):
    _b = bbox(_p)
    if 380 <= _b[0] and _b[2] <= 470 and _b[1] <= 320 and _b[3] >= 520:
        _wall_pts += analyze.path_points(re.search(r' d="([^"]*)"', _p).group(1))
def wall_x(y, margin=6):
    near = [q[0] for q in _wall_pts if abs(q[1]-y) < 4]
    if not near:
        tab = [(300, 428), (330, 436), (370, 444), (400, 450), (430, 452), (445, 452), (470, 448), (490, 444)]
        for a, b in zip(tab, tab[1:]):
            if a[0] <= y <= b[0]: return a[1] + (b[1]-a[1])*(y-a[0])/(b[0]-a[0]) + margin
        return 450 + margin
    return max(near) + margin
CAV_R = 486          # the exposed cavity ends at the spine's left edge
SPINE_X = 500        # the spine sits on the body's axis; only its left half shows
WAIST = 456          # the opening ends at the waist line (y~461 in the original)
def cavity_poly(top=302, bot=WAIST):
    left = [(wall_x(y, 3), y) for y in range(top, bot+1, 12)]
    return left + [(CAV_R, bot), (CAV_R, top)]
def shell_hatch(p):
    poly = [(506, 312), (560, 316), (588, 336), (580, 372), (572, 410), (560, 448), (556, 482), (506, 482)]
    inner = [(540, 314), (566, 322), (588, 336), (580, 372), (572, 410), (560, 448), (556, 482), (536, 482)]
    hatch(poly, HATCH_ANG, 7.6, HATW, p.shade, bow=0.12)
    hatch(inner, HATCH_ANG, 7.6, HATW, p.shade, bow=0.12)
    hatch([(560, 330), (588, 340), (578, 380), (570, 420), (560, 460), (548, 482), (536, 482), (548, 420), (552, 360)], HATCH_ANG+60, 9.5, HATW*0.85, p.deep)
def spine(p):
    # vertebrae centred on x=500: the left half is exposed, the right half is
    # behind the closed shell, whose cut edge runs down the axis
    for k in range(7):
        y = 316 + k*21                       # last one at 442, clear of the waist line
        half = ellipse_pts((SPINE_X, y), 15, 6, 0, math.pi/2, 3*math.pi/2, 20)
        ribbon(half, MECHW*1.25, p.mech, amp=0.25, taper=False)
        line((SPINE_X-3, y-6), (SPINE_X-3, y+6), MECHW*0.6, p.mech, taper=False)       # facet at the cut
        if k < 6: line((SPINE_X-6, y+7), (SPINE_X-6, y+14), MECHW*0.75, p.mech, taper=False)     # left connector
        line((SPINE_X-13, y+2), (SPINE_X-17, y+8), MECHW*0.65, p.mech, taper=False)    # transverse process
        arc((SPINE_X, y), 9, 2.2, 4.1, HATW*0.9, p.shade, amp=0.15)
def cavity_hatch(p):
    hatch(cavity_poly(), HATCH_ANG, 7.0, HATW*0.9, p.shade)
def cyl(p, a0, a1, r, rod_to=None, pin=True):
    """A hydraulic cylinder from a0 to a1 with radius r, rod to rod_to."""
    uu = N(S(a1, a0)); mm = perp(uu)
    line(V(a0, M(mm, -r)), V(a1, M(mm, -r)), MECHW*1.05, p.mech, taper=False)
    line(V(a0, M(mm,  r)), V(a1, M(mm,  r)), MECHW*1.05, p.mech, taper=False)
    ellipse(a0, r*0.38, r, math.atan2(uu[1], uu[0]), MECHW*0.85, p.mech); ellipse(a1, r*0.38, r, math.atan2(uu[1], uu[0]), MECHW*0.85, p.mech)
    ellipse(lerp(a0, a1, 0.2), r*0.38, r*1.08, math.atan2(uu[1], uu[0]), MECHW*0.7, p.mech)
    hatch([V(a0, M(mm, 1)), V(a1, M(mm, 1)), V(a1, M(mm, r-0.5)), V(a0, M(mm, r-0.5))], HATCH_ANG, 4.4, HATW*0.9, p.deep)
    if rod_to:
        line(a1, rod_to, MECHW*1.15, p.mech, taper=False)
        if pin: circle(rod_to, 3.6, SEAMW*0.8, p.ink, shade=0); circle(rod_to, 1.4, SEAMW*0.6, p.ink, shade=0)
def gear(p, g, r, teeth_n, tooth=None, pin_ang=None):
    tooth = tooth or max(1.8, r*0.3)
    teeth = []
    for k in range(teeth_n):
        a = 6.2832*k/teeth_n; a2 = a + 6.2832/(2*teeth_n)
        teeth += [(g[0]+r*math.cos(a), g[1]+r*math.sin(a)), (g[0]+(r+tooth)*math.cos(a+0.08), g[1]+(r+tooth)*math.sin(a+0.08)),
                  (g[0]+(r+tooth)*math.cos(a2-0.08), g[1]+(r+tooth)*math.sin(a2-0.08)), (g[0]+r*math.cos(a2), g[1]+r*math.sin(a2))]
    ribbon(teeth + [teeth[0]], MECHW*0.8, p.mech, closed=True, amp=0.12, noise=0.05)
    circle(g, max(1.4, r*0.28), SEAMW*0.6, p.ink, shade=0)
    if pin_ang is not None:
        return V(g, M((math.cos(pin_ang), math.sin(pin_ang)), r*0.8))

def trunk_lines(p, top=392, bot=WAIST-2):
    """Pressure and return lines running down the exposed side of the spine."""
    for dx in (-4, -9):
        curve([(SPINE_X-19+dx, top), (SPINE_X-20+dx, (top+bot)/2), (SPINE_X-19+dx, bot)], MECHW*0.6, p.mech, amp=0.35)
def shoulder_cyl(p):
    """The shoulder actuator that the original already shows: a cylinder just
    inside the opening, its rod reaching up to the shoulder ball."""
    cyl(p, (458, 340), (444, 312), 6, rod_to=(438, 300), pin=True)
def rib_hoops(p, ys=(330, 360, 392, 426)):
    for y in ys:
        curve([(SPINE_X-16, y), (466, y+3), (452, y+10), (wall_x(y+18, 4), y+18)], MECHW*0.85, p.mech, amp=0.5)
def gear_pump(p, c=(466, 378), r=17):
    """A gear pump: two meshing gears in a round housing, driven by a shaft
    that comes through the shell from the power core on the hidden side."""
    circle(c, r, MECHW*1.1, p.mech, shade=0)
    circle(c, r+3, MECHW*0.6, p.mech, shade=0)
    g1 = (c[0]-7, c[1]); g2 = (c[0]+7, c[1])
    gear(p, g1, 5.2, 8); gear(p, g2, 5.2, 8)
    line((c[0]+r, c[1]), (SPINE_X-17, c[1]), MECHW*0.9, p.mech, taper=False)          # drive shaft to the axis
    ellipse((c[0]+r+2, c[1]), 1.6, 4, 0, MECHW*0.6, p.mech)
    # ports: inlet from above, outlet down to the trunk lines
    curve([(c[0]-4, c[1]-r-1), (c[0]-6, c[1]-r-9), (c[0]-2, c[1]-r-16)], MECHW*0.6, p.mech, amp=0.3)
    curve([(c[0], c[1]+r+1), (c[0]+6, c[1]+r+6), (SPINE_X-23, c[1]+r+12)], MECHW*0.6, p.mech, amp=0.3)
    hatch([(c[0]-r+2, c[1]+3), (c[0]+r-2, c[1]+3), (c[0]+r-6, c[1]+r-3), (c[0]-r+6, c[1]+r-3)], HATCH_ANG, 4.2, HATW*0.8, p.deep)
def chest_A():   # structure: rib hoops + the shoulder cylinder + trunk lines
    p = P(); cavity_hatch(p); spine(p)
    rib_hoops(p); shoulder_cyl(p); trunk_lines(p, 350)
    shell_hatch(p); return p
def chest_B():   # power: gear pump + the shoulder cylinder + trunk lines
    p = P(); cavity_hatch(p); spine(p)
    shoulder_cyl(p); gear_pump(p); trunk_lines(p, 392)
    rib_hoops(p, ys=(426,))
    shell_hatch(p); return p
def chest_C():   # frame: truss + trunk lines
    p = P(); cavity_hatch(p); spine(p)
    nodes = [(478, 322), (wall_x(352, 9), 352), (476, 382), (wall_x(412, 9), 412), (474, 442)]
    for a, b in zip(nodes, nodes[1:]): line(a, b, MECHW, p.mech, taper=False)
    for y in (322, 382, 442):
        line((478, y), (wall_x(y+2, 6), y+2), MECHW*0.9, p.mech, taper=False)
    for y in (352, 412):
        line((wall_x(y-2, 6), y-2), (480, y), MECHW*0.9, p.mech, taper=False)
    for nd in nodes: circle(nd, 3.2, SEAMW*0.7, p.ink, shade=0)
    trunk_lines(p, 330)
    shell_hatch(p); return p

# ------------------------------------------------------------ assemble
def build():
    parts = {
      "hd": {"A": head_A(), "B": head_B(), "C": head_C(), "D": head_D(), "E": head_E()},
      "hn": {"A": hands(hand_A), "B": hands(hand_B), "C": hands(hand_C)},
      "ft": {"A": feet(foot_A), "B": feet(foot_B), "C": feet(foot_C)},
      "ch": {"A": chest_A(), "B": chest_B(), "C": chest_C()},
    }
    orig = {"hd": ["head"], "hn": ["hand_L", "hand_R", "hand_UL", "hand_UR"], "ft": ["feet_stand", "foot_L", "foot_R"], "ch": ["chest_open", "chest_shell"]}
    body = []
    for ln in ORDER:
        ps = base.get(ln, [])
        if ln == "l-ink": body.append('<use href="#vm-ink" class="l-halo"/><g class="l-ink" id="vm-ink">%s</g>' % "\n".join(ps))
        else: body.append('<g class="%s">%s</g>' % (ln, "\n".join(ps)))
    groups = []
    for key, regs in orig.items():
        per = {}
        for r in regs:
            for ln, ps in removed.get(r, {}).items(): per.setdefault(ln, []).extend(ps)
        groups.append(group_html("%s-O" % key, per, "%s-O-ink" % key))
        for v, part in parts[key].items():
            groups.append(part.html("%s-%s" % (key, v), "%s-%s-ink" % (key, v)))
    svg = HEADER + "\n" + "\n".join(body) + "\n" + "\n".join(groups) + "\n</g>\n</svg>"
    return svg

if __name__ == "__main__":
    svg = build()
    open(os.path.join(HERE, "master.svg"), "w").write(svg)
    print("master bytes", len(svg))

import math, random, re
LIGHT = (0.5, 0.866)
HATCH_ANG = 48
WEIGHT = 1.0

def V(a, b): return (a[0]+b[0], a[1]+b[1])
def S(a, b): return (a[0]-b[0], a[1]-b[1])
def M(a, k): return (a[0]*k, a[1]*k)
def D(a, b): return a[0]*b[0] + a[1]*b[1]
def L(a):    return math.hypot(a[0], a[1])
def N(a):
    l = L(a) or 1.0
    return (a[0]/l, a[1]/l)
def perp(a): return (-a[1], a[0])
def rot(p, c, ang):
    s, co = math.sin(ang), math.cos(ang)
    x, y = p[0]-c[0], p[1]-c[1]
    return (c[0] + x*co - y*s, c[1] + x*s + y*co)
def lerp(a, b, t): return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t)
def clamp(x, a, b): return max(a, min(b, x))

class Layer:
    def __init__(self, cls):
        self.cls, self.paths = cls, []
    def add(self, poly):
        d = "M" + " ".join("%.1f %.1f" % p for p in poly) + "Z"
        d = re.sub(r"\.0\b", "", d).replace(" -", "-")
        self.paths.append('<path d="%s"/>' % d)
    def svg(self):
        return "\n".join(self.paths)

class Pen:
    """Four layers, matching the plate: hatch (deep+shade), mech, ink."""
    def __init__(self):
        self.HATCH = Layer("l-shade"); self.DEEP = Layer("l-deep"); self.MECH = Layer("l-mech"); self.INK = Layer("l-ink")

def dense(pts, step=8.0):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(L(S(b, a)) / step))
        for k in range(1, n+1): out.append(lerp(a, b, k/n))
    return out

def wobble(pts, amp=0.7):
    if len(pts) < 3 or amp <= 0: return pts
    ph = [random.random()*6.283 for _ in range(3)]
    out, s = [], 0.0
    for i, p in enumerate(pts):
        if i: s += L(S(p, pts[i-1]))
        a = pts[max(i-1, 0)]; b = pts[min(i+1, len(pts)-1)]
        n = perp(N(S(b, a)))
        d = amp*(math.sin(s/41.0+ph[0]) + 0.6*math.sin(s/67.0+ph[1]) + 0.22*math.sin(s/9.0+ph[2]))
        out.append(V(p, M(n, d)))
    return out

def spline(ctrl, closed=False, step=7.0):
    P = list(ctrl)
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else:      P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P)-2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        n = max(2, int(L(S(p2, p1)) / step))
        for k in range(n):
            t = k/n; t2, t3 = t*t, t*t*t
            x = 0.5*((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5*((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x, y))
    if not closed: out.append(P[-2])
    return out

def ribbon(pts, w, layer, taper=True, shade=0, closed=False, noise=0.14, wmin=0.22, amp=0.7):
    pts = wobble(pts, amp)
    if closed and L(S(pts[0], pts[-1])) > 0.5: pts = pts + [pts[0]]
    n_pts = len(pts)
    if n_pts < 2: return
    osign = 1
    if closed:
        cx = sum(p[0] for p in pts)/n_pts; cy = sum(p[1] for p in pts)/n_pts
        votes = 0
        for i in range(n_pts-1):
            n = perp(N(S(pts[i+1], pts[i])))
            votes += 1 if D(n, S(pts[i], (cx, cy))) > 0 else -1
        osign = 1 if votes >= 0 else -1
    T = sum(L(S(pts[i+1], pts[i])) for i in range(n_pts-1)) or 1.0
    ph = random.random()*6.283
    left, right, s = [], [], 0.0
    for i, p in enumerate(pts):
        if i: s += L(S(p, pts[i-1]))
        if closed:
            a = pts[i-1 if i > 0 else n_pts-2]; b = pts[i+1 if i < n_pts-1 else 1]
        else:
            a = pts[max(i-1, 0)]; b = pts[min(i+1, n_pts-1)]
        n = perp(N(S(b, a)))
        f = 1.0
        if taper and not closed:
            t = s/T
            e = clamp(min(t, 1-t)/0.22, 0, 1)
            f = wmin + (1-wmin)*math.sqrt(e)
        if shade:
            nn = M(n, osign) if closed else M(n, shade)
            f *= 0.68 + 0.62*max(0.0, D(nn, LIGHT))
        f *= 1 + noise*math.sin(s/23.0 + ph)
        hw = max(0.3, w*WEIGHT*f/2)
        left.append(V(p, M(n, hw))); right.append(S(p, M(n, hw)))
    layer.add(left + right[::-1])

def line(a, b, w, layer, shade=0, amp=0.6, taper=True):
    ribbon(dense([a, b]), w, layer, taper=taper, shade=shade, amp=amp)

def curve(ctrl, w, layer, closed=False, shade=0, amp=0.6, taper=True):
    ribbon(spline(ctrl, closed), w, layer, taper=taper, shade=shade, closed=closed, amp=amp)

def circle_pts(c, r, a0=0.0, a1=6.2832, n=None):
    n = n or max(12, int(r*1.3))
    return [(c[0]+r*math.cos(a0+(a1-a0)*k/n), c[1]+r*math.sin(a0+(a1-a0)*k/n)) for k in range(n+1)]

def circle(c, r, w, layer, shade=1):
    ribbon(circle_pts(c, r), w, layer, closed=True, shade=shade, amp=min(0.5, r/18.0))

def arc(c, r, a0, a1, w, layer, amp=0.4):
    ribbon(circle_pts(c, r, a0, a1), w, layer, amp=amp)

def ellipse_pts(c, rx, ry, ang=0.0, a0=0.0, a1=6.2832, n=32):
    return [rot((c[0]+rx*math.cos(a0+(a1-a0)*k/n), c[1]+ry*math.sin(a0+(a1-a0)*k/n)), c, ang) for k in range(n+1)]

def ellipse(c, rx, ry, ang, w, layer, shade=1):
    ribbon(ellipse_pts(c, rx, ry, ang), w, layer, closed=True, shade=shade, amp=0.25)

def inside_poly(p, poly):
    x, y, ins = p[0], p[1], False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1) % len(poly)]
        if (a[1] > y) != (b[1] > y):
            xi = a[0] + (y-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if xi > x: ins = not ins
    return ins

def hatch(poly, ang_deg, spacing, w, layer, bow=0.0, trim=1.5):
    if len(poly) < 3: return
    u = (math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg)))
    n = perp(u)
    ds = [D(p, n) for p in poly]; ts = [D(p, u) for p in poly]
    d0, d1, t0, t1 = min(ds), max(ds), min(ts), max(ts)
    d = d0 + spacing*(0.3 + 0.5*random.random())
    while d < d1:
        step, run, t = 1.5, [], t0
        while t <= t1:
            p = (u[0]*t + n[0]*d, u[1]*t + n[1]*d)
            if inside_poly(p, poly): run.append(p)
            elif run:
                _stroke(run, w, bow, layer, trim); run = []
            t += step
        if run: _stroke(run, w, bow, layer, trim)
        d += spacing * (0.88 + 0.24*random.random())

def _stroke(run, w, bow, layer, trim):
    if len(run) < 3: return
    a, b = run[0], run[-1]
    ln = L(S(b, a))
    if ln < 4: return
    u = N(S(b, a))
    a = V(a, M(u, random.random()*trim)); b = S(b, M(u, random.random()*trim))
    c = lerp(a, b, 0.5)
    tilt = math.radians(random.uniform(-2.0, 2.0))
    a, b = rot(a, c, tilt), rot(b, c, tilt)
    if bow:
        m = V(c, M(perp(u), bow*ln))
        pts = spline([a, m, b], step=11)
    else:
        pts = dense([a, b], 11)
    ribbon(pts, w, layer, amp=0.3, noise=0.25, wmin=0.15)

def band_poly(edge_out, edge_in):
    return list(edge_out) + list(edge_in)[::-1]

def shadow_normal(u):
    n = perp(u)
    return n if D(n, LIGHT) > 0 else M(n, -1)

def edge_pts(A, B, n, ra, rb, sign, bulge=1.0, at=0.5):
    mid = lerp(A, B, at)
    rm = (ra + (rb-ra)*at) * bulge
    return spline([V(A, M(n, sign*ra)), V(mid, M(n, sign*rm)), V(B, M(n, sign*rb))], step=7)

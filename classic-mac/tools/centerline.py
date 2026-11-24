"""New York 12 and 24 as centerlines and pen widths, and New York 12's centerlines drawn with widths between the two.

    python3 tools/centerline.py [t ...]

Each glyph is decomposed, in em units (1000 to the em), into its centerlines: the paths of its strokes'
skeleton, each point with the stroke's radius there and its left and right pen widths, the ink's reach along the
centerline's left and right normals. A pen of those widths swept along the centerlines gives the glyph back. The
glyphs are the traced outlines, unthinned (LIGHTEN 0): the strokes at the bitmap's own weight.

New York 12 Blend HD keeps New York 12's centerlines, advances and spacing exactly; only its strokes' thickness
changes. Each centerline point's left and right widths are t of the way from New York 12's to New York 24's,
taken from the nearest point of New York 24's centerline with its glyph fitted onto 12's by their ink boxes, and
the strokes are thinned t of the way from New York 12 HD's thinning to 24 HD's. t = 0 is New York 12 HD drawn
back from its centerlines; t = 1 has New York 24's stroke weight and contrast on New York 12's letters.
centerlines/<font>.json keep the decompositions. specimen/centerline-newyork.png shows them (New York 12's and
24's ink with their centerlines in red, blue where a stroke is over 1.3 times the glyph's median radius; between,
New York 12 drawn back from its centerlines), and specimen/newyork-blend.png sets the blends.
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import build as B, bitmap
sys.path.insert(0, os.path.join(ROOT, '..', 'common'))
import trace

EM = 1000                       # em units to the em
PAD = 120                       # raster margin, em units


def flatten(contours, s):
    """contours in font units -> polygons in em units (s em units per font unit)"""
    out = []
    for c in contours:
        P = [c[0][1]]
        for seg in c:
            if seg[0] == 'L': P.append(seg[2])
            else:
                p0, a, b, p1 = (np.array(p) for p in seg[1:])
                for t in np.linspace(0, 1, 12)[1:]:
                    P.append(tuple((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t * t * b + t ** 3 * p1))
        out.append([(x * s, y * s) for x, y in P])
    return out


def raster(polys):
    """ink of polygons (filled even-odd), 1 px = 1 em unit; the origin, and y up -> row"""
    xs = [x for P in polys for x, _ in P]; ys = [y for P in polys for _, y in P]
    x0, y1 = int(np.floor(min(xs))) - PAD, int(np.ceil(max(ys))) + PAD
    W, H = int(np.ceil(max(xs))) + PAD - x0, y1 - int(np.floor(min(ys))) + PAD
    m = np.zeros((H, W), np.uint8)
    for P in polys:
        t = Image.new('L', (W, H), 0)
        ImageDraw.Draw(t).polygon([(x - x0, y1 - y) for x, y in P], fill=1)
        m ^= np.asarray(t)
    return m, x0, y1


NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def paths(sk):
    """a skeleton's pixels walked into paths: from node to node (an end or a fork), and closed loops"""
    pts = set(zip(*np.nonzero(sk)))
    nbrs = {p: [(p[0] + a, p[1] + b) for a, b in NB if (p[0] + a, p[1] + b) in pts] for p in pts}
    nodes = {p for p in pts if len(nbrs[p]) != 2}
    seen, out = set(), []
    def walk(a, b):
        path = [a, b]
        while path[-1] not in nodes:
            nxt = [q for q in nbrs[path[-1]] if q != path[-2] and (path[-1], q) not in seen]
            if not nxt: break
            seen.add((path[-1], nxt[0])); seen.add((nxt[0], path[-1]))
            path.append(nxt[0])
            if path[-1] == path[0]: break
        return path
    for a in nodes:
        for b in nbrs[a]:
            if (a, b) in seen: continue
            seen.add((a, b)); seen.add((b, a))
            out.append(walk(a, b))
    for p in pts:                   # loops with no node (an o, a 0)
        if not nbrs[p] or any((p, q) in seen for q in nbrs[p]): continue
        q = nbrs[p][0]; seen.add((p, q)); seen.add((q, p))
        out.append(walk(p, q))
    for p in nodes:                 # a lone pixel: a dot
        if not nbrs[p]: out.append([p])
    return out


def simplify(P, eps=1.5):
    """Ramer-Douglas-Peucker on (x, y, r) points, by x, y"""
    if len(P) < 3: return P
    a, b = np.array(P[0][:2]), np.array(P[-1][:2])
    d = b - a; n = np.hypot(*d)
    dist = [abs(d[0] * (p[1] - a[1]) - d[1] * (p[0] - a[0])) / n if n else np.hypot(p[0] - a[0], p[1] - a[1])
            for p in P]
    i = int(np.argmax(dist))
    if dist[i] <= eps: return [P[0], P[-1]]
    return simplify(P[:i + 1], eps)[:-1] + simplify(P[i:], eps)


STEP = 6                        # em units between the centerline points kept
SMOOTH = 16                     # the axis: the skeleton smoothed along its length by this (em units, a Gaussian's
                                # sigma), so that it runs straight through a stroke's lean or wedge, and the lean is
                                # in its left and right widths
REACH = 2.5                     # a pen width at most this times the stroke's radius
JOIN = 1.5                      # a point within this many of a fork's radii of the fork is in a join: its widths
                                # run on into the stroke that crosses
CAP = 1.1                       # ... and are kept to this times the stroke's radius where they are drawn


def widths(m, x, y, nx, ny, r):
    """the ink's reach from (x, y) along the left normal (nx, ny) and the right: the run of ink along the normal
    that holds the point, or the nearest, as its distances either side of the point (one can be negative)"""
    T = REACH * r + 2
    ts = np.arange(-T, T + 0.25, 0.5)
    rows = np.round(m[1] - (y + ny * ts)).astype(int); cols = np.round(x + nx * ts - m[2]).astype(int)
    ok = (rows >= 0) & (rows < m[0].shape[0]) & (cols >= 0) & (cols < m[0].shape[1])
    ink = np.zeros(len(ts), bool); ink[ok] = m[0][rows[ok], cols[ok]] > 0
    if not ink.any(): return r, r
    runs, i = [], 0
    while i < len(ts):
        if ink[i]:
            j = i
            while j + 1 < len(ts) and ink[j + 1]: j += 1
            runs.append((ts[i] - 0.25, ts[j] + 0.25)); i = j + 1
        else: i += 1
    a, b = min(runs, key=lambda u: 0 if u[0] <= 0 <= u[1] else min(abs(u[0]), abs(u[1])))
    return min(b, REACH * r), min(-a, REACH * r)


DOT = 30                        # em units: a path with two free ends shorter than three times this is a dot
SPUR = 1.2                      # a branch from a fork to a free end shorter than this many of the fork's radii is
                                # a spur into a corner (a serif's), not a stroke: pruned


def degree(sk):
    return cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.uint8), borderType=cv2.BORDER_CONSTANT) - 1


def prune(sk, dist):
    """the skeleton without its spurs: short branches from a fork to a free end"""
    sk = sk.copy()
    for _ in range(3):
        deg = degree(sk); cut = False
        for path in paths(sk):
            if len(path) < 2: continue
            for end, other in ((path[0], path[-1]), (path[-1], path[0])):
                if deg[end] == 1 and deg[other] >= 3 and len(path) < SPUR * dist[other]:
                    for q in path:
                        if q != other: sk[q] = 0
                    cut = True; break
        if not cut: break
        sk = skeletonize(sk)
    return sk


def extend(path, m, deg):
    """a path's free ends carried on along their direction to the edge of the ink, so that the centerline
    reaches the stroke's end"""
    path = list(path)
    for flip in (False, True):
        if flip: path.reverse()
        if len(path) < 3 or deg[path[-1]] != 1: continue
        if deg[path[0]] == 1 and len(path) < 3 * DOT: continue       # a dot, or a stroke no longer than it is thick
        a, b = np.array(path[max(0, len(path) - 12)], float), np.array(path[-1], float)
        d = b - a; n = np.hypot(*d)
        if n == 0: continue
        d /= n; k = 1
        while True:
            q = tuple(np.round(b + d * k).astype(int))
            if not (0 <= q[0] < m.shape[0] and 0 <= q[1] < m.shape[1]) or not m[q]: break
            if q != path[-1]: path.append(q)
            k += 1
    return path


def decompose(font):
    """{char: dict(lines=[[(x, y, r, L, R, nx, ny, j), ...], ...], adv, box=[x0, y0, x1, y1])} in em units,
    unthinned: each point of a centerline (the axis), the stroke's radius there, its left and right pen widths
    (the ink's reach along the axis's left and right normals), its left normal, and j = 1 in a join"""
    from scipy.ndimage import gaussian_filter1d
    keep = B.LIGHTEN[font]; B.LIGHTEN[font] = 0
    G = B.glyphs(font)
    B.LIGHTEN[font] = keep
    strike, _ = bitmap.strike(B.SOURCE.get(font, font))
    B.reaccent(font, G, strike); B.redot(font, G, strike)
    s = EM / (B.SIZE[font] * B.PX)
    out = {}
    for ch, (contours, adv) in G.items():
        polys = flatten(contours, s)
        if not polys: continue
        m, x0, y1 = raster(polys)
        dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
        sk = prune(skeletonize(m.astype(bool)), dist)
        deg = degree(sk)
        lines = []
        for path in paths(sk):
            path = extend(path, m, deg)
            P = np.array([(c + x0, y1 - r) for r, c in path], float)
            loop = len(path) > 2 and path[0] == path[-1]
            if len(P) > 2:
                Q = P[:-1] if loop else P
                S_ = gaussian_filter1d(Q, SMOOTH, axis=0, mode='wrap' if loop else 'nearest')
                if not loop:            # the ends kept where they are: the smoothing comes in over 2 SMOOTH
                    k = np.arange(len(Q)); w = np.clip(np.minimum(k, len(Q) - 1 - k) / (2 * SMOOTH), 0, 1)[:, None]
                    S_ = Q + (S_ - Q) * w
                Q = S_
                P = np.vstack([Q, Q[:1]]) if loop else Q
            arc = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
            fork = [deg[path[0]] >= 3 and not loop, deg[path[-1]] >= 3 and not loop]
            keep_i = sorted(set(range(0, len(P), STEP)) | {len(P) - 1})
            L = []
            for i in keep_i:
                r = float(dist[path[i]])
                a, b = P[max(0, i - 4)], P[min(len(P) - 1, i + 4)]
                tx, ty = b - a; n = np.hypot(tx, ty)
                nx, ny = (-ty / n, tx / n) if n else (0.0, 1.0)
                l, rr = widths((m, y1, x0), P[i][0], P[i][1], nx, ny, r)
                j = int((fork[0] and arc[i] < JOIN * dist[path[0]]) or (fork[1] and arc[-1] - arc[i] < JOIN * dist[path[-1]]))
                L.append([round(float(v), 1) for v in (P[i][0], P[i][1], r, l, rr)] + [round(float(nx), 3), round(float(ny), 3), j])
            lines.append(L)
        rows, cols = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
        box = [float(cols[0] + x0), float(y1 - rows[-1] - 1), float(cols[-1] + 1 + x0), float(y1 - rows[0])]
        out[ch] = dict(lines=lines, adv=adv * s, box=box, raster=(m, x0, y1))
    return out


def draw(lines, shrink=0.0):
    """a pen of each point's left and right widths, less shrink each, swept along the centerlines, with round
    joins and ends: ink in em units (1 px = 1 em unit), and the raster's left and top"""
    xs = [p[0] for L in lines for p in L]; ys = [p[1] for L in lines for p in L]
    R = max(max(abs(p[3]), abs(p[4])) for L in lines for p in L)
    x0, y1 = int(min(xs) - R) - 8, int(max(ys) + R) + 8
    W, H = int(max(xs) + R) + 8 - x0, y1 - int(min(ys) - R) + 8
    m = np.zeros((H, W), np.uint8)
    px = lambda x, y: (x - x0, y1 - y)
    for L in lines:
        pts = [(x, y, l - shrink, r - shrink, nx, ny) for x, y, _, l, r, nx, ny, *_ in L]
        for x, y, l, r, nx, ny in pts:                   # round joins and ends
            if l + r < 0.6: continue
            c = px(x + nx * (l - r) / 2, y + ny * (l - r) / 2)
            cv2.circle(m, (int(round(c[0] * 4)), int(round(c[1] * 4))), int(round((l + r) / 2 * 4)), 1, -1, cv2.LINE_8, 2)
        for (xa, ya, la, ra, nax, nay), (xb, yb, lb, rb, nbx, nby) in zip(pts, pts[1:]):
            q = [px(xa + nax * la, ya + nay * la), px(xb + nbx * lb, yb + nby * lb),
                 px(xb - nbx * rb, yb - nby * rb), px(xa - nax * ra, ya - nay * ra)]
            cv2.fillPoly(m, [np.round(np.array(q) * 4).astype(np.int32)], 1, cv2.LINE_8, 2)
    return m, x0, y1


def glyph(lines, shrink, s):
    """the outlines of the centerlines drawn with shrink, in font units (s em units per font unit)"""
    m, x0, y1 = draw(lines, shrink)
    f = cv2.resize(m.astype(np.float32), (int(round(m.shape[1] / s)), int(round(m.shape[0] / s))),
                   interpolation=cv2.INTER_AREA)
    ox, oy = x0 / s, y1 / s                    # the raster's top left in font units
    return [[(seg[0],) + tuple((p[0] + ox, p[1] + oy) for p in seg[1:]) for seg in c] for c in trace.trace(f, B.SIGMA)]


OBLIQUE = 1.15                  # h's ink along g's normal more than this times h's stroke's thickness is a
                                # slanting cut through the stroke
ALIGN = 0.7                     # a New York 24 centerline point whose stroke runs within 45 degrees of 12's ...
NEAR = 60                       # ... and within this many em units of it (its glyph fitted onto 12's by their
                                # boxes) gives its thickness


def matched(g, h):
    """New York 24's pen widths along New York 12's centerline, with h, New York 24's glyph, fitted onto g, New
    York 12's, by their ink boxes. At each point of g, the stroke's thickness is h's own (its pen widths at the
    nearest point of its centerline that runs the same way, in ems, not scaled with the box: a stroke stays as
    thick as in 24); its middle is the middle of h's ink along g's normal, mapped back, so that the stroke's edges
    fall where 24's do (a thin serif on the baseline, not centred on 12's thicker one; a wedge leaning the way
    24's does). A point of g in a join (h's ink there runs on into the stroke that crosses), or with nothing of h
    near it, takes the widths along its centerline from its neighbours'."""
    (a0, b0, a1, b1), (c0, d0, c1, d1) = g['box'], h['box']
    sx, sy = (a1 - a0) / (c1 - c0), (b1 - b0) / (d1 - d0)
    m = (h['raster'][0], h['raster'][2], h['raster'][1])      # (ink, its top, its left), as widths() takes it
    H = np.array([(a0 + (p[0] - c0) * sx, b0 + (p[1] - d0) * sy, p[3] + p[4], p[5] / sx, p[6] / sy)
                  for L in h['lines'] for p in L if not p[7]] or [(0, 0, 0, 0, 1)])
    nrm = np.hypot(H[:, 3], H[:, 4]); H[:, 3] /= nrm; H[:, 4] /= nrm
    own = [p[3] + p[4] for L in g['lines'] for p in L if not p[7]] or [1]
    ratio = np.median(H[:, 2]) / np.median(own)
    out = []
    for L in g['lines']:
        M = []
        for p in L:
            if p[7]: M.append(None); continue
            d = np.hypot(H[:, 0] - p[0], H[:, 1] - p[1])
            d[np.abs(H[:, 3] * p[5] + H[:, 4] * p[6]) < ALIGN] = np.inf
            j = int(np.argmin(d))
            if d[j] > NEAR: M.append(None); continue
            w = H[j, 2]
            qx, qy = c0 + (p[0] - a0) / sx, d0 + (p[1] - b0) / sy          # the point in h
            nx, ny = p[5] * sx, p[6] * sy; n = np.hypot(nx, ny); nx, ny = nx / n, ny / n   # its normal in h
            l, r = widths(m, qx, qy, nx, ny, p[2])
            if l + r <= 1: M.append(None); continue
            # the run's edges mapped back onto g's normal: where h's stroke's edges are along it
            back = lambda u: (a0 + (qx + nx * u - c0) * sx - p[0]) * p[5] + (b0 + (qy + ny * u - d0) * sy - p[1]) * p[6]
            lo, hi = back(-r), back(l)
            if hi - lo > OBLIQUE * w:   # a slanting cut through h's stroke: narrowed to its thickness about its middle
                c = (hi + lo) / 2; lo, hi = c - w / 2, c + w / 2
            M.append((hi, -lo))
        known = [i for i, w in enumerate(M) if w is not None]
        for i, w in enumerate(M):
            if w is not None: continue
            if not known: M[i] = (min(L[i][3], CAP * L[i][2]) * ratio, min(L[i][4], CAP * L[i][2]) * ratio); continue
            a = max([k for k in known if k < i], default=None); b = min([k for k in known if k > i], default=None)
            if a is None or b is None: M[i] = M[a if b is None else b]; continue
            u = (i - a) / (b - a)
            M[i] = tuple((1 - u) * M[a][k] + u * M[b][k] for k in (0, 1))
        out.append(M)
    return out


def blend(t, d12, d24):
    """New York 12's centerlines, advances and spacing, its pen widths t of the way to New York 24's, and thinned
    t of the way from New York 12 HD's thinning to 24 HD's: {char: (contours, adv)} in New York 12's font units.
    New York 12's own widths in a join are kept to CAP times its radius."""
    s = EM / (B.SIZE['newyork12'] * B.PX)
    shrink = (1 - t) * B.LIGHTEN['newyork12'] * s + t * B.LIGHTEN['newyork24'] * EM / (B.SIZE['newyork24'] * B.PX)
    G = {}
    for ch, g in d12.items():
        own = [[(min(p[3], CAP * p[2]), min(p[4], CAP * p[2])) if p[7] else (p[3], p[4]) for p in L] for L in g['lines']]
        W = matched(g, d24[ch]) if ch in d24 else own
        lines = [[p[:3] + [(1 - t) * o[0] + t * w[0], (1 - t) * o[1] + t * w[1]] + p[5:] for p, o, w in zip(L, O, M)]
                 for L, O, M in zip(g['lines'], own, W)]
        G[ch] = (glyph(lines, shrink, s), g['adv'] / s)
    return G


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'centerlines'), exist_ok=True)
    D = {}
    for f in ('newyork12', 'newyork24'):
        D[f] = decompose(f)
        json.dump({c: {k: v for k, v in g.items() if k != 'raster'} for c, g in D[f].items()},
                  open(os.path.join(ROOT, 'centerlines', f'{f}.json'), 'w'), ensure_ascii=False)
        print(f, len(D[f]), 'glyphs decomposed')
    # the blends: New York 12's centerlines with bearings t of the way to New York 24's
    for t in [float(a) for a in sys.argv[1:]] or [0.5]:
        key = 'newyork12blend' if t == 0.5 else f'newyork12blend{int(round(t * 100)):02d}'
        B.VERSIONS.setdefault(key, B.BLEND_VERSION); B.SOURCE[key] = 'newyork12'; B.SIZE[key] = 12
        B.NAMES.setdefault(key, 'New York 12 Blend HD' if t == 0.5 else f'New York 12 Blend {int(round(t * 100))} HD')
        B.ORIGINAL[key] = B.ORIGINAL['newyork12']
        B.MID[key] = (f' Its letters are New York 12\'s, drawn along their centerlines with pen widths '
                      f'{int(round(t * 100))} % of the way from New York 12\'s to New York 24\'s.')
        strike, metrics = bitmap.strike('newyork12')
        G = blend(t, D['newyork12'], D['newyork24'])
        B.font(key, True, (G, strike, metrics)); B.font(key, False, (G, strike, metrics))

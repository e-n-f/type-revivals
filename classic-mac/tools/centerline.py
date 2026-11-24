"""New York 12 and 24 as centerlines and bearings, and New York 12's centerlines set with bearings between the two.

    python3 tools/centerline.py [t ...]

Each glyph is decomposed, in em units (1000 to the em), into
  - its centerlines: the paths of its strokes' skeleton, each point with the radius of the stroke there (its
    distance to the edge of the ink), so that a round pen of that radius drawn along them gives the glyph back;
  - its bearings: the space left of its ink and right of it, inside its advance.
The glyphs are the traced outlines, unthinned (LIGHTEN 0): the strokes at the bitmap's own weight.

New York 12 Blend HD draws New York 12's centerlines (less LIGHTEN a side, as the other fonts are thinned) with
each glyph's bearings a fraction t of the way from New York 12's to New York 24's: the letters of 12, spaced
between 12 and 24. t = 0 gives New York 12's own spacing (a check of the decomposition against New York 12 HD).
centerlines/<font>.json keep the decompositions. specimen/centerline-newyork.png shows them (New York 12's and
24's ink with their centerlines in red, blue where a stroke is over 1.3 times the glyph's median radius; between,
New York 12 drawn back from its centerlines), and specimen/newyork-blend.png sets the blend between the two.
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


def decompose(font):
    """{char: dict(lines=[[(x, y, r), ...], ...], lsb, rsb, adv, ink=[x0, x1])} in em units, unthinned"""
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
        sk = skeletonize(m.astype(bool))
        lines = []
        for path in paths(sk):
            P = [(float(c + x0), float(y1 - r), float(dist[r, c])) for r, c in path]
            lines.append([[round(v, 1) for v in p] for p in simplify(P)])
        cols = np.nonzero(m.any(0))[0]
        ink = [float(cols[0] + x0), float(cols[-1] + 1 + x0)]
        out[ch] = dict(lines=lines, adv=adv * s, ink=ink, lsb=ink[0], rsb=adv * s - ink[1])
    return out


def draw(lines, shrink=0.0, dx=0.0):
    """a round pen of each point's radius less shrink, drawn along the centerlines: ink in em units"""
    xs = [p[0] + dx for L in lines for p in L]; ys = [p[1] for L in lines for p in L]
    R = max(p[2] for L in lines for p in L)
    x0, y1 = int(min(xs) - R) - 8, int(max(ys) + R) + 8
    W, H = int(max(xs) + R) + 8 - x0, y1 - int(min(ys) - R) + 8
    m = np.zeros((H, W), np.uint8)
    for L in lines:
        pts = [(p[0] + dx, p[1], p[2]) for p in L]
        if len(pts) == 1: pts = pts * 2
        for (xa, ya, ra), (xb, yb, rb) in zip(pts, pts[1:]):
            n = max(2, int(np.hypot(xb - xa, yb - ya)) + 1)
            for t in np.linspace(0, 1, n):
                r = (1 - t) * ra + t * rb - shrink
                if r > 0.5:
                    cv2.circle(m, (int(round((1 - t) * xa + t * xb - x0)), int(round(y1 - ((1 - t) * ya + t * yb)))),
                               int(round(r)), 1, -1, cv2.LINE_8)
    return m, x0, y1


def glyph(lines, shrink, dx, s):
    """the outlines of the centerlines drawn with shrink, in font units (s em units per font unit)"""
    m, x0, y1 = draw(lines, shrink, dx)
    f = cv2.resize(m.astype(np.float32), (int(round(m.shape[1] / s)), int(round(m.shape[0] / s))),
                   interpolation=cv2.INTER_AREA)
    ox, oy = x0 / s, y1 / s                    # the raster's top left in font units
    return [[(seg[0],) + tuple((p[0] + ox, p[1] + oy) for p in seg[1:]) for seg in c] for c in trace.trace(f, B.SIGMA)]


def blend(t, d12, d24):
    """New York 12's centerlines, each glyph's bearings t of the way to New York 24's: {char: (contours, adv)}
    in New York 12's font units"""
    s = EM / (B.SIZE['newyork12'] * B.PX)
    shrink = B.LIGHTEN['newyork12'] * s            # thinned as New York 12 HD is
    G = {}
    for ch, g in d12.items():
        h = d24.get(ch, g)
        lsb = (1 - t) * g['lsb'] + t * h['lsb']; rsb = (1 - t) * g['rsb'] + t * h['rsb']
        dx = lsb - g['lsb']
        adv = g['ink'][1] - g['ink'][0] + lsb + rsb
        G[ch] = (glyph(g['lines'], shrink, dx, s), adv / s)
    return G


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'centerlines'), exist_ok=True)
    D = {}
    for f in ('newyork12', 'newyork24'):
        D[f] = decompose(f)
        json.dump(D[f], open(os.path.join(ROOT, 'centerlines', f'{f}.json'), 'w'), ensure_ascii=False)
        print(f, len(D[f]), 'glyphs decomposed')
    # the blends: New York 12's centerlines with bearings t of the way to New York 24's
    for t in [float(a) for a in sys.argv[1:]] or [0.5]:
        key = 'newyork12blend' if t == 0.5 else f'newyork12blend{int(round(t * 100)):02d}'
        B.VERSIONS.setdefault(key, B.BLEND_VERSION); B.SOURCE[key] = 'newyork12'; B.SIZE[key] = 12
        B.NAMES.setdefault(key, 'New York 12 Blend HD' if t == 0.5 else f'New York 12 Blend {int(round(t * 100))} HD')
        B.ORIGINAL[key] = B.ORIGINAL['newyork12']
        B.MID[key] = (f' Its letters are New York 12\'s, drawn along their centerlines, spaced {int(round(t * 100))} % of '
                      f'the way from New York 12\'s bearings to New York 24\'s.')
        strike, metrics = bitmap.strike('newyork12')
        G = blend(t, D['newyork12'], D['newyork24'])
        B.font(key, True, (G, strike, metrics)); B.font(key, False, (G, strike, metrics))

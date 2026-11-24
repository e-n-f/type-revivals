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
CAP = 1.1                       # a pen width at most this times the stroke's radius (at a join, the normal runs on
                                # into the stroke that crosses)


def widths(m, P, i, r):
    """the ink's reach from point i of path P along its left and right normals (em units), and the left normal"""
    a, b = P[max(0, i - 4)], P[min(len(P) - 1, i + 4)]
    tx, ty = b[0] - a[0], b[1] - a[1]; n = np.hypot(tx, ty)
    if n == 0: return r, r, (0.0, 1.0)
    nx, ny = -ty / n, tx / n                        # the left normal (x right, y up)
    out = []
    for sgn in (1, -1):
        d = 0.0
        while d < CAP * r + 2:
            x, y = P[i][0] + sgn * nx * (d + 0.5), P[i][1] + sgn * ny * (d + 0.5)
            row, col = int(round(m[1] - y)), int(round(x - m[2]))
            if not (0 <= row < m[0].shape[0] and 0 <= col < m[0].shape[1]) or not m[0][row, col]: break
            d += 0.5
        out.append(min(d + 0.5, CAP * r))
    return out[0], out[1], (nx, ny)


def decompose(font):
    """{char: dict(lines=[[(x, y, r, L, R, nx, ny), ...], ...], adv, box=[x0, y0, x1, y1])} in em units, unthinned:
    each centerline point with the stroke's radius there, its left and right pen widths (the ink's reach along
    the centerline's left and right normals) and its left normal"""
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
            P = [(float(c + x0), float(y1 - r)) for r, c in path]
            keep_i = sorted(set(range(0, len(P), STEP)) | {len(P) - 1})
            L = []
            for i in keep_i:
                r = float(dist[path[i]])
                l, rr, (nx, ny) = widths((m, y1, x0), P, i, r)
                L.append([round(v, 1) for v in (P[i][0], P[i][1], r, l, rr)] + [round(nx, 3), round(ny, 3)])
            lines.append(L)
        rows, cols = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
        box = [float(cols[0] + x0), float(y1 - rows[-1] - 1), float(cols[-1] + 1 + x0), float(y1 - rows[0])]
        out[ch] = dict(lines=lines, adv=adv * s, box=box)
    return out


def draw(lines, shrink=0.0):
    """a pen of each point's left and right widths, less shrink each, swept along the centerlines, with round
    joins and ends: ink in em units (1 px = 1 em unit), and the raster's left and top"""
    xs = [p[0] for L in lines for p in L]; ys = [p[1] for L in lines for p in L]
    R = max(max(p[3], p[4]) for L in lines for p in L)
    x0, y1 = int(min(xs) - R) - 8, int(max(ys) + R) + 8
    W, H = int(max(xs) + R) + 8 - x0, y1 - int(min(ys) - R) + 8
    m = np.zeros((H, W), np.uint8)
    px = lambda x, y: (x - x0, y1 - y)
    for L in lines:
        pts = [(x, y, max(l - shrink, 0.3), max(r - shrink, 0.3), nx, ny) for x, y, _, l, r, nx, ny in L]
        for x, y, l, r, nx, ny in pts:                   # round joins and ends
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


NEAR = 60                       # em units: a New York 24 centerline point further than this from New York 12's
                                # (its glyph fitted onto 12's by their boxes) is no match


def matched(g, h):
    """New York 24's pen widths at each of New York 12's centerline points: New York 24's glyph h fitted onto
    New York 12's g by their ink boxes, each point of g taking the left and right widths of the nearest point of
    h (swapped where its centerline runs the other way); unmatched points keep g's widths scaled by the two
    glyphs' median ratio. The widths are not scaled with the box: a stroke stays as thick, in ems, as in 24."""
    (a0, b0, a1, b1), (c0, d0, c1, d1) = g['box'], h['box']
    sx, sy = (a1 - a0) / (c1 - c0), (b1 - b0) / (d1 - d0)
    H = np.array([(a0 + (p[0] - c0) * sx, b0 + (p[1] - d0) * sy, p[3], p[4], p[5] / sx, p[6] / sy)
                  for L in h['lines'] for p in L])
    nrm = np.hypot(H[:, 4], H[:, 5]); H[:, 4] /= nrm; H[:, 5] /= nrm
    ratio = np.median(H[:, 2] + H[:, 3]) / np.median([p[3] + p[4] for L in g['lines'] for p in L])
    out = []
    for L in g['lines']:
        M = []
        for p in L:
            d = np.hypot(H[:, 0] - p[0], H[:, 1] - p[1]); j = int(np.argmin(d))
            if d[j] > NEAR: M.append((p[3] * ratio, p[4] * ratio)); continue
            l, r = H[j, 2], H[j, 3]
            if H[j, 4] * p[5] + H[j, 5] * p[6] < 0: l, r = r, l
            M.append((l, r))
        out.append(M)
    return out


def blend(t, d12, d24):
    """New York 12's centerlines, advances and spacing, its pen widths t of the way to New York 24's, and thinned
    t of the way from New York 12 HD's thinning to 24 HD's: {char: (contours, adv)} in New York 12's font units"""
    s = EM / (B.SIZE['newyork12'] * B.PX)
    shrink = (1 - t) * B.LIGHTEN['newyork12'] * s + t * B.LIGHTEN['newyork24'] * EM / (B.SIZE['newyork24'] * B.PX)
    G = {}
    for ch, g in d12.items():
        W = matched(g, d24[ch]) if ch in d24 else [[(p[3], p[4]) for p in L] for L in g['lines']]
        lines = [[p[:3] + [(1 - t) * p[3] + t * w[0], (1 - t) * p[4] + t * w[1]] + p[5:] for p, w in zip(L, M)]
                 for L, M in zip(g['lines'], W)]
        G[ch] = (glyph(lines, shrink, s), g['adv'] / s)
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
        B.MID[key] = (f' Its letters are New York 12\'s, drawn along their centerlines with pen widths '
                      f'{int(round(t * 100))} % of the way from New York 12\'s to New York 24\'s.')
        strike, metrics = bitmap.strike('newyork12')
        G = blend(t, D['newyork12'], D['newyork24'])
        B.font(key, True, (G, strike, metrics)); B.font(key, False, (G, strike, metrics))

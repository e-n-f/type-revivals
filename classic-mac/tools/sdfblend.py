"""New York 12 and 24 blended in raster space: New York 24 warped onto New York 12, and their distance fields averaged.

    python3 tools/sdfblend.py [t ...]          # t = 0.5 by default

For each glyph:
  1. both fonts' unthinned outlines (LIGHTEN 0) are rasterized at 1000 em units to the em;
  2. New York 24's glyph is fitted onto New York 12's: across by their ink boxes; up and down, for a letter, by
     the fonts' guide lines (descender, baseline, x-height, cap height, ascender) stretched linearly between them,
     and for a figure or a sign by its box (New York's old-style figures hang below the baseline, each font's by
     its own amount); a spacing accent (` ´ ^ ¨) keeps its own size, centred on 12's;
  3. it is registered to New York 12's by a smoothed thin-plate spline, fitted through pairs again and again
     (ROUNDS): for a letter, points of the two glyphs' ink edges facing the same way (mutual nearest), so that a
     stroke's sides meet the other's, and its thickness and ends morph as shapes (a crossbar's square end stays
     square, a serif's foot stays on the baseline, crossbars meet at their heights); for a figure or a sign,
     points of their centerlines (centerlines/, from tools/centerline.py) running the same way, with the stroke
     ends and the edges on the guide lines held to each other. Small pieces of ink (dots, accents) are paired by
     their centres and held;
  4. the two glyphs' signed distance fields (positive inside; outside, the chessboard distance, whose contours
     round a corner stay square) are warped to the shape t of the way from 12's to 24's (MORPH); 24's is kept
     within GROW outside and THIN inside 12's (where the warp goes wrong it can't put ink in a counter, nor lose an
     accent); they are averaged, t of the way to 24's, less the thinning (t of the way from New York 12 HD's to 24
     HD's); and the result is traced at its edge, specks off 12's ink dropped.
In the lower case, upright strokes are thickened SIDES a side across and stems thinned STEM_THIN more
(lighten_stems()): as thick as the thick of a curve, stems looked heavier than the curves, which thin round from
it. New York 24's two bars of ¢ and $ are run together (MERGE); ª º are fitted by their boxes (SUPERIOR); a's
counter is smoothed (COUNTERS); s and g, whose rounds read heavy, are thinned instead of thickened (LIGHTER);
§ ™ are New York 12's own at the blend's weight (OWN). W and w are two of the blended V and v side by side
(DOUBLED): the W across its advance less the V's sidebearings, its V's narrowed a little to stand as far apart
as New York 24's, crossed near the top; the w across New York 12's w, its v's meeting at the top, as 12's. A
glyph whose blend comes apart (in more or fewer pieces than New York 12's) is blended again with New York 12's shape kept, then a
quarter of the way, else is New York 12's own, thinned; the build lists them. The advances and spacing are New
York 12's exactly.
"""
import os, sys, unicodedata
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import build as B, bitmap
from centerline import flatten, raster, EM
sys.path.insert(0, os.path.join(ROOT, '..', 'common'))
import trace

FLOW = 4                        # em units to a pixel of the registration's canvas
BLUR = 3                        # its ink blurred by this (pixels of the canvas, a Gaussian's sigma)
WIN = 31                        # the flow's window (canvas pixels)
SMOOTH = 6                      # the flow field smoothed by this (canvas pixels, a Gaussian's sigma)
GROW = 20                       # em units: the furthest New York 24's ink may lie outside New York 12's
THIN = 32                       # em units: the most New York 12's strokes may thin a side (to 24's hairlines)
MARGIN = 150                    # em units round New York 12's glyph that the blend covers
FAR = 1000.0                    # the distance field outside New York 24's raster


def unthinned(font):
    """{char: (ink 0/1, x0, y1, advance)} in em units: the font's outlines unthinned, rasterized"""
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
        out[ch] = (m, x0, y1, adv * s)
    return out


def sdf(m):
    """signed distance to the ink's edge, positive inside (em units). Outside the ink it is the chessboard
    distance, whose contours round a corner stay square: averaged, two crossbars that end a little apart end square
    (an f's, a t's), where the Euclidean distance's round contours would round them"""
    m = m.astype(np.uint8)
    return cv2.distanceTransform(m, cv2.DIST_L2, 5) - cv2.distanceTransform(1 - m, cv2.DIST_C, 3)


def box(m, x0, y1):
    rows, cols = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
    return cols[0] + x0, y1 - rows[-1] - 1, cols[-1] + 1 + x0, y1 - rows[0]


def lines_image(lines, X0, Y1, W, H, fit=lambda x, y: (x, y)):
    """centerlines drawn as soft lines on the registration's canvas"""
    im = np.zeros((H // FLOW, W // FLOW), np.uint8)
    for L in lines:
        P = np.array([((fit(p[0], p[1])[0] - X0) / FLOW, (Y1 - fit(p[0], p[1])[1]) / FLOW) for p in L])
        if len(P) == 1: P = np.vstack([P, P])
        cv2.polylines(im, [np.round(P * 4).astype(np.int32)], False, 255, 6, cv2.LINE_AA, 2)
    return cv2.GaussianBlur(im, (0, 0), BLUR)


EDGE_BEND = 1000                # the thin-plate spline's smoothing, registering by edges
BY_EDGES = True                 # letters registered by the glyphs' ink edges (tps_edges()), not their centerlines
MORPH = True                    # the blend's shapes moved t of the way to New York 24's, not New York 12's kept
ANCHOR = 12                     # em units: an edge this near a guide line is on it
EDGE_STEP = 10                  # em units between the edges sampled along the guide lines
DOUBLED = {'W': 'V', 'w': 'v'}  # made of two of another (doubled())
APART = {'W': 0.405}            # ... spread across the advance (less the V's sidebearings), the second V this much of
                                # a V's width right of the first, as in New York 24's W (12's W is too narrow for
                                # two of the V: they would almost coincide)
PIECE = 200                     # em units squared: a piece of ink this small isn't counted
FELL = []                       # the glyphs blended less than the rest (blend())
STEM_RUN = 350                  # em units: an upright run of ink longer than this is a stem (not the side of an o)
STEM_THIN = 4                   # em units a side that lower-case stems are thinned
SIDES = 5                       # em units a side that a lower-case letter's upright strokes are thickened (the sides
                                # of an o), its stems thinned STEM_THIN more than that
COUNTERS = {c: 30 for c in 'aàáâãäå'}            # em units: these glyphs' counters smoothed, bumps and bites narrower than this gone
MERGE = {'¢': 60, '$': 60}      # em units: New York 24's two bars, this far apart, run together into one as New York 12's
OWN = '§™'                      # New York 12's own, at the blend's weight (New York 12 Mid HD's): too unlike 24's to blend
SUPERIOR = 'ªº'                 # letters set high: fitted by their boxes, not the guide lines
LIGHTER = {'s': 4, 'g': 6}      # em units a side these glyphs are thinned more (their rounds read heavy), not thickened SIDES
CHAR = ''                       # the glyph blend_glyph() is blending
STEM_FADE = 15                  # em units the thinning fades in over
SMALL = 0.25                    # a piece of ink less than this of the glyph's largest is a dot or an accent
NEAR = 150                      # em units: the furthest two such pieces are paired
SPECK = 2500                    # em units squared: a piece of the blend this small, off New York 12's ink, is dropped
ROUNDS = 6                      # rounds of matching and fitting (registration by centerlines)
PAIR = 60                       # em units: the furthest a centerline point is matched
ALIGNED = 0.7                   # ... to one whose stroke runs within 45 degrees of its own
BEND = 300                      # the thin-plate spline's smoothing


def pieces(m, x0, y1):
    """the separate pieces of a glyph's ink: their centres (em units) and areas"""
    n, lab, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    return [((cen[i][0] + x0 + 0.5, y1 - cen[i][1] - 0.5), st[i][4]) for i in range(1, n)]


def anchors(g, h, inv):
    """pairs of the centres of the two glyphs' small pieces of ink (a dot, an accent): each of New York 12's
    paired with the nearest of New York 24's (fitted onto it), one to one. A dot has no stroke direction to be
    matched by, and unmoved it would be cross-faded in two halves"""
    a = [(c, s) for c, s in pieces(*g[:3])]; b = [(inv(*c), s) for c, s in pieces(*h[:3])]
    big_a, big_b = max(s for _, s in a), max(s for _, s in b)
    a = [c for c, s in a if s < SMALL * big_a]; b = [c for c, s in b if s < SMALL * big_b]
    pairs = sorted((np.hypot(p[0] - q[0], p[1] - q[1]), i, j) for i, p in enumerate(a) for j, q in enumerate(b))
    used_a, used_b, out = set(), set(), []
    for d, i, j in pairs:
        if d > NEAR or i in used_a or j in used_b: continue
        used_a.add(i); used_b.add(j); out.append((a[i], b[j]))
    return out


def guides(R):
    """a font's guide lines, in em units, from its rasters: (baseline, x-height, cap height, ascender, descender)"""
    b = lambda c: box(*R[c][:3])
    return b('x')[1], b('x')[3], b('H')[3], b('h')[3], b('p')[1]


def guide_pins(g, D24f, warp, inv_y, G12, G24):
    """pairs holding the guide lines: where New York 12's ink has an edge on a guide line (a serif's foot on the
    baseline, an arch's top on the x-height), the edge is pinned to the same guide line of New York 24's, where the
    warp puts it across, if 24's ink has an edge there too. Lined up by their centerlines, a thin serif of 24's
    would sit on the middle of 12's thicker one, and its edge sag from the baseline"""
    m, x0, y1, _ = g
    lines = [(G12[0], G24[0], -1), (G12[4], G24[4], -1), (G12[1], G24[1], 1), (G12[2], G24[2], 1), (G12[3], G24[3], 1)]
    out = []
    for c in range(0, m.shape[1], EDGE_STEP):
        col = m[:, c]
        rows = np.nonzero(col[1:] != col[:-1])[0]          # edges down the column, between rows r and r + 1
        x = c + x0 + 0.5
        for r in rows:
            y = y1 - (r + 1)                                # the edge's height
            top = col[r + 1] > col[r]                       # ink below it: a top edge
            for y12, y24, side in lines:
                if abs(y - y12) > ANCHOR or (side == 1) != top: continue
                qx, _ = warp(np.array([[x, y]]))[0]
                qy = inv_y(y24) + (y - y12)                 # 24's guide, on the canvas, as far off it as 12's edge
                if abs(D24f(qx, qy)) < ANCHOR: out.append(((x, y), (qx, qy)))
    return out


def end_pins(L12, L24, inv):
    """pairs of the two glyphs' stroke ends: each free end of New York 12's centerlines (a crossbar's tip, an
    arm's end) paired with the nearest free end of 24's (fitted) whose stroke runs the same way, one to one. Held,
    ends meet ends, and the warp doesn't shear a square end in between"""
    def ends(L, f):
        out = []
        for l in L:
            if not l or l[0][8] == 0 or len(l) < 2: continue
            for p, q in ((l[0], l[1]), (l[-1], l[-2])):
                x, y = f(p[0], p[1]); a, b = f(q[0], q[1])
                d = np.hypot(x - a, y - b) or 1
                out.append(((x, y), ((x - a) / d, (y - b) / d)))   # the end, and the stroke's way out to it
        return out
    a, b = ends(L12, lambda x, y: (x, y)), ends(L24, inv)
    pairs = sorted((np.hypot(p[0] - q[0], p[1] - q[1]), i, j) for i, (p, u) in enumerate(a)
                   for j, (q, v) in enumerate(b) if u[0] * v[0] + u[1] * v[1] > ALIGNED)
    used_a, used_b, out = set(), set(), []
    for d, i, j in pairs:
        if d > PAIR or i in used_a or j in used_b: continue
        used_a.add(i); used_b.add(j); out.append((a[i][0], b[j][0]))
    return out


def edges(m, x0, y1, to=lambda x, y: (x, y), step=8):
    """points along a glyph's ink edges, every step em units, with their outward normals: [(x, y, nx, ny)]"""
    S = cv2.GaussianBlur(sdf(m).astype(np.float32), (0, 0), 2)
    gy, gx = np.gradient(S)                                    # (row, col) gradient: inward
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        for col, row in c[::step, 0]:
            nx, ny = -gx[row, col], gy[row, col]               # outward, y up
            n = np.hypot(nx, ny)
            if n == 0: continue
            x, y = to(col + x0 + 0.5, y1 - row - 0.5)
            out.append((x, y, nx / n, ny / n))
    return np.array(out)


def tps_edges(E12, E24, pins=()):
    """the warp carrying New York 12's ink edges E12 onto 24's E24 (fitted onto the canvas): each edge point of
    12's matched to the nearest of 24's facing the same way (its outward normal within 45 degrees), a smoothed
    thin-plate spline through the pairs, ROUNDS times. Matching edges to edges, a stroke's sides meet the other's
    sides: morphed, its thickness and its ends move as shapes, and a square end stays square"""
    from scipy.interpolate import RBFInterpolator
    if len(E12) < 4 or len(E24) < 4: return lambda Z: Z
    P, Q = E12[:, :2], E24[:, :2]
    ok = (E12[:, 2:] @ E24[:, 2:].T) >= ALIGNED
    warp = lambda Z: Z
    for _ in range(ROUNDS):
        Pm = warp(P)
        d = np.hypot(Pm[:, None, 0] - Q[None, :, 0], Pm[:, None, 1] - Q[None, :, 1]); d[~ok] = np.inf
        j = np.argmin(d, 1); keep = d[np.arange(len(P)), j] < PAIR
        # mutual pairs only: 24's point's own nearest of 12's (facing the same way) is this one, or next to it
        back = np.argmin(d, 0)
        keep &= np.hypot(*(P[back[j]] - P).T) < 3 * 8
        if keep.sum() < 4: break
        src, dst = P[keep], Q[j[keep]]
        if pins:
            src = np.vstack([src] + [np.array([p for p, _ in pins])] * 10)
            dst = np.vstack([dst] + [np.array([q for _, q in pins])] * 10)
        rbf = RBFInterpolator(src, dst - src, kernel='thin_plate_spline', smoothing=EDGE_BEND)
        warp = lambda Z, rbf=rbf: Z + rbf(Z)
    return warp


def tps_register(L12, L24, inv, pins=()):
    """the warp carrying New York 12's centerlines L12 onto New York 24's L24 (inv: h's em units -> the
    canvas): each point of 12's centerline matched to the nearest point of 24's whose stroke runs the same way,
    a smoothed thin-plate spline fitted through the pairs, and again, ROUNDS times, each round matching from
    where the last put 12's points. pins: pairs always held (anchors()), each counted ten times. Returns a
    function from canvas points (n, 2) to their counterparts."""
    from scipy.interpolate import RBFInterpolator
    pts = lambda L, f: [(f(p[0], p[1]), (p[5], p[6])) for l in L for p in l if p[7] != 1]
    P = np.array([q for q, _ in pts(L12, lambda x, y: (x, y))], float)
    N12 = np.array([n for _, n in pts(L12, lambda x, y: (x, y))], float)
    Q = np.array([q for q, _ in pts(L24, inv)], float)
    N24 = np.array([n for _, n in pts(L24, inv)], float)
    if len(P) < 4 or len(Q) < 4: return lambda Z: Z
    ok = np.abs(N12 @ N24.T) >= ALIGNED                       # (P, Q) pairs whose strokes run the same way
    warp = lambda Z: Z
    for _ in range(ROUNDS):
        Pm = warp(P)
        d = np.hypot(Pm[:, None, 0] - Q[None, :, 0], Pm[:, None, 1] - Q[None, :, 1]); d[~ok] = np.inf
        j = np.argmin(d, 1); keep = d[np.arange(len(P)), j] < PAIR
        if keep.sum() < 4: break
        src, dst = P[keep], Q[j[keep]]
        if pins:
            src = np.vstack([src] + [np.array([p for p, _ in pins])] * 10)
            dst = np.vstack([dst] + [np.array([q for _, q in pins])] * 10)
        rbf = RBFInterpolator(src, dst - src, kernel='thin_plate_spline', smoothing=BEND)
        warp = lambda Z, rbf=rbf: Z + rbf(Z)
    return warp


def lighten_stems(D):
    """D with its long upright stems (ink in runs down a column longer than STEM_RUN) thinned STEM_THIN a side,
    fading in over STEM_FADE: a stem as thick as the thick of a curve looks heavier than the curve, which thins
    round from it"""
    ink = D > 0
    run = np.zeros(D.shape, np.float32)
    for c in range(D.shape[1]):
        col = ink[:, c]
        d = np.diff(np.r_[0, col.astype(np.int8), 0]); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]
        for a, b in zip(s, e): run[a:b, c] = b - a
    w = cv2.GaussianBlur((run > STEM_RUN).astype(np.float32), (0, 0), STEM_FADE)
    return D - (STEM_THIN + SIDES) * np.clip(w * 2, 0, 1)


def blend_glyph(g, h, t, shrink, cl=None, G=None, by_guides=True, keep_size=False, stems=False):
    """New York 12's glyph g and 24's h, (ink, x0, y1, adv): the blended ink on a canvas round g, (f, x0, y1),
    f the field to trace (0 to 1, its edge at 0.5)"""
    m12, x12, y12, _ = g; m24, x24, y24, _ = h
    if CHAR in MERGE:   # 24's two bars (¢ $) run together, to register with 12's one
        m24 = cv2.morphologyEx(m24.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((1, MERGE[CHAR] + 1), np.uint8)).astype(m24.dtype)
    a0, b0, a1, b1 = box(m12, x12, y12); c0, d0, c1, d1 = box(m24, x24, y24)
    sx, sy = (a1 - a0) / (c1 - c0), (b1 - b0) / (d1 - d0)
    if keep_size:   # a spacing accent (` ´ ^ ~ ¨): 24's, half the size of 12's, centred on 12's, not stretched to it
        sx = sy = 1.0
        c0, d0 = c0 - ((a0 + a1) - (c0 + c1)) / 2 + (a0 - c0), d0 - ((b0 + b1) - (d0 + d1)) / 2 + (b0 - d0)
        a0, b0 = a0, b0
    # vertically, a letter of h is fitted to g by the fonts' guide lines (descender, baseline, x-height, cap height,
    # ascender), stretched linearly between them, so that 24's x-height falls on 12's and so on, whatever the
    # glyph's own box (an accented capital's takes in its accent); a figure or a sign, which doesn't keep to them
    # (New York's old-style 3 and 9 hang below the baseline, each font's by its own amount), by its box; across, by
    # the boxes
    if G and by_guides and not keep_size:
        g12, g24 = sorted(G[0]), sorted(G[1])
        def piecewise(y, src, dst):
            y = np.asarray(y, np.float64)
            out = np.interp(y, src, dst)
            lo, hi = y < src[0], y > src[-1]
            out = np.where(lo, dst[0] + (y - src[0]) * (dst[1] - dst[0]) / (src[1] - src[0]), out)
            return np.where(hi, dst[-1] + (y - src[-1]) * (dst[-1] - dst[-2]) / (src[-1] - src[-2]), out)
        to12 = lambda y: piecewise(y, g24, g12); to24 = lambda y: piecewise(y, g12, g24)
    else:
        to12 = lambda y: b0 + (np.asarray(y) - d0) * sy; to24 = lambda y: d0 + (np.asarray(y) - b0) / sy
    # the canvas: g's box and a margin, in em units (1 px = 1 em unit), x0 left and Y1 top
    X0, Y1 = int(a0) - MARGIN, int(b1) + MARGIN
    W, H = int(a1) + MARGIN - X0, Y1 - (int(b0) - MARGIN)
    xs = np.arange(W) + X0 + 0.5; ys = Y1 - np.arange(H) - 0.5
    X, Y = np.meshgrid(xs, ys)
    # g's distance field on the canvas
    D12 = cv2.remap(sdf(m12).astype(np.float32), (X - x12).astype(np.float32), (y12 - Y).astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-FAR)
    # h fitted by the boxes: its ink on the canvas
    fx = lambda X: c0 + (X - a0) / sx; fy = to24                              # canvas -> h's em units
    S24 = sdf(m24).astype(np.float32)
    fit = lambda Xs, Ys: cv2.remap(S24, (fx(Xs) - x24).astype(np.float32), (y24 - fy(Ys)).astype(np.float32),
                                   cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-FAR)
    # the registration, on a coarser canvas: optical flow from g's ink (blurred) to fitted h's
    small = lambda D: cv2.GaussianBlur(cv2.resize((D > 0).astype(np.float32), (W // FLOW, H // FLOW),
                                                  interpolation=cv2.INTER_AREA), (0, 0), BLUR)
    if cl:      # the two glyphs' centerlines (centerline.py): matched point to point, a thin-plate spline through them
        inv = lambda x, y: (a0 + (x - c0) * sx, float(to12(y)))           # h's em units -> the canvas
        pins = anchors(g, h, inv)
        if BY_EDGES and by_guides:    # a letter: the two glyphs' ink edges matched (a figure or a sign, whose
                                      # curves change thickness along them, by its centerlines)
            warp = tps_edges(edges(*g[:3]), edges(*h[:3], to=inv), pins)
        else:
            pins = pins + end_pins(cl[0], cl[1], inv)
            warp = tps_register(cl[0], cl[1], inv, pins)
            if G:       # then held at the guide lines too, and registered again
                D24f = lambda x, y: float(fit(np.array([[x]], np.float32), np.array([[y]], np.float32))[0, 0])
                pins = pins + guide_pins(g, D24f, warp, lambda y: float(to12(y)), *G)
                warp = tps_register(cl[0], cl[1], inv, pins)
        gx, gy = np.meshgrid(np.arange(0, W, FLOW) + X0 + 0.5, Y1 - np.arange(0, H, FLOW) - 0.5)
        Z = warp(np.c_[gx.ravel(), gy.ravel()])
        TX = cv2.resize(Z[:, 0].reshape(gx.shape).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        TY = cv2.resize(Z[:, 1].reshape(gy.shape).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        # the shapes moved t of the way too: each point of the blend takes 12's ink from t of the way back along
        # the warp, and 24's from the rest of the way on
        UX, UY = TX - X, TY - Y
        D12 = cv2.remap(sdf(m12).astype(np.float32), (X - t * UX - x12).astype(np.float32),
                        (y12 - (Y - t * UY)).astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT, borderValue=-FAR) if MORPH else D12
        D24 = fit(X + (1 - t) * UX, Y + (1 - t) * UY) if MORPH else fit(TX, TY)
    else:       # their ink, blurred: optical flow between them
        A = np.clip(small(D12) * 255, 0, 255).astype(np.uint8); Bf = np.clip(small(fit(X, Y)) * 255, 0, 255).astype(np.uint8)
        flow = cv2.calcOpticalFlowFarneback(A, Bf, None, 0.5, 4, WIN, 6, 7, 1.5, cv2.OPTFLOW_FARNEBACK_GAUSSIAN)
        # smoothed, and trusted only near ink (in blank space optical flow has nothing to follow, and points
        # anywhere): each pixel's flow the average of its neighbours', weighted by the ink of either glyph about them
        w = cv2.GaussianBlur(np.maximum(A, Bf).astype(np.float32) / 255, (0, 0), BLUR) + 1e-3
        flow = (cv2.GaussianBlur(flow * w[..., None], (0, 0), SMOOTH)
                / cv2.GaussianBlur(w, (0, 0), SMOOTH)[..., None])
        flow = cv2.resize(flow, (W, H), interpolation=cv2.INTER_LINEAR) * FLOW     # canvas px, x right and y down
        D24 = fit(X + flow[..., 0], Y - flow[..., 1])
    # New York 24 kept near New York 12: no ink more than GROW outside 12's (where the warp misplaces a stroke,
    # into a counter), nor 12's thinned by more than THIN a side (where 24's part is elsewhere: an accent)
    D24 = np.clip(D24, D12 - THIN, D12 + GROW)
    D = (1 - t) * D12 + t * D24 - shrink
    if stems:   # a lower-case letter: its upright strokes thickened SIDES a side, its stems as much less again
        D = cv2.dilate(D, np.ones((1, 2 * SIDES + 1), np.uint8)) if SIDES and CHAR not in LIGHTER else D - LIGHTER.get(CHAR, 0)
        D = lighten_stems(D)
    if CHAR in COUNTERS:    # its counters smoothed: bumps and bites the warp left where the two designs' joins differ
        r = COUNTERS[CHAR]; k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        ink = (D > 0).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(1 - ink, 4)
        for i in range(1, n):
            x, y, w, h, _ = st[i]
            if x == 0 or y == 0 or x + w == D.shape[1] or y + h == D.shape[0]: continue      # outside, not a counter
            c = (lab == i).astype(np.uint8)
            s = cv2.morphologyEx(cv2.morphologyEx(c, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
            D = np.where((c > s), 1.0, np.where(s > c, -1.0, D)).astype(np.float32)
    # a small piece of the blend mostly off New York 12's ink is a speck the warp left: dropped
    n, lab, st, _ = cv2.connectedComponentsWithStats((D > 0).astype(np.uint8), 8)
    for i in range(1, n):
        if st[i][4] < SPECK and (D12[lab == i] > 0).mean() < 0.5: D[lab == i] = -1
    return np.clip(0.5 + D / 2, 0, 1).astype(np.float32), X0, Y1


def doubled(fv, target, apart=None):
    """a W of two V's (or a w of two v's): two copies of the blended V's ink, side by side, spanning New York 12's W
    across (its ink box, target); where they overlap, their middle strokes cross, as New York 24's W's do. New York
    12's W and 24's differ in their middle (one apex; two V's crossed), and blended they mix the two"""
    f, X0, Y1 = fv
    cols = np.nonzero((f > 0.5).any(0))[0]
    v0, v1 = cols[0] + X0, cols[-1] + 1 + X0                 # the V's ink across, em units
    a0, _, a1, _ = target
    if apart:   # each V narrowed so that the second is this fraction of a V's width right of the first
        s = (a1 - a0) / (1 + apart) / (v1 - v0)
        f = cv2.resize(f, (int(round(f.shape[1] * s)), f.shape[0]), interpolation=cv2.INTER_AREA)
        X0 = v0 - (v0 - X0) * s; v1 = v0 + (v1 - v0) * s
    dx = int(round((a1 - a0) - (v1 - v0)))                    # the second V this far right of the first
    out = np.zeros((f.shape[0], f.shape[1] + max(dx, 0)), np.float32)
    out[:, :f.shape[1]] = f
    out[:, dx:dx + f.shape[1]] = np.maximum(out[:, dx:dx + f.shape[1]], f)
    return out, int(round(X0 + (a0 - v0))), Y1


def blend(t, R12, R24, C12=None, C24=None):
    """{char: (contours, adv)} in New York 12's font units; C12, C24 the fonts' centerlines, to register by"""
    s = EM / (B.SIZE['newyork12'] * B.PX)
    shrink = (1 - t) * B.LIGHTEN['newyork12'] * s + t * B.LIGHTEN['newyork24'] * EM / (B.SIZE['newyork24'] * B.PX)
    global MORPH, CHAR
    G12, G24 = guides(R12), guides(R24)
    G, fields = {}, {}
    # W and w last: two of the blended V and v (doubled()), not blends of their own
    R12 = dict(sorted(R12.items(), key=lambda kv: kv[0] in DOUBLED))
    own = lambda g: (np.clip(0.5 + (sdf(g[0]) - shrink) / 2, 0, 1).astype(np.float32), g[1], g[2])
    for ch, g in R12.items():
        if ch in DOUBLED and DOUBLED[ch] in fields:
            if ch in APART:     # spanning 12's W's advance less the V's sidebearings, the V's apart as 24's are
                v = R12[DOUBLED[ch]]; vb = box(*v[:3])
                f, X0, Y1 = doubled(fields[DOUBLED[ch]], (vb[0], 0, g[3] - (v[3] - vb[2]), 0), APART[ch])
            else:
                f, X0, Y1 = doubled(fields[DOUBLED[ch]], box(*g[:3]))
        elif ch in OWN:     # New York 12's own, thinned as New York 12 Mid HD is
            f, X0, Y1 = np.clip(0.5 + (sdf(g[0]) - B.LIGHTEN['newyork12mid'] * s) / 2, 0, 1).astype(np.float32), g[1], g[2]
        elif ch in R24:
            cl = (C12[ch]['lines'], C24[ch]['lines']) if C12 and ch in C12 and ch in C24 else None
            # a glyph whose blend comes apart (in more or fewer pieces than New York 12's: where the two designs
            # differ, a stem of 12's that 24's lacks thins away) is blended again with its shape kept, then a
            # quarter of the way only, and else is New York 12's own, thinned
            want = len([1 for _, a in pieces(*g[:3]) if a > PIECE])
            for morph, u in ((True, t), (False, t), (False, t / 2)):
                MORPH = morph; CHAR = ch
                f, X0, Y1 = blend_glyph(g, R24[ch], u, shrink, cl, (G12, G24),
                                        unicodedata.category(ch).startswith('L') and ch not in SUPERIOR, unicodedata.category(ch) == 'Sk',
                                        unicodedata.category(ch) == 'Ll')
                if len([1 for _, a in pieces(f > 0.5, X0, Y1) if a > PIECE]) == want: break
            else:
                f, X0, Y1 = own(g); FELL.append(ch)
            MORPH = True
            if (morph, u) != (True, t) and ch not in FELL: FELL.append(ch)
        else:                       # nothing to blend with: New York 12's own, thinned
            f, X0, Y1 = own(g)
        fields[ch] = (f, X0, Y1)
        f = cv2.resize(f, (int(round(f.shape[1] / s)), int(round(f.shape[0] / s))), interpolation=cv2.INTER_AREA)
        ox, oy = X0 / s, Y1 / s
        G[ch] = ([[(seg[0],) + tuple((p[0] + ox, p[1] + oy) for p in seg[1:]) for seg in c]
                  for c in trace.trace(f, B.SIGMA)], g[3] / s)
    return G


if __name__ == '__main__':
    R12, R24 = unthinned('newyork12'), unthinned('newyork24')
    # the two fonts' centerlines (tools/centerline.py), which register the glyphs better than their ink
    import json
    C = [json.load(open(os.path.join(ROOT, 'centerlines', f'{f}.json'))) for f in ('newyork12', 'newyork24')]
    for t in [float(a) for a in sys.argv[1:]] or [0.5]:
        key = 'newyork12blend' if t == 0.5 else f'newyork12blend{int(round(t * 100)):02d}'
        B.VERSIONS.setdefault(key, B.BLEND_VERSION); B.SOURCE[key] = 'newyork12'; B.SIZE[key] = 12
        B.NAMES.setdefault(key, 'New York 12 Blend HD' if t == 0.5 else f'New York 12 Blend {int(round(t * 100))} HD')
        B.ORIGINAL[key] = B.ORIGINAL['newyork12']
        B.MID[key] = (f' New York 12 blended {int(round(t * 100))} % of the way to New York 24: New York 24 warped onto '
                      f'New York 12, their distance fields averaged; New York 12\'s spacing.')
        strike, metrics = bitmap.strike('newyork12')
        G = blend(t, R12, R24, *C)
        B.font(key, True, (G, strike, metrics)); B.font(key, False, (G, strike, metrics))
        print('blended less:', ''.join(FELL) or 'none')

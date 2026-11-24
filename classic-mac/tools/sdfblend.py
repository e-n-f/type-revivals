"""New York 12 and 24 blended in raster space: New York 24 warped onto New York 12, and their distance fields averaged.

    python3 tools/sdfblend.py [t ...]          # t = 0.5 by default

For each glyph:
  1. both fonts' unthinned outlines (LIGHTEN 0) are rasterized at 1000 em units to the em;
  2. New York 24's glyph is fitted onto New York 12's by their ink boxes, then registered to it by a smooth,
     dense displacement field: optical flow (Farneback) between the two glyphs' centerlines (centerlines/, from
     tools/centerline.py), drawn as soft lines of one weight, which the flow follows where the two glyphs' ink,
     thick against thin, misleads it; smoothed, and trusted only near the lines. It moves strokes onto New York
     12's without fattening them: New York 24's stay as thick as they are (a thin serif, centred on 12's thicker
     one, rides a little above the baseline);
  3. New York 24's signed distance field (distance to the ink's edge, positive inside) is warped onto New York
     12's positions with it;
  4. New York 24's field is kept within GROW outside and THIN inside New York 12's (where the warp goes wrong it
     can't put ink in a counter, nor lose an accent), and the two fields are averaged, t of the way to New York 24's, less the thinning (t of the way from New York
     12 HD's to 24 HD's), and the result traced at its edge.
Where the two designs agree in structure, strokes take in-between thickness and contrast; where they differ
(a % or an @ drawn differently), the parts cross-fade rather than break. The advances and spacing are New York
12's exactly; the shapes may move a little from 12's, towards 24's (12's square serifs, forced by its pixels).
"""
import os, sys
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
    """signed distance to the ink's edge, positive inside (em units)"""
    m = m.astype(np.uint8)
    return cv2.distanceTransform(m, cv2.DIST_L2, 5) - cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)


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


def blend_glyph(g, h, t, shrink, cl=None):
    """New York 12's glyph g and 24's h, (ink, x0, y1, adv): the blended ink on a canvas round g, (f, x0, y1),
    f the field to trace (0 to 1, its edge at 0.5)"""
    m12, x12, y12, _ = g; m24, x24, y24, _ = h
    a0, b0, a1, b1 = box(m12, x12, y12); c0, d0, c1, d1 = box(m24, x24, y24)
    sx, sy = (a1 - a0) / (c1 - c0), (b1 - b0) / (d1 - d0)
    # the canvas: g's box and a margin, in em units (1 px = 1 em unit), x0 left and Y1 top
    X0, Y1 = int(a0) - MARGIN, int(b1) + MARGIN
    W, H = int(a1) + MARGIN - X0, Y1 - (int(b0) - MARGIN)
    xs = np.arange(W) + X0 + 0.5; ys = Y1 - np.arange(H) - 0.5
    X, Y = np.meshgrid(xs, ys)
    # g's distance field on the canvas
    D12 = cv2.remap(sdf(m12).astype(np.float32), (X - x12).astype(np.float32), (y12 - Y).astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-FAR)
    # h fitted by the boxes: its ink on the canvas
    fx = lambda X: c0 + (X - a0) / sx; fy = lambda Y: d0 + (Y - b0) / sy      # canvas -> h's em units
    S24 = sdf(m24).astype(np.float32)
    fit = lambda Xs, Ys: cv2.remap(S24, (fx(Xs) - x24).astype(np.float32), (y24 - fy(Ys)).astype(np.float32),
                                   cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=-FAR)
    # the registration, on a coarser canvas: optical flow from g's ink (blurred) to fitted h's
    small = lambda D: cv2.GaussianBlur(cv2.resize((D > 0).astype(np.float32), (W // FLOW, H // FLOW),
                                                  interpolation=cv2.INTER_AREA), (0, 0), BLUR)
    if cl:      # the two glyphs' centerlines (centerline.py): thin lines of one weight in both, which the flow follows
        inv = lambda x, y: (a0 + (x - c0) * sx, b0 + (y - d0) * sy)        # h's em units -> the canvas
        A, Bf = lines_image(cl[0], X0, Y1, W, H), lines_image(cl[1], X0, Y1, W, H, inv)
    else:       # their ink, blurred
        A = np.clip(small(D12) * 255, 0, 255).astype(np.uint8); Bf = np.clip(small(fit(X, Y)) * 255, 0, 255).astype(np.uint8)
    flow = cv2.calcOpticalFlowFarneback(A, Bf, None, 0.5, 4, WIN, 6, 7, 1.5, cv2.OPTFLOW_FARNEBACK_GAUSSIAN)
    # smoothed, and trusted only near ink (in blank space optical flow has nothing to follow, and points anywhere):
    # each pixel's flow the average of its neighbours', weighted by the ink of either glyph about them
    w = cv2.GaussianBlur(np.maximum(A, Bf).astype(np.float32) / 255, (0, 0), BLUR) + 1e-3
    flow = (cv2.GaussianBlur(flow * w[..., None], (0, 0), SMOOTH)
            / cv2.GaussianBlur(w, (0, 0), SMOOTH)[..., None])
    flow = cv2.resize(flow, (W, H), interpolation=cv2.INTER_LINEAR) * FLOW     # canvas px, x right and y down
    D24 = fit(X + flow[..., 0], Y - flow[..., 1])
    # New York 24 kept near New York 12: no ink more than GROW outside 12's (where the warp misplaces a stroke,
    # into a counter), nor 12's thinned by more than THIN a side (where 24's part is elsewhere: an accent)
    D24 = np.clip(D24, D12 - THIN, D12 + GROW)
    D = (1 - t) * D12 + t * D24 - shrink
    return np.clip(0.5 + D / 2, 0, 1).astype(np.float32), X0, Y1


def blend(t, R12, R24, C12=None, C24=None):
    """{char: (contours, adv)} in New York 12's font units; C12, C24 the fonts' centerlines, to register by"""
    s = EM / (B.SIZE['newyork12'] * B.PX)
    shrink = (1 - t) * B.LIGHTEN['newyork12'] * s + t * B.LIGHTEN['newyork24'] * EM / (B.SIZE['newyork24'] * B.PX)
    G = {}
    for ch, g in R12.items():
        if ch in R24:
            cl = (C12[ch]['lines'], C24[ch]['lines']) if C12 and ch in C12 and ch in C24 else None
            f, X0, Y1 = blend_glyph(g, R24[ch], t, shrink, cl)
        else:                       # nothing to blend with: New York 12's own, thinned
            m, X0, Y1, _ = g
            f = np.clip(0.5 + (sdf(m) - shrink) / 2, 0, 1).astype(np.float32)
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

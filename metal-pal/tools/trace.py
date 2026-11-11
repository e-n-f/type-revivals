"""Ink raster (1 px = 1 font unit) -> closed outlines of lines and cubic Béziers."""
import numpy as np, cv2
from skimage import measure
import vec

SIGMA = 1.5      # smoothing of the scan's ink, font units
ERR = 2.5        # max deviation of the fitted curves, font units
MINAREA = 150    # drop specks smaller than this (units^2)

def field(ink, sigma=SIGMA):
    f = ink.astype(np.float32)
    if sigma: f = cv2.GaussianBlur(f, (0, 0), sigma)
    return f

def contours(f, level=0.5):
    """iso-contours of f in (x, y-up) unit coordinates relative to the raster's top left"""
    f = np.pad(f, 2)
    out = []
    for c in measure.find_contours(f, level):
        P = np.c_[c[:, 1] - 2, -(c[:, 0] - 2)]
        if np.allclose(P[0], P[-1]): P = P[:-1]
        if len(P) < 8: continue
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        if abs(area) < MINAREA: continue
        out.append((P, area))
    return out

def orient(cs):
    """TrueType direction: outer contours clockwise, holes counter-clockwise (y up).
    find_contours puts ink on a consistent side, so the sign of the area tells holes from outers."""
    res = []
    for P, area in cs:
        # ink (high values) lies to the right walking a contour from skimage in (row,col);
        # after the y flip, outer contours come out with negative area = clockwise already
        res.append(P)
    return res

SMOOTH = 6      # half-width (in 2-unit steps) of the smoothing between corners

def smooth_between_corners(P, w=SMOOTH):
    """moving average along the contour that never crosses a corner (after mkfont.process
    in highway-61-revisited): rounds off the scan's ragged edges, keeps serif corners sharp"""
    n = len(P); cs = vec.corners(P)
    if not cs:
        Q = P.copy()
        for k in range(1, w + 1): Q = Q + np.roll(P, k, 0) + np.roll(P, -k, 0)
        return Q / (2 * w + 1)
    Q = P.copy()
    for j, a in enumerate(cs):
        b = cs[(j + 1) % len(cs)]
        if b <= a: b += n
        idx = np.arange(a, b + 1) % n; seg = P[idx]
        for t in range(1, len(seg) - 1):
            k = min(w, t, len(seg) - 1 - t)
            Q[idx[t]] = seg[t - k:t + k + 1].mean(0)
    return Q

def simplify(P):
    P = vec.resample(P, 2.0)
    P = smooth_between_corners(P)
    vec.MINRUN = 70; vec.LTOL = 0.7
    return vec.contour_segments(P, ERR)

def _split(c, t):
    """de Casteljau: one cubic -> two at t"""
    p0, p1, p2, p3 = [np.asarray(p, float) for p in c]
    a = p0 + (p1 - p0) * t; b = p1 + (p2 - p1) * t; cc = p2 + (p3 - p2) * t
    d = a + (b - a) * t; e = b + (cc - b) * t; m = d + (e - d) * t
    return (p0, a, d, m), (m, e, cc, p3)

def _extrema(c):
    """parameters in (0, 1) where x or y has a turning point"""
    p0, p1, p2, p3 = [np.asarray(p, float) for p in c]
    ts = []
    for k in (0, 1):
        a = -p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]; b = 2 * (p0[k] - 2 * p1[k] + p2[k]); cc = p1[k] - p0[k]
        if abs(a) < 1e-9:
            if abs(b) > 1e-9: ts.append(-cc / b)
        else:
            disc = b * b - 4 * a * cc
            if disc >= 0:
                r = np.sqrt(disc); ts += [(-b + r) / (2 * a), (-b - r) / (2 * a)]
    return sorted(t for t in ts if 0.03 < t < 0.97)

def at_extrema(segs):
    """split every curve at its horizontal and vertical extremes (points on the extremes)"""
    out = []
    for s in segs:
        if s[0] != 'C': out.append(s); continue
        c = s[1:]; ts = _extrema(c); done = 0.0
        for t in ts:
            u = (t - done) / (1 - done)
            if not 0.03 < u < 0.97: continue
            a, c = _split(c, u); out.append(('C',) + a); done = t
        out.append(('C',) + tuple(c))
    return out

def trace(ink, sigma=SIGMA):
    f = field(ink, sigma)
    return [at_extrema(simplify(P)) for P in orient(contours(f))]

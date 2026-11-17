"""Glyph images in font units: each character averaged over its occurrences on the scans (shared by the revivals)."""
import numpy as np, cv2


class Img:
    """ink in font units: column 0 at x = x0, row 0 at y = top (y up)"""
    def __init__(self, ink, x0, top):
        self.ink = np.asarray(ink, np.float32); self.x0 = float(x0); self.top = float(top)

    def bbox(self, thr=0.5):
        m = self.ink > thr
        ys = np.nonzero(m.any(1))[0]; xs = np.nonzero(m.any(0))[0]
        return self.x0 + xs[0], self.top - ys[-1] - 1, self.x0 + xs[-1] + 1, self.top - ys[0]

    def shift(self, dx, dy):
        return Img(self.ink, self.x0 + dx, self.top + dy)

    def union(self, o):
        x0 = min(self.x0, o.x0); top = max(self.top, o.top)
        x1 = max(self.x0 + self.ink.shape[1], o.x0 + o.ink.shape[1])
        bot = min(self.top - self.ink.shape[0], o.top - o.ink.shape[0])
        W = int(np.ceil(x1 - x0)) + 1; H = int(np.ceil(top - bot)) + 1
        out = np.zeros((H, W), np.float32)
        for im in (self, o):
            M = np.float32([[1, 0, im.x0 - x0], [0, 1, top - im.top]])
            out = np.maximum(out, cv2.warpAffine(im.ink, M, (W, H), flags=cv2.INTER_LINEAR))
        return Img(out, x0, top)

    def parts(self, thr=0.5):
        """its connected pieces, largest first"""
        m = (self.ink > thr).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        order = sorted(range(1, n), key=lambda i: -st[i][4])
        out = []
        for i in order:
            mk = cv2.dilate((lab == i).astype(np.uint8), np.ones((9, 9), np.uint8))
            out.append(Img(np.where(mk > 0, self.ink, 0), self.x0, self.top))
        return out

    def rot180(self):
        H, W = self.ink.shape
        b = self.bbox(); cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        return Img(self.ink[::-1, ::-1].copy(), 2 * cx - (self.x0 + W), 2 * cy - (self.top - H))

    def cx(self):
        b = self.bbox(); return (b[0] + b[2]) / 2


def place(o, k):
    """one occurrence scaled to font units; x = 0 at its measured ink edge, y = 0 on the line's baseline"""
    up = np.clip(cv2.resize(o['ink'], None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC), 0, 1)
    return Img(up, (o['X0'] - o['x0']) * k, (o['base'] - o['Y0']) * k)


def average(occs, k):
    """occurrences of one character, scaled, aligned to their mean by phase correlation, and averaged"""
    return average_imgs([place(o, k) for o in occs])


def average_imgs(ims):
    """images in font units aligned to their mean by phase correlation and averaged; the mean of the shifts
    is kept at zero, so a measured edge and baseline stay put"""
    if len(ims) == 1: return ims[0]
    x0 = min(i.x0 for i in ims); top = max(i.top for i in ims)
    x1 = max(i.x0 + i.ink.shape[1] for i in ims); bot = min(i.top - i.ink.shape[0] for i in ims)
    pad = 20; W = int(x1 - x0) + 2 * pad; H = int(top - bot) + 2 * pad
    def put(i, dx=0.0, dy=0.0):
        M = np.float32([[1, 0, i.x0 - x0 + pad + dx], [0, 1, top - i.top + pad + dy]])
        return cv2.warpAffine(i.ink, M, (W, H), flags=cv2.INTER_LINEAR)
    stack = [put(i) for i in ims]; shifts = [(0.0, 0.0)] * len(ims)
    win = cv2.createHanningWindow((W, H), cv2.CV_32F)
    def fit(a, b): return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))
    for _ in range(2):
        mean = np.mean(stack, 0)
        new = []
        for i, (sx, sy) in zip(ims, shifts):
            here = put(i, sx, sy)
            (dx, dy), _ = cv2.phaseCorrelate(here, mean, win)
            # only small corrections: the prints are placed by their cells and baselines already, within a few
            # pixels, and a tall bowl matches itself a bowl's height away (Directory's o came out three o's)
            if abs(dx) > 0.06 * W or abs(dy) > 0.06 * H: dx = dy = 0
            # a shift only if it fits the mean better: with prints from several pages, the mean can have a
            # second, fainter copy, and phase correlation can jump to it (Directory's o, a bowl's height off)
            if (dx or dy) and fit(put(i, sx + dx, sy + dy), mean) <= fit(here, mean): dx = dy = 0
            new.append((sx + dx, sy + dy))
        shifts = new
        stack = [put(i, sx, sy) for i, (sx, sy) in zip(ims, shifts)]
    # keep the mean of the shifts at zero, so the measured edge and baseline stay put
    mx = np.mean([s[0] for s in shifts]); my = np.mean([s[1] for s in shifts])
    stack = [put(i, sx - mx, sy - my) for i, (sx, sy) in zip(ims, shifts)]
    return Img(np.mean(stack, 0), x0 - pad, top + pad)

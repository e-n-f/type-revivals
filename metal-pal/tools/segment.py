"""Find glyph groups (connected components merged by horizontal overlap) in a band of a scan."""
import sys, numpy as np, cv2
from PIL import Image, ImageDraw

def load(path):
    g = np.asarray(Image.open(path).convert('L'), dtype=np.float32) / 255.0
    return g

def components(g, box, thresh=0.5, minarea=40):
    x0, y0, x1, y1 = box
    sub = g[y0:y1, x0:x1]
    b = (sub < thresh).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(b, 8)
    comps = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < minarea: continue
        comps.append(dict(id=i, x=x + x0, y=y + y0, w=w, h=h, a=a, cy=cen[i][1] + y0))
    return comps, lab, (x0, y0)

def group(comps, slant=0.0, base=0.0, frac=0.5):
    """union-find on overlap of (slanted) x-ranges"""
    def xr(c):
        # slanted x range using bbox corners: shift by (base - y)*slant
        xs = [c['x'] + (base - yy) * slant for yy in (c['y'], c['y'] + c['h'])]
        lo = min(xs); hi = max(xs) + c['w']
        if slant:  # use centre-shift only, keep width
            m = c['x'] + c['w'] / 2 + (base - (c['y'] + c['h'] / 2)) * slant
            return m - c['w'] / 2, m + c['w'] / 2
        return c['x'], c['x'] + c['w']
    par = list(range(len(comps)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    R = [xr(c) for c in comps]
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            a, b = R[i], R[j]
            ov = min(a[1], b[1]) - max(a[0], b[0])
            if ov > frac * min(a[1] - a[0], b[1] - b[0]):
                par[f(i)] = f(j)
    gs = {}
    for i in range(len(comps)): gs.setdefault(f(i), []).append(comps[i])
    out = sorted(gs.values(), key=lambda G: min(R[comps.index(c)][0] for c in G))
    return out

def bbox(G):
    x0 = min(c['x'] for c in G); y0 = min(c['y'] for c in G)
    x1 = max(c['x'] + c['w'] for c in G); y1 = max(c['y'] + c['h'] for c in G)
    return x0, y0, x1, y1

def debug(path, box, out, slant=0.0, frac=0.5):
    g = load(path)
    comps, lab, _ = components(g, box)
    base = box[3]
    gs = group(comps, slant, base, frac)
    im = Image.fromarray((g[box[1]:box[3], box[0]:box[2]] * 255).astype(np.uint8)).convert('RGB')
    d = ImageDraw.Draw(im)
    for k, G in enumerate(gs):
        x0, y0, x1, y1 = bbox(G)
        d.rectangle((x0 - box[0], y0 - box[1], x1 - box[0], y1 - box[1]), outline=(255, 0, 0), width=4)
        d.text((x0 - box[0] + 3, y0 - box[1] - 0), str(k), fill=(0, 0, 255), font_size=60)
    sc = 2000 / im.width
    im.resize((2000, int(im.height * sc))).save(out)
    print(len(gs), 'groups')

if __name__ == '__main__':
    p = sys.argv[1]; box = tuple(map(int, sys.argv[2].split(','))); slant = float(sys.argv[4]) if len(sys.argv) > 4 else 0
    debug(p, box, sys.argv[3], slant)

def sheet(path, region, bands, out, slant=0.0, frac=0.5):
    """bands: list of (ytop, ybottom) ranges; a component belongs to the band holding its bbox centre."""
    g = load(path)
    comps, _, _ = components(g, region)
    lines = []
    for (a, b) in bands:
        cs = [c for c in comps if a <= c['y'] + c['h'] / 2 < b]
        lines.append(group(cs, slant, b, frac))
    return g, lines

def contact(g, lines, out, cell=260):
    ims = []
    for li, gs in enumerate(lines):
        for k, G in enumerate(gs):
            x0, y0, x1, y1 = bbox(G)
            crop = Image.fromarray((g[y0:y1, x0:x1] * 255).astype(np.uint8))
            s = min((cell - 40) / max(crop.width, 1), (cell - 40) / max(crop.height, 1))
            crop = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))))
            c = Image.new('L', (cell, cell), 255); c.paste(crop, (20, 30))
            ImageDraw.Draw(c).text((2, 0), f'{li}.{k} {x1-x0}x{y1-y0}', fill=0, font_size=22)
            ims.append(c)
    cols = 10; rows = (len(ims) + cols - 1) // cols
    S = Image.new('L', (cols * cell, rows * cell), 200)
    for i, c in enumerate(ims): S.paste(c, ((i % cols) * cell, (i // cols) * cell))
    S.save(out)

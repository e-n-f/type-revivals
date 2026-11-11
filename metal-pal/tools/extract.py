"""Cut every glyph out of the specimen scans into an ink raster in font units.

    python3 tools/extract.py            # writes build/raster-<Style>.pkl
    python3 tools/extract.py contact    # numbered contact sheets of the groups, build/contact-*.png
"""
import sys, os, pickle, itertools, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from segment import load, components, group, bbox, contact
from sheets import SHEETS

ROOT = os.path.join(os.path.dirname(__file__), '..')
CAP = 692.0          # cap height in font units (as digital Palatino)
BUILD = os.path.join(ROOT, 'build')

def ransac_line(xs, ys, tol=6):
    """the line through the most points within tol; refitted to its inliers"""
    xs = np.asarray(xs, float); ys = np.asarray(ys, float); best = None
    for i, j in itertools.combinations(range(len(xs)), 2):
        if abs(xs[j] - xs[i]) < 200: continue
        b = (ys[j] - ys[i]) / (xs[j] - xs[i]); a = ys[i] - b * xs[i]
        inl = np.abs(ys - (a + b * xs)) < tol
        if best is None or inl.sum() > best.sum(): best = inl
    if best is None or best.sum() < 2:
        return np.median(ys), 0.0, np.ones(len(xs), bool)
    b, a = np.polyfit(xs[best], ys[best], 1)
    return a, b, best

def analyse(style):
    S = SHEETS[style]
    g = load(os.path.join(ROOT, 'scans', S['scan']))
    boxes = []
    for box in S['boxes']:
        comps, lab, (x0, y0) = components(g, box)
        gs = group(comps)
        for G in gs:
            for c in G:
                if c['y'] <= box[1] or c['y'] + c['h'] >= box[3]:
                    print(f'warning: {style} box {box} component touches the box edge at x={c["x"]}')
        bx = [bbox(G) for G in gs]
        a, b, inl = ransac_line([(q[0] + q[2]) / 2 for q in bx], [q[3] for q in bx])
        boxes.append(dict(box=box, lab=lab, off=(x0, y0), groups=gs, bboxes=bx, base=(a, b)))
    return g, boxes

def glyph_mask(boxes, refs):
    """(x0,y0,mask) for the union of the referenced groups' components"""
    parts = []
    for r in refs:
        bi, gi = map(int, r.split('.'))
        B = boxes[bi]; G = B['groups'][gi]
        parts.append((B, G))
    x0 = min(bbox(G)[0] for _, G in parts); y0 = min(bbox(G)[1] for _, G in parts)
    x1 = max(bbox(G)[2] for _, G in parts); y1 = max(bbox(G)[3] for _, G in parts)
    P = 12
    x0 -= P; y0 -= P; x1 += P; y1 += P
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    for B, G in parts:
        ox, oy = B['off']
        for c in G:
            sub = (B['lab'] == c['id'])
            ys, xs = np.nonzero(sub)
            m[ys + oy - y0, xs + ox - x0] = 1
    return x0, y0, m, int(refs[0].split('.')[0])

def raster(g, boxes, refs, scale):
    x0, y0, m, bi = glyph_mask(boxes, refs)
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    ink = 1.0 - g[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
    ink = np.where(m > 0, ink, 0.0)
    a, b = boxes[bi]['base']
    xc = x0 + m.shape[1] / 2
    base = a + b * xc
    # rotate the scan's baseline slope out (small) by shearing rows
    big = cv2.resize(ink.astype(np.float32), None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    big = np.clip(big, 0, 1)
    return dict(ink=big.astype(np.float16), x=x0 * scale, top=(base - y0) * scale, box=bi,
                px=(x0, y0, m.shape[1], m.shape[0]))

def measure(boxes, refs, base_box=None):
    """height above the baseline (px) of the top of the referenced groups"""
    x0, y0, m, bi = glyph_mask(boxes, refs)
    a, b = boxes[bi]['base']
    ys, xs = np.nonzero(m)
    xc = x0 + m.shape[1] / 2
    return (a + b * xc) - (ys.min() + y0)

def run(style):
    S = SHEETS[style]; G = S['glyphs']
    g, boxes = analyse(style)
    flat = [c for c in 'HIEFLTZ' if c in G]
    caph = np.median([measure(boxes, G[c]) for c in flat])
    scale = CAP / caph
    xh = np.median([measure(boxes, G[c]) for c in 'xvwz'])
    # the accent line is a smaller size: scale it to the same x-height
    xh_acc = np.median([measure(boxes, G['acc.' + c]) for c in ('ae', 'oe')])
    xh_main = np.median([measure(boxes, G[c]) for c in 'aeo'])
    acc_scale = scale * xh_main / xh_acc
    lf_h = np.median([measure(boxes, G[f + '.lf']) for f in ('one', 'two', 'four', 'seven')])
    lf_scale = CAP / lf_h
    print(f'{style}: cap {caph:.1f}px  x-height {xh:.1f}px = {xh*scale:.0f} units  scale {scale:.4f}'
          f'  accents x{acc_scale/scale:.3f}  lining figures x{lf_scale/scale:.3f}')
    out = {}
    for name, refs in G.items():
        bi = int(refs[0].split('.')[0])
        sc = acc_scale if name.startswith('acc.') else lf_scale if name.endswith('.lf') else scale
        out[name] = raster(g, boxes, refs, sc)
        out[name]['scale'] = sc
    meta = dict(scale=scale, xheight=xh * scale, acc_scale=acc_scale, lf_scale=lf_scale)
    os.makedirs(BUILD, exist_ok=True)
    pickle.dump(dict(glyphs=out, meta=meta), open(os.path.join(BUILD, f'raster-{style}.pkl'), 'wb'))

if __name__ == '__main__':
    styles = [a for a in sys.argv[1:] if a in SHEETS] or list(SHEETS)
    for st in styles:
        if 'contact' in sys.argv:
            g, boxes = analyse(st)
            contact(g, [B['groups'] for B in boxes], os.path.join(BUILD, f'contact-{st}.png'), cell=170)
        else:
            run(st)

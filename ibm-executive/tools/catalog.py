"""IBM's "Type Available" catalogue (form 1268416, January 1972): each face's characters in a grid, with
each character's width in units printed as a superscript beside it.

Every face's first page starts with the alphabet: line 01 holds A–T over a–t, line 02 U–Z over u–z in its
first six cells.  This reads those 52 cells of each face: the glyph (for the letters the other sources lack:
w and W) and the width digit (to check the fitted tables against IBM's own).

    python3 tools/catalog.py      # build/occ-Catalog<Face>.pkl, build/catalog-units.json, build/catalog-<Face>.png

The scans are 1-bit, about 600 dpi.  The grid's rules are found by morphological opening; a line is 417 px
high, a cell 205 px wide.
"""
import sys, os, json, pickle, numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import read as R

PAGES = {'Modern': 399, 'Documentary': 424, 'MidCentury': 459, 'Arcadia': 533, 'Doric': 538,
         'BoldFace1': 351, 'BoldFace2': 466, 'Charter': 464}
UPPER = ['ABCDEFGHIJKLMNOPQRST', 'UVWXYZ']
LOWER = ['abcdefghijklmnopqrst', 'uvwxyz']
# Arcadia's widths as printed (read from the scan), to make the digit templates
KNOWN = {'Arcadia': dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                             map(int, '33443344223354434333435333' '33333233223243333232334333')))}

def page(face):
    return np.asarray(Image.open(os.path.join(R.SCANS, f'catalog-1972-{PAGES[face]}.png')).convert('L')) < 128

def grid(ink):
    """the y of the rules between lines, and the x of the rules between cells"""
    H, W = ink.shape
    im = cv2.dilate(ink.astype(np.uint8), np.ones((3, 3), np.uint8))
    hp = cv2.morphologyEx(im, cv2.MORPH_OPEN, np.ones((1, 150), np.uint8)).sum(1)
    vp = cv2.morphologyEx(im, cv2.MORPH_OPEN, np.ones((150, 1), np.uint8)).sum(0)
    def peaks(p, thr):
        out = []
        for x in np.flatnonzero(p > thr):
            if out and x - out[-1][-1] <= 6: out[-1].append(x)
            else: out.append([x])
        return [int(np.mean(g)) for g in out]
    rows, cols = peaks(hp, 0.4 * W), peaks(vp, 0.4 * H)
    # double rules (the frame, the middle): keep the inner one of each pair
    cols = [c for i, c in enumerate(cols) if not (i + 1 < len(cols) and cols[i + 1] - c < 30 and i == 0)]
    cells = []
    for a, b in zip(cols, cols[1:]):
        if b - a > 150: cells.append((a, b))
    lines = [(a, b) for a, b in zip(rows, rows[1:]) if b - a > 300]
    return lines, cells

def half(ink, line, cell, lower):
    """one half of a cell: (digit ink, glyph ink, glyph box in page pixels)"""
    (t, b), (l, r) = line, cell
    y0, y1 = (t + 195, t + 355) if lower else (t + 15, t + 195)
    digit = ink[y0:y0 + 60, l + 8:l + 60]
    x0 = l + 62
    region = ink[y0:y1, x0:r - 4].astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(region, 8)
    H = y1 - y0
    # not a sliver of a cell's rule (as tall as the region), nor the tick that ends a row (a short dash)
    cand = [i for i in range(1, n) if st[i][4] >= 12 and st[i][3] < 0.9 * H
            and not (st[i][3] < 10 and st[i][2] > 12 and st[i][1] > 0.5 * H)]
    if not cand: return digit, None, None
    big = max(cand, key=lambda i: st[i][4])
    bx, by, bw, bh = st[big][:4]
    # the glyph: the largest piece and the pieces near it (an i's dot, a j's), not specks of the paper
    keep = [i for i in cand if i == big or (st[i][4] >= 40 and st[i][0] < bx + bw + 15 and st[i][0] + st[i][2] > bx - 15
                                            and st[i][1] < by + bh + 40 and st[i][1] + st[i][3] > by - 60)]
    m = np.isin(lab, keep)
    return digit, m, (x0, y0)

def digit_feature(d):
    """the digit's ink, cropped to its box and scaled to 24 x 32"""
    ys, xs = np.nonzero(d)
    if len(xs) < 10: return None
    c = d[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    return cv2.resize(c, (24, 32), interpolation=cv2.INTER_AREA).ravel()

def identify(face, row, lower):
    """which letter each glyph of a row is: compared with the face's font (the brochure's letters), each
    normalized to its box, and assigned one to one.  (IBM's grid doesn't always keep alphabetical order:
    Documentary has T before S.)"""
    from fontTools.ttLib import TTFont
    from PIL import ImageFont
    from scipy.optimize import linear_sum_assignment
    font = ImageFont.truetype(os.path.join(R.ROOT, 'fonts', 'otf', f'Exec{face}-Regular.otf'), 200)
    def norm(a):
        ys, xs = np.nonzero(a > 0.5)
        c = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
        return cv2.resize(c, (32, 40), interpolation=cv2.INTER_AREA).ravel()
    def render(ch):
        im = Image.new('L', (400, 400), 0); ImageDraw.Draw(im).text((100, 50), ch, font=font, fill=255)
        return np.asarray(im) / 255.0
    letters = [o['ch'] for o in row]
    refs = [norm(render(c)) for c in letters]
    cost = np.array([[np.sum((norm(o['ink']) - r) ** 2) for r in refs] for o in row])
    ri, ci = linear_sum_assignment(cost)
    return {i: letters[j] for i, j in zip(ri, ci)}

def read_face(face, templates=None):
    ink = page(face)
    lines, cells = grid(ink)
    occ, digits = [], {}
    for li, (up, low) in enumerate(zip(UPPER, LOWER)):
        for lower, chars in ((False, up), (True, low)):
            row = []
            for k, ch in enumerate(chars):
                d, m, (x0, y0) = half(ink, lines[li], cells[k], lower)
                digits[('cell', li, lower, k)] = digit_feature(d)
                if m is None: continue
                ys, xs = np.nonzero(m)
                X0, Y0 = x0 + xs.min() - 4, y0 + ys.min() - 4
                g = m[ys.min() - 4 + 4 if False else 0:, :]
                crop = np.pad(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 4).astype(np.float32)
                row.append(dict(ch=ch, word=(li, int(lower)), idx=k, ink=crop, X0=X0, Y0=Y0,
                                x0=X0 + 4, x1=X0 + 4 + xs.max() - xs.min() + 1, top=Y0 + 4,
                                bottom=Y0 + 4 + ys.max() - ys.min() + 1, w=int(xs.max() - xs.min() + 1),
                                line=li * 2 + int(lower), scan=f'catalog-1972-{PAGES[face]}.png', off=(0, 0),
                                touching=False, _cell=('cell', li, lower, k)))
            ids = identify(face, row, lower)
            moved = {o['ch']: ids[i] for i, o in enumerate(row) if ids[i] != o['ch']}
            if moved: print(f'  {face}: cells in another order: {moved}')
            for i, o in enumerate(row):
                if ids[i] != o['ch']:
                    o['ch'] = ids[i]; digits[('_', ids[i])] = digits.pop(o['_cell'])
            # the row's baseline: the feet of its letters that sit on it
            feet = [o['bottom'] for o in row if o['ch'] in R.BASE]
            base = float(np.median(feet))
            for o in row: o['base'] = base
            occ += row
    # the digits by the letter now in each cell
    digits = {k[1] if k[0] == '_' else next((o['ch'] for o in occ if o['_cell'] == k), None): f for k, f in digits.items()}
    digits.pop(None, None)
    units = {}
    if templates:
        for ch, f in digits.items():
            if f is None: continue
            units[ch] = min(templates, key=lambda u: min(float(np.sum((f - t) ** 2)) for t in templates[u]))
    return occ, digits, units

def contact(face, occ, units, out):
    cell = 110; cols = 26
    sheet = Image.new('L', (cols * cell, 2 * cell * 2), 255); d = ImageDraw.Draw(sheet)
    for i, o in enumerate(occ):
        im = Image.fromarray(((1 - o['ink']) * 255).astype(np.uint8)); im.thumbnail((cell - 10, cell - 26))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 5, y + 24)); d.text((x + 3, y + 1), f"{o['ch']} {units.get(o['ch'], '?')}", fill=0, font_size=18)
    sheet.save(out)

if __name__ == '__main__':
    os.makedirs(R.BUILD, exist_ok=True)
    _, dig, _ = read_face('Arcadia')
    templates = {}
    for ch, u in KNOWN['Arcadia'].items():
        if dig.get(ch) is not None: templates.setdefault(u, []).append(dig[ch])
    # a second set of templates: every digit whose first reading agrees with the face's fitted table
    first = {}
    for face in PAGES:
        occ, dig, units = read_face(face, templates)
        fit = json.load(open(os.path.join(R.BUILD, f'units-{face}.json')))['units']
        for ch, u in units.items():
            if fit.get(ch) == u and dig.get(ch) is not None: first.setdefault(u, []).append(dig[ch])
    templates = first
    allunits = {}
    for face in [a for a in sys.argv[1:] if a in PAGES] or PAGES:
        occ, _, units = read_face(face, templates)
        allunits[face] = units
        pickle.dump([(f'catalogue {face}', occ)], open(os.path.join(R.BUILD, f'occ-Catalog{face}.pkl'), 'wb'))
        contact(face, occ, units, os.path.join(R.BUILD, f'catalog-{face}.png'))
        print(face, len(occ), 'letters;', ''.join(str(units.get(c, '?')) for c in ''.join(UPPER)), ''.join(str(units.get(c, '?')) for c in ''.join(LOWER)))
    p = os.path.join(R.BUILD, 'catalog-units.json')
    old = json.load(open(p)) if os.path.exists(p) else {}
    json.dump({**old, **allunits}, open(p, 'w'), indent=1)

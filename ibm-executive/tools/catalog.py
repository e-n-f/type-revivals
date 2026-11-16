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

# Widths read by eye from the catalogue's other lines (the punctuation's places vary from face to face).
# Arcadia, page 533: where it lists a character twice, the plain form (its ¢ is 3 units, the barred one 4).
READ_BY_EYE = {'Arcadia': {'!': 3, ':': 2, ';': 2, '"': 3, '?': 4, '/': 3, '£': 3, '§': 3, '+': 3, '*': 3, '@': 4,
                           '$': 3, '¢': 3, '=': 3, '#': 3, '%': 4, '(': 2, ')': 2, '&': 4, '-': 3, "'": 2, '_': 3}}

# all of each face's pages in the catalogue
ALL_PAGES = {'BoldFace1': [351, 352, 370, 371, 372, 373], 'Modern': [399, 400, 401, 402, 421, 422, 423],
             'Documentary': [424, 425, 426, 427], 'MidCentury': [459, 460, 461, 462], 'Charter': [464, 465],
             'BoldFace2': [466, 480, 501], 'Arcadia': [533, 534], 'Doric': [538, 539]}

def page(face, number=None):
    n = number or PAGES[face]
    return np.asarray(Image.open(os.path.join(R.SCANS, f'catalog-1972-{n}.png')).convert('L')) < 128

def all_cells(face):
    """every half-cell of every page of a face: its glyph (as an occurrence), width digit, and place"""
    out = []
    for pg in ALL_PAGES[face]:
        ink = page(face, pg); lines, cells = grid(ink)
        for li, line in enumerate(lines):
            for lower in (False, True):
                row = []
                for k, cell in enumerate(cells):
                    d, m, at = half(ink, line, cell, lower)
                    if m is None: continue
                    x0, y0 = at
                    ys, xs = np.nonzero(m)
                    X0, Y0 = x0 + xs.min() - 4, y0 + ys.min() - 4
                    crop = np.pad(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 4).astype(np.float32)
                    row.append(dict(ch=None, cell=(pg, li + 1, k + 1, 'lower' if lower else 'upper'),
                                    digit=digit_feature(d), ink=crop, X0=X0, Y0=Y0, x0=X0 + 4,
                                    x1=X0 + 4 + xs.max() - xs.min() + 1, top=Y0 + 4,
                                    bottom=Y0 + 4 + ys.max() - ys.min() + 1, w=int(xs.max() - xs.min() + 1),
                                    word=(pg, li, int(lower)), idx=k, line=(pg, li, int(lower)),
                                    scan=f'catalog-1972-{pg}.png', off=(0, 0), touching=False))
                if not row: continue
                # the half-row's baseline: the commonest foot among its taller glyphs
                hs = np.array([o['bottom'] - o['top'] for o in row]); tall = [o for o, h in zip(row, hs) if h >= 0.6 * hs.max()]
                base = float(np.median([o['bottom'] for o in tall]))
                for o in row: o['base'] = base
                out += row
    return out

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

# ------------------------------------------------------------------------------------------ the other cells
# Each cell's glyph is compared with references: the face's own font where it has the character, else
# another face's or a generic one; by its shape (normalized to its box) and by its size and place against
# the baseline (in cap heights), so that , and ' or - and _ are told apart.  Decoys (fractions, accented
# letters, signs) keep the many cells that are none of the wanted characters from being forced onto them.
# The candidates are then looked at (catalog-<Face>-candidates.png) and chosen in CHOSEN.
ASCII = ''.join(chr(c) for c in range(33, 127))
DECOYS = '½¼¾⅓⅔⅛⅜⅝⅞°±¶†‡¿¡µπ®©¢£§¨´`àáâäåçèéêëìíîïñòóôöùúûüÀÁÂÄÅÇÈÉÊËÑÖÜßøØæÆœŒ'
FALLBACK = ['Charter', 'Modern', None]          # None: DejaVu Serif
GENERIC = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'

def shape(a):
    ys, xs = np.nonzero(a > 0.5)
    c = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    return cv2.resize(c, (24, 32), interpolation=cv2.INTER_AREA).ravel()

def references(face):
    from fontTools.ttLib import TTFont
    from PIL import ImageFont
    refs = {}
    fonts = []
    for f in [face] + [f for f in FALLBACK if f != face]:
        path = os.path.join(R.ROOT, 'fonts', 'otf', f'Exec{f}-Regular.otf') if f else GENERIC
        tt = TTFont(path)
        cap = getattr(tt['OS/2'], 'sCapHeight', 0) or 0.73 * tt['head'].unitsPerEm
        fonts.append((f, path, set(tt.getBestCmap()), cap, tt['head'].unitsPerEm, ImageFont.truetype(path, 400)))
    for ch in ASCII + DECOYS:
        for f, path, cmap, cap, upm, font in fonts:
            if ord(ch) not in cmap: continue
            size = 400
            im = Image.new('L', (900, 900), 0); ImageDraw.Draw(im).text((300, 600), ch, font=font, fill=255, anchor='ls')
            a = np.asarray(im) / 255.0
            if not (a > 0.5).any(): break
            ys, xs = np.nonzero(a > 0.5); px = cap * size / upm
            geo = np.array([(xs.max() - xs.min() + 1) / px, (ys.max() - ys.min() + 1) / px,
                            (600 - ys.max() - 1) / px, (600 - ys.min()) / px])
            refs[ch] = (shape(a), geo, f or 'generic')
            break
    return refs

def classify(face, cells, refs, cap):
    for o in cells:
        a = o['ink']; geo = np.array([o['w'] / cap, (o['bottom'] - o['top']) / cap, (o['base'] - o['bottom']) / cap,
                                      (o['base'] - o['top']) / cap])
        sh = shape(a)
        d = {ch: float(np.mean((sh - r[0]) ** 2)) + 2.0 * float(np.sum((geo - r[1]) ** 2)) for ch, r in refs.items()}
        o['scores'] = sorted(d.items(), key=lambda kv: kv[1])[:3]
        o['ch'] = o['scores'][0][0]
    return cells

def cap_height(face):
    occ, _, _ = read_face(face)
    return float(np.median([o['bottom'] - o['top'] for o in occ if o['ch'] in 'EFHILT']))

def candidates(face, cells, want, out, n=4):
    """for each wanted character, the n cells that match it best"""
    rows = []
    for ch in want:
        best = sorted((o for o in cells if any(c == ch for c, _ in o['scores'])),
                      key=lambda o: dict(o['scores'])[ch])[:n]
        rows.append((ch, best))
    cell = 120
    sheet = Image.new('L', (cell * (n + 1), cell * len(rows)), 255); d = ImageDraw.Draw(sheet)
    for r, (ch, best) in enumerate(rows):
        d.text((10, r * cell + 30), repr(ch), fill=0, font_size=40)
        for i, o in enumerate(best):
            im = Image.fromarray(((1 - o['ink']) * 255).astype(np.uint8)); im.thumbnail((cell - 10, cell - 36))
            x, y = (i + 1) * cell, r * cell
            sheet.paste(im, (x + 5, y + 30)); pg, li, k, hf = o['cell']
            d.text((x + 2, y + 2), f"{pg}/{li}/{k}{hf[0]} {o.get('units', '?')}", fill=0, font_size=16)
    sheet.save(out)


# Cells chosen by eye from the candidates (catalog-<Face>-candidates.png, made by `catalog.py survey`): the
# characters each font lacks, as (page, line, cell, half).  Their width is the cell's.  Characters with no clear
# cell are left out: \ and | in every face, { } and ~ but in Mid-Century, < > but in Arcadia and Charter.
U, L = 'upper', 'lower'
CHOSEN = {
    'Modern': {'=': (399, 4, 17, U), '^': (399, 4, 12, U)},
    'Documentary': {'!': (425, 1, 8, U), '#': (425, 3, 6, U), "'": (424, 11, 19, L), '*': (424, 6, 15, L),
                    ':': (426, 6, 3, U), ';': (426, 7, 4, U), '=': (426, 6, 12, U), '[': (424, 12, 9, U),
                    ']': (426, 3, 7, L), '_': (426, 5, 20, L)},
    'MidCentury': {'!': (459, 4, 1, U), "'": (459, 11, 20, L), '@': (459, 12, 9, U), '[': (461, 3, 8, U),
                   ']': (461, 3, 8, L), '{': (461, 3, 12, U), '}': (461, 3, 12, L), '^': (461, 10, 13, U),
                   '~': (460, 3, 8, U), '#': (459, 10, 1, U)},
    'Arcadia': {'<': (534, 3, 15, U), '>': (534, 3, 15, L), '[': (534, 3, 10, U), ']': (534, 3, 11, U),
                '^': (533, 9, 3, U)},
    'Doric': {'!': (538, 10, 2, U), '"': (538, 5, 4, U), "'": (538, 6, 19, L), '*': (538, 6, 8, U),
              ':': (539, 2, 7, U), ';': (538, 4, 8, U), '[': (539, 2, 1, U), ']': (539, 2, 1, L), '^': (539, 6, 7, U)},
    'BoldFace1': {'"': (371, 5, 18, U), '#': (370, 13, 12, U), '$': (351, 12, 8, U), "'": (371, 6, 18, U),
                  '*': (351, 9, 16, U), ':': (352, 2, 18, L), ';': (371, 4, 17, L), '@': (371, 1, 3, U),
                  '^': (351, 6, 1, U)},
    'BoldFace2': {'!': (466, 9, 14, U), '"': (466, 6, 11, L), "'": (466, 4, 13, U), '*': (480, 3, 12, U),
                  ':': (480, 4, 13, U), ';': (466, 3, 11, L), '[': (466, 5, 13, U), ']': (466, 10, 13, U),
                  '^': (480, 11, 13, U)},
    'Charter': {'"': (464, 4, 6, U), '^': (464, 4, 16, U), '_': (464, 11, 20, L)},
}
# The widths of characters the fonts have, where the catalogue's cells agree (read from the same sheets).
# The period and comma are 3 units where the fits gave 2: a period is nearly always followed by a space, so the
# pairs only ever saw one side of it.
WIDTHS = {
    'Modern': {'!': 3, ',': 3, '.': 3, '/': 3, '?': 4},
    'Documentary': {',': 3, '.': 3, '/': 3, '&': 4, '?': 4},
    'MidCentury': {',': 3, '/': 3, '?': 4},
    'Arcadia': {},
    'Doric': {',': 3, '/': 3},
    'BoldFace1': {'!': 3, ',': 3, '.': 3, '/': 3, '?': 4},
    'BoldFace2': {'%': 4, '&': 4, '(': 2, ')': 2, ',': 3, '-': 3, '.': 3, '?': 4},
    'Charter': {'!': 3, '%': 4, '/': 3, '?': 3, '<': 3, '>': 3, '[': 2, ']': 2},
}

def chosen_cells(face, templates):
    """the chosen cells as occurrences of their characters, with their widths"""
    want = CHOSEN.get(face, {})
    if not want: return [], {}
    by = {o['cell']: o for o in all_cells(face)}
    occ, units = [], {}
    for ch, cell in want.items():
        o = dict(by[cell], ch=ch); occ.append(o)
        units[ch] = read_digit(o['digit'], templates)
    return occ, units

def digit_templates():
    """the width digits 2-5: first from Arcadia's cells as read by eye (KNOWN), then every digit whose first
    reading agrees with the face's fitted table"""
    _, dig, _ = read_face('Arcadia')
    templates = {}
    for ch, u in KNOWN['Arcadia'].items():
        if dig.get(ch) is not None: templates.setdefault(u, []).append(dig[ch])
    first = {}
    for face in PAGES:
        occ, dig, units = read_face(face, templates)
        fit = json.load(open(os.path.join(R.BUILD, f'units-{face}.json')))['units']
        for ch, u in units.items():
            if fit.get(ch) == u and dig.get(ch) is not None: first.setdefault(u, []).append(dig[ch])
    return first

def read_digit(f, templates):
    if f is None: return None
    return min(templates, key=lambda u: min(float(np.sum((f - t) ** 2)) for t in templates[u]))

def survey(face, templates):
    """all of a face's cells, classified, with their widths; and the candidates for its punctuation"""
    cells = all_cells(face)
    classify(face, cells, references(face), cap_height(face))
    for o in cells: o['units'] = read_digit(o['digit'], templates)
    pickle.dump(cells, open(os.path.join(R.BUILD, f'cells-{face}.pkl'), 'wb'))
    want = [c for c in ASCII if not c.isalnum()]
    candidates(face, cells, want, os.path.join(R.BUILD, f'catalog-{face}-candidates.png'))
    return cells

if __name__ == '__main__':
    os.makedirs(R.BUILD, exist_ok=True)
    templates = digit_templates()
    if 'survey' in sys.argv:
        for face in [a for a in sys.argv[1:] if a in PAGES] or PAGES: survey(face, templates)
        sys.exit()
    allunits = {}
    for face in [a for a in sys.argv[1:] if a in PAGES] or PAGES:
        occ, _, units = read_face(face, templates)
        extra, xunits = chosen_cells(face, templates)
        print(f'  {face}: from other cells', xunits)
        allunits[face] = {**units, **xunits, **READ_BY_EYE.get(face, {}), **WIDTHS.get(face, {})}
        pickle.dump([(f'catalogue {face}', occ + extra)], open(os.path.join(R.BUILD, f'occ-Catalog{face}.pkl'), 'wb'))
        contact(face, occ, units, os.path.join(R.BUILD, f'catalog-{face}.png'))
        print(face, len(occ), 'letters;', ''.join(str(units.get(c, '?')) for c in ''.join(UPPER)), ''.join(str(units.get(c, '?')) for c in ''.join(LOWER)))
    p = os.path.join(R.BUILD, 'catalog-units.json')
    old = json.load(open(p)) if os.path.exists(p) else {}
    json.dump({**old, **allunits}, open(p, 'w'), indent=1)


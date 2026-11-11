"""Compare the text sizes (5-12 p) and display sizes (12-48 p) on the size cards with the fonts.

The fonts are traced from each card's type list, which matches the 28 p display line.  For every
line set in another size, each letter is matched to its glyph (as in spacing.py) and compared at
equal x-height:

  width   median letter width against the font's
  stem    median stem thickness of n m u against the font's
  x/cap   x-height over cap height (text blocks: from the capitals line)
  x/body  x-height in proportion to the point size, against the median of the 14-48 p lines
  gap     mean change of the gaps between letters within words, units

    python3 tools/textsizes.py      # prints a table per style
"""
import sys, os, pickle, itertools, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from segment import load, components, group, bbox
from sheets import DISPLAY
from spacing import tokenizations, inkbox, NAMES
import spacing

ROOT = os.path.join(os.path.dirname(__file__), '..')
spacing.NAMES = dict(NAMES, **{',': 'comma', '.': 'period', '-': 'hyphen'})
XL = set('acemnorsuvwxz')
FLATCAPS = set('EFHIKLMNTUXZ')
DISPLAY_SIZES = {'Regular': [12, 14, 16, 20, 24, 28, 36, 48], 'Italic': [14, 16, 20, 24, 28, 36, 48],
                 'Bold': [14, 16, 20, 24, 28, 36, 48]}
# text blocks in the left column (x 500-3700): (size, [(band, text)])
TEXT = {
 'Regular': [
  (5, [((770, 865), 'Von den vielen Welten, die der Mensch nicht von der Natur ge-'),
       ((895, 990), 'schenkt bekam, sondern sich aus dem eigenen Geist erschaffen hat,'),
       ((1015, 1115), 'ist die Welt der Bücher die größte. Jedes Kind, wenn es die ersten'),
       ((1140, 1215), 'Buchstaben auf seine Schultafel malt und die ersten Leseversuche'),
       ((1280, 1370), 'MACHT, TUT DAMIT DEN ERSTEN SCHRITT IN EINE')]),
  (6, [((1735, 1830), 'Von den vielen Welten, die der Mensch nicht von der Natur'),
       ((1880, 1980), 'geschenkt bekam, sondern sich aus dem eigenen Geist er-'),
       ((2020, 2120), 'schaffen hat, ist die Welt der Bücher die größte. Jedes Kind,'),
       ((2160, 2245), 'wenn es die ersten Buchstaben auf seine Schultafel malt und'),
       ((2315, 2410), 'DIE ERSTEN LESEVERSUCHE MACHT, TUT DAMIT')]),
  (8, [((2780, 2905), 'Von den vielen Welten, die der Mensch nicht von'),
       ((2960, 3095), 'der Natur geschenkt bekam, sondern sich aus'),
       ((3135, 3270), 'dem eigenen Geist erschaffen hat, ist die Welt der'),
       ((3315, 3450), 'Bücher die größte. Jedes Kind, wenn es die ersten'),
       ((3510, 3615), 'BUCHSTABEN AUF SEINE SCHULTAFEL')]),
  (9, [((4080, 4220), 'Von den vielen Welten, die der Mensch nicht'),
       ((4275, 4425), 'von der Natur geschenkt bekam, sondern sich'),
       ((4470, 4635), 'aus dem eigenen Geist erschaffen hat, ist die'),
       ((4665, 4815), 'Welt der Bücher die größte. Jedes Kind, wenn'),
       ((4880, 4995), 'ES DIE ERSTEN BUCHSTABEN AUF')]),
  (10, [((5390, 5540), 'Von den vielen Welten, die der Mensch'),
        ((5600, 5765), 'nicht von der Natur geschenkt bekam,'),
        ((5815, 5975), 'sondern sich aus dem eigenen Geist er-'),
        ((6025, 6170), 'schaffen hat, ist die Welt der Bücher die'),
        ((6245, 6410), 'GRÖSSTE. JEDES KIND, WENN ES')])],
 'Italic': [
  (5, [((585, 680), 'Von den vielen Welten, die der Mensch nicht von der Natur geschenkt bekam,'),
       ((695, 790), 'sondern sich aus dem eigenen Geist erschaffen hat, ist die Welt der Bücher'),
       ((800, 900), 'die größte. Jedes Kind, wenn es die ersten Buchstaben auf seine Schultafel'),
       ((930, 1010), 'MALT UND DIE ERSTEN LESEVERSUCHE MACHT, TUT DAMIT DEN')]),
  (6, [((1410, 1515), 'Von den vielen Welten, die der Mensch nicht von der Natur geschenkt'),
       ((1535, 1645), 'bekam, sondern sich aus dem eigenen Geist erschaffen hat, ist die Welt'),
       ((1665, 1770), 'der Bücher die größte. Jedes Kind, wenn es die ersten Buchstaben auf seine'),
       ((1815, 1900), 'SCHULTAFEL MALT UND DIE ERSTEN LESEVERSUCHE MA')]),
  (8, [((2290, 2410), 'Von den vielen Welten, die der Mensch nicht von der Natur'),
       ((2450, 2590), 'geschenkt bekam, sondern sich aus dem eigenen Geist erschaffen'),
       ((2615, 2745), 'hat, ist die Welt der Bücher die größte. Jedes Kind, wenn es'),
       ((2790, 2900), 'DIE ERSTEN BUCHSTABEN AUF SEINE SCHU')]),
  (9, [((3445, 3580), 'Von den vielen Welten, die der Mensch nicht von der'),
       ((3625, 3775), 'Natur geschenkt bekam, sondern sich aus dem eigenen'),
       ((3805, 3950), 'Geist erschaffen hat, ist die Welt der Bücher die größte.'),
       ((4000, 4145), 'JEDES KIND, WENN ES DIE ERSTEN BUCH')]),
  (10, [((4535, 4685), 'Von den vielen Welten, die der Mensch nicht von'),
        ((4730, 4900), 'der Natur geschenkt bekam, sondern sich aus dem'),
        ((4930, 5100), 'eigenen Geist erschaffen hat, ist die Welt der Bü-'),
        ((5140, 5300), 'CHER DIE GRÖSSTE. JEDES KIND, WE')]),
  (12, [((5690, 5870), 'Von den vielen Welten, die der Mensch nicht'),
        ((5925, 6120), 'von der Natur geschenkt bekam, sondern'),
        ((6180, 6335), 'SICH AUS DEM EIGENEN GEIST')])],
 'Bold': [
  (6, [((565, 660), 'Von den vielen Welten, die der Mensch nicht von der Natur'),
       ((690, 795), 'geschenkt bekam, sondern aus dem eigenen Geist erschaffen'),
       ((815, 920), 'hat, ist die Welt der Bücher die größte. Jedes Kind, wenn es'),
       ((940, 1025), 'die ersten Buchstaben auf seine Schultafel malt und seine'),
       ((1080, 1175), 'ERSTEN LESEVERSUCHE MACHT, TUT DAMIT DE')]),
  (8, [((1565, 1685), 'Von den vielen Welten, die der Mensch nicht von'),
       ((1725, 1860), 'der Natur geschenkt bekam, sondern aus dem'),
       ((1885, 2020), 'eigenen Geist erschaffen hat, ist die Welt der Bü-'),
       ((2045, 2180), 'cher die größte. Jedes Kind, wenn es die ersten'),
       ((2225, 2330), 'BUCHSTABEN AUF SEINE SCHULTAFEL')]),
  (9, [((2865, 3005), 'Von den vielen Welten, die der Mensch nicht'),
       ((3045, 3210), 'von der Natur geschenkt bekam, sondern aus'),
       ((3220, 3385), 'dem eigenen Geist erschaffen hat, ist die Welt'),
       ((3400, 3565), 'der Bücher die größte. Jedes Kind, wenn es'),
       ((3595, 3715), 'DIE ERSTEN BUCHSTABEN AUF SE')]),
  (10, [((4125, 4275), 'Von den vielen Welten, die der Mensch'),
        ((4320, 4490), 'nicht von der Natur geschenkt bekam,'),
        ((4515, 4685), 'sondern aus dem eigenen Geist erschaffen'),
        ((4710, 4880), 'hat, ist die Welt der Bücher die größte.'),
        ((4930, 5080), 'JEDES KIND, WENN ES DIE ERS')]),
  (12, [((5460, 5635), 'Von den zahlreichen Welten, welche'),
        ((5690, 5890), 'der Mensch nicht von der Natur ge-'),
        ((5920, 6095), 'schenkt bekam, sondern aus dem'),
        ((6175, 6325), 'EIGENEN GEIST ERSCHAFFE')])],
}

def stroke(m):
    d = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
    ridge = (d >= cv2.dilate(d, np.ones((3, 3)))) & (d > 1)
    return 2 * np.median(d[ridge]) if ridge.any() else np.nan

def read_line(g, x0, x1, band, text, R, width):
    """match the line's groups to glyphs; None if the counts can't be made to agree"""
    a, b = band
    comps, lab, (ox, oy) = components(g, (x0, a - 25, x1, b + 25), minarea=12)
    comps = [c for c in comps if a - 5 <= c['y'] + c['h'] / 2 < b + 5]
    G = group(comps); gs = [bbox(q) for q in G]
    best = None
    words = text.split()
    for combo in itertools.product(*[list(tokenizations(w, R)) for w in words]):
        toks = [t for w in combo for t in w]
        if len(toks) != len(gs): continue
        ratio = np.array([width[t] / max(q[2] - q[0], 1) for t, q in zip(toks, gs)])
        e = np.std(np.log(ratio))
        if best is None or e < best[0]: best = (e, combo)
    if best is None or best[0] > 0.25: return None
    return best[1], G, gs, lab, (ox, oy)

def glyph_mask(Gc, q, lab, off):
    ox, oy = off
    m = np.zeros((q[3] - q[1], q[2] - q[0]), bool)
    for c in Gc:
        sub = lab[c['y'] - oy:c['y'] - oy + c['h'], c['x'] - ox:c['x'] - ox + c['w']] == c['id']
        m[c['y'] - q[1]:c['y'] - q[1] + c['h'], c['x'] - q[0]:c['x'] - q[0] + c['w']] |= sub
    return m

def measure(style):
    data = pickle.load(open(os.path.join(ROOT, 'build', f'raster-{style}.pkl'), 'rb'))
    R = data['glyphs']; XH = data['meta']['xheight']; CAP = 692.0
    sb = __import__('json').load(open(os.path.join(ROOT, 'build', f'spacing-{style}.json')))['sb']
    width = {n: inkbox(r)[1] - inkbox(r)[0] for n, r in R.items()}
    st_ref = np.median([stroke(R[c]['ink'].astype(np.float32) > 0.5) for c in 'nmu'])
    scan, dlines = DISPLAY[style]
    g = load(os.path.join(ROOT, 'scans', scan))
    blocks = [(s, [(band, t)], 3900, 7900) for s, (band, t) in zip(DISPLAY_SIZES[style], dlines)]
    blocks += [(s, lines, 500, 3700) for s, lines in TEXT[style]]
    rows = []
    for size, lines, x0, x1 in blocks:
        xh, cap, wr, sw, gaps, nread = [], [], [], [], [], 0
        for band, text in lines:
            r = read_line(g, x0, x1, band, text, R, width)
            if r is None: continue
            nread += 1
            combo, G, gs, lab, off = r
            toks = [t for w in combo for t in w]
            hs = [q[3] - q[1] for t, q in zip(toks, gs) if t in XL]
            ch = [q[3] - q[1] for t, q in zip(toks, gs) if t in FLATCAPS]
            if hs: xh.append((np.median(hs), len(hs)))
            if ch: cap.append((np.median(ch), len(ch)))
            sc = XH / np.median(hs) if hs else None          # units per px at equal x-height
            if sc is None: continue
            wr += [(q[2] - q[0]) * sc / width[t] for t, q in zip(toks, gs) if len(t) == 1 and t.islower()]
            sw += [stroke(glyph_mask(Gc, q, lab, off)) * sc / st_ref
                   for t, q, Gc in zip(toks, gs, G) if t in 'nmu']
            i = 0
            for w in combo:
                for a_, b_ in zip(w, w[1:]):
                    if a_ in sb and b_ in sb and a_.islower() and b_.islower():
                        gaps.append((gs[i + 1][0] - gs[i][2]) * sc - (sb[a_][1] + sb[b_][0]))
                    i += 1
                i += 1
        xh_px = np.average([v for v, _ in xh], weights=[n for _, n in xh]) if xh else np.nan
        cap_px = np.average([v for v, _ in cap], weights=[n for _, n in cap]) if cap else np.nan
        rows.append(dict(size=size, lines=f'{nread}/{len(lines)}', xh=xh_px, xcap=xh_px / cap_px,
                         width=np.median(wr) if wr else np.nan, stem=np.nanmedian(sw) if sw else np.nan,
                         nstem=len(sw), gap=np.mean(gaps) if gaps else np.nan, ngap=len(gaps)))
    ref_body = np.median([r['xh'] / r['size'] for r in rows if r['size'] >= 14])
    print(f'\n{style}: font (type list) x-height/cap height {XH / CAP:.3f}')
    print('  size  lines   x-ht px  x/cap   x/body  width  stem (n)    gap units (pairs)')
    for r in sorted(rows, key=lambda r: r['size']):
        body = (r['xh'] / r['size']) / ref_body
        print(f"  {r['size']:3d} p  {r['lines']:>5}  {r['xh']:6.1f}  {r['xcap']:6.3f}  {body:6.3f}  {r['width']:5.3f}"
              f"  {r['stem']:4.2f} ({r['nstem']:2d})  {r['gap']:+6.1f} ({r['ngap']})")

if __name__ == '__main__':
    for st in [a for a in sys.argv[1:] if a in TEXT] or list(TEXT):
        measure(st)

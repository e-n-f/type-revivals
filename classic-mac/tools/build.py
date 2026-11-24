"""Build the classic Mac recreations: each character traced from an upscaled sheet of the bitmap font, on the
bitmap's own metrics.

    python3 tools/build.py [athens]

For each font, scans/<font>-upscaled.png is the bitmap font's glyph sheet upscaled to 36 times its pixels, and
scans/<font>-glyphs.json says where each character is on it: the cell it occupies, its origin (pen position on the
baseline) and the bitmap's advance width, in the coordinates of the sheet at 6 times (so the upscaled sheet's are
6 times those). Each character's ink is cut from its cell, traced at its 50 % contour, and placed by its origin.
One bitmap pixel is 50 font units, so every advance, the ascender and the descender are exactly the bitmap's, and
the em is the bitmap's point size in pixels (900 units for Athens 18).
The bitmap font itself (scans/<Font>_<size>.dfont, tools/bitmap.py) gives the space and the vertical metrics.
"""
import os, sys, json
import numpy as np, cv2
from PIL import Image
from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.reverseContourPen import ReverseContourPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, '..', 'common'))
import trace
from fontio import draw, autohint
import bitmap

Image.MAX_IMAGE_PIXELS = None

PX = 50                                   # font units per bitmap pixel
VERSIONS = {'athens': '1.002', 'chicago': '1.002', 'geneva': '1.001', 'newyork12': '1.002', 'newyork24': '1.001',
            'monaco': '1.003', 'newyork12mid': '1.002', 'newyork24mid': '1.002'}
# New York 12 Blend HD (tools/sdfblend.py: New York 24 warped onto New York 12, their distance fields averaged)
BLEND_VERSION = '1.006'
# fonts traced from another's sources (sheet, glyph positions and bitmap) at another weight
SOURCE = {'newyork12mid': 'newyork12', 'newyork24mid': 'newyork24'}
MID = {f: ' Its strokes are at the weight halfway between those of New York 12 HD and 24 HD.' for f in SOURCE}
# the size the Mac's menus gave the bitmap font, in points: its em, at 72 dpi, in pixels (the strike's 22 px are
# its ascender and descender), so that set at 18 pt Athens HD matches Athens 18
SIZE = {'athens': 18, 'chicago': 12, 'geneva': 12, 'newyork12': 12, 'newyork24': 24, 'monaco': 12,
        'newyork12mid': 12, 'newyork24mid': 24}
NAMES = {'athens': 'Athens HD', 'chicago': 'Chicago HD', 'geneva': 'Geneva HD', 'newyork12': 'New York 12 HD',
         'newyork24': 'New York 24 HD', 'monaco': 'Monaco HD', 'newyork12mid': 'New York 12 Mid HD',
         'newyork24mid': 'New York 24 Mid HD'}
ORIGINAL = {'athens': ('Athens', 'Susan Kare', 1984), 'chicago': ('Chicago', 'Susan Kare', 1984),
            'geneva': ('Geneva', 'Susan Kare', 1984), 'newyork12': ('New York', 'Susan Kare', 1984),
            'newyork24': ('New York', 'Susan Kare', 1984), 'monaco': ('Monaco', 'Susan Kare', 1984)}
ORIGINAL.update({f: ORIGINAL[s] for f, s in SOURCE.items()})
# Characters the sheet names by their Mac control codes, at their Unicode places: Chicago's command key, check
# mark, diamond and Apple logo (the logo where Apple's own fonts put it, in the Private Use Area). The OS X
# .dfont keeps them at Mac OS Roman 0xD9-0xDC instead, in the places of Ÿ ⁄ ¤ ‹.
CODES = {'chicago': {'<11>': 0x2318, '<12>': 0x2713, '<13>': 0x25C6, '<14>': 0xF8FF}}
MOVED = {'chicago': 'Ÿ⁄¤‹'}
# further code points for a character: Ω is both the Greek letter and the ohm sign (Mac OS Roman 0xBD is either)
ALSO = {'Ω': [0x2126]}
SIGMA = 1.5                               # smoothing of the traced ink, in font units
# Font units taken off each side of every stroke. Traced at their 50 % contour, the stems come out the bitmap's
# exact width (2 px), but antialiased outlines (and macOS's font smoothing) read darker than crisp pixels:
# both are thinned to about 1.8 px
LIGHTEN = {'athens': 4, 'chicago': 4, 'geneva': 4, 'newyork12': 4, 'newyork24': 4, 'monaco': 4,
# New York 12's and 24's bitmaps differ in weight: traced at their 50 % contour, unthinned, their strokes average
# 0.0735 em and 0.0546 em, and thinned by 4 units a side as the others are, as New York 12 HD and 24 HD, 0.0601
# and 0.0479. The Mid fonts are both at about the weight halfway between those two, 0.054 em: 12's thinned by 6
# units a side (of its em of 600), to 0.0537 em, 24's by 1 (of 1200), to 0.0529. A negative LIGHTEN thickens
           'newyork12mid': 6, 'newyork24mid': 1}
# Accented letters whose accent the upscaling got wrong: Geneva 12's acute, grave and dieresis are two or three
# pixels, and on the sheet á à é came out as circumflexes, ä and ï as broken marks. Each takes the accent of a
# letter the sheet gets right whose bitmap accent has the same pixels (reaccent())
REACCENT = {'geneva': 'áàäéï', 'monaco': 'à'}           # Monaco's à came out a circumflex
# Monospaced fonts: every advance, in bitmap pixels. Monaco 12's © and ® advance only 6 in the bitmap (the left of
# each circle is cut off); here they advance 7 like the rest, their ink where the bitmap has it, and the font is
# marked fixed-pitch
MONO = {'monaco': 7}
# Characters the AI upscaling got wrong but bitmap-upscaling's 6-times sheet (scans/<font>-6x.png) has right,
# traced from that instead: New York 24's comma came out a dagger, its ™ a TH, and À's grave a dot
SIX = {'newyork24': ',™À'}
# Characters whose one-pixel dots (the dieresis) the upscaling drew faint or lost: each dot is a round dot a pixel
# across (less LIGHTEN a side), at its pixel in the bitmap
DOTS = {'newyork24': 'ÄÖÜäëïöüÿ¨'}


def gname(ch):
    return UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def glyphs(font):
    """{char: (contours in font units, advance)} traced from the upscaled sheet"""
    src = SOURCE.get(font, font)
    info = json.load(open(os.path.join(ROOT, 'scans', f'{src}-glyphs.json')))
    def load(name):
        sheet = np.asarray(Image.open(os.path.join(ROOT, 'scans', name)).convert('L'), np.float32) / 255
        k = sheet.shape[1] / info['image_size'][0]           # sheet pixels per layout pixel
        return sheet, k, float(np.median(sheet)), float(np.percentile(sheet, 0.5))
    sheets = {'up': load(f'{src}-upscaled.png')}
    if src in SIX: sheets['6x'] = load(f'{src}-6x.png')
    out = {}
    # each glyph's room across: two bitmap pixels past its ink box, but not past halfway to its neighbours' on the
    # same line. Glyphs that touch on the sheet (New York's w x y, its — and “) are one piece of ink, divided
    # there; a glyph pasted in from another source, reaching a little past its box, keeps what it reaches
    ink_box = lambda g: (min(g['ink_best'][0], g['ink_avg'][0]), max(g['ink_best'][2], g['ink_avg'][2]))
    room = {}
    by_line = {}
    for g in info['glyphs']: by_line.setdefault(g['line'], []).append(g)
    for gs in by_line.values():
        gs = sorted(gs, key=lambda g: ink_box(g)[0])
        for i, g in enumerate(gs):
            a, b = ink_box(g); p = 2 * info['scale'][0]
            lo, hi = a - p, b + p
            if i > 0: lo = max(lo, (ink_box(gs[i - 1])[1] + a) / 2)
            if i < len(gs) - 1: hi = min(hi, (b + ink_box(gs[i + 1])[0]) / 2)
            room[g['char']] = (lo, hi)
    for g in info['glyphs']:
        sheet, k, paper, dark = sheets['6x' if g['char'] in SIX.get(src, '') else 'up']
        f = PX / (info['scale'][0] * k)                      # font units per sheet pixel
        pad = int(round(2 * info['scale'][0] * k))         # two bitmap pixels
        # the cell and two pixels round it: a glyph pasted in from another source can reach a little past its
        # cell. Its pieces of ink are those mostly inside the cell (a neighbour's can reach into it too)
        cx0, cy0, cx1, cy1 = (int(round(v * k)) for v in g['cell'])
        x0, y0 = max(0, cx0 - pad), max(0, cy0 - pad)
        x1, y1 = min(sheet.shape[1], cx1 + pad), min(sheet.shape[0], cy1 + pad)
        crop = np.clip((paper - sheet[y0:y1, x0:x1]) / max(paper - dark, 0.2), 0, 1)
        lo, hi = (v * k for v in room[g['char']])
        cols = np.arange(x0, x1)
        crop[:, (cols < lo) | (cols >= hi)] = 0
        n, lab, st, _ = cv2.connectedComponentsWithStats((crop > 0.25).astype(np.uint8), 8)
        inside = np.bincount(lab[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0].ravel(), minlength=n)
        own = [i for i in range(1, n) if inside[i] > 0.5 * st[i][4]]
        crop = np.where(np.isin(lab, own), crop, 0).astype(np.float32)
        ink = cv2.resize(crop, (int(round(crop.shape[1] * f)), int(round(crop.shape[0] * f))),
                         interpolation=cv2.INTER_LINEAR)
        r = LIGHTEN.get(font, 0)
        if r:
            disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * abs(r) + 1,) * 2)
            if r > 0:
                # thinning widens any dent in the ink by the disc's radius each side, into a notch: first fill
                # dents narrower than the disc (a closing), then thin
                ink = cv2.erode(cv2.erode(cv2.dilate(ink, disc), disc), disc)
            else: ink = cv2.dilate(ink, disc)
        ox, oy = g['origin'][0] * k, g['origin'][1] * k
        dx, dy = (x0 - ox) * f, (oy - y0) * f                # the crop's top left corner, from the origin
        contours = [[(s[0],) + tuple((p[0] + dx, p[1] + dy) for p in s[1:]) for s in c]
                    for c in trace.trace(ink, SIGMA)]
        out[g['char']] = (contours, g['source']['advance'] * PX)
    return out


def reaccent(font, G, strike):
    """the letters of REACCENT with the accent of another letter: one with the same accent (by its Unicode
    decomposition) whose bitmap accent has the same pixels, and that isn't itself in REACCENT. A letter keeps its own
    base; the accent, its outlines above the x-height, is moved to where the letter's bitmap has its accent"""
    import unicodedata
    gx = strike['x']                                       # the x-height, in pixels: the top of x's ink (Monaco's
    xh = gx['y'] - next(y for y, row in enumerate(gx['bits']) if row.any())   # boxes are all the strike's height)
    def accent(c):                                         # the bitmap's accent pixels, as (x, y up) from the origin
        g = strike[c]
        return {(g['x'] + x, g['y'] - y) for y, row in enumerate(g['bits']) for x, v in enumerate(row)
                if v and g['y'] - y > xh}
    mark = lambda c: unicodedata.decomposition(c).split()[-1:]
    norm = lambda a: frozenset((x - min(p[0] for p in a), y - min(p[1] for p in a)) for x, y in a)
    above = lambda c: max(p[1] for s in c for p in s[1:]) > xh * PX and min(p[1] for s in c for p in s[1:]) >= xh * PX - 10
    notes = []
    for t in REACCENT.get(font, ''):
        at = accent(t)
        donors = [d for d in G if len(d) == 1 and d != t and d not in REACCENT[font] and d in strike
                  and mark(d) == mark(t) and d.islower() == t.islower() and accent(d) and norm(accent(d)) == norm(at)]
        if not donors: raise SystemExit(f'{font}: no letter with the accent of {t!r}')
        d = donors[0]; ad = accent(d)
        dx = (min(p[0] for p in at) - min(p[0] for p in ad)) * PX
        dy = (min(p[1] for p in at) - min(p[1] for p in ad)) * PX
        base = [c for c in G[t][0] if not above(c)]
        mark_ = [[(s[0],) + tuple((p[0] + dx, p[1] + dy) for p in s[1:]) for s in c] for c in G[d][0] if above(c)]
        G[t] = (base + mark_, G[t][1])
        notes.append(f'{t} from {d}')
    return notes


def redot(font, G, strike):
    """the one-pixel dots of DOTS's characters' bitmaps, each a round dot a pixel across (less LIGHTEN a side) at
    its pixel, in place of what the sheet traced there"""
    src = SOURCE.get(font, font)
    if src not in DOTS: return
    gx = strike['x']
    xh = gx['y'] - next(y for y, row in enumerate(gx['bits']) if row.any())
    area = lambda c: sum(a[0] * b[1] - b[0] * a[1] for a, b in zip([s[1] for s in c], [s[-1] for s in c])) / 2
    sign = 1 if area(max(G['.'][0], key=lambda c: abs(area(c)))) > 0 else -1   # the trace's outer direction
    r = PX / 2 - LIGHTEN.get(font, 0); K = 0.5523 * r
    for ch in DOTS[src]:
        g = strike[ch]; bits = np.pad(g['bits'], 1)
        dots = [((g['x'] + x + 0.5) * PX, (g['y'] - y - 0.5) * PX) for y, row in enumerate(g['bits'])
                for x, v in enumerate(row) if v and g['y'] - y > xh and bits[y:y + 3, x:x + 3].sum() == 1]
        near = lambda c: any(abs(np.mean([p[0] for s in c for p in s[1:]]) - x) < 1.5 * PX and
                             abs(np.mean([p[1] for s in c for p in s[1:]]) - y) < 1.5 * PX for x, y in dots)
        above = lambda c: min(p[1] for s in c for p in s[1:]) >= xh * PX - 10
        keep = [c for c in G[ch][0] if not (above(c) and near(c))]
        for x, y in dots:
            P = [(x + r, y), (x, y + r), (x - r, y), (x, y - r)]
            H = [((0, K), (K, 0)), ((-K, 0), (0, K)), ((0, -K), (-K, 0)), ((K, 0), (0, -K))]
            c = [('C', P[i], (P[i][0] + H[i][0][0], P[i][1] + H[i][0][1]),
                  (P[(i + 1) % 4][0] + H[i][1][0], P[(i + 1) % 4][1] + H[i][1][1]), P[(i + 1) % 4]) for i in range(4)]
            if np.sign(area(c)) != sign: c = [('C', s[4], s[3], s[2], s[1]) for s in reversed(c)]
            keep.append(c)
        G[ch] = (keep, G[ch][1])


def font(fontname, otf=True, data=None):
    G, strike, metrics = data
    family = NAMES[fontname]; style = 'Regular'
    psname = family.replace(' ', '') + '-' + style
    VERSION = VERSIONS[fontname]
    glyphs_, adv, cmap = {}, {}, {}
    for ch, (contours, a) in G.items():
        cp = CODES.get(fontname, {}).get(ch, None) or ord(ch)
        n = gname(chr(cp)); glyphs_[n] = contours; adv[n] = a; cmap[cp] = n
        for more in ALSO.get(ch, []): cmap[more] = n
    glyphs_['space'] = []; adv['space'] = strike[' ']['adv'] * PX; cmap[0x20] = 'space'; cmap[0xA0] = 'space'
    w = strike.get(' ', {}).get('adv', 5) * PX
    glyphs_['.notdef'] = [[('L', (50, 0), (50, 700)), ('L', (50, 700), (w - 50, 700)), ('L', (w - 50, 700), (w - 50, 0)),
                           ('L', (w - 50, 0), (50, 0))]]
    adv['.notdef'] = w
    if fontname in MONO: adv = {n: MONO[fontname] * PX for n in adv}
    order = ['.notdef', 'space'] + sorted(n for n in glyphs_ if n not in ('.notdef', 'space'))
    UPM = SIZE[fontname] * PX
    fb = FontBuilder(UPM, isTTF=not otf)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    if otf:
        cs = {}
        for n in order:
            pen = T2CharStringPen(adv[n], None); draw(ReverseContourPen(pen), glyphs_[n]); cs[n] = pen.getCharString()
        fb.setupCFF(psname, {'FullName': family, 'FamilyName': family, 'Weight': 'Regular'}, cs, {})
    else:
        gl = {}
        for n in order:
            pen = TTGlyphPen(None); draw(pen, glyphs_[n], quad=True); gl[n] = pen.glyph()
        fb.setupGlyf(gl)
    lsb = {}; ymax = 0; ymin = 0
    for n in order:
        bp = BoundsPen(None); draw(bp, glyphs_[n], quad=not otf)
        lsb[n] = int(np.floor(bp.bounds[0])) if bp.bounds else 0
        if bp.bounds: ymin = min(ymin, bp.bounds[1]); ymax = max(ymax, bp.bounds[3])
    fb.setupHorizontalMetrics({n: (adv[n], lsb[n]) for n in order})
    # the bitmap's own ascender and descender: lines a bitmap em apart, as on the Mac
    asc, desc = metrics['ascender'] * PX, metrics['descender'] * PX
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    name, designer, year = ORIGINAL[fontname]
    fb.setupNameTable({
        'familyName': family, 'styleName': style, 'uniqueFontIdentifier': f'{psname};{VERSION}', 'fullName': family,
        'psName': psname, 'version': f'Version {VERSION}',
        'copyright': f'Traced from an upscaling of the {name} bitmap font ({designer}, {year}).',
        'description': f'A high-resolution recreation of the classic Mac bitmap font {name} '
                       f'{SIZE[fontname]}, on its metrics: set at {SIZE[fontname]} pt, its advances fall on '
                       f'the bitmap\'s pixels.' + (MID.get(fontname, '')),
    })
    bbox = lambda c: BoundsPen(None)
    def box(ch):
        bp = BoundsPen(None); draw(bp, glyphs_[gname(ch)]); return bp.bounds
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=int(np.ceil(max(ymax, asc))), usWinDescent=int(np.ceil(max(-ymin, -desc))),
                sxHeight=int(round(box('x')[3])), sCapHeight=int(round(box('H')[3])), usWeightClass=400,
                achVendID='NONE', fsType=0, fsSelection=0x40 | 0x80, version=4)
    fb.setupPost(isFixedPitch=int(fontname in MONO))
    if fontname in MONO:                  # PANOSE: Latin text, monospaced
        fb.font['OS/2'].panose.bFamilyType = 2; fb.font['OS/2'].panose.bProportion = 9
    fb.font['head'].fontRevision = float(VERSION)
    d = os.path.join(ROOT, 'fonts', 'otf' if otf else 'ttf')
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f'{psname}.{"otf" if otf else "ttf"}')
    fb.save(path)
    if not otf: autohint(path)
    print('  wrote', os.path.relpath(path, ROOT), len(order), 'glyphs')


if __name__ == '__main__':
    for f in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        G = glyphs(f)
        strike, metrics = bitmap.strike(SOURCE.get(f, f))
        notes = reaccent(SOURCE.get(f, f), G, strike)
        if notes: print(f'{f}: accents', ', '.join(notes))
        redot(f, G, strike)
        missing = sorted(c for c in strike if c not in G and c not in ' \xa0' + MOVED.get(f, '')
                         and not any(ord(c) in ALSO.get(g, []) for g in G))
        print(f'{f}: {len(G)} characters traced; in the bitmap but not on the sheet: {"".join(missing) or "none"}')
        data = (G, strike, metrics)
        font(f, True, data); font(f, False, data)

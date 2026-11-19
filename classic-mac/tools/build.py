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
VERSIONS = {'athens': '1.000', 'chicago': '1.000'}
# the size the Mac's menus gave the bitmap font, in points: its em, at 72 dpi, in pixels (the strike's 22 px are
# its ascender and descender), so that set at 18 pt Athens HD matches Athens 18
SIZE = {'athens': 18, 'chicago': 12}
NAMES = {'athens': 'Athens HD', 'chicago': 'Chicago HD'}
ORIGINAL = {'athens': ('Athens', 'Susan Kare', 1984), 'chicago': ('Chicago', 'Susan Kare', 1984)}
# Characters the sheet names by their Mac control codes, at their Unicode places: Chicago's command key, check
# mark, diamond and Apple logo (the logo where Apple's own fonts put it, in the Private Use Area). The OS X
# .dfont keeps them at Mac OS Roman 0xD9-0xDC instead, in the places of Ÿ ⁄ ¤ ‹.
CODES = {'chicago': {'<11>': 0x2318, '<12>': 0x2713, '<13>': 0x25C6, '<14>': 0xF8FF}}
MOVED = {'chicago': 'Ÿ⁄¤‹'}
# further code points for a character: Ω is both the Greek letter and the ohm sign (Mac OS Roman 0xBD is either)
ALSO = {'Ω': [0x2126]}
SIGMA = 1.5                               # smoothing of the traced ink, in font units


def gname(ch):
    return UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def glyphs(font):
    """{char: (contours in font units, advance)} traced from the upscaled sheet"""
    info = json.load(open(os.path.join(ROOT, 'scans', f'{font}-glyphs.json')))
    sheet = np.asarray(Image.open(os.path.join(ROOT, 'scans', f'{font}-upscaled.png')).convert('L'), np.float32) / 255
    k = sheet.shape[1] / info['image_size'][0]               # upscaled sheet pixels per layout pixel
    f = PX / (info['scale'][0] * k)                          # font units per upscaled sheet pixel
    paper = float(np.median(sheet)); dark = float(np.percentile(sheet, 0.5))
    out = {}
    pad = int(round(2 * info['scale'][0] * k))             # two bitmap pixels
    for g in info['glyphs']:
        # the cell and two pixels round it: a glyph pasted in from another source can reach a little past its
        # cell. Its pieces of ink are those mostly inside the cell (a neighbour's can reach into it too)
        cx0, cy0, cx1, cy1 = (int(round(v * k)) for v in g['cell'])
        x0, y0 = max(0, cx0 - pad), max(0, cy0 - pad)
        x1, y1 = min(sheet.shape[1], cx1 + pad), min(sheet.shape[0], cy1 + pad)
        crop = np.clip((paper - sheet[y0:y1, x0:x1]) / max(paper - dark, 0.2), 0, 1)
        n, lab, st, _ = cv2.connectedComponentsWithStats((crop > 0.25).astype(np.uint8), 8)
        inside = np.bincount(lab[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0].ravel(), minlength=n)
        own = [i for i in range(1, n) if inside[i] > 0.5 * st[i][4]]
        crop = np.where(np.isin(lab, own), crop, 0).astype(np.float32)
        ink = cv2.resize(crop, (int(round(crop.shape[1] * f)), int(round(crop.shape[0] * f))),
                         interpolation=cv2.INTER_LINEAR)
        ox, oy = g['origin'][0] * k, g['origin'][1] * k
        dx, dy = (x0 - ox) * f, (oy - y0) * f                # the crop's top left corner, from the origin
        contours = [[(s[0],) + tuple((p[0] + dx, p[1] + dy) for p in s[1:]) for s in c]
                    for c in trace.trace(ink, SIGMA)]
        out[g['char']] = (contours, g['source']['advance'] * PX)
    return out


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
                       f'the bitmap\'s pixels.',
    })
    bbox = lambda c: BoundsPen(None)
    def box(ch):
        bp = BoundsPen(None); draw(bp, glyphs_[gname(ch)]); return bp.bounds
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=int(np.ceil(max(ymax, asc))), usWinDescent=int(np.ceil(max(-ymin, -desc))),
                sxHeight=int(round(box('x')[3])), sCapHeight=int(round(box('H')[3])), usWeightClass=400,
                achVendID='NONE', fsType=0, fsSelection=0x40 | 0x80, version=4)
    fb.setupPost()
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
        strike, metrics = bitmap.strike(f)
        missing = sorted(c for c in strike if c not in G and c not in ' \xa0' + MOVED.get(f, '')
                         and not any(ord(c) in ALSO.get(g, []) for g in G))
        print(f'{f}: {len(G)} characters traced; in the bitmap but not on the sheet: {"".join(missing) or "none"}')
        data = (G, strike, metrics)
        font(f, True, data); font(f, False, data)

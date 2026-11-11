"""Assemble the traced glyphs into fonts.

    python3 tools/build.py [Regular|Italic|Bold ...]   ->  fonts/otf/*.otf, fonts/ttf/*.ttf
"""
import sys, os, json, pickle, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
import trace, vec
from extract import CAP
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.cu2qu import curve_to_quadratic
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ROOT = os.path.join(os.path.dirname(__file__), '..')
BUILD = os.path.join(ROOT, 'build')
VERSION = '1.000'
FAMILY = 'Metal Pal'
UPM = 1000
FIGW = 500                       # figures are on an en (Halbgeviert) body
SPACE = 250

UNI = {
    'space': 0x20, 'exclam': 0x21, 'quotedbl': 0x22, 'ampersand': 0x26, 'quotesingle': 0x27,
    'parenleft': 0x28, 'parenright': 0x29, 'asterisk': 0x2A, 'comma': 0x2C, 'hyphen': 0x2D,
    'period': 0x2E, 'slash': 0x2F, 'colon': 0x3A, 'semicolon': 0x3B, 'equal': 0x3D, 'question': 0x3F,
    'bracketleft': 0x5B, 'bracketright': 0x5D, 'section': 0xA7, 'guillemotleft': 0xAB,
    'paragraph': 0xB6, 'periodcentered': 0xB7, 'guillemotright': 0xBB, 'emdash': 0x2014,
    'endash': 0x2013, 'quoteleft': 0x2018, 'quoteright': 0x2019, 'quotesinglbase': 0x201A,
    'quotedblleft': 0x201C, 'quotedblright': 0x201D, 'quotedblbase': 0x201E, 'dagger': 0x2020,
    'dblhyphen': 0x2E40, 'dotlessi': 0x131, 'germandbls': 0xDF, 'ae': 0xE6, 'oe': 0x153,
    'AE': 0xC6, 'OE': 0x152, 'nbspace': 0xA0, 'guilsinglleft': 0x2039, 'guilsinglright': 0x203A,
}
for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ': UNI[c] = ord(c)
FIGS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
for i, f in enumerate(FIGS): UNI[f] = 0x30 + i
ACCENTED = {  # name: (base, mark name, unicode)
    'aacute': ('a', 'acute', 0xE1), 'agrave': ('a', 'grave', 0xE0), 'acircumflex': ('a', 'circumflex', 0xE2),
    'eacute': ('e', 'acute', 0xE9), 'egrave': ('e', 'grave', 0xE8), 'ecircumflex': ('e', 'circumflex', 0xEA),
    'edieresis': ('e', 'dieresis', 0xEB), 'iacute': ('dotlessi', 'acute', 0xED), 'igrave': ('dotlessi', 'grave', 0xEC),
    'icircumflex': ('dotlessi', 'circumflex', 0xEE), 'idieresis': ('dotlessi', 'dieresis', 0xEF),
    'oacute': ('o', 'acute', 0xF3), 'ograve': ('o', 'grave', 0xF2), 'ocircumflex': ('o', 'circumflex', 0xF4),
    'uacute': ('u', 'acute', 0xFA), 'ugrave': ('u', 'grave', 0xF9), 'ucircumflex': ('u', 'circumflex', 0xFB),
    'yacute': ('y', 'acute', 0xFD), 'ydieresis': ('y', 'dieresis', 0xFF), 'ccedilla': ('c', 'cedilla', 0xE7),
    'Aacute': ('A', 'acute.cap', 0xC1), 'Agrave': ('A', 'grave.cap', 0xC0), 'Acircumflex': ('A', 'circumflex.cap', 0xC2),
    'Eacute': ('E', 'acute.cap', 0xC9), 'Egrave': ('E', 'grave.cap', 0xC8), 'Ecircumflex': ('E', 'circumflex.cap', 0xCA),
    'Edieresis': ('E', 'dieresis.cap', 0xCB), 'Iacute': ('I', 'acute.cap', 0xCD), 'Igrave': ('I', 'grave.cap', 0xCC),
    'Icircumflex': ('I', 'circumflex.cap', 0xCE), 'Idieresis': ('I', 'dieresis.cap', 0xCF),
    'Oacute': ('O', 'acute.cap', 0xD3), 'Ograve': ('O', 'grave.cap', 0xD2), 'Ocircumflex': ('O', 'circumflex.cap', 0xD4),
    'Uacute': ('U', 'acute.cap', 0xDA), 'Ugrave': ('U', 'grave.cap', 0xD9), 'Ucircumflex': ('U', 'circumflex.cap', 0xDB),
    'Yacute': ('Y', 'acute.cap', 0xDD), 'Ydieresis': ('Y', 'dieresis.cap', 0x178), 'Ccedilla': ('C', 'cedilla', 0xC7),
}
NATIVE_ACC = {'adieresis': 0xE4, 'odieresis': 0xF6, 'udieresis': 0xFC,
              'Adieresis': 0xC4, 'Odieresis': 0xD6, 'Udieresis': 0xDC}
KERNED = ('f', 'j', 'f_f', 'f_i', 'f_l', 'f_t', 'germandbls')   # sorts that may overhang their body

class Img:
    """ink raster placed in glyph space: column 0 at x = x0, row 0 at y = top (y up)"""
    def __init__(self, ink, x0, top):
        self.ink = np.asarray(ink, np.float32); self.x0 = float(x0); self.top = float(top)
    @classmethod
    def of(cls, r): return cls(r['ink'], r['x'], r['top'])
    def rows_y(self): return self.top - np.arange(self.ink.shape[0])
    def cols_x(self): return self.x0 + np.arange(self.ink.shape[1])
    def bbox(self, thr=0.5):
        m = self.ink > thr
        ys = np.nonzero(m.any(1))[0]; xs = np.nonzero(m.any(0))[0]
        return self.x0 + xs[0], self.top - ys[-1], self.x0 + xs[-1] + 1, self.top - ys[0]
    def select(self, keep):
        """keep(xgrid, ygrid) -> bool array"""
        X, Y = np.meshgrid(self.cols_x(), self.rows_y())
        return Img(np.where(keep(X, Y), self.ink, 0), self.x0, self.top)
    def components(self, thr=0.35):
        m = (self.ink > thr).astype(np.uint8)
        n, lab = cv2.connectedComponents(m, connectivity=8)
        return [Img(np.where(cv2.dilate((lab == i).astype(np.uint8), np.ones((5, 5))) > 0, self.ink, 0),
                    self.x0, self.top) for i in range(1, n)]
    def shift(self, dx, dy): return Img(self.ink, self.x0 + dx, self.top + dy)
    def union(self, o):
        x0 = min(self.x0, o.x0); top = max(self.top, o.top)
        x1 = max(self.x0 + self.ink.shape[1], o.x0 + o.ink.shape[1])
        bot = min(self.top - self.ink.shape[0], o.top - o.ink.shape[0])
        W = int(np.ceil(x1 - x0)) + 1; H = int(np.ceil(top - bot)) + 1
        out = np.zeros((H, W), np.float32)
        for im in (self, o):
            # sub-pixel placement by affine warp
            M = np.float32([[1, 0, im.x0 - x0], [0, 1, top - im.top]])
            out = np.maximum(out, cv2.warpAffine(im.ink, M, (W, H), flags=cv2.INTER_LINEAR))
        return Img(out, x0, top)
    def anchor(self, lo, hi):
        """horizontal centre of the ink between heights lo and hi"""
        s = self.select(lambda X, Y: (Y >= lo) & (Y <= hi))
        w = s.ink.sum(0)
        if w.sum() == 0: b = self.bbox(); return (b[0] + b[2]) / 2
        return float((w * self.cols_x()).sum() / w.sum())
    def thin(self, d):
        """move the outline inwards by d units (signed distance field)"""
        if abs(d) < 0.3: return self
        P = 8
        m = np.pad(self.ink, P) > 0.5
        din = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5)
        dout = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 5)
        sdf = din - dout                      # >0 inside
        sdf = cv2.GaussianBlur(sdf, (0, 0), 1.0)
        ink = np.clip(0.5 + (sdf - d), 0, 1)
        return Img(ink, self.x0 - P, self.top + P)

def stroke(im):
    """typical stroke thickness: twice the median of the distance transform's ridge"""
    m = (im.ink > 0.5).astype(np.uint8)
    d = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    ridge = (d >= cv2.dilate(d, np.ones((3, 3)))) & (d > 2)
    return 2 * np.median(d[ridge])

def build(style):
    data = pickle.load(open(os.path.join(BUILD, f'raster-{style}.pkl'), 'rb'))
    R = data['glyphs']; meta = data['meta']
    sp = json.load(open(os.path.join(BUILD, f'spacing-{style}.json')))['sb']
    italic = style == 'Italic'
    XH = meta['xheight']
    G = {n: Img.of(r) for n, r in R.items()}

    # the accent line and the lining figures come from a smaller size, which is drawn
    # heavier: thin them to the stroke of the main size
    st_main = np.median([stroke(G[c]) for c in 'aeo'])
    st_small = np.median([stroke(G['acc.' + c]) for c in ('ae', 'oe')])
    thin = (st_small - st_main) / 2
    print(f'{style}: x-height {XH:.0f}, stroke {st_main:.1f}; accent line stroke {st_small:.1f} -> thinned {thin:.1f}')
    for n in list(G):
        if n.startswith('acc.') or n.endswith('.lf'): G[n] = G[n].thin(thin)

    # --- marks
    marks = {}
    def body_and_marks(im, h):
        cs = im.components()
        body = [c for c in cs if c.bbox()[1] < h * 0.6]
        mk = [c for c in cs if c.bbox()[1] >= h * 0.6]
        return body, mk
    def merge(ims):
        out = ims[0]
        for o in ims[1:]: out = out.union(o)
        return out
    for src, mname, h in [('acc.aacute', 'acute', XH), ('acc.agrave', 'grave', XH), ('acc.acircumflex', 'circumflex', XH),
                          ('acc.Eacute', 'acute.cap', CAP), ('acc.Egrave', 'grave.cap', CAP),
                          ('acc.Ecircumflex', 'circumflex.cap', CAP), ('adieresis', 'dieresis', XH),
                          ('Adieresis', 'dieresis.cap', CAP)]:
        body, mk = body_and_marks(G[src], h)
        b = merge(body); m = merge(mk)
        marks[mname] = (m, m.anchor(-1e9, 1e9) - b.anchor(0.7 * h, h))
    for src, mname, h in [('acc.ccedilla', 'cedilla', XH)]:
        im = G[src]
        m = im.select(lambda X, Y: Y < -6)
        b = im.select(lambda X, Y: Y >= 0)
        marks[mname] = (m, m.anchor(-1e9, 1e9) - b.anchor(0, 0.3 * h))

    # --- derived glyphs
    i_ = G['i']
    body = [c for c in i_.components() if c.bbox()[1] < XH * 0.5]
    G['dotlessi'] = merge(body)
    for name, (base, mk, u) in ACCENTED.items():
        if base not in G: continue
        h = CAP if base[0].isupper() else XH
        m, off = marks[mk]
        b = G[base]
        if mk == 'cedilla':
            ax = b.anchor(-1e9, 0.3 * h)
            # sit the cedilla below the base's own bottom
            m = m.shift(0, b.bbox()[1] - 0)
        else:
            ax = b.anchor(0.7 * h, h)
            if base[0].isupper() and not mk.endswith('.cap'): pass
        cx = m.anchor(-1e9, 1e9)
        dy = 0
        if base[0].isupper() and mk.endswith('.cap'):
            dy = max(0, b.bbox()[3] + 25 - m.bbox()[1])      # keep clear of a tall base
        G[name] = b.union(m.shift(ax + off - cx, dy))
    for n in ('ae', 'oe', 'AE', 'OE'):
        G[n] = G['acc.' + n]
    G['quotesingle'] = G['quoteright']; G['quotedbl'] = G['quotedblleft']
    G['quotedblright'] = G['quotedblleft']; G['quoteleft'] = G['quoteright']
    qb = G['quotedblbase'].bbox(); qr = G['quoteright'].bbox()
    G['quotesinglbase'] = G['quoteright'].shift(0, qb[1] - qr[1])
    G['equal'] = G['dblhyphen']
    # en dash: the em dash with its middle taken out
    em = G['emdash']; b = em.bbox(); L = b[2] - b[0]; cut = L * 0.5
    left = em.select(lambda X, Y: X < b[0] + (L - cut) / 2)
    right = em.select(lambda X, Y: X >= b[2] - (L - cut) / 2)
    G['endash'] = left.union(right.shift(-cut, 0))
    # single guillemets: one chevron of the double ones
    for d, s in (('guillemotleft', 'guilsinglleft'), ('guillemotright', 'guilsinglright')):
        cs = sorted(G[d].components(), key=lambda c: c.bbox()[0])
        G[s] = cs[0] if d == 'guillemotright' else cs[-1]

    # --- side bearings
    def sb(n):
        base = n.split('.')[0]
        for k in (n, base, ACCENTED.get(n, (None,))[0], 'i' if n == 'dotlessi' else None):
            if k in sp: l, r = sp[k]; break
        else:
            l = r = 0.06 * (G[n].bbox()[3] - G[n].bbox()[1]) + 15  # punctuation and the rest
            if n in ('period', 'comma', 'colon', 'semicolon', 'quoteright', 'quotesingle', 'quoteleft',
                     'quotedblleft', 'quotedblright', 'quotedblbase', 'quotesinglbase', 'quotedbl', 'exclam'):
                l = r = 0.5 * st_main
        if not italic and n not in KERNED:
            l, r = max(l, 5), max(r, 5)
        return l, r

    names = [n for n in G if not n.startswith('acc.')]
    order = ['.notdef', 'space', 'nbspace'] + sorted(names, key=lambda n: (n not in UNI, n))
    glyphs = {}; adv = {}
    for n in names:
        segs = trace.trace(G[n].ink)
        im = G[n]
        outl = [[(s[0],) + tuple((p[0] + im.x0, p[1] + im.top) for p in s[1:]) for s in c] for c in segs]
        bp = BoundsPen(None); draw(bp, outl)
        xmin, _, xmax, _ = bp.bounds
        cb = ControlBoundsPen(None); draw(cb, outl)
        if max(bp.bounds[0] - cb.bounds[0], cb.bounds[2] - bp.bounds[2]) > 40:
            print(f'  note: {n} has long curve handles')
        l, r = sb(n)
        if n.endswith('.osf') or n.endswith('.lf'):
            w = max(FIGW, xmax - xmin + 30); l = (w - (xmax - xmin)) / 2; r = w - (xmax - xmin) - l
        glyphs[n] = [[(s[0],) + tuple((p[0] - xmin + l, p[1]) for p in s[1:]) for s in c] for c in outl]
        adv[n] = int(round(xmax - xmin + l + r))
    for f in FIGS:   # default figures are the old-style ones
        glyphs[f] = glyphs[f + '.osf']; adv[f] = adv[f + '.osf']
        names.append(f); order.append(f)
    glyphs['space'] = glyphs['nbspace'] = []; adv['space'] = adv['nbspace'] = SPACE
    glyphs['.notdef'] = [[('L', (50, 0), (50, 700)), ('L', (50, 700), (450, 700)), ('L', (450, 700), (450, 0)), ('L', (450, 0), (50, 0))]]
    adv['.notdef'] = 500
    order = list(dict.fromkeys(order))
    return order, glyphs, adv, XH

def draw(pen, contours, quad=False):
    R = lambda p: (round(p[0], 1 if not quad else 0), round(p[1], 1 if not quad else 0))
    for c in contours:
        pen.moveTo(R(c[0][1]))
        for s in c:
            if s[0] == 'L': pen.lineTo(R(s[2]))
            elif quad:
                q = curve_to_quadratic([tuple(p) for p in s[1:]], 0.5)
                pen.qCurveTo(*[R(p) for p in q[1:]])
            else: pen.curveTo(*[R(p) for p in s[2:]])
        pen.closePath()

FEA = """
languagesystem DFLT dflt;
languagesystem latn dflt;
feature liga {{ {liga} }} liga;
feature dlig {{ {dlig} }} dlig;
feature lnum {{ {lnum} }} lnum;
feature onum {{ {onum} }} onum;
{extra}
"""

def font(style, otf=True):
    order, glyphs, adv, XH = build(style)
    have = set(order)
    lig = lambda parts: f'sub {" ".join(parts)} by {"_".join(parts)};'
    liga = ' '.join(lig(p) for p in (['f', 'f', 'i'], ['f', 'f'], ['f', 'i'], ['f', 'l'], ['f', 't'], ['Q', 'u'])
                    if '_'.join(p) in have)
    dlig = ' '.join(lig(p) for p in (['c', 'h'], ['c', 'k'], ['t', 'z'], ['t', 't']) if '_'.join(p) in have)
    if 'T_h.swsh' in have: dlig += ' sub T h by T_h.swsh;'
    liga = liga.replace('sub f f i by f_f_i;', '')
    lnum = ' '.join(f'sub {f} by {f}.lf;' for f in FIGS)
    onum = ' '.join(f'sub {f}.lf by {f};' for f in FIGS)
    extra = ''
    sw = [n for n in order if n.endswith('.swsh') and '_' not in n]
    if sw:
        extra += 'feature swsh { ' + ' '.join(f'sub {n.split(".")[0]} by {n};' for n in sw) + ' sub T h by T_h.swsh; } swsh;\n'
        alts = [n for n in order if n.endswith(('.alt',)) or n == 'e.swsh']
        extra += 'feature ss01 { ' + ' '.join(f'sub {n.split(".")[0]} by {n};' for n in alts) + ' } ss01;\n'
        extra += 'feature salt { ' + ' '.join(f'sub {n.split(".")[0]} by {n};' for n in alts + sw) + ' } salt;\n'
    fea = FEA.format(liga=liga or '', dlig=dlig or '', lnum=lnum, onum=onum, extra=extra)
    fea = fea.replace('feature dlig {  } dlig;', '')

    psname = FAMILY.replace(' ', '') + '-' + style
    fb = FontBuilder(UPM, isTTF=not otf)
    fb.setupGlyphOrder(order)
    cmap = {UNI[n]: n for n in order if n in UNI}
    for n, u in NATIVE_ACC.items(): cmap[u] = n
    for n, (_, _, u) in ACCENTED.items():
        if n in have: cmap[u] = n
    fb.setupCharacterMap(cmap)
    if otf:
        cs = {}
        for n in order:
            pen = T2CharStringPen(adv[n], None)
            draw(ReverseContourPen(pen), glyphs[n])
            cs[n] = pen.getCharString()
        fb.setupCFF(psname, {'FullName': f'{FAMILY} {style}', 'FamilyName': FAMILY, 'Weight': style}, cs, {})
    else:
        gl = {}
        for n in order:
            pen = TTGlyphPen(None); draw(pen, glyphs[n], quad=True); gl[n] = pen.glyph()
        fb.setupGlyf(gl)
    lsb = {}
    for n in order:
        bp = BoundsPen(None); draw(bp, glyphs[n], quad=not otf)
        lsb[n] = int(np.floor(bp.bounds[0])) if bp.bounds else 0
    fb.setupHorizontalMetrics({n: (adv[n], lsb[n]) for n in order})
    asc, desc = 800, -250
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=200)
    bold = style == 'Bold'; italic = style == 'Italic'
    fb.setupNameTable({
        'familyName': FAMILY, 'styleName': style,
        'uniqueFontIdentifier': f'{psname};{VERSION}', 'fullName': f'{FAMILY} {style}',
        'psName': psname, 'version': f'Version {VERSION}',
        'copyright': 'Traced from D. Stempel AG specimen cards of the foundry type designed by Hermann Zapf (1950-51), photographed by Letterform Archive.',
        'description': 'A revival of a 1950s Stempel foundry type, traced from its specimen cards.',
    })
    fsSel = (0x20 if bold else 0) | (0x01 if italic else 0) | (0x40 if style == 'Regular' else 0)
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=200, usWinAscent=1000, usWinDescent=330,
                sxHeight=int(round(XH)), sCapHeight=int(CAP), usWeightClass=700 if bold else 400,
                achVendID='NONE', fsType=0, fsSelection=fsSel)
    fb.setupPost(italicAngle=-9.0 if italic else 0)
    if bold or italic:
        fb.font['head'].macStyle = (1 if bold else 0) | (2 if italic else 0)
    fb.font['head'].fontRevision = float(VERSION)
    addOpenTypeFeaturesFromString(fb.font, fea)
    d = os.path.join(ROOT, 'fonts', 'otf' if otf else 'ttf')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f'{psname}.{"otf" if otf else "ttf"}')
    fb.save(p); print('wrote', os.path.relpath(p, ROOT), len(order), 'glyphs')

if __name__ == '__main__':
    for st in [a for a in sys.argv[1:] if a in ('Regular', 'Italic', 'Bold')] or ['Regular', 'Italic', 'Bold']:
        font(st, otf=True); font(st, otf=False)

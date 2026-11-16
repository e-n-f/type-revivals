"""Build the Exec fonts: each IBM Executive face's characters averaged over the scans, traced, and set on the
typewriter's unit widths.

    python3 tools/build.py [Modern Documentary ...]   ->  fonts/otf/Exec<Face>-Regular.otf, fonts/ttf/...ttf

Needs build/occ-*.pkl and build/units-*.json from tools/read.py and tools/units.py.

Scale: 200 font units to the 1/32-inch unit, so 6400 units to the inch (1000 to the em: the type prints at
its typewriter size when set at 11.25 pt).  A 1/36-inch face's unit is 6400/36 = 177.8 font units and a
1/45-inch face's 142.2; each advance is its whole number of units, rounded to the font unit.
"""
import sys, os, json, pickle, unicodedata, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
import trace
from fontio import draw, autohint
from glyphs import Img, average, average_imgs
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.agl import UV2AGL

ROOT = os.path.join(HERE, '..')
BUILD = os.path.join(ROOT, 'build')
# Each font's version, in the head table and the name table.  Raise a font's version with every change to
# that font, or font managers treat the new file as a duplicate of the installed one (see CONTRIBUTING.md).
VERSIONS = {'Modern': '1.000', 'Documentary': '1.000', 'MidCentury': '1.000', 'Arcadia': '1.000',
            'Doric': '1.000', 'BoldFace1': '1.000', 'BoldFace2': '1.000', 'Charter': '1.000'}
NAMES = {'Modern': 'Modern', 'Documentary': 'Documentary', 'MidCentury': 'Mid-Century', 'Arcadia': 'Arcadia',
         'Doric': 'Doric', 'BoldFace1': 'Bold Face 1', 'BoldFace2': 'Bold Face 2', 'Charter': 'Charter'}
BOLD = {'BoldFace1', 'BoldFace2'}
# where each face's glyphs come from, in order of preference: a character missing from the first source is
# taken from the next.  Modern: the Jowa card (large, sharp) and the Finnish brochure for ` ´ §.
# (source, the characters taken from it; None for all)
SOURCES = {f: [(f, None)] for f in VERSIONS}
SOURCES['Modern'] = [('Modern', None), ('ModernFI', '`´§&'), ('Keyboard', '@#¢_')]
# the keyboard photograph is scaled so its figures are as tall as the Jowa card's (its unit fit is too rough
# to set the scale by)
MATCH_FIGURES = {'Keyboard': 'Modern'}
SPACE_FROM = {'Modern': 'ModernFI'}      # the Jowa text is justified foundry type: its word spaces vary
UPM = 1000
PER_INCH = 6400                          # 200 font units to the 1/32 inch
LINE = PER_INCH / 6                      # single spacing, six lines to the inch
SIGMA = 0.25                             # smoothing of the traced ink, in pixels of the scan

NATIVE = set('çÇøØß')                    # accented and special letters kept as printed, not composed
COMPOSE = 'àáâãäåèéêëìíîïñòóôõöùúûüýÿÀÁÂÃÄÅÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝŸ'
MARK = {'̀': 'grave', '́': 'acute', '̂': 'circumflex', '̃': 'tilde', '̈': 'dieresis',
        '̊': 'ring'}
SPACING = {'`': 'grave', '´': 'acute'}   # the typewriter's dead-key accents, printed on their own
# typographic quotes typed with the typewriter's straight ones
ALIAS = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0xA0: ' '}


def decompose(ch):
    d = unicodedata.normalize('NFD', ch)
    return (d[0], MARK[d[1]]) if len(d) == 2 and d[1] in MARK else (None, None)


def gname(ch):
    if ch == 'ı': return 'dotlessi'
    return UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


class Source:
    def __init__(self, name):
        self.name = name
        u = json.load(open(os.path.join(BUILD, f'units-{name}.json')))
        self.esc = u['escapement']; self.p = u['pitch']; self.units = u['units']; self.offset = u['offset']
        self.unit = PER_INCH / self.esc              # font units per typewriter unit
        self.k = self.unit / self.p                  # font units per scan pixel
        res = pickle.load(open(os.path.join(BUILD, f'occ-{name}.pkl'), 'rb'))
        self.occ = [o for _, oc in res if oc for o in oc]
        if name in MATCH_FIGURES:
            ref = Source(MATCH_FIGURES[name])
            h = lambda s, c: np.median([o['bottom'] - o['top'] for o in s.occ if o['ch'] == c])
            figs = [c for c in '0123456789' if c in self.units and c in ref.units]
            self.k = float(np.median([h(ref, c) * ref.k / h(self, c) for c in figs]))

    def by_char(self):
        d = {}
        for o in self.occ: d.setdefault(o['ch'], []).append(o)
        return d

    def space(self):
        """the word space in units: from the gap between the slugs of the last letter of a word and the first
        of the next, on the same line"""
        lines = {}
        for o in self.occ: lines.setdefault(o['line'], []).append(o)
        gaps = []
        for occ in lines.values():
            occ.sort(key=lambda o: o['x0'])
            for a, b in zip(occ, occ[1:]):
                if a['word'] == b['word'] or a['ch'] not in self.units or b['ch'] not in self.units: continue
                ra = a['x0'] + a['w'] / 2 - self.offset.get(a['ch'], 0) + self.units[a['ch']] * self.p / 2
                lb = b['x0'] + b['w'] / 2 - self.offset.get(b['ch'], 0) - self.units[b['ch']] * self.p / 2
                gaps.append((lb - ra) / self.p)
        return max(2, int(round(float(np.median(gaps))))), len(gaps)


def clean(occs):
    """drop occurrences much wider or narrower than the median (a mismatched or damaged print), and touching
    ones that were split from a neighbour if enough whole ones remain"""
    whole = [o for o in occs if not o.get('touching')]
    if len(whole) >= 2: occs = whole
    if len(occs) < 3: return occs
    w = np.median([o['w'] for o in occs]); h = np.median([o['bottom'] - o['top'] for o in occs])
    keep = [o for o in occs if abs(o['w'] - w) < 0.2 * w + 2 and abs(o['bottom'] - o['top'] - h) < 0.2 * h + 2]
    return keep or occs


def mask_rows(im, keep):
    """im with only the rows (y in font units) where keep(y) is true"""
    ys = im.top - np.arange(im.ink.shape[0])
    return Img(np.where(keep(ys)[:, None], im.ink, 0), im.x0, im.top)


def top_of(im): return im.bbox()[3]


def glyph_images(face):
    """{char: (Img in font units, baseline at y = 0, ink placed anywhere), units, offset in font units, source}"""
    srcs = [Source(s) for s, _ in SOURCES[face]]
    G = {}
    for s, (_, only) in zip(srcs, SOURCES[face]):
        for ch, occs in s.by_char().items():
            if ch in G or (only and ch not in only): continue
            occs = clean(occs)
            # a character with no neighbour to fit (the last of a line): its ink and half a unit of margin
            # (a width fitted from another source of the face comes first: Modern's & from the brochure)
            u = (next((t.units[ch] for t in srcs if ch in t.units), None)
                 or max(2, int(round(np.median([o['w'] for o in occs]) / s.p + 0.5))))
            G[ch] = dict(img=average(occs, s.k), units=u, off=s.offset.get(ch, 0) * s.k, src=s, n=len(occs))
    return G, srcs


def marks(G, xh, cap):
    """the accents, each averaged over the letters that carry it: {(kind, 'lc'|'uc'): (Img centred on x = 0,
    offset of its centre from the base letter's centre)}"""
    found = {}
    for ch, g in G.items():
        base, kind = decompose(ch)
        if not base or base not in G: continue
        case = 'uc' if base.isupper() else 'lc'
        bimg = G['ı']['img'] if base == 'i' and 'ı' in G else G[base]['img']
        btop = top_of(bimg)
        im = g['img']
        parts = [p for p in im.parts() if p.ink.max() > 0.5]
        mk = [p for p in parts if p.bbox()[1] > btop - 0.05 * xh]
        if mk:
            m = mk[0]
            for p in mk[1:]: m = m.union(p)
            rest = [p for p in parts if not any(p is q for q in mk)]
            b = rest[0]
            for p in rest[1:]: b = b.union(p)
        else:      # the accent touches the letter (a ring on A): cut above the letter's top
            cut = btop + 0.03 * (cap if case == 'uc' else xh)
            m = mask_rows(im, lambda y: y > cut); b = mask_rows(im, lambda y: y <= cut)
        if not (m.ink > 0.5).any(): continue
        dx = m.cx() - b.cx()
        found.setdefault((kind, case), []).append((m.shift(-m.cx(), 0), dx, g['n']))
    for ch, kind in SPACING.items():   # the dead-key accents, where no letter shows the accent
        if ch in G and (kind, 'lc') not in found:
            m = G[ch]['img']; found[(kind, 'lc')] = [(m.shift(-m.cx(), 0), 0.0, G[ch]['n'])]
    out = {}
    for key, lst in found.items():
        img = average_imgs([m for m, _, _ in lst])
        dx = sum(d * n for _, d, n in lst) / sum(n for _, _, n in lst)
        out[key] = (img.shift(-img.cx(), 0), dx)
    for kind in set(k for k, _ in out):   # a capital's accent missing: the lower case one, raised
        if (kind, 'uc') not in out and (kind, 'lc') in out:
            m, dx = out[(kind, 'lc')]; out[(kind, 'uc')] = (m.shift(0, cap - xh), dx)
    return out


def standin(G, small, big, ref):
    """w (W) from two overlapped v (V): the width in units from the v and Modern's ratio of w to v; the two
    copies spaced so the w has the v's side bearings"""
    v = G[small]
    units = max(v['units'] + 1, int(round(v['units'] * ref[big] / ref[small])))
    unit = v['src'].unit
    b = v['img'].bbox(); inkw = b[2] - b[0]
    target = inkw + (units - v['units']) * unit
    img = v['img'].union(v['img'].shift(target - inkw, 0))
    return dict(img=img, units=units, off=v['off'], src=v['src'], n=v['n'], standin=True)


def build(face):
    G, srcs = glyph_images(face)
    notes = []
    xh = top_of(G['x']['img']); cap = top_of(G['H']['img'])
    # ( and ) are one another turned round, where the source shows only one
    for a, b in (('(', ')'), (')', '(')):
        if a in G and b not in G:
            G[b] = dict(G[a], img=G[a]['img'].rot180(), off=-G[a]['off']); notes.append(f'{b} from {a}')
    if 'i' in G:     # dotless i: the i without its dot
        parts = G['i']['img'].parts()
        stem = [p for p in parts if p.bbox()[1] < 0.5 * xh]
        img = stem[0]
        for p in stem[1:]: img = img.union(p)
        G['ı'] = dict(G['i'], img=img)
    ref = json.load(open(os.path.join(BUILD, 'units-Modern.json')))['units']
    if 'w' not in G and 'v' in G: G['w'] = standin(G, 'v', 'w', ref); notes.append('w from two v')
    if 'W' not in G and 'V' in G: G['W'] = standin(G, 'V', 'W', ref); notes.append('W from two V')
    M = marks(G, xh, cap)
    composed = []
    for ch in COMPOSE:
        base, kind = decompose(ch)
        case = 'uc' if base.isupper() else 'lc'
        bk = 'ı' if base == 'i' else base
        if bk not in G or (kind, case) not in M: continue
        m, dx = M[(kind, case)]; b = G[bk]
        img = b['img'].union(m.shift(b['img'].cx() + dx, 0))
        G[ch] = dict(b, img=img); composed.append(ch)
    for ch, kind in SPACING.items():   # spacing accents: the mark averaged from the letters, where they show it
        if (kind, 'lc') in M:
            m, _ = M[(kind, 'lc')]
            G[ch] = dict(img=m, units=G[ch]['units'] if ch in G else 2, off=0.0, src=srcs[0], n=0)
    if (('dieresis', 'lc') in M) and '¨' not in G:
        G['¨'] = dict(img=M[('dieresis', 'lc')][0], units=G['´']['units'] if '´' in G else 2, off=0.0,
                      src=srcs[0], n=0)
    # an accented letter printed but not composable (its accent found on no other letter) stays as printed

    # outlines: each glyph's ink centre at the centre of its slug, moved by the fitted offset
    glyphs, adv = {}, {}
    for ch, g in G.items():
        a = int(round(g['units'] * g['src'].unit))
        im = g['img']; b = im.bbox()
        im = im.shift(a / 2 + g['off'] - (b[0] + b[2]) / 2, 0)
        segs = trace.trace(im.ink, SIGMA * g['src'].k)
        glyphs[gname(ch)] = [[(s[0],) + tuple((p[0] + im.x0, p[1] + im.top) for p in s[1:]) for s in c]
                             for c in segs]
        adv[gname(ch)] = a
    s = Source(SPACE_FROM.get(face, face))
    assert s.unit == srcs[0].unit
    su, n = s.space()
    adv['space'] = int(round(su * srcs[0].unit)); glyphs['space'] = []
    glyphs['.notdef'] = [[('L', (60, 0), (60, 640)), ('L', (60, 640), (340, 640)), ('L', (340, 640), (340, 0)),
                          ('L', (340, 0), (60, 0))]]
    adv['.notdef'] = 400
    cmap = {ord(ch): gname(ch) for ch in G}
    cmap[0x20] = 'space'
    for u, ch in ALIAS.items():
        if ch == ' ' or ch in G: cmap[u] = 'space' if ch == ' ' else gname(ch)
    print(f'{face}: {len(G)} characters ({len(composed)} composed), space {su} units from {n} gaps;'
          f' {"; ".join(notes)}')
    return glyphs, adv, cmap, dict(xh=xh, cap=cap, esc=srcs[0].esc, space=su, composed=''.join(composed))


def font(face, otf=True, data=None):
    glyphs, adv, cmap, info = data or build(face)
    family = 'Exec ' + NAMES[face]; style = 'Regular'
    psname = family.replace(' ', '').replace('-', '') + '-' + style
    VERSION = VERSIONS[face]
    order = ['.notdef', 'space'] + sorted(n for n in glyphs if n not in ('.notdef', 'space'))
    fb = FontBuilder(UPM, isTTF=not otf)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    if otf:
        cs = {}
        for n in order:
            pen = T2CharStringPen(adv[n], None); draw(ReverseContourPen(pen), glyphs[n]); cs[n] = pen.getCharString()
        fb.setupCFF(psname, {'FullName': family, 'FamilyName': family, 'Weight': 'Bold' if face in BOLD else 'Regular'},
                    cs, {})
    else:
        gl = {}
        for n in order:
            pen = TTGlyphPen(None); draw(pen, glyphs[n], quad=True); gl[n] = pen.glyph()
        fb.setupGlyf(gl)
    lsb = {}; ymax = 0; ymin = 0
    for n in order:
        bp = BoundsPen(None); draw(bp, glyphs[n], quad=not otf)
        lsb[n] = int(np.floor(bp.bounds[0])) if bp.bounds else 0
        if bp.bounds: ymin = min(ymin, bp.bounds[1]); ymax = max(ymax, bp.bounds[3])
    fb.setupHorizontalMetrics({n: (adv[n], lsb[n]) for n in order})
    # the line is the typewriter's single spacing, split between ascent and descent as the glyphs are
    desc = int(np.floor(ymin)); asc = int(round(LINE)) + desc
    asc = max(asc, int(np.ceil(info['cap'] * 1.25)))
    gap = max(0, int(round(LINE)) - (asc - desc))
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=gap)
    fb.setupNameTable({
        'familyName': family, 'styleName': style,
        'uniqueFontIdentifier': f'{psname};{VERSION}', 'fullName': family,
        'psName': psname, 'version': f'Version {VERSION}',
        'copyright': 'Traced from printed specimens of the IBM Executive typewriter faces (1950s).',
        'description': f'A revival of the IBM Executive proportional typewriter face {NAMES[face]} '
                       f'(1/{info["esc"]}-inch units), traced from its specimens.',
    })
    bold = face in BOLD
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=gap,
                usWinAscent=int(np.ceil(max(ymax, asc))), usWinDescent=int(np.ceil(max(-ymin, -desc))),
                sxHeight=int(round(info['xh'])), sCapHeight=int(round(info['cap'])),
                usWeightClass=700 if bold else 400, achVendID='NONE', fsType=0,
                fsSelection=0x40 | 0x80)   # regular, use the typo metrics
    fb.setupPost()
    fb.font['head'].fontRevision = float(VERSION)
    d = os.path.join(ROOT, 'fonts', 'otf' if otf else 'ttf')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f'{psname}.{"otf" if otf else "ttf"}')
    fb.save(p)
    if not otf: autohint(p)
    print('  wrote', os.path.relpath(p, ROOT), len(order), 'glyphs')


if __name__ == '__main__':
    infos = {}
    for face in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        data = build(face)
        font(face, True, data); font(face, False, data)
        infos[face] = data[3]
    json.dump(infos, open(os.path.join(BUILD, 'fonts.json'), 'w'), indent=1, ensure_ascii=False)

"""Build the Executive fonts: each Executive typewriter face's characters averaged over the scans, traced, and set on the
typewriter's unit widths.

    python3 tools/build.py [Modern Documentary ...]   ->  fonts/otf/Executive<Face>-Regular.otf, fonts/ttf/...ttf

Needs build/occ-*.pkl and build/units-*.json from tools/read.py and tools/units.py.

Scale: 200 font units to the 1/32-inch unit, so 6400 units to the inch (1000 to the em: the type prints at
its typewriter size when set at 11.25 pt).  A 1/36-inch face's unit is 6400/36 = 177.8 font units and a
1/45-inch face's 142.2; each advance is its whole number of units, rounded to the font unit.
"""
import sys, os, json, pickle, unicodedata, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
import trace
from fontio import draw, autohint
from glyphs import Img, average, average_imgs
from fontTools.fontBuilder import FontBuilder
import sources as _S0
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ROOT = os.path.join(HERE, '..')
BUILD = os.path.join(ROOT, 'build')
# Each font's version, in the head table and the name table.  Raise a font's version with every change to
# that font, or font managers treat the new file as a duplicate of the installed one (see CONTRIBUTING.md).
VERSIONS = {'Modern': '1.005', 'Documentary': '1.007', 'MidCentury': '1.005', 'Arcadia': '1.007',
            'Doric': '1.006', 'BoldFace1': '1.007', 'BoldFace2': '1.006', 'Charter': '1.006',
            'Secretarial': '1.000', 'Registry': '1.000'}
OLD_FACES = list(VERSIONS)
# the faces whose main source is their page of 'Typesetting with the IBM Executive' (tools/units.py SET_FACES)
NEW_FACES = ['Text', 'Directory', 'Testimonial', 'BoldFaceItalic', 'Copperplate1', 'Copperplate2', 'Patron']
VERSIONS.update({f: '1.000' for f in NEW_FACES})
# Raised for the signs § ‡ ¶ † ‘ from the 'Typesetting' pages
VERSIONS.update(Modern='1.006', Documentary='1.008', MidCentury='1.006', Arcadia='1.008', Doric='1.006',
                BoldFace1='1.008', BoldFace2='1.007', Charter='1.007', Secretarial='1.001', Registry='1.001')
NAMES = {'Modern': 'Modern', 'Documentary': 'Documentary', 'MidCentury': 'Mid-Century', 'Arcadia': 'Arcadia',
         'Doric': 'Doric', 'BoldFace1': 'Bold Face 1', 'BoldFace2': 'Bold Face 2', 'Charter': 'Charter',
         'Secretarial': 'Secretarial', 'Registry': 'Registry', 'Text': 'Text', 'Directory': 'Directory',
         'Testimonial': 'Testimonial', 'BoldFaceItalic': 'Bold Face 1', 'Copperplate1': 'Copperplate Gothic 1',
         'Copperplate2': 'Copperplate Gothic 2', 'Patron': 'Patron'}
# Bold Face Italic is the italic of Bold Face 1 (IBM's 1972 catalogue: "Boldface Italic No. 1"): the same family
ITALIC = {'BoldFaceItalic': -14.0}
BOLD = {'BoldFace1', 'BoldFace2', 'BoldFaceItalic'}
# where each face's glyphs come from, in order of preference: a character missing from the first source is
# taken from the next.  Modern: the Jowa card (large, sharp) and the Finnish brochure for ` ´ §.
# (source, the characters taken from it; None for all)
SOURCES = {f: [(f, None)] for f in VERSIONS}
SOURCES['Modern'] = [('Modern', None), ('ModernFI', '`´§&'), ('Keyboard', '@#¢_')]
# documents typed in the faces, for what the brochure lacks (a real w and W among it)
SOURCES['MidCentury'] = [('MidCenturyTyped', 'wW'), ('MidCentury', None), ('MidCenturyTyped', ':;"*')]
# Arcadia's a: the two-storey one of the 1955 newsletter that announced the face (and of IBM's catalogue);
# the brochure's machine had the one-storey alternate, which is ss01
SOURCES['Arcadia'] = [('ArcadiaTyped', 'awW'), ('Arcadia', None), ('ArcadiaTyped', ':;\'"@#$¢*_')]
SOURCES['Charter'] = [('CharterTyped', 'W'), ('Charter', None), ('CharterTyped', ';:*\'#@!\\')]
# IBM's 1972 "Type Available" catalogue (tools/catalog.py): a real w and W for every face that has no other
# source of them, the characters chosen from its other cells (catalog.CHOSEN; Mid-Century's # among them, in
# place of the letter's small raised one), and IBM's own widths
from catalog import CHOSEN as _CHOSEN
for _f in OLD_FACES: SOURCES[_f].append((f'Catalog{_f}', 'wW' + ''.join(_CHOSEN.get(_f, {}))))
# 'Typesetting with the IBM Executive': § ‡ ¶ † ‘, which no other source of these faces shows
for _f in OLD_FACES:
    if _f in _S0.TYPESET: SOURCES[_f].append((f'{_f}Set', '§‡¶†‘'))   # (Doric has no page)
# The new faces: their 'Typesetting' page, the catalogue filling in.  Bold Face Italic's page is soft (read
# darkened, which thickens it), so its letters are the catalogue's and the page gives the rest.
for _f in NEW_FACES: SOURCES[_f] = [(f'{_f}Set', None), (f'Catalog{_f}', None)]
SOURCES['BoldFaceItalic'] = [('CatalogBoldFaceItalic', None), ('BoldFaceItalicSet', None)]
SOURCES['Copperplate1'] = [('Copperplate1Set', None)]           # its catalogue page shows signs only
# Faces with no brochure line (tools/units.py CATALOG_FACES): Secretarial's letters from the catalogue (the memo
# typed in it is a faint photocopy), its signs and figures from the memo; Registry's from the newsletter typed in
# it, the catalogue filling in.  MAIN: the source the others are scaled, thickened and levelled to.
# Secretarial's 1 and 0, which the catalogue and the memo lack, are its 'Typesetting' page's; that page also
# fills in what the others don't show (§ ‡ ¶ † ‘, and Secretarial's & and #), as Registry's does for it
SOURCES['Secretarial'] = [('SecretarialSet', '10'), ('CatalogSecretarial', None), ('SecretarialTyped', None)]
SOURCES['Registry'] = [('RegistryTyped', None), ('CatalogRegistry', None)]
for _f in ('Secretarial', 'Registry'):
    if _f in _S0.TYPESET: SOURCES[_f].append((f'{_f}Set', None))
MAIN = {'Secretarial': 'CatalogSecretarial', 'Registry': 'RegistryTyped',
        **{f: f'{f}Set' for f in NEW_FACES}, 'BoldFaceItalic': 'CatalogBoldFaceItalic'}
# A source scaled so its letters are as tall as another's: the keyboard photograph's figures to the Jowa
# card's (its unit fit is too rough to set the scale by), and the typed documents' letters to the brochure's
# (the brochure's halftone thins the ink, so its letters print a few per cent smaller than typed ones).
MATCH_HEIGHTS = {'Keyboard': ('Modern', '0123456789'), 'MidCenturyTyped': ('MidCentury', 'EFHILTZxzvnmu'),
                 'CharterTyped': ('Charter', 'EFHILTZxzvnmu'), 'ArcadiaTyped': ('Arcadia', 'EFHILTZxzvnmu'),
                 **{f'Catalog{f}': (f, 'EFHILTZxzvnmu') for f in VERSIONS},
                 'CatalogSecretarial': ('SecretarialTyped', 'EFHILTxzvnmu'),
                 'CatalogRegistry': ('RegistryTyped', 'EFHILTZxzvnmu'),
                 **{f'{f}Set': (MAIN.get(f, f), 'EFHILTZxzvnmu') for f in OLD_FACES if f in _S0.TYPESET},
                 **{f'Catalog{f}': (f'{f}Set', 'EFHILTZxzvnmu') for f in NEW_FACES},
                 'CatalogBoldFaceItalic': ('BoldFaceItalicSet', 'EFHILTZxzvnmu')}
# printed sources, crisper than the typed ones: thickened to the face's weight (match_weight)
REWEIGHT = ({f'Catalog{f}' for f in VERSIONS} - {'CatalogSecretarial', 'CatalogBoldFaceItalic'}
            | {f'{f}Set' for f in OLD_FACES} | {'BoldFaceItalicSet'}) - {'SecretarialSet'}
# (Secretarial's page is as heavy as its catalogue letters already: matching would erode its thin strokes away)
# Stylistic alternates: (source, character, feature, name).  Arcadia's one-storey a (IBM part 1112308), as the
# Finnish brochure's machine had it; it has the a's width and place in its slug, and the accented a's get it
# too.  Each alternate is also offered by salt.
ALTERNATES = {'Arcadia': [('Arcadia', 'a', 'ss01', 'One-storey a')]}
SPACE_FROM = {'Modern': 'ModernFI'}      # the Jowa text is justified foundry type: its word spaces vary
SPACE_FROM.update(Secretarial='SecretarialTyped', Registry='RegistryTyped', **{f: f'{f}Set' for f in NEW_FACES})
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
    if len(ch) > 1: base, suffix = ch.rsplit('.', 1); return gname(base) + '.' + suffix   # an alternate
    if ch == 'ı': return 'dotlessi'
    return UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


class Source:
    def __init__(self, name):
        self.name = name
        path = os.path.join(BUILD, f'units-{name}.json')
        if os.path.exists(path):
            u = json.load(open(path))
            self.esc = u['escapement']; self.p = u['pitch']; self.units = u['units']; self.offset = u['offset']
            # a character seen in few neighbour pairs (a sign typed once, beside other signs): its fitted offset
            # trades against its width and can be off by a unit, so it is centred in its slug instead
            cnt = u.get('count', {})
            self.offset = {c: v for c, v in self.offset.items() if cnt.get(c, 0) >= 4}
            self.unit = PER_INCH / self.esc              # font units per typewriter unit
            self.k = self.unit / self.p                  # font units per scan pixel
        else:       # a printed sheet: no units of its own; its scale is set by MATCH_HEIGHTS
            self.esc = self.p = None; self.units = {}; self.offset = {}
        res = pickle.load(open(os.path.join(BUILD, f'occ-{name}.pkl'), 'rb'))
        drop = _S0.TYPESET_DROP.get(name, '')
        self.occ = [o for _, oc in res if oc for o in oc if o['ch'] not in drop]
        if name in MATCH_HEIGHTS:
            ref, chars = MATCH_HEIGHTS[name]; ref = Source(ref)
            if self.esc is None: self.esc, self.unit = ref.esc, ref.unit
            h = lambda s, c: np.median([o['bottom'] - o['top'] for o in s.occ if o['ch'] == c])
            have = set(o['ch'] for o in self.occ) & set(o['ch'] for o in ref.occ)
            self.k = float(np.median([h(ref, c) * ref.k / h(self, c) for c in chars if c in have]))

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
    ones that were split from a neighbour if there is a whole one: the split clips them (Documentary's X in its
    capitals line lost a serif), and a clipped copy averaged with a whole one smears it"""
    whole = [o for o in occs if not o.get('touching')]
    if whole: occs = whole
    if len(occs) < 3: return occs
    w = np.median([o['w'] for o in occs]); h = np.median([o['bottom'] - o['top'] for o in occs])
    keep = [o for o in occs if abs(o['w'] - w) < 0.2 * w + 2 and abs(o['bottom'] - o['top'] - h) < 0.2 * h + 2]
    return keep or occs


def mask_rows(im, keep):
    """im with only the rows (y in font units) where keep(y) is true"""
    ys = im.top - np.arange(im.ink.shape[0])
    return Img(np.where(keep(ys)[:, None], im.ink, 0), im.x0, im.top)


def top_of(im): return im.bbox()[3]


# sources read from an un-slanted scan (sources.SHEAR): their glyphs slanted back
import sources as _S
UNSHEAR = {'BoldFaceItalicSet': _S.SHEAR['typesetting-boldfaceitalic-1.png']}


def slant(img, sh):
    """img leaned right by sh (x + sh * height above its bottom), undoing the shear the scan was read with"""
    H, W = img.ink.shape; pad = int(np.ceil(sh * H)) + 2
    M = np.float32([[1, -sh, sh * (H - 1)], [0, 1, 0]])
    ink = cv2.warpAffine(img.ink, M, (W + pad, H), flags=cv2.INTER_LINEAR)
    return Img(ink, img.x0, img.top)


def height(o):
    """an occurrence's ink's centre of mass, in pixels above its line's baseline"""
    a = o['ink']; return (o['base'] - o['Y0']) - float((a.sum(1) * np.arange(a.shape[0])).sum() / a.sum())


def level(occs, s, main):
    """occurrences from a second source, moved up or down to the main source's baselines.  A line's baseline is
    estimated from the letters on it that sit on the baseline, and a line of signs has few: its baseline can be
    several pixels off (Arcadia's and Bold Face 1's $ came out 100 units high).  So each line is moved by the
    median difference, in font units, between its characters and the same characters in the main source"""
    if s.name == main.name: return occs
    ref = {c: float(np.median([height(o) for o in os_])) * main.k for c, os_ in main.by_char().items()}
    lines = {}
    for o in s.occ: lines.setdefault(o['line'], []).append(o)
    out = []
    for o in occs:
        d = [ref[q['ch']] - height(q) * s.k for q in lines.get(o['line'], []) if q['ch'] in ref]
        if len(d) < 2: out.append(o); continue
        out.append(dict(o, base=o['base'] + float(np.median(d)) / s.k))
    return out


def rescale(o, f):
    """an occurrence redrawn at f times its scale, so it can be averaged with another source's (place() uses only
    its ink and its edge and baseline relative to the ink's corner)"""
    ink = cv2.resize(o['ink'], None, fx=f, fy=f, interpolation=cv2.INTER_LINEAR)
    return dict(o, ink=ink, X0=0.0, Y0=0.0, x0=(o['x0'] - o['X0']) * f, base=(o['base'] - o['Y0']) * f,
                w=o['w'] * f, top=(o['top'] - o['Y0']) * f, bottom=(o['bottom'] - o['Y0']) * f)


# a face's further 'Typesetting' pages, pooled with its first: their prints averaged in, each from its own scale
POOL = {f'{f}Set': [f'{f}Set{n}' for n in pages] for f, pages in _S0.TYPESET_MORE.items()}


def glyph_images(face):
    """{char: (Img in font units, baseline at y = 0, ink placed anywhere), units, offset in font units, source}"""
    srcs = [Source(s) for s, _ in SOURCES[face]]
    main = Source(MAIN.get(face, face))    # the face's own (brochure or Jowa) letters, for the weight
    cat = json.load(open(os.path.join(BUILD, 'catalog-units.json'))).get(face, {})
    G = {}
    for s, (_, only) in zip(srcs, SOURCES[face]):
        extra = {}
        for name in POOL.get(s.name, []):
            if not os.path.exists(os.path.join(BUILD, f'units-{name}.json')): continue
            t = Source(name)
            if len(t.occ) < 300: continue                 # a page that read poorly
            # its scale: by the heights of the letters both pages show (a fitted unit can be some way off on a
            # small, soft page; drawn to the wrong size, its prints blur the first page's)
            hs, ht = s.by_char(), t.by_char()
            h = lambda os_: float(np.median([o['bottom'] - o['top'] for o in os_]))
            fs = [h(hs[c]) / h(ht[c]) for c in 'EFHILTZxzvnmu' if c in hs and c in ht]
            if fs: t.k = s.k * float(np.median(fs))         # (level() moves it at this scale too)
            for ch, os_ in t.by_char().items():
                extra.setdefault(ch, []).extend(rescale(o, t.k / s.k) for o in level(clean(os_), t, s))
        for ch, occs in s.by_char().items():
            if ch in G or (only and ch not in only): continue
            occs = level(clean(occs + extra.get(ch, [])), s, main)
            # a character with no neighbour to fit (the last of a line): its ink and half a unit of margin
            # (IBM's own width comes first, where the catalogue prints one; then a width fitted from another
            # source of the face: Modern's & from the brochure)
            u = (cat.get(ch) or next((t.units[ch] for t in srcs if ch in t.units), None)
                 or max(2, int(round(np.median([o['w'] for o in occs]) / s.p + 0.5))))
            img = average(occs, s.k)
            if s.name in UNSHEAR: img = slant(img, UNSHEAR[s.name])
            if s.name in REWEIGHT: img, _ = match_weight(img, s, main)
            # the fitted offset in the slug holds only with the fitted width: where IBM's width differs (a
            # period fitted at 2 units, printed at 3), the glyph is centred
            fitted = next((t.units[ch] for t in srcs if ch in t.units), None)
            off = s.offset.get(ch, 0) * s.k if fitted in (None, u) else 0.0
            if not (img.ink > 0.5).any():          # too faint to trace: leave it for a later source
                print(f'  {face}: {ch!r} from {s.name} too faint, skipped'); continue
            G[ch] = dict(img=img, units=u, off=off, src=s, n=len(occs))
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


def stems(im, y):
    """the widths of the strokes the row at height y crosses"""
    m = im.ink[int(round(im.top - y))] > 0.5
    edges = np.flatnonzero(np.diff(np.r_[0, m.astype(np.int8), 0]))
    return list(edges[1::2] - edges[::2])


def match_weight(img, src, ref, chars='nmhu'):
    """img, from src, thickened to ref's weight: by the median difference of the stems of chars at half the
    x-height, half on each side.  (The type designs sheet is a crisp print; the brochure's halftone spreads the
    ink, and every other glyph of the face comes from it.)"""
    diffs = []
    for c in chars:
        a, b = average(clean(src.by_char()[c]), src.k), average(clean(ref.by_char()[c]), ref.k)
        xh = top_of(b); sa, sb = stems(a, xh / 2), stems(b, xh / 2)
        if len(sa) == len(sb): diffs += [y - x for x, y in zip(sa, sb)]
    if not diffs: return img, 0
    d = int(round(np.median(diffs) / 2))                         # positive: thicken; negative: thin
    if d == 0: return img, 0
    r = abs(d)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    ink = (cv2.dilate if d > 0 else cv2.erode)(np.pad(img.ink, r), k)
    # thickening grows the glyph by r on every side (thinning shrinks it): scale it back to its height and width
    # about its middle, so only its strokes change (a catalogue W was 5 % taller than the capitals beside it)
    m = img.ink > 0.5; ys = np.nonzero(m.any(1))[0]; xs = np.nonzero(m.any(0))[0]
    if not len(ys) or min(len(ys), len(xs)) <= max(0, -2 * d) + 1: return img, 0   # too faint or small to change
    h, w = ys[-1] - ys[0] + 1, xs[-1] - xs[0] + 1
    sy, sx = h / (h + 2 * d), w / (w + 2 * d)
    cy, cx = r + (ys[0] + ys[-1]) / 2, r + (xs[0] + xs[-1]) / 2       # the ink's middle in the padded image
    M = np.float32([[sx, 0, cx * (1 - sx)], [0, sy, cy * (1 - sy)]])
    ink = cv2.warpAffine(ink, M, (ink.shape[1], ink.shape[0]), flags=cv2.INTER_LINEAR)
    return Img(ink, img.x0 - r, img.top + r), 2 * d


def on_s(dollar, s):
    """the $ moved up or down so its centre of mass is the S's: its S-shaped body is most of its ink, and its
    bar reaches about as far above as below.  A $ from a line of signs is placed by that line's baseline, which
    can be off (Arcadia's and Bold Face 1's were 50-100 units high)"""
    c = lambda im: im.top - float((im.ink.sum(1) * np.arange(im.ink.shape[0])).sum() / im.ink.sum())
    return dollar.shift(0, c(s) - c(dollar))


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
    if '$' in G and 'S' in G: G['$'] = dict(G['$'], img=on_s(G['$']['img'], G['S']['img']))
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
    features = []
    large = [c for c in G if len(c) == 1 and 0xFF01 <= ord(c) <= 0xFF5E]   # Copperplate's shifted figures and signs
    if large:
        subs = []
        for c in large:
            base = chr(ord(c) - 0xFEE0)
            if base not in G: G[base] = G.pop(c); continue      # a sign printed only large: its only form
            G[f'{base}.ss01'] = G.pop(c); subs.append((gname(base), gname(f'{base}.ss01')))
        features.append(('ss01', 'Large figures and signs', sorted(subs)))
        notes.append(f'ss01: {len(subs)} large figures and signs')
    for src, ch, feat, label in ALTERNATES.get(face, []):
        s = Source(src); alt = average(clean(s.by_char()[ch]), s.k)
        alt, thick = match_weight(alt, s, Source(MAIN.get(face, face)))
        subs = [(ch, f'{ch}.{feat}')]
        G[f'{ch}.{feat}'] = dict(G[ch], img=alt, n=len(s.by_char()[ch]))
        for acc in composed:        # its accented forms, with the same accents in the same places
            base, kind = decompose(acc)
            if base != ch: continue
            m, dx = M[(kind, 'uc' if base.isupper() else 'lc')]
            G[f'{acc}.{feat}'] = dict(G[acc], img=alt.union(m.shift(alt.cx() + dx, 0)))
            subs.append((acc, f'{acc}.{feat}'))
        features.append((feat, label, [(gname(a), gname(b)) for a, b in subs]))
        notes.append(f'{feat}: {len(subs)} alternates from {src}, strokes {thick} units heavier')

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
    cmap = {ord(ch): gname(ch) for ch in G if len(ch) == 1}
    # a face with no 1 or 0 (Secretarial: its keyboard had none): typed with the l and the O, as on the machine
    for fig, letter in (('1', 'l'), ('0', 'O')):
        if fig not in G and letter in G: cmap[ord(fig)] = gname(letter)
    cmap[0x20] = 'space'
    for u, ch in ALIAS.items():
        if chr(u) in G: continue                       # the face has its own (a ‘ from 'Typesetting')
        if ch == ' ' or ch in G: cmap[u] = 'space' if ch == ' ' else gname(ch)
    print(f'{face}: {len(G)} characters ({len(composed)} composed), space {su} units from {n} gaps;'
          f' {"; ".join(notes)}')
    return glyphs, adv, cmap, dict(xh=xh, cap=cap, esc=srcs[0].esc, space=su, composed=''.join(composed),
                                   features=features)


def font(face, otf=True, data=None):
    glyphs, adv, cmap, info = data or build(face)
    family = 'Executive ' + NAMES[face]; style = 'Italic' if face in ITALIC else 'Regular'
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
    lsb = {}; ymax = 0; ymin = 0; lmin = 0
    for n in order:
        bp = BoundsPen(None); draw(bp, glyphs[n], quad=not otf)
        lsb[n] = int(np.floor(bp.bounds[0])) if bp.bounds else 0
        if bp.bounds:
            ymin = min(ymin, bp.bounds[1]); ymax = max(ymax, bp.bounds[3])
            if len(n) == 1 and n.isalpha(): lmin = min(lmin, bp.bounds[1])
    fb.setupHorizontalMetrics({n: (adv[n], lsb[n]) for n in order})
    # the line is the typewriter's single spacing, six lines to the inch, with the letters' descenders below
    # the baseline and the rest above (the underscore prints lower, at about the descender line, as typed)
    desc = int(np.floor(lmin)); asc = int(round(LINE)) + desc; gap = 0
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=gap)
    fb.setupNameTable({
        'familyName': family, 'styleName': style,
        'uniqueFontIdentifier': f'{psname};{VERSION}', 'fullName': family if style == 'Regular' else f'{family} {style}',
        'psName': psname, 'version': f'Version {VERSION}',
        'copyright': 'Traced from printed specimens of the Executive typewriter faces (1950s).',
        'description': f'A revival of the Executive proportional typewriter face {NAMES[face]} '
                       f'(1/{info["esc"]}-inch units), traced from its specimens.',
    })
    bold = face in BOLD
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=gap,
                usWinAscent=int(np.ceil(max(ymax, asc))), usWinDescent=int(np.ceil(max(-ymin, -desc))),
                sxHeight=int(round(info['xh'])), sCapHeight=int(round(info['cap'])),
                usWeightClass=700 if bold else 400, achVendID='NONE', fsType=0,
                fsSelection=(0x01 if face in ITALIC else 0x40) | 0x80, version=4)   # use the typo metrics (OS/2 v4)
    fb.setupPost(italicAngle=ITALIC.get(face, 0))
    if face in ITALIC: fb.font['head'].macStyle = 2
    fb.font['head'].fontRevision = float(VERSION)
    if info.get('features'):
        fea = 'languagesystem DFLT dflt;\nlanguagesystem latn dflt;\n'
        for feat, label, subs in info['features']:
            fea += (f'feature {feat} {{ featureNames {{ name "{label}"; }}; '
                    + ' '.join(f'sub {a} by {b};' for a, b in subs) + f' }} {feat};\n')
        fea += 'feature salt { ' + ' '.join(f'sub {a} by {b};' for _, _, subs in info['features'] for a, b in subs) + ' } salt;\n'
        addOpenTypeFeaturesFromString(fb.font, fea)
    d = os.path.join(ROOT, 'fonts', 'otf' if otf else 'ttf')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f'{psname}.{"otf" if otf else "ttf"}')
    fb.save(p)
    if not otf: autohint(p)
    print('  wrote', os.path.relpath(p, ROOT), len(order), 'glyphs')


if __name__ == '__main__':
    p = os.path.join(BUILD, 'fonts.json')        # what the specimens need of each font; kept for the others
    infos = json.load(open(p)) if os.path.exists(p) else {}
    for face in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        data = build(face)
        font(face, True, data); font(face, False, data)
        infos[face] = data[3]
    json.dump(infos, open(os.path.join(BUILD, 'fonts.json'), 'w'), indent=1, ensure_ascii=False)

"""Build the Sel fonts: each IBM Selectric face's characters averaged over the scans, traced, and set in the
typewriter's fixed cells.

    python3 tools/build.py [Courier72 Orator ...]   ->  fonts/otf/Sel<Face>-Regular.otf, fonts/ttf/...ttf

Needs build/occ-*.pkl from tools/read.py.

Every character is 600 font units wide, at 1000 to the em: a 10-pitch face set at 12 pt, or a 12-pitch face
at 10 pt, prints at the typewriter's own size (1/10 or 1/12 inch to the character).  A character keeps the
place in its cell the scans show: x = 0 at the cell's centre on the scan is x = 300 in the font.
"""
import sys, os, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
import trace
from fontio import draw, autohint
from glyphs import average
import sources as S
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
VERSIONS = {f: '1.000' for f in S.FACES}
NAMES = {'Advocate': 'Advocate', 'BookfaceAcademic72': 'Bookface Academic 72', 'Courier72': 'Courier 72',
         'Delegate': 'Delegate', 'Pica72': 'Pica 72', 'PrestigePica72': 'Prestige Pica 72', 'Adjutant': 'Adjutant',
         'Artisan12': 'Artisan 12', 'Courier12': 'Courier 12', 'Courier12Italic': 'Courier 12 Italic',
         'Elite72': 'Elite 72', 'LargeElite72': 'Large Elite 72', 'LetterGothic': 'Letter Gothic',
         'PrestigeElite72': 'Prestige Elite 72', 'Scribe': 'Scribe', 'Manifold72': 'Manifold 72', 'Orator': 'Orator',
         'DualGothic': 'Dual Gothic', 'LightItalic': 'Light Italic', 'Script': 'Script'}
ITALIC = {'Courier12Italic': -12.0, 'LightItalic': -12.0, 'Script': -10.0}
CAPS_ONLY = {'Manifold72'}            # the lower-case keys type the capitals
UPM, ADV = 1000, 600
SIGMA = 0.6                           # smoothing of the traced ink, in pixels of the scan
# typographic quotes typed with the typewriter's straight ones
ALIAS = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0xA0: ' '}


def gname(ch):
    return UV2AGL.get(ord(ch), f'uni{ord(ch):04X}')


def shape(a):
    ys, xs = np.nonzero(a > 0.5)
    c = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    import cv2
    return cv2.resize(c, (16, 20), interpolation=cv2.INTER_AREA).ravel()


def clean(occs):
    """drop occurrences of the wrong size or shape (a cell misread, a character damaged).  A paragraph's
    occurrence must look like the character's print in the alphabet lines, whose places are certain (a word
    matched to the wrong text has the right length but other letters); then any far from the median in width,
    height or normalized shape go too"""
    refs = [o for o in occs if o.get('ref')]
    if refs:
        r = refs[0]; rs = shape(r['ink']); rh = r['bottom'] - r['top']
        occs = [o for o in occs if o.get('ref') or
                (float(np.sqrt(((shape(o['ink']) - rs) ** 2).mean())) < 0.3
                 and abs(o['bottom'] - o['top'] - rh) < 0.25 * rh + 2)]
    if len(occs) < 3: return occs
    w = np.median([o['w'] for o in occs]); h = np.median([o['bottom'] - o['top'] for o in occs])
    occs = [o for o in occs if abs(o['w'] - w) < 0.25 * w + 2 and abs(o['bottom'] - o['top'] - h) < 0.25 * h + 2] or occs
    if len(occs) < 3: return occs
    sh = np.array([shape(o['ink']) for o in occs]); med = np.median(sh, 0)
    d = np.sqrt(((sh - med) ** 2).mean(1)); cut = np.median(d) * 2.5 + 0.02
    return [o for o, x in zip(occs, d) if x <= cut] or occs


def register(occs, k):
    """shift each occurrence to fit the character's alphabet-line print (sharper to align to than a blurred
    mean): by phase correlation of the two, placed in font units, on a common canvas"""
    from glyphs import place
    import cv2
    refs = [o for o in occs if o.get('ref')]
    if not refs or len(occs) < 2: return occs
    r = place(refs[0], k)
    out = []
    for o in occs:
        if o is refs[0]: out.append(o); continue
        im = place(o, k)
        x0 = min(r.x0, im.x0); top = max(r.top, im.top)
        W = int(max(r.x0 + r.ink.shape[1], im.x0 + im.ink.shape[1]) - x0) + 40
        H = int(top - min(r.top - r.ink.shape[0], im.top - im.ink.shape[0])) + 40
        def put(a):
            M = np.float32([[1, 0, a.x0 - x0 + 20], [0, 1, top - a.top + 20]])
            return cv2.warpAffine(a.ink, M, (W, H), flags=cv2.INTER_LINEAR)
        (dx, dy), resp = cv2.phaseCorrelate(put(im), put(r), cv2.createHanningWindow((W, H), cv2.CV_32F))
        if abs(dx) > 0.25 * W or abs(dy) > 0.25 * H: out.append(o); continue
        # move the occurrence by (dx, dy) font units: X0 and Y0 are in scan pixels, y down
        out.append(dict(o, X0=o['X0'] + dx / k, Y0=o['Y0'] + dy / k))
    return out


def build(face):
    data = pickle.load(open(os.path.join(BUILD, f'occ-{face}.pkl'), 'rb'))
    p = float(np.median([q for q, _ in data['pitches']])); pitch = data['pitches'][0][1]
    k = ADV / p                                   # font units per scan pixel
    by = {}
    for o in data['occ']: by.setdefault(o['ch'], []).append(o)
    glyphs, adv, counts = {}, {}, {}
    for ch, occs in by.items():
        occs = register(clean(occs), k); counts[ch] = len(occs)
        im = average(occs, k)
        segs = trace.trace(im.ink, SIGMA * k)
        glyphs[gname(ch)] = [[(s[0],) + tuple((q[0] + im.x0 + ADV / 2, q[1] + im.top) for q in s[1:]) for s in c]
                             for c in segs]
        adv[gname(ch)] = ADV
    glyphs['space'] = []; adv['space'] = ADV
    glyphs['.notdef'] = [[('L', (100, 0), (100, 600)), ('L', (100, 600), (500, 600)), ('L', (500, 600), (500, 0)),
                          ('L', (500, 0), (100, 0))]]
    adv['.notdef'] = ADV
    cmap = {ord(ch): gname(ch) for ch in by}
    if face in CAPS_ONLY:
        for c in S.LC: cmap[ord(c)] = gname(c.upper())
    cmap[0x20] = 'space'
    for u, ch in ALIAS.items():
        if ch == ' ' or ch in by: cmap[u] = 'space' if ch == ' ' else gname(ch)
    def top_of(n):
        bp = BoundsPen(None); draw(bp, glyphs[n]); return bp.bounds[3] if bp.bounds else 0
    xh = top_of('x') if 'x' in glyphs and face not in CAPS_ONLY else top_of('X') * 0.7
    cap = top_of('H')
    rare = {c: n for c, n in counts.items() if n < 2}
    print(f'{face}: {len(by)} characters, pitch {p:.2f} px (1/{pitch} inch); cap height {cap:.0f};'
          f' seen once: {"".join(sorted(rare))}')
    return glyphs, adv, cmap, dict(pitch=pitch, cap=cap, xh=xh, counts=counts)


def font(face, otf=True, data=None):
    glyphs, adv, cmap, info = data or build(face)
    family = 'Sel ' + NAMES[face]; style = 'Italic' if face in ITALIC else 'Regular'
    psname = 'Sel' + face + '-' + style
    VERSION = VERSIONS[face]
    order = ['.notdef', 'space'] + sorted(n for n in glyphs if n not in ('.notdef', 'space'))
    fb = FontBuilder(UPM, isTTF=not otf)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    if otf:
        cs = {}
        for n in order:
            pen = T2CharStringPen(adv[n], None); draw(ReverseContourPen(pen), glyphs[n]); cs[n] = pen.getCharString()
        fb.setupCFF(psname, {'FullName': f'{family} {style}' if style != 'Regular' else family, 'FamilyName': family,
                             'Weight': 'Regular', 'isFixedPitch': True}, cs, {})
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
    # single spacing, six lines to the inch: 12 pt, which is 1000 units at 12 pt (10 pitch) or 1200 at 10 pt
    line = 1000 if info['pitch'] == 10 else 1200
    desc = int(np.floor(lmin)); asc = line + desc
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    full = family if style == 'Regular' else f'{family} {style}'
    fb.setupNameTable({
        'familyName': family, 'styleName': style,
        'uniqueFontIdentifier': f'{psname};{VERSION}', 'fullName': full,
        'psName': psname, 'version': f'Version {VERSION}',
        'copyright': 'Traced from IBM Selectric typewriter type style brochures (1970s).',
        'description': f'A revival of the IBM Selectric typewriter face {NAMES[face]} ({info["pitch"]} pitch), '
                       f'traced from its specimens.',
    })
    italic = style == 'Italic'
    from fontTools.ttLib.tables.O_S_2f_2 import Panose
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, sTypoLineGap=0,
                usWinAscent=int(np.ceil(max(ymax, asc))), usWinDescent=int(np.ceil(max(-ymin, -desc))),
                sxHeight=int(round(info['xh'])), sCapHeight=int(round(info['cap'])), usWeightClass=400,
                achVendID='NONE', fsType=0, fsSelection=(0x01 if italic else 0x40) | 0x80, version=4,
                panose=dict(bFamilyType=2, bSerifStyle=0, bWeight=0, bProportion=9, bContrast=0,   # monospaced
                            bStrokeVariation=0, bArmStyle=0, bLetterForm=0, bMidline=0, bXHeight=0))
    fb.setupPost(isFixedPitch=1, italicAngle=ITALIC.get(face, 0))
    if italic: fb.font['head'].macStyle = 2
    fb.font['head'].fontRevision = float(VERSION)
    d = os.path.join(ROOT, 'fonts', 'otf' if otf else 'ttf')
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f'{psname}.{"otf" if otf else "ttf"}')
    fb.save(path)
    if not otf: autohint(path)
    print('  wrote', os.path.relpath(path, ROOT), len(order), 'glyphs')


if __name__ == '__main__':
    p = os.path.join(BUILD, 'fonts.json')
    infos = json.load(open(p)) if os.path.exists(p) else {}
    for face in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        data = build(face)
        font(face, True, data); font(face, False, data)
        infos[face] = dict(pitch=data[3]['pitch'], cap=data[3]['cap'])
    json.dump(infos, open(p, 'w'), indent=1)

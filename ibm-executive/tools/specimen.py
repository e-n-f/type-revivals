"""Specimen images in specimen/: the fonts set in lines, and each face beside its scan.

    python3 tools/specimen.py

compare-<Face>.png shows a stretch of the scan above the same words set in the font at the scan's scale, each
word started where the scan has it (the Jowa card's text is justified foundry type, so its spaces vary).
"""
import os, sys, json, pickle, numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
import read as R
from build import VERSIONS, NAMES, PER_INCH
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'specimen')
LABEL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def fontpath(face): return os.path.join(ROOT, 'fonts', 'otf', f'Exec{face}-Regular.otf')

TEXT = ['Dear Sir: We acknowledge with thanks your letter of June 4, 1952,',
        'and enclose our cheque for $1,284.50 (net 30 days) as agreed.']
SETS = ['abcdefghijklmnopqrstuvwxyz ß', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', '1234567890 & .,:;-!?\'"()/*+%$£§@#¢_',
        'àáâãäåçèéêëìíîïñòóôõöøùúûüýÿ ÀÁÂÄÅÇÉÑÖØÜ']

def lines():
    size = 64; W = 2400
    lab = ImageFont.truetype(LABEL, 26)
    rows = []
    for face in VERSIONS:
        f = ImageFont.truetype(fontpath(face), size)
        info = json.load(open(os.path.join(R.BUILD, 'fonts.json')))[face]
        rows.append(('label', f'Exec {NAMES[face]}  (1/{info["esc"]} inch units)', lab))
        cmap = TTFont(fontpath(face)).getBestCmap()
        for t in SETS + TEXT:     # leave out what the face doesn't have
            rows.append(('text', ''.join(c for c in t if c == ' ' or ord(c) in cmap), f))
    H = sum(48 if r[0] == 'label' else int(size * 1.3) for r in rows) + 60
    im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im); y = 30
    for r in rows:
        if r[0] == 'label':
            y += 16; d.text((40, y), r[1], font=r[2], fill=110); y += 32
        else:
            d.text((40, y), r[1], font=r[2], fill=0); y += int(size * 1.3)
    im.save(os.path.join(OUT, 'specimen-lines.png'))

# which lines of each source to show: (source, line ids, display scale)
COMPARE = {'Modern': ('Modern', [0, 1, 2, 3, 4, 5, 6, 7], 0.3)}
for _f in VERSIONS:
    if _f != 'Modern': COMPARE[_f] = (_f, list(range(12)), 1.0)

def compare(face):
    src, lids, scale = COMPARE[face]
    res = pickle.load(open(os.path.join(R.BUILD, f'occ-{src}.pkl'), 'rb'))
    u = json.load(open(os.path.join(R.BUILD, f'units-{src}.json')))
    occ = [o for _, oc in res if oc for o in oc if o['line'] in lids]
    scans = sorted(set(o['scan'] for o in occ))
    panels = []
    size = 1000 * u['pitch'] / (PER_INCH / u['escapement'])     # px per em on the scan
    font = ImageFont.truetype(fontpath(face), max(4, int(round(size))))
    texts = {}
    for t, oc in res:
        if oc: texts[oc[0]['line']] = t
    for scan in scans:
        os_ = [o for o in occ if o['scan'] == scan]
        X = lambda o: o['x0'] + o['off'][0]; Y = lambda o, v: v + o['off'][1]
        x0 = int(min(X(o) for o in os_)) - 30; x1 = int(max(o['x1'] + o['off'][0] for o in os_)) + 30
        y0 = int(min(Y(o, o['top']) for o in os_)) - 30; y1 = int(max(Y(o, o['bottom']) for o in os_)) + 30
        g = R.gray(scan)[y0:y1, x0:x1]
        top = Image.fromarray((np.clip(g / max(np.median(g), 0.3), 0, 1) * 255).astype(np.uint8))
        bot = Image.new('L', top.size, 255); d = ImageDraw.Draw(bot)
        words = {}
        for o in os_: words.setdefault(o['word'], []).append(o)
        for (lid, wi), ws in words.items():
            first = min(ws, key=lambda o: o['idx'])
            text = texts[lid].split()[wi][first['idx']:]
            ink_left = font.getbbox(text[0], anchor='ls')[0]
            d.text((X(first) - x0 - ink_left, Y(first, first['base']) - y0), text, font=font, fill=0, anchor='ls')
        panels += [('scan', top), ('font', bot)]
    lab = ImageFont.truetype(LABEL, 22)
    ims = [p.resize((int(p.width * scale), int(p.height * scale)), Image.LANCZOS) for _, p in panels]
    W = max(i.width for i in ims) + 20; H = sum(i.height + 40 for i in ims) + 10
    out = Image.new('L', (W, H), 255); d = ImageDraw.Draw(out); y = 10
    for (kind, _), im in zip(panels, ims):
        d.text((10, y), f'{kind}: {"the scan" if kind == "scan" else f"Exec {NAMES[face]}, set at the scan’s size"}',
               font=lab, fill=110)
        out.paste(im, (10, y + 30)); y += im.height + 40
    out.save(os.path.join(OUT, f'compare-{face}.png'))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    lines()
    for face in [a for a in sys.argv[1:] if a in VERSIONS] or VERSIONS:
        compare(face)

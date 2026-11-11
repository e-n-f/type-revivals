"""Specimen images in specimen/: the fonts set in lines, and each style beside its scan.

    python3 tools/specimen.py
"""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from sheets import SHEETS
ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'specimen')
STYLES = ['Regular', 'Italic', 'Bold']
LABEL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CARDS = {'Regular': 'St. 2 (Palatino)', 'Italic': 'St. 43 (Palatino-Kursiv)', 'Bold': 'St. 44 (Halbfette Palatino)'}

def fontpath(st): return os.path.join(ROOT, 'fonts', 'otf', f'MetalPal-{st}.otf')

TEXT = ['Von den vielen Welten, die der Mensch nicht von der Natur geschenkt',
        'bekam, sondern sich aus dem eigenen Geist erschaffen hat, ist die Welt',
        'der Bücher die größte. Jedes Kind, wenn es die ersten Buchstaben auf',
        'seine Schultafel malt und die ersten Leseversuche macht, tut damit den']
SETS = {
    'Regular': ['abcdefghijklmnopqrstuvwxyz äöü ß', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ ÄÖÜ',
                '1234567890 & .·,:;-–—!?’„“»«/()[]§†*¶', 'fi fl ff ft Qu   ch ck tz (dlig)'],
    'Italic': ['abcdefghijklmnopqrstuvwxyz äöü ß', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ ÄÖÜ',
               '1234567890 & .·,:;-–—!?’„“»«/()[]§†*¶', 'fi fl ff ft Qu   ch ck tt tz (dlig)'],
    'Bold': ['abcdefghijklmnopqrstuvwxyz äöü ß', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ ÄÖÜ',
             '1234567890 & .·,:;-–—!?’„“»«/()[]§†*', 'fi fl ff ft   ch ck tt tz (dlig)'],
}

def lines():
    W, size = 2400, 64
    lab = ImageFont.truetype(LABEL, 26)
    rows = []
    for st in STYLES:
        f = ImageFont.truetype(fontpath(st), size)
        rows.append(('label', f'Metal Pal {st}', lab))
        for i, t in enumerate(SETS[st]):
            feats = ['liga', 'dlig'] if i == 3 else ['liga']
            rows.append(('text', t, f, feats))
        if st == 'Italic':
            rows.append(('text', 'ABDEJMNRSTZ Th  (swsh)   e k z  (ss01)', f, ['swsh', 'ss01', 'dlig']))
        rows.append(('text', '1234567890  (lnum)', f, ['lnum']))
        for t in TEXT[:2]: rows.append(('text', t, f, ['liga']))
    H = sum(44 if r[0] == 'label' else int(size * 1.35) for r in rows) + 60
    im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im); y = 30
    for r in rows:
        if r[0] == 'label':
            y += 14; d.text((40, y), r[1], font=r[2], fill=110); y += 30
        else:
            d.text((40, y), r[1], font=r[2], fill=0, features=r[3]); y += int(size * 1.35)
    im.save(os.path.join(OUT, 'specimen-lines.png'))

def compare(st):
    """the scan's character sheet above the same characters in the font, at the same size"""
    from extract import analyse, CAP
    from segment import load
    S = SHEETS[st]; g = load(os.path.join(ROOT, 'scans', S['scan']))
    x0, y0, x1, y1 = S['boxes'][0][0], S['boxes'][0][1], 9500, S['boxes'][1][3]
    crop = Image.fromarray((g[y0:y1, x0:x1] * 255).astype(np.uint8))
    _, boxes = analyse(st)
    G = S['glyphs']; Hb = boxes[1]
    # cap height on the scan, px
    capref = [Hb['bboxes'][int(G[c][0].split('.')[1])] for c in 'HE']
    cap_px = np.median([q[3] - q[1] for q in capref])
    size = cap_px / CAP * 1000
    f = ImageFont.truetype(fontpath(st), int(round(size)))
    ren = Image.new('L', crop.size, 255); d = ImageDraw.Draw(ren)
    a0, b0 = boxes[0]['base']; a1, b1 = boxes[1]['base']
    t0 = 'abcdefghijklmnopqrstuvwxyz'; t1 = ''.join(c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if G.get(c, ['x'])[0].startswith('1.'))
    asc = f.getmetrics()[0]
    for t, a, b, bi in ((t0, a0, b0, 0), (t1, a1, b1, 1)):
        first = boxes[bi]['bboxes'][0][0]
        d.text((first - x0, a + b * first - y0), t, font=f, fill=0, anchor='ls')
    w = 2400; s = w / crop.width; h = int(crop.height * s)
    lab = ImageFont.truetype(LABEL, 30); L = 56
    both = Image.new('L', (w, 2 * (L + h) + 24), 255); d = ImageDraw.Draw(both)
    d.text((10, 12), f'SCAN  ·  Stempel specimen card {CARDS[st]}, type list (Drucktypenverzeichnis)',
           font=lab, fill=90)
    both.paste(crop.resize((w, h), Image.LANCZOS), (0, L))
    y = L + h + 12
    d.line((0, y, w, y), fill=170, width=2)
    d.text((10, y + 12), f'RENDERED  ·  the alphabets set in Metal Pal {st}, at the same cap height and baseline'
           ' (the card letterspaces its capitals; the font does not)', font=lab, fill=90)
    both.paste(ren.resize((w, h), Image.LANCZOS), (0, y + L))
    both.save(os.path.join(OUT, f'compare-{st}.png'))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    lines()
    for st in STYLES: compare(st)

"""Specimen images in specimen/.

    python3 tools/specimen.py [athens]

compare-<font>.png: every character of the font set over its bitmap (pink, at three times its pixels), with the
bitmap's advance width underlined in blue, so that the outlines can be checked against the pixels they recreate.
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import bitmap
from build import VERSIONS, NAMES, PX, CODES, MOVED, ALSO

LABEL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def compare(font):
    strike, metrics = bitmap.strike(font)
    S = 3                                                   # specimen pixels per bitmap pixel
    path = os.path.join(ROOT, 'fonts', 'otf', NAMES[font].replace(' ', '') + '-Regular.otf')
    from fontTools.ttLib import TTFont
    em = TTFont(path)['head'].unitsPerEm / PX              # the font's em, in bitmap pixels (18 for Athens 18)
    F = ImageFont.truetype(path, int(round(em * S)))
    chars = [g['char'] for g in json.load(open(os.path.join(ROOT, 'scans', f'{font}-glyphs.json')))['glyphs']]
    cols, cw = 14, max(strike[c]['adv'] for c in chars if c in strike) * S + 20
    ch = (metrics['ascender'] - metrics['descender']) * S + 30
    im = Image.new('RGB', (cols * cw + 20, ((len(chars) + cols - 1) // cols) * ch + 50), 'white')
    d = ImageDraw.Draw(im)
    d.text((10, 10), f'{NAMES[font]} over its bitmap (pink); the advance in blue', font=ImageFont.truetype(LABEL, 18),
           fill=(90, 90, 90))
    # the characters the sheet names by control code: the bitmap keeps them in Mac OS Roman places of their own
    moved = dict(zip(CODES.get(font, {}), MOVED.get(font, '')))
    for i, c in enumerate(chars):
        x0 = (i % cols) * cw + 15; base = 50 + (i // cols) * ch + metrics['ascender'] * S
        b = moved.get(c, c)
        if b not in strike: b = next(chr(cp) for cp in ALSO.get(c, []) if chr(cp) in strike)   # Ω at U+2126
        g = strike[b]
        if c in CODES.get(font, {}): c = chr(CODES[font][c])
        for yy in range(g['h']):
            for xx in range(g['w']):
                if g['bits'][yy][xx]:
                    d.rectangle([x0 + (g['x'] + xx) * S, base - (g['y'] - yy) * S,
                                 x0 + (g['x'] + xx + 1) * S - 1, base - (g['y'] - yy - 1) * S - 1], fill=(255, 170, 170))
        d.text((x0, base), c, font=F, fill=(0, 0, 0), anchor='ls')
        d.line([(x0, base + 4), (x0 + g['adv'] * S, base + 4)], fill=(0, 120, 255), width=2)
    os.makedirs(os.path.join(ROOT, 'specimen'), exist_ok=True)
    im.save(os.path.join(ROOT, 'specimen', f'compare-{font}.png'), optimize=True)


if __name__ == '__main__':
    for f in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        compare(f)

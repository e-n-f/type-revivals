"""Specimen images in specimen/.

    python3 tools/specimen.py [athens] [path/to/Apple's/New York.ttf]

compare-<font>.png: every character of the font set over its bitmap (pink, at three times its pixels), with the
bitmap's advance width underlined in blue, so that the outlines can be checked against the pixels they recreate.
"""
import os, sys, json
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import bitmap
from build import VERSIONS, NAMES, PX, CODES, MOVED, ALSO, SOURCE

LABEL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def compare(font):
    strike, metrics = bitmap.strike(SOURCE.get(font, font))
    S = 3                                                   # specimen pixels per bitmap pixel
    path = os.path.join(ROOT, 'fonts', 'otf', NAMES[font].replace(' ', '') + '-Regular.otf')
    from fontTools.ttLib import TTFont
    em = TTFont(path)['head'].unitsPerEm / PX              # the font's em, in bitmap pixels (18 for Athens 18)
    F = ImageFont.truetype(path, int(round(em * S)))
    chars = [g['char'] for g in json.load(open(os.path.join(ROOT, 'scans', f'{SOURCE.get(font, font)}-glyphs.json')))['glyphs']]
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


def weights():
    """newyork-weights.png: New York 12 HD and 24 HD and their Mid fonts, set at one size"""
    names = [n for k, n in NAMES.items() if k.startswith('newyork')]
    order = ['New York 12 HD', 'New York 12 Mid HD', 'New York 24 Mid HD', 'New York 24 HD']
    text = 'Hamburgefonstiv, The quick brown fox jumps over the lazy dog. 0123456789'
    L = ImageFont.truetype(LABEL, 18)
    im = Image.new('RGB', (1900, 70 + 3 * 100 * len(order)), 'white'); d = ImageDraw.Draw(im)
    d.text((10, 10), 'New York 12 HD and 24 HD, and the Mid fonts at the weight halfway between, at 24, 36 and 72 px',
           font=L, fill=(90, 90, 90))
    y = 50
    for n in order:
        path = os.path.join(ROOT, 'fonts', 'otf', n.replace(' ', '') + '-Regular.otf')
        d.text((10, y), n, font=L, fill=(90, 90, 90)); y += 26
        for size in (24, 36, 72):
            d.text((10, y + size), text, font=ImageFont.truetype(path, size), fill=(0, 0, 0), anchor='ls')
            y += int(size * 1.25)
        y += 20
    im = im.crop((0, 0, im.width, y))
    im.save(os.path.join(ROOT, 'specimen', 'newyork-weights.png'), optimize=True)


def blend(size=144, official=None):
    """newyork-alphabets.png: the alphabets and figures on one line, in New York 12's bitmap, New York 12 HD,
    New York 12 Blend HD, New York 24 HD and New York 24's bitmap, all at one size; and, given the path of Apple's
    TrueType New York (not in this repository), in that too"""
    text = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789'
    L = ImageFont.truetype(LABEL, 28)
    rows = [('newyork12', 'New York 12 bitmap'), ('New York 12 HD', None), ('New York 12 Blend HD', None),
            ('New York 24 HD', None), ('newyork24', 'New York 24 bitmap')]
    if official: rows.append((official, 'New York (Apple TrueType, 1991), at the size that sets the line as wide as New York 12 HD'))
    gap = int(size * 1.45) + 30
    im = Image.new('RGB', (60 * size, len(rows) * gap + 20), 'white'); d = ImageDraw.Draw(im)
    right = 0
    for i, (f, label) in enumerate(rows):
        top = 10 + i * gap; base = top + 36 + size
        d.text((10, top), label or f, font=L, fill=(90, 90, 90))
        if label and f == official:     # at the size that sets the line as wide as New York 12 HD does
            F12 = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'otf', 'NewYork12HD-Regular.otf'), size)
            F = ImageFont.truetype(f, size * d.textlength(text, font=F12) / d.textlength(text, font=ImageFont.truetype(f, size)))
            d.text((10, base), text, font=F, fill=(0, 0, 0), anchor='ls'); x = 10 + d.textlength(text, font=F)
        elif label:                                         # a bitmap, each pixel a square size/ppem across
            strike, metrics = bitmap.strike(f); x = 10.0
            hd = os.path.join(ROOT, 'fonts', 'otf', NAMES[f].replace(' ', '') + '-Regular.otf')
            s = size * PX / TTFont(hd)['head'].unitsPerEm      # the HD font's em is unitsPerEm/PX of its pixels
            for c in text:
                g = strike[c]
                for yy in range(g['h']):
                    for xx in range(g['w']):
                        if g['bits'][yy][xx]:
                            d.rectangle([round(x + (g['x'] + xx) * s), round(base - (g['y'] - yy) * s),
                                         round(x + (g['x'] + xx + 1) * s) - 1, round(base - (g['y'] - yy - 1) * s) - 1],
                                        fill=(0, 0, 0))
                x += g['adv'] * s
        else:
            F = ImageFont.truetype(os.path.join(ROOT, 'fonts', 'otf', f.replace(' ', '') + '-Regular.otf'), size)
            d.text((10, base), text, font=F, fill=(0, 0, 0), anchor='ls'); x = 10 + d.textlength(text, font=F)
        right = max(right, x)
    im = im.crop((0, 0, int(right) + 20, im.height))
    im.save(os.path.join(ROOT, 'specimen', 'newyork-alphabets.png'), optimize=True)


if __name__ == '__main__':
    official = next((a for a in sys.argv[1:] if a.lower().endswith('.ttf')), None)
    for f in [a for a in sys.argv[1:] if a in VERSIONS] or list(VERSIONS):
        compare(f)
    weights()
    blend(official=official)

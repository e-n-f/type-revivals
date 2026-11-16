"""Specimen images in specimen/.

    python3 tools/specimen.py

specimen-lines.png: every face in a line of text, its alphabets and signs.  ascii.png: every face's printable
ASCII (0x21-0x7E) in code order, a character the face lacks as an empty box.
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from build import VERSIONS, NAMES, ITALIC
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'specimen')
LABEL = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def fontpath(face):
    return os.path.join(ROOT, 'fonts', 'otf', f'Selectric{face}-{"Italic" if face in ITALIC else "Regular"}.otf')

TEXT = 'The quick brown fox jumps over the lazy dog. 1234567890'
SIGNS = '!@#$%¢&*()-_=+½¼?/"\':;,.'
info = json.load(open(os.path.join(ROOT, 'build', 'fonts.json')))

def size(face, base):
    """the same size on paper: a 12-pitch face is set 10/12 the size of a 10-pitch one"""
    return int(round(base * (1 if info[face]['pitch'] == 10 else 10 / 12)))

def lines():
    W, base = 2400, 60
    lab = ImageFont.truetype(LABEL, 24)
    rows = []
    for face in VERSIONS:
        f = ImageFont.truetype(fontpath(face), size(face, base))
        rows.append(('label', f'Selectric {NAMES[face]}  ({info[face]["pitch"]} pitch)', lab))
        rows.append(('text', TEXT, f))
        rows.append(('text', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz', f))
        rows.append(('text', SIGNS, f))
    H = sum(38 if r[0] == 'label' else int(base * 1.25) for r in rows) + 40
    im = Image.new('L', (W, H), 255); d = ImageDraw.Draw(im); y = 20
    for r in rows:
        if r[0] == 'label': y += 10; d.text((40, y), r[1], font=r[2], fill=110); y += 28
        else: d.text((40, y), r[1], font=r[2], fill=0); y += int(base * 1.25)
    im.save(os.path.join(OUT, 'specimen-lines.png'))

def ascii_chart():
    chars = [chr(c) for c in range(0x21, 0x7F)]
    rows = [chars[:31], chars[31:63], chars[63:]]
    cw, ch, base = 72, 96, 64
    lab = ImageFont.truetype(LABEL, 24); small = ImageFont.truetype(LABEL, 13)
    W = 40 + 32 * cw + 20; block = 40 + 3 * ch + 24
    im = Image.new('L', (W, 30 + block * len(VERSIONS)), 255); d = ImageDraw.Draw(im); y = 30
    for face in VERSIONS:
        f = ImageFont.truetype(fontpath(face), size(face, base))
        cmap = TTFont(fontpath(face)).getBestCmap()
        have = sum(ord(c) in cmap for c in chars)
        d.text((40, y), f'Selectric {NAMES[face]}  ({have} of {len(chars)})', font=lab, fill=90); y += 40
        for r, row in enumerate(rows):
            for i, c in enumerate(row):
                x = 40 + (i + (1 if r == 0 else 0)) * cw; top = y + r * ch
                d.text((x + 3, top), f'{ord(c):02X}', font=small, fill=150)
                if ord(c) in cmap: d.text((x + cw / 2, top + ch - 22), c, font=f, fill=0, anchor='ms')
                else: d.rectangle((x + 14, top + 22, x + cw - 14, top + ch - 14), outline=170, width=2)
        y += 3 * ch + 24
    im.save(os.path.join(OUT, 'ascii.png'))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    lines(); ascii_chart()

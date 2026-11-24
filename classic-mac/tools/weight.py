"""Each HD font's ink against its bitmap's.

    python3 tools/weight.py [athens]

Over A-Z, a-z and 0-9, the ink of the HD font (its outlines' area) and of the bitmap (its pixels'), and how many
font units a side the HD font's strokes would have to be thickened (or, negative, thinned) by to carry the
bitmap's ink: the difference of the two areas over the outlines' length.
"""
import os, sys
import numpy as np, cv2
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import bitmap, build

TEXT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
K = 20                                      # rendering pixels per bitmap pixel


def weight(font):
    """(HD ink / bitmap ink, font units a side to the bitmap's ink)"""
    strike, _ = bitmap.strike(getattr(build, 'SOURCE', {}).get(font, font))
    path = os.path.join(ROOT, 'fonts', 'otf', build.NAMES[font].replace(' ', '') + '-Regular.otf')
    em = TTFont(path)['head'].unitsPerEm / build.PX           # the em, in bitmap pixels
    F = ImageFont.truetype(path, em * K)
    bits = ink = edge = 0
    for c in TEXT:
        bits += strike[c]['bits'].sum() * K * K
        im = Image.new('L', (int(em * K * 3), int(em * K * 3)), 0)
        ImageDraw.Draw(im).text((em * K, 2 * em * K), c, font=F, fill=255, anchor='ls')
        a = np.asarray(im, np.float32) / 255; ink += a.sum()
        cs, _ = cv2.findContours((a > 0.5).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        edge += sum(cv2.arcLength(x, True) for x in cs)
    return ink / bits, (bits - ink) / edge * build.PX / K


if __name__ == '__main__':
    for f in [a for a in sys.argv[1:] if a in build.VERSIONS] or list(build.VERSIONS):
        r, d = weight(f)
        print(f'{build.NAMES[f]:22s} LIGHTEN {build.LIGHTEN[f]:3g}   ink {r:6.1%} of the bitmap\'s   '
              f'{d:+.1f} units a side to match')

#!/usr/bin/env python3
"""Download links and one-line specimens for every font, in each family's README and in the top-level README.

    python3 scripts/font_links.py

A family is a directory with fonts/otf/*.otf. For each font this draws <family>/specimen/fonts/<file>.png, the
alphabets and figures set in it, and lists the font with links to its OTF and TTF files on GitHub (raw, so that
they download). The lists go between the markers <!-- downloads --> and <!-- /downloads -->, which are added
the first time: before a family README's first section, and before the top-level README's last paragraph.
Fonts are listed in the order their family's README first names their files, then any others by name.
"""
import glob, os, re, sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = 'https://raw.githubusercontent.com/e-n-f/type-revivals/main'
TEXT = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789'
SIZE = 40                                  # px per em of the specimen lines
BEGIN, END = '<!-- downloads -->', '<!-- /downloads -->'


def families():
    """the font directories, in the order the top-level README names them"""
    top = open(os.path.join(ROOT, 'README.md')).read()
    fams = [d for d in os.listdir(ROOT) if glob.glob(os.path.join(ROOT, d, 'fonts', 'otf', '*.otf'))]
    return sorted(fams, key=lambda d: (top.find(f'{d}/') if f'{d}/' in top else len(top), d))


def fonts(family):
    """[(full name, file stem)] in the order the family's README names them"""
    readme = open(os.path.join(ROOT, family, 'README.md')).read()
    out = []
    for p in glob.glob(os.path.join(ROOT, family, 'fonts', 'otf', '*.otf')):
        stem = os.path.splitext(os.path.basename(p))[0]
        name = TTFont(p)['name'].getDebugName(4) or stem
        at = readme.find(stem)
        out.append((at if at >= 0 else len(readme), stem, name))
    return [(name, stem) for _, stem, name in sorted(out)]


def specimen(family, stem):
    """the font's one-line specimen, drawn if it is missing or older than the font; its path in the family"""
    font = os.path.join(ROOT, family, 'fonts', 'otf', stem + '.otf')
    rel = os.path.join('specimen', 'fonts', stem + '.png')
    path = os.path.join(ROOT, family, rel)
    if os.path.exists(path) and os.path.getmtime(path) >= os.path.getmtime(font): return rel
    f = ImageFont.truetype(font, SIZE)
    l, t, r, b = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), TEXT, font=f)
    im = Image.new('L', (r - l + 16, b - t + 16), 255)
    ImageDraw.Draw(im).text((8 - l, 8 - t), TEXT, font=f, fill=0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)
    return rel


def entries(family, prefix=''):
    lines = []
    for name, stem in fonts(family):
        img = specimen(family, stem)
        lines.append(f'**{name}**: [OTF]({RAW}/{family}/fonts/otf/{stem}.otf) · '
                     f'[TTF]({RAW}/{family}/fonts/ttf/{stem}.ttf)  ')
        lines.append(f'![{name}]({prefix}{img})')
        lines.append('')
    return lines


def put(path, block, before):
    """the block between the markers in the README at path: replacing what is there, or inserted before the first
    line that `before` matches (at the end if none does)"""
    text = open(path).read()
    block = '\n'.join([BEGIN] + block + [END])
    if BEGIN in text:
        text = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), lambda m: block, text, flags=re.S)
    else:
        lines = text.split('\n')
        at = next((i for i, l in enumerate(lines) if before(l)), len(lines))
        lines[at:at] = [block, '']
        text = '\n'.join(lines)
    open(path, 'w').write(text)


def main():
    top = []
    for fam in families():
        put(os.path.join(ROOT, fam, 'README.md'), ['## Download', ''] + entries(fam), lambda l: l.startswith('## '))
        title = open(os.path.join(ROOT, fam, 'README.md')).readline().lstrip('# ').strip()
        top += [f'### {title}', ''] + entries(fam, prefix=f'{fam}/')
    put(os.path.join(ROOT, 'README.md'), ['## Download', ''] + top, lambda l: l.startswith('Every change'))
    print('downloads listed for', ', '.join(families()))


if __name__ == '__main__':
    main()

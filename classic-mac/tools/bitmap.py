"""The bitmap fonts the recreations match: each character's pixels and metrics, read from its .dfont.

The OS X .dfont versions of the classic Mac bitmap fonts hold an 'sfnt' resource with Apple's bitmap-only tables
(bhed, bloc, bdat: one strike of 1-bit glyphs). Their 'maxp' table carries 26 stray bytes after its 6, which
fontTools rejects, so it is cut to its 6 bytes before the font is read.
"""
import io, os
import numpy as np
from fontTools.misc.macRes import ResourceReader
from fontTools.ttLib import TTFont
from fontTools.ttLib.sfnt import SFNTReader, SFNTWriter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DFONT = {'athens': 'Athens_22.dfont', 'chicago': 'Chicago_15.dfont', 'geneva': 'Geneva_15.dfont',
         'monaco': 'Monaco_15.dfont'}


def sfnt(font):
    """the font's sfnt resource as a TTFont"""
    data = ResourceReader(os.path.join(ROOT, 'scans', DFONT[font]))['sfnt'][0].data
    r = SFNTReader(io.BytesIO(data))
    tables = {t: r[t] for t in r.tables}
    tables['maxp'] = tables['maxp'][:6]                 # version 0.5: numGlyphs only
    buf = io.BytesIO(); w = SFNTWriter(buf, len(tables), sfntVersion=r.sfntVersion)
    for t, v in tables.items(): w[t] = v
    w.close(); buf.seek(0)
    return TTFont(buf)


def strike(font):
    """{char: dict(bits: rows of 0/1, top row first; x: left, y: top above the baseline; w, h; adv)} in pixels,
    and the strike's ppem, ascender and descender"""
    f = sfnt(font)
    cmap = f.getBestCmap()
    st = f['bloc'].strikes[0].bitmapSizeTable
    out = {}
    data = f['bdat'].strikeData[0]
    # a monospaced strike (Monaco's) keeps one set of metrics for all its glyphs in the index, not in each glyph
    shared = {n: sub.metrics for sub in f['bloc'].strikes[0].indexSubTables if hasattr(sub, 'metrics')
              for n in sub.names}
    for cp, name in sorted(cmap.items()):
        if cp < 0x20 or name not in data: continue
        b = data[name]; b.decompile()
        m = b.metrics if 'metrics' in b.__dict__ else shared[name]
        bits = np.zeros((m.height, m.width), np.uint8)
        for y in range(m.height):
            row = b.getRow(y, bitDepth=1, metrics=m)
            for x in range(m.width): bits[y, x] = (row[x // 8] >> (7 - x % 8)) & 1
        x, y, adv = ((m.BearingX, m.BearingY, m.Advance) if hasattr(m, 'BearingX')        # small metrics
                     else (m.horiBearingX, m.horiBearingY, m.horiAdvance))              # big metrics
        out[chr(cp)] = dict(bits=bits, x=x, y=y, w=m.width, h=m.height, adv=adv, name=name)
    return out, dict(ppem=st.ppemY, ascender=st.hori.ascender, descender=st.hori.descender)

"""Where every glyph is on the specimen sheets.

Groups are numbered by segment.group() within each box, left to right
(see `python3 tools/extract.py contact`).  A glyph is a list of "box.index"
references whose components are merged.
"""
LC = 'abcdefghijklmnopqrstuvwxyz'
UC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
FIG = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']
ACC = ['aacute', 'agrave', 'acircumflex', 'eacute', 'egrave', 'ecircumflex', 'edieresis',
       'iacute', 'igrave', 'icircumflex', 'idieresis', 'oacute', 'ograve', 'ocircumflex',
       'uacute', 'ugrave', 'ucircumflex', 'ccedilla', 'ae', 'oe',
       'Eacute', 'Egrave', 'Ecircumflex', 'Edieresis', 'Ccedilla', 'AE', 'OE']

def seq(names, box, start=0):
    return {n: [f'{box}.{start + i}'] for i, n in enumerate(names)}

def lcnames(): return list(LC)
def ucnames(s): return list(s)

# ---------------------------------------------------------------- Regular, St. 2
REGULAR = dict(
    scan='53152153329_ccac30d200_o.jpg',
    boxes=[(300, 2250, 9500, 2860), (300, 2860, 9500, 3420), (300, 3420, 9500, 4020),
           (300, 4020, 5500, 4540), (300, 4660, 5600, 5000), (7300, 4660, 9600, 5000)],
    glyphs={},
)
g = REGULAR['glyphs']
g.update(seq(LC, 0)); g.update(seq(['adieresis', 'odieresis', 'udieresis'], 0, 26))
g.update({'c_h': ['0.29'], 'c_k': ['0.30', '0.31'], 'germandbls': ['0.32'], 't_z': ['0.33']})
g.update(seq('ABCDEFGHIJKLMNOPQRST', 1)); g.update(seq(['f_f', 'f_i', 'f_l', 'f_t'], 1, 20))
g.update(seq('UVWXYZ', 2)); g.update(seq(['Adieresis', 'Odieresis', 'Udieresis', 'Q_u', 'ampersand',
         'period', 'periodcentered', 'comma', 'colon', 'semicolon', 'hyphen', 'dblhyphen', 'emdash',
         'exclam', 'question', 'quoteright'], 2, 6))
g.update({'quotedblbase': ['2.22', '2.23'], 'quotedblleft': ['2.24', '2.25'],
          'guillemotright': ['2.26', '2.27'], 'guillemotleft': ['2.28', '2.29']})
g.update(seq(['slash', 'parenleft', 'parenright', 'bracketleft', 'bracketright', 'section',
              'dagger', 'asterisk', 'paragraph'], 2, 30))
g.update(seq([f + '.osf' for f in FIG], 3))
g.update(seq(['acc.' + a for a in ACC], 4))
g.update(seq([f + '.lf' for f in FIG], 5))

# ---------------------------------------------------------------- Italic, St. 43
ITALIC = dict(
    scan='53151948621_96e2d43e53_o.jpg',
    boxes=[(300, 2250, 9500, 2850), (300, 2850, 9500, 3420), (300, 3420, 9500, 4010),
           (300, 4010, 9500, 4570), (300, 4720, 5600, 5000), (7300, 4690, 9600, 5000)],
    glyphs={},
)
g = ITALIC['glyphs']
g.update(seq(LC, 0)); g.update(seq(['adieresis', 'odieresis', 'udieresis'], 0, 26))
g.update({'c_h': ['0.29', '0.30'], 'c_k': ['0.31', '0.32']})
g.update(seq(['f_f', 'f_i', 'f_l', 'f_t', 'germandbls', 't_t', 't_z'], 0, 33))
g.update(seq(UC, 1))
g.update(seq(['Adieresis', 'Odieresis', 'Udieresis', 'Q_u'], 2))
g.update(seq(['A.swsh', 'B.swsh', 'D.swsh', 'E.swsh', 'J.swsh', 'M.swsh', 'N.swsh', 'R.swsh',
              'S.swsh', 'T.swsh', 'T_h.swsh', 'Z.swsh'], 2, 19))
g.update(seq([f + '.osf' for f in FIG], 3))
g.update(seq(['ampersand', 'period', 'periodcentered', 'comma'], 3, 10))
g.update({'colon': ['3.14', '3.15']})
g.update(seq(['semicolon', 'hyphen', 'dblhyphen', 'emdash'], 3, 16))
g.update({'exclam': ['3.20', '3.21'], 'question': ['3.22'], 'quoteright': ['3.23'],
          'quotedblbase': ['3.24', '3.25'], 'quotedblleft': ['3.26', '3.27'],
          'guillemotright': ['3.28', '3.29'], 'guillemotleft': ['3.30', '3.31']})
g.update(seq(['slash', 'parenleft', 'parenright', 'bracketleft', 'bracketright', 'section',
              'dagger', 'asterisk', 'paragraph', 'e.swsh', 'k.alt', 'z.alt'], 3, 32))
acc = {}
i = 0
for a in ACC:
    if a in ('edieresis', 'idieresis'):
        acc['acc.' + a] = [f'4.{i}', f'4.{i+1}']; i += 2
    else:
        acc['acc.' + a] = [f'4.{i}']; i += 1
g.update(acc)
g.update(seq([f + '.lf' for f in FIG], 5))

# ---------------------------------------------------------------- Bold (Halbfette), St. 44
BOLD = dict(
    scan='53152152234_df7303667c_o.jpg',
    boxes=[(300, 2250, 9500, 2860), (300, 2860, 9500, 3450), (300, 3450, 9500, 3980),
           (300, 3980, 9500, 4530), (300, 4640, 5600, 5000), (7300, 4670, 9600, 5000)],
    glyphs={},
)
g = BOLD['glyphs']
g.update(seq(LC, 0)); g.update(seq(['adieresis', 'odieresis', 'udieresis', 'c_h', 'c_k', 'f_f'], 0, 26))
g.update(seq('ABCDEFGHIJKLMNOPQ', 1))
g.update(seq(['f_i', 'f_l', 'f_t', 'germandbls', 't_t', 't_z'], 1, 17))
g.update(seq('RSTUVWXYZ', 2))
g.update(seq(['ampersand', 'period', 'periodcentered', 'comma', 'colon', 'semicolon', 'hyphen',
              'dblhyphen', 'emdash', 'exclam', 'question', 'quoteright'], 2, 9))
g.update({'quotedblbase': ['2.21', '2.22'], 'quotedblleft': ['2.23', '2.24'],
          'guillemotright': ['2.25', '2.26'], 'guillemotleft': ['2.27', '2.28']})
g.update(seq(['slash', 'parenleft', 'parenright', 'bracketleft', 'bracketright', 'section',
              'dagger', 'asterisk'], 2, 29))
g.update(seq(['Adieresis', 'Odieresis', 'Udieresis'], 3))
g.update(seq([f + '.osf' for f in FIG], 3, 3))
g.update(seq(['acc.' + a for a in ACC], 4))
g.update(seq([f + '.lf' for f in FIG], 5))

SHEETS = {'Regular': REGULAR, 'Italic': ITALIC, 'Bold': BOLD}

# ---------------------------------------------------------------- display lines (for spacing)
# (scan, (y0, y1) band of the line, text).  x range of the right-hand column: 3900-7900.
DISPLAY = {
    'Regular': ('53151949716_f2b68c5eb6_o.jpg', [
        ((600, 1060), 'Die neue Blütezeit der italienischen Baukunst'),
        ((1190, 1690), 'Technikum für Meister und Ingenieure'),
        ((1800, 2340), 'Technische Hochschule in Hamburg'),
        ((2450, 3050), 'Ferien im sonnigen Portugal'),
        ((3170, 3800), 'Neuheiten im Autobau'),
        ((3920, 4640), 'Glas und Porzellan'),
        ((4750, 5590), 'Insel der Götter'),
        ((5710, 6450), 'Sternkunde')]),
    'Italic': ('53151374322_e5932bda02_o.jpg', [
        ((550, 1110), 'Die Kulturgeschichte der Länder in Osteuropa'),
        ((1230, 1840), 'Eine Wandlung im deutschen Geistesleben'),
        ((1960, 2640), 'Die Prinzipien der Staatsordnung'),
        ((2750, 3510), 'Weg der modernen Literatur'),
        ((3630, 4450), 'Forschung am Nordpol'),
        ((4570, 5530), 'Tänze aus Spanien'),
        ((5650, 6450), 'Balkanstaaten')]),
    'Bold': ('53151948591_7b952d8a3e_o.jpg', [
        ((540, 1120), 'Die Gesellenprüfung als Autoschlosser'),
        ((1230, 1850), 'Tiere und Pflanzen aus Australien'),
        ((1960, 2640), 'Institut für Krebsforschung'),
        ((2760, 3510), 'Rheinbrücke bei Deutz'),
        ((3630, 4450), 'Deutsche Gedichte'),
        ((4570, 5520), 'Farbendrucker'),
        ((5630, 6450), 'Eisenwerke')]),
}
# runs of the character sheets set solid, as glyph names in order
def runs(style):
    G = SHEETS[style]['glyphs']
    R = [list(LC), [c for c in UC if c in G and G[c][0].startswith('1.')],
         [c for c in UC if c in G and G[c][0].startswith('2.')],
         [f + '.osf' for f in FIG]]
    if style == 'Italic':
        R.append(['c_h', 'c_k', 'f_f', 'f_i', 'f_l', 'f_t', 'germandbls', 't_t', 't_z'])
        R.append(['adieresis', 'odieresis', 'udieresis'])
    elif style == 'Regular':
        R.append(['c_h', 'c_k', 'germandbls', 't_z']); R.append(['f_f', 'f_i', 'f_l', 'f_t'])
        R.append(['adieresis', 'odieresis', 'udieresis'])
    else:
        R.append(['f_i', 'f_l', 'f_t', 'germandbls', 't_t', 't_z'])
        R.append(['adieresis', 'odieresis', 'udieresis'])
    R.append(['Adieresis', 'Odieresis', 'Udieresis'])
    R.append([f + '.lf' for f in FIG])
    return R

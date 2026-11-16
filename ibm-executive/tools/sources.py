"""Where every face's text is on the scans.

A source line is (scan, box, text).  The box is x0, y0, x1, y1 in pixels of the scan; the line's glyphs are the
components whose centres fall in it.  The text is what the line says; each character is one group of
components (segment.group), except those in MULTI, which print as several groups side by side.

Paragraph lines may be given as one stream (PARA) together with their boxes; read.py breaks the stream into
lines by counting the groups on each line.
"""

MULTI = {'"': 2}          # characters that print as more than one group side by side

# --------------------------------------------------------------------------------------------- Jowa (Modern)
# Johannes Wagner GmbH, Ingolstadt: "IBM Executive 602", foundry type cast in 10 p Didot after Monotype's
# drawings of its series 602, which is IBM's Modern.  Card "Jowa 64", front (type list) and back (text).
JOWA_LIST = '53151352897_bb00092d19_o.jpg'
JOWA_TEXT = '53152131364_bf2060fa84_o.jpg'

JOWA_LINES = [
    (JOWA_LIST, (300, 2600, 9500, 2990), 'abcdefghijklmnopqrstuvwxyz äöü ß'),
    (JOWA_LIST, (300, 2990, 9500, 3380), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ ÄÖÜ'),
    (JOWA_LIST, (300, 3380, 9500, 3780), '1234567890 & .,-:;!?(/"»«\'*+ %$£'),
    (JOWA_LIST, (300, 4650, 9500, 5050), 'àáâçèéêëìíîïòóôùúû åñø ÇÈÉÊ ÅÑØ'),
]
JOWA_SPLIT = {'ÅÑ': 2}    # groups the card prints touching: split at the narrowest column
# the guillemets print as two chevrons each, the asterisk as two halves: groups per character
JOWA_MULTI = {'»': 2, '«': 2, '*': 2, '"': 2}

JOWA_BLOCK1 = [
    'Bei dieser neuen Schreibmaschinenschrift ist das Alphabet in vier',
    'systematische Dicken aufgeteilt (4, 6, 8 und 10p). Besonderer',
    'Schreibmaschinenausschluß ist nicht mehr notwendig. Es kann vielmehr',
    'der normale Ausschluß nach Punktsystem benutzt werden. Diese',
    'IBM Schreibmaschinenschrift kann auch mit Randausgleich gesetzt',
    'werden, so wie es mit der IBM Executive Schreib-Setz-Maschine',
    'ebenfalls möglich ist. Der besondere Vorteil dieser neuen',
    'Schreibmaschinenschrift liegt darin, daß das Bild der im Monotype-',
    'Schriftmusterbuch als Serie 602 gezeigten Schrift unverändert',
    'nach dem in Europa gültigem deutsch-französischem Didot-System',
    'gegossen wurde. Der Satz dieser neuen Schreibmaschinenschrift',
    'ist dadurch besonders einfach. Die verschiedenen Buchstabenbreiten',
    'in Verbindung mit den unterschiedlichen Wortzwischenräumen',
    'erlauben es dem Setzer, nach allgemeinen typographischen Regeln mit',
]
JOWA_BLOCK2 = JOWA_BLOCK1[:10]
# (x0, x1, first baseline, line pitch) of the two text blocks: a component belongs to the line whose baseline
# is 0.2 pitch below to 0.8 pitch above its centre
JOWA_BLOCKS = [((450, 7400), 672, 178.3, JOWA_BLOCK1),
               ((450, 7400), 3952, 248.7, JOWA_BLOCK2)]

# ------------------------------------------------------------------------------- Finnish brochure (all faces)
# "IBM Executive -kirjoituskoneen kirjasinnäytteet": eight faces, each a paragraph, figures and symbols, and
# the lower- and upper-case alphabets of Finnish (no w or W).  Coordinates in the 1600-px-wide preview, scaled.
FINNISH = 'ibm-executive-typefaces-finnish.jp2'
PARA = ('IBM EXECUTIVE on jokaisen sihteerin toivekone. Sen jälki on kaunista. Se on ulkoasultaan tyylikäs ja '
        'edustava. Valitkaa mieleisenne kirjasinmalli ja väri. Kokeilkaa. Kirjoitustyö sujuu nopeasti ja '
        'vaivattomasti. Miellytte.')
LC_FI = 'abcdefghijklmnopqrstuvxyzåäö.,-'
UC_FI = 'ABCDEFGHIJKLMNOPQRSTUVXYZÅÄÖ'
L1 = 'IBM EXECUTIVE on jokaisen sihteerin'
STD = [L1, 'toivekone. Sen jälki on kaunista. Se on', 'ulkoasultaan tyylikäs ja edustava.',
       'Valitkaa mieleisenne kirjasinmalli ja', 'väri. Kokeilkaa. Kirjoitustyö sujuu',
       'nopeasti ja vaivattomasti. Miellytte.']
ALT = [L1, 'toivekone. Sen jälki on kaunista. Se', 'on ulkoasultaan tyylikäs ja edustava.'] + STD[3:]
LINES_FI = {
    'Modern': STD, 'Documentary': STD, 'BoldFace1': STD, 'BoldFace2': STD,
    'MidCentury': ALT, 'Arcadia': ALT,
    'Doric': [L1, 'toivekone Sen jälki on kaunista. Se on'] + STD[2:],     # no full stop on the card
    'Charter': ['IBM EXECUTIVE on jokaisen sihteerin toivekone.', 'Sen jälki on kaunista. Se on ulkoasultaan tyylikäs',
                'ja edustava. Valitkaa mieleisenne kirjasinmalli', 'ja väri. Kokeilkaa. Kirjoitustyö sujuu nopeasti ja',
                'vaivattomasti. Miellytte.'],
}
# block (preview coordinates), number of paragraph lines, symbols after the figures
FACES_FI = {
    'Modern':      ((668, 92, 1048, 282), 6, '£()?%+&$/§"`ü´'),
    'Documentary': ((668, 315, 1048, 502), 6, '£()?%+&$/§"`ü´'),
    'MidCentury':  ((668, 540, 1048, 727), 6, 'ü+§=%?&()/`£´$'),
    'Arcadia':     ((668, 765, 1048, 935), 6, '!+§=%?&()/`£´ü'),
    'Doric':       ((1193, 92, 1578, 282), 6, 'ü+§=%?&()/`£´$'),
    'BoldFace1':   ((1193, 315, 1578, 502), 6, '!+§=%?&()/´£`ü'),
    'BoldFace2':   ((1193, 540, 1578, 727), 6, 'ü+§=%?&()/`£´$'),
    'Charter':     ((1193, 765, 1578, 890), 5, 'ü+§=%?&()/`£´$'),
}

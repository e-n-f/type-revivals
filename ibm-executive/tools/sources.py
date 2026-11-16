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
# The symbols after the figures each print once, some in pieces (%, ") or touching a neighbour (Charter's =%,
# Doric's +§, Bold Face 2's ()), so matching them by counting groups goes wrong.  Their columns are given by
# hand instead, in the coordinates of the line as read.block_lines finds it (pixels of the full scan from the
# block's left edge): (character, first column, last column).  A character missing from the list printed
# too faintly to be found (Documentary's `, Arcadia's ´).
SYMBOL_COLUMNS = {
    'Modern': [('£', 756, 787), ('(', 807, 822), (')', 832, 846), ('?', 863, 889), ('%', 906, 952), ('+', 960, 991),
               ('&', 1001, 1039), ('$', 1054, 1085), ('/', 1097, 1123), ('§', 1138, 1158), ('"', 1171, 1197),
               ('`', 1219, 1233), ('ü', 1259, 1295), ('´', 1317, 1332)],
    'Documentary': [('£', 703, 736), ('(', 743, 759), (')', 767, 783), ('?', 794, 821), ('%', 832, 879),
                    ('+', 888, 924), ('&', 930, 972), ('$', 987, 1017), ('/', 1034, 1060), ('§', 1074, 1101),
                    ('"', 1112, 1140), ('ü', 1200, 1236), ('´', 1270, 1289)],
    'MidCentury': [('ü', 680, 706), ('+', 711, 744), ('§', 754, 777), ('=', 779, 812), ('%', 816, 870),
                   ('?', 885, 915), ('&', 927, 966), ('(', 974, 989), (')', 991, 1006), ('/', 1012, 1053),
                   ('`', 1050, 1067), ('£', 1089, 1119), ('´', 1137, 1153), ('$', 1170, 1196)],
    'Arcadia': [('!', 717, 727), ('+', 744, 779), ('§', 786, 816), ('=', 823, 859), ('%', 868, 911), ('?', 926, 953),
                ('&', 971, 1009), ('(', 1029, 1043), (')', 1047, 1061), ('/', 1071, 1113), ('`', 1120, 1136),
                ('£', 1154, 1184), ('ü', 1257, 1291)],
    'Doric': [('ü', 708, 741), ('+', 751, 787), ('§', 787, 822), ('=', 829, 865), ('%', 867, 914), ('?', 920, 952),
              ('&', 958, 995), ('(', 999, 1021), (')', 1028, 1049), ('/', 1051, 1089), ('`', 1092, 1114),
              ('£', 1129, 1163), ('´', 1186, 1209), ('$', 1222, 1256)],
    'BoldFace1': [('!', 755, 765), ('+', 781, 817), ('§', 830, 853), ('=', 862, 895), ('%', 905, 954),
                  ('?', 968, 999), ('&', 1006, 1049), ('(', 1058, 1075), (')', 1083, 1100), ('/', 1107, 1143),
                  ('´', 1157, 1174), ('£', 1195, 1232), ('`', 1258, 1274), ('ü', 1305, 1340)],
    'BoldFace2': [('ü', 640, 673), ('+', 676, 706), ('§', 712, 733), ('=', 745, 776), ('%', 783, 825),
                  ('?', 835, 862), ('&', 877, 915), ('(', 927, 941), (')', 941, 956), ('/', 966, 995),
                  ('`', 1005, 1021), ('£', 1044, 1073), ('´', 1099, 1116), ('$', 1135, 1164)],
    'Charter': [('ü', 782, 808), ('+', 814, 839), ('§', 846, 861), ('=', 870, 889), ('%', 889, 933), ('?', 940, 957),
                ('&', 963, 986), ('(', 992, 1002), (')', 1013, 1023), ('/', 1031, 1049), ('`', 1057, 1071),
                ('£', 1087, 1111), ('´', 1128, 1141), ('$', 1152, 1175)],
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

# ------------------------------------------------------------------------------------- keyboard sheet (Modern)
# Typed on a 1950s Executive in Modern: the shifted top row, for the characters neither card shows.  The 8
# printed too faintly to read; its slug is still there (KEYBOARD_GHOST: character, units, after which
# character), so the positions of the others can be fitted.
KEYBOARD = 'typed-keyboard-pairs.jpg'
KEYBOARD_LINE = (KEYBOARD, (200, 1520, 2200, 1760), '@2#3$4%5¢6&7*(9)0_-+')
KEYBOARD_SPLIT = {'4%': 2}
KEYBOARD_MULTI = {'*': 3, '%': 2}
KEYBOARD_GHOST = ('8', 3, '*')
KEYBOARD_SKIP = '(4%'     # inked over by the faint 8, or split from one another: their centres are unreliable
# The positions on this photograph are too rough (a few pixels to the unit's 27) to tell 3 units from 4, so
# the widths of # ¢ _ are IBM's own: the typed sheet typed-bold-face-1-units.jpg lists them at 3 units of
# 1/32 inch ("qeryuopasdghkzxcvbnSJ!#$¢*"_ : 3 units"), as the fitted tables have the other characters.
KEYBOARD_UNITS = {'#': 3, '¢': 3, '_': 3}

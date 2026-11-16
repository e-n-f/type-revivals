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

# ----------------------------------------------------------------------------- typed documents (300 dpi scans)
# Pages typed on Executives, for characters the brochure doesn't show.  Each entry is (scan, box, text): a
# box holding one line and its text, or a box holding several lines (found as for the brochure) and a list
# of their texts.  Boxes in pixels of the scan.
#
# Mid-Century: a letter of the American Standards Association, 28 May 1962 (ISO/TC97/WGB document USA-4).
MC_LETTER = 'midcentury-asa-letter-0027.jpg'
TYPED = {
    'MidCentury': [
        (MC_LETTER, (380, 735, 2157, 812), 'ISO/TC97/Working Group B - COMPUTERS AND INFORMATION PROCESSING'),
        (MC_LETTER, (268, 898, 392, 962), 'Date:'),
        (MC_LETTER, (490, 898, 777, 962), '28 May 1962'),
        (MC_LETTER, (1205, 898, 1935, 962), 'Return Address: Mr. Leon Bloom'),
        (MC_LETTER, (1578, 956, 2395, 1012), 'The National Cash Register Company'),
        (MC_LETTER, (1578, 1013, 2275, 1070), '1401 East El Segundo Boulevard'),
        (MC_LETTER, (268, 1018, 1072, 1077), 'Document Number: ISO/TC97/WGB'),
        (MC_LETTER, (768, 1077, 982, 1133), '(USA - 4)'),
        (MC_LETTER, (1578, 1071, 2085, 1128), 'Hawthorne, California'),
        (MC_LETTER, (268, 1240, 452, 1312), 'Subject:'),
        (MC_LETTER, (490, 1226, 2190, 1300), 'Action of ASA Subcommittee of X3.2 on Resolution #1 of WGB - 4 May 1962'),
        (MC_LETTER, (495, 1415, 1400, 1645), ['Mr. J. Birle, Director General', 'Association Francaise De NORmalisation',
                                             '23, Rue Notre-Dame Des Victoires', 'Paris, (2), FRANCE']),
        (MC_LETTER, (495, 1708, 862, 1766), 'Dear Mr. Birle:'),
        (MC_LETTER, (495, 1812, 2118, 1998), ['The ASA X3.2 Subcommittee on Character Codes and Sets has considered',
                                             'Proposal B of Working Group B and in that regard have passed the follow-',
                                             'ing resolution by a vote of seven (7) for, and two (2) against:']),
        (MC_LETTER, (490, 2042, 2140, 2342), ['" That X3.2 recommend to X3 that the USA support Proposal B of WGB',
                                             'Resolution 1 of 3 and 4 May 1962, subject to recommendations on Logical',
                                             'End of Media (LEM) and to satisfy requirements of X3.3 (transmission) and',
                                             'the needs of the Sterling areas; documentation of unanimous or majority',
                                             'and minority positions to be provided".']),
        (MC_LETTER, (495, 2388, 2100, 2456), 'The changes indicated by the resolution are specifically the following:'),
        (MC_LETTER, (705, 2503, 2022, 2566), 'Logical End of Media (LEM) to replace End of Block (EOB).'),
        (MC_LETTER, (840, 2618, 2080, 2686), 'is reserved for possible future use as a Data Link Escape.'),
        (MC_LETTER, (705, 2733, 2052, 2916), ['The colon (:) and semi colon (;) has been interchanged with',
                                             'the asterisk (*) and plus (+) in order to better accommodate',
                                             'the Sterling monitary requirements in the 6-bit set.']),
    ],
}

# Charter: "Standard BCD Interchange Code", 1962, typed in Charter.  Page 46's Graphics column holds one
# character (or two) to a row, rows CH_ROW0 + k CH_PITCH pixels down (k = collating number - 1); page 47's
# captions and labels give the neighbour pairs for the unit.
CH_TABLE, CH_LABELS = 'charter-bcd-code-0046.jpg', 'charter-bcd-code-0047.jpg'
CH_ROW0, CH_PITCH = 405, 42.33
# Each row is a line of its own; a lone symbol can't show where the baseline is, so it is set at the depth the
# rows of flat-footed capitals have it (all rows are the same height).
def _row(k, text): return (CH_TABLE, (600, int(CH_ROW0 + CH_PITCH * (k - 0.5)), 800, int(CH_ROW0 + CH_PITCH * (k + 0.5))), text, 'row')
CH_CALIBRATION = ((25, 'A'), (26, 'B'), (28, 'D'), (29, 'E'), (30, 'F'), (32, 'H'), (37, 'K'), (38, 'L'), (39, 'M'),
                  (40, 'N'), (46, 'T'), (49, 'W'), (50, 'X'), (52, 'Z'))
TYPED['Charter'] = [_row(k, t) for k, t in CH_CALIBRATION] + [_row(k, t) for k, t in ((2, '['), (3, '<'), (5, '& +'), (7, '*'), (8, ']'), (9, ';'), (14, '% ('),
                                             (16, '\\'), (19, '# ='), (20, "@ '"), (21, ':'), (22, '>'), (24, '?'),
                                             (34, '!'))] + [
    (CH_LABELS, (557, 472, 830, 512), 'Graphic Subset 1'),
    (CH_LABELS, (557, 517, 890, 557), 'Print Arrangement A'),
    (CH_LABELS, (557, 562, 830, 604), 'Graphic Subset 2'),
    (CH_LABELS, (557, 607, 895, 647), 'Print Arrangement H'),
    (CH_LABELS, (552, 688, 1090, 732), 'Figure 2. Graphic Subset 1 and 2'),
    (CH_LABELS, (562, 923, 866, 963), 'Control Characters'),
    (CH_LABELS, (680, 1013, 965, 1055), 'Group Mark'),
    (CH_LABELS, (680, 1058, 965, 1100), 'Tape Mark'),
    (CH_LABELS, (680, 1103, 965, 1145), 'Segment Mark'),
    (CH_LABELS, (680, 1148, 965, 1190), 'Mode Change'),
    (CH_LABELS, (680, 1193, 965, 1235), 'Record Mark'),
    (CH_LABELS, (680, 1238, 965, 1280), 'Substitute Blank'),
    (CH_LABELS, (680, 1283, 965, 1325), 'Word Separator'),
    (CH_LABELS, (552, 1365, 1240, 1409), 'Figure 3. Control Characters and Graphics'),
    (CH_LABELS, (700, 1728, 866, 1771), 'Minus Zero'),
    (CH_LABELS, (700, 1773, 866, 1816), 'Plus Zero'),
    (CH_LABELS, (552, 1863, 1040, 1905), 'Figure 4. Minus and Plus Zero'),
    (CH_LABELS, (750, 1998, 1242, 2042), 'Standard BCD Interchange Code'),
    (CH_LABELS, (562, 2789, 1170, 2833), 'Figure 5. Code Summary Comparison'),
]

# ----------------------------------------------------------------------------------- printed sheets (alternates)
# IBM's "Type designs for the IBM 'Executive' Typewriter", sheet 1: Arcadia with a two-storey a, where the
# Finnish brochure's Arcadia has a one-storey one.  Printed, not typed; read for that a alone.
SHEETS = {
    'ArcadiaSheet': [('type-designs-ibm-executive-0001.jp2', (2450, 2480, 8400, 3140),
                      ['This is a sample of IBM Arcadia Type. Designed for all-',
                       'purpose use, its distinctive appearance enhances finished',
                       'copy in a variety of applications.'])],
}

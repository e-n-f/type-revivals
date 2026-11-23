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
    'systematische Dickten aufgeteilt (4, 6, 8 und 10p). Besonderer',
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
FINNISH = 'executive-typefaces-finnish.jp2'
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

# Arcadia: IBM's E. T. News Letter No. 16 (1955), page 5, announcing the face: a paragraph and the whole
# keyboard, typed with the two-storey a (the one-storey a is an alternate, IBM part 1112308).
NL55 = 'et-newsletter-16-1955-p5.png'
TYPED['Arcadia'] = [
    (NL55, (565, 1050, 3045, 2200), ['IBM Electric Typewriters bring quality, ease, and speed',
                                     "to today's typing. With only a feather-light touch re-",
                                     'quired to release the electrically-powered keys, un-',
                                     'necessary hand and arm motion has been eliminated.',
                                     'All operating keys - the carriage return, tabulator, shift,',
                                     'and back spacer - are located on the nearly level key-',
                                     'board and are released with the same light touch. Better',
                                     'quality of typewritten work, increased speed and ease',
                                     'of operation, and the ability to produce many legible',
                                     'carbon copies are only a few of the advantages of IBM',
                                     'Electric Typewriters.']),
    (NL55, (1030, 2290, 2200, 2385), "234567890-1';/.,"),
    (NL55, (1030, 2385, 1760, 2490), '@#$%¢&*()_!":?'),
    (NL55, (1030, 2490, 2320, 2595), 'abcdefghijklmnopqrstuvwxyz'),
    (NL55, (1030, 2595, 2560, 2700), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
]

# ------------------------------------------------------------------------------- Secretarial and Registry
# Faces with no brochure line: a typed page is the main source, IBM's 1972 catalogue (tools/catalog.py) the
# widths and the characters the page lacks.
#
# Secretarial: R. W. Bemer's memo of 7 November 1961 on the X3.2 code, typed in it (a faint photocopy, 300 dpi).
MEMO = 'secretarial-bemer-memo-1961.jpg'
TYPED['Secretarial'] = [
    (MEMO, (290, 530, 2240, 850), ['Four characters of the 4-bit subset have been available to IBM customers',
                                   'for use in ordering keys. They are . , - / . The * is also used and is',
                                   'to be paired (for keyboard convenience) with the +. Of these characters',
                                   '- and / have, according to our surveys, high frequency usage in keys.',
                                   'The usage of * is small and that of . and , are negligible.']),
    (MEMO, (290, 885, 2240, 1650), ['The presently agreed code of X3.2 was specifically structured so that',
                                    '- and / were not in the same stick as the decimal digits. I refused to',
                                    'agree upon a code for IBM unless this condition were met. The reason',
                                    'for this is that with the present X3.2 code the numeric stick can be rotated',
                                    'high with a simple EXCLUSIVE OR element and collate for the 6-bit',
                                    'set effectively identical to the present IBM collating sequence (the changed',
                                    'order among the special characters has been shown to have a trivial',
                                    'effect). The six characters which exist in the numeric stick would not',
                                    'be used in keys, nor do they have relevant ordering properties. This',
                                    'was agreed to by J.R. Auwaerter by Teletype, realizing that the normal',
                                    'keyboard arrangement for these keys would have to be reversed or else',
                                    'the shift bit would have to be inverted for these keys only. Apparently',
                                    'this is not too great a hardship.']),
    (MEMO, (290, 1690, 2240, 2050), ['Howard Smith, meeting with DS and GP, has now proposed a variation',
                                     'which was accepted at the 3 November meeting of the CSTC. I am in',
                                     'agreement with all of these changes except those pertaining to the above',
                                     'situation! . and / are now in the numeric stick and a transformation',
                                     'much fancier than an EXCLUSIVE OR would be required to get a',
                                     'collating sequence suitable to IBM.']),
    (MEMO, (290, 2085, 2240, 2450), ['I realize that with an 8-bit set (and upper and lower case alphabets) some',
                                     'extra logic is required to effect the collating of somewhere near 256',
                                     'characters. However, I think it reasonable to demand that the 6-bit',
                                     'set operate very simply. I suspect that GS and DP might not have known',
                                     'what they were agreeing to. I suggest that you do not propose this',
                                     'particular change to X3.2 on 8 November.']),
]
# Registry: IBM's E. T. News Letter No. 16 (1955), page 6, announcing the face: a paragraph and the keyboard.
NL55_6 = 'et-newsletter-16-1955-p6.png'
TYPED['Registry'] = [
    (NL55_6, (280, 1330, 2700, 2390), ['IBM Electric Typewriters bring quality, ease, and speed to',
                                       "today's typing. With only a feather-light touch required to",
                                       'release the electrically-powered keys, unnecessary hand',
                                       'and arm motion has been eliminated. All operating keys -',
                                       'the carriage return, tabulator, shift, and back spacer - are',
                                       'located on the nearly level keyboard and are released with',
                                       'the same light touch. Better quality of typewritten work, in-',
                                       'creased speed and ease of operation, and the ability to pro-',
                                       'duce many legible carbon copies are only a few of the advan-',
                                       'tages of IBM Electric Typewriters.']),
    # (the keyboard's _ didn't print: the line has a gap where it is)
    (NL55_6, (680, 2440, 2320, 2880), ["234567890-1';/.,", '@#$%¢&*()!":?', 'abcdefghijklmnopqrstuvwxyz',
                                       'ABCDEFGHIJKLMNOPQRSTUVWXYZ']),
]

# characters a typed page prints as more than one group side by side, besides MULTI's: Registry's % (a slash
# and a small o)
TYPED_MULTI = {'Registry': {'%': 2}}

# A typed line whose signs are read by hand-listed columns (character, first, last column, in pixels from the
# box's left edge), as the brochure's symbol lines are: Registry's keyboard line of signs, whose @# and *( touch
# and whose % prints in two pieces, so counting groups goes wrong
# The NOMDA dealers' guide's pages of IBM type styles (6-70, from Typecast; small and cut off at the right):
# Doric's keyboard row and Bold Face 2's (code 057, the lighter of the two Bold Faces) line of signs give their
# @ # ¢, and Doric's _, which no other source shows
NOMDA = 'NOMDA-type-IBM-09.jpg'
TYPED['Doric'] = []
TYPED['BoldFace2'] = []
TYPED_COLUMNS = {'Doric': [(NOMDA, (335, 540, 630, 592),
                            [('[', 8, 19), ('@', 19, 43), ('#', 44, 61), ('$', 61, 81), ('%', 82, 105), ('¢', 106, 123),
                             ('&', 124, 144), ('*', 145, 158), ('(', 160, 173), (')', 174, 184), ('_', 185, 205),
                             ('+', 206, 226)])],
                 'BoldFace2': [(NOMDA, (300, 222, 640, 262),
                                [('#', 10, 27), ('*', 27, 43), ('¶', 44, 58), ('/', 59, 76), ('$', 76, 94), ('†', 94, 109),
                                 ('?', 114, 132), ('!', 137, 147), ('¢', 149, 166), ('(', 166, 175), (')', 175, 186),
                                 ('@', 187, 210)])],
                 'Registry': [(NL55_6, (680, 2570, 2320, 2690),
                               [('@', 28, 93), ('#', 93, 140), ('$', 158, 199), ('%', 208, 270), ('¢', 279, 315),
                                ('&', 319, 375), ('*', 379, 425), ('(', 425, 447), (')', 460, 484), ('!', 547, 560),
                                ('"', 577, 605), (':', 625, 640), ('?', 658, 694)])]}

# IBM's Mag Card Executive type catalogue (TC 5.1 and 5.2, July 1983; scanned at 400 dpi, soft): a line of
# signs and figures in each face, two rows: !@#$%¢&*()_+¼:",.? over 1234567890-=½;',./.  Its Arcadia 72, Bold Face
# 72, Bold Face Italic 72, Document 72 and Modern 72 are our Arcadia, Bold Face 1 (the 1/32-inch Bold Face),
# Bold Face 1 Italic, Documentary and Modern.  It gives their ¼ and ½, which nothing else shows, Bold Face 1's and
# Documentary's ¢, and Modern's ) (its card has only the ().  Read by hand-listed columns: in the first row the _
# touches the +, and the second row's top is cut below the first row's _, which prints over the 0 - =.  (Arcadia's
# first row is read to its :, after which it has a stray dot.)  Each is a source of its own, MagCard<Face>Typed,
# fitted with its face's unit table (UNITS_OF).
TC51, TC52 = 'mag-card-catalog-1983-tc51.jpg', 'mag-card-catalog-1983-tc52.jpg'
MAGCARD = {
    'MagCardArcadia': [(TC51, (2620, 1191, 3320, 1262),
        [('!', 68, 76), ('@', 92, 122), ('#', 124, 151), ('$', 155, 180), ('%', 186, 215), ('¢', 217, 244), ('&', 249, 276), ('*', 281, 307), ('(', 322, 335), (')', 344, 356), ('_', 373, 409), ('+', 409, 432), ('¼', 439, 461), (':', 471, 480)]),
       (TC51, (2620, 1262, 3320, 1319),
        [('1', 63, 83), ('2', 91, 116), ('3', 124, 148), ('4', 154, 180), ('5', 185, 210), ('6', 217, 243), ('7', 248, 273), ('8', 280, 305), ('9', 311, 338), ('0', 343, 369), ('-', 375, 399), ('=', 402, 432), ('½', 440, 462), (';', 468, 479), ("'", 503, 510), (',', 528, 538), ('.', 560, 568), ('/', 585, 608)])],
    'MagCardBoldFace1': [(TC51, (2620, 1679, 3320, 1747),
        [('!', 65, 75), ('@', 92, 123), ('#', 125, 153), ('$', 156, 181), ('%', 187, 216), ('¢', 219, 246), ('&', 250, 277), ('*', 282, 307), ('(', 319, 338), (')', 345, 363), ('_', 373, 410), ('+', 410, 435), ('¼', 439, 464), (':', 471, 481), ('"', 501, 523), (',', 541, 552), ('.', 572, 582), ('?', 596, 617)]),
       (TC51, (2620, 1747, 3320, 1804),
        [('1', 62, 85), ('2', 93, 117), ('3', 125, 150), ('4', 155, 182), ('5', 188, 213), ('6', 219, 244), ('7', 250, 274), ('8', 281, 307), ('9', 314, 340), ('0', 345, 370), ('-', 376, 401), ('=', 405, 434), ('½', 441, 465), (';', 471, 482), ("'", 503, 512), (',', 531, 542), ('.', 561, 572), ('/', 585, 608)])],
    'MagCardBoldFaceItalic': [(TC51, (2620, 2163, 3320, 2230),
        [('!', 66, 80), ('@', 98, 128), ('#', 130, 159), ('$', 161, 190), ('%', 192, 221), ('¢', 226, 253), ('&', 256, 285), ('*', 288, 312), ('(', 323, 341), (')', 350, 369), ('_', 380, 415), ('+', 415, 441), ('¼', 444, 468), (':', 475, 486), ('"', 511, 532), (',', 543, 554), ('.', 575, 584), ('?', 601, 621)]),
       (TC51, (2620, 2230, 3320, 2287),
        [('1', 68, 89), ('2', 98, 126), ('3', 131, 157), ('4', 161, 187), ('5', 194, 221), ('6', 227, 254), ('7', 260, 284), ('8', 287, 315), ('9', 320, 347), ('0', 353, 379), ('-', 384, 408), ('=', 412, 443), ('½', 447, 470), (';', 475, 488), ("'", 513, 521), (',', 534, 544), ('.', 565, 574), ('/', 588, 620)])],
    'MagCardDocumentary': [(TC51, (2620, 2648, 3320, 2714),
        [('!', 68, 77), ('@', 94, 124), ('#', 127, 155), ('$', 158, 184), ('%', 189, 218), ('¢', 222, 248), ('&', 252, 278), ('*', 284, 308), ('(', 325, 338), (')', 348, 361), ('_', 376, 411), ('+', 411, 435), ('¼', 442, 465), (':', 473, 482), ('"', 504, 524), (',', 541, 552), ('.', 574, 583), ('?', 597, 618)]),
       (TC51, (2620, 2714, 3320, 2773),
        [('1', 65, 86), ('2', 94, 118), ('3', 127, 150), ('4', 158, 183), ('5', 190, 214), ('6', 221, 245), ('7', 253, 276), ('8', 283, 307), ('9', 315, 338), ('0', 346, 370), ('-', 378, 402), ('=', 406, 434), ('½', 443, 466), (';', 471, 483), ("'", 506, 514), (',', 530, 541), ('.', 562, 572), ('/', 586, 607)])],
    'MagCardModern': [(TC52, (2280, 1096, 2980, 1169),
        [('!', 78, 88), ('@', 107, 140), ('#', 143, 172), ('$', 175, 204), ('%', 208, 239), ('¢', 244, 268), ('&', 275, 303), ('*', 309, 337), ('(', 346, 367), (')', 375, 396), ('_', 407, 444), ('+', 444, 470), ('¼', 475, 501), (':', 510, 519), ('"', 545, 562), (',', 582, 593), ('.', 617, 626), ('?', 643, 664)]),
       (TC52, (2280, 1169, 2980, 1230),
        [('1', 74, 96), ('2', 105, 132), ('3', 141, 167), ('4', 173, 201), ('5', 208, 234), ('6', 240, 267), ('7', 273, 299), ('8', 306, 333), ('9', 342, 368), ('0', 375, 402), ('-', 409, 433), ('=', 439, 468), ('½', 477, 501), (';', 507, 518), ("'", 545, 551), (',', 570, 581), ('.', 605, 614), ('/', 630, 654)])],
}
TYPED_COLUMNS.update(MAGCARD)
TYPED.update({f: [] for f in MAGCARD})
# the unit table a typed source is fitted with, where it isn't its own face's
UNITS_OF = {**{f: f[len('MagCard'):] for f in MAGCARD}, 'MagCardBoldFaceItalic': 'BoldFaceItalicSet'}

# ------------------------------------------------------------------------------ Typesetting with IBM Executive Typewriters
# "Typesetting with IBM Executive Typewriters" (archive.org typesettingwithi0000gard): a page per face typed on the
# Executive, all with the same paragraph, then the signs and the two alphabets.  Screenshots of the book's page
# images (typesetting-<face>-<n>.png).  The keyboard's underscore is left out of the signs: it often prints a
# line low, over a capital of the alphabet line (read.py trims what reaches above the capitals there).
def _set_para(of='of', quotes=True):
    q = '"color"' if quotes else 'color'
    return ['The purpose of this paragraph is to show the various IBM Executive',
            'types when set on different ratchet spacings and with different',
            'percentages of reduction. These lines have purposely been set',
            f'without right hand margination so that the true {q} of the type',
            'will show. Consult the separate charts in this book to find out how',
            f'wide to set a line to achieve a given reduction {of} the width you',
            'want the final printed job to be.']
_SIGNS = "§1234567890%‡='-.,#*¶/$†?!¢()@&+‘_;:"
_ALPHA = 'abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_SETBOX = {'arcadia': (0, 238, 2090, 855), 'boldface1': (0, 295, 2114, 994), 'boldface2': (0, 242, 1982, 857),
           'boldfaceitalic': (0, 225, 2400, 848), 'charter': (0, 273, 2032, 930),
           'copperplate1': (0, 331, 2352, 1065), 'copperplate2': (0, 309, 2382, 1045),
           'directory': (0, 372, 2520, 1372), 'documentary': (0, 329, 2552, 1064), 'heritage': (31, 322, 2426, 1115),
           'midcentury': (0, 333, 2286, 1071), 'modern': (18, 272, 2594, 1013), 'patron': (0, 326, 2400, 1066),
           'registry': (0, 305, 2350, 1059), 'secretarial': (0, 306, 2567, 1040),
           'testimonial': (0, 290, 2538, 1041), 'text': (0, 261, 1864, 890)}
_AT = {'modern', 'boldfaceitalic', 'copperplate1'}         # (Copperplate 2's pages: 'of')
_SETSIGNS = {'boldfaceitalic': "§234567890-=1';/.,¶@#$%¢&*()_+!\":?.,",
             'patron': "1234567890-=';/.,!@#$%¢&*()_+\":?.,",
             # Copperplate: the small figures and signs (unshifted keys), then the large ones (shifted), which
             # are named by their full-width forms here and in the font's ss01
             # (one word: the gap between the sets is no wider than Copperplate's letter spacing)
             'copperplate1': '1234567890()*$?-+.１２３４５６７８９０（）＊＄？－＋．',
             'copperplate2': '1234567890()*$?-+.１２３４５６７８９０（）＊＄？－＋．'}
_FACE = {'arcadia': 'Arcadia', 'boldface1': 'BoldFace1', 'boldface2': 'BoldFace2', 'boldfaceitalic': 'BoldFaceItalic',
         'charter': 'Charter', 'copperplate1': 'Copperplate1', 'copperplate2': 'Copperplate2', 'directory': 'Directory',
         'documentary': 'Documentary', 'heritage': 'Heritage', 'midcentury': 'MidCentury', 'modern': 'Modern',
         'patron': 'Patron', 'registry': 'Registry', 'secretarial': 'Secretarial', 'testimonial': 'Testimonial',
         'text': 'Text'}
TYPESET = {}
for _k, _box in _SETBOX.items():
    _para = _set_para('at' if _k in _AT else 'of', quotes=not _k.startswith('copperplate'))
    TYPESET[_FACE[_k]] = [(f'typesetting-{_k}-1.png', _box, _para + [_SETSIGNS.get(_k, _SIGNS), _ALPHA])]

# Scans read through a correction: SHEAR un-slants an italic page (x + s*y) so its letters stand apart; OPEN
# closes the small breaks in a faint print (a grey opening of k px)
SHEAR = {'typesetting-boldfaceitalic-1.png': 0.32}
# The smallest piece of ink kept as part of a character, in pixels, where the usual 15 is too much: Text's first
# page is printed so small that its i and j dots are under it
MINAREA = {'typesetting-text-1.png': 5}
# Scans stretched in one direction, read squashed back by this factor vertically (boxes are given in the scan's
# own pixels).  The Bemer memo's photocopy: its single-spaced lines are 57.4 px apart, but at its 1/32-inch units
# (9.50 px: 303.9 dpi across) a sixth of an inch is 50.65 px, so it is 13% taller than it is wide.
SCALE_Y = {'secretarial-bemer-memo-1961.jpg': 50.65 / 57.4}
OPEN = {}
# GAMMA darkens a soft page's mid-tones (g ** gamma), so thin strokes stay joined to their letters
GAMMA = {'typesetting-boldfaceitalic-1.png': 3.0, 'typesetting-boldface2-1.png': 2.0, 'typesetting-testimonial-1.png': 3.0,
         'typesetting-testimonial-3.png': 2.0, 'typesetting-secretarial-1.png': 2.0,
         'typesetting-copperplate2-1.png': 2.0}

# More pages of 'Typesetting with IBM Executive Typewriters', at other ratchet spacings and reductions: each its own
# source (<Face>Set<n>), since each is at its own scale.  Pages whose lines run together, or that are cut off,
# are left out.
TYPESET_MORE = {}
TYPESET_MORE.setdefault(_FACE['arcadia'], {})[3] = [('typesetting-arcadia-3.png', (0, 330, 2648, 1279), _set_para('at' if 'arcadia' in _AT else 'of', quotes=not 'arcadia'.startswith('copperplate')) + [_SETSIGNS.get('arcadia', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['boldface1'], {})[3] = [('typesetting-boldface1-3.png', (93, 376, 2823, 1328), _set_para('at' if 'boldface1' in _AT else 'of', quotes=not 'boldface1'.startswith('copperplate')) + [_SETSIGNS.get('boldface1', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['boldface1'], {})[4] = [('typesetting-boldface1-4.png', (71, 336, 2801, 1168), _set_para('at' if 'boldface1' in _AT else 'of', quotes=not 'boldface1'.startswith('copperplate')) + [_SETSIGNS.get('boldface1', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['boldface2'], {})[3] = [('typesetting-boldface2-3.png', (0, 298, 2592, 1021), _set_para('at' if 'boldface2' in _AT else 'of', quotes=not 'boldface2'.startswith('copperplate')) + [_SETSIGNS.get('boldface2', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['boldfaceitalic'], {})[3] = [('typesetting-boldfaceitalic-3.png', (89, 317, 2831, 1275), _set_para('at' if 'boldfaceitalic' in _AT else 'of', quotes=not 'boldfaceitalic'.startswith('copperplate')) + [_SETSIGNS.get('boldfaceitalic', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['charter'], {})[2] = [('typesetting-charter-2.png', (0, 268, 2446, 820), _set_para('at' if 'charter' in _AT else 'of', quotes=not 'charter'.startswith('copperplate')) + [_SETSIGNS.get('charter', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['charter'], {})[3] = [('typesetting-charter-3.png', (0, 305, 2192, 1243), _set_para('at' if 'charter' in _AT else 'of', quotes=not 'charter'.startswith('copperplate')) + [_SETSIGNS.get('charter', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['copperplate1'], {})[2] = [('typesetting-copperplate1-2.png', (0, 280, 2558, 814), _set_para('at' if 'copperplate1' in _AT else 'of', quotes=not 'copperplate1'.startswith('copperplate')) + [_SETSIGNS.get('copperplate1', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['copperplate1'], {})[3] = [('typesetting-copperplate1-3.png', (0, 309, 2534, 1472), _set_para('at' if 'copperplate1' in _AT else 'of', quotes=not 'copperplate1'.startswith('copperplate')) + [_SETSIGNS.get('copperplate1', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['copperplate2'], {})[2] = [('typesetting-copperplate2-2.png', (0, 303, 2576, 843), _set_para('at' if 'copperplate2' in _AT else 'of', quotes=not 'copperplate2'.startswith('copperplate')) + [_SETSIGNS.get('copperplate2', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['copperplate2'], {})[3] = [('typesetting-copperplate2-3.png', (0, 353, 2604, 1278), _set_para('at' if 'copperplate2' in _AT else 'of', quotes=not 'copperplate2'.startswith('copperplate')) + [_SETSIGNS.get('copperplate2', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['directory'], {})[2] = [('typesetting-directory-2.png', (62, 416, 1719, 1676), _set_para('at' if 'directory' in _AT else 'of', quotes=not 'directory'.startswith('copperplate')) + [_SETSIGNS.get('directory', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['directory'], {})[3] = [('typesetting-directory-3.png', (103, 423, 2807, 1517), _set_para('at' if 'directory' in _AT else 'of', quotes=not 'directory'.startswith('copperplate')) + [_SETSIGNS.get('directory', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['documentary'], {})[2] = [('typesetting-documentary-2.png', (69, 311, 2784, 1258), _set_para('at' if 'documentary' in _AT else 'of', quotes=not 'documentary'.startswith('copperplate')) + [_SETSIGNS.get('documentary', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['documentary'], {})[3] = [('typesetting-documentary-3.png', (69, 322, 2784, 1267), _set_para('at' if 'documentary' in _AT else 'of', quotes=not 'documentary'.startswith('copperplate')) + [_SETSIGNS.get('documentary', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['midcentury'], {})[3] = [('typesetting-midcentury-3.png', (0, 281, 2455, 1379), _set_para('at' if 'midcentury' in _AT else 'of', quotes=not 'midcentury'.startswith('copperplate')) + [_SETSIGNS.get('midcentury', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['modern'], {})[3] = [('typesetting-modern-3.png', (26, 391, 2735, 1538), _set_para('at' if 'modern' in _AT else 'of', quotes=not 'modern'.startswith('copperplate')) + [_SETSIGNS.get('modern', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['patron'], {})[3] = [('typesetting-patron-3.png', (0, 268, 2579, 1191), _set_para('at' if 'patron' in _AT else 'of', quotes=not 'patron'.startswith('copperplate')) + [_SETSIGNS.get('patron', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['registry'], {})[3] = [('typesetting-registry-3.png', (13, 277, 2552, 1232), _set_para('at' if 'registry' in _AT else 'of', quotes=not 'registry'.startswith('copperplate')) + [_SETSIGNS.get('registry', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['secretarial'], {})[2] = [('typesetting-secretarial-2.png', (89, 298, 2804, 1208), _set_para('at' if 'secretarial' in _AT else 'of', quotes=not 'secretarial'.startswith('copperplate')) + [_SETSIGNS.get('secretarial', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['secretarial'], {})[3] = [('typesetting-secretarial-3.png', (65, 319, 2788, 1317), _set_para('at' if 'secretarial' in _AT else 'of', quotes=not 'secretarial'.startswith('copperplate')) + [_SETSIGNS.get('secretarial', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['testimonial'], {})[3] = [('typesetting-testimonial-3.png', (98, 0, 2807, 1134), _set_para('at' if 'testimonial' in _AT else 'of', quotes=not 'testimonial'.startswith('copperplate')) + [_SETSIGNS.get('testimonial', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['text'], {})[3] = [('typesetting-text-3.png', (0, 331, 2596, 1271), _set_para('at' if 'text' in _AT else 'of', quotes=not 'text'.startswith('copperplate')) + [_SETSIGNS.get('text', _SIGNS), _ALPHA])]
TYPESET_MORE.setdefault(_FACE['text'], {})[4] = [('typesetting-text-4.png', (0, 426, 2418, 1708), _set_para('at' if 'text' in _AT else 'of', quotes=not 'text'.startswith('copperplate')) + [_SETSIGNS.get('text', _SIGNS), _ALPHA])]
# characters of a page that read wrong and are left out: Directory's first page prints its % in pieces that
# merge with the 0 and the ‡ beside it
TYPESET_DROP = {'DirectorySet': '%‡O',      # (its O is worn away at the lower left; its third page's isn't)
                'DirectorySet2': '%‡'}
# ... and signs read with a neighbour joined to them, cut free at a column of their crop (tools/read.py): a
# column n clears what is left of it, -n what is right of it.  The whole % of Directory's third page touches the
# 0 before it; its first and second pages' 0 carry a piece of the % after it
SET_CUT = {'DirectorySet3': {'%': 45}, 'DirectorySet': {'0': -41}, 'DirectorySet2': {'0': -30}}

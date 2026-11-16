"""Where every face's text is on the scans.

A face's block is (scan, (x0, x1, y0, y1), pitch, lines): the box in pixels of the scan between the rules above
and below it, the face's pitch (10 or 12 characters to the inch) and the text of its lines in order.  In a
text, '·' marks a character that is read but not used (a figure of another version of the face, a sign the
face has twice).  Spaces don't need to be exact: the reader finds each word's cells from where its ink is.
"""

SYM = '!@#$%¢&*()-_=+½¼?/"\':;,.'
UC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LC = 'abcdefghijklmnopqrstuvwxyz'
FIG = '1234567890'

def para(*lines, lower=LC, symbols=SYM):
    return list(lines) + [UC + ' ' + symbols, lower + ' ' + FIG]

# "IBM Selectric Typewriter Type Styles", 1972: archive.org ibm-selectric-typewriter-type-styles, pages 3, 4
# and 6 (scans/selectric-a-0003.jp2 ...).  About 595 dpi.
A3, A4, A6 = 'selectric-a-0003.jp2', 'selectric-a-0004.jp2', 'selectric-a-0006.jp2'
X = (1120, 5050)
FACES = {
    'Advocate': [(A3, X + (1243, 1861), 10, para(
        'IBM ADVOCATE Type is an open spaced square-serif design.',
        'It is well suited to all correspondence needs and is also',
        'available in a Puerto Rican version.'))],
    'BookfaceAcademic72': [(A3, X + (1861, 2458), 10, para(
        'IBM BOOKFACE ACADEMIC 72 Type is similar to the Bookface',
        'Academic type style offered with the IBM Model D Type-',
        'writer. It is also available in an accounting version.'))],
    'Courier72': [(A3, X + (2458, 3094), 10, para(
        'IBM COURIER 72 Type is a square-serif design in the Pica',
        'family of type styles. This type style is also available in',
        'a legal, court reporter and Puerto Rican version.'))],
    'Delegate': [(A3, X + (3094, 3725), 10, para(
        'IBM DELEGATE Type is a weighted type conveying the feeling',
        'of printed material. It is ideal for text copy and similar',
        'jobs. It is also available in a Puerto Rican version.'))],
    'Pica72': [(A3, X + (3725, 4341), 10, para(
        'IBM PICA 72 Type is similar to the Pica type styles offered',
        'with the IBM Model D Typewriter. It is also available in',
        'a legal, court reporter and chemical version.'))],
    'PrestigePica72': [(A3, X + (4341, 4969), 10, para(
        'IBM PRESTIGE PICA 72 Type is similar to Prestige Pica type',
        'style offered with the IBM Model D Typewriter. It is also',
        'available in a legal, accounting and Puerto Rican version.'))],
    'Adjutant': [(A3, X + (4969, 5600), 12, para(
        'IBM ADJUTANT Type is a weighted serif type design that conveys the',
        'feeling of printed material. It is recommended for the preparation of',
        'text copy and other similar typing applications.'))],
    'Artisan12': [(A3, X + (5600, 6250), 12, para(
        'IBM ARTISAN 12 (72) Type is a sans-serif design. It is well suited',
        'to typed matter which requires maximum use of typing space. Artisan is',
        'also available in a Puerto Rican version.'))],
    'Courier12': [(A4, X + (1262, 1873), 12, para(
        'IBM COURIER 12 Type is a square-serif design in the Elite family',
        'of type styles and is similar to the Courier 72 element. It is well',
        'suited for a wide variety of typing applications.'))],
    'Courier12Italic': [(A4, X + (1873, 2470), 12, para(
        'IBM COURIER 12 ITALIC Type complements the Courier 12 type style.',
        'It may be used alone or in combination with other 12-pitch type',
        'styles for a wide variety of typing applications.'))],
    'Elite72': [(A4, X + (2470, 3110), 12, para(
        'IBM ELITE 72 Type is similar to the Elite type styles offered with the',
        'IBM Model D Typewriter. It is also available with special characters for',
        'library work and in a tri-lingual version for foreign language typing.'))],
    'LargeElite72': [(A4, X + (3110, 3734), 12, para(
        'IBM LARGE ELITE 72 Type is similar to the Large Elite style',
        'offered with the IBM Model D Typewriter. Its clean, crisp appearance',
        'makes it suitable for a wide variety of typing applications.'))],
    'LetterGothic': [(A4, X + (3734, 4327), 12, para(
        'IBM LETTER GOTHIC Type is a distinctive sans-serif design. It is',
        'ideal for invoices, statements and other typing applications where bold-',
        'ness is desired. It is also available in a Puerto Rican version.'))],
    'PrestigeElite72': [(A4, X + (4327, 4959), 12, para(
        'IBM PRESTIGE ELITE 72 Type is a weighted serif type similar to the',
        'Prestige Elite styles offered with the IBM Model D Typewriter. It is',
        'also available with legal, chemical and French/English characters.'))],
    'Scribe': [(A4, X + (4959, 5594), 12, para(
        'IBM SCRIBE Type is a modern square-serif design in the Elite family',
        'of type styles. It is ideally suited for the preparation of reports and',
        'correspondence. Scribe is also available in a Puerto Rican version.'))],
    # capitals only: its "lower case" keys type capitals too.  The paragraph's figures are the pica-numeral
    # version's, and its slashed zero another version's: not used.
    'Manifold72': [(A6, X + (1261, 1879), 10, [
        'IBM MANIFOLD 72 TYPE IS A SANS-SERIF TYPE FOR BILLING AND',
        'FORMS PREPARATION. IT IS ALSO AVAILABLE IN A PICA NUMERAL',
        'VERSION (··········) AND A CANCELLED ZERO VERSION (·).',
        UC + ' ' + SYM, FIG])],
    # the lower case is small capitals, typed as the paragraph's lower case
    'Orator': [(A6, X + (1879, 2504), 10, para(
        'IBM ORATOR Type is a large, sans-serif type style. Its',
        'bold, legible characters provide impact and command',
        'attention. Orator is recommended for speeches and charts.'))],
    'DualGothic': [(A6, X + (2504, 3121), 12, para(
        'IBM DUAL GOTHIC Type is a sans-serif type similar to Dual Basic',
        'Gothic type style offered with the IBM Model D Typewriter. Its crisp',
        'appearance adds legibility to all types of copy preparation.'))],
    'LightItalic': [(A6, X + (3121, 3746), 12, para(
        'IBM LIGHT ITALIC Type is a "fine-line" italic style that may be',
        'used alone or in combination with Pica or Elite type styles to add',
        'impact and emphasis to a wide variety of typing applications.'))],
    'Script': [(A6, X + (3746, 4364), 12, para(
        'IBM SCRIPT Type is a special purpose type style that simulates hand-',
        'writing. It provides the look of a personal note and a change of pace',
        'and emphasis. Script is also available in a Puerto Rican version.'))],
}

# The same brochure, a later printing: archive.org ibm-selectric-typewriter-type-styles-brochure, pages 2, 3 and
# 5 (scans/selectric-c-0002.jp2 ...).  The same faces and texts but "Latin American" for "Puerto Rican", and the
# footnote marks printed black: read, and not used ('·').
C2, C3, C5 = 'selectric-c-0002.jp2', 'selectric-c-0003.jp2', 'selectric-c-0005.jp2'
XC = (1250, 5080)
SECOND = {
    'Advocate': (C2, (1231, 1850), {'available in a Puerto Rican version.': 'available in a Latin American version.·'}),
    'BookfaceAcademic72': (C2, (1850, 2445), {'accounting version.': 'accounting version.·'}),
    'Courier72': (C2, (2445, 3083), {'and Puerto Rican version.': 'and Latin American version.·'}),
    'Delegate': (C2, (3083, 3715), {'in a Puerto Rican version.': 'in a Latin American version.·'}),
    'Pica72': (C2, (3715, 4335), {'chemical version.': 'chemical version.·'}),
    'PrestigePica72': (C2, (4335, 4962), {'and Puerto Rican version.': 'and Latin American version.·'}),
    'Adjutant': (C2, (4962, 5594), {}),
    'Artisan12': (C2, (5594, 6250), {'in a Puerto Rican version.': 'in a Latin American version.·'}),
    'Courier12': (C3, (1242, 1856), {}),
    'Courier12Italic': (C3, (1856, 2448), {}),
    'Elite72': (C3, (2448, 3089), {'language typing.': 'language typing.·'}),
    'LargeElite72': (C3, (3089, 3725), {}),
    'LetterGothic': (C3, (3725, 4321), {'in a Puerto Rican version.': 'in a Latin American version.·'}),
    'PrestigeElite72': (C3, (4321, 4954), {'English characters.': 'English characters.·'}),
    'Scribe': (C3, (4954, 5585), {'in a Puerto Rican version.': 'in a Latin American version.·'}),
    'Manifold72': (C5, (1229, 1849), {}),
    'Orator': (C5, (1849, 2478), {}),
    'DualGothic': (C5, (2478, 3095), {}),
    'LightItalic': (C5, (3095, 3721), {}),
    'Script': (C5, (3721, 4342), {'in a Puerto Rican version.': 'in a Latin American version.··'}),
}
for _f, (_scan, (_y0, _y1), _subs) in SECOND.items():
    _, _, _pitch, _lines = FACES[_f][0]
    _new = []
    for _l in _lines:
        for _a, _b in _subs.items(): _l = _l.replace(_a, _b)
        _new.append(_l)
    FACES[_f].append((_scan, XC + (_y0, _y1), _pitch, _new))

# ------------------------------------------------------------------------------------------------ OCR faces
# Page 5 of the first printing, page 4 of the second.  ANSI is OCR-A (ANSI X3.17, font A, size 1): its
# symbols are OCR-A's own, mapped to the ASCII keys OCR-A puts them on (hook ⑁ for !, chair ⑂ for @, fork ⑃ for
# #, the long bar for |, the long dash for _, the block █ for ^).  AN3/360's lower case is small capitals.
A5, C4 = 'selectric-a-0005.jp2', 'selectric-c-0004.jp2'
OCR_SYM = {
    # the specimen shows its : and ; the wrong way round (the two-dot colon on the ; key): put right here
    'ANSIOCR': '⑁⑂⑃$%|&*{}-_=+█/?\'";:.¬',
    'AN3360': '‡@#$%¤&*()-_=+<>?/°\':;,.',
}
FACES['ANSIOCR'] = [(A5, X + (1250, 1869), 10, para(
    'IBM ANSI Type meets the American National Standards Institute',
    'specification for A font, size 1. It is available in corres-',
    'pondence or keypunch simulator keyboard arrangements.', symbols=OCR_SYM['ANSIOCR'])),
                    (C4, XC + (1203, 1822), 10, para(
    'IBM ANSI Type meets the American National Standards Institute',
    'specification for A font, size 1. It is available in corres-',
    'pondence or keypunch simulator keyboard arrangements.', symbols=OCR_SYM['ANSIOCR']))]
_AN3 = ['IBM AN3/360 Type style lower case, alphabetic characters,',
        'numerals and symbols are designed to match .079 inch size',
        'AN3 style popular on IBM System/360 chain/train printers.']
FACES['AN3360'] = [(A5, X + (1869, 2494), 10, para(*_AN3, symbols=OCR_SYM['AN3360'])),
                   (C4, XC + (1822, 2448), 10, para(*_AN3, symbols=OCR_SYM['AN3360']))]

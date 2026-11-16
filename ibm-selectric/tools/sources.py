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

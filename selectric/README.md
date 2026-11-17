# Selectric

Digital fonts traced from the type of the **Selectric** typewriter, as IBM's type-style brochure of 1972
shows it, in two printings. Every Selectric character is the same width: 1/10 inch on a 10-pitch element, 1/12 inch on a 12-pitch
one. The fonts are monospaced to match, so text set in them lines up as it did on the machine.

![The fonts](specimen/specimen-lines.png)

| Font | Pitch | Font | Pitch |
|---|---|---|---|
| Selectric Advocate | 10 | Selectric Courier 12 | 12 |
| Selectric Bookface Academic 72 | 10 | Selectric Courier 12 Italic | 12 |
| Selectric Courier 72 | 10 | Selectric Elite 72 | 12 |
| Selectric Delegate | 10 | Selectric Large Elite 72 | 12 |
| Selectric Pica 72 | 10 | Selectric Letter Gothic | 12 |
| Selectric Prestige Pica 72 | 10 | Selectric Prestige Elite 72 | 12 |
| Selectric Manifold 72 | 10 | Selectric Scribe | 12 |
| Selectric Orator | 10 | Selectric Adjutant | 12 |
| Selectric ANSI OCR | 10 | Selectric Artisan 12 | 12 |
| Selectric AN3 360 | 10 | Selectric Dual Gothic | 12 |
| Selectric Printing and Publishing 2 | 10 | | |
| | | Selectric Light Italic | 12 |
| | | Selectric Script | 12 |

The files are `fonts/otf/Selectric<Face>-Regular.otf` (cubic outlines, unhinted) and `fonts/ttf/Selectric<Face>-Regular.ttf`
(quadratic, hinted with [ttfautohint](https://freetype.org/ttfautohint/) at 8–50 px), with `-Italic` for Courier
12 Italic, Light Italic and Script. The text faces are at version 1.002 (Bookface Academic 72 and Large Elite 72 at 1.003), ANSI OCR at 1.002 and
AN3 360 at 1.001. The sources are listed in
[`scans/README.md`](scans/README.md).

## Size and spacing

Every character is 600 font units wide, at 1000 units to the em. **A 10-pitch face set at 12 pt, or a 12-pitch
face at 10 pt, prints at the typewriter's own size.** The line spacing is the Selectric's single spacing, six
lines to the inch: 1000 units for a 10-pitch face, 1200 for a 12-pitch one (12 pt at 10 pt). Each character
keeps the place in its cell that the scans show.

## Character set

Each face has what its brochure line shows: A–Z, a–z, the figures, and `! @ # $ % ¢ & * ( ) - _ = + ½ ¼ ? / " '
: ; , .` (88 glyphs with the space and `.notdef`). The typographic quotes ‘ ’ “ ” map to the straight `'` and `"`.

- **Selectric Manifold 72** is capitals only; its lower-case keys type the capitals, as on the element.
- **Selectric Orator**'s lower case is small capitals, as on the element.
- No text face has `< > [ \ ] ^ ` { | } ~`: a standard Selectric element doesn't have them.
- **Selectric ANSI OCR** is OCR-A (the American National Standards Institute's font A, size 1), with its own signs in
  place of the usual ones: the hook ⑁, chair ⑂ and fork ⑃ (on `!`, `@` and `#`, as OCR-A puts them, and also at
  their own code points U+2441–2443), the long bar `|`, braces `{ }`, the solid block █ (on `^` and at U+2588), an
  upright `"` and `'`, and `¬`. It has no `( ) ¢ ½ ¼ ,`; the `-` and `_` are its short and long dashes. The
  specimen shows its `:` and `;` the wrong way round (OCR-A's two-dot colon in the `;` place); here they are swapped
  back.
- **Selectric Printing and Publishing 2** is the "Perry Font" (REI-X04), for Recognition Equipment's scanners:
  a monoline face with a hooked e and g. Its signs are `! ¶ @ $ % ⁄ & * ( ) - — { } ¤ △ ? / + = : ; , .` on the
  keys where the text faces have `!@#$%¢&*()-_=+½¼?/"':;,.`; the long dash is also on `_`. Version 1.000.
- **Selectric AN3 360** matches IBM's AN3 chain and train printer type of System/360. Its lower case is small capitals,
  like Orator's, and its signs are `‡ @ # $ % ¤ & * ( ) - _ = + < > ? / ° ' : ; , .` (no `!`, `"` or `¢`).

![Printable ASCII in each font](specimen/ascii.png)

Each face also has `specimen/compare-<Face>.png`, which shows the specimen's alphabet lines as scanned with the font
set beneath them, character for character in the same cells. Anything odd that shows in both, such as Prestige
Elite's j reaching into the i's cell or the gap between Courier 12 Italic's 7 and 8, is in the original type.

## How the fonts are made

Everything is under `tools/` and runs from this directory (`selectric/`). The scans aren't in the
repository: see [`scans/README.md`](scans/README.md) for where to get them.

```bash
python3 tools/read.py        # build/occ-<Face>.pkl: every character of every source line, in its cell
python3 tools/build.py       # fonts/otf, fonts/ttf
python3 tools/specimen.py    # specimen/
```

1. **Reading** (`read.py`, with the faces' blocks and texts in `sources.py`). Each face appears in both printings
   of the brochure (a and c in `scans/README.md`), so every character has at least two prints. Each face's block holds a
   paragraph of three lines, its capitals and signs, and its lower case and figures. The reader finds the
   lines, fits the block's pitch and each line's phase (the lattice that puts the most character centres in
   the middle of a cell), and puts every piece of ink in the cell of its centre. A piece wider than a cell
   (touching characters) is cut at the cells' edges, unless the slice is only the tail of a stroke (Script).
   The occupied cells fall into runs, which are matched to the text's words by their lengths. Each line then
   fits its own pitch and phase to its characters, and its baseline as a sloped line (the scans are a little
   skewed).
2. **Averaging and tracing** (`build.py`, `common/glyphs.py`, `common/trace.py`). Every occurrence of a
   character, measured from the centre of its cell, is scaled to font units and aligned to the others by
   phase correlation. Occurrences of the wrong size or shape are dropped, the rest averaged, and the 50 % ink
   contour traced into Bézier curves. A print is dropped if it has much less ink than the character's fullest
   print (one printing's Scribe figures are broken), if it lies far from where the others sit in their cells, or
   (from a paragraph) if it doesn't look like the character's alphabet-line print.

## Not yet done

- The signs and rarer letters have only two prints, one from each printing. Brochure b (about 1970, different
  texts) would give a third.
- The other OCR faces (AN3/360 Bold, DF-2, 915, 12L2/12F2, 1403, Printing and Publishing 2 and 3; USASI and
  Communications in brochure b) and the Symbol 10 and 12 elements aren't made yet.

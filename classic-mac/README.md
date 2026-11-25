# Classic Mac

High-resolution recreations of the bitmap fonts of the early Macintosh, each drawn on its bitmap's own metrics:
set at the bitmap's point size, every character advances by exactly the bitmap's pixels, so text set in the
recreation lines up as the bitmap font set it.

| Font | Recreates | Version | Files |
|---|---|---|---|
| Athens HD | Athens 18 (Susan Kare, 1984) | 1.004 | `fonts/otf/AthensHD-Regular.otf`, `fonts/ttf/AthensHD-Regular.ttf` |
| Chicago HD | Chicago 12 (Susan Kare, 1984) | 1.004 | `fonts/otf/ChicagoHD-Regular.otf`, `fonts/ttf/ChicagoHD-Regular.ttf` |
| Geneva HD | Geneva 12 (Susan Kare, 1984) | 1.003 | `fonts/otf/GenevaHD-Regular.otf`, `fonts/ttf/GenevaHD-Regular.ttf` |
| Monaco HD | Monaco 12 (Susan Kare, 1984) | 1.005 | `fonts/otf/MonacoHD-Regular.otf`, `fonts/ttf/MonacoHD-Regular.ttf` |
| London HD | London 18 (Susan Kare, 1984) | 1.000 | `fonts/otf/LondonHD-Regular.otf`, `fonts/ttf/LondonHD-Regular.ttf` |

Each font is in `fonts/otf/` (cubic outlines, unhinted) and `fonts/ttf/` (quadratic, hinted with
[ttfautohint](https://freetype.org/ttfautohint/) at 8–50 px).

<!-- downloads -->
## Download

**Athens HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/AthensHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/AthensHD-Regular.ttf)  
![Athens HD](specimen/fonts/AthensHD-Regular.png)

**Chicago HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/ChicagoHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/ChicagoHD-Regular.ttf)  
![Chicago HD](specimen/fonts/ChicagoHD-Regular.png)

**Geneva HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/GenevaHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/GenevaHD-Regular.ttf)  
![Geneva HD](specimen/fonts/GenevaHD-Regular.png)

**London HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/LondonHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/LondonHD-Regular.ttf)  
![London HD](specimen/fonts/LondonHD-Regular.png)

**Monaco HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/MonacoHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/MonacoHD-Regular.ttf)  
![Monaco HD](specimen/fonts/MonacoHD-Regular.png)

<!-- /downloads -->

## Size and metrics

One bitmap pixel is 50 font units, and the em is the bitmap's point size in pixels, so each recreation set at
its bitmap's point size is the bitmap's size on a 72-dpi Mac screen:

| Font | Set at | Em | Ascender | Descender | Lines apart |
|---|---|---|---|---|---|
| Athens HD | 18 pt | 18 px, 900 units | 18 px, 900 units | 4 px, 200 units | 22 px |
| Chicago HD | 12 pt | 12 px, 600 units | 12 px, 600 units | 3 px, 150 units | 15 px |
| Geneva HD | 12 pt | 12 px, 600 units | 12 px, 600 units | 3 px, 150 units | 15 px |
| Monaco HD | 12 pt | 12 px, 600 units | 12 px, 600 units | 3 px, 150 units | 15 px |
| London HD | 18 pt | 18 px, 900 units | 17 px, 850 units | 3 px, 150 units | 20 px |

Every advance width is the bitmap's, in whole pixels, and the line gap is none. There is no kerning, as the bitmaps
had none. Monaco HD is monospaced, and marked so: every character advances 7 pixels, 350 units. (The bitmap's `©` and `®`
advance 6; here they advance 7 like the rest, with their ink where the bitmap has it.)

Traced at their 50 % contour, the strokes come out about the bitmap's width (Chicago's and Athens's stems are 2
pixels, London's 2 and its hairlines 1, the others' 1), but with a little less ink than the bitmap: the pixels'
corners are rounded and the steps of diagonals cut. Each font's strokes are thickened by as many units a side as give it its bitmap's ink,
over A–Z, a–z and 0–9 (`LIGHTEN` in `tools/build.py`; `tools/weight.py` measures it): Athens HD and Chicago HD
by 1, Geneva HD by 2, Monaco HD by 3, London HD by 5 (its many hairlines and points lose the most), each then
within 2 % of its bitmap's ink.
`specimen/line-<font>.png` ([Athens](specimen/line-athens.png), [Chicago](specimen/line-chicago.png),
[Geneva](specimen/line-geneva.png), [Monaco](specimen/line-monaco.png), [London](specimen/line-london.png)) sets the
alphabets and figures on one
line in the bitmap and in the HD font, to compare.

## Character set

Athens HD has every character of the bitmap: ASCII and the upper half of Mac OS Roman as Athens has it (the
accented letters, `† ° ¢ £ • ß ® © ™ ´ ¨ Æ Ø ¥ ª º æ ø ¿ ¡ « » … À Ã Õ Œ œ – — “ ” ‘ ’ ◊ ÿ`). Athens's `Ÿ`
(Mac OS Roman 0xD9) is a pair of paw prints, and stays so, at U+0178. The bitmap's other Mac OS Roman places
(`± ≤ ≥ µ ∂ ∑ ∏ π ∫ Ω √ ƒ ≈ ∆ ≠ ∞` and the like) are empty in Athens, so they are here too.

Chicago HD has more of Mac OS Roman: Athens's characters but its paw prints, and `§ ¶ ≠ ∞ ± ≤ ≥ µ ∂ ∑ ∏ π ∫ Ω ¬ √ ƒ
≈ ∆ ÷`.
Chicago's four menu symbols, at the control codes 0x11–0x14 on the Mac, are at their Unicode places: ⌘ U+2318,
✓ U+2713, ◆ U+25C6, and the Apple logo at U+F8FF, in the Private Use Area, where Apple's own fonts put it. The
logo is Apple's trademark. (The OS X `.dfont` keeps the four in Mac OS Roman's 0xD9–0xDC, the places of
`Ÿ ⁄ ¤ ‹`, which Chicago doesn't otherwise have.) Ω is both U+03A9 and U+2126, which Mac OS Roman's 0xBD
stood for.

Geneva HD and Monaco HD have Chicago's characters, but in place of its menu symbols, a joke of Susan Kare's at
`Ÿ` (U+0178), as Athens has its paw prints: Geneva's is a rabbit, Monaco's a candle. Ω is at both U+03A9 and
U+2126 wherever the bitmap has it.

London HD has ASCII but `` < > ^ ` ~ ``, which are in the bitmap but not on the upscaled sheet, and `– — ‘ ’ “ ”`; at `Ÿ`
(U+0178), as the others have their jokes, an ornament.

Monaco's `©` and `®` are cut off on the left, in the bitmap as here: the bitmap has the right-hand part of
each circle only.

`specimen/compare-<font>.png` ([Athens](specimen/compare-athens.png), [Chicago](specimen/compare-chicago.png),
[Geneva](specimen/compare-geneva.png), [Monaco](specimen/compare-monaco.png), [London](specimen/compare-london.png))
sets every character over its bitmap (pink), with its advance width
underlined.

## How the fonts are made

Everything is under `tools/` and runs from this directory (`classic-mac/`). The sources are in `scans/`, and
[`scans/README.md`](scans/README.md) says where each came from.

It needs Python 3 with the packages in `requirements.txt`, and the DejaVu fonts (`fonts-dejavu` on Debian and
Ubuntu) at `/usr/share/fonts/truetype/dejavu/` for the specimen's label.

```bash
pip install -r requirements.txt
python3 tools/build.py       # fonts/otf, fonts/ttf (about a minute)
python3 tools/specimen.py    # specimen/
python3 tools/weight.py      # each font's ink against its bitmap's
python3 ../scripts/font_links.py   # the download lists and their specimen lines
```

1. **The sheet.** `scans/<font>-upscaled.png` is the bitmap font's characters laid out in lines, upscaled to
   36 times its pixels: first to 6 times by
   [bitmap-upscaling](https://github.com/e-n-f/bitmap-upscaling) (each character averaged over the many phases it
   was rendered at), then 6 times again by an AI upscaler. `scans/<font>-glyphs.json`, from the same project,
   says where each character is on the sheet: its cell, its origin (pen position on the baseline) and the
   bitmap's advance, in the coordinates of the 6-times sheet.
2. **Tracing** (`tools/build.py`, with `common/trace.py`). Each character's ink is cut from its cell, with two
   pixels round it for a character that reaches a little past its cell, keeping the pieces of ink that lie mostly
   inside the cell (a neighbour's can reach into it), and no further across than halfway to its neighbours on the
   line, for characters that touch on the sheet. It is scaled to font units and traced at its 50 % contour.
3. **Placing.** Each outline is placed by its origin, and given the bitmap's advance. The bitmap font itself
   (`scans/*.dfont`, read by `tools/bitmap.py`) gives the space's width and the
   ascender and descender.
4. **Accents.** Where the sheet has a wrong accent over a letter (Geneva's `á à ä é ï`, Monaco's `à ë`: `REACCENT` in
   `tools/build.py`), the accent is taken from another letter whose bitmap has the same accent, pixel for pixel,
   and set where the bitmap has it.

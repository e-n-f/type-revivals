# Classic Mac

High-resolution recreations of the bitmap fonts of the early Macintosh, each drawn on its bitmap's own metrics:
set at the bitmap's point size, every character advances by exactly the bitmap's pixels, so text set in the
recreation lines up as the bitmap font set it.

| Font | Recreates | Version | Files |
|---|---|---|---|
| Athens HD | Athens 18 (Susan Kare, 1984) | 1.000 | `fonts/otf/AthensHD-Regular.otf`, `fonts/ttf/AthensHD-Regular.ttf` |
| Chicago HD | Chicago 12 (Susan Kare, 1984) | 1.000 | `fonts/otf/ChicagoHD-Regular.otf`, `fonts/ttf/ChicagoHD-Regular.ttf` |

Each font is in `fonts/otf/` (cubic outlines, unhinted) and `fonts/ttf/` (quadratic, hinted with
[ttfautohint](https://freetype.org/ttfautohint/) at 8–50 px).

<!-- downloads -->
## Download

**Athens HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/AthensHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/AthensHD-Regular.ttf)  
![Athens HD](specimen/fonts/AthensHD-Regular.png)

**Chicago HD**: [OTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/otf/ChicagoHD-Regular.otf) · [TTF](https://raw.githubusercontent.com/e-n-f/type-revivals/main/classic-mac/fonts/ttf/ChicagoHD-Regular.ttf)  
![Chicago HD](specimen/fonts/ChicagoHD-Regular.png)

<!-- /downloads -->

## Size and metrics

One bitmap pixel is 50 font units, and the em is the bitmap's point size in pixels, so each recreation set at
its bitmap's point size is the bitmap's size on a 72-dpi Mac screen:

| Font | Set at | Em | Ascender | Descender | Lines apart |
|---|---|---|---|---|---|
| Athens HD | 18 pt | 18 px, 900 units | 18 px, 900 units | 4 px, 200 units | 22 px |
| Chicago HD | 12 pt | 12 px, 600 units | 12 px, 600 units | 3 px, 150 units | 15 px |

Every advance width is the bitmap's, in whole pixels, and the line gap is none. There is no kerning, as the bitmaps
had none.

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

[`specimen/compare-athens.png`](specimen/compare-athens.png) and
[`specimen/compare-chicago.png`](specimen/compare-chicago.png) set every character over its bitmap (pink), with
its advance width underlined.

## How the fonts are made

Everything is under `tools/` and runs from this directory (`classic-mac/`). The sources are in `scans/`, and
[`scans/README.md`](scans/README.md) says where each came from.

It needs Python 3 with the packages in `requirements.txt`, and the DejaVu fonts (`fonts-dejavu` on Debian and
Ubuntu) at `/usr/share/fonts/truetype/dejavu/` for the specimen's label.

```bash
pip install -r requirements.txt
python3 tools/build.py       # fonts/otf, fonts/ttf (about a minute)
python3 tools/specimen.py    # specimen/
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
   inside the cell (a neighbour's can reach into it). It is scaled to font units and traced at its 50 % contour.
3. **Placing.** Each outline is placed by its origin, and given the bitmap's advance. The bitmap font itself
   (`scans/Athens_22.dfont`, `scans/Chicago_15.dfont`, read by `tools/bitmap.py`) gives the space's width and the
   ascender and descender.

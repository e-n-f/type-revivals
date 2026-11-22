# Scans

The sources for the classic Mac recreations, kept here so that the fonts can be rebuilt from them.

| File | What it is | Used for |
|---|---|---|
| `Athens_22.dfont` | Athens, the 18-point bitmap font of the Macintosh (Susan Kare, 1984), as converted for Mac OS X: an `sfnt` resource with one strike of 1-bit glyphs at 22 px (`bhed`, `bloc`, `bdat`), from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | The space's width, the ascender and descender, and the check of every outline against its pixels (`tools/bitmap.py`, `specimen/compare-athens.png`) |
| `athens-glyphs.json` | Where each character is on the sheet: its cell, origin and the bitmap's advance, in the coordinates of the 6-times sheet. From [bitmap-upscaling](https://github.com/e-n-f/bitmap-upscaling) (branch `upscaling-experiments`, `font-specimens/phase-grid/pruna-picks-mac/Athens_18_sq_ls2_mac_6x_glyphs.json`) | Cutting out and placing every character |
| `athens-upscaled.png` | The sheet of Athens's characters, upscaled to 36 times the bitmap's pixels (5724 × 14148): bitmap-upscaling's 6-times sheet, upscaled 6 times again by an AI upscaler on Replicate. Kept as 8-bit grey (the upscaler's output was RGB, its three channels within one level of each other) | The outlines |
| `Chicago_15.dfont` | Chicago, the 12-point bitmap font of the Macintosh's menus (Susan Kare, 1984), as converted for Mac OS X: one strike at 15 px, from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | As Athens's |
| `chicago-glyphs.json` | As Athens's: from bitmap-upscaling's `Chicago_12_sq_ls2_mac_6x_glyphs.json` | As Athens's |
| `chicago-upscaled.png` | As Athens's, for Chicago (4464 × 11592) | As Athens's |
| `Geneva_15.dfont` | Geneva, the 12-point bitmap font (Susan Kare, 1984), as converted for Mac OS X: one strike at 15 px, from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | As Athens's |
| `geneva-glyphs.json` | As Athens's: from bitmap-upscaling's `Geneva_12_sq_ls2_mac_6x_glyphs.json` | As Athens's |
| `geneva-upscaled.png` | As Athens's, for Geneva (4032 × 10872) | As Athens's |
| `NewYork_15.dfont` | New York, the 12-point bitmap font (Susan Kare, 1984), as converted for Mac OS X: one strike at 15 px, from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | As Athens's |
| `newyork-glyphs.json` | As Athens's: from bitmap-upscaling's `NewYork_12_sq_ls2_mac_6x_glyphs.json` | As Athens's |
| `newyork-upscaled.png` | As Athens's, for New York (4140 × 10152) | As Athens's |
| `Monaco_15.dfont` | Monaco, the 12-point monospaced bitmap font (Susan Kare, 1984), as converted for Mac OS X: one strike at 15 px, from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | As Athens's |
| `monaco-glyphs.json` | As Athens's: from bitmap-upscaling's `Monaco_12_sq_ls2_mac_6x_glyphs.json` | As Athens's |
| `monaco-upscaled.png` | Monaco's sheet at 6 times the bitmap's pixels only (576 × 1812): bitmap-upscaling's `Monaco_12_sq_ls2_mac_6x_best_grey.png` itself, not upscaled again. Kept as 8-bit grey (it was grey with an opaque alpha channel) | As Athens's |

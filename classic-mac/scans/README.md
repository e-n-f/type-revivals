# Scans

The sources for the classic Mac recreations, kept here so that the fonts can be rebuilt from them.

| File | What it is | Used for |
|---|---|---|
| `Athens_22.dfont` | Athens, the 18-point bitmap font of the Macintosh (Susan Kare, 1984), as converted for Mac OS X: an `sfnt` resource with one strike of 1-bit glyphs at 22 px (`bhed`, `bloc`, `bdat`), from [macfonts](https://github.com/JohnDDuncanIII/macfonts) (`Macintosh OS 1-6/OS X/`) | The space's width, the ascender and descender, and the check of every outline against its pixels (`tools/bitmap.py`, `specimen/compare-athens.png`) |
| `athens-glyphs.json` | Where each character is on the sheet: its cell, origin and the bitmap's advance, in the coordinates of the 6-times sheet. From [bitmap-upscaling](https://github.com/e-n-f/bitmap-upscaling) (branch `upscaling-experiments`, `font-specimens/phase-grid/pruna-picks-mac/Athens_18_sq_ls2_mac_6x_glyphs.json`) | Cutting out and placing every character |
| `athens-upscaled.png` | The sheet of Athens's characters, upscaled to 36 times the bitmap's pixels (5724 × 14148): bitmap-upscaling's 6-times sheet, upscaled 6 times again by an AI upscaler on Replicate. Kept as 8-bit grey (the upscaler's output was RGB, its three channels within one level of each other) | The outlines |

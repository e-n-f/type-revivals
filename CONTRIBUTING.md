# Contributing

## Font versions

**Every change to a font file raises that font's version number.** Font managers and operating systems
identify an installed font by its name and version. A changed font with an unchanged version is treated as a
duplicate of the installed one, and users keep the old outlines or get a mix of both.

- Raise the version of each font whose file changes, and only those fonts. In `metal-pal/`, the versions are
  in `VERSIONS` near the top of `tools/build.py`. Each revival keeps its own build script and version setting.
- Use three decimal places, adding 0.001 for each change (1.000, 1.001, 1.002, …). The build writes the
  version to both `head.fontRevision` and the name table's version string (name ID 5).
- Don't commit a font that you rebuilt without changing it: it differs only in its build timestamp. Restore it
  with `git checkout main -- <file>`.

`scripts/check_font_versions.py` checks this against a base revision (default `origin/main`):

```bash
python3 scripts/check_font_versions.py origin/main
```

It runs on every pull request that touches a `.otf` or `.ttf` file (`.github/workflows/font-versions.yml`).
It fails if a changed font's version isn't higher than the base's, if the two version fields disagree, or if a
font differs only in its timestamp.

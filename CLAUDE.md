# Notes for Claude

- Follow `CONTRIBUTING.md`. In particular, whenever a change alters a font file, raise that font's version
  (for Metal Pal: `VERSIONS` in `metal-pal/tools/build.py`), rebuild it, and run
  `python3 scripts/check_font_versions.py origin/main` before committing.
- Commit only the fonts that actually changed. A rebuilt font that differs only in its timestamp should be
  restored from `main`.

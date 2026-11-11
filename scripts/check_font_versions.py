#!/usr/bin/env python3
"""Check that every font file changed since a base revision has a higher version number.

    python3 scripts/check_font_versions.py [base]      # base defaults to origin/main

For each .otf and .ttf under the repository that differs from the base:
  - a new file passes;
  - a file whose glyphs, metrics or other data changed must have a higher head.fontRevision, and a
    name-table version string (ID 5) that agrees with it;
  - a file that differs only in its build timestamp fails too: it shouldn't be committed.
Exit status 1 if any file fails.
"""
import io, re, subprocess, sys
from fontTools.ttLib import TTFont

IGNORE_HEAD = {'modified', 'checkSumAdjustment', 'fontRevision', 'created'}
VERSIONED_NAMES = {3, 5}       # unique identifier and version string carry the version

def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout

def name_version(f):
    rec = f['name'].getName(5, 3, 1, 0x409) or f['name'].getName(5, 1, 0, 0)
    m = re.search(r'Version (\d+\.\d+)', str(rec)) if rec else None
    return float(m.group(1)) if m else None

def content_differs(a, b):
    """True if anything but the version and timestamps differs"""
    tags = set(a.reader.keys()) | set(b.reader.keys())
    for t in sorted(tags):
        if t not in a.reader or t not in b.reader: return True
        if t == 'head':
            ha, hb = a['head'].__dict__, b['head'].__dict__
            if any(ha.get(k) != hb.get(k) for k in set(ha) | set(hb) if k not in IGNORE_HEAD and k != 'tableTag'):
                return True
        elif t == 'name':
            ra = {(r.nameID, r.platformID, r.platEncID, r.langID): r.toUnicode() for r in a['name'].names
                  if r.nameID not in VERSIONED_NAMES}
            rb = {(r.nameID, r.platformID, r.platEncID, r.langID): r.toUnicode() for r in b['name'].names
                  if r.nameID not in VERSIONED_NAMES}
            if ra != rb: return True
        elif t in ('CFF ', 'CFF2'):
            # the CFF top dict has its own version; compare the charstrings and the rest of the font
            ca, cb = a[t].cff, b[t].cff
            ga, gb = a.getGlyphSet(), b.getGlyphSet()
            if a.getGlyphOrder() != b.getGlyphOrder(): return True
            from fontTools.pens.recordingPen import RecordingPen
            for n in a.getGlyphOrder():
                pa, pb = RecordingPen(), RecordingPen(); ga[n].draw(pa); gb[n].draw(pb)
                if pa.value != pb.value or ga[n].width != gb[n].width: return True
        elif a.reader[t] != b.reader[t]:
            return True
    return False

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'origin/main'
    changed = git('diff', '--name-only', '--diff-filter=AM', f'{base}...HEAD').decode().split()
    fonts = [p for p in changed if p.lower().endswith(('.otf', '.ttf'))]
    failures = 0
    for p in fonts:
        new = TTFont(p)
        rev, nv = round(new['head'].fontRevision, 3), name_version(new)
        if nv is not None and abs(nv - rev) > 0.0005:
            print(f'FAIL {p}: head.fontRevision {rev:.3f} but name table says Version {nv:.3f}'); failures += 1
        try:
            old = TTFont(io.BytesIO(git('show', f'{base}:{p}')))
        except subprocess.CalledProcessError:
            print(f'ok   {p}: new file, version {rev:.3f}'); continue
        old_rev = round(old['head'].fontRevision, 3)
        if not content_differs(old, new):
            print(f'FAIL {p}: only the build timestamp changed; restore it with git checkout {base} -- {p}')
            failures += 1
        elif rev <= old_rev:
            print(f'FAIL {p}: changed, but its version {rev:.3f} is not above {old_rev:.3f}')
            failures += 1
        else:
            print(f'ok   {p}: {old_rev:.3f} -> {rev:.3f}')
    if not fonts: print('no font files changed')
    sys.exit(1 if failures else 0)

if __name__ == '__main__':
    main()

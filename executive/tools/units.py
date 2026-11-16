"""Unit widths: the typewriter moves the carriage by a whole number of units for each character.

Within a word the left edges of two neighbours are  w(first) + l(second) - l(first)  apart, where w is the
first character's width and l a character's left side bearing.  All neighbour pairs of a face give a least
squares fit of w and l in pixels; the unit is the pitch that makes the widths whole numbers, with the narrowest
characters (i, l, j, f, t, ., ', the punctuation) 2 units, as on every Executive.

    python3 tools/units.py      # build/units-<Face>.json

The keyboard sheet (Modern's @ # ¢ _) is one line typed key after key, fitted with Modern's widths fixed.
"""
import sys, os, re, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import read as R

NARROW = set('iljf.,;:\'')

def pairs_of(occ):
    by = {}
    for o in occ: by.setdefault(o['word'], []).append(o)
    out = []
    for w, os_ in by.items():
        os_.sort(key=lambda o: o['idx'])
        typ = np.median([o['w'] for o in os_]) if os_ else 0
        for a, b in zip(os_, os_[1:]):
            if b['idx'] == a['idx'] + 1 and b['x0'] - a['x1'] < 0.9 * typ:   # wider: a space between them
                out.append((a['ch'], b['ch'], (b['x0'] + b['w'] / 2) - (a['x0'] + a['w'] / 2)))
    return out

def inkw(occ):
    d = {}
    for o in occ: d.setdefault(o['ch'], []).append(o['w'])
    return {c: float(np.median(v)) for c, v in d.items()}

def solve(pairs, ink, p=None, units=None):
    """centre-to-centre distance of neighbours = (w_a + w_b)/2 + d_b - d_a, d a character's offset from the
    centre of its slug.  Priors: d near 0; w near the ink width plus a margin m (fitted, one per face).
    With `units` given, the widths are fixed to units * p and only the offsets are solved."""
    chars = sorted(set(c for a, b, _ in pairs for c in (a, b)))
    ix = {c: i for i, c in enumerate(chars)}; n = len(chars)
    N = 2 * n + 1          # w..., d..., m
    rows, ys, ws = [], [], []
    for a, b, D in pairs:
        r = np.zeros(N); r[ix[a]] += 0.5; r[ix[b]] += 0.5; r[n + ix[b]] += 1; r[n + ix[a]] -= 1
        rows.append(r); ys.append(D); ws.append(1.0)
    scale = np.median([ink[c] for c in chars])
    for c in chars:
        r = np.zeros(N); r[n + ix[c]] = 1; rows.append(r); ys.append(0); ws.append(1 / (0.08 * scale))   # d ~ 0
        if units is None:
            r = np.zeros(N); r[ix[c]] = 1; r[-1] = -1; rows.append(r); ys.append(ink[c]); ws.append(1 / (0.5 * scale))
        else:
            r = np.zeros(N); r[ix[c]] = 1; rows.append(r); ys.append(units[c] * p); ws.append(100.0)
    A = np.array(rows); y = np.array(ys); W = np.array(ws)
    wt = np.ones(len(pairs))
    for _ in range(4):
        Wt = W.copy(); Wt[:len(pairs)] *= wt
        x = np.linalg.lstsq(A * Wt[:, None], y * Wt, rcond=None)[0]
        res = (A @ x - y)[:len(pairs)]
        mad = np.median(np.abs(res)) + 0.3
        wt = np.where(np.abs(res) > 5 * mad, 0.0, 1.0)
    cnt = {c: 0 for c in chars}
    for (a, b, _), k in zip(pairs, wt):
        if k: cnt[a] += 1; cnt[b] += 1
    return ({c: float(x[ix[c]]) for c in chars}, {c: float(x[n + ix[c]]) for c in chars}, float(x[-1]), cnt,
            float(np.sqrt(np.mean(res[wt > 0] ** 2))), int((wt == 0).sum()))

def pitch(w, cnt):
    """the unit in px: the narrow letters are 2 units; refined so the widths are whole numbers"""
    nar = [w[c] for c in w if c in 'ilj' and cnt[c] >= 2]
    p = np.median(nar) / 2
    for _ in range(5):
        units = {c: max(2, round(w[c] / p)) for c in w}
        good = [c for c in units if cnt[c] >= 6]
        p = sum(w[c] * units[c] for c in good) / sum(units[c] ** 2 for c in good)
    return p, {c: max(2, round(w[c] / p)) for c in w}

BASE = {'ä': 'a', 'å': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Å': 'A', 'Ö': 'O', 'Ü': 'U'}
for _b, _acc in (('a', 'àáâ'), ('e', 'èéêë'), ('i', 'ìíîï'), ('o', 'òóôø'), ('u', 'ùúû'), ('c', 'ç'), ('n', 'ñ'),
                 ('C', 'Ç'), ('E', 'ÈÉÊ'), ('N', 'Ñ'), ('O', 'Ø')):
    for _c in _acc: BASE[_c] = _b
FIGS = '0123456789'
RARE = 4

def run(face, standard=None, p32=None):
    res = pickle.load(open(os.path.join(R.BUILD, f'occ-{face}.pkl'), 'rb'))
    occ = [o for _, oc in res if oc for o in oc]
    pr = pairs_of(occ); ink = inkw(occ)
    w, d, m, cnt, rms, rej = solve(pr, ink)
    p, units = pitch(w, cnt)
    esc = 32 if p32 is None else min((32, 36, 45), key=lambda e: abs(32 * p32 / p - e))
    fitted = dict(units)
    rule = {}
    for c in units:
        if cnt.get(c, 0) < RARE:
            # a letter seen twice whose fit lands on a whole unit keeps it: Arcadia's capitals F L P R Y Z are
            # 3 units, not the 4 of the other faces
            if c.isalpha() and cnt.get(c, 0) >= 2 and abs(w[c] / p - round(w[c] / p)) < 0.35: rule[c] = 'fit'
            elif esc == 32 and standard and c in standard: units[c] = standard[c]; rule[c] = 'standard'
            else: units[c] = max(2, round((ink[c] + m) / p)); rule[c] = 'ink'
    figs = [w[c] / p for c in FIGS if c in w]
    if figs:
        u = (standard or {}).get('0') if esc == 32 and standard else None
        u = u or max(2, round(float(np.median(figs))))
        for c in FIGS:
            if c in units: units[c] = u; rule[c] = 'figures'
    for c, b in BASE.items():
        if c in units and b in units: units[c] = units[b]; rule[c] = 'base'
    w2, d2, _, cnt2, rms2, rej2 = solve(pr, ink, p, units)
    changed = {c: f'{fitted[c]}->{units[c]}' for c in units if fitted[c] != units[c]}
    print(f'{face}: 1/{esc} inch, unit {p:.2f} px, margin {m / p:.2f} unit; {len(pr)} pairs, rms {rms2:.2f} px with'
          f' whole units; changed from the fit: {changed}')
    json.dump(dict(pitch=p, escapement=esc, units=units, offset=d2, ink=ink, count=cnt2, rule=rule, rms=rms2, margin=m / p),
              open(os.path.join(R.BUILD, f'units-{face}.json'), 'w'), indent=1, ensure_ascii=False)
    return p, units

def run_keyboard(standard):
    """the keyboard sheet: one line typed key after key.  Each slug's centre is at  s + p (U + u/2),  U the units
    of the slugs before it; with Modern's widths, IBM's for # ¢ _ (sources.KEYBOARD_UNITS) and the faint 8's
    slug, a straight line fit gives the unit p in pixels, for the scale.  The first character's width is not
    seen in the positions: it comes from its ink, as for a rare character."""
    import sources as S
    res = pickle.load(open(os.path.join(R.BUILD, 'occ-Keyboard.pkl'), 'rb'))
    occ = sorted(res[0][1], key=lambda o: o['idx'])
    ghost, gu, after = S.KEYBOARD_GHOST
    u = dict(standard); u.update(S.KEYBOARD_UNITS); u[ghost] = gu
    seq = []
    for o in occ:
        seq.append((o['ch'], o))
        if o['ch'] == after: seq.append((ghost, None))
    U = 0; V, Y = [], []
    for i, (c, o) in enumerate(seq):
        if i and o is not None and c not in S.KEYBOARD_SKIP: V.append(U + u[c] / 2); Y.append(o['x0'] + o['w'] / 2)
        if i: U += u[c]
    V, Y = np.array(V), np.array(Y)
    p, s = np.polyfit(V, Y, 1); rms = float(np.sqrt(np.mean((Y - (s + p * V)) ** 2)))
    units = {c: u[c] for c, o in seq if o is not None and c in u}
    first = seq[0][0]
    if first not in units: units[first] = max(2, round((seq[0][1]['w'] + 0.5 * p) / p))
    rule = {c: 'IBM table' for c in S.KEYBOARD_UNITS}; rule[first] = rule.get(first, 'ink')
    print(f'Keyboard: unit {p:.2f} px, rms {rms:.2f} px; widths of the characters Modern lacks:',
          {c: units[c] for c in units if c not in standard})
    json.dump(dict(pitch=float(p), escapement=32, units=units, offset={}, rule=rule, rms=rms),
              open(os.path.join(R.BUILD, 'units-Keyboard.json'), 'w'), indent=1, ensure_ascii=False)

def run_typed(face, dpi=300, src='Typed'):
    """a face's typed documents: the unit in pixels from the pairs of characters the face's table has (two
    centres  p (u_a + u_b) / 2  apart), then each other character's width from its pairs with known ones.  At
    the scan's 300 dpi the unit should come out at dpi / escapement pixels."""
    path = os.path.join(R.BUILD, f'units-{face}.json')
    if not os.path.exists(path): path = os.path.join(R.BUILD, f'units-{face}Typed.json')   # Secretarial, Registry
    known = json.load(open(path))
    ku, esc = known['units'], known['escapement']
    res = pickle.load(open(os.path.join(R.BUILD, f'occ-{face}{src}.pkl'), 'rb'))
    occ = [o for _, oc in res if oc for o in oc]
    pr = pairs_of(occ)
    S = np.array([(ku[a] + ku[b]) / 2 for a, b, _ in pr if a in ku and b in ku])
    D = np.array([d for a, b, d in pr if a in ku and b in ku])
    p = float(S @ D / (S @ S))
    for _ in range(3):              # drop the pairs that don't fit (a misread, a space taken for a gap)
        keep = np.abs(D - p * S) < 0.6 * p
        p = float(S[keep] @ D[keep] / (S[keep] @ S[keep]))
    rms = float(np.sqrt(np.mean((D[keep] - p * S[keep]) ** 2)))
    est = {}
    for a, b, d in pr:
        for c, other in ((a, b), (b, a)):
            # not from parentheses: the typist spaced them, "( : )", about two units wider than set solid
            if c not in ku and other in ku and other not in '()':
                est.setdefault(c, []).append(2 * d / p - ku[other])
    units = {c: max(2, int(round(float(np.median(v))))) for c, v in est.items()}
    ink = inkw(occ); m = known.get('margin', 0.5)
    for c in ink:       # no usable pair: from its ink and the face's fitted margin, as for a rare character
        if c not in ku and c not in units: units[c] = max(2, round(ink[c] / p + m)); est[c] = 'ink'
    for c in list(units):   # a fit far from the character's ink (a sign between other signs): from its ink
        by_ink = max(2, round(ink[c] / p + m))
        if est.get(c) != 'ink' and abs(units[c] - by_ink) > 1: units[c] = by_ink; est[c] = 'ink'
    for a, b in ('[]', '<>', '()'):   # a pair of brackets alike: the wider
        if a in units and b in units: units[a] = units[b] = max(units[a], units[b])
    if '‘' in units and "'" in ku: units['‘'] = ku["'"]       # the left quote as wide as the apostrophe
    print(f'{face}{src}: unit {p:.2f} px (1/{esc} inch at {dpi} dpi: {dpi / esc:.2f}), rms {rms:.2f} px over'
          f' {int(keep.sum())} pairs; new widths:', {c: (units[c], est[c] if est[c] == 'ink' else round(float(np.median(est[c])), 2))
                                                      for c in sorted(units)})
    json.dump(dict(pitch=p, escapement=esc, units=units, offset={}, rule={c: 'typed' for c in units}, rms=rms),
              open(os.path.join(R.BUILD, f'units-{face}{src}.json'), 'w'), indent=1, ensure_ascii=False)

# Faces with no brochure line: their typed page fitted with the catalogue's widths.  The escapement from the
# unit in pixels: the memo is scanned at 300 dpi; the newsletter's scale is that of its page 5, whose Arcadia
# (1/32 inch) has a 17.00 px unit.
CATALOG_FACES = {'Secretarial': 300.0, 'Registry': 32 * 17.00}
# Faces whose main source is their page of 'Typesetting with the IBM Executive' (screenshots, of no known scale):
# the escapement each is printed with in IBM's 1960 catalogue
SET_FACES = {'Text': 45, 'BoldFaceItalic': 32, 'Directory': 32, 'Testimonial': 32, 'Copperplate1': 36,
             'Copperplate2': 36, 'Patron': 36}

def run_catalog_typed(face, dpi=None, src='Typed', esc=None):
    cat = json.load(open(os.path.join(R.BUILD, 'catalog-units.json'))).get(face, {})
    res = pickle.load(open(os.path.join(R.BUILD, f'occ-{face}{src}.pkl'), 'rb'))
    occ = [o for _, oc in res if oc for o in oc]
    pr = pairs_of(occ); ink = inkw(occ)
    if cat:
        S_ = np.array([(cat[a] + cat[b]) / 2 for a, b, _ in pr if a in cat and b in cat])
        D = np.array([d for a, b, _ in pr if a in cat and b in cat]) if False else \
            np.array([d for a, b, d in pr if a in cat and b in cat])
        p = float(S_ @ D / (S_ @ S_))
        for _ in range(3):
            keep = np.abs(D - p * S_) < 0.6 * p
            p = float(S_[keep] @ D[keep] / (S_[keep] @ S_[keep]))
    else:          # no catalogue alphabet (Copperplate 1): the unit from a fit of the widths, as for a brochure
        w0, _, _, cnt0, _, _ = solve(pr, ink); p = pitch(w0, cnt0)[0]
    if esc is None: esc = min((32, 36, 45), key=lambda e: abs(dpi / e - p))
    # the characters the catalogue's alphabet doesn't give: from their pairs, as for a brochure face
    w, d, m, cnt, rms, rej = solve(pr, ink, p, {c: cat.get(c, max(2, round(ink[c] / p + 0.5))) for c in ink})
    units = {c: cat.get(c, max(2, round(w[c] / p)) if c in w else max(2, round(ink[c] / p + m / p))) for c in ink}
    for c in ink: cnt.setdefault(c, 0)
    print(f'{face}{src}: unit {p:.2f} px, 1/{esc} inch, rms {rms:.2f} px over {len(pr)} pairs;'
          f' widths not in the catalogue: {dict((c, units[c]) for c in sorted(units) if c not in cat)}')
    json.dump(dict(pitch=p, escapement=esc, units=units, offset=d, ink=ink, count=cnt, rule={}, rms=rms, margin=m / p),
              open(os.path.join(R.BUILD, f'units-{face}{src}.json'), 'w'), indent=1, ensure_ascii=False)

if __name__ == '__main__':
    faces = [a for a in sys.argv[1:] if a in R.FACES + R.TYPED] or R.FACES + R.TYPED
    (p32, fi), std = run('ModernFI'), run('Modern')[1]       # the 1/32 calibration, and the machine's table
    for face in faces:
        if face == 'Keyboard': run_keyboard({**fi, **std})
        elif face in R.TYPED: pass
        elif face not in ('Modern', 'ModernFI'): run(face, std, p32)
    for face in faces:              # after the faces' own tables
        m = re.match(r'(.+)(Set\d*)$', face)
        if m and not os.path.exists(os.path.join(R.BUILD, f'occ-{face}.pkl')): continue   # a page not read
        if m and m.group(1) in SET_FACES:
            run_catalog_typed(m.group(1), src=m.group(2), esc=SET_FACES[m.group(1)])
        elif m: run_typed(m.group(1), src=m.group(2))
        elif face in R.TYPED and face[:-len('Typed')] in CATALOG_FACES:
            run_catalog_typed(face[:-len('Typed')], CATALOG_FACES[face[:-len('Typed')]])
        elif face in R.TYPED: run_typed(face[:-len('Typed')])

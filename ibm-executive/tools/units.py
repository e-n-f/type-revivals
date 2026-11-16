"""Unit widths: the typewriter moves the carriage by a whole number of units for each character.

Within a word the left edges of two neighbours are  w(first) + l(second) - l(first)  apart, where w is the
first character's width and l a character's left side bearing.  All neighbour pairs of a face give a least
squares fit of w and l in pixels; the unit is the pitch that makes the widths whole numbers, with the narrowest
characters (i, l, j, f, t, ., ', the punctuation) 2 units, as on every Executive.

    python3 tools/units.py      # build/units-<Face>.json
"""
import sys, os, json, pickle, numpy as np
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
            if esc == 32 and standard and c in standard: units[c] = standard[c]; rule[c] = 'standard'
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
    json.dump(dict(pitch=p, escapement=esc, units=units, offset=d2, ink=ink, count=cnt2, rule=rule, rms=rms2),
              open(os.path.join(R.BUILD, f'units-{face}.json'), 'w'), indent=1, ensure_ascii=False)
    return p, units

if __name__ == '__main__':
    faces = [a for a in sys.argv[1:] if a in R.FACES] or R.FACES
    p32, std = run('ModernFI')[0], run('Modern')[1]       # the 1/32 calibration, and the machine's table
    for face in faces:
        if face not in ('Modern', 'ModernFI'): run(face, std, p32)

"""Side bearings from the gaps between letters set solid in the specimens.

Metal type has no kerning: two sorts set side by side leave a gap between their inks of
exactly  rsb(left) + lsb(right).  Every adjacent pair in the character sheets' solid runs and
in the display lines (14-48 p, scaled to font units by the letters' own widths) is one
equation; a per-line tracking term absorbs any letterspacing of a line, and a weak prior
(lsb = rsb, and towards a typical value) fixes what the sums alone leave free.

    python3 tools/spacing.py   ->  build/spacing-<Style>.json
"""
import sys, os, json, pickle, itertools, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from segment import load, components, group, bbox
from sheets import SHEETS, DISPLAY, runs

ROOT = os.path.join(os.path.dirname(__file__), '..')
BUILD = os.path.join(ROOT, 'build')
LIGS = ['ch', 'ck', 'fl', 'fi', 'ff', 'ft', 'tz', 'tt']
NAMES = {'ä': 'adieresis', 'ö': 'odieresis', 'ü': 'udieresis', 'Ä': 'Adieresis', 'Ö': 'Odieresis',
         'Ü': 'Udieresis', 'ß': 'germandbls'}
# letters whose sides are the same shape as another's: (letter, like, side 0=left 1=right)
LIKE = [('c', 'o', 0), ('e', 'o', 0), ('C', 'O', 0), ('G', 'O', 0), ('Q', 'O', 0), ('Q', 'O', 1)]
SYM = set('AHIMNOTUVWXYilovwxnmuh') | {'zero.osf', 'zero.lf', 'one.lf', 'eight.osf', 'eight.lf'}

def inkbox(r, thr=0.5):
    m = r['ink'].astype(np.float32) > thr
    cols = np.nonzero(m.any(0))[0]
    return r['x'] + cols[0], r['x'] + cols[-1] + 1

def tokenizations(word, have):
    """all ways of reading a word as glyphs, ligatures optional"""
    pos = [i for i in range(len(word) - 1) if word[i:i + 2] in LIGS and
           '_'.join(word[i:i + 2]) in have]
    for k in range(len(pos) + 1):
        for use in itertools.combinations(pos, k):
            if any(b - a < 2 for a, b in zip(use, use[1:])): continue
            toks = []; i = 0
            while i < len(word):
                if i in use: toks.append(word[i] + '_' + word[i + 1]); i += 2
                else: toks.append(NAMES.get(word[i], word[i])); i += 1
            yield toks

def solve(style, verbose=False):
    R = pickle.load(open(os.path.join(BUILD, f'raster-{style}.pkl'), 'rb'))['glyphs']
    width = {n: inkbox(r)[1] - inkbox(r)[0] for n, r in R.items()}
    eqs = []   # (left, right, gap, line id or None, weight)
    # 1. solid runs on the character sheet
    # The lower case a-z of the sheet is set solid and is the reference; every other run
    # (the capitals are letterspaced on the sheets) and each display line get a tracking
    # term of their own.
    scan, lines = DISPLAY[style]
    RUNS = runs(style); nr = len(RUNS)
    # The swash capitals' card has no lower case to refer to.  Its type list is taken as
    # letterspaced like the italic card's capitals, by the same amount (that run's tracking).
    swash = style == 'Swash'
    if swash:
        caps_track = json.load(open(os.path.join(BUILD, 'spacing-Italic.json')))['track'][0]
    for ri, run in enumerate(RUNS):
        run = [n for n in run if n in R]
        for a, b in zip(run, run[1:]):
            gap = inkbox(R[b])[0] - inkbox(R[a])[1]
            if swash:
                if gap < 250: eqs.append((a, b, gap - caps_track, None, 1.0))
            elif gap < 250: eqs.append((a, b, gap, None if ri == 0 else 0 if ri in (1, 2) else ri - 1, 1.0))  # the two runs of capitals share one
            elif verbose: print('  word space:', a, b, round(gap))
    # 2. display lines
    g = load(os.path.join(ROOT, 'scans', scan))
    for li, ((y0, y1), text) in enumerate(lines):
        comps, _, _ = components(g, (3900, y0, 7900, y1), minarea=100)
        gs = [bbox(G) for G in group(comps)]
        words = text.split(); best = None
        readings = ([[[c + '.swsh' if c.isalpha() else 'ampersand.swsh' for c in w]] for w in words] if swash
                    else [list(tokenizations(w, R)) for w in words])
        for combo in itertools.product(*readings):
            toks = [t for w in combo for t in w]
            if len(toks) != len(gs): continue
            ratio = np.array([width[t] / (q[2] - q[0]) for t, q in zip(toks, gs)])
            err = np.std(np.log(ratio))
            if best is None or err < best[0]: best = (err, combo, np.median(ratio))
        if best is None:
            print(f'  {style}: cannot read "{text}"'); continue
        err, combo, sc = best
        i = 0
        for w in combo:
            for a, b in zip(w, w[1:]):
                if (a, b) not in (('c', 'h'), ('c', 'k')):
                    eqs.append((a, b, (gs[i + 1][0] - gs[i][2]) * sc, nr - 1 + li, 1.0))
                i += 1
            i += 1
        if verbose: print(f'  line {li}: scale {sc:.3f} width spread {err:.3f}  {combo}')
    names = sorted(set(n for e in eqs for n in e[:2]))
    idx = {n: i for i, n in enumerate(names)}
    nl = len(lines) + nr - 1; N = 2 * len(names) + nl
    w = np.array([e[4] for e in eqs])
    for it in range(4):
        A = []; y = []; W = []
        for (a, b, gap, li, wt), ww in zip(eqs, w):
            row = np.zeros(N); row[2 * idx[a] + 1] = 1; row[2 * idx[b]] = 1
            if li is not None: row[2 * len(names) + li] = 1
            A.append(row); y.append(gap); W.append(ww)
        for n in names:
            k = 0.3 if n in SYM else 0.1
            row = np.zeros(N); row[2 * idx[n]] = k; row[2 * idx[n] + 1] = -k; A.append(row); y.append(0); W.append(1)
            typ = 25 if n[0].islower() else 40
            for side in (0, 1):
                row = np.zeros(N); row[2 * idx[n] + side] = 0.05; A.append(row); y.append(0.05 * typ); W.append(1)
        for a, b, side in LIKE:
            if a in idx and b in idx:
                row = np.zeros(N); row[2 * idx[a] + side] = 0.5; row[2 * idx[b] + side] = -0.5
                A.append(row); y.append(0); W.append(1)
        for j in range(nl):
            row = np.zeros(N); row[2 * len(names) + j] = 0.02; A.append(row); y.append(0); W.append(1)
        A = np.array(A); y = np.array(y); W = np.sqrt(np.array(W))
        x = np.linalg.lstsq(A * W[:, None], y * W, rcond=None)[0]
        res = (A @ x - y)[:len(eqs)]
        mad = np.median(np.abs(res)) + 1e-6
        w = np.where(np.abs(res) > max(4 * 1.48 * mad, 20), 0.0, 1.0)
    out = {n: (float(x[2 * idx[n]]), float(x[2 * idx[n] + 1])) for n in names}
    track = list(x[2 * len(names):])
    print(f'{style}: {len(eqs)} pairs, {int((w == 0).sum())} rejected, rms {np.sqrt(np.mean(res[w > 0] ** 2)):.1f} units;'
          f' line tracking {[round(t) for t in track]}')
    json.dump(dict(sb=out, track=track), open(os.path.join(BUILD, f'spacing-{style}.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    # Swash after Italic: it takes the italic capitals' letterspacing on their card
    for st in [a for a in sys.argv[1:] if a in SHEETS] or list(SHEETS):
        sb = solve(st, verbose='-v' in sys.argv)
        print('  ', ' '.join(f'{n.split(".")[0]}:{l:.0f}/{r:.0f}' for n, (l, r) in sb.items()
                             if len(n.split('.')[0]) == 1))

"""Read the scans: every character of every source line, in its cell of the typewriter's fixed grid.

A Selectric moves the same distance for every character, so a line's characters sit in cells of one width
(the pitch), from a starting phase.  The reader finds a block's lines, fits the pitch (shared by the block's
lines) and each line's phase, puts every piece of ink in its cell, and lines the cells up with the text:
the occupied cells fall into runs (words), matched to the text's words by their lengths.

    python3 tools/read.py [Face ...]          # build/occ-<Face>.pkl
    python3 tools/read.py contact [Face ...]  # also build/contact-<Face>.png: every character read, labelled
"""
import sys, os, pickle, numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sources as S

ROOT = os.path.join(HERE, '..')
SCANS = os.path.join(ROOT, 'scans'); BUILD = os.path.join(ROOT, 'build')
Image.MAX_IMAGE_PIXELS = None
# characters that sit on the baseline, for finding it
BASE = set('abcdefhiklmnorstuvwxzABCDEFGHIKLMNOPRSTUVWXYZ1234567890')
SKIP = '·'

_cache = {}
def gray(name):
    if name not in _cache:
        _cache[name] = np.asarray(Image.open(os.path.join(SCANS, name)).convert('L'), np.float32) / 255
    return _cache[name]

def ink_of(region):
    """ink 0..1: paper (its median) -> 0, the darkest ink -> 1"""
    bg = np.median(region); dark = np.percentile(region, 0.2)
    return np.clip((bg - region) / max(bg - dark, 0.2) * 1.1, 0, 1)

def components(ink):
    m = (ink > 0.5).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 6: continue
        if w > 300 and h < 20: continue                    # a rule
        if ink[lab == i].max() < 0.55: continue            # a grey footnote mark
        out.append(dict(id=i, x=int(x), y=int(y), w=int(w), h=int(h), a=int(a), cx=float(cen[i][0]),
                        cy=float(cen[i][1])))
    return out, lab

def lines_of(comps):
    """the block's lines: the tall components clustered by their feet; then every other one given to a line"""
    big = [c for c in comps if c['a'] > 40]
    H = float(np.median([c['h'] for c in big]))
    tall = sorted([c for c in big if c['h'] > 0.75 * H], key=lambda c: c['y'] + c['h'])
    groups = []
    for c in tall:
        f = c['y'] + c['h']
        if groups and f - groups[-1]['foot'] < 0.6 * H:
            groups[-1]['c'].append(c); groups[-1]['foot'] = float(np.median([d['y'] + d['h'] for d in groups[-1]['c']]))
        else: groups.append(dict(c=[c], foot=f))
    groups = [g for g in groups if len(g['c']) >= 3]
    lines = []
    for g in groups:
        base = float(np.median([c['y'] + c['h'] for c in g['c']]))
        top = float(np.percentile([c['y'] for c in g['c']], 10))
        lines.append(dict(base=base, top=top, comps=[]))
    ids = {id(c) for g in groups for c in g['c']}
    for g, L in zip(groups, lines): L['comps'] = list(g['c'])
    for c in comps:
        if id(c) in ids: continue
        inside = [L for L in lines if L['top'] - 0.15 * H <= c['cy'] <= L['base']]
        if inside: inside[0]['comps'].append(c); continue
        def cost(L):
            # an underscore: wide and flat, below its line's baseline by up to about a cap height
            if c['h'] < 0.3 * H and c['w'] > 0.5 * H and L['base'] < c['cy'] < L['base'] + 1.1 * H: return 0.0
            if c['cy'] > L['base']: return (c['cy'] - L['base']) / H          # comma, underscore: below
            return 1.5 * (L['top'] - c['cy']) / H                              # an accent: above
        best = min(lines, key=cost)
        if cost(best) < 0.9: best['comps'].append(c)
    return lines, H

def fit_pitch(lines, nominal):
    """the pitch that puts the most characters' centres on a lattice, in every line at once"""
    def score(p):
        s = 0.0
        for L in lines:
            xs = np.array([c['cx'] for c in L['comps'] if c['a'] > 40])
            z = np.exp(2j * np.pi * xs / p); s += abs(z.sum())
        return s
    ps = np.arange(0.85 * nominal, 1.15 * nominal, 0.05)
    p = max(ps, key=score)
    fine = np.arange(p - 0.1, p + 0.1, 0.005)
    return float(max(fine, key=score))

def phase(L, p):
    xs = np.array([c['cx'] for c in L['comps'] if c['a'] > 40])
    z = np.exp(2j * np.pi * xs / p).mean()
    return float(np.angle(z) / (2 * np.pi) * p)        # a cell's centre is at phase + k p

def cells(L, p, lab, ink):
    """{cell number: ink of that cell (in line-block coordinates)}: each component in the cell of its centre;
    one spanning more than a cell (touching characters) is cut at the cells' edges"""
    c0 = phase(L, p); out = {}
    typical = float(np.median([c['a'] for c in L['comps'] if c['a'] > 40]))
    for c in L['comps']:
        ks = [int(round((c['cx'] - c0) / p))]
        if c['w'] > 1.35 * p:
            ks = list(range(int(round((c['x'] - c0) / p)), int(round((c['x'] + c['w'] - c0) / p)) + 1))
        for k in ks:
            lo = c0 + (k - 0.5) * p; hi = c0 + (k + 0.5) * p
            x0 = c['x'] if len(ks) == 1 else max(c['x'], int(np.floor(lo)))
            x1 = c['x'] + c['w'] if len(ks) == 1 else min(c['x'] + c['w'], int(np.ceil(hi)))
            if x1 <= x0: continue
            m = np.zeros_like(lab, dtype=bool)
            m[c['y']:c['y'] + c['h'], x0:x1] = lab[c['y']:c['y'] + c['h'], x0:x1] == c['id']
            # a slice of a wide piece is a character of that cell only if it has a fair share of ink: not the
            # tail of a script letter's stroke reaching into the space beside it
            if len(ks) > 1 and m.sum() < 0.3 * typical:
                if out.get(k) is None: continue
            out.setdefault(k, []).append(m)
    return out, c0

def runs_of(ks):
    ks = sorted(ks); out = []
    for k in ks:
        if out and k == out[-1][-1] + 1: out[-1].append(k)
        else: out.append([k])
    return out

def align(words, runs):
    """words to runs: a word takes one run of its length, or a few runs one cell apart whose cells add up to its
    length (a sign typed with a space beside it); words or runs left over are skipped"""
    n, m = len(words), len(runs); INF = 1e9
    C = np.full((n + 1, m + 1), INF); B = {}; C[0, 0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            c = C[i, j]
            if c >= INF: continue
            if i < n and c + 1 < C[i + 1, j]: C[i + 1, j] = c + 1; B[(i + 1, j)] = ('skipw', i, j)
            if j < m and c + 1 < C[i, j + 1]: C[i, j + 1] = c + 1; B[(i, j + 1)] = ('skipr', i, j)
            if i < n:
                tot = 0
                for t in range(j, m):
                    if t > j and runs[t][0] - runs[t - 1][-1] != 2: break
                    tot += len(runs[t])
                    if tot == len(words[i]):
                        cc = c + 0.5 * (t - j)
                        if cc < C[i + 1, t + 1]: C[i + 1, t + 1] = cc; B[(i + 1, t + 1)] = ('match', i, j, t)
                    if tot >= len(words[i]): break
    out = []; i, j = n, m
    while (i, j) != (0, 0):
        b = B[(i, j)]
        if b[0] == 'match':
            _, wi, j0, t = b; slots = [k for r in runs[j0:t + 1] for k in r]
            out += list(zip(words[wi], slots))
        i, j = b[1], b[2]
    return out, C[n, m]

def read_block(scan, box, pitch, texts):
    x0, x1, y0, y1 = box; g = gray(scan)
    ink = ink_of(g[y0:y1, x0:x1])
    comps, lab = components(ink)
    lines, H = lines_of(comps)
    if len(lines) != len(texts):
        raise SystemExit(f'{scan} {box}: found {len(lines)} lines, expected {len(texts)}')
    dpi = g.shape[1] / 8.5
    p = fit_pitch(lines, dpi / pitch)
    occ = []; report = []
    for li, (L, text) in enumerate(zip(lines, texts)):
        cs, c0 = cells(L, p, lab, ink)
        runs = runs_of(cs)
        pairs, cost = align(text.split(), runs)
        # the baseline: a straight line through the feet of the characters that sit on it (the scans are a
        # little skewed, so one height for the whole line would be off by several pixels at its ends)
        feet = []
        for ch, k in pairs:
            if ch in BASE:
                m = np.any(cs[k], axis=0); ys, xs = np.nonzero(m)
                feet.append((c0 + k * p, ys.max() + 1))
        a, b = L['base'], 0.0
        if len(feet) >= 4:
            fx, fy = np.array(feet, float).T; keep = np.ones(len(fx), bool)
            for _ in range(3):
                b, a = np.polyfit(fx[keep], fy[keep], 1)
                r = fy - (a + b * fx); keep = np.abs(r) < max(3.0, 2.5 * np.median(np.abs(r[keep])))
        base_at = lambda x: a + b * x
        report.append((text, len(pairs), sum(len(w) for w in text.split()), cost))
        for ch, k in pairs:
            if ch == SKIP: continue
            m = np.any(cs[k], axis=0)
            # with the faint ink around the strokes (a light print's edges, below the threshold), within the cell
            lo, hi = int(np.floor(c0 + (k - 0.6) * p)), int(np.ceil(c0 + (k + 0.6) * p))
            grown = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            cols = np.arange(m.shape[1]); grown[:, (cols < lo) | (cols >= hi)] = False
            m = m | grown
            ys, xs = np.nonzero(m)
            Y0, Y1 = max(0, ys.min() - 4), min(ink.shape[0], ys.max() + 5)
            X0, X1 = max(0, xs.min() - 4), min(ink.shape[1], xs.max() + 5)
            crop = np.where(m[Y0:Y1, X0:X1], ink[Y0:Y1, X0:X1], 0).astype(np.float32)
            occ.append(dict(ch=ch, ink=crop, ref=li >= len(texts) - 2, X0=X0, Y0=Y0, x0=c0 + k * p,
                            base=float(base_at(c0 + k * p)), w=int(xs.max() - xs.min() + 1),
                            top=int(ys.min()), bottom=int(ys.max() + 1), line=(scan, box, li), cell=k,
                            scan=scan, off=(x0, y0)))
    return occ, p, report

def read(face):
    occ = []; pitches = []
    for scan, box, pitch, texts in S.FACES[face]:
        o, p, report = read_block(scan, box, pitch, texts)
        occ += o; pitches.append((p, pitch))
        for text, got, want, cost in report:
            if got < want: print(f'   {face}: {got}/{want} in "{text[:50]}"')
    return occ, pitches

def contact(face, occ, out):
    cell = 70; cols = 30; rows = (len(occ) + cols - 1) // cols
    sheet = Image.new('L', (cols * cell, rows * cell), 255); d = ImageDraw.Draw(sheet)
    for i, o in enumerate(sorted(occ, key=lambda o: o['ch'])):
        im = Image.fromarray(((1 - o['ink']) * 255).astype(np.uint8)); im.thumbnail((cell - 8, cell - 20))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 4, y + 18)); d.text((x + 3, y + 1), o['ch'], fill=0, font_size=15)
    sheet.save(out)

if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    for face in [a for a in sys.argv[1:] if a in S.FACES] or S.FACES:
        occ, pitches = read(face)
        n = len(set(o['ch'] for o in occ))
        print(f'{face}: {len(occ)} characters, {n} different; pitch ' +
              ', '.join(f'{p:.2f} px (1/{nominal} inch)' for p, nominal in pitches))
        pickle.dump(dict(occ=occ, pitches=pitches), open(os.path.join(BUILD, f'occ-{face}.pkl'), 'wb'))
        if 'contact' in sys.argv: contact(face, occ, os.path.join(BUILD, f'contact-{face}.png'))

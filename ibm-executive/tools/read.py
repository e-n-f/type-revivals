"""Read the scans: every character of every source line, matched to its place in the known text.

Each occurrence records the character, its ink (0..1, the page's paper normalized to 0), its ink box, the
line's baseline, and its neighbour in the same word, for the unit fit and the glyph averaging.

    python3 tools/read.py            # build/occ-<Face>.pkl, and a summary of what matched
    python3 tools/read.py contact    # build/contact-<Face>.png: every matched character, labelled
"""
import sys, os, pickle, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'common'))
from segment import group, bbox as _bbox
def bbox(G):
    if isinstance(G, dict): return G['cut'][0], G['y'], G['cut'][1], G['y'] + G['h']
    return _bbox(G)
import sources as S
from PIL import Image, ImageDraw

ROOT = os.path.join(HERE, '..')
SCANS = os.path.join(ROOT, 'scans')
BUILD = os.path.join(ROOT, 'build')
Image.MAX_IMAGE_PIXELS = None
# characters that sit on the baseline with no overshoot worth worrying about
BASE = set('abdefhiklmnrtuvxzABDEFHIKLMNPRTUVXZ1247äüåÄÜÅ')

_cache = {}
def gray(name):
    if name not in _cache:
        _cache[name] = np.asarray(Image.open(os.path.join(SCANS, name)).convert('L'), np.float32) / 255
    return _cache[name]

def ink_of(region):
    """ink 0..1 from a grey region: paper (its median) -> 0, the darkest ink -> 1"""
    bg = np.median(region); dark = np.percentile(region, 0.5)
    return np.clip((bg - region) / max(bg - dark, 0.2) * 1.1, 0, 1)

def components(ink, minarea):
    m = (ink > 0.5).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a >= minarea: out.append(dict(id=i, x=x, y=y, w=w, h=h, a=a, cy=cen[i][1]))
    return out, lab

def split_group(G, lab, parts, frac=None):
    """split one group of touching characters at the narrowest columns (near frac of the width, for two)"""
    if isinstance(G, dict):          # a piece of a group already split
        x0, x1 = G['cut']; _, y0, _, y1 = _bbox(G['parent']); comps = G['parent']
    else:
        x0, y0, x1, y1 = _bbox(G); comps = G
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for c in comps: m |= (lab[y0:y1, x0:x1] == c['id'])
    parent = G['parent'] if isinstance(G, dict) else G
    prof = m.sum(0); cuts = []
    for k in range(1, parts):
        f = frac if (frac is not None and parts == 2) else k / parts
        lo, hi = int((x1 - x0) * (f - 0.15)), int((x1 - x0) * (f + 0.15))
        lo, hi = max(1, lo), max(lo + 1, min(hi, x1 - x0 - 1))
        cuts.append(lo + int(np.argmin(prof[lo:hi])))
    edges = [0] + cuts + [x1 - x0]
    return [dict(x=x0 + a, y=y0, w=b - a, h=y1 - y0, a=int(m[:, a:b].sum()), cut=(x0 + a, x0 + b), parent=parent) for a, b in zip(edges, edges[1:])]

class Line:
    """the groups of one line of text.  Either a band of a scan (box), or components already assigned to it
    (comps, with the label image and ink they come from)."""
    def __init__(self, scan, box=None, minarea=10, center=None, comps=None, lab=None, ink=None, off=None):
        self.scan = scan
        if comps is not None:
            self.ink, self.lab, self.off = ink, lab, off
            self.groups = group(comps); return
        x0, y0, x1, y1 = box; g = gray(scan); pad = 40
        Y0, Y1 = max(0, y0 - pad), min(g.shape[0], y1 + pad)
        self.off = (x0, Y0)
        self.ink = ink_of(g[Y0:Y1, x0:x1])
        comps, self.lab = components(self.ink, minarea)
        lo, hi = (y0 - Y0, y1 - Y0)
        if center is not None: lo, hi = center
        self.groups = group([c for c in comps if lo <= c['cy'] < hi])

    def crop(self, G, pad=6):
        """the ink of one group (its own components only), with its box in line coordinates"""
        if isinstance(G, dict):      # a piece of a split group
            x0, x1 = G['cut']; _, y0, _, y1 = bbox(G['parent']); comps = G['parent']
        else:
            x0, y0, x1, y1 = bbox(G); comps = G
        X0, Y0 = max(0, x0 - pad), max(0, y0 - pad)
        X1, Y1 = min(self.ink.shape[1], x1 + pad), min(self.ink.shape[0], y1 + pad)
        mask = np.zeros((Y1 - Y0, X1 - X0), np.uint8)
        for c in comps: mask |= (self.lab[Y0:Y1, X0:X1] == c['id']).astype(np.uint8)
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        if isinstance(G, dict):
            cols = np.arange(X0, X1); mask[:, (cols < x0) | (cols >= x1)] = 0
        return np.where(mask > 0, self.ink[Y0:Y1, X0:X1], 0), (X0, Y0)

def block_lines(scan, box, minarea):
    """the lines of a block of text: lines from the tall components; a small one (comma, full stop, hyphen) in
    a line's band goes to that line, and one outside every band (a dot, ring, accent) to the line of the
    letter it sits over, or else to the nearest line"""
    x0, y0, x1, y1 = box; g = gray(scan)
    ink = ink_of(g[y0:y1, x0:x1]); comps, lab = components(ink, minarea)
    H = np.median([c['h'] for c in comps if c['h'] > 0.4 * max(c['h'] for c in comps)])
    tall = [c for c in comps if c['h'] > 0.55 * H]
    # the lines are the bands of the ink's row profile; each tall component goes to the band holding its centre
    bs = bands(ink, 0.6 * H)
    rows = [[] for _ in bs]
    for c in tall:
        k = min(range(len(bs)), key=lambda k: max(bs[k][0] - c['cy'], c['cy'] - bs[k][1], 0))
        rows[k].append(c)
    keep = [k for k, r in enumerate(rows) if len(r) > 2]
    rows = [rows[k] for k in keep]
    # a 'tall' component that starts below its line's foot is a mark of the next line (a ring over a capital)
    for r in rows:
        foot = np.median([c['y'] + c['h'] for c in r])
        r[:] = [c for c in r if c['y'] < foot - 0.1 * H]
    span = [(min(c['y'] for c in r), max(c['y'] + c['h'] for c in r)) for r in rows]
    members = [list(r) for r in rows]
    tall_ids = {id(c) for r in rows for c in r}
    # a line's band: from its letters' (median) top to a little below their (median) foot, where commas hang
    band = [(np.median([c['y'] for c in r]), np.median([c['y'] + c['h'] for c in r]) + 0.15 * H) for r in rows]
    for c in comps:
        if id(c) in tall_ids: continue
        inside = [k for k, (t, b) in enumerate(band) if t <= c['cy'] <= b]
        if inside:          # a comma, full stop or hyphen on the line
            members[inside[0]].append(c); continue
        # an accent or dot: the line of the letter it sits over (the lines are close: a ring over a capital
        # can be nearer the line above's comma than its own letter's top)
        over = [(t['y'] - (c['y'] + c['h']), k) for k, r in enumerate(rows) for t in r
                if min(t['x'] + t['w'], c['x'] + c['w']) - max(t['x'], c['x']) > 0
                and -0.3 * t['h'] <= t['y'] - (c['y'] + c['h']) < 0.5 * H]
        if over:
            members[min(over)[1]].append(c); continue
        def dist(t):
            dx = max(t['x'] - (c['x'] + c['w']), c['x'] - (t['x'] + t['w']), 0)
            dy = max(t['y'] - (c['y'] + c['h']), c['y'] - (t['y'] + t['h']), 0)
            return np.hypot(dx, dy)
        k = min(range(len(rows)), key=lambda k: min(dist(t) for t in rows[k]))
        members[k].append(c)
    return [Line(scan, comps=m, lab=lab, ink=ink, off=(x0, y0)) for m in members]

def tokens(text, multi):
    """characters of the text with their word index; spaces separate words"""
    out = []; w = 0
    for ch in text:
        if ch == ' ': w += 1; continue
        out.append((ch, w))
    return out, sum(multi.get(ch, 1) for ch, _ in out)

def baseline(occ):
    pts = [(o['x0'] + o['w'] / 2, o['bottom']) for o in occ if o['ch'] in BASE]
    if len(pts) < 2: pts = [(o['x0'] + o['w'] / 2, o['bottom']) for o in occ]
    xs, ys = np.array(pts, float).T
    keep = np.ones(len(xs), bool)
    for _ in range(3):
        b, a = np.polyfit(xs[keep], ys[keep], 1) if keep.sum() > 2 else (0.0, np.median(ys[keep]))
        r = ys - (a + b * xs); keep = np.abs(r) < max(2.5 * np.median(np.abs(r[keep])) + 1, 2)
    return a, b

def area(G, lab):
    return G['a'] if isinstance(G, dict) else sum(c.get('a', 0) for c in G)

def fit_word(gs, chars, multi, lab, model):
    """groups of one word -> list of group lists, one per character; None if they can't be made to fit.
    Counts that agree are taken as they are; otherwise a dynamic programme decides, from the widths in
    `model`, which groups hold several touching characters, which pairs of groups are one character printed
    in two pieces, and which small groups are noise."""
    need = sum(multi.get(c, 1) for c in chars)
    if len(gs) == need:
        out = []; gi = 0
        for ch in chars:
            n = multi.get(ch, 1); out.append(gs[gi:gi + n]); gi += n
        return out if widths_ok(out, chars, model) else None
    W = [bbox(G)[2] - bbox(G)[0] for G in gs]; A = [area(G, lab) for G in gs]
    X0 = [bbox(G)[0] for G in gs]; X1 = [bbox(G)[2] for G in gs]
    typ = float(np.median(W)); tA = float(np.median(A))
    e = lambda ch: model.get(ch, typ)
    sig = lambda v: 0.15 * v + 2.5
    n, m = len(chars), len(gs); INF = 1e18
    C = np.full((n + 1, m + 1), INF); B = {}; C[0, 0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            c0 = C[i, j]
            if c0 >= INF: continue
            if j < m and A[j] < 0.25 * tA:            # noise
                if c0 + 5 < C[i, j + 1]: C[i, j + 1] = c0 + 5; B[(i, j + 1)] = ('skip', i, j)
            if i == n: continue
            k = multi.get(chars[i], 1)
            if k > 1:
                if j + k <= m:
                    c = c0 + ((X1[j + k - 1] - X0[j] - e(chars[i])) / sig(e(chars[i]))) ** 2
                    if c < C[i + 1, j + k]: C[i + 1, j + k] = c; B[(i + 1, j + k)] = ('one', i, j, k)
                continue
            for t in (1, 2, 3):                      # one group, t touching characters
                if i + t > n or j + 1 > m or any(multi.get(chars[i + u], 1) > 1 for u in range(t)): break
                ex = sum(e(chars[i + u]) for u in range(t)) + (t - 1) * 0.1 * typ
                c = c0 + ((W[j] - ex) / sig(ex)) ** 2 + 8 * (t - 1)
                if c < C[i + t, j + 1]: C[i + t, j + 1] = c; B[(i + t, j + 1)] = ('touch', i, j, t)
            if j + 2 <= m and X0[j + 1] - X1[j] <= 4:  # one character in two pieces
                c = c0 + ((X1[j + 1] - X0[j] - e(chars[i])) / sig(e(chars[i]))) ** 2 + 8
                if c < C[i + 1, j + 2]: C[i + 1, j + 2] = c; B[(i + 1, j + 2)] = ('one', i, j, 2)
    if C[n, m] >= INF or C[n, m] / n > 4: return None
    plan = []; i, j = n, m
    while (i, j) != (0, 0):
        b = B[(i, j)]; plan.append(b)
        if b[0] == 'skip': j = b[2]
        else: i, j = b[1], b[2]
    out = []
    for b in plan[::-1]:
        if b[0] == 'skip': continue
        if b[0] == 'one': out.append(gs[b[2]:b[2] + b[3]])
        else:
            _, i, j, t = b
            if t == 1: out.append([gs[j]]); continue
            ws = [e(chars[i + u]) for u in range(t)]
            pieces = [gs[j]]
            for u in range(t - 1):     # peel off one character at a time from the left
                rest = pieces.pop(); f = ws[u] / sum(ws[u:])
                pieces += split_group(rest, lab, 2, frac=f)
            out += [[p] for p in pieces]
    return out if len(out) == n and widths_ok(out, chars, model) else None

def widths_ok(out, chars, model):
    for ch, G in zip(chars, out):
        if ch in model:
            w = max(bbox(g)[2] for g in G) - min(bbox(g)[0] for g in G)
            if not 0.6 * model[ch] - 3 <= w <= 1.45 * model[ch] + 3: return False
    return True

def match(line, text, multi, split=None, lid=0, model=None):
    """occurrences for a line whose text is known.  Words are told apart by the widest gaps; a word whose
    groups don't fit its letters is left out.  Returns (occurrences, words fitted, words)"""
    model = model or {}
    words = text.split()
    groups = sorted(line.groups, key=lambda G: bbox(G)[0])
    if split:   # characters the source prints touching
        flat = text.replace(' ', '')
        for pair, n in split.items():
            if pair in flat and len(groups) == sum(multi.get(c, 1) for c in flat) - (n - 1):
                gi = sum(multi.get(c, 1) for c in flat[:flat.index(pair)])
                groups[gi:gi + 1] = split_group(groups[gi], line.lab, n)
    gaps = [bbox(b)[0] - bbox(a)[2] for a, b in zip(groups, groups[1:])]
    cuts = sorted(np.argsort(gaps)[::-1][:len(words) - 1]) if len(words) > 1 else []
    wg = []; s0 = 0
    for c in list(cuts) + [len(groups) - 1]:
        wg.append(groups[s0:c + 1]); s0 = c + 1
    occ = []; ok = 0
    for wi, (w, gs) in enumerate(zip(words, wg)):
        fit = fit_word(gs, list(w), multi, line.lab, model)
        if fit is None: continue
        ok += 1
        for k, (ch, G) in enumerate(zip(w, fit)):
            o = occurrence(line, ch, G, (lid, wi), k)
            if o is not None: occ.append(o)
    if len(occ) < 3: return None
    a, b = baseline(occ)
    for o in occ:
        o['base'] = a + b * (o['x0'] + o['w'] / 2)
    return occ

def occurrence(line, ch, gs, word, k):
    pieces = []
    for G in gs:
        ink, (X0, Y0) = line.crop(G); pieces.append((ink, X0, Y0))
    X0 = min(p[1] for p in pieces); Y0 = min(p[2] for p in pieces)
    X1 = max(p[1] + p[0].shape[1] for p in pieces); Y1 = max(p[2] + p[0].shape[0] for p in pieces)
    ink = np.zeros((Y1 - Y0, X1 - X0), np.float32)
    for p, px, py in pieces:
        sl = (slice(py - Y0, py - Y0 + p.shape[0]), slice(px - X0, px - X0 + p.shape[1]))
        ink[sl] = np.maximum(ink[sl], p)
    m = ink > 0.5
    if not m.any(): return None
    cols = np.nonzero(m.any(0))[0]; rows = np.nonzero(m.any(1))[0]
    return dict(ch=ch, word=word, idx=k, ink=ink, X0=X0, Y0=Y0,
                x0=X0 + cols[0], x1=X0 + cols[-1] + 1, top=Y0 + rows[0], bottom=Y0 + rows[-1] + 1,
                w=cols[-1] + 1 - cols[0], line=word[0], scan=line.scan, off=line.off,
                touching=any(isinstance(G, dict) for G in gs))

def read_stream(lines, stream, multi, lid0, model=None, breaks=None):
    """paragraph lines: take words from the stream for each line.  The break is the one whose character count
    best fits the line's groups (touching or broken letters make the counts differ a little); once a line
    has matched, `breaks` remembers it."""
    words = stream.split(); out = []; wi = 0
    for li, line in enumerate(lines):
        n = len(line.groups)
        if breaks and li < len(breaks): k = breaks[li]
        else:
            cands = []
            for k in range(1, len(words) - wi + 1):
                have = sum(multi.get(c, 1) for w in words[wi:wi + k] for c in w)
                cands.append((abs(have - n), k))
                if have > n + 4: break
            k = min(cands)[1] if li < len(lines) - 1 else len(words) - wi
        text = ' '.join(words[wi:wi + k]); wi += k
        out.append((text, match(line, text, multi, lid=lid0 + li, model=model)))
    return out

# ------------------------------------------------------------------------------------------------- per source
def bands(ink, minh):
    prof = (ink > 0.5).sum(1); on = prof > 2; out = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            out.append([i, j]); i = j
        i += 1
    merged = []
    for a, b in out:     # a short band (an accent above the next line) joins the next one
        if merged and merged[-1][1] - merged[-1][0] < minh: merged[-1][1] = b
        else: merged.append([a, b])
    if merged and merged[-1][1] - merged[-1][0] < minh and len(merged) > 1:
        merged[-2][1] = merged[-1][1]; merged.pop()
    # two lines run together (an accent bridging the gap): split at the emptiest row near the middle
    med = np.median([b - a for a, b in merged]); out = []
    for a, b in merged:
        if b - a > 1.6 * med:
            lo, hi = a + int(0.3 * (b - a)), a + int(0.7 * (b - a))
            c = lo + int(np.argmin(prof[lo:hi])); out += [(a, c), (c, b)]
        else: out.append((a, b))
    return out

def width_model(res):
    ws = {}
    for _, oc in res:
        for o in oc or []:
            if not o.get('touching'): ws.setdefault(o['ch'], []).append(o['w'])
    return {ch: float(np.median(v)) for ch, v in ws.items()}

def read_finnish(face):
    block, npara, syms = S.FACES_FI[face]
    g = gray(S.FINNISH); s = g.shape[1] / 1600
    box = [int(v * s) for v in block]
    lines = block_lines(S.FINNISH, box, 10)
    texts = [None] * npara + ['1234567890 ' + syms, S.LC_FI, S.UC_FI]
    if len(lines) != len(texts):
        raise SystemExit(f'{face}: found {len(lines)} lines, expected {len(texts)}')
    model = None
    for _ in range(3):   # widths from what matched, then match the rest with them
        res = [(t, match(ln, t, S.MULTI, lid=k, model=model)) for k, (t, ln) in enumerate(zip(S.LINES_FI[face], lines))]
        for k, t in enumerate(texts[npara:]):
            lid = npara + k
            if k == 0: res.append((t, symbols(lines[lid], t, S.SYMBOL_COLUMNS[face], lid, model)))
            else: res.append((t, match(lines[lid], t, S.MULTI, lid=lid, model=model)))
        model = width_model(res)
    return res, lines

def columns(line, x0, x1):
    """the groups of a line in the columns x0..x1: a group mostly inside is taken whole, one that runs on into a
    neighbour's columns (touching it) is cut at the edge"""
    out = []
    for G in line.groups:
        a, _, b, _ = bbox(G)
        ov = min(b, x1) - max(a, x0)
        if ov <= 0 or (ov < 0.5 * (b - a) and ov < 0.5 * (x1 - x0)): continue
        if a >= x0 - 2 and b <= x1 + 2: out.append(G); continue
        _, y0, _, y1 = bbox(G)
        out.append(dict(x=max(a, x0), y=y0, w=min(b, x1) - max(a, x0), h=y1 - y0, a=0, cut=(max(a, x0), min(b, x1)),
                        parent=G))
    return out

def symbols(line, text, cols, lid, model):
    """the figures matched as a word, and the symbols from their columns (sources.SYMBOL_COLUMNS)"""
    figs = text.split()[0]
    allg = line.groups; line.groups = [G for G in allg if bbox(G)[2] < cols[0][1]]
    occ = match(line, figs, S.MULTI, lid=lid, model=model) or []
    line.groups = allg
    for k, (ch, x0, x1) in enumerate(cols):
        gs = columns(line, x0, x1)
        o = occurrence(line, ch, gs, (lid, 1), k) if gs else None
        if o is not None:
            o['touching'] = any(isinstance(G, dict) for G in gs); occ.append(o)
    a, b = baseline(occ)
    for o in occ: o['base'] = a + b * (o['x0'] + o['w'] / 2)
    return occ

def read_jowa():
    res = []; lines = []
    for k, (scan, box, text) in enumerate(S.JOWA_LINES):
        ln = Line(scan, box, 40); lines.append(ln)
        res.append((text, match(ln, text, S.JOWA_MULTI, S.JOWA_SPLIT, lid=k)))
    lid = len(S.JOWA_LINES)
    for (x0, x1), base0, pitch, texts in S.JOWA_BLOCKS:
        for i, t in enumerate(texts):
            yb = base0 + i * pitch; y0 = int(yb - 1.1 * pitch); y1 = int(yb + 0.5 * pitch)
            ln = Line(S.JOWA_TEXT, (x0, y0, x1, y1), 40,
                      center=(yb - 0.8 * pitch - y0 + 40, yb + 0.2 * pitch - y0 + 40))
            lines.append(ln)
            res.append((t, match(ln, t, S.JOWA_MULTI, lid=lid)))
            lid += 1
    return res, lines

def read_keyboard():
    scan, box, text = S.KEYBOARD_LINE
    ln = Line(scan, box, 30)
    return [(text, match(ln, text, S.KEYBOARD_MULTI, S.KEYBOARD_SPLIT))], [ln]

FACES = ['Modern', 'ModernFI', 'Keyboard', 'Documentary', 'MidCentury', 'Arcadia', 'Doric', 'BoldFace1', 'BoldFace2', 'Charter']

def read(face):
    """occurrences of every character of a face, and the brochure's Modern for the unit calibration"""
    if face == 'Modern':
        return read_jowa()
    if face == 'Keyboard':    # Modern's @ # ¢ _, from the typed keyboard sheet
        return read_keyboard()
    if face == 'ModernFI':    # the brochure's Modern: for the unit calibration and the characters Jowa lacks
        return read_finnish('Modern')
    return read_finnish(face)

def contact(face, res, out):
    occ = [o for _, oc in res if oc for o in oc]
    cell = 90; cols = 24; rows = (len(occ) + cols - 1) // cols
    sheet = Image.new('L', (cols * cell, rows * cell), 255); d = ImageDraw.Draw(sheet)
    for i, o in enumerate(occ):
        im = Image.fromarray(((1 - o['ink']) * 255).astype(np.uint8))
        im.thumbnail((cell - 8, cell - 22))
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + 4, y + 18)); d.text((x + 3, y + 1), o['ch'], fill=0, font_size=16)
    sheet.save(out)

if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    for face in [a for a in sys.argv[1:] if a in FACES] or FACES:
        res, _ = read(face)
        bad = [(t, ) for t, oc in res if oc is None]
        n = sum(len(oc) for _, oc in res if oc)
        print(f'{face}: {len(res) - len(bad)}/{len(res)} lines matched, {n} characters')
        for t, oc in res:
            if oc is None: print('   unmatched:', t[:70])
        pickle.dump([(t, oc) for t, oc in res], open(os.path.join(BUILD, f'occ-{face}.pkl'), 'wb'))
        if 'contact' in sys.argv: contact(face, res, os.path.join(BUILD, f'contact-{face}.png'))

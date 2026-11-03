"""Single-sided placement + pin/gate assignment by simulated annealing (single board E.2).

Cost = MST length + XW * (net/net crossings + crossings through pin walls) + overlap/outside penalties.
A wall is a pair of pads of the same part whose copper gap is too small for one track (0.9 + 2 x 1.1 mm).
Moves: displace, rotate, swap two parts, swap two members of a pin/gate class.
Usage: python3 colocar.py SEED ITER OUT [inicio: d2|azar]
"""
import sys, os, json, math, random
import numpy as np
import base, pcbnew as k
from pcbnew import ToMM, VECTOR2I

SEED, ITER, OUT = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
INICIO = sys.argv[4] if len(sys.argv) > 4 else 'd2'
random.seed(SEED); np.random.seed(SEED)
W, H = base.W, base.H
GAP = 2.0; MARGEN = 1.5; PASO = 0.9 + 2 * 1.1
XW = float(os.environ.get('XW', 20))

b = base.construir()
partes = sorted(b.GetFootprints(), key=lambda f: f.GetReference())
REF = [f.GetReference() for f in partes]; NP = len(partes)
d2 = {f.GetReference(): (ToMM(f.GetPosition().x), ToMM(f.GetPosition().y), int(round(f.GetOrientationDegrees())) % 360 // 90) for f in partes}

def geom(f):
    out = []
    for r in range(4):
        f.SetPosition(VECTOR2I(0, 0)); f.SetOrientationDegrees(90 * r)
        cy = f.GetCourtyard(k.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        pads = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in f.Pads()]
        sz = [(ToMM(p.GetBoundingBox().GetWidth()), ToMM(p.GetBoundingBox().GetHeight())) for p in f.Pads()]
        out.append(dict(bb=(ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())), pads=np.array(pads), sz=np.array(sz)))
    return out
GEOM = [geom(f) for f in partes]
PADNUM = [[p.GetNumber() for p in f.Pads()] for f in partes]
PADNET0 = [[p.GetNetname() for p in f.Pads()] for f in partes]

nets = sorted({n for pn in PADNET0 for n in pn if n and not n.startswith('unconnected')})
NI = {n: i for i, n in enumerate(nets)}
pad_part, pad_idx, net0, key = [], [], [], {}
for i, pn in enumerate(PADNET0):
    for j, n in enumerate(pn):
        key[(REF[i], PADNUM[i][j])] = len(pad_part)
        pad_part.append(i); pad_idx.append(j); net0.append(NI[n] if n in NI else -1)
pad_part = np.array(pad_part); pad_idx = np.array(pad_idx)
CLASES = [[tuple(key[m] for m in memb) for memb in cl] for cl in base.clases(lambda r: PADNUM[REF.index(r)])]
CPESO = np.array([len(c) for c in CLASES], float); CPESO /= CPESO.sum()

# wall candidates: pad pairs inside a part (fixed per rotation)
PARES = []
for i in range(NP):
    sel = np.where(pad_part == i)[0]
    pr = []
    for r in range(4):
        g = GEOM[i][r]; lst = []
        for a in range(len(sel)):
            for c in range(a + 1, len(sel)):
                pa, pc = g['pads'][pad_idx[sel[a]]], g['pads'][pad_idx[sel[c]]]
                dx, dy = abs(pa[0] - pc[0]), abs(pa[1] - pc[1])
                if dx > dy: gap = dx - (g['sz'][pad_idx[sel[a]]][0] + g['sz'][pad_idx[sel[c]]][0]) / 2
                else: gap = dy - (g['sz'][pad_idx[sel[a]]][1] + g['sz'][pad_idx[sel[c]]][1]) / 2
                if gap < PASO and math.hypot(dx, dy) < 6: lst.append((sel[a], sel[c]))
        pr.append(lst)
    PARES.append(pr)

def pads_xy(pos):
    xy = np.empty((len(pad_part), 2))
    for t, (i, j) in enumerate(zip(pad_part, pad_idx)):
        g = GEOM[i][int(pos[i, 2])]['pads'][j]
        xy[t] = (pos[i, 0] + g[0], pos[i, 1] + g[1])
    return xy

def mst(pts):
    n = len(pts)
    if n < 2: return []
    d = np.hypot(*(pts[:, None, :] - pts[None, :, :]).transpose(2, 0, 1))
    en = np.zeros(n, bool); en[0] = True; best = d[0].copy(); par = np.zeros(n, int); e = []
    for _ in range(n - 1):
        best[en] = np.inf; j = int(np.argmin(best)); e.append((par[j], j)); en[j] = True
        upd = d[j] < best; par[upd] = j; best = np.minimum(best, d[j])
    return e

def cruces(A, B, same):
    p, r = A[:, None, :2], A[:, None, 2:] - A[:, None, :2]
    q, s = B[None, :, :2], B[None, :, 2:] - B[None, :, :2]
    rxs = r[..., 0] * s[..., 1] - r[..., 1] * s[..., 0]
    qp = q - p
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (qp[..., 0] * s[..., 1] - qp[..., 1] * s[..., 0]) / rxs
        u = (qp[..., 0] * r[..., 1] - qp[..., 1] * r[..., 0]) / rxs
    hit = (np.abs(rxs) > 1e-9) & (t > 0.02) & (t < 0.98) & (u > 0.02) & (u < 0.98) & ~same
    return int(hit.sum())

SALTAR = {NI[x] for x in os.environ.get('SALTAR', '').split(',') if x}
HB = [(hx - 3.5, hy - 3.5, hx + 3.5, hy + 3.5) for hx, hy in base.HOLES]
def costo(pos, pn, detalle=False):
    xy = pads_xy(pos)
    segs, sn, L = [], [], 0.0
    for n in range(len(nets)):
        if n in SALTAR: continue
        idx = np.where(pn == n)[0]
        for a, c in mst(xy[idx]):
            P, Q = xy[idx[a]], xy[idx[c]]
            segs.append((*P, *Q)); sn.append(n); L += math.hypot(*(P - Q))
    S = np.array(segs); sn = np.array(sn)
    X = cruces(S, S, sn[:, None] == sn[None, :]) // 2
    wl, wn = [], []
    for i in range(NP):
        for a, c in PARES[i][int(pos[i, 2])]:
            if pn[a] != pn[c] or pn[a] < 0:
                wl.append((*xy[a], *xy[c])); wn.append((pn[a], pn[c]))
    Wa = np.array(wl); wn = np.array(wn)
    same = (sn[:, None] == wn[None, :, 0]) | (sn[:, None] == wn[None, :, 1])
    Wc = cruces(S, Wa, same)
    bbs = []
    for i in range(NP):
        x0, y0, x1, y1 = GEOM[i][int(pos[i, 2])]['bb']
        bbs.append((pos[i, 0] + x0 - GAP / 2, pos[i, 1] + y0 - GAP / 2, pos[i, 0] + x1 + GAP / 2, pos[i, 1] + y1 + GAP / 2))
    B = np.array(bbs + HB)
    ox = np.clip(np.minimum(B[:, None, 2], B[None, :, 2]) - np.maximum(B[:, None, 0], B[None, :, 0]), 0, None)
    oy = np.clip(np.minimum(B[:, None, 3], B[None, :, 3]) - np.maximum(B[:, None, 1], B[None, :, 1]), 0, None)
    o = ox * oy; np.fill_diagonal(o, 0); ov = o[:NP].sum()
    m = MARGEN - GAP / 2
    fuera = (np.clip(m - B[:NP, 0], 0, None) + np.clip(B[:NP, 2] - (W - m), 0, None) + np.clip(m - B[:NP, 1], 0, None) + np.clip(B[:NP, 3] - (H - m), 0, None)).sum()
    c = L + XW * (X + Wc) + 40 * ov + 200 * fuera
    if detalle: return dict(L=round(L), cruces=X, muros=Wc, solape=round(float(ov), 2), fuera=round(float(fuera), 2), costo=round(c))
    return c

if INICIO == 'd2':
    pos = np.array([d2[r] for r in REF], float)
else:
    pos = np.array([[random.uniform(12, W - 12), random.uniform(12, H - 12), random.randrange(4)] for _ in range(NP)], float)
pn = np.array(net0)
c = costo(pos, pn); best = (c, pos.copy(), pn.copy())
T0, T1 = float(os.environ.get('T0', 60)), 0.3
for it in range(ITER):
    T = T0 * (T1 / T0) ** (it / ITER)
    npos, npn = pos, pn
    r = random.random()
    if r < 0.25:
        cl = CLASES[np.random.choice(len(CLASES), p=CPESO)]
        a, z = random.sample(range(len(cl)), 2); npn = pn.copy()
        npn[list(cl[a])], npn[list(cl[z])] = pn[list(cl[z])], pn[list(cl[a])]
        if (npn == pn).all(): continue
    elif r < 0.37:
        npos = pos.copy(); i = random.randrange(NP); npos[i, 2] = (npos[i, 2] + random.choice((1, 2, 3))) % 4
    elif r < 0.45:
        npos = pos.copy(); i, j = random.sample(range(NP), 2); npos[i, :2], npos[j, :2] = pos[j, :2].copy(), pos[i, :2].copy()
    else:
        npos = pos.copy(); i = random.randrange(NP); s = max(1.0, min(W, H) * 0.35 * T / T0)
        npos[i, 0] = np.clip(npos[i, 0] + random.gauss(0, s), 0, W); npos[i, 1] = np.clip(npos[i, 1] + random.gauss(0, s), 0, H)
    nc = costo(npos, npn)
    if nc < c or random.random() < math.exp((c - nc) / T):
        pos, pn, c = npos, npn, nc
        if c < best[0]: best = (c, pos.copy(), pn.copy())
    if it % 20000 == 0: print(SEED, it, round(c), costo(best[1], best[2], True), flush=True)
c, pos, pn = best
snap = pos.copy(); snap[:, :2] = np.round(snap[:, :2] / 1.27) * 1.27
if costo(snap, pn) <= c + 30: pos = snap
d = costo(pos, pn, True)
pines = []
for cl in CLASES:
    for memb in cl:
        for t in memb:
            r, j = REF[pad_part[t]], PADNUM[pad_part[t]][pad_idx[t]]
            pines.append([r, j, nets[pn[t]] if pn[t] >= 0 else None])
res = dict(seed=SEED, W=W, H=H, detalle=d, pines=pines,
           partes={r: dict(x=float(pos[i, 0]), y=float(pos[i, 1]), rot=90 * int(pos[i, 2])) for i, r in enumerate(REF)})
json.dump(res, open(OUT, 'w'), indent=1)
print('FIN', SEED, d, flush=True)

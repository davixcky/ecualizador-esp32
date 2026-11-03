"""Single-sided placement by simulated annealing.

Cost = MST length + weight * (crossings between different nets + crossings through pin "walls")
       + penalties for overlap / leaving the board.
Each crossing roughly becomes one bridge after routing, so the placer minimises them directly.
Usage: python3 colocar.py GROUP W H SEED ITER  -> placement JSON on stdout path
"""
import sys, json, math, random
import numpy as np
import comun, pcbnew as k
from pcbnew import ToMM, FromMM as MM, VECTOR2I

G, W, H, SEED, ITER = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
LADO = sys.argv[6] if len(sys.argv) > 6 else 'izq'
OUT = sys.argv[7] if len(sys.argv) > 7 else f'col-{G}-{SEED}.json'
random.seed(SEED); np.random.seed(SEED)
GAP = 2.0          # courtyard-to-courtyard spacing
WALL = 5.2         # pad pitch below which no track fits between two pads
XW = float(__import__('os').environ.get('XW', 14))
MARGEN = 1.5

b = comun.construir(G)
fps = [f for f in b.GetFootprints()]
partes = [f for f in fps if f.GetReference() != 'JX']
jx = next(f for f in fps if f.GetReference() == 'JX')
cruce = [p.GetNetname() for p in sorted(jx.Pads(), key=lambda p: int(p.GetNumber()))]
NJ = len(cruce)

def geom(f):
    out = []
    for r in range(4):
        f.SetPosition(VECTOR2I(0, 0)); f.SetOrientationDegrees(90 * r)
        cy = f.GetCourtyard(k.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        pads = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in f.Pads()]
        out.append(dict(bb=(ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())), pads=np.array(pads)))
    return out

GEOM = [geom(f) for f in partes]
PADNET = [[p.GetNetname() for p in f.Pads()] for f in partes]
NP = len(partes)
nets = sorted({n for pn in PADNET for n in pn if n and not n.startswith('unconnected')} | set(cruce))
NI = {n: i for i, n in enumerate(nets)}
# pad table
pad_part, pad_idx, pad_net = [], [], []
for i, pn in enumerate(PADNET):
    for j, n in enumerate(pn):
        if n and not n.startswith('unconnected'):
            pad_part.append(i); pad_idx.append(j); pad_net.append(NI[n])
pad_part = np.array(pad_part); pad_idx = np.array(pad_idx); pad_net = np.array(pad_net)
# header pins: fixed column on one edge, centred; pin i carries net perm[i]
x_jx = MARGEN + 2.5 if LADO == 'izq' else W - MARGEN - 2.5
y0 = H / 2 - (NJ - 1) * 2.54 / 2
JXP = np.array([[x_jx, y0 + 2.54 * i] for i in range(NJ)])
JXBB = (x_jx - 1.8 - GAP / 2, y0 - 1.8 - GAP / 2, x_jx + 1.8 + GAP / 2, y0 + 2.54 * (NJ - 1) + 1.8 + GAP / 2)
HOLES = [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]

def inicial():
    pos = []
    for i in range(NP):
        pos.append([random.uniform(10, W - 10), random.uniform(10, H - 10), random.randrange(4)])
    return np.array(pos, dtype=float)

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
    """Proper segment intersections between rows of A (n,4) and B (m,4); same[n,m] masks out pairs."""
    p, r = A[:, None, :2], A[:, None, 2:] - A[:, None, :2]
    q, s = B[None, :, :2], B[None, :, 2:] - B[None, :, :2]
    rxs = r[..., 0] * s[..., 1] - r[..., 1] * s[..., 0]
    qp = q - p
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (qp[..., 0] * s[..., 1] - qp[..., 1] * s[..., 0]) / rxs
        u = (qp[..., 0] * r[..., 1] - qp[..., 1] * r[..., 0]) / rxs
    hit = (np.abs(rxs) > 1e-9) & (t > 0.02) & (t < 0.98) & (u > 0.02) & (u < 0.98) & ~same
    return int(hit.sum())

def costo(pos, perm, detalle=False):
    xy = pads_xy(pos)
    allxy = np.vstack([xy, JXP]); alln = np.concatenate([pad_net, np.array([NI[cruce[p]] for p in perm])])
    segs, sn = [], []
    L = 0.0
    for n in range(len(nets)):
        idx = np.where(alln == n)[0]
        for a, c in mst(allxy[idx]):
            P, Q = allxy[idx[a]], allxy[idx[c]]
            segs.append((*P, *Q)); sn.append(n); L += math.hypot(*(P - Q))
    S = np.array(segs); sn = np.array(sn)
    X = cruces(S, S, sn[:, None] == sn[None, :]) // 2
    # walls: neighbouring pads of different nets too close for a track (same part, and header pins)
    wl, wn = [], []
    for i in range(NP):
        sel = np.where(pad_part == i)[0]
        for a in range(len(sel)):
            for c in range(a + 1, len(sel)):
                pa, pc = xy[sel[a]], xy[sel[c]]
                if math.hypot(*(pa - pc)) < WALL and pad_net[sel[a]] != pad_net[sel[c]]:
                    wl.append((*pa, *pc)); wn.append((pad_net[sel[a]], pad_net[sel[c]]))
    for i in range(NJ - 1):
        wl.append((*JXP[i], *JXP[i + 1])); wn.append((NI[cruce[perm[i]]], NI[cruce[perm[i + 1]]]))
    Wc = 0
    if wl:
        Wa = np.array(wl); wn = np.array(wn)
        same = (sn[:, None] == wn[None, :, 0]) | (sn[:, None] == wn[None, :, 1])
        Wc = cruces(S, Wa, same)
    # overlap / bounds
    ov = 0.0
    bbs = []
    for i in range(NP):
        x0, y0_, x1, y1 = GEOM[i][int(pos[i, 2])]['bb']
        bbs.append((pos[i, 0] + x0 - GAP / 2, pos[i, 1] + y0_ - GAP / 2, pos[i, 0] + x1 + GAP / 2, pos[i, 1] + y1 + GAP / 2))
    bbs.append(JXBB)
    for hx, hy in HOLES: bbs.append((hx - 3.5, hy - 3.5, hx + 3.5, hy + 3.5))
    B = np.array(bbs)
    ox = np.clip(np.minimum(B[:, None, 2], B[None, :, 2]) - np.maximum(B[:, None, 0], B[None, :, 0]), 0, None)
    oy = np.clip(np.minimum(B[:, None, 3], B[None, :, 3]) - np.maximum(B[:, None, 1], B[None, :, 1]), 0, None)
    o = ox * oy; np.fill_diagonal(o, 0); ov = o[:NP].sum()  # fixed items do not overlap each other
    m = MARGEN - GAP / 2
    fuera = (np.clip(m - B[:NP, 0], 0, None) + np.clip(B[:NP, 2] - (W - m), 0, None) + np.clip(m - B[:NP, 1], 0, None) + np.clip(B[:NP, 3] - (H - m), 0, None)).sum()
    c = L + XW * (X + Wc) + 40 * ov + 200 * fuera
    if detalle: return dict(L=round(L), cruces=X, muros=Wc, solape=round(float(ov), 2), fuera=round(float(fuera), 2), costo=round(c))
    return c

pos = inicial(); perm = list(range(NJ)); random.shuffle(perm)
c = costo(pos, perm); best = (c, pos.copy(), perm[:])
T0, T1 = 60.0, 0.3
for it in range(ITER):
    T = T0 * (T1 / T0) ** (it / ITER)
    npos, nperm = pos.copy(), perm[:]
    r = random.random()
    if r < 0.12 and NJ > 1:
        a, z = random.sample(range(NJ), 2); nperm[a], nperm[z] = nperm[z], nperm[a]
    elif r < 0.25:
        i = random.randrange(NP); npos[i, 2] = (npos[i, 2] + random.choice((1, 2, 3))) % 4
    elif r < 0.33:
        i, j = random.sample(range(NP), 2); npos[i, :2], npos[j, :2] = pos[j, :2].copy(), pos[i, :2].copy()
    else:
        i = random.randrange(NP); s = max(1.0, min(W, H) * 0.4 * T / T0)
        npos[i, 0] = np.clip(npos[i, 0] + random.gauss(0, s), 0, W); npos[i, 1] = np.clip(npos[i, 1] + random.gauss(0, s), 0, H)
    nc = costo(npos, nperm)
    if nc < c or random.random() < math.exp((c - nc) / T):
        pos, perm, c = npos, nperm, nc
        if c < best[0]: best = (c, pos.copy(), perm[:])
c, pos, perm = best
# snap to 1.27 mm grid, keep if not worse by much
snap = pos.copy(); snap[:, :2] = np.round(snap[:, :2] / 1.27) * 1.27
if costo(snap, perm) <= c + 30: pos = snap
d = costo(pos, perm, True)
res = dict(grupo=G, W=W, H=H, seed=SEED, lado=LADO, detalle=d,
           partes={f.GetReference(): dict(x=float(pos[i, 0]), y=float(pos[i, 1]), rot=90 * int(pos[i, 2])) for i, f in enumerate(partes)},
           jx=dict(x=x_jx, y0=y0, redes=[cruce[p] for p in perm]))
json.dump(res, open(OUT, 'w'), indent=1)
print(G, SEED, d, flush=True)

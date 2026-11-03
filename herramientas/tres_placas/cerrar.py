"""Close every connection the router left open with a wire between the nearest pads of the two islands.
The wire footprint's holes coincide with existing component pads (same net), as in D.2 (JP67-JP79).
Usage: python3 cerrar.py routed_dir final_dir
"""
import sys, json, shutil, subprocess, math
from pathlib import Path
import comun, pcbnew as k
from pcbnew import ToMM
import motor_freerouting as motor, pcb_freerouting as pf
SRC, DST = Path(sys.argv[1]), Path(sys.argv[2]); DST.mkdir(parents=True, exist_ok=True)
pcb = next(SRC.glob('*.kicad_pcb'))
b = k.LoadBoard(str(pcb))
d = json.load(open(SRC / 'drc.json'))
by_uuid = {}
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[p.m_Uuid.AsString()] = p
for t in b.GetTracks(): by_uuid[t.m_Uuid.AsString()] = t
from shapely.geometry import LineString, Point
def forma(it):
    if it.Type() == k.PCB_PAD_T:
        return it.GetEffectivePolygon(k.B_Cu).Outline(0) and Point(ToMM(it.GetPosition().x), ToMM(it.GetPosition().y)).buffer(ToMM(min(it.GetSize(k.B_Cu).x, it.GetSize(k.B_Cu).y)) / 2)
    a, e = it.GetStart(), it.GetEnd()
    return LineString([(ToMM(a.x), ToMM(a.y)), (ToMM(e.x), ToMM(e.y))]).buffer(ToMM(it.GetWidth()) / 2)
def isla(item):
    net = item.GetNetCode()
    cobre = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == net] + [t for t in b.GetTracks() if t.GetNetCode() == net and t.GetLayer() == k.B_Cu]
    sh = [forma(c) for c in cobre]
    par = list(range(len(cobre)))
    def r(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(cobre)):
        for j in range(i + 1, len(cobre)):
            if sh[i].distance(sh[j]) < 1e-3: par[r(i)] = r(j)
    # bridge footprints join their pads electrically too
    for f in b.GetFootprints():
        if f.GetReference().startswith('JP'):
            idx = [cobre.index(p) for p in f.Pads() if p in cobre]
            for x in idx[1:]: par[r(x)] = r(idx[0])
    me = cobre.index(item) if item in cobre else min(range(len(cobre)), key=lambda i: sh[i].distance(forma(item)))
    pads = [c for i, c in enumerate(cobre) if r(i) == r(me) and c.Type() == k.PCB_PAD_T]
    comp = [p for p in pads if not p.GetParentFootprint().GetReference().startswith('JP')]
    return comp or pads

n0 = len([f for f in b.GetFootprints() if f.GetReference().startswith('JP')])
hechos = []
for i, u in enumerate(d['unconnected_items'], start=1):
    a, z = (by_uuid[it['uuid']] for it in u['items'])
    pa, pz = isla(a), isla(z)
    best = min(((p, q) for p in pa for q in pz), key=lambda pq: (pq[0].GetPosition() - pq[1].GetPosition()).EuclideanNorm())
    P = (round(ToMM(best[0].GetPosition().x), 4), round(ToMM(best[0].GetPosition().y), 4))
    Q = (round(ToMM(best[1].GetPosition().x), 4), round(ToMM(best[1].GetPosition().y), 4))
    ref = f'JP{n0 + i}'
    motor.agregar_puente(b, ref, best[0].GetNet(), [P, Q], [(P, Q)])
    fp = next(f for f in b.GetFootprints() if f.GetReference() == ref)
    for bp, cp in zip(sorted(fp.Pads(), key=lambda x: (x.GetPosition().x, x.GetPosition().y)), sorted(best, key=lambda x: (x.GetPosition().x, x.GetPosition().y))):
        bp.SetShape(k.F_Cu, cp.GetShape(k.B_Cu)); bp.SetSize(k.F_Cu, cp.GetSize(k.B_Cu)); bp.SetOrientation(cp.GetOrientation())
        bp.SetDrillSize(cp.GetDrillSize())
    hechos.append(dict(ref=ref, red=best[0].GetNetname(), de=f"{best[0].GetParentFootprint().GetReference()}.{best[0].GetNumber()}",
                       a=f"{best[1].GetParentFootprint().GetReference()}.{best[1].GetNumber()}", largo_mm=round(math.dist(P, Q), 1)))
out = DST / pcb.name
b.Save(str(out)); pf.reglas(out.with_suffix('.kicad_pro'))
shutil.copy(SRC / 'puentes.json', DST / 'puentes-ruteados.json')
json.dump(hechos, open(DST / 'alambres-directos.json', 'w'), indent=1)
rep = DST / 'drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', str(out), '--format', 'json', '-o', str(rep)], capture_output=True)
r = json.load(open(rep))
err = {}
for v in r['violations']:
    if v['severity'] == 'error': err[v['type']] = err.get(v['type'], 0) + 1
print(json.dumps(dict(placa=out.name, directos=len(hechos), sin_conectar=len(r['unconnected_items']), errores=err)))

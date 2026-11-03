"""Close every split net with direct wires between component pads (zone-aware).
Copper islands per net = pads + B.Cu tracks + filled zone polygons (with holes), joined by existing JP wires.
Islands are joined by a minimum spanning tree over the nearest component-pad pair; each edge = one wire JPn
whose holes coincide with the two component pads. Then refill and DRC.
Usage: python3 cerrar2.py routed_dir final_dir
"""
import sys, json, shutil, subprocess, math
from pathlib import Path
import base, pcbnew as k
from pcbnew import ToMM
import motor_freerouting as motor, pcb_freerouting as pf
from shapely.geometry import LineString, Point, Polygon
SRC, DST = Path(sys.argv[1]), Path(sys.argv[2]); DST.mkdir(parents=True, exist_ok=True)
pcb = next(SRC.glob('*.kicad_pcb'))
b = k.LoadBoard(str(pcb))

def poly(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i); ext = [(ToMM(o.CPoint(j).x), ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]
        holes = []
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h); holes.append([(ToMM(hh.CPoint(j).x), ToMM(hh.CPoint(j).y)) for j in range(hh.PointCount())])
        out.append(Polygon(ext, holes).buffer(0))
    return out

def padshape(p):
    return Point(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)).buffer(ToMM(min(p.GetSize(k.B_Cu).x, p.GetSize(k.B_Cu).y)) / 2)

nets = {}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() > 0: nets.setdefault(p.GetNetname(), []).append(p)
n0 = len([f for f in b.GetFootprints() if f.GetReference().startswith('JP')])
hechos = []
for net, pads in sorted(nets.items()):
    items = [('p', p, padshape(p)) for p in pads]
    for t in b.GetTracks():
        if t.GetNetname() == net and t.Type() == k.PCB_TRACE_T and t.GetLayer() == k.B_Cu:
            a, e = t.GetStart(), t.GetEnd()
            items.append(('t', t, LineString([(ToMM(a.x), ToMM(a.y)), (ToMM(e.x), ToMM(e.y))]).buffer(ToMM(t.GetWidth()) / 2)))
    for z in b.Zones():
        if z.GetNetname() == net and not z.GetIsRuleArea():
            for pg in poly(z.GetFilledPolysList(k.B_Cu)): items.append(('z', z, pg))
    par = list(range(len(items)))
    def r(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][2].distance(items[j][2]) < 1e-3: par[r(i)] = r(j)
    for f in b.GetFootprints():
        if f.GetReference().startswith('JP'):
            idx = [i for i, it in enumerate(items) if it[0] == 'p' and it[1].GetParentFootprint().GetReference() == f.GetReference()]
            for x in idx[1:]: par[r(x)] = r(idx[0])
    comps = {}
    for i, it in enumerate(items):
        if it[0] == 'p' and not it[1].GetParentFootprint().GetReference().startswith('JP'):
            comps.setdefault(r(i), []).append(it[1])
    grupos = list(comps.values())
    if len(grupos) < 2: continue
    # Kruskal over islands
    aristas = []
    for i in range(len(grupos)):
        for j in range(i + 1, len(grupos)):
            d, P, Q = min(((p.GetPosition() - q.GetPosition()).EuclideanNorm(), p, q) for p in grupos[i] for q in grupos[j])
            aristas.append((d, i, j, P, Q))
    gp = list(range(len(grupos)))
    def g(i):
        while gp[i] != i: gp[i] = gp[gp[i]]; i = gp[i]
        return i
    for d, i, j, P, Q in sorted(aristas, key=lambda x: x[0]):
        if g(i) == g(j): continue
        gp[g(i)] = g(j)
        A = (round(ToMM(P.GetPosition().x), 4), round(ToMM(P.GetPosition().y), 4)); B = (round(ToMM(Q.GetPosition().x), 4), round(ToMM(Q.GetPosition().y), 4))
        ref = f'JP{n0 + len(hechos) + 1}'
        motor.agregar_puente(b, ref, P.GetNet(), [A, B], [(A, B)])
        fp = next(f for f in b.GetFootprints() if f.GetReference() == ref)
        for bp, cp in zip(sorted(fp.Pads(), key=lambda x: (x.GetPosition().x, x.GetPosition().y)), sorted((P, Q), key=lambda x: (x.GetPosition().x, x.GetPosition().y))):
            bp.SetShape(k.F_Cu, cp.GetShape(k.B_Cu)); bp.SetSize(k.F_Cu, cp.GetSize(k.B_Cu)); bp.SetOrientation(cp.GetOrientation()); bp.SetDrillSize(cp.GetDrillSize())
        hechos.append(dict(ref=ref, red=net, de=f"{P.GetParentFootprint().GetReference()}.{P.GetNumber()}",
                           a=f"{Q.GetParentFootprint().GetReference()}.{Q.GetNumber()}", largo_mm=round(math.dist(A, B), 1)))
out = DST / pcb.name
b.Save(str(out)); pf.reglas(out.with_suffix('.kicad_pro'))
for extra in ('puentes.json',):
    if (SRC / extra).exists(): shutil.copy(SRC / extra, DST / 'puentes-ruteados.json')
json.dump(hechos, open(DST / 'alambres-directos.json', 'w'), indent=1)
subprocess.run([sys.executable, str(Path(__file__).parent / 'rellenar.py'), str(out)], capture_output=True)
rep = DST / 'drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', str(out), '--format', 'json', '-o', str(rep)], capture_output=True)
rr = json.load(open(rep)); err = {}
for v in rr['violations']:
    if v['severity'] == 'error': err[v['type']] = err.get(v['type'], 0) + 1
ruteados = sum(len(x['alambres']) for x in json.load(open(SRC / 'puentes.json'))) if (SRC / 'puentes.json').exists() else 0
print(json.dumps(dict(placa=str(SRC), ruteados=ruteados, directos=len(hechos), total=ruteados + len(hechos), sin_conectar=len(rr['unconnected_items']), errores=err)))

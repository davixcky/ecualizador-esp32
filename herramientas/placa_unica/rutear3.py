"""Route every net except GND single-sided (Freerouting, bridges on F.Cu), then flood B.Cu with GND.
Usage: python3 rutear3.py placement.json outdir"""
import os, sys, json, re, subprocess
from pathlib import Path
col = json.load(open(sys.argv[1])); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('JUMPER_COST', '20'); os.environ.setdefault('VIA_COST', '60')
import base, pcbnew as k
from pcbnew import FromMM as MM, ToMM, VECTOR2I
import motor_freerouting as motor, pcb_freerouting as pf
motor.W, motor.H = base.W, base.H
NOMBRE = 'ecualizador-E2'
jar = str(Path.home() / '.local/share/freerouting/freerouting.jar')

def pour(b):
    z = k.ZONE(b); z.SetLayer(k.B_Cu); z.SetNet(b.FindNet('GND'))
    o = z.Outline(); o.NewOutline()
    for x, y in [(1.0, 1.0), (base.W - 1, 1.0), (base.W - 1, base.H - 1), (1.0, base.H - 1)]: o.Append(MM(x), MM(y))
    z.SetPadConnection(k.ZONE_CONNECTION_FULL); z.SetLocalClearance(MM(float(os.environ.get('CL', 1.1)))); z.SetMinThickness(MM(.9))
    z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(0); b.Add(z)
    # ESP32 antenna: no copper under it (from 12 mm beyond pin 1 to 3 mm past it, across both rows)
    u5 = next(f for f in b.GetFootprints() if f.GetReference() == 'U5')
    p1 = next(p for p in u5.Pads() if p.GetNumber() == '1'); p20 = next(p for p in u5.Pads() if p.GetNumber() == '38')
    a = k.ZONE(b); a.SetIsRuleArea(True); a.SetLayer(k.B_Cu); a.SetDoNotAllowZoneFills(True)
    a.SetDoNotAllowTracks(False); a.SetDoNotAllowVias(False); a.SetDoNotAllowPads(False); a.SetDoNotAllowFootprints(False)
    o = a.Outline(); o.NewOutline()
    P1 = (ToMM(p1.GetPosition().x), ToMM(p1.GetPosition().y)); P2 = (ToMM(p20.GetPosition().x), ToMM(p20.GetPosition().y))
    # unit vector along the module towards the antenna (away from pin 2)
    p2 = next(p for p in u5.Pads() if p.GetNumber() == '2'); Q = (ToMM(p2.GetPosition().x), ToMM(p2.GetPosition().y))
    ux, uy = (P1[0] - Q[0]) / 2.54, (P1[1] - Q[1]) / 2.54
    vx, vy = P2[0] - P1[0], P2[1] - P1[1]
    for s, t in [(-3, -0.06), (12, -0.06), (12, 1.06), (-3, 1.06)]:
        o.Append(MM(P1[0] + ux * s + vx * t), MM(P1[1] + uy * s + vy * t))
    b.Add(a)
    pass

b = base.construir(base.overrides_de(col)); base.colocar(b, col)
if os.environ.get('CL'):
    cl = float(os.environ['CL']); ds = b.GetDesignSettings(); ds.m_MinClearance = MM(cl)
    for nc in [ds.m_NetSettings.GetDefaultNetclass(), ds.m_NetSettings.GetNetClassByName('Alimentacion')]:
        nc.SetClearance(MM(cl))
    ds.m_NetSettings.GetNetClassByName('Alimentacion').SetTrackWidth(MM(float(os.environ.get('PW', 1.0))))
gnd = b.FindNet('GND'); padsg = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND']
if not os.environ.get('CONGND'):
    for p in padsg: p.SetNetCode(0)
dsn = OUT / 'r.dsn'; ses = OUT / 'r.ses'
k.ExportSpecctraDSN(b, str(dsn)); (None if os.environ.get('DOBLE') else dsn.write_text(motor.preparar_dsn(dsn.read_text())))
if os.environ.get('SOLOABAJO'):
    import restringir; dsn.write_text(restringir.restringir(dsn.read_text()))
if not (os.environ.get('REUSAR') and ses.exists()):
  with (OUT / 'fr.log').open('w') as log:
    subprocess.run(['java', '-Xmx2G', '-jar', jar, '-de', str(dsn), '-do', str(ses), '--router.autorouter.max_passes=' + os.environ.get('FR_PASES', '60'), '-mt', '1',
                    '--gui.enabled=false', '--router.automatic_neckdown=false', '--router.fanout.enabled=false', '--router.optimizer.max_passes=6', '--router.optimizer.max_threads=1'],
                   stdout=log, stderr=subprocess.STDOUT, timeout=2400)
fin = re.findall(r'\((\d+) unrouted and (\d+) violations\)', (OUT / 'fr.log').read_text())
u = int(fin[-1][0]) if fin else -1
print("imp",flush=True); k.ImportSpecctraSES(b, str(ses)); print("ok imp",flush=True)
if os.environ.get('DOBLE'):
    vias=[t for t in b.GetTracks() if t.Type()==k.PCB_VIA_T]; top=sum(ToMM(t.GetLength()) for t in b.GetTracks() if t.Type()==k.PCB_TRACE_T and t.GetLayer()==k.F_Cu)
    print(json.dumps(dict(src=sys.argv[1], doble=True, unrouted=u, vias=len(vias), mm_arriba=round(top)))); sys.exit(0)
lista = motor.hacer_puentes(b)
for p in padsg: p.SetNet(gnd)
print("pour",flush=True); pour(b); print("ok pour",flush=True)
pcb = OUT / f'{NOMBRE}.kicad_pcb'; b.Save(str(pcb)); pf.reglas(pcb.with_suffix('.kicad_pro'))
json.dump([dict(ref=r, red=n, puntos=p, alambres=e) for r, n, p, e in lista], open(OUT / 'puentes.json', 'w'), indent=1)
subprocess.run([sys.executable, str(Path(__file__).parent / 'rellenar.py'), str(pcb)], capture_output=True)
rep = OUT / 'drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', str(pcb), '--format', 'json', '-o', str(rep)], capture_output=True)
d = json.load(open(rep)); tipos = {}; abiertos = {}
for v in d['violations']:
    if v['severity'] == 'error': tipos[v['type']] = tipos.get(v['type'], 0) + 1
for x in d['unconnected_items']:
    n = re.search(r"\[([^\]]+)\]", x['items'][0]['description']); n = n.group(1) if n else '?'; abiertos[n] = abiertos.get(n, 0) + 1
print(json.dumps(dict(src=Path(sys.argv[1]).name, unrouted_fr=u, sin_conectar=len(d['unconnected_items']), abiertos=abiertos, errores=tipos,
                      puentes=len(lista), alambres=sum(len(x[3]) for x in lista))), flush=True)

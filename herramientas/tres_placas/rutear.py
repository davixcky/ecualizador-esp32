"""Build a group's board from a placement JSON, route single-sided with Freerouting, make bridges, run DRC.
Usage: python3 rutear.py placement.json outdir [jumper_cost]
"""
import os, sys, json, re, subprocess
from pathlib import Path
col = json.load(open(sys.argv[1])); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
os.environ['JUMPER_COST'] = sys.argv[3] if len(sys.argv) > 3 else '20'
import comun, pcbnew as k
from pcbnew import FromMM as MM, ToMM, VECTOR2I
import motor_freerouting as motor, pcb_legado_b1 as base, pcb_freerouting as pf
G, W, H = col['grupo'], col['W'], col['H']
motor.W, motor.H = W, H
NOMBRE = {'A': 'ecualizador-A-audio', 'B': 'ecualizador-B-detectores', 'C': 'ecualizador-C-control'}[G]

def construir():
    b = comun.construir(G)
    for f in b.GetFootprints():
        r = f.GetReference()
        if r == 'JX':
            f.SetOrientationDegrees(0); f.SetPosition(VECTOR2I(MM(col['jx']['x']), MM(col['jx']['y0'])))
            for p in f.Pads(): p.SetNet(b.FindNet(col['jx']['redes'][int(p.GetNumber()) - 1]))
            f.SetValue('Conector entre placas')
        else:
            q = col['partes'][r]; f.SetOrientationDegrees(q['rot']); f.SetPosition(VECTOR2I(MM(q['x']), MM(q['y'])))
            f.Reference().SetPosition(f.GetPosition() + VECTOR2I(MM(1), MM(-2)))
    for xy in [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]: base.agujero(b, *xy)
    base.linea(b, k.Edge_Cuts, [(0, 0), (W, 0), (W, H), (0, H), (0, 0)], .1)
    t = b.GetTitleBlock(); t.SetTitle(f'Ecualizador - placa {G} (CNC una cara)'); t.SetRevision('E.1'); t.SetCompany('CUC')
    return b

b = construir()
if os.environ.get('FINO'):
    tw,cl=[float(x) for x in os.environ['FINO'].split(',')]
    ds=b.GetDesignSettings();ds.m_MinClearance=MM(cl);ds.m_TrackMinWidth=MM(tw)
    for nc in [ds.m_NetSettings.GetDefaultNetclass(),ds.m_NetSettings.GetNetClassByName('Alimentacion')]:
        nc.SetTrackWidth(MM(max(tw,0.8) if nc.GetName()=='Alimentacion' else tw));nc.SetClearance(MM(cl))
dsn = OUT / f'{NOMBRE}.dsn'; ses = OUT / f'{NOMBRE}.ses'
k.ExportSpecctraDSN(b, str(dsn))
if not os.environ.get('DOBLE'): dsn.write_text(motor.preparar_dsn(dsn.read_text()))
if ses.exists(): ses.unlink()
jar = str(Path.home() / '.local/share/freerouting/freerouting.jar')
with (OUT / 'freerouting.log').open('w') as log:
    subprocess.run(['java', '-Xmx2G', '-jar', jar, '-de', str(dsn), '-do', str(ses), '--router.autorouter.max_passes='+os.environ.get('FR_PASES', '60'), '-mt', '2',
                    '--gui.enabled=false', '--router.automatic_neckdown=false', '--router.fanout.enabled='+os.environ.get('FR_FANOUT','false'), '--router.optimizer.max_passes=8', '--router.optimizer.max_threads=2'],
                   stdout=log, stderr=subprocess.STDOUT, timeout=1500)
txt = (OUT / 'freerouting.log').read_text()
fin = re.findall(r'\((\d+) unrouted and (\d+) violations\)', txt)
unrouted = int(fin[-1][0]) if fin else -1
if not ses.exists(): print(json.dumps(dict(grupo=G, src=sys.argv[1], error='sin sesion', unrouted=unrouted))); sys.exit(1)
k.ImportSpecctraSES(b, str(ses))
if os.environ.get('DOBLE'):
    vias=[t for t in b.GetTracks() if t.Type()==k.PCB_VIA_T];top=sum(ToMM(t.GetLength()) for t in b.GetTracks() if t.Type()==k.PCB_TRACE_T and t.GetLayer()==k.F_Cu)
    print(json.dumps(dict(grupo=G,doble=True,unrouted_fr=unrouted,vias=len(vias),mm_arriba=round(top))));sys.exit(0)
lista = motor.hacer_puentes(b)
pcb = OUT / f'{NOMBRE}.kicad_pcb'; b.Save(str(pcb)); pf.reglas(pcb.with_suffix('.kicad_pro'))
json.dump([dict(ref=r, red=n, puntos=p, alambres=e) for r, n, p, e in lista], open(OUT / 'puentes.json', 'w'), indent=1)
rep = OUT / 'drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', str(pcb), '--format', 'json', '--schematic-parity', '-o', str(rep)], capture_output=True)
d = json.load(open(rep))
errs = [v for v in d['violations'] if v['severity'] == 'error']
tipos = {}
for v in errs: tipos[v['type']] = tipos.get(v['type'], 0) + 1
alambres = sum(len(x[3]) for x in lista)
print(json.dumps(dict(grupo=G, src=Path(sys.argv[1]).name, unrouted_fr=unrouted, sin_conectar=len(d['unconnected_items']), errores=tipos,
                      puentes=len(lista), alambres=alambres)), flush=True)

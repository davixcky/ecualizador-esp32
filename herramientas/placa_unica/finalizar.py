"""Package single board E.2: pin labels on headers, fabrication files, wire list, pin map, firmware config, renders.
Usage: python3 finalizar.py closed_dir placement.json OUT"""
import sys, json, csv, math, shutil, subprocess
from pathlib import Path
import base, pcbnew as k
from pcbnew import FromMM as MM, ToMM, VECTOR2I
import pcb_freerouting as pf, pcb_legado_b1 as lb
SRC, COL, OUT = Path(sys.argv[1]), json.load(open(sys.argv[2])), Path(sys.argv[3])
(OUT / 'placa').mkdir(parents=True, exist_ok=True); (OUT / 'fabricacion').mkdir(exist_ok=True); (OUT / 'vistas').mkdir(exist_ok=True); (OUT / 'firmware').mkdir(exist_ok=True)
b = k.LoadBoard(str(next(SRC.glob('*.kicad_pcb'))))
pn0, _ = base.netlist_base()
ETQ = {'J1': {'T': 'T', 'R': 'R', 'S': 'S'}, 'J2': {'T': 'T', 'R': 'R', 'S': 'S'},
       'J3': {'1': '5V', '2': 'GND', '3': 'IN', '4': 'GND'}, 'J5': {'1': '5V', '2': 'DIN', '3': 'GND'},
       'J4': {'1': 'VCC', '2': 'GND', '3': 'DIN', '4': 'CLK', '5': 'CS', '6': 'DC', '7': 'RST', '8': 'BL'},
       'SW1': {'1': 'SW', '2': 'GND'}}
for r in ('RV1', 'RV2', 'RV3', 'RV4', 'RV5'): ETQ[r] = {'1': '1', '2': 'W', '3': '3'}
FP = {f.GetReference(): f for f in b.GetFootprints()}
tabla = []
for r, et in ETQ.items():
    f = FP[r]; pads = sorted(f.Pads(), key=lambda p: p.GetNumber())
    porred = {}
    for num, lab in et.items(): porred.setdefault(pn0[(r, num)], lab)
    xs = [ToMM(p.GetPosition().x) for p in pads]; ys = [ToMM(p.GetPosition().y) for p in pads]
    vertical = (max(ys) - min(ys)) >= (max(xs) - min(xs))
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    for p in pads:
        lab = porred[p.GetNetname()]
        x, y = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
        if vertical: tx, ty = (x - 3.2 if cx < base.W / 2 else x + 3.2), y
        else: tx, ty = x, (y - 2.8 if cy < base.H / 2 else y + 2.8)
        t = k.PCB_TEXT(b); t.SetText(lab); t.SetLayer(k.F_SilkS); t.SetPosition(VECTOR2I(MM(tx), MM(ty)))
        t.SetTextSize(VECTOR2I(MM(1.0), MM(1.0))); t.SetTextThickness(MM(0.15)); b.Add(t)
        tabla.append(dict(conector=r, pin=p.GetNumber(), etiqueta=lab, red=p.GetNetname()))
tb = b.GetTitleBlock(); tb.SetTitle('Ecualizador - placa unica CNC una cara'); tb.SetRevision('E.2'); tb.SetCompany('CUC'); tb.SetDate('2026-11-03')
pcb = OUT / 'placa' / 'ecualizador-E2.kicad_pcb'; b.Save(str(pcb)); pf.reglas(pcb.with_suffix('.kicad_pro'))
subprocess.run([sys.executable, str(Path(__file__).parent / 'rellenar.py'), str(pcb)], capture_output=True)
for fn in ('alambres-directos.json', 'puentes-ruteados.json'): shutil.copy(SRC / fn, OUT / 'placa' / fn)
# DRC
rep = OUT / 'placa' / 'drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', str(pcb), '--format', 'json', '-o', str(rep)], capture_output=True)
d = json.load(open(rep)); err = {}
for v in d['violations']: err.setdefault(v['severity'], {}).setdefault(v['type'], 0); err[v['severity']][v['type']] += 1
# wire list (routed bridges + direct wires)
import itertools
filas = []
for x in json.load(open(SRC / 'puentes-ruteados.json')):
    for a, z in x['alambres']: filas.append([x['ref'], x['red'], 'ruteado', f'({a[0]:.1f},{a[1]:.1f})', f'({z[0]:.1f},{z[1]:.1f})', round(math.dist(a, z), 1)])
for x in json.load(open(SRC / 'alambres-directos.json')):
    filas.append([x['ref'], x['red'], 'pad a pad', x['de'], x['a'], x['largo_mm']])
with open(OUT / 'alambres.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['puente', 'red', 'tipo', 'desde', 'hasta', 'largo_mm']); w.writerows(filas)
with open(OUT / 'etiquetas-conectores.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['conector', 'pin', 'etiqueta', 'red']); w.writeheader(); w.writerows(tabla)
# fabrication
fab = OUT / 'fabricacion'
subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', str(pcb), '-o', str(fab) + '/', '-l', 'B.Cu,Edge.Cuts'], capture_output=True)
subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', str(pcb), '-o', str(fab) + '/', '--generate-map'], capture_output=True)
for drill in fab.glob('*.drl'):
    seen = set(); tool = ''; lines = []
    for line in drill.read_text().splitlines():
        if line.startswith('T') and 'C' not in line: tool = line
        if line.startswith('X'):
            if (tool, line) in seen: continue
            seen.add((tool, line))
        lines.append(line)
    drill.write_text('\n'.join(lines) + '\n')
subprocess.run(['kicad-cli', 'pcb', 'export', 'pdf', str(pcb), '-o', str(fab / 'cobre-B.Cu-1a1.pdf'), '-l', 'B.Cu,Edge.Cuts', '--mode-single', '--scale', '1'], capture_output=True)
subprocess.run(['kicad-cli', 'pcb', 'export', 'pdf', str(pcb), '-o', str(fab / 'montaje-cara-componentes.pdf'), '-l', 'F.SilkS,F.Fab,Edge.Cuts', '--mode-single', '--scale', '0'], capture_output=True)
# views
V = OUT / 'vistas'
for nombre, capas in (('cobre', 'B.Cu,Edge.Cuts'), ('montaje', 'F.Silkscreen,Edge.Cuts'), ('cobre-y-alambres', 'B.Cu,F.Silkscreen,Edge.Cuts')):
    subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', str(pcb), '-o', str(V / f'{nombre}.svg'), '--layers', capas, '--mode-single', '--exclude-drawing-sheet', '--fit-page-to-board'], capture_output=True)
    subprocess.run(['rsvg-convert', '-w', '2000', '-b', 'white', str(V / f'{nombre}.svg'), '-o', str(V / f'{nombre}.png')]); (V / f'{nombre}.svg').unlink()
for lado in ('top', 'bottom'):
    subprocess.run(['kicad-cli', 'pcb', 'render', str(pcb), '-o', str(V / f'3d-{lado}.png'), '--side', lado, '--width', '1800', '--height', '1100', '--quality', 'high', '--background', 'opaque'], capture_output=True)
subprocess.run(['kicad-cli', 'pcb', 'render', str(pcb), '-o', str(V / '3d-iso.png'), '--width', '1800', '--height', '1100', '--quality', 'high', '--background', 'opaque', '--rotate', "'-45,0,30'", '--zoom', '0.9'], capture_output=True)
print(json.dumps(dict(drc=err, sin_conectar=len(d['unconnected_items']), alambres=len(filas))))

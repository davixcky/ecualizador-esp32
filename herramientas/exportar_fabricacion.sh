#!/usr/bin/env bash
# D.2: cobre B.Cu; puentes cortos superiores y cableado inferior aislado.
set -euo pipefail
cd "$(dirname "$0")/../hardware"
mkdir -p fabricacion/D2
kicad-cli sch export pdf ecualizador.kicad_sch -o ecualizador.pdf >/dev/null
kicad-cli sch export bom ecualizador.kicad_sch -o fabricacion/bom.csv --fields 'Reference,Value,Footprint,${QUANTITY}' --group-by Value,Footprint >/dev/null
kicad-cli pcb drc ecualizador.kicad_pcb -o drc.rpt --schematic-parity --severity-error --exit-code-violations
kicad-cli sch erc ecualizador.kicad_sch -o erc.rpt --exit-code-violations
kicad-cli pcb export gerbers ecualizador.kicad_pcb -o fabricacion/D2/ -l B.Cu,B.Mask,Edge.Cuts >/dev/null
kicad-cli pcb export drill ecualizador.kicad_pcb -o fabricacion/D2/ --generate-map --generate-report >/dev/null
kicad-cli pcb export pdf ecualizador.kicad_pcb -o una-cara/cobre-inferior-1a1.pdf -l B.Cu,Edge.Cuts --mode-single --scale 1 >/dev/null
kicad-cli pcb export pdf ecualizador.kicad_pcb -o una-cara/montaje-kicad.pdf -l F.Fab,Edge.Cuts --mode-single --scale 0 >/dev/null
kicad-cli pcb export vrml ecualizador.kicad_pcb -o 3d/ecualizador-placa.wrl --units mm -f >/dev/null
python3 ../herramientas/guia_puentes.py
/usr/bin/python3 ../herramientas/exportar_plano_d2.py
"${PYTHON:-../.venv/bin/python}" ../herramientas/dibujar_pcb_una_cara.py
"${PYTHON:-../.venv/bin/python}" ../herramientas/exportar_toner.py
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
p=Path('fabricacion/D2')
assert not list(p.glob('*F_Cu*'))
# Taladros coincidentes de los puentes a terminal: un solo ciclo por agujero físico.
for drill in p.glob('*.drl'):
 seen=set();tool='';lines=[]
 for line in drill.read_text().splitlines():
  if 'TF.FileFunction' in line or 'TA.AperFunction' in line:continue
  if line.startswith('T') and 'C' not in line:tool=line
  if line.startswith('X'):
   key=(tool,line)
   if key in seen:continue
   seen.add(key)
  lines.append(line)
 drill.write_text('\n'.join(lines)+'\n')
 from collections import Counter
 counts=Counter(tool for tool,line in seen)
 sizes={line.split('C')[0]:line.split('C')[1] for line in lines if line.startswith('T') and 'C' in line}
 report=['D.2 - INFORME DE TALADROS PARA PCB DE UNA CARA', 'Cobre: B.Cu. Todos los taladros se fabrican SIN metalizar.', 'Las coordenadas repetidas de puentes a terminal se perforan una sola vez.', '']
 report += [f'{tool}: diametro {sizes[tool]} mm; {count} taladros unicos' for tool,count in sorted(counts.items())]
 report += [f'Total: {sum(counts.values())} taladros unicos.']
 (p/'ecualizador-drill.rpt').write_text('\n'.join(report)+'\n')


# El job automático conserva la pila interna de dos capas de KiCad: no enviarlo.
for f in p.glob('*.gbrjob'):f.unlink()
for f in p.glob('*B_Cu*'):
 f.write_text(f.read_text().replace('FileFunction,Copper,L2,Bot','FileFunction,Copper,L1,Bot'))
(p/'LEEME-FABRICACION.txt').write_text('D.2 — PCB DE UNA CARA. 200 x 120 mm; FR4 de 1,6 mm.\nUna sola capa de cobre, INFERIOR (B.Cu). No fabricar cobre superior.\nLos cruces son 80 cables aislados instalados a mano, fuera de los Gerbers.\nLos taladros de componentes y puentes se sueldan desde abajo; no requieren conexión metalizada entre capas.\nMascara inferior opcional. Sin serigrafia de fabricacion. Separacion minima 1 mm; pistas >=0,9 mm.\nConsultar montaje/PUENTES.md y montaje/puentes.csv. JP67-JP79 se sueldan a terminales existentes por debajo; no abrir nuevos agujeros.\n')
with ZipFile('fabricacion/ecualizador-D2-una-cara.zip','w',ZIP_DEFLATED) as z:
 for f in p.iterdir():z.write(f,f.name)
 z.write('PUENTES.md','montaje/PUENTES.md')
 z.write('una-cara/puentes.csv','montaje/puentes.csv')
 z.write('una-cara/toner-espejo-1a1.pdf','toner/toner-espejo-1a1.pdf')
PY

"""Guía de cableado sincronizada con el generador de la PCB."""
import json,math
from pathlib import Path
from montaje_puentes import cara
r=Path(__file__).resolve().parents[1];js=json.loads((r/'hardware/ruteo-validado.json').read_text())['puentes']
counts={c:sum(len(j['alambres']) for j in js if cara(j)==c) for c in ('superior','inferior')}
lines=['# Puentes D.2 — montaje por caras','',f"{counts['superior']} tramos cortos arriba (hasta 20 mm entre extremos) y {counts['inferior']} cables aislados por debajo. Se mantienen 80 tramos en 79 grupos: este cambio ordena el montaje; no reduce el número de conexiones.",'',
'La PCB tiene cobre únicamente en B.Cu. La cara de montaje del cable no es una capa adicional de cobre. JP67–JP79 se sueldan a terminales existentes; los restantes tienen taladros propios.', '',
'## Montaje', '',
'1. Instalar los puentes superiores antes de los componentes que puedan taparlos. Usar cable aislado; no dejar conductor desnudo en los cruces.',
'2. Montar los componentes y después el cableado inferior. Identificar ambos extremos con el mismo número JP. Seguir la columna Cara, no una línea impresa sobre la placa.',
'3. Mantener los cables inferiores dentro del contorno, separados de los tornillos y sujetos con pequeños puntos de adhesivo apto para electrónica. Reservar 8 mm libres bajo la PCB; el gabinete dispone de 26 mm hasta el piso. Comprobar también la separación respecto al parlante y su cableado.',
'4. Evitar mazos compartidos entre señales de audio y alimentación LED/reloj de pantalla. Los cruces entre cables deben conservar su aislamiento. No prensarlos contra las soldaduras.',
'5. Antes de alimentar, comprobar continuidad de cada JP y ausencia de cortos entre alimentación y GND. La DRC comprueba las conexiones del diseño; no sustituye esta revisión del montaje.', '',
'Los modelos 3D muestran arcos orientativos de cable, no una longitud de corte ni un ensayo de colisiones. Los planos de cada cara y las coordenadas definen los extremos reales. Todas las coordenadas de la tabla se leen desde arriba; el plano inferior está reflejado para verlo desde abajo.', '',
'| Puente | Red | Inicio (x, y), mm | Fin (x, y), mm | Cara | Conexión |','|---|---|---|---|---|---|']
for j in sorted(js,key=lambda j:int(j['ref'][2:])):
 for i,(a,b) in enumerate(j['alambres'],1):
  ref=j['ref']+(f'/{i}' if len(j['alambres'])>1 else '')
  lines.append(f"| {ref} | {j['red']} | {a[0]:.3f}, {a[1]:.3f} | {b[0]:.3f}, {b[1]:.3f} | {cara(j)} | {'Terminal existente' if j['terminal'] else 'Taladros propios'} |")
(r/'hardware/PUENTES.md').write_text('\n'.join(lines)+'\n');print(counts)

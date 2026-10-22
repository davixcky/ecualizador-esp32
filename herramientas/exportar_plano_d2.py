#!/usr/bin/env python3
"""Coordenadas y guía de montaje extraídas de la PCB D.2, sin rejilla perforada."""
import json
from pathlib import Path
import pcbnew as k
from montaje_puentes import cara
R=Path(__file__).resolve().parents[1];D=R/'hardware/una-cara';b=k.LoadBoard(str(R/'hardware/ecualizador.kicad_pcb'))
def xy(p):return [round(k.ToMM(p.x),6),round(k.ToMM(p.y),6)]
old=json.loads((D/'montaje.json').read_text());routing=json.loads((R/'hardware/ruteo-validado.json').read_text());m=dict(revision='D.2',estado='DRC y paridad con esquema verificados',ancho=200,alto=120,paso=1,origen=[0,0],panel=old['panel'],pines={},redes={},pistas=[],puentes=[])
for fp in b.GetFootprints():
 if fp.GetReference().startswith(('JP','H')):continue
 for p in fp.Pads():
  if p.GetNetCode():
   m['pines'][fp.GetReference()+'.'+p.GetNumber()]=xy(p.GetPosition());m['redes'].setdefault(p.GetNetname(),[]).append(xy(p.GetPosition()))
for t in b.GetTracks():m['pistas'].append(dict(red=t.GetNetname(),puntos=[xy(t.GetStart()),xy(t.GetEnd())]))
for j in routing['puentes']:
 for i,(a,c) in enumerate(j['alambres'],1):m['puentes'].append(dict(ref=j['ref']+(f'/{i}' if len(j['alambres'])>1 else ''),red=j['red'],a=a,b=c,terminal=j['terminal'],cara=cara(j)))
(D/'montaje.json').write_text(json.dumps(m,indent=2,ensure_ascii=False))

#!/usr/bin/env python3
"""Validez de sólidos y ajuste nominal de pantalla/tiras; no sustituye prueba de impresión."""
import sys, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'cad'))
import gabinete
p=gabinete.construir()
results={n:{'valido':all(v.isValid() for v in s.vals()),'volumen_mm3':round(sum(v.Volume() for v in s.vals()),3)} for n,s in p.items()}
assert all(r['valido'] and r['volumen_mm3']>0 for r in results.values())
collisions={}
for a,b in [('cuerpo','tira0'),('cuerpo','tira1'),('cuna-tft','tft-placa'),('tapa','tft-placa'),('cuerpo','tapa')] + [(f'iman-base{i}', 'cuerpo') for i in range(4)] + [(f'iman-tapa{i}', 'tapa') for i in range(4)]:
    volume=p[a].val().intersect(p[b].val()).Volume()
    collisions[a+'/'+b]=round(volume,6)
    assert volume<0.01,(a,b,volume)
report={'piezas':results,'intersecciones_mm3':collisions,'alcance':'Validez de sólidos y ajustes nominales de pantalla, LED, tapa e imanes; no certifica tolerancias, componentes reales ni montaje completo.'}
(root/'cad/validacion.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(f'{len(p)} piezas válidas; {len(collisions)} ajustes sin intersección de volumen.')

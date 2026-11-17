#!/usr/bin/env python3
"""Valida las tres restricciones geométricas del taller para una PCB KiCad."""
import json
import math
import sys

import pcbnew as k
from pcbnew import ToMM
from shapely.geometry import LineString


pcb = sys.argv[1]
track_min = float(sys.argv[2]) if len(sys.argv) > 2 else 0.7
pad_min = float(sys.argv[3]) if len(sys.argv) > 3 else 1.9
b = k.LoadBoard(pcb)
errores = []

tracks = [t for t in b.GetTracks() if t.Type() == k.PCB_TRACE_T]
for t in tracks:
    ancho = ToMM(t.GetWidth())
    if ancho + 1e-6 < track_min:
        errores.append(f"pista {ancho:.3f} mm < {track_min:.3f} mm")

for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() != k.PAD_ATTRIB_PTH:
            continue
        s = p.GetSize(k.B_Cu)
        menor = min(ToMM(s.x), ToMM(s.y))
        if menor + 1e-6 < pad_min:
            errores.append(f"{f.GetReference()}.{p.GetNumber()}: dona {menor:.3f} mm < {pad_min:.3f} mm")

# Un puente de alambre es un componente independiente: sus dos terminales deben
# tener taladros propios y nunca quedar superpuestos con el pad de otro componente.
component_pads = [(f, p) for f in b.GetFootprints() if not f.GetReference().startswith('JP') for p in f.Pads()]
shared_bridge_holes = []
for f in b.GetFootprints():
    if not f.GetReference().startswith('JP'):
        continue
    for p in f.Pads():
        px, py = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
        for cf, cp in component_pads:
            cx, cy = ToMM(cp.GetPosition().x), ToMM(cp.GetPosition().y)
            if math.hypot(px - cx, py - cy) < 0.01:
                shared_bridge_holes.append(f"{f.GetReference()}.{p.GetNumber()} con {cf.GetReference()}.{cp.GetNumber()}")
errores.extend(f"puente reutiliza agujero de componente: {x}" for x in shared_bridge_holes)

# El segmento libre entre centros de dos pads adyacentes de la misma huella representa
# el canal prohibido. Se recorta por el radio de cada pad para no confundir una pista que
# simplemente sale del propio terminal.
cruces = []
for f in b.GetFootprints():
    pads = [p for p in f.Pads() if p.GetAttribute() == k.PAD_ATTRIB_PTH]
    for i, a in enumerate(pads):
        ax, ay = ToMM(a.GetPosition().x), ToMM(a.GetPosition().y)
        for z in pads[i + 1:]:
            zx, zy = ToMM(z.GetPosition().x), ToMM(z.GetPosition().y)
            dist = math.hypot(zx - ax, zy - ay)
            if not 2.45 <= dist <= 2.62:
                continue
            ux, uy = (zx - ax) / dist, (zy - ay) / dist
            sa, sz = a.GetSize(k.B_Cu), z.GetSize(k.B_Cu)
            ra = min(ToMM(sa.x), ToMM(sa.y)) / 2 + 0.03
            rz = min(ToMM(sz.x), ToMM(sz.y)) / 2 + 0.03
            hueco = LineString([(ax + ux * ra, ay + uy * ra), (zx - ux * rz, zy - uy * rz)])
            for t in tracks:
                p, q = t.GetStart(), t.GetEnd()
                extremos = {(round(ToMM(p.x), 4), round(ToMM(p.y), 4)),
                            (round(ToMM(q.x), 4), round(ToMM(q.y), 4))}
                centros = {(round(ax, 4), round(ay, 4)), (round(zx, 4), round(zy, 4))}
                # Una unión directa entre estos dos terminales no es una pista que
                # "pasa entre" pines: comienza y termina precisamente en ellos.
                if extremos == centros and a.GetNetCode() == z.GetNetCode() == t.GetNetCode():
                    continue
                cobre = LineString([(ToMM(p.x), ToMM(p.y)), (ToMM(q.x), ToMM(q.y))]).buffer(ToMM(t.GetWidth()) / 2 - 1e-4)
                if cobre.intersects(hueco):
                    cruces.append(f"{f.GetReference()} {a.GetNumber()}-{z.GetNumber()}")
                    break
errores.extend(f"pista en espacio de pines 2,54 mm: {x}" for x in sorted(set(cruces)))

out = {
    'pcb': pcb,
    'track_min_mm': min((ToMM(t.GetWidth()) for t in tracks), default=None),
    'pad_min_mm': min((min(ToMM(p.GetSize(k.B_Cu).x), ToMM(p.GetSize(k.B_Cu).y))
                       for f in b.GetFootprints() for p in f.Pads()
                       if p.GetAttribute() == k.PAD_ATTRIB_PTH), default=None),
    'vias': sum(t.Type() == k.PCB_VIA_T for t in b.GetTracks()),
    'forbidden_2_54_crossings': sorted(set(cruces)),
    'shared_bridge_holes': shared_bridge_holes,
    'errors': errores,
}
print(json.dumps(out, indent=2, ensure_ascii=False))
raise SystemExit(bool(errores))

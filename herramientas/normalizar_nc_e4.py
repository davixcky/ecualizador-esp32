#!/usr/bin/env python3
"""Normaliza nombres de red físicos de E.4 sin alterar su conectividad."""
import sys

import pcbnew as k


path = sys.argv[1]
b = k.LoadBoard(path)
nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByName().values()}
cambios = []

# Las etiquetas locales de KiCad reciben el prefijo de hoja '/'. Guardarlo
# también en la PCB evita usar símbolos globales rojos encima de los pines NC.
for nombre, net in list(nets.items()):
    if nombre.startswith("NC-"):
        net.SetNetname("/" + nombre)
        cambios.append(f"{nombre} -> /{nombre}")

# Estos nombres fueron heredados del esquemático lógico anterior. La PCB ya
# tiene la conectividad correcta; se renombran para que el esquema físico pueda
# ser legible y coincidir estrictamente sin etiquetas Net-(...) superpuestas.
renombres = {
    "Net-(U1A-+)": "Net-(U1C-+)",
    "Net-(U1C-+)": "Net-(U1A-+)",
    "Net-(U2D-+)": "Net-(U2C-+)",
    "Net-(U2C--)": "Net-(U2D--)",
    "Net-(U4C--)": "Net-(U3C--)",
    "Net-(U4C-out)": "Net-(U4C--)",
    "Net-(C9-Pad1)": "/NIVEL",
    "Net-(R4-Pad2)": "/MIX",
}
pendientes = []
if "/NIVEL" not in nets:  # marcador que hace esta operación idempotente
    for i, (viejo, nuevo) in enumerate(renombres.items()):
        net = nets.get(viejo)
        if net is None:
            continue
        temporal = f"__E4_RENAME_{i}__"
        net.SetNetname(temporal)
        pendientes.append((net, viejo, nuevo))
    for net, viejo, nuevo in pendientes:
        net.SetNetname(nuevo)
        cambios.append(f"{viejo} -> {nuevo}")

nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByName().values()}
for f in b.GetFootprints():
    if f.GetReference().startswith("JP"):
        continue
    for p in f.Pads():
        if p.GetNetCode() and not p.GetNetname().startswith("unconnected-"):
            continue
        nombre = f"/NC-{f.GetReference()}-{p.GetNumber()}"
        if nombre not in nets:
            net = k.NETINFO_ITEM(b, nombre)
            b.Add(net)
            nets[nombre] = net
        p.SetNet(nets[nombre])
        cambios.append(f"NC: {nombre}")
b.Save(path)
print(f"{len(cambios)} normalizaciones")

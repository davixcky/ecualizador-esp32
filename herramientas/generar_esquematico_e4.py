#!/usr/bin/env python3
"""Genera el esquema físico E.4 desde la asignación que también usa la PCB.

La PCB conserva el ruteo validado de una cara. Este generador retroanota en el
esquema las unidades equivalentes de LM324 y todos los pines reasignados. El
resultado debe cerrar con `kicad-cli pcb drc --schematic-parity` sin conflictos.
"""
import json
from pathlib import Path

import pcbnew as k

import generar_esquematico as g


ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "hardware" / "E4-LM324"
PCB = E4 / "placa" / "ecualizador-E4-LM324.kicad_pcb"
OUT = E4 / "proyecto" / "ecualizador-E4-LM324.kicad_sch"


def normalizar(red):
    if red is None:
        return None
    return red[1:] if red.startswith("/") else red


col = json.loads((E4 / "colocacion.json").read_text())

# Función lógica dibujada -> sección física que quedó conectada en la PCB.
g.OPAMP_UNIT_OVERRIDE = {
    "U1A": "U1C", "U1B": "U1B", "U1C": "U1A", "U1D": "U1D",
    "U2A": "U2A", "U2B": "U2B", "U2C": "U2D", "U2D": "U2C",
    "U3A": "U3D", "U3B": "U4D", "U3C": "U3A", "U3D": "U3B",
    "U4A": "U4A", "U4B": "U4B", "U4C": "U3C", "U4D": "U4C",
}

# Nombres semánticos de las dos conexiones que cruzan al potenciómetro RV1.
g.NET_ALIAS = {}

board = k.LoadBoard(str(PCB))
g.PIN_RED_OVERRIDE = {
    (f.GetReference(), p.GetNumber()): normalizar(p.GetNetname()) if p.GetNetCode() else None
    for f in board.GetFootprints()
    if not f.GetReference().startswith("JP")
    for p in f.Pads()
}
g.FOOTPRINT_OVERRIDE = {
    f.GetReference(): (
        f"{f.GetFPID().GetLibNickname().wx_str()}:{f.GetFPID().GetLibItemName().wx_str()}"
    )
    for f in board.GetFootprints()
    if not f.GetReference().startswith("JP")
}
g.DESCRIPTION_OVERRIDE = {
    f.GetReference(): f.GetFieldText("Description")
    for f in board.GetFootprints()
    if not f.GetReference().startswith("JP")
}
g.DESCRIPCION_FISICA = True
g.PROYECTO = "ecualizador-E4-LM324"
g.SALIDA = str(OUT)

e = g.construir()
e.guardar(
    str(OUT),
    [
        "Ecualizador E.4-LM324 — esquema físico de la PCB de una cara",
        "2026-11-06",
        "E.4-LM324",
        "Electrónica II — Universidad de la Costa",
        "Fuente de verdad física: asignación E.4; coincide pin por pin con la PCB",
        "LM324N a 5 V; VREF = 1,65 V; ADC protegido por atenuadores 2:1",
    ],
)
print(OUT)

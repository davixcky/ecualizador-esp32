#!/usr/bin/env python3
"""Modelo mecánico E.5: cuatro perforadas, arneses y dos barras WS2812B.

Ejecutar con:
    freecadcmd hardware/E5-perforadas/3d/generar_modelo.py

El modelo reserva el ancho conservador de 12,5 mm publicado para algunas tiras
WS2812B. El soporte acepta tiras de 10 a 12,5 mm mediante una cuna de 13,2 mm.
"""
from pathlib import Path
import json
import math
import sys

import FreeCAD as App
import Import
import MeshPart
import Part


HERE = Path(__file__).resolve().parent
OUT = HERE
STL = OUT / "stl"
STL.mkdir(parents=True, exist_ok=True)

# Gabinete ampliado para una sola capa comprobable.
W, D, H = 236.0, 186.0, 58.0
WALL, FLOOR, LID = 2.5, 3.0, 3.0
Z_BOARD = 9.0
STRIP_W = 12.5

# x, y, ancho, fondo, etiqueta
BOARDS = {
    "T1": (8.0, 8.0, 90.0, 70.0, "ENTRADA + U1"),
    "T2": (112.0, 8.0, 100.0, 70.0, "FILTROS + U2"),
    "T3": (8.0, 90.0, 100.0, 70.0, "DETECTORES U3/U4"),
    "T4": (122.0, 88.0, 100.0, 80.0, "ESP32 + CONTROL"),
}

COLORS = {
    "body": (0.11, 0.14, 0.17), "lid": (0.32, 0.35, 0.39),
    "perf": (0.45, 0.25, 0.08), "pad": (0.86, 0.62, 0.15),
    "chip": (0.035, 0.04, 0.045), "connector": (0.92, 0.92, 0.88),
    "esp": (0.05, 0.25, 0.20), "strip": (0.96, 0.96, 0.96),
    "led": (0.10, 0.78, 0.92), "wire": (0.06, 0.45, 0.92),
    "power": (0.85, 0.08, 0.05), "support": (0.16, 0.18, 0.20),
}


def vec(p):
    return App.Vector(*p)


def box(w, d, h, x=0, y=0, z=0):
    return Part.makeBox(w, d, h, vec((x, y, z)))


def tube(points, radius=0.7):
    pieces = []
    for a, b in zip(points, points[1:]):
        av, bv = vec(a), vec(b)
        delta = bv.sub(av)
        if delta.Length > 0.01:
            pieces.append(Part.makeCylinder(radius, delta.Length, av, delta))
    return Part.makeCompound(pieces)


def add(doc, name, shape, color, group="interior"):
    obj = doc.addObject("PartDesign::Feature", name)
    obj.Label = name.replace("_", " ")
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "ColorRGB", "Render")
    obj.ColorRGB = ",".join(str(v) for v in COLORS[color])
    obj.addProperty("App::PropertyString", "AssemblyGroup", "Render")
    obj.AssemblyGroup = group
    return obj


def perfboard(x, y, w, d):
    shape = box(w, d, 1.6, x, y, Z_BOARD)
    holes = [(x + 4, y + 4), (x + w - 4, y + 4),
             (x + 4, y + d - 4), (x + w - 4, y + d - 4)]
    for hx, hy in holes:
        shape = shape.cut(Part.makeCylinder(1.6, 3, vec((hx, hy, Z_BOARD - .5))))
    return shape, holes


def pad_grid(x, y, w, d):
    pads = []
    # Malla aligerada: muestra el paso 2,54 mm sin convertir cada dona en objeto.
    for px in range(0, int((w - 8) // 5.08) + 1):
        for py in range(0, int((d - 8) // 5.08) + 1):
            cx, cy = x + 4 + px * 5.08, y + 4 + py * 5.08
            ring = Part.makeCylinder(1.15, .12, vec((cx, cy, Z_BOARD + 1.6)))
            ring = ring.cut(Part.makeCylinder(.45, .2, vec((cx, cy, Z_BOARD + 1.55))))
            pads.append(ring)
    return Part.makeCompound(pads)


def dip(x, y, pins=14):
    length = 20 if pins == 14 else 26
    body = box(length, 10, 4, x, y, Z_BOARD + 2.0)
    notch = Part.makeCylinder(1.5, 2, vec((x + 3, y + 5, Z_BOARD + 5)))
    return body.cut(notch)


def resistor_row(x, y, count, dx=9):
    return Part.makeCompound([box(6.3, 2.5, 2.5, x + i * dx, y, Z_BOARD + 2) for i in range(count)])


def connector(x, y, pins, vertical=False):
    w, d = (6, pins * 2.54 + 2) if vertical else (pins * 2.54 + 2, 6)
    return box(w, d, 7, x, y, Z_BOARD + 1.6)


def enclosure(doc):
    bottom = box(W, D, FLOOR)
    walls = [box(W, WALL, H - FLOOR, 0, 0, FLOOR), box(W, WALL, H - FLOOR, 0, D - WALL, FLOOR),
             box(WALL, D - 2 * WALL, H - FLOOR, 0, WALL, FLOOR),
             box(WALL, D - 2 * WALL, H - FLOOR, W - WALL, WALL, FLOOR)]
    add(doc, "Gabinete_E5", bottom.fuse(walls), "body", "body")
    lid = box(W, D, LID, 0, 0, H)
    # Ventana TFT y ranuras visuales para las dos barras.
    lid = lid.cut(box(46, 26, LID + 2, 151, 119, H - 1))
    lid = lid.cut(box(102, 5, LID + 2, 12, 174, H - 1))
    lid = lid.cut(box(102, 5, LID + 2, 122, 174, H - 1))
    add(doc, "Tapa_E5", lid, "lid", "lid")


def populate(doc):
    mounting = []
    for ref, (x, y, w, d, label) in BOARDS.items():
        shape, holes = perfboard(x, y, w, d)
        add(doc, f"{ref}_Perforada_{int(w)}x{int(d)}", shape, "perf")
        add(doc, f"{ref}_Donas", pad_grid(x, y, w, d), "pad")
        mounting += holes
        if ref == "T1":
            add(doc, "T1_U1_LM324", dip(x + 33, y + 27), "chip")
            add(doc, "T1_Pasivos", resistor_row(x + 10, y + 12, 7, 10), "connector")
            add(doc, "T1_JAB", connector(x + w - 20, y + d - 9, 4), "connector")
        elif ref == "T2":
            add(doc, "T2_U2_LM324", dip(x + 39, y + 26), "chip")
            add(doc, "T2_Potenciometros", Part.makeCompound([
                box(12, 12, 8, x + 8 + i * 18, y + 7, Z_BOARD + 1.6) for i in range(5)]), "connector")
            add(doc, "T2_JBC", connector(x + w - 25, y + d - 9, 5), "connector")
        elif ref == "T3":
            add(doc, "T3_U3_U4", Part.makeCompound([dip(x + 18, y + 25), dip(x + 55, y + 25)]), "chip")
            add(doc, "T3_Detectores", resistor_row(x + 10, y + 10, 8, 10), "connector")
            add(doc, "T3_JC4", connector(x + w - 22, y + d - 9, 4), "connector")
        else:
            add(doc, "T4_ESP32", box(28, 54, 8, x + 8, y + 12, Z_BOARD + 1.6), "esp")
            add(doc, "T4_HCT245", dip(x + 48, y + 20, 20), "chip")
            add(doc, "T4_LCD_Header", connector(x + 60, y + 52, 8), "connector")
            add(doc, "T4_JBUS", connector(x + w - 12, y + 8, 4, True), "connector")
    # Postes de cada tarjeta, independientes y accesibles.
    posts = []
    for x, y in mounting:
        posts.append(Part.makeCylinder(3.2, Z_BOARD - FLOOR, vec((x, y, FLOOR))))
    add(doc, "Postes_M3", Part.makeCompound(posts), "support")

    # Arnés lógico y bus estrella por el corredor central.
    wires = [
        ((98, 70, 15), (112, 70, 15)), ((108, 125, 15), (122, 125, 15)),
        ((212, 70, 15), (212, 88, 15)), ((55, 78, 15), (55, 90, 15)),
        ((100, 84, 17), (218, 84, 17)),
    ]
    add(doc, "Arneses_E5", Part.makeCompound([tube([a, b], .8) for a, b in wires]), "wire")
    add(doc, "Bus_5V_GND", tube([(210, 164, 18), (228, 164, 18), (228, 82, 18), (104, 82, 18)], 1.2), "power")

    # Dos barras cortadas de la misma tira WS2812B de 60 LED/m: 6 píxeles por tramo.
    for idx, x in enumerate((12.0, 122.0), 1):
        y, z = 171.0, 35.0
        support = box(104, STRIP_W + .7, 2.2, x - 2, y - .35, z - 1.5)
        strip = box(100, STRIP_W, 1.2, x, y, z)
        leds = Part.makeCompound([box(5, 5, 1.8, x + 6.7 + i * 16.67, y + (STRIP_W - 5) / 2, z + 1.2) for i in range(6)])
        add(doc, f"Soporte_NeoPixel_{idx}_13p2mm", support, "support")
        add(doc, f"Barra_NeoPixel_{idx}_WS2812B_6px", strip, "strip")
        add(doc, f"Pixels_{idx}", leds, "led")


def validate():
    issues = []
    rects = []
    for ref, (x, y, w, d, _) in BOARDS.items():
        if x < WALL + 2 or y < WALL + 2 or x + w > W - WALL - 2 or y + d > D - WALL - 8:
            issues.append(f"{ref} fuera del volumen útil")
        for other, ox, oy, ow, od in rects:
            if x < ox + ow and x + w > ox and y < oy + od and y + d > oy:
                issues.append(f"solape {ref}/{other}")
        rects.append((ref, x, y, w, d))
    report = {
        "revision": "E.5", "enclosure_mm": [W, D, H + LID],
        "boards": {k: list(v[:4]) for k, v in BOARDS.items()},
        "neopixel_strip_mm": [100, STRIP_W], "support_clearance_mm": 13.2,
        "issues": issues, "valid": not issues,
        "note": "La colocación de componentes es envolvente mecánica, no plantilla agujero por agujero.",
    }
    (OUT / "validacion-3d.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if issues:
        raise RuntimeError(issues)


def main():
    validate()
    doc = App.newDocument("Ecualizador_E5_Perforadas")
    enclosure(doc)
    populate(doc)
    doc.recompute()
    doc.saveAs(str(OUT / "ecualizador-E5-perforadas.FCStd"))
    objects = [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
    Import.export(objects, str(OUT / "ecualizador-E5-perforadas.step"))
    for name in ("Gabinete_E5", "Tapa_E5", "Soporte_NeoPixel_1_13p2mm", "Soporte_NeoPixel_2_13p2mm"):
        obj = doc.getObject(name)
        mesh = MeshPart.meshFromShape(Shape=obj.Shape, LinearDeflection=.12, AngularDeflection=.35)
        mesh.write(str(STL / f"{name.lower()}.stl"))
    print(f"E.5 CAD: {len(objects)} objetos; {W} x {D} x {H + LID} mm")


if __name__ == "__main__":
    main()

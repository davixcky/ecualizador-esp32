#!/usr/bin/env python3
"""Probetas de la pantalla en tres holguras (freecadcmd variantes_pantalla.py).

Genera pruebas-de-ajuste/variantes/tapa_pantalla_CYD_{A,B,C}.stl con CYD_AJUSTE
-0,15 (B, apretada), 0 (A, nominal) y +0,2 (C, holgada). Muescas en el borde
frontal para identificarlas: A sin muesca, B una, C dos.
"""
import importlib
import os
from pathlib import Path

os.environ["E5_SOLO_DEFINIR"] = "1"
import FreeCAD as App  # noqa: E402
import MeshPart  # noqa: E402
import Part  # noqa: E402
import generar_modelo as g  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "pruebas-de-ajuste" / "variantes"
OUT.mkdir(parents=True, exist_ok=True)

VARIANTES = [("A_nominal", 0.0, 0), ("B_apretada", -0.15, 1), ("C_holgada", 0.2, 2)]
H, LID = None, None
for nombre, ajuste, muescas in VARIANTES:
    os.environ["CYD_AJUSTE"] = str(ajuste)
    importlib.reload(g.E)
    E = g.E
    H, LID = E.H, E.LID
    parts, _ = E.build_all()
    doc = App.newDocument(f"variante_{nombre}")
    for p in parts:
        if p["meta"].get("fundir") == "tapa":
            g.add(doc, p["name"], g.shape_of(p), p["color"], p["group"], p["meta"])
    _, lid0 = g.enclosure(doc)
    lid = g.fused(doc, lid0, "tapa")
    cupon = lid.common(Part.makeBox(70, 103, 11, App.Vector(104, 27, H - 8)))
    for k in range(muescas):
        cupon = cupon.cut(Part.makeBox(3, 1.6, 2.5, App.Vector(110 + k * 6, 26.5, H + LID - 1.5)))
    assert cupon.isValid() and len(cupon.Solids) == 1, (nombre, len(cupon.Solids))
    MeshPart.meshFromShape(Shape=cupon, LinearDeflection=.12, AngularDeflection=.35).write(str(OUT / f"tapa_pantalla_CYD_{nombre}.stl"))
    print(f"variante {nombre}: ajuste {ajuste:+.2f} mm, {muescas} muescas")
    App.closeDocument(doc.Name)
print("listo:", OUT)

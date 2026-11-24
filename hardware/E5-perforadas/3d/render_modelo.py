#!/usr/bin/env python3
"""Vistas fijas del ensamble E.5 y detalle explotado de la pantalla.

    freecadcmd hardware/E5-perforadas/3d/generar_modelo.py      # antes: CAD y malla
    blender -b -P hardware/E5-perforadas/3d/render_modelo.py

Opcional: `-- cerrado abierto planta detalle pantalla-soporte` para elegir vistas.
La pantalla CYD vertical muestra `tft-render-vertical.png`: una propuesta estática
para los renders. El firmware del CYD aún no existe.
"""
from pathlib import Path
import os
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpy  # noqa: E402
import escena_blender  # noqa: E402

ROOT = HERE.parents[2]
views = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["cerrado", "abierto", "planta"]
s = escena_blender.build(engine=os.environ.get("MOTOR", "CYCLES"), samples=int(os.environ.get("MUESTRAS", "96")),
                         tft_image=HERE / "tft-render-vertical.png")
scene, lay = s["scene"], s["layout"]
scene.render.resolution_x, scene.render.resolution_y = 2000, 1300
W, D, H = lay["W"], lay["D"], lay["H"]
for ref in ("RV1", "RV2", "RV3", "RV4", "RV5"):
    s["set_knob"](ref, .5)


def shot(name):
    scene.render.filepath = str(HERE / f"ecualizador-E5-{name}.png")
    bpy.ops.render.render(write_still=True)


if "cerrado" in views:
    s["set_lid"](0)
    s["aim"]((-150, -400, 330), (W / 2, D / 2 - 6, 26), 50)
    shot("cerrado")
if "detalle" in views:
    s["set_lid"](0)
    s["aim"]((139, -170, 190), (139, 40, 62), 50)
    shot("detalle-controles")
if "abierto" in views:
    s["set_lid"](lay["lid_open_deg"])
    s["aim"]((500, 470, 430), (W / 2, 62, 46), 42)
    shot("abierto")
if "planta" in views:
    # Planta desplegada: tapa volteada 180° hacia el frente para ver su cara interior,
    # las cuatro tarjetas y todos los arneses sin que nada tape nada.
    s["set_lid"](180)
    scene.render.resolution_x, scene.render.resolution_y = 1500, 2100
    s["aim"]((W / 2, -4, 900), (W / 2, -4 + .01, 0), ortho=416)
    shot("planta")
if "pantalla-soporte" in views:
    # Vista didáctica desde el interior: frente de prueba (con las cuatro uñas fijas) y la
    # pantalla 3,5" separada. No representa la posición de funcionamiento, sino el montaje.
    s["set_lid"](0)
    bpy.ops.wm.stl_import(filepath=str(HERE / "pruebas-de-ajuste/tapa_pantalla_CYD.stl"))
    front = bpy.context.object
    front.name = "Frente_prueba_pantalla_CYD"
    front.data.materials.append(escena_blender.make_material("lid", lay["colors"]["lid"]))
    display_names = {
        "CYD_3248S035_PCB_56p5x97p5",
        "CYD_modulo_TFT_3p5_marco",
        "CYD_tactil_cara_exterior",
        "CYD_area_activa_320x480",
        "CYD_ESP_WROOM_32_blindaje",
        "CYD_antena_WROOM",
        "CYD_micro_USB",
        "CYD_pulsadores_RST_BOOT",
        "CYD_ranura_TF",
        "CYD_P1_conector_serie_4v",
    }
    keep = display_names | {front.name}
    for obj in scene.objects:
        if obj.type in {"MESH", "CURVE", "FONT"}:
            obj.hide_render = obj.name not in keep
    s["screen"].hide_render = True
    for name in display_names:
        if name in s["objs"]:
            s["objs"][name].location.z -= 18
    scene.render.resolution_x, scene.render.resolution_y = 1800, 1350
    s["aim"]((210, -155, -30), (139, 73, 45), 62)
    shot("pantalla-soporte-explotado")

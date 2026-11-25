"""Se ejecuta dentro de Blender sobre docs/video/ecualizador-animado.blend. Imprime JSON."""
import json
import math
import os
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timeline import FPS, FRAMES, SWEEP_START, state, lid_angle  # noqa: E402

s = bpy.context.scene
names = [o.name for o in bpy.data.objects]
bad = [n for n in names + [m.name for m in bpy.data.meshes] + [m.name for m in bpy.data.materials] if any(k in n.lower() for k in ("desliz", "slider", "slide"))]
knobs = sorted(n for n in names if n.startswith("Perilla_RV"))
assert len(knobs) == 5, knobs
assert s.frame_end == FRAMES and s.render.fps == FPS
assert (s.render.resolution_x, s.render.resolution_y) == (1920, 1080)
order = {"RV1": 0, "RV2": 1, "RV3": 2, "RV4": 3, "RV5": 4}
worst = 0.0
moved = {k: [1e9, -1e9] for k in order}
for frame in sorted({1, FRAMES, *[int((b + d) * FPS) + 1 for b in SWEEP_START for d in (0, .9, 1.5, 3, 4.5, 6.9)], 1117, 1200, 1320, 1420, 1500}):
    s.frame_set(frame)
    t = (frame - 1) / FPS
    values, _ = state(t)
    for name in knobs:
        ref = name.split("_")[1]
        deg = math.degrees(bpy.data.objects[name].rotation_euler.z)
        moved[ref][0], moved[ref][1] = min(moved[ref][0], deg), max(moved[ref][1], deg)
        worst = max(worst, abs(deg - (0.5 - values[order[ref]]) * 300))
    worst_lid = abs(math.degrees(bpy.data.objects["Tapa_pivote"].rotation_euler.x) - lid_angle(t))
    assert worst_lid < .01, (frame, worst_lid)
assert worst < .01, worst
for ref in order:   # los CINCO controles giran todo su recorrido en el video
    assert moved[ref][1] - moved[ref][0] > 290, (ref, moved[ref])
s.frame_set(1)
assert abs(bpy.data.objects["Tapa_pivote"].rotation_euler.x) < 1e-6
s.frame_set(FRAMES)
assert abs(bpy.data.objects["Tapa_pivote"].rotation_euler.x) < 1e-6
led = {}
for band in ("GRAVES", "MEDIOS", "AGUDOS"):
    mat = bpy.data.objects[f"Difusor_opalino_{band}"].data.materials[0]
    node = mat.node_tree.nodes["Principled BSDF"]
    assert node.inputs["Emission Strength"].is_linked is False and mat.node_tree.animation_data is None, band
    led[band] = round(node.inputs["Emission Strength"].default_value, 3)
sounds = [x for x in s.sequence_editor.strips if x.type == "SOUND"]
assert len(sounds) == 1 and sounds[0].frame_start == 1 and os.path.isfile(bpy.path.abspath(sounds[0].sound.filepath))
missing = [im.name for im in bpy.data.images if im.users and im.source in {"FILE", "SEQUENCE"} and not im.packed_file and not os.path.isfile(bpy.path.abspath(im.filepath))]
assert not missing, missing
hooked = sum(1 for o in bpy.data.objects if o.name.startswith("Cable_") and any(m.type == "HOOK" for m in o.modifiers))
print("E5_BLEND_JSON " + json.dumps({
    "objetos": len(names), "nombres_con_deslizable": bad, "controles_rotativos": knobs,
    "B10K": sorted(n for n in names if "_B10K_" in n and n.endswith("_cuerpo")),
    "A10K_pendientes": sorted(n for n in names if "_A10K_" in n and "PENDIENTE" in n and n.endswith("_cuerpo")),
    "giro_grados": {k: [round(v[0], 1), round(v[1], 1)] for k, v in moved.items()}, "error_max_giro_grados": worst,
    "led_emision_fija": led, "cables": sum(n.startswith("Cable_") for n in names), "cables_que_siguen_la_tapa": hooked,
    "parlantes": sorted(n for n in names if n.endswith("marco_100x45")), "tapa_cerrada_en_primer_y_ultimo_fotograma": True,
    "audio_en_fotograma": 1}, ensure_ascii=False))

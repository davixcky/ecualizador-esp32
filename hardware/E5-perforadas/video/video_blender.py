"""Blender 5.1: escena animada y fotogramas del video E.5 (50 s, 24 fps, 1920x1080).

    blender -b -P hardware/E5-perforadas/video/video_blender.py            # escena + todos los fotogramas
    BUILD_ONLY=1 blender -b -P ...                                          # solo guarda el .blend editable
    PREVIEW=1,150,400 blender -b -P ...                                     # fotogramas sueltos de revisión
    RANGO=1-300 blender -b -P ...                                           # un tramo; omite los ya existentes

Guarda docs/video/ecualizador-animado.blend (rutas relativas) y escribe PNG en docs/video/frames/.
La geometría viene del CAD E.5 (escena_blender.py); el movimiento, de timeline.py.
"""
from pathlib import Path
import math
import os
import sys

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "3d"))
import escena_blender  # noqa: E402
from timeline import FPS, FRAMES, BAND_START, BAND_LEN, BUTTON_T, state, lid_angle, button_press  # noqa: E402

OUT = ROOT / "docs/video"
FRAMES_DIR = OUT / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
TFT_DIR = OUT / "tft-fotogramas"

s = escena_blender.build(engine="CYCLES", samples=int(os.environ.get("MUESTRAS", "40")), tft_image=TFT_DIR / "tft-0001.png")
scene, lay, cam = s["scene"], s["layout"], s["cam"]
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1920, 1080, 100
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, FRAMES
scene.render.use_persistent_data = True

# Pantalla: secuencia dibujada por el firmware, un PNG por fotograma.
tex = s["tex"]
tex.image.source = "SEQUENCE"
tex.image_user.frame_duration = FRAMES
tex.image_user.frame_start = 1
tex.image_user.frame_offset = 0
tex.image_user.use_auto_refresh = True

# Controles: RV2-RV4 siguen la línea de tiempo; RV1 y RV5 (A10K pendientes) no se mueven.
order = ("RV2", "RV3", "RV4")
for ref in ("RV1", "RV5"):
    s["set_knob"](ref, .5)
for frame in range(1, FRAMES + 1):
    t = (frame - 1) / FPS
    values, active = state(t)
    moving = any(b - .1 <= t <= b + BAND_LEN + .1 for b in BAND_START)
    if moving or frame in (1, FRAMES):
        for ref, v in zip(order, values):
            s["set_knob"](ref, v)
            s["knobs"][ref].keyframe_insert("rotation_euler", index=2, frame=frame)
    a = lid_angle(t)
    if frame in (1, FRAMES) or 30.9 <= t <= 47.1:
        s["pivot"].rotation_euler.x = math.radians(a)
        s["pivot"].keyframe_insert("rotation_euler", index=0, frame=frame)
    if frame in (1, FRAMES) or abs(t - BUTTON_T) < .4:
        s["button"].location.z = s["button"].location.z * 0 + button_press(t)
        s["button"].keyframe_insert("location", index=2, frame=frame)

# Cámara: sigue a un objetivo; ambos con claves Bézier.
target = bpy.data.objects.new("Camara_objetivo", None)
scene.collection.objects.link(target)
cam.rotation_euler = (0, 0, 0)
con = cam.constraints.new("TRACK_TO")
con.target, con.track_axis, con.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
SHOTS = [  # segundo, posición de cámara, objetivo, focal
    (0.0, (-150, -400, 330), (139, 90, 26), 50),
    (4.0, (150, -300, 250), (120, 60, 50), 50),
    (4.6, (70, -160, 175), (90, 40, 62), 50),       # detalle de las cinco perillas
    (6.8, (208, -160, 175), (188, 40, 62), 50),
    (8.0, (120, -225, 335), (139, 82, 50), 45),     # perillas + TFT + tres barras LED
    (27.5, (158, -225, 335), (139, 82, 50), 45),
    (28.6, (139, -70, 300), (139, 112, 60), 50),    # TFT y LED de cerca; pulsación de VISTA
    (30.8, (150, -90, 310), (139, 112, 60), 50),
    (32.4, (500, -60, 430), (139, 70, 60), 42),     # rodea por la derecha mientras abre la tapa
    (34.2, (500, 470, 430), (139, 62, 46), 42),     # interior completo desde atrás
    (37.8, (400, 520, 410), (139, 66, 46), 42),
    (39.0, (330, 265, 235), (185, 22, 52), 48),     # T2, PAM8403 y parlantes en la tapa
    (40.8, (300, 265, 235), (175, 22, 52), 48),
    (42.0, (395, 250, 270), (232, 146, 14), 50),    # T4, ESP32S y USB-C en la pared derecha
    (43.8, (420, 215, 260), (236, 146, 14), 50),
    (45.6, (500, -120, 420), (139, 70, 50), 45),    # cierra la tapa
    (47.4, (230, -400, 330), (139, 90, 26), 50),
    (50.0, (150, -420, 320), (139, 90, 26), 50),    # producto cerrado
]
for sec, pos, tgt, lens in SHOTS:
    fr = min(FRAMES, round(sec * FPS) + 1)
    cam.location, target.location, cam.data.lens = pos, tgt, lens
    cam.keyframe_insert("location", frame=fr)
    target.keyframe_insert("location", frame=fr)
    cam.data.keyframe_insert("lens", frame=fr)

# Audio en la escena editable: el mismo WAV que se multiplexa en el MP4.
editor = scene.sequence_editor_create()
editor.strips.new_sound("Audio del modelo SPICE", str(OUT / "demo-audio.wav"), channel=1, frame_start=1)

scene["descripcion"] = "Ecualizador E.5 en tarjetas perforadas: cinco controles rotativos, sin deslizables. Modelo de diseño; no sustituye pruebas."
scene.render.filepath = str(FRAMES_DIR / "frame-")
scene.frame_set(1)
blend = OUT / "ecualizador-animado.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=str(blend))


def render(frames, pattern):
    for fr in frames:
        path = Path(pattern.format(fr))
        if path.exists() and not os.environ.get("FORZAR"):
            continue
        scene.frame_set(fr)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)


if os.environ.get("PREVIEW"):
    render([int(v) for v in os.environ["PREVIEW"].split(",")], str(OUT / "preview-{}.png"))
elif not os.environ.get("BUILD_ONLY"):
    a, b = (int(v) for v in os.environ.get("RANGO", f"1-{FRAMES}").split("-"))
    render(range(a, b + 1), str(FRAMES_DIR / "frame-{:04d}.png"))

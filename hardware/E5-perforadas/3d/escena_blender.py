"""Escena de Blender 5.1 del ensamble E.5 (la usan render_modelo.py y el video).

Lee .render/ensamble.json, que escribe generar_modelo.py: malla teselada del CAD
y trazado de cables. No contiene cotas propias: si cambia el CAD, cambia la escena.

Jerarquía útil para animar:
    Tapa_pivote (vacío sobre el borde frontal; rotation_euler.x bascula la tapa imantada)
      ├─ piezas del grupo «lid», pantalla y rótulos
      ├─ Perilla_RV1..RV5 (vacíos; rotation_euler.z gira eje + perilla)
      └─ SW1_capuchon_VISTA (location.z)
    Cables: curvas con modificador Hook hacia Tapa_pivote en los puntos de la tapa.
"""
from pathlib import Path
import json
import math
import subprocess

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
ENSAMBLE = HERE / ".render" / "ensamble.json"

EMISSION = {"graves": .9, "medios": .9, "agudos": .9}
METAL = {"knob": (1.0, .26), "metal": (.72, .30), "pot": (.9, .38), "pot_pend": (.85, .42), "pad": (1.0, .35)}
ROUGH = {"body": .42, "lid": .38, "tono_a": .5, "tono_b": .5, "screen": .3, "knob": .32, "chip": .35, "strip": .5, "cone": .7, "speaker": .55}


def _principled(mat):
    mat.use_nodes = True
    return mat.node_tree.nodes["Principled BSDF"]


def make_material(key, rgb):
    name = f"E5_{key}"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    b = _principled(mat)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = ROUGH.get(key, .5)
    if key in METAL:
        b.inputs["Metallic"].default_value, b.inputs["Roughness"].default_value = METAL[key]
    if key in EMISSION:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = EMISSION[key]
    if key == "screen":       # vidrio negro: poco reflejo para que el AMOLED apagado se vea negro
        b.inputs["Specular IOR Level"].default_value = .08
    if key == "perf":
        perfboard_nodes(mat, rgb)
    return mat


def perfboard_nodes(mat, rgb):
    """Islas de cobre estañado cada 2,54 mm, generadas por coordenadas de objeto."""
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    dist = []
    for axis in ("X", "Y"):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = "MODULO"; m.inputs[1].default_value = 2.54
        nt.links.new(sep.outputs[axis], m.inputs[0])
        s = nt.nodes.new("ShaderNodeMath"); s.operation = "SUBTRACT"; s.inputs[1].default_value = 1.27
        nt.links.new(m.outputs[0], s.inputs[0])
        p = nt.nodes.new("ShaderNodeMath"); p.operation = "POWER"; p.inputs[1].default_value = 2
        nt.links.new(s.outputs[0], p.inputs[0])
        dist.append(p)
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
    nt.links.new(dist[0].outputs[0], add.inputs[0]); nt.links.new(dist[1].outputs[0], add.inputs[1])
    ring = nt.nodes.new("ShaderNodeMath"); ring.operation = "LESS_THAN"; ring.inputs[1].default_value = .95 ** 2
    hole = nt.nodes.new("ShaderNodeMath"); hole.operation = "LESS_THAN"; hole.inputs[1].default_value = .45 ** 2
    nt.links.new(add.outputs[0], ring.inputs[0]); nt.links.new(add.outputs[0], hole.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*rgb, 1); mix.inputs["B"].default_value = (.78, .74, .62, 1)
    nt.links.new(ring.outputs[0], mix.inputs["Factor"])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    mix2.inputs["B"].default_value = (.02, .02, .02, 1)
    nt.links.new(mix.outputs["Result"], mix2.inputs["A"]); nt.links.new(hole.outputs[0], mix2.inputs["Factor"])
    nt.links.new(mix2.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(ring.outputs[0], b.inputs["Metallic"])
    b.inputs["Roughness"].default_value = .45


def system_font():
    path = subprocess.check_output(["fc-match", "-f", "%{file}", "DejaVu Sans:bold"], text=True)
    font = bpy.data.fonts.load(path, check_existing=True)
    return font


def build(engine="BLENDER_EEVEE", samples=64, tft_image=None):
    data = json.loads(ENSAMBLE.read_text(encoding="utf-8"))
    lay = data["layout"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.unit_settings.length_unit = "MILLIMETERS"
    H, LID, W, D = lay["H"], lay["LID"], lay["W"], lay["D"]

    def link(o, parent=None):
        scene.collection.objects.link(o)
        if parent is not None:
            o.parent = parent
            o.matrix_parent_inverse = parent.matrix_world.inverted()
        return o

    pivot = bpy.data.objects.new("Tapa_pivote", None)
    pivot.empty_display_size = 12
    pivot.location = (0, lay["pivot"][0], lay["pivot"][1])
    link(pivot)
    pivot["nota"] = "rotation_euler.x bascula la tapa sobre su borde frontal; cierre con imanes"
    knobs = {}
    for c in lay["controls"]:
        e = bpy.data.objects.new(f"Perilla_{c['ref']}_{c['func']}", None)
        e.empty_display_size = 6
        e.location = (c["x"], c["y"], H + LID)
        e["tipo"], e["compra"], e["funcion"] = c["kind"], c["estado"], c["func"]
        knobs[c["ref"]] = e
        scene.collection.objects.link(e)
    bpy.context.view_layer.update()
    for e in knobs.values():
        e.parent = pivot
        e.matrix_parent_inverse = pivot.matrix_world.inverted()
    bpy.context.view_layer.update()

    objs, groups = {}, {}
    for item in data["objects"]:
        mesh = bpy.data.meshes.new(item["name"])
        verts = item["vertices"]
        g = item["group"]
        origin = Vector((0, 0, 0))
        if g.startswith("knob:"):
            origin = knobs[g[5:]].matrix_world.translation.copy()
            verts = [(v[0] - origin.x, v[1] - origin.y, v[2] - origin.z) for v in verts]
        mesh.from_pydata(verts, [], item["faces"])
        mesh.update()
        for p in mesh.polygons:
            p.use_smooth = True
        mesh.set_sharp_from_angle(angle=math.radians(28))
        o = bpy.data.objects.new(item["name"], mesh)
        mesh.materials.append(make_material(item["color"], lay["colors"][item["color"]]))
        for k, v in item["meta"].items():
            o[k] = v
        scene.collection.objects.link(o)
        if g.startswith("knob:"):
            o.parent = knobs[g[5:]]
        elif g in ("lid", "button"):
            o.parent = pivot
            o.matrix_parent_inverse = pivot.matrix_world.inverted()
        objs[item["name"]], groups[item["name"]] = o, g

    # Difusores: plástico opalino iluminado desde abajo con el color fijo de su banda.
    for bar in lay["bars"]:
        o = objs[f"Difusor_opalino_{bar['name']}"]
        mat = bpy.data.materials.new(f"E5_difusor_{bar['name']}")
        b = _principled(mat)
        col = bar["color"]
        sat = [max(0.0, c - .18) ** 1.6 for c in col]
        b.inputs["Base Color"].default_value = (*[c * .30 for c in sat], 1)
        b.inputs["Emission Color"].default_value = (*sat, 1)
        # Relieve hexagonal: el fondo de cada celda (0,5 mm) deja pasar más luz que el nervio (1,1 mm).
        nt = mat.node_tree
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        rib = nt.nodes.new("ShaderNodeMath"); rib.operation = "GREATER_THAN"; rib.inputs[1].default_value = lay["hex_rib_z"]
        nt.links.new(sep.outputs["Z"], rib.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        mix.inputs["A"].default_value = (*sat, 1); mix.inputs["B"].default_value = (*[c * .42 for c in sat], 1)
        nt.links.new(rib.outputs[0], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 1.1      # brillo fijo moderado (NEOPIXEL_BRILLO = 32/255)
        b.inputs["Roughness"].default_value = .7
        o.data.materials.clear(); o.data.materials.append(mat)
        o["firmware"] = "color fijo; no reacciona al audio"

    # Cables como curvas; los puntos de la tapa siguen a Tapa_pivote.
    wires = []
    inv = pivot.matrix_world.inverted()
    for w in lay["wires"]:
        cu = bpy.data.curves.new(w["name"], "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = w["dia"] / 2
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        sp = cu.splines.new("POLY")
        sp.points.add(len(w["pts"]) - 1)
        for p, q in zip(sp.points, w["pts"]):
            p.co = (q[0], q[1], q[2], 1)
        o = bpy.data.objects.new(f"Cable_{w['name']}", cu)
        cu.materials.append(make_material(w["color"], lay["colors"][w["color"]]))
        o["arnes"] = w["harness"]
        scene.collection.objects.link(o)
        lid_idx = [i for i, q in enumerate(w["pts"]) if q[3] == "l"]
        if lid_idx and len(lid_idx) == len(w["pts"]):
            o.parent = pivot
            o.matrix_parent_inverse = inv
        elif lid_idx:
            hook = o.modifiers.new("Sigue_a_la_tapa", "HOOK")
            hook.object = pivot
            hook.vertex_indices_set(lid_idx)
            hook.matrix_inverse = inv
        wires.append(o)

    # Pantalla: plano emisivo del área activa, sobre el módulo del CYD, que queda al ras de la tapa.
    t = lay["tft"]
    aw, ah = t["active"]
    cx, cy = t["center"][0] + t["offset_x"], t["center"][1]
    z = H + lay["LID"] + .08
    mesh = bpy.data.meshes.new("TFT_imagen")
    mesh.from_pydata([(cx - aw / 2, cy - ah / 2, z), (cx + aw / 2, cy - ah / 2, z), (cx + aw / 2, cy + ah / 2, z), (cx - aw / 2, cy + ah / 2, z)], [], [(0, 1, 2, 3)])
    uv = mesh.uv_layers.new(name="UV")
    for loop, co in zip(uv.data, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop.uv = co
    screen = bpy.data.objects.new("Pantalla_CYD_imagen_240x320_girada", mesh)
    smat = bpy.data.materials.new("E5_TFT_imagen")
    b = _principled(smat)
    tex = smat.node_tree.nodes.new("ShaderNodeTexImage")
    tex.interpolation = "Linear"
    if tft_image:
        tex.image = bpy.data.images.load(str(tft_image))
    smat.node_tree.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Strength"].default_value = 1.5
    b.inputs["Roughness"].default_value = .3
    b.inputs["Specular IOR Level"].default_value = .08
    mesh.materials.append(smat)
    link(screen, pivot)

    # Rótulos del panel.
    font = system_font()
    font.pack()
    ink = bpy.data.materials.new("E5_rotulo")
    ib = _principled(ink)
    ib.inputs["Base Color"].default_value = (.82, .84, .86, 1)
    ib.inputs["Roughness"].default_value = .6

    def label(text, x, y, size=4.2, align="CENTER", rot=0.0):
        cu = bpy.data.curves.new(f"Rotulo_{text}", "FONT")
        cu.body, cu.font, cu.size = text, font, size
        cu.align_x, cu.align_y = align, "CENTER"
        cu.extrude = .05
        o = bpy.data.objects.new(f"Rotulo_{text}", cu)
        o.location = (x, y, H + LID + .03)
        o.rotation_euler.z = rot
        cu.materials.append(ink)
        link(o, pivot)
        return o

    for c in lay["controls"]:
        label(c["func"], c["x"], c["y"] - 16.5)
        for a, txt in ((150, "–"), (-150, "+")):
            ang = math.radians(90 + a)
            label(txt, c["x"] + 14.5 * math.cos(ang), c["y"] + 14.5 * math.sin(ang), 4.0)
    label("VISTA", lay["sw1"][0], lay["sw1"][1] - 9.5, 3.2)
    for bar in lay["bars"]:
        label(bar["name"], bar["x0"] - 5, bar["y"], 3.6, "RIGHT")
    # En el borde trasero: el frente derecho lo ocupan ahora VOLUMEN y el pulsador VISTA.
    label("ECUALIZADOR · 3 BANDAS · E.5", W - 14, 183.5, 3.0, "RIGHT")

    # Piso, mundo y luces de estudio.
    floor = bpy.data.meshes.new("Piso")
    floor.from_pydata([(-1500, -1500, -.05), (1800, -1500, -.05), (1800, 1700, -.05), (-1500, 1700, -.05)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new("Piso", floor)
    fm = bpy.data.materials.new("E5_piso")
    fb = _principled(fm)
    fb.inputs["Base Color"].default_value = (.045, .055, .07, 1)
    fb.inputs["Roughness"].default_value = .55
    floor.materials.append(fm)
    link(fo)
    scene.world = bpy.data.worlds.new("Mundo")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (.10, .12, .15, 1)
    bg.inputs["Strength"].default_value = .55
    lights = []
    for name, pos, energy, size in (("Luz_principal", (-160, -330, 430), 1.9e6, 320), ("Luz_relleno", (520, -120, 300), 0.9e6, 300),
                                    ("Luz_contra", (140, 520, 360), 1.4e6, 260), ("Luz_cenital", (139, 96, 520), 0.7e6, 380)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.shape, ld.size = energy, "DISK", size
        lo = bpy.data.objects.new(name, ld)
        lo.location = pos
        lo.rotation_euler = (Vector((W / 2, D / 2, 20)) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        link(lo)
        lights.append(lo)
    cam_data = bpy.data.cameras.new("Camara")
    cam_data.clip_start, cam_data.clip_end = 5, 6000
    cam = bpy.data.objects.new("Camara", cam_data)
    link(cam)
    scene.camera = cam

    scene.render.engine = engine
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                break
            except Exception:
                continue
        for d in prefs.devices:
            d.use = d.type != "CPU"
        scene.cycles.device = "GPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        try:
            scene.cycles.denoiser = "OPTIX"
        except Exception:
            pass
    else:
        scene.eevee.taa_render_samples = samples
        for attr, val in (("use_raytracing", True), ("use_shadows", True)):
            if hasattr(scene.eevee, attr):
                setattr(scene.eevee, attr, val)
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.image_settings.file_format = "PNG"

    def aim(pos, target, lens=50, ortho=None):
        cam.location = pos
        cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        if ortho:
            cam_data.type, cam_data.ortho_scale = "ORTHO", ortho
        else:
            cam_data.type, cam_data.lens = "PERSP", lens

    def set_lid(angle_deg):
        pivot.rotation_euler.x = math.radians(angle_deg)

    def set_knob(ref, p):
        knobs[ref].rotation_euler.z = math.radians((0.5 - p) * lay["pot_travel_deg"])

    return {"scene": scene, "layout": lay, "objs": objs, "groups": groups, "pivot": pivot, "knobs": knobs, "wires": wires,
            "screen": screen, "tex": tex, "cam": cam, "aim": aim, "set_lid": set_lid, "set_knob": set_knob, "lights": lights,
            "button": objs["SW1_capuchon_VISTA"]}

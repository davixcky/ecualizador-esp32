"""Renderiza el ecualizador en Blender: la PCB exportada de KiCad (VRML) dentro del gabinete de
CadQuery (stl/), con la pantalla mostrando la vista de bandas del firmware.

    blender -b -P render_blender.py            → ../img/3d-gabinete-*.png

Necesita ../hardware/3d/ecualizador-placa.wrl (generar.sh lo exporta con kicad-cli) y la imagen
../img/ui-tft-bandas.png (firmware/test: make pantallas).
"""
import math
import os
import sys

import addon_utils
import bpy
from mathutils import Matrix, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(AQUI, "stl")
IMG = os.path.join(AQUI, "..", "img")
WRL = os.path.join(AQUI, "..", "hardware", "3d", "ecualizador-placa.wrl")
PANTALLA = os.path.join(IMG, "ui-tft-bandas.png")
MUESTRAS = int(os.environ.get("MUESTRAS", "96"))

# del modelo de CadQuery (gabinete.py)
TFT_CENTRO = (-46.0, 29.0)
Z_VIDRIO = 17.6
TAPA_SUBE = 85.0          # separación de la tapa en la vista abierta

bpy.ops.wm.read_factory_settings(use_empty=True)
for m in ("io_scene_x3d", "io_mesh_stl"):
    addon_utils.enable(m)
esc = bpy.context.scene
esc.unit_settings.scale_length = 0.001


def material(nombre, color, rugosidad=0.5, metal=0.0, emision=None, fuerza=0.0, transmision=0.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rugosidad
    b.inputs["Metallic"].default_value = metal
    if emision:
        b.inputs["Emission Color"].default_value = (*emision, 1)
        b.inputs["Emission Strength"].default_value = fuerza
    if transmision:
        b.inputs["Transmission Weight"].default_value = transmision
    return m


MAT = {
    "cuerpo": material("cuerpo", (0.78, 0.79, 0.81), 0.45),
    "tapa": material("tapa", (0.035, 0.04, 0.05), 0.38),
    "franja0": material("naranja", (1.0, 0.30, 0.08), 0.4, emision=(1.0, 0.30, 0.08), fuerza=1.5),
    "franja1": material("verde", (0.08, 0.75, 0.30), 0.4, emision=(0.08, 0.75, 0.30), fuerza=1.5),
    "franja2": material("cian", (0.05, 0.50, 1.0), 0.4, emision=(0.05, 0.50, 1.0), fuerza=1.5),
    "perilla": material("aluminio", (0.80, 0.80, 0.82), 0.28, metal=1.0),
    "deslizable": material("caucho", (0.02, 0.02, 0.025), 0.55),
    "boton": material("boton", (0.08, 0.75, 0.30), 0.35),
    "separadores": material("laton", (0.85, 0.65, 0.30), 0.3, metal=1.0),
    "parlante": material("parlante", (0.03, 0.03, 0.03), 0.6),
    "pam8403": material("pam", (0.05, 0.25, 0.65), 0.5),
    "pam8403-ci": material("ci", (0.02, 0.02, 0.02), 0.4),
    "tft-placa": material("tft-placa", (0.65, 0.05, 0.06), 0.5),
    "tft-vidrio": material("vidrio", (0.005, 0.005, 0.008), 0.08),
}


def importar_stl(nombre):
    bpy.ops.import_mesh.stl(filepath=os.path.join(STL, nombre + ".stl"))
    o = bpy.context.selected_objects[0]
    o.name = nombre
    clave = nombre if nombre in MAT else nombre.rstrip("0123456789").split("-")[0]
    o.data.materials.append(MAT.get(clave, MAT["cuerpo"]))
    bpy.ops.object.shade_smooth()
    if hasattr(o.data, "use_auto_smooth"):          # Blender 4.0
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(35)
    return o


# ---------------------------------------------------------------- placa de KiCad
antes = set(bpy.data.objects)
bpy.ops.import_scene.x3d(filepath=WRL)
nuevos = [o for o in bpy.data.objects if o not in antes]
mallas = [o for o in nuevos if o.type == "MESH"]
vacios = [o.name for o in nuevos if o.type != "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in mallas:
    o.select_set(True)
bpy.context.view_layer.objects.active = mallas[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.join()
pcb = bpy.context.view_layer.objects.active
pcb.name = "pcb"
for n in vacios:
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n])
# El VRML de KiCad viene con el eje Y hacia arriba: se gira para que la altura quede en Z.
# Primero se aplica la transformación que trae cada pieza del VRML (escala 2,54 y giros), así los
# vértices quedan en las coordenadas del VRML: centrado en la placa, X_vrml = 100 − x_pcb,
# Z_vrml = 60 − y_pcb y la altura en Y_vrml, con el centro del espesor de la placa en 0 (medido).
# Luego se lleva a X = x_pcb − 100, Y = 60 − y_pcb, Z = 0 en la cara inferior de la PCB.
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pcb.matrix_world = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0.79), (0, 0, 0, 1)))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---------------------------------------------------------------- gabinete
obj = {}
for f in sorted(os.listdir(STL)):
    if f.endswith(".stl"):
        obj[f[:-4]] = importar_stl(f[:-4])

# pantalla: plano con la imagen de la interfaz como emisión (área activa de 57,6 × 43,2 mm)
bpy.ops.mesh.primitive_plane_add(size=1, location=(TFT_CENTRO[0], TFT_CENTRO[1], Z_VIDRIO + 0.05))
pantalla = bpy.context.active_object
pantalla.name = "pantalla"
pantalla.scale = (57.6, 43.2, 1)
mp = bpy.data.materials.new("pantalla")
mp.use_nodes = True
nt = mp.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(PANTALLA)
tex.interpolation = "Closest"
emi = nt.nodes.new("ShaderNodeEmission")
emi.inputs["Strength"].default_value = 1.6
nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
nt.links.new(emi.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
pantalla.data.materials.append(mp)

TAPA = ["tapa", "franja0", "franja1", "franja2", "perilla-nivel", "perilla-volumen", "deslizable0", "deslizable1",
        "deslizable2", "boton"]

# ---------------------------------------------------------------- luz, mundo y render
mundo = bpy.data.worlds.new("mundo")
esc.world = mundo
mundo.use_nodes = True
fondo = mundo.node_tree.nodes["Background"]
fondo.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1)
fondo.inputs["Strength"].default_value = 0.35


def luz(nombre, tipo, pos, energia, tam=None, color=(1, 1, 1)):
    d = bpy.data.lights.new(nombre, tipo)
    d.energy = energia
    d.color = color
    if tam:
        d.size = tam
    o = bpy.data.objects.new(nombre, d)
    esc.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


luz("principal", "AREA", (-260, -320, 420), 3.2e6, 260)
luz("relleno", "AREA", (380, -120, 200), 0.9e6, 220, (0.9, 0.95, 1.0))
luz("contra", "AREA", (0, 380, 300), 1.2e6, 220)

# piso infinito
bpy.ops.mesh.primitive_plane_add(size=5000, location=(0, 0, -31.5))
piso = bpy.context.active_object
piso.data.materials.append(material("piso", (0.93, 0.94, 0.96), 0.85))

esc.render.engine = "CYCLES"
esc.cycles.samples = MUESTRAS
esc.cycles.use_denoising = False   # la versión de Blender de Ubuntu no trae OpenImageDenoise
esc.cycles.device = "CPU"
esc.render.resolution_x = 1800
esc.render.resolution_y = 1150
esc.render.film_transparent = False
esc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
                                                      esc.view_settings.bl_rna.properties["view_transform"].enum_items] \
    else "Filmic"
esc.view_settings.look = "None"

cam_d = bpy.data.cameras.new("camara")
cam = bpy.data.objects.new("camara", cam_d)
esc.collection.objects.link(cam)
esc.camera = cam


def apuntar(pos, objetivo, lente=55, orto=None):
    cam.location = pos
    cam.rotation_euler = (Vector(objetivo) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    if orto:
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = orto
    else:
        cam_d.type = "PERSP"
        cam_d.lens = lente
    cam_d.clip_end = 10000


def render(nombre):
    esc.render.filepath = os.path.join(IMG, nombre)
    bpy.ops.render.render(write_still=True)
    print("Escrita", nombre)


vistas = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["cerrado", "abierto", "planta", "debajo"]

if "cerrado" in vistas:
    apuntar((170, -330, 300), (5, -5, 0), 50)
    render("3d-gabinete-cerrado.png")

if "planta" in vistas:
    esc.render.resolution_y = 1110
    apuntar((0, 0, 600), (0, 0, 0), orto=232)
    render("3d-gabinete-planta.png")
    esc.render.resolution_y = 1150

if "abierto" in vistas:
    for n in TAPA:
        obj[n].location.z += TAPA_SUBE
    apuntar((210, -330, 430), (0, 5, 20), 46)
    render("3d-gabinete-abierto.png")
    for n in TAPA:
        obj[n].location.z -= TAPA_SUBE

if "debajo" in vistas:
    piso.hide_render = True
    apuntar((150, -260, -260), (0, 0, -10), 50)
    render("3d-gabinete-debajo.png")
    piso.hide_render = False

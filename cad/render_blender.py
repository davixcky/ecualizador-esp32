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
TFT_CENTRO = (-49.0, 29.0)
Z_VIDRIO = 17.6
TAPA_SUBE = 85.0          # separación de la tapa en la vista abierta

bpy.ops.wm.read_factory_settings(use_empty=True)

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
    "rotulos": material("rotulos plata", (.72,.75,.78), .55),
    "iman": material("neodimio niquelado", (0.65,0.67,0.69), .22, metal=1),
    "tira": material("tira", (0.04,0.04,0.04)),
    "led": material("led", (0.6,0.9,1.0), emision=(0.2,0.7,1.0), fuerza=3),
    "difusor": material("difusor opal", (0.7,0.9,1.0), emision=(0.1,0.5,0.7), fuerza=1.5),
    "cuerpo": material("cuerpo", (0.035, 0.043, 0.052), 0.4),
    "tapa": material("tapa", (0.10, 0.12, 0.14), 0.36),
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
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.stl_import(filepath=os.path.join(STL, nombre + ".stl"))
    o = bpy.context.active_object
    o.name = nombre
    clave = nombre if nombre in MAT else nombre.rstrip("0123456789").split("-")[0]
    o.data.materials.append(MAT.get(clave, MAT["cuerpo"]))
    bpy.ops.object.shade_flat()
    if hasattr(o.data, "use_auto_smooth"):          # Blender 4.0
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(35)
    return o


# ---------------------------------------------------------------- placa de KiCad
bpy.ops.import_scene.gltf(filepath=os.path.join(AQUI,"..","hardware","3d","ecualizador-placa.glb"))
mallas=[o for o in bpy.context.scene.objects if o.type=="MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in mallas:o.select_set(True)
bpy.context.view_layer.objects.active=mallas[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.join()
pcb=bpy.context.active_object
pcb.name="pcb"
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
pcb.scale=(1,1,1) # glTF importer already converts metres to scene millimetres
assert 199 < pcb.dimensions.x < 201, f"Escala PCB incorrecta: {pcb.dimensions}"
pcb.location.z=1.6
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

# Controles del panel: posiciones mecánicas conservadas, ahora conectados por cables.
# Los modelos proceden de las huellas originales; se sujetan al panel.
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(AQUI,"..","hardware","3d","panel-controles.glb"))
control_models=[o for o in set(bpy.data.objects)-before if o.type=="MESH"]
for o in control_models:
    bpy.context.view_layer.objects.active=o
    o.select_set(True)
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    o.location.z+=1.6
    o.select_set(False)

# ---------------------------------------------------------------- gabinete
obj = {}
for f in sorted(os.listdir(STL)):
    if f.endswith(".stl"):
        obj[f[:-4]] = importar_stl(f[:-4])

# Pantalla Waveshare: área activa horizontal 42,72 × 22,70 mm.
bpy.ops.mesh.primitive_plane_add(size=1, location=(TFT_CENTRO[0], TFT_CENTRO[1], Z_VIDRIO + 0.05))
pantalla = bpy.context.active_object
pantalla.name = "pantalla"
pantalla.scale = (42.72, 22.70, 1)
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

TAPA = ["tapa", "rotulos", "franja0", "franja1", "franja2", "perilla-nivel", "perilla-volumen", "deslizable0", "deslizable1",
        "deslizable2", "boton", "cuna-tft", "tft-placa", "tft-vidrio"] + [f"iman-tapa{i}" for i in range(4)]

# Identificación del parlante sobre la culata, visible en la vista de canales.
rotulo=bpy.data.curves.new('etiqueta-parlante','FONT');rotulo.body='PARLANTE\n4 ohm / 3 W';rotulo.size=2.0;rotulo.align_x='CENTER';rotulo.align_y='CENTER';rotulo.extrude=.01
obj_rot=bpy.data.objects.new('etiqueta-parlante',rotulo);bpy.context.collection.objects.link(obj_rot);obj_rot.location=(-55,-28,-7.15);rotulo.materials.append(MAT['rotulos'])

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
esc.render.image_settings.file_format = "PNG"
esc.cycles.use_denoising = True   # la versión de Blender de Ubuntu no trae OpenImageDenoise
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
    for o in control_models: o.location.z += TAPA_SUBE
    pantalla.location.z += TAPA_SUBE
    for n in TAPA:
        obj[n].location.z += TAPA_SUBE
    apuntar((210, -330, 430), (0, 5, 20), 46)
    render("3d-gabinete-abierto.png")
    for o in control_models: o.location.z -= TAPA_SUBE
    pantalla.location.z -= TAPA_SUBE
    for n in TAPA:
        obj[n].location.z -= TAPA_SUBE

if "debajo" in vistas:
    piso.hide_render = True
    apuntar((150, -260, -260), (0, 0, -10), 50)
    render("3d-gabinete-debajo.png")
    piso.hide_render = False

if "canales" in vistas:
    for o in control_models: o.hide_render = True
    pcb.hide_render = True
    pantalla.hide_render = True
    for n in TAPA: obj[n].hide_render = True
    apuntar((80, -260, 340), (0, 0, -3), 48)
    render("3d-gabinete-canales.png")

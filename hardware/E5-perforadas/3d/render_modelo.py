#!/usr/bin/env python3
"""Exporta el FCStd a JSON con FreeCAD y lo renderiza con Blender."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
TEMP = HERE / ".render"


def exportar():
    import FreeCAD as App
    TEMP.mkdir(exist_ok=True)
    doc = App.openDocument(str(HERE / "ecualizador-E5-perforadas.FCStd"))
    data = []
    for obj in doc.Objects:
        if not hasattr(obj, "Shape") or obj.Shape.isNull():
            continue
        vertices, faces = obj.Shape.tessellate(.18)
        data.append({
            "name": obj.Name, "vertices": [tuple(v) for v in vertices], "faces": faces,
            "color": [float(v) for v in obj.ColorRGB.split(",")], "group": obj.AssemblyGroup,
        })
    path = TEMP / "ensamble.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    print(path)


def renderizar(path):
    import bpy
    from mathutils import Vector
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 2000, 1300
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.72, .74, .78, 1)
    background.inputs["Strength"].default_value = .75
    scene.view_settings.look = "AgX - Medium High Contrast"
    objects, groups = {}, {}
    for item in data:
        mesh = bpy.data.meshes.new(item["name"])
        mesh.from_pydata(item["vertices"], [], item["faces"]); mesh.update()
        obj = bpy.data.objects.new(item["name"], mesh); scene.collection.objects.link(obj)
        mat = bpy.data.materials.new(item["name"]); mat.diffuse_color = (*item["color"], 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*item["color"], 1)
        shader.inputs["Roughness"].default_value = .62
        if "Pixels" in item["name"]:
            shader.inputs["Emission Color"].default_value = (*item["color"], 1)
            shader.inputs["Emission Strength"].default_value = 1.8
        obj.data.materials.append(mat)
        objects[item["name"]], groups[item["name"]] = obj, item["group"]
    floor = bpy.data.meshes.new("Floor")
    floor.from_pydata([(-500,-500,0),(500,-500,0),(500,500,0),(-500,500,0)], [], [(0,1,2,3)])
    floor_obj = bpy.data.objects.new("Floor", floor); scene.collection.objects.link(floor_obj)
    fm = bpy.data.materials.new("Floor"); fm.diffuse_color=(.93,.94,.96,1); floor_obj.data.materials.append(fm)
    for pos, energy, size in (((-180,-220,360),1300,220),((360,80,260),900,180)):
        light = bpy.data.lights.new("Area", "AREA"); light.energy=energy; light.shape="DISK"; light.size=size
        lo=bpy.data.objects.new("Area",light); scene.collection.objects.link(lo); lo.location=pos
        lo.rotation_euler=(Vector((118,93,20))-lo.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new("Camera"); camera_data.type="ORTHO"
    camera=bpy.data.objects.new("Camera",camera_data); scene.collection.objects.link(camera); scene.camera=camera

    def shot(name, target, direction, scale):
        target=Vector(target); camera.location=target+Vector(direction).normalized()*600
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler(); camera_data.ortho_scale=scale
        scene.render.filepath=str(HERE/name); bpy.ops.render.render(write_still=True)

    for name,obj in objects.items():
        obj.location=(0,0,0); obj.hide_render=False
    shot("ecualizador-E5-cerrado.png", (139,96,30), (-.65,-.9,1), 340)
    for name,obj in objects.items():
        obj.location=(300,0,-61) if groups[name]=="lid" else (0,0,0); obj.hide_render=False
    shot("ecualizador-E5-abierto.png", (215,96,24), (-.55,-.85,1.15), 500)
    for name,obj in objects.items():
        obj.location=(0,0,0); obj.hide_render=groups[name]=="lid"
    shot("ecualizador-E5-planta.png", (139,96,12), (0,-.06,1), 310)


if "--" in sys.argv:
    renderizar(sys.argv[-1])
else:
    exportar()

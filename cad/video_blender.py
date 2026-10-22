"""Blender 5.1: video reproducible del CAD con LED y TFT animados.
PREVIEW=1 blender -b -P cad/video_blender.py: tres fotogramas de revisión.
blender -b -P cad/video_blender.py: secuencia completa (36 s, 24 fps).
"""
import os, sys, runpy, math, json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from demo_timeline import FPS,FRAMES,state
# Reutilizar geometría, posiciones y materiales del render estático, sin renderizar vistas.
sys.argv=['render_blender.py','--','escena']
s=runpy.run_path(str(ROOT/'render_blender.py'))
scene=s['esc']; cam=s['cam']; obj=s['obj']; mats=s['MAT']
OUT=ROOT.parent/'docs/video'; OUT.mkdir(exist_ok=True)
frames=OUT/'frames'; frames.mkdir(exist_ok=True)
scene.render.engine='CYCLES'
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX'; prefs.get_devices()
for device in prefs.devices: device.use=device.type!='CPU'
scene.cycles.device='GPU'; scene.cycles.samples=24; scene.cycles.denoiser='OPTIX'
scene.render.resolution_x=1920; scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.fps=FPS; scene.frame_start=1; scene.frame_end=FRAMES
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(frames/'frame-')
# Estudio oscuro, superficies legibles y borde de luz.
s['fondo'].inputs['Color'].default_value=(.06,.08,.11,1)
s['fondo'].inputs['Strength'].default_value=.3
s['piso'].data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.027,.036,.048,1)
s['piso'].data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.45
# Fotogramas de pantalla a resolución física horizontal 320×170.
tex=s['tex']; tex.image=bpy.data.images.load(str(ROOT/'video-texturas/tft-0001.png'))
tex.image.source='SEQUENCE'; tex.image_user.frame_duration=FRAMES
tex.image_user.frame_start=1; tex.image_user.use_auto_refresh=True
tex.interpolation='Closest'
# LED: color de la banda que se está ajustando; intensidad a partir del audio.
rows=json.loads((OUT/'demo-timeline.json').read_text())
palette=[(1,.24,.035,1),(.04,.8,.35,1),(.035,.45,1,1)]
for key in ['led','difusor']:
    node=mats[key].node_tree.nodes['Principled BSDF']
    for fr,row in enumerate(rows,1):
        color=palette[row['active']] if row['active'] is not None else (.05,.5,.8,1)
        for field in ['Emission Color','Base Color']:
            node.inputs[field].default_value=color
            node.inputs[field].keyframe_insert('default_value',frame=fr)
        node.inputs['Emission Strength'].default_value=.65+2.1*max(row['bands'])
        node.inputs['Emission Strength'].keyframe_insert('default_value',frame=fr)
# Cámara: vista general, acercamiento a los controles y apertura de tapa.
shots=[(1,(210,-340,310),(0,0,0),50),(73,(15,-295,410),(0,0,0),52),
       (577,(15,-295,410),(0,0,0),52),(673,(180,-340,340),(0,0,0),49),
       (745,(230,-355,380),(0,0,35),47),(793,(250,-330,365),(0,0,35),47),
       (864,(210,-340,310),(0,0,0),50)]
for fr,pos,target,lens in shots:
    s['apuntar'](pos,target,lens)
    cam.keyframe_insert('location',frame=fr); cam.keyframe_insert('rotation_euler',frame=fr)
    cam.data.keyframe_insert('lens',frame=fr)
# Despiece: la tapa imantada sube junto con su pantalla y controles.
lid=[obj[n] for n in s['TAPA']]+s['control_models']+[s['pantalla']]
for o in lid:
    z=o.location.z
    for fr,offset in [(1,0),(673,0),(745,72),(793,72),(850,0),(864,0)]:
        o.location.z=z+offset; o.keyframe_insert('location',index=2,frame=fr)
# Los STL tienen posiciones iniciales +9,+2,-5 mm: centrar y recorrer 30 mm.
for i in range(3):
    slider=obj[f'deslizable{i}']
    for fr,row in enumerate(rows,1):
        slider.location.y=(row['sliders'][i]-.5)*30-(9,2,-5)[i]
        slider.keyframe_insert('location',index=1,frame=fr)
# Audio en la escena editable: el mismo WAV se multiplexa en el MP4.
editor=scene.sequence_editor_create()
editor.strips.new_sound('Demo SPICE',str(OUT/'demo-audio.wav'),channel=1,frame_start=1)
# Halo óptico moderado de los LED y pantalla.
scene.use_nodes=True
nt=scene.compositing_node_group if hasattr(scene,'compositing_node_group') else scene.node_tree
if nt is None:
    nt=bpy.data.node_groups.new('Composición','CompositorNodeTree'); scene.compositing_node_group=nt
nt.nodes.clear()
r=nt.nodes.new('CompositorNodeRLayers'); glare=nt.nodes.new('CompositorNodeGlare')
glare.inputs['Type'].default_value='Fog Glow'; glare.inputs['Quality'].default_value='Medium'; glare.inputs['Threshold'].default_value=2
# Blender 5.1 usa salida de grupo en lugar de Composite.
if hasattr(scene,'compositing_node_group'):
    nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    out=nt.nodes.new('NodeGroupOutput')
else: out=nt.nodes.new('CompositorNodeComposite')
nt.links.new(r.outputs['Image'],glare.inputs['Image']); nt.links.new(glare.outputs['Image'],out.inputs[0])
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ecualizador-animado.blend'))
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ecualizador-animado.blend'))
if os.environ.get('PREVIEW'):
    for fr in [1,192,745]:
        scene.frame_set(fr); scene.render.filepath=str(OUT/f'preview-{fr}.png')
        bpy.ops.render.render(write_still=True)
elif not os.environ.get('BUILD_ONLY'): bpy.ops.render.render(animation=True)

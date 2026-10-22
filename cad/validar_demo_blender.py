"""Verifica el reloj compartido de deslizadores, pantalla, luces y sonido."""
import bpy,json,math,os
from pathlib import Path
root=Path(bpy.data.filepath).parent
rows=json.loads((root/'demo-timeline.json').read_text())
s=bpy.context.scene
assert s.frame_end==len(rows)==864
for frame in [1,94,121,192,241,289,361,409,457,529,577,673,745,864]:
    s.frame_set(frame);row=rows[frame-1]
    for i in range(3):
        y=bpy.data.objects[f'deslizable{i}'].location.y
        expected=(row['sliders'][i]-.5)*30-(9,2,-5)[i]
        assert abs(y-expected)<1e-4,(frame,i,y,expected)
    material=bpy.data.materials['difusor opal'].node_tree.nodes['Principled BSDF']
    expected=.65+2.1*max(row['bands'])
    assert abs(material.inputs['Emission Strength'].default_value-expected)<1e-4
sounds=[strip for strip in s.sequence_editor.strips if strip.type=='SOUND']
assert len(sounds)==1 and sounds[0].frame_start==1
assert os.path.isfile(bpy.path.abspath(sounds[0].sound.filepath))
missing=[im.name for im in bpy.data.images if im.users and im.source in {'FILE','SEQUENCE'} and not im.packed_file and not os.path.isfile(bpy.path.abspath(im.filepath))]
assert not missing,missing
print('DEMO_SYNC_OK: 14 estados, 3 deslizadores, emisión LED y audio en fotograma 1')

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
    # El firmware mantiene los 12 WS2812B fijos y tenues durante la captura ADC:
    # cuatro naranjas, cuatro verdes y cuatro azules. La dinámica está en el TFT.
    for side in range(2):
        for band in range(3):
            diffuser=bpy.data.materials[f'difusor-banda-{side}-{band}'].node_tree.nodes['Principled BSDF']
            assert abs(diffuser.inputs['Emission Strength'].default_value-1.6)<1e-4
            for pixel in range(band*2,band*2+2):
                led=bpy.data.materials[f'pixel-{side}-{pixel}'].node_tree.nodes['Principled BSDF']
                assert abs(led.inputs['Emission Strength'].default_value-3.0)<1e-4
sounds=[strip for strip in s.sequence_editor.strips if strip.type=='SOUND']
assert len(sounds)==1 and sounds[0].frame_start==1
assert os.path.isfile(bpy.path.abspath(sounds[0].sound.filepath))
missing=[im.name for im in bpy.data.images if im.users and im.source in {'FILE','SEQUENCE'} and not im.packed_file and not os.path.isfile(bpy.path.abspath(im.filepath))]
assert not missing,missing
print('DEMO_SYNC_OK: 14 estados, 3 deslizadores, 12 LED fijos por banda y audio en fotograma 1')

"""Renderiza un tramo del .blend usando OptiX; omite fotogramas existentes."""
import bpy,sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
a,b=map(int,args)
p=bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type='OPTIX';p.get_devices()
for d in p.devices:d.use=d.type!='CPU'
s=bpy.context.scene;s.cycles.device='GPU';s.cycles.denoiser='OPTIX'
s.render.threads_mode='FIXED';s.render.threads=3
out=Path(bpy.data.filepath).parent/'frames'
for f in range(a,b+1):
    target=out/f'frame-{f:04d}.png'
    if target.exists():continue
    s.frame_set(f);s.render.filepath=str(target)
    bpy.ops.render.render(write_still=True)

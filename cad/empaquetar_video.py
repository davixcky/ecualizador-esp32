"""Paquete de Blender que conserva las rutas relativas de las texturas."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parent.parent
out=root/'docs/video'
with ZipFile(out/'ecualizador-blender.zip','w',ZIP_DEFLATED) as z:
    for p in [out/'ecualizador-animado.blend',out/'README.md',out/'demo-audio.wav',out/'demo-entrada.wav',out/'demo-timeline.json',out/'respuestas-spice.npz',out/'validacion-audio.json',*sorted((root/'cad/video-texturas').glob('*.png'))]:
        z.write(p,p.relative_to(root))
    z.writestr('ABRIR.txt','Extraer todo. Abrir docs/video/ecualizador-animado.blend en Blender 5.1.\nLas texturas se encuentran en cad/video-texturas; conservar las carpetas.\nLa barra espaciadora reproduce la animación con su pista de sonido. La escena usa Cycles/OptiX; elegir CPU u otra GPU si hace falta.\n')
print(out/'ecualizador-blender.zip')

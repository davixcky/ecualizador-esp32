"""Paquete transportable: conservar rutas relativas y ofrecer entradas sencillas."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
r=Path(__file__).resolve().parents[1]
files=[r/'docs/informe-fase2.pdf',r/'hardware/ecualizador.pdf',r/'hardware/pcb-rev-D2.pdf']
files+=list((r/'docs/presentacion').glob('*.pdf'))+list((r/'docs/presentacion').glob('*.pptx'))
files+=list((r/'simulacion/velxio').glob('*.md'))+list((r/'simulacion/velxio').glob('validacion-integrado-*.json'))+list((r/'simulacion/velxio').glob('*.vlx'))+[r/'simulacion/velxio/index.html',r/'simulacion/velxio/DEMO-HOY.md']
# Incluir el esquema editable y sus bibliotecas locales, sin exigir las rutas del autor.
files += [r/'hardware'/name for name in ('ecualizador.kicad_sch','ecualizador.kicad_pro','Ecualizador.kicad_sym','sym-lib-table','fp-lib-table')]
files += list((r/'hardware/Ecualizador.pretty').glob('*'))
files += list((r/'img').glob('velxio-*.png'))+[r/'img/marca/cuc-logo.png']
files += [r/'docs/video/ecualizador-animado.mp4', r/'docs/video/portada.jpg', r/'docs/video/README.md']
with ZipFile(r/'docs/exposicion-portable.zip','w',ZIP_DEFLATED) as z:
 for p in dict.fromkeys(files):
  if p.is_file():z.write(p,p.relative_to(r))
 z.write(r/'hardware/ecualizador.pdf','esquema.pdf')
 z.writestr('ABRIR-PRIMERO.txt','Extraer TODO el ZIP antes de abrir los archivos.\n\nPresentación: docs/presentacion/presentacion-animada.pptx\nPDF: docs/presentacion/presentacion-fase2.pdf\nVideo del dispositivo: docs/video/ecualizador-animado.mp4 (36 s, Full HD; con audio del modelo SPICE).\nEsquema independiente: esquema.pdf (no requiere KiCad).\nEl botón Abrir esquema PDF salta al anexo interno del PDF y PowerPoint.\nSimulaciones: simulacion/velxio/index.html; importar los VLX en https://velxio.dev/editor?esp32sim=qemu. Requiere Internet.\nEsquema editable: hardware/ecualizador.kicad_sch, con KiCad 9 o posterior y las bibliotecas incluidas.\n')
print('docs/exposicion-portable.zip')

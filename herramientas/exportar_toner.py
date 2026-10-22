#!/usr/bin/env python3
"""PDF vectorial a escala 1:1, centrado y con regla de comprobación de 100 mm."""
from pathlib import Path
import subprocess,tempfile
import pymupdf as f
R=Path(__file__).resolve().parents[1];mm=72/25.4
with tempfile.TemporaryDirectory() as folder:
 for mirror,name in [(False,'cobre-inferior-1a1.pdf'),(True,'toner-espejo-1a1.pdf')]:
  raw=Path(folder)/name;cmd=['kicad-cli','pcb','export','pdf',str(R/'hardware/ecualizador.kicad_pcb'),'-o',str(raw),'-l','B.Cu,Edge.Cuts','--mode-single','--scale','1','--black-and-white']
  if mirror:cmd+=['--mirror']
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
  src=f.open(raw);doc=f.open();page=doc.new_page(width=297*mm,height=210*mm)
  clip=f.Rect(src[0].rect.width-200*mm if mirror else 0,0,src[0].rect.width if mirror else 200*mm,120*mm)
  target=f.Rect(48.5*mm,45*mm,248.5*mm,165*mm);page.show_pdf_page(target,src,0,clip=clip,keep_proportion=False)
  page.draw_rect(target,color=(0,0,0),width=.2)
  page.insert_text((48.5*mm,34*mm),'D.2 - COBRE INFERIOR - '+('ESPEJO PARA TONER' if mirror else 'VISTA DESDE COMPONENTES'),fontsize=11)
  page.insert_text((48.5*mm,40*mm),'200 x 120 mm | Imprimir al 100 %, sin ajustar a la pagina.',fontsize=9)
  a,b=f.Point(48.5*mm,180*mm),f.Point(148.5*mm,180*mm);page.draw_line(a,b,color=(0,0,0),width=.5)
  for x in [a.x,b.x]:page.draw_line((x,178*mm),(x,182*mm),color=(0,0,0),width=.5)
  page.insert_text((82*mm,187*mm),'Comprobar: 100 mm',fontsize=9)
  doc.save(R/'hardware/una-cara'/name)

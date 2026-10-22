#!/usr/bin/env python3
"""Recortes vectoriales del esquema real para explicar etapas en LaTeX."""
from pathlib import Path
import pymupdf as f
root=Path(__file__).resolve().parents[1]
p=f.open(root/'hardware/ecualizador.pdf');mm=72/25.4
crops={'entrada':(133.35,15.24,262.89,96.52),'referencia':(12.7,15.24,130.81,96.52),'filtros':(12.7,99.06,407.67,151.13),'graves':(13,107,111,150),'medios':(108,107,299,150),'agudos':(307,107,406,151),'antialias':(151,208,263,248),'pantalla':(266,16,407,96),'sumador':(12.7,153.67,148.59,248.92),'detector-graves':(266,161,380,188),'detectores':(265.43,153.67,407.67,248.92),'neopixel':(12.7,254,407.67,335.28)}
outdir=root/'img/circuitos';outdir.mkdir(exist_ok=True)
for name,b in crops.items():
 clip=f.Rect(*(v*mm for v in b));out=f.open();page=out.new_page(width=clip.width,height=clip.height);page.show_pdf_page(page.rect,p,0,clip=clip);out.save(outdir/f'{name}.pdf');page.get_pixmap(matrix=f.Matrix(2,2)).save(outdir/f'{name}.png')
p[0].get_pixmap(matrix=f.Matrix(1.4,1.4)).save(root/'img/esquematico.png')
# Plano D.2: distribución real de componentes, generado por dibujar_pcb_una_cara.py.
import shutil
shutil.copyfile(root/'hardware/una-cara/pcb-una-cara-componentes.pdf',outdir/'pcb-capas.pdf')
shutil.copyfile(root/'img/pcb-una-cara-componentes.png',outdir/'pcb-capas.png')
# Aislar el detector usando la MISMA función de dibujo: evita cortar la fila contigua.
import subprocess,tempfile,sys
sys.path.insert(0,str(root/'herramientas'))
from generar_esquematico import Esquematico,detector
with tempfile.TemporaryDirectory() as folder:
    sch=Esquematico()
    detector(sch,'U3A','U3B',30,30,'D1','C22','R27','G_W','ADC_G')
    src=Path(folder)/'detector.kicad_sch'
    sch.guardar(str(src),['Detector de graves','2026-10-22','B.1','CUC'],papel='A4')
    dest=Path(folder)/'detector.pdf'
    subprocess.run(['kicad-cli','sch','export','pdf',str(src),'-o',str(dest),'--exclude-drawing-sheet'],check=True,capture_output=True)
    original=f.open(dest);clip=f.Rect(*(v*mm for v in (10,17,108,49)))
    out=f.open();page=out.new_page(width=clip.width,height=clip.height);page.show_pdf_page(page.rect,original,0,clip=clip)
    out.save(outdir/'detector-graves.pdf');page.get_pixmap(matrix=f.Matrix(3,3)).save(outdir/'detector-graves.png')

# Figuras de enseñanza sin bordes cortados ni fragmentos de etapas vecinas.
from generar_esquematico import sallen_key, entrada, salida, pasivo_h, pasivo_v, a_potencia

def guardar_etapa(name, sch, bounds):
    with tempfile.TemporaryDirectory() as folder:
        src=Path(folder)/'etapa.kicad_sch';dest=Path(folder)/'etapa.pdf'
        sch.guardar(str(src),['Etapa del ecualizador','2026-10-22','D.2','CUC'],papel='A4')
        subprocess.run(['kicad-cli','sch','export','pdf',str(src),'-o',str(dest),'--exclude-drawing-sheet'],check=True,capture_output=True)
        # Comparar las redes de la figura con los mismos pines de circuito.py.
        from verificar_netlist import netlist_kicad
        import circuito
        actual,_=netlist_kicad(str(src));expected={};observed={}
        for rp,net in actual.items():
            if rp[0].startswith('#') or net.startswith('unconnected'):continue
            expected.setdefault(circuito.pieza(rp[0])['pines'][rp[1]],set()).add(rp)
            observed.setdefault(net,set()).add(rp)
        assert {frozenset(v) for v in expected.values()}=={frozenset(v) for v in observed.values()},name
        original=f.open(dest);clip=f.Rect(*(v*mm for v in bounds));out=f.open()
        page=out.new_page(width=clip.width,height=clip.height);page.show_pdf_page(page.rect,original,0,clip=clip)
        out.save(outdir/f'{name}.pdf');page.get_pixmap(matrix=f.Matrix(3,3)).save(outdir/f'{name}.png')

for name,unit,refs,rin,rout in [
    ('graves','U1C',('R9','R10','C11','C12'),'PRE','GRAVES'),
    ('agudos','U2B',('C17','C18','R15','R16'),'PRE','AGUDOS'),
    ('antialias','U2D',('R25','R26','C20','C21'),'EQ_OUT','ADC_FFT')]:
    sch=Esquematico();sallen_key(sch,unit,60,40,*refs,rin,rout)
    guardar_etapa(name,sch,(0,20,110,58))
sch=Esquematico()
a,b=sallen_key(sch,'U1D',60,40,'C13','C14','R11','R12','PRE','MED_HP',etiquetas=False)
c,d=sallen_key(sch,'U2A',140,40,'R13','R14','C15','C16','MED_HP','MEDIOS',etiquetas=False)
entrada(sch,a,'PRE');sch.cable(b,(90,b[1]),(90,c[1]),c);sch.etiqueta('MED_HP',90,c[1]);salida(sch,d,'MEDIOS')
guardar_etapa('medios',sch,(5,20,178,58))
# Ruta de datos LED continua. Las alimentaciones usan símbolos +5V/GND convencionales.
sch=Esquematico();u=sch.colocar('U6',60,40,unidad=1,ref_at=(57,31),val_at=(53,34))
r1,r2=pasivo_h(sch,'R31',95,40)
j=sch.colocar('J5',140,40,ref_at=(136,32),val_at=(128,65))
sch.cable(u['3'],r1);sch.cable(r2,j['2'])
sch.cable((27,40),u['2']);sch.etiqueta('LED_DATA',27,40,180)
a,b=pasivo_v(sch,'R32',38,55);sch.cable((38,40),a)
a_potencia(sch,b,'GND',[(0,3.81)],0);a_potencia(sch,u['1'],'GND',[(0,5.08)],0)
a_potencia(sch,j['1'],'+5V',[(-7.62,0),(0,-10.16)],0)
a_potencia(sch,j['3'],'GND',[(-7.62,0),(0,12.7)],0)
# A la derecha, condensadores junto al conector; el primer LED recibe DIN desde J5.
for ref,x in [('C25',165),('C26',187)]:
 a,b=pasivo_v(sch,ref,x,40);a_potencia(sch,a,'+5V',[(0,-5.08)],0);a_potencia(sch,b,'GND',[(0,5.08)],0)
guardar_etapa('neopixel',sch,(8,18,204,69))

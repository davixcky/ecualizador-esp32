"""Figuras para guía de cableado, con margen suficiente para las etiquetas."""
from pathlib import Path
import tempfile,subprocess
import pymupdf as f
from generar_esquematico import Esquematico,detector
root=Path(__file__).resolve().parents[1];outdir=root/'docs/protoboard';mm=72/25.4
source=f.open(root/'hardware/ecualizador.pdf')
for name,bounds in [('sumador',(12.7,153.67,157,248.92)),('salida',(151,153.67,263,204))]:
    out=f.open();rect=f.Rect(*(v*mm for v in bounds));p=out.new_page(width=rect.width,height=rect.height);p.show_pdf_page(p.rect,source,0,clip=rect);out.save(outdir/f'esquema-{name}.pdf')
with tempfile.TemporaryDirectory() as folder:
    sch=Esquematico();detector(sch,'U3A','U3B',30,30,'D1','C22','R27','G_W','ADC_G')
    src=Path(folder)/'detector.kicad_sch';pdf=Path(folder)/'detector.pdf'
    sch.guardar(str(src),['Detector de graves','2026-10-23','D.2','CUC'],papel='A4')
    subprocess.run(['kicad-cli','sch','export','pdf',str(src),'-o',str(pdf),'--exclude-drawing-sheet'],check=True,capture_output=True)
    original=f.open(pdf);rect=f.Rect(*(v*mm for v in (10,17,120,49)));out=f.open();p=out.new_page(width=rect.width,height=rect.height);p.show_pdf_page(p.rect,original,0,clip=rect);out.save(outdir/'esquema-detector.pdf')
# Salida de línea aislada: evita incluir textos de los bloques vecinos.
from generar_esquematico import pasivo_h,pasivo_v,entrada,salida,a_potencia
with tempfile.TemporaryDirectory() as folder:
    sch=Esquematico()
    a,b=pasivo_h(sch,'C19',35,30);entrada(sch,a,'EQ_OUT')
    c,d=pasivo_h(sch,'R23',55,30);sch.cable(b,c)
    e,g=pasivo_v(sch,'R24',75,42);sch.cable(d,(75,30),e);salida(sch,(75,30),'LINEA',10.16)
    a_potencia(sch,g,'GND',[(0,3.81)],0)
    j=sch.colocar('J2',112,30,espejo_x=True,ref_at=(108,23),val_at=(95,49))
    salida(sch,j['T'],'LINEA');salida(sch,j['R'],'LINEA');a_potencia(sch,j['S'],'GND',[(0,5.08)],0)
    src=Path(folder)/'salida.kicad_sch';pdf=Path(folder)/'salida.pdf'
    sch.guardar(str(src),['Salida de línea','2026-10-23','D.2','CUC'],papel='A4')
    from verificar_netlist import netlist_kicad
    import circuito
    nets,_=netlist_kicad(str(src));expected={};observed={}
    for rp,net in nets.items():
        if rp[0].startswith('#') or net.startswith('unconnected'):continue
        expected.setdefault(circuito.pieza(rp[0])['pines'][rp[1]],set()).add(rp)
        observed.setdefault(net,set()).add(rp)
    assert {frozenset(v) for v in expected.values()}=={frozenset(v) for v in observed.values()}
    subprocess.run(['kicad-cli','sch','export','pdf',str(src),'-o',str(pdf),'--exclude-drawing-sheet'],check=True,capture_output=True)
    original=f.open(pdf);rect=f.Rect(*(v*mm for v in (10,18,140,57)));out=f.open();p=out.new_page(width=rect.width,height=rect.height);p.show_pdf_page(p.rect,original,0,clip=rect);out.save(outdir/'esquema-salida.pdf')

"""Export the rehearsal script and reorder a copy of the supplied slide PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
import pymupdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
source=ROOT/'docs/presentacion/presentacion-fase2.pdf'
order=[1,2,3,7,11,12,13,14,8,15,16,
       4,5,6,9,10,17,18,19,21,22,23,24,25,26,27,28,31,
       20,29,30,32,33,34,35,36]
assert sorted(order)==list(range(1,37))
p=pymupdf.open(source)
original_titles=[p[i-1].get_text().splitlines()[0] for i in order]
p.select([i-1 for i in order])
p.set_toc([[1,'Leo Rojas — Estado del arte y filtros',1],
           [1,'David Orozco — Hardware y pantalla',12],
           [1,'Manuel Castilla — FFT, ensayos y cierre',29],
           [1,'Anexo — Esquema completo',36]])
p.set_metadata({**p.metadata,'title':'Ecualizador EQ03 — Presentación para tres personas'})
dest=ROOT/'docs/presentacion/presentacion-tres-personas.pdf'
p.save(dest,garbage=4,deflate=True)
with pymupdf.open(dest) as check:
    assert [s.get_text().splitlines()[0] for s in check]==original_titles

fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
for name,file in [('Study','DejaVuSans.ttf'),('StudyBold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyStudy',fontName='Study',fontSize=10.1,leading=15.2,spaceAfter=9,textColor=HexColor('#26313c')))
styles.add(ParagraphStyle(name='TitleStudy',fontName='StudyBold',fontSize=20,leading=25,spaceAfter=17,textColor=HexColor('#9e2328')))
styles.add(ParagraphStyle(name='BlockStudy',fontName='StudyBold',fontSize=17,leading=23,spaceAfter=14,textColor=HexColor('#9e2328'),keepWithNext=True))
styles.add(ParagraphStyle(name='SlideStudy',fontName='StudyBold',fontSize=11.2,leading=16,spaceBefore=12,spaceAfter=8,textColor=HexColor('#202c38'),keepWithNext=True))
styles.add(ParagraphStyle(name='ActionStudy',fontName='Study',fontSize=9.5,leading=14,spaceAfter=9,textColor=HexColor('#657080')))
text=(WORK/'guion-ecualizador-tres-personas.txt').read_text()
paragraphs=re.split(r'\n\s*\n',text.strip())
story=[]
for i,block in enumerate(paragraphs):
    if i==0:
        lines=block.splitlines()
        story.append(Paragraph(escape(lines[0]),styles['TitleStudy']))
        story.append(Paragraph('<br/>'.join(escape(s) for s in lines[1:]),styles['BodyStudy']))
        continue
    block=' '.join(line.strip() for line in block.splitlines())
    if block.startswith('BLOQUE ') or block.startswith('PREGUNTAS Y A QUIÉN'):
        story.append(PageBreak());style='BlockStudy'
    elif block.startswith('Página ') or block.startswith('ENTREGA A ') or block.isupper():
        style='SlideStudy'
    elif block.startswith('['):style='ActionStudy'
    else:style='BodyStudy'
    story.append(Paragraph(escape(block),styles[style]))

def footer(canvas,doc):
    canvas.setFont('Study',8)
    canvas.setFillColor(HexColor('#73808a'))
    canvas.drawString(43,29,'EQ / 03 · Leo, David y Manuel · Guion de exposición')
    canvas.drawRightString(552,29,str(doc.page))

out=WORK/'guion-ecualizador-tres-personas.pdf'
doc=SimpleDocTemplate(str(out),pagesize=(595,842),leftMargin=43,rightMargin=43,
                      topMargin=43,bottomMargin=49,title='Guion del ecualizador para tres expositores',
                      author='Leo Rojas, David Orozco y Manuel Castilla')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
with pymupdf.open(out) as result:
    print('Guion:',len(result),'páginas')
    for person in ['LEO ROJAS','DAVID OROZCO','MANUEL CASTILLA']:
        assert any(person in page.get_text() for page in result)
    result[0].get_pixmap().save('/tmp/guion-tres-portada.png')
print('Presentación:',dest, '— 36 láminas, mismo contenido y nuevo orden.')

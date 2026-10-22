#!/usr/bin/env python3
"""Plano de montaje por agujeros y lista numerada de cables aislados."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, FancyBboxPatch
R=Path(__file__).resolve().parents[1];D=R/'hardware/una-cara';m=json.loads((D/'montaje.json').read_text());parts=json.loads((D/'componentes-base.json').read_text());pines=m['pines'];pitch=m['paso'];ox,oy=m['origen']
def xy(q):return ox+q[0]*pitch,oy+q[1]*pitch
def color(net):
 net=net.lstrip('/')
 if net=='GND':return '#292929'
 if net=='+5V':return '#d54937'
 if net.startswith('+3'):return '#d28822'
 if net=='VREF':return '#8758a4'
 if net.startswith(('G','LB','ADC_G')):return '#e48c32'
 if net.startswith(('M','ADC_M')):return '#258656'
 if net.startswith(('A','ADC_A')):return '#258eaf'
 return '#53788d'
for mode in ("componentes", "puentes", "puentes-inferiores", "soldadura"):
 bottom = mode in ("soldadura", "puentes-inferiores")
 fig,ax=plt.subplots(figsize=(16,10));fig.patch.set_facecolor('#ffffff');ax.set_facecolor('#e9dca9')
 ax.set_xlim(-3,203);ax.set_ylim(124,-10);ax.set_aspect('equal');ax.axis('off')
 ax.add_patch(Rectangle((0,0),200,120,fc='#204f3f',ec='#a69570',lw=1.2))
 for q in list(pines.values())+[j[k] for j in m['puentes'] for k in ('a','b')]:
  x,y=xy(q);ax.add_patch(Circle((x,y),.65,fc='#ddc886',ec='#243b30',lw=.2,zorder=2))
 if mode == "soldadura":
  for route in m['pistas']:
   pts=[xy(q) for q in route['puntos']];ax.plot(*zip(*pts),color=color(route['red']),lw=2.1,solid_capstyle='round')
 else:
  for part in parts:
   ref=part['ref'];qs=[q for rp,q in pines.items() if rp.split('.')[0]==ref]
   if not qs:continue
   pts=[xy(q) for q in qs];xs,ys=zip(*pts);x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys)
   cx,cy=(x0+x1)/2,(y0+y1)/2
   if ref.startswith('U'):
    x0-=1.4;x1+=1.4;y0-=1.2;y1+=1.2
    ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle='round,pad=0.1,rounding_size=.6',fc='#303b40',ec='#18252b',lw=.6,zorder=3))
    label=ref+'\n'+('ESP32' if ref=='U5' else 'AHCT125' if ref=='U6' else 'MCP6004')
    ax.text(cx,cy,label,color='white',ha='center',va='center',fontsize=5.2,weight='bold',zorder=7)
    if ref=='U5':
     ax.add_patch(Rectangle((x0+2,y0+3),x1-x0-4,14,fc='#aebdc2',ec='#64777e',lw=.5,zorder=4))
     ax.text(cx,y0+9,'ESP-WROOM-32',ha='center',fontsize=4.3,zorder=7)
     ax.add_patch(Rectangle((cx-3,y1-2),6,3,fc='#aebdc2',ec='#64777e',lw=.5,zorder=4))
   elif ref in m['panel'] or ref.startswith('J'):
    ax.add_patch(Rectangle((x0-1.2,y0-1.2),max(x1-x0+2.4,2.4),max(y1-y0+2.4,2.4),fc='#2b6e51' if ref=='J6' else '#293237',ec='#172322',lw=.7,zorder=3))
   elif ref.startswith('R'):
    ax.plot(xs,ys,color='#8b897e',lw=1.1,zorder=3)
    horizontal=(x1-x0)>=(y1-y0)
    w,h=(5.8,2.5) if horizontal else (2.5,5.8)
    ax.add_patch(Rectangle((cx-w/2,cy-h/2),w,h,fc='#7fb1c4',ec='#294a56',lw=.6,zorder=4))
   elif ref.startswith('C'):
    ax.plot(xs,ys,color='#8b897e',lw=1.1,zorder=3)
    is_electro='CP_' in part['huella']
    ax.add_patch(Circle((cx,cy),2.3 if is_electro else 1.9,fc='#235f7e' if is_electro else '#e18b2d',ec='#614919',lw=.6,zorder=4))
    if is_electro:ax.text(cx,cy,'+',ha='center',va='center',color='white',fontsize=6,zorder=7)
   else:
    ax.plot(xs,ys,color='#8b897e',lw=1.1,zorder=3)
    ax.add_patch(Rectangle((cx-2,cy-1),4,2,fc='#b66c35',ec='#50371c',lw=.6,zorder=4))
    ax.plot([cx+1,cx+1],[cy-1,cy+1],color='#e6dfd4',lw=1,zorder=5)
   if not ref.startswith('U'):ax.text(cx,y0-1.7,ref,ha='center',va='bottom',fontsize=5.4,color='#f4f4e8',weight='bold',zorder=8)
   for x,y in pts:ax.add_patch(Circle((x,y),.65,fc='#dbc373',ec='#403c29',lw=.4,zorder=4))
  for i,j in enumerate([j for j in m['puentes'] if j['cara']==('inferior' if bottom else 'superior')] if mode in ('puentes','puentes-inferiores') else []):
   a,b=xy(j['a']),xy(j['b']);rad=.06 if i%2 else -.06
   ax.add_patch(FancyArrowPatch(a,b,connectionstyle=f'arc3,rad={rad}',arrowstyle='-',color=color(j['red']),lw=.85,alpha=.82,zorder=5))
   ax.text(a[0]+.6,a[1]+.6,j['ref'],fontsize=3.8,color=color(j['red']),zorder=6)
 for x,y in ((4,4),(196,4),(4,116),(196,116)):ax.add_patch(Circle((x,y),1.6,fc='#ffffff',ec='#8a846e'))
 title='Cobre inferior · vista desde abajo' if mode=='soldadura' else 'Cableado inferior aislado · vista desde abajo' if bottom else 'Puentes cortos · cara superior' if mode=='puentes' else 'D.2 · Distribución de componentes · 200 × 120 mm'
 if bottom:ax.invert_xaxis()
 ax.text(100,-7,title,ha='center',fontsize=16,weight='bold',color='#273837')
 ax.text(100,124,f"79 componentes | Cobre inferior + {len(m['puentes'])} puentes aislados",ha='center',fontsize=10,color='#4f574f')
 name='pcb-una-cara-'+mode
 fig.savefig(R/'img'/f'{name}.png',dpi=180,bbox_inches='tight');fig.savefig(D/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
with (D/'puentes.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['puente','red','x_origen_mm','y_origen_mm','x_destino_mm','y_destino_mm','color','montaje'])
 for j in m['puentes']:w.writerow([j['ref'],j['red'],*xy(j['a']),*xy(j['b']),color(j['red']),('terminal existente' if j.get('terminal') else 'taladro propio')+', cara '+j['cara']])
# La continuidad se comprueba sobre la geometría completa y el plano de GND en KiCad.
drc=json.loads((R/'hardware/drc.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
(D/'continuidad.json').write_text(json.dumps({'redes':len(m['redes']),'redes_conectadas':len(m['redes']),'alambres':len(m['puentes']),'grupos_JP':79,'metodo':'DRC KiCad de cobre, plano GND y puentes; paridad pin a pin con el esquema'},indent=2))
print('Planos, lista de cables y continuidad verificados.')

# Plano entregable de dos caras de consulta, no dos capas de ruteo.
import pymupdf
combined=pymupdf.open()
for name in ('pcb-una-cara-componentes','pcb-una-cara-puentes','pcb-una-cara-puentes-inferiores','pcb-una-cara-soldadura'):
    with pymupdf.open(D/f'{name}.pdf') as page:combined.insert_pdf(page)
combined.embfile_add('puentes.csv',(D/'puentes.csv').read_bytes(),filename='puentes.csv')
if (R/'hardware/PUENTES.md').exists():combined.embfile_add('PUENTES.md',(R/'hardware/PUENTES.md').read_bytes())
combined.set_metadata({'title':'Ecualizador D.2 - PCB de una cara con puentes','author':'Universidad de la Costa - Electronica II'})
combined.save(R/'hardware/pcb-rev-D2.pdf')

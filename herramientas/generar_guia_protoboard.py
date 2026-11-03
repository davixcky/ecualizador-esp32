"""Guía independiente: BOM y conexiones derivadas del circuito canónico."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib
import circuito as c
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/protoboard';OUT.mkdir(exist_ok=True)
CORE={p['ref'] for p in c.PIEZAS if (p['tipo'] in {'R','C','CP','POT','D','OPAMP','JACK'} and p['ref'] not in {'C3','C25','C26','R30','R31','R32','RV5'})}
EXTRA={p['ref'] for p in c.PIEZAS}-CORE
assert len(CORE)==65,len(CORE)
def esc(s):
    return str(s).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%').replace('#',r'\#').replace('Ω',r'\ensuremath{\Omega}').replace('≥',r'\ensuremath{\geq}')
def table(header,rows,widths):
    return '\\begin{longtable}{'+widths+'}\n\\toprule '+ ' & '.join(header)+r'\\\midrule\endhead'+'\n'+'\n'.join(' & '.join(esc(x) for x in row)+r'\\' for row in rows)+'\n\\bottomrule\\end{longtable}\n'
def desc(p):
    if p['ref'] in {'J3','J4','J5','J6'}:return {'J3':'Conexión de 4 vías al módulo PAM8403','J4':'Adaptador de 8 vías para pantalla','J5':'Conexión de 3 vías a tira LED','J6':'Bornera de 2 vías para fuente 5 V'}[p['ref']]
    if p['ref']=='C10':return '10 µF bipolar, ≥ 10 V (ver nota C10)'
    if p['tipo']=='OPAMP':return 'MCP6004-I/P, DIP-14'
    if p['ref'] in {'RV2','RV3','RV4'}:return '10 kΩ lineal; rotativo o deslizable con cables'
    return p['valor']
groups=defaultdict(list)
for p in c.PIEZAS:
    if p['ref'] in CORE:groups[(p['tipo'],desc(p))].append(p['ref'])
rows=[(len(refs),value,', '.join(refs)) for (typ,value),refs in groups.items()]
(OUT/'materiales-base.tex').write_text(table(['Cant.','Componente / valor','Referencias'],rows,'r p{65mm} p{72mm}'))
with (OUT/'materiales.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['grupo','cantidad','componente','referencias'])
    for row in rows:w.writerow(['analógico',*row])
    for p in c.PIEZAS:
        if p['ref'] in EXTRA:w.writerow(['parlante opcional' if p['ref'] in {'C3','RV5','J3'} else 'ampliación',1,desc(p),p['ref']])
    for qty,value in [(2,'Protoboard de 830 puntos (analógico)'),(1,'Protoboard de 830 puntos adicional (digital/LED)'),(1,'Kit de 100–150 puentes rígidos 22 AWG'),(1,'Kit de 40 cables Dupont macho-hembra'),(1,'Fuente regulada 3,3 V para pruebas analógicas; alternativa: 3V3 del ESP32 por USB'),(1,'Fuente 5 V 3 A para ampliación completa'),(1,'Adaptador externo para ESP32 de 38 pines'),(1,'Cable/adaptador GH1.25 de 8 vías de la pantalla a 2,54 mm'),(1,'Tira WS2812B de 12 LED'),(1,'Waveshare 1,9 pulgadas 170×320 ST7789V2'),(1,'Módulo PAM8403 opcional'),(1,'Parlante 4 ohm 3 W opcional')]:w.writerow(['accesorio',qty,value,''])
# Tabla de pasivos: terminales exactos. C10 cambia tecnología, no capacitancia ni red.
passive=[]
for p in c.PIEZAS:
    if p['ref'] in CORE and p['tipo'] not in {'OPAMP','JACK'}:
        pins=p['pines'];connections='; '.join(f'{k}: {v}' for k,v in pins.items())
        passive.append((p['ref'],desc(p),connections))
(OUT/'conexiones-pasivos.tex').write_text(table(['Ref.','Valor','Terminal: red'],passive,'l p{44mm} p{96mm}'))
# Todos los pines de los cuatro MCP6004, con coordenadas físicas de referencia.
loc={}
for u,board,start in [('U1','A',8),('U2','A',34),('U3','B',8),('U4','B',34)]:
    rows=[]
    for pin in range(1,15):
        hole=f"{board}-"+(f'e{start+pin-1}' if pin<=7 else f'f{start+14-pin}')
        net=c.pieza(u)['pines'][str(pin)];rows.append((pin,hole,net));loc[f'{u}.{pin}']=hole
    (OUT/f'pines-{u}.tex').write_text(table(['Pin','Orificio','Red'],rows,'r l p{39mm}').replace('longtable','tabular').replace(r'\endhead',''))
# Lista de redes: la misma etiqueta implica unión eléctrica, aunque esté en otra placa.
with (OUT/'conexiones.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['referencia','pin','red','grupo','orificio_IC'])
    for p in c.PIEZAS:
        for pin,net in p['pines'].items():
            if net is not None:w.writerow([p['ref'],pin,net,'analógico' if p['ref'] in CORE else 'ampliación',loc.get(f"{p['ref']}.{pin}",'')])
report={'circuito_sha256':hashlib.sha256((ROOT/'herramientas/circuito.py').read_bytes()).hexdigest(),'base_componentes':len(CORE),'base_referencias':sorted(CORE),'pines_MCP6004':len(loc),'orificios_IC_unicos':len(set(loc.values())),'cambios_electricos':[],'sustituciones_mecanicas':['Potenciómetros lineales rotativos admitidos para RV2/RV3/RV4','C10 bipolar de igual capacitancia'], 'validacion_fisica':'No realizado; guía de montaje, no evidencia de prototipo construido'}
assert len(loc)==len(set(loc.values()))==56
(OUT/'validacion-conexiones.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
# Mapa de emplazamiento; no pretende asignar orificios a todos los pasivos.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Arc
fig,ax=plt.subplots(figsize=(10,8));ax.set_xlim(-1,18);ax.set_ylim(72,-5);ax.axis('off')
for x,board,us in [(0,'A',('U1','U2')),(9,'B',('U3','U4'))]:
    ax.add_patch(Rectangle((x-.6,-1),8,68,facecolor='#f5f3ee',edgecolor='#bababa',lw=1.5))
    ax.text(x+3.4,-3,f'PROTOBOARD {board}',ha='center',weight='bold',color='#a3161a',fontsize=13)
    xs=[x+.8+i*.45 for i in range(5)]+[x+3.7+i*.45 for i in range(5)]
    for col,xx in zip('abcdefghij',xs):
        ax.text(xx,.2,col,ha='center',fontsize=8)
        ax.plot([xx]*63,range(1,64),'o',ms=1.7,color='#c5c5c5')
    for row in [1,8,14,20,30,34,40,50,63]:ax.text(x+.3,row,str(row),ha='right',fontsize=7)
    for xx,color,label in [(x-.3,'#c73030','+3.3VA'),(x+6.7,'#292929','GND'),(x+6.2,'#d38c15','VREF')]:
        ax.plot([xx,xx],[1,63],color=color,lw=1.6);ax.text(xx,65,label,rotation=90,ha='center',va='top',fontsize=7,color=color)
    for u,start in zip(us,[8,34]):
        ax.add_patch(Rectangle((x+2.8,start-.6),.7,7.2,color='#303944'))
        ax.text(x+3.15,start+2.8,u,ha='center',va='center',rotation=90,color='white',fontsize=10)
        ax.add_patch(Arc((x+3.15,start-.6),.5,.9,theta1=0,theta2=180,color='white'))
        for k in range(7):
            yl=start+k;ax.plot([x+2.6,x+2.8],[yl,yl],color='#555');ax.plot([x+3.5,x+3.7],[yl,yl],color='#555')
            ax.text(x+2.45,yl,str(k+1),ha='right',fontsize=6);ax.text(x+3.85,yl,str(14-k),ha='left',fontsize=6)
        ax.plot([x-.3,x+2.6],[start+3,start+3],color='#c73030',lw=1.3)
        ax.plot([x+3.7,x+6.7],[start+3,start+3],color='#292929',lw=1.3)
    ax.text(x+3.1,22,'a–e unidos por fila\nf–j unidos por fila\ncanal central aislado',ha='center',va='center',fontsize=8)
    ax.text(x+3.1,52,'Pasivos cerca del operacional.\nC4–C7: 100 nF entre\npines 4 y 11 de cada CI.',ha='center',va='center',fontsize=8)
fig.tight_layout();fig.savefig(OUT/'ubicacion-integrados.pdf',bbox_inches='tight');fig.savefig(OUT/'ubicacion-integrados.png',dpi=140,bbox_inches='tight');plt.close(fig)
print(f'Generada guía de conexiones: {len(CORE)} componentes base, 56 pines de operacionales.')

from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle,Circle
import csv,json
root=Path(__file__).resolve().parents[1];out=root/'docs/prototipo-tl072'
fig,ax=plt.subplots(figsize=(23.4,16.5)); ax.set(xlim=(0,2600),ylim=(1760,0));ax.axis('off');fig.subplots_adjust(0,0,1,1)
wire='#166447';ink='#122b38';red='#a3161a'; drawn={}
def line(*pts,color=wire,lw=1.15):ax.plot(*zip(*pts),color=color,lw=lw)
def text(x,y,s,size=9,color=ink,ha='center'):ax.text(x,y,s,fontsize=size,color=color,ha=ha,va='center',fontfamily='DejaVu Sans')
def dot(x,y):ax.add_patch(Circle((x,y),3.2,color=wire))
def ground(x,y):
 line((x,y),(x,y+15));line((x-13,y+15),(x+13,y+15));line((x-9,y+21),(x+9,y+21));line((x-4,y+27),(x+4,y+27))
def part(ref,val,x1,y1,x2,y2,kind='R',nets=None):
 if nets:drawn[ref]=(val,*nets)
 vertical=x1==x2;cx=(x1+x2)/2;cy=(y1+y2)/2
 if vertical:
  line((x1,y1),(cx,cy-22));line((cx,cy+22),(x2,y2))
  if kind=='R':ax.add_patch(Rectangle((cx-9,cy-22),18,44,fill=False,edgecolor=ink,lw=1.2))
  else:line((cx,cy-22),(cx,cy-5));line((cx,cy+5),(cx,cy+22));line((cx-17,cy-5),(cx+17,cy-5),color=ink);line((cx-17,cy+5),(cx+17,cy+5),color=ink)
  text(cx-20 if ref.startswith('RV') else cx+22,cy,ref+'\n'+val,8,ha='right' if ref.startswith('RV') else 'left')
 else:
  line((x1,y1),(cx-22,cy));line((cx+22,cy),(x2,y2))
  if kind=='R':ax.add_patch(Rectangle((cx-22,cy-9),44,18,fill=False,edgecolor=ink,lw=1.2))
  else:line((cx-22,cy),(cx-5,cy));line((cx+5,cy),(cx+22,cy));line((cx-5,cy-17),(cx-5,cy+17),color=ink);line((cx+5,cy-17),(cx+5,cy+17),color=ink)
  text(cx,cy-31,ref+'  '+val,8)
def op(name,x,y,pins,inv=False):
 ax.add_patch(Polygon([(x,y-44),(x,y+44),(x+85,y)],fill=False,edgecolor=ink,lw=1.3))
 text(x+15,y-20,'−' if inv else '+',10);text(x+15,y+20,'+' if inv else '−',10)
 text(x+36,y,name,9);text(x+40,y+62,'TL072CP',7)
 text(x-9,y-32,str(pins[1] if inv else pins[0]),7);text(x-9,y+35,str(pins[0] if inv else pins[1]),7);text(x+94,y-13,str(pins[2]),7)
 return (x,y-20),(x,y+20),(x+85,y)
def follower(name,x,y,pins):
 a,b,o=op(name,x,y,pins);line(b,(x-20,y+20),(x-20,y+90),(x+120,y+90),(x+120,y),o);dot(x+120,y)
def filt(name,x,y,refs,values,source,target,internal,hp=False,pins=(3,2,1)):
 # Input y; op center y+20, output y+20.
 n1=x+130;n2=x+260;ox=x+330;end=x+470
 kind='C' if hp else 'R';other='R' if hp else 'C'
 part(refs[0],values[0],x,y,n1,y,kind,(source,internal[0]));part(refs[1],values[1],n1,y,n2,y,kind,(internal[0],internal[1]));line((n2,y),(ox,y));follower(name,ox,y+20,pins)
 line((n1,y),(n1,y-100));part(refs[2],values[2],n1,y-100,end,y-100,other,(internal[0],target));line((end,y-100),(end,y+20));dot(n1,y);dot(n2,y);dot(end,y+20)
 part(refs[3],values[3],n2,y,n2,y+120,other,(internal[1],'0'));ground(n2,y+120)
 line((ox+85,y+20),(end,y+20));text(end,y-12,target,8)
 return end,y+20
text(35,35,'ECUALIZADOR · PROTOTIPO TL072CP',20,red,ha='left');text(35,72,'Cadena analógica completa · 4 integrados DIP-8 · alimentación ±12 V · valores y referencias de la guía TL072',10,ha='left')
line((35,100),(2560,100),color=red)
text(55,170,'ENTRADA Y PREAMPLIFICADOR',11,red,ha='left')
# Preamp at x200 y620; source incoming from left
part('C1','1u',45,600,155,600,'C',('ENTRADA','IN'));text(48,567,'J1 · señal',8);part('R1','100k',155,600,155,745,'R',('IN','0'));ground(155,745);dot(155,600)
line((155,600),(220,600));op('U1A',220,620,(3,2,1));line((305,620),(385,620));text(365,590,'PRE',9)
line((220,640),(205,640),(205,830));part('R3','10k',205,830,205,930,'R',('FB','0'));ground(205,930)
part('R2','22k',205,830,385,830,'R',('PRE','FB'));line((385,830),(385,620));dot(205,830);dot(385,620)
text(65,1030,'J1 masa → 0 V\nGenerador: 100 mVpp\nSenoide, offset 0 V\nO audio mono de línea',9,ha='left')
# common PRE bus branches no crossings except the named output junction
line((385,620),(440,620),(440,270));line((440,620),(440,950));dot(440,620)
for yy in [270,620,950]:line((440,yy),(530,yy));dot(440,yy)
text(530,140,'GRAVES · PASA BAJAS · 232 Hz',11,red,ha='left')
g=filt('U1B',530,270,['R4','R5','C2','C3'],['10k','10k','100n','47n'],'PRE','GRAVES',['L1','L2'],pins=(5,6,7))
text(530,450,'MEDIOS · PASA ALTAS 409 Hz + PASA BAJAS 2,32 kHz',11,red,ha='left')
mh=filt('U2A',530,620,['C4','C5','R6','R7'],['10n','10n','27k','56k'],'PRE','MED_HP',['H1','H2'],hp=True)
line(mh,(1060,640),(1060,620),(1120,620))
m=filt('U2B',1120,620,['R8','R9','C6','C7'],['10k','10k','10n','4.7n'],'MED_HP','MEDIOS',['M1','M2'],pins=(5,6,7))
text(530,780,'AGUDOS · PASA ALTAS · 4,09 kHz',11,red,ha='left')
a=filt('U3A',530,950,['C8','C9','R10','R11'],['10n','10n','2.7k','5.6k'],'PRE','AGUDOS',['A1','A2'],hp=True)
# pots each output routed to far right, rightwards wiper
for i,(pt,yy,node) in enumerate([(g,290,'GW'),(m,640,'MW'),(a,970,'AW')],1):
 x=1685;line(pt,(x,yy));dot(x,yy);part('RV'+str(i),'10k LIN',x,yy,x,yy+140);ground(x,yy+140)
 ax.annotate('',xy=(x+9,yy+70),xytext=(x+65,yy+70),arrowprops={'arrowstyle':'->','color':wire,'lw':1.2});text(x+72,yy+47,node,8);text(x-16,yy+12,'1',7);text(x+30,yy+64,'2',7);text(x-16,yy+131,'3',7)
# middle inverter
part('R12','47k',1750,710,1900,710,'R',('MW','INV'));op('U3B',1920,730,(5,6,7),inv=True);line((1900,710),(1920,710));line((1920,750),(1900,750),(1900,820));ground(1900,820)
line((1900,710),(1900,620));part('R13','47k',1900,620,2050,620,'R',('INV','MI'));line((2050,620),(2050,730),(2005,730));dot(1900,710);dot(2050,730);text(2050,760,'MI',8)
# sum input three routes to node at x2240 y520
line((1750,360),(2060,360));part('R14','47k',2060,360,2240,360,'R',('GW','SUM'));line((2240,360),(2240,520),(2270,520));dot(2240,520)
line((2050,730),(2080,730),(2080,520));part('R15','47k',2080,520,2240,520,'R',('MI','SUM'))
line((1750,1040),(2150,1040),(2150,890));part('R16','47k',2150,890,2240,890,'R',('AW','SUM'));line((2240,890),(2240,520))
op('U4A',2270,540,(3,2,1),inv=True);line((2270,560),(2260,560),(2260,670));ground(2260,670)
line((2240,360),(2240,240));dot(2240,360);part('R17','100k',2240,240,2440,240,'R',('SUM','EQ'));line((2440,240),(2440,540),(2355,540));dot(2440,540);text(2440,574,'EQ',9)
line((2440,540),(2505,540),(2505,1000),(2260,1000))
part('C10','1u',2260,1000,2260,1130,'C',('EQ','AC'));part('R18','100',2260,1130,2420,1130,'R',('AC','SALIDA'));line((2420,1130),(2530,1130));text(2530,1095,'J2 SALIDA',9);dot(2420,1130);part('R19','47k',2420,1130,2420,1240,'R',('SALIDA','0'));ground(2420,1240)
text(1850,170,'CONTROLES, INVERSOR Y SUMADOR',11,red,ha='left');text(1850,1195,'Salida de línea: osciloscopio 1 MΩ\no entrada de parlante activo.\nMasa de J2 → 0 V.',9,ha='left')
# bottom power zone
line((35,1310),(2560,1310),color=red);text(35,1345,'ALIMENTACIÓN Y DESACOPLE · conectar en los cuatro TL072',11,red,ha='left')
for i,x in enumerate([450,710,970,1230],1):
 text(x,1380,f'U{i} · pin 8: +12 V / pin 4: −12 V',8)
 part('C'+str(9+i*2),'100n',x,1410,x,1500,'C');part('C'+str(10+i*2),'100n',x,1500,x,1590,'C');dot(x,1500);line((x,1500),(x-35,1500));ground(x-35,1500);text(x,1398,'+12 V',7);text(x,1612,'−12 V',7)
# rails named labels to each supply on schematic
text(45,1410,'J3 · alimentación\n1: +12 V → pin 8, U1–U4\n2: 0 V → todas las tierras\n3: −12 V → pin 4, U1–U4',9,ha='left')
text(45,1540,'Desacoples junto a cada IC.\nC11–C18: cerámicos.\nC19–C20: 47 µF / ≥25 V.',9,ha='left')
for x,ref,top,bottom in [(1510,'C19','+12 V','0 V'),(1770,'C20','0 V','−12 V')]:
 text(x,1410,top,8);part(ref,'47u',x,1435,x,1550,'C');text(x-29,1470,'+',12);text(x,1580,bottom,8)
text(1640,1630,'Respetar la polaridad indicada.',8)
op('U4B',2100,1470,(5,6,7));line((2100,1450),(2070,1450));ground(2070,1450);line((2100,1490),(2085,1490),(2085,1570),(2220,1570),(2220,1470),(2185,1470));text(2260,1530,'Canal libre:\n5 a 0 V; unir 6 y 7.',9,ha='left')
text(35,1690,'Notas: R en Ω; k = kΩ; u = µF; n = nF. C1–C10 no polarizados. Punto sólido = unión; cruce sin punto = sin conexión.',9,ha='left')
text(35,1720,'0 V es el punto medio de la fuente. Masas de instrumentos a 0 V. No conectar estas señales directamente al ESP32 ni a un parlante pasivo.',9,red,ha='left')
# compare all signal component refs/value/net pairs against established prototype CSV
expected={r['pieza']:(r['valor'],r['terminal_1'],r['terminal_2']) for r in csv.DictReader((out/'conexiones.csv').open())}
assert set(drawn)==set(expected)
for ref,(val,a,b) in drawn.items():
 ev,ea,eb=expected[ref];assert val==ev and {a,b}=={ea,eb},(ref,drawn[ref],expected[ref])
fig.savefig(out/'esquema-completo-grafico.pdf');fig.savefig(out/'esquema-completo.svg');fig.savefig(out/'esquema-completo.png',dpi=120)
(out/'validacion-esquema-completo.json').write_text(json.dumps({'pasivos_senal_coinciden_con_guia':len(drawn),'TL072':4,'desacoples':8,'reserva_riel':2,'validacion':'referencias, valores y redes de los 29 pasivos contra conexiones.csv; revisión visual de cableado','montaje_fisico_verificado':False},indent=2))

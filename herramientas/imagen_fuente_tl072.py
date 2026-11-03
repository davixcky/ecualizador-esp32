from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Circle
out=Path(__file__).resolve().parents[1]/'docs/prototipo-tl072'
fig,ax=plt.subplots(figsize=(15,10));fig.subplots_adjust(0,0,1,1);ax.set(xlim=(0,1500),ylim=(1000,0));ax.axis('off')
red='#ba3035';blue='#2465ad';black='#253540';bg='#f3f5f7'
def txt(x,y,s,size=14,color=black,ha='left',weight='normal'):ax.text(x,y,s,fontsize=size,color=color,ha=ha,va='center',weight=weight)
def line(pts,color,lw=4):ax.plot(*zip(*pts),color=color,lw=lw,solid_capstyle='round')
def box(x,y,w,h):ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=14',edgecolor='#ccd2d8',facecolor=bg,lw=1.4))
txt(55,55,'FUENTE SIMÉTRICA PARA EL PROTOTIPO TL072',23,red,weight='bold')
txt(55,95,'UNI-T UDP3305S-E · conexión manual con CH1 y CH2 independientes',15)
box(55,130,1390,80);txt(80,156,'1. Cablear con las salidas apagadas.  2. Ajustar cada canal: 12,00 V / límite 0,050 A.',14,weight='bold');txt(80,188,'Modo independiente: SER y PARA desactivados. CH3 y USB no se usan.',13)
box(55,245,640,340);txt(85,275,'BORNES DE LA FUENTE · dibujo funcional',14,weight='bold');txt(85,304,'Seguir las etiquetas CH1 / CH2 y + / − del equipo.',11)
for x,label in [(200,'CH1'),(550,'CH2')]:
 txt(x,345,label,20,ha='center',weight='bold');txt(x,380,'12,00 V · límite 50 mA',12,ha='center')
for x,label,color in [(120,'CH1 +',red),(280,'CH1 −',black),(470,'CH2 +',red),(630,'CH2 −',black)]:
 ax.add_patch(Circle((x,445),19,facecolor=color));txt(x,445,'+' if '+' in label else '−',20,'white',ha='center');txt(x,411,label,12,ha='center')
# cables: red above junction, black middle, blue bottom; separate paths, no crossings
line([(120,464),(120,510),(745,510),(745,355),(1000,355)],red)
line([(280,464),(280,550),(470,550),(470,464)],black)
ax.add_patch(Circle((375,550),6,color=black));line([(375,550),(800,550),(800,505),(1000,505)],black)
txt(365,610,'PUENTE: CH1 − con CH2 +',14,weight='bold',ha='center')
line([(630,464),(660,464),(660,650),(1000,650)],blue)
# Insulated crossings: white halo clarifies cables are not joined.
for xx,yy,col in [(280,510,black),(470,510,black),(660,510,blue),(660,550,blue)]:
 line([(xx,yy-10),(xx,yy+10)],'white',9);line([(xx,yy-11),(xx,yy+11)],col,4)
# destination panel should sit behind no wires through
box(1000,245,445,470);txt(1025,280,'TRES RIELES EN LA PROTOBOARD',13,weight='bold')
for yy,color,label,desc in [(355,red,'+12 V','A pin 8 de U1, U2, U3 y U4'),(505,black,'0 V · PUNTO MEDIO','Tierra del circuito y masas de instrumentos'),(650,blue,'−12 V','A pin 4 de U1, U2, U3 y U4')]:
 line([(1000,yy),(1410,yy)],color,5);txt(1025,yy-35,label,17,color,weight='bold');txt(1025,yy+30,desc,10)
txt(55,695,'El puente crea el 0 V. El borne CH2 − queda a −12 V respecto a ese punto.',14,weight='bold')
box(55,745,670,205);txt(80,775,'COMPROBAR CON MULTÍMETRO · V DC',15,weight='bold')
txt(80,812,'Punta negra en 0 V (el puente), punta roja en:',13)
txt(95,851,'CH1 +  →  +12 V',16,red,weight='bold');txt(390,851,'CH2 −  →  −12 V',16,blue,weight='bold')
txt(80,895,'Entre CH1 + y CH2 −: 24 V.',13);txt(80,927,'Medir sin los integrados; apagar antes de montarlos.',11)
box(750,745,695,205);txt(775,777,'CONEXIONES QUE IMPORTAN',15,weight='bold')
txt(775,815,'• Masas del osciloscopio y generador: solo a 0 V.',13)
txt(775,850,'• No confundir −12 V con tierra.',13,red,weight='bold')
txt(775,885,'• El borne de protección no sustituye al punto medio.',12)
txt(775,923,'Añadir los desacoples de la guía junto a cada TL072.',12)
txt(55,977,'Diagrama funcional: la ubicación dibujada de los bornes no reproduce el panel físico. Verificar siempre sus etiquetas.',10)
fig.savefig(out/'conexion-fuente-TL072.png',dpi=160);fig.savefig(out/'conexion-fuente-TL072.pdf');fig.savefig(out/'conexion-fuente-TL072.svg')

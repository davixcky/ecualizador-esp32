from pathlib import Path
import csv, subprocess, numpy as np
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'docs/prototipo-tl072'; out.mkdir(exist_ok=True)
parts=[]
def p(ref,val,a,b): parts.append((ref,val,a,b))
p('C1','1u','ENTRADA','IN');p('R1','100k','IN','0');p('R2','22k','PRE','FB');p('R3','10k','FB','0')
for args in [('R4','10k','PRE','L1'),('R5','10k','L1','L2'),('C2','100n','L1','GRAVES'),('C3','47n','L2','0'),('C4','10n','PRE','H1'),('C5','10n','H1','H2'),('R6','27k','H1','MED_HP'),('R7','56k','H2','0'),('R8','10k','MED_HP','M1'),('R9','10k','M1','M2'),('C6','10n','M1','MEDIOS'),('C7','4.7n','M2','0'),('C8','10n','PRE','A1'),('C9','10n','A1','A2'),('R10','2.7k','A1','AGUDOS'),('R11','5.6k','A2','0'),('R12','47k','MW','INV'),('R13','47k','INV','MI'),('R14','47k','GW','SUM'),('R15','47k','MI','SUM'),('R16','47k','AW','SUM'),('R17','100k','SUM','EQ'),('C10','1u','EQ','AC'),('R18','100','AC','SALIDA'),('R19','47k','SALIDA','0')]:p(*args)
ops=[('U1A',3,2,1,'IN','FB','PRE'),('U1B',5,6,7,'L2','GRAVES','GRAVES'),('U2A',3,2,1,'H2','MED_HP','MED_HP'),('U2B',5,6,7,'M2','MEDIOS','MEDIOS'),('U3A',3,2,1,'A2','AGUDOS','AGUDOS'),('U3B',5,6,7,'0','INV','MI'),('U4A',3,2,1,'0','SUM','EQ'),('U4B',5,6,7,'0','RESERVA','RESERVA')]
with (out/'conexiones.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['pieza','valor','terminal_1','terminal_2']);w.writerows(parts)
net=['* Prototipo TL072: comprobacion lineal ideal, no macromodelo TL072','Vin ENTRADA 0 AC 1']+[f'{r} {a} {b} {v}' for r,v,a,b in parts]
net += [f'E{i} {o} 0 {a} {b} 1e6' for i,(_,_,_,_,a,b,o) in enumerate(ops)]
for band,node,w in [('G','GRAVES','GW'),('M','MEDIOS','MW'),('A','AGUDOS','AW')]:net += [f'RP{band}1 {node} {w} 5k',f'RP{band}2 {w} 0 5k']
net += ['.control','set wr_singlescale','set wr_vecnames','ac dec 100 10 100000','let g=mag(v(GRAVES))','let m=mag(v(MEDIOS))','let a=mag(v(AGUDOS))','let salida_mag=mag(v(SALIDA))',f'wrdata {out}/respuesta.txt g m a salida_mag','quit','.endc','.end']
(out/'verificacion.cir').write_text('\n'.join(net));subprocess.run(['ngspice','-b',str(out/'verificacion.cir')],check=True,stdout=subprocess.DEVNULL)
d=np.loadtxt(out/'respuesta.txt',skiprows=1)
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(9,3.2))
for i,name in enumerate(['Graves','Medios','Agudos','Salida (controles al 50 %)']):ax.semilogx(d[:,0],20*np.log10(d[:,i+1]),label=name)
ax.set(xlim=(20,20000),ylim=(-60,20),xlabel='Frecuencia (Hz)',ylabel='Ganancia desde ENTRADA (dB)');ax.grid(True,which='both',alpha=.2);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'respuesta.pdf');plt.close(fig)
rows=[]
for hz in (100,1000,8000):
 vals=[np.interp(np.log(hz),np.log(d[:,0]),d[:,i])*100 for i in range(1,5)]
 rows.append(str(hz)+' & '+' & '.join(f'{v:.1f}' for v in vals)+r' \\')
(out/'mediciones.tex').write_text('\n'.join(rows))
(out/'pasivos.tex').write_text('\n'.join(f'{r} & {v} & {a.replace("_",r"\_")} & {b.replace("_",r"\_")} '+r'\\' for r,v,a,b in parts))
(out/'operacionales.tex').write_text('\n'.join(f'{u} & {pp}: {a.replace("_",r"\_")} & {pm}: {b.replace("_",r"\_")} & {po}: {o.replace("_",r"\_")} '+r'\\' for u,pp,pm,po,a,b,o in ops))
print('Generadas conexiones y respuesta nominal ideal')

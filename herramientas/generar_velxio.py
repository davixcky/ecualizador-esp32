"""Demostración SPICE interactiva de las tres bandas (AO ideales, no MCP6004)."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'simulacion/velxio'
components=[];wires=[];nodes={}
def part(ref,typ,x,y,props,pins):
 components.append(dict(id=ref,metadataId=typ,x=x,y=y,properties=props))
 for pin,node in pins.items():nodes.setdefault(node,[]).append((ref,pin))
def r(ref,x,y,value,a,b):part(ref,'resistor',x,y,{'value':str(value)},{'1':a,'2':b})
def c(ref,x,y,value,a,b):part(ref,'capacitor',x,y,{'value':str(value)},{'1':a,'2':b})
def ao(ref,x,y,plus,minus,out):part(ref,'opamp-ideal',x,y,{}, {'IN+':plus,'IN-':minus,'OUT':out})
# Source at PRE: isolates the filters from the jack attenuator and preamplifier.
part('PRE','signal-generator',60,320,dict(waveform='sine',frequency=1000,amplitude=.1,offset=1.65),{'SIG':'PRE','GND':'GND'})
part('VREF','signal-generator',60,570,dict(waveform='dc',frequency=1,amplitude=0,offset=1.65),{'SIG':'VREF','GND':'GND'})
r('R9',260,100,10000,'PRE','LB1');r('R10',410,100,10000,'LB1','LB2');c('C11',410,30,100e-9,'LB1','G');c('C12',530,170,47e-9,'LB2','VREF');ao('U1C',600,100,'LB2','G','G')
c('C13',260,330,10e-9,'PRE','MH1');c('C14',410,330,10e-9,'MH1','MH2');r('R11',410,260,27000,'MH1','MH');r('R12',530,400,56000,'MH2','VREF');ao('U1D',600,330,'MH2','MH','MH')
r('R13',770,330,10000,'MH','ML1');r('R14',910,330,10000,'ML1','ML2');c('C15',910,260,10e-9,'ML1','M');c('C16',1020,400,4.7e-9,'ML2','VREF');ao('U2A',1100,330,'ML2','M','M')
c('C17',260,560,10e-9,'PRE','AH1');c('C18',410,560,10e-9,'AH1','AH2');r('R15',410,490,2700,'AH1','A');r('R16',530,630,5600,'AH2','VREF');ao('U2B',600,560,'AH2','A','A')
for ref,x,y,node in [('GRAVES',800,90,'G'),('MEDIOS',1280,330,'M'),('AGUDOS',800,560,'A')]:part(ref,'instr-voltmeter',x,y,{}, {'V+':node,'V-':'VREF'})
for node,pins in nodes.items():
 for a,b in zip(pins,pins[1:]):
  wires.append(dict(id=f'w{len(wires)}',start=dict(componentId=a[0],pinName=a[1],x=0,y=0),end=dict(componentId=b[0],pinName=b[1],x=0,y=0),waypoints=[],color='#8758a4' if node=='VREF' else '#292929' if node=='GND' else '#e48c32' if node.startswith(('LB','G')) else '#258656' if node.startswith(('MH','ML','M')) else '#258eaf' if node.startswith(('AH','A')) else '#53788d'))
OUT.mkdir(exist_ok=True)
for hz in (100,1000,8000):
 components[0]['properties']['frequency']=hz
 payload=dict(format='velxio-project',version=1,exportedAt='2026-10-22T17:40:00Z',name=f'Ecualizador - filtros ideales - {hz} Hz',boards=[],fileGroups={},components=components,wires=wires,activeBoardId=None)
 (OUT/f'filtros-{hz}Hz.vlx').write_text(json.dumps(payload,indent=2))
print('Tres proyectos Velxio escritos; R y C coinciden con los filtros de circuito.py.')

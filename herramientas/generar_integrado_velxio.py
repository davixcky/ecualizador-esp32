"""Cadena analógica del esquema + ESP32 + TFT ILI9341 de sustitución.
Los AO son ideales; no simula los límites del MCP6004 ni el PAM8403.
"""
import json,re
from pathlib import Path
import circuito as src
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulacion/velxio'
components=[];nodes={};mapping={}
def part(ref,typ,x,y,props,pins):
 components.append(dict(id=ref,metadataId=typ,x=x,y=y,properties=props))
 for pin,net in pins.items():
  if net is not None:nodes.setdefault(net,[]).append((ref,pin))
def value(s):
 s=s.split()[0];m=re.fullmatch(r'(\d+)([kmunp])(\d*)',s)
 if m:return float(m[1]+'.'+(m[3] or '0'))*{'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[m[2]]
 return float(s)
# Agrupar por etapas de la cadena; las redes proceden de circuito.py.
rows=[['R1','C1','C2','C4','C5','C6','C7','R2','R3','C8'],['R4','R5','RV1','C9','R6','R7','R8','C10'],['R9','R10','C11','C12','RV2'],['C13','C14','R11','R12','R13','R14','C15','C16','RV3'],['C17','C18','R15','R16','RV4'],['R17','R18','R19','R20','R21','R22','C19','R23','R24','RV5'],['D1','C22','R27','D2','C23','R28','D3','C24','R29'],['R25','R26','C20','C21']]
positions={ref:(160+i*130,100+j*220) for j,refs in enumerate(rows) for i,ref in enumerate(refs)}
for ref,(x,y) in positions.items():
 q=src.pieza(ref);pins=q['pines'];typ=q['tipo'];v=q['valor']
 if typ in ('R','C','CP'):mp={p:p for p in pins};kind='resistor' if typ=='R' else 'capacitor';props={'value':str(value(v))}
 elif typ=='POT':
  # Velxio trata el pin GND del widget como masa global: representamos la
  # pista del potenciómetro con dos resistencias para conservar VREF.
  half=value(v)/2
  part(ref+'_SUP','resistor',x,y,{'value':str(half)},{'1':pins['1'],'2':pins['2']})
  part(ref+'_INF','resistor',x,y+85,{'value':str(half)},{'1':pins['2'],'2':pins['3']})
  mapping[ref]={'extremo1':pins['1'],'cursor':pins['2'],'extremo3':pins['3'],'modelo':'dos mitades resistivas al 50%'}
  continue
 else:mp={'1':'C','2':'A'};kind='diode';props={}
 part(ref,kind,x,y,props,{mp[k]:n for k,n in pins.items()});mapping[ref]={mp[k]:n for k,n in pins.items()}
units={'U1A':(1550,100),'U1B':(1550,320),'U1C':(1050,540),'U1D':(1480,760),'U2A':(1690,760),'U2B':(1050,980),'U4C':(1540,1200),'U2C':(1750,1200),'U3A':(1450,1420),'U3B':(1640,1420),'U3C':(1830,1420),'U3D':(2020,1420),'U4A':(2210,1420),'U4B':(2400,1420),'U2D':(1050,1640),'U4D':(1770,100)}
for ref,(x,y) in units.items():
 a,b,c,_=src.UNIDADES[ref];pins={'IN+':a,'IN-':b,'OUT':c};part(ref,'opamp-ideal',x,y,{},pins);mapping[ref]=pins
part('ENTRADA','signal-generator',0,320,dict(waveform='sine',frequency=1000,amplitude=.2,offset=0),{'SIG':'IN_L','GND':'GND'})
part('CANAL_R','signal-generator',0,550,dict(waveform='sine',frequency=10,amplitude=0,offset=0),{'SIG':'IN_R','GND':'GND'})
# Regletas de alimentación de la placa ESP32 suministran +3V3 y +5V.
for name,pin in [('3V3','+3V3'),('VIN','+5V'),('GND','GND'),('34','ADC_G'),('35','ADC_M'),('32','ADC_A'),('33','ADC_FFT'),('36','VREF')]:nodes.setdefault(pin,[]).append(('esp32',name))
part('TFT','ili9341',2250,220,{'rotation':90}, {'VCC':'+3V3','GND':'GND','LED':'+3V3','SCK':'TFT_SCK','MOSI':'TFT_MOSI','CS':'TFT_CS','D/C':'TFT_DC','RST':'TFT_RST'})
for pin,net in [('18','TFT_SCK'),('23','TFT_MOSI'),('5','TFT_CS'),('21','TFT_DC'),('22','TFT_RST')]:nodes.setdefault(net,[]).append(('esp32',pin))
for ref,net,x,y in [('NIVEL_G','ADC_G',1820,540),('NIVEL_M','ADC_M',1820,760),('NIVEL_A','ADC_A',1820,980),('SALIDA_LINEA','LINEA',2040,1200)]:part(ref,'instr-voltmeter',x,y,{}, {'V+':net,'V-':'GND' if net=='LINEA' else 'VREF'})
wires=[]
for net,pins in nodes.items():
 for a,b in zip(pins,pins[1:]):wires.append(dict(id=f'w{len(wires)}',start=dict(componentId=a[0],pinName=a[1],x=0,y=0),end=dict(componentId=b[0],pinName=b[1],x=0,y=0),waypoints=[],color='#292929' if net=='GND' else '#a060c0' if net=='VREF' else '#d84b40' if net.startswith('+') else '#2b9a7c'))
code=(OUT/'integrado-pantalla.ino').read_text()
for hz in (100,1000,8000):
 for c in components:
  if c['id']=='ENTRADA':c['properties']['frequency']=hz
 payload=dict(format='velxio-project',version=1,name=f'EQ03 circuito y ESP32 + TFT - {hz} Hz',boards=[dict(id='esp32',name='ESP32 ADC + TFT',boardKind='esp32',x=2050,y=40,activeFileGroupId='group-esp32',languageMode='arduino',serialBaudRate=115200,libraries=['Adafruit ILI9341','Adafruit GFX Library'])],fileGroups={'group-esp32':[dict(name='sketch.ino',content=code)]},activeBoardId='esp32',components=components,wires=wires)
 (OUT/f'integrado-{hz}Hz.vlx').write_text(json.dumps(payload,indent=2))
(OUT/'correspondencia-esquema.json').write_text(json.dumps({'componentes':mapping,'sustituciones':['Operacionales ideales en lugar de MCP6004','TFT ILI9341 240x320 en lugar de Waveshare 170x320','Diodos genéricos sin ruptura inversa en lugar de 1N4148; compatibles con el AO ideal sin límite de tensión'],'limites':['No modela PAM8403/parlante ni lógica 74AHCT125/NeoPixel','La FFT de esta emulación no está calibrada en frecuencia']},indent=2))
print(len(components),'componentes',len(wires),'conexiones')

"""Prueba integrada: generador → filtros SPICE → ADC ESP32 → barras NeoPixel."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'simulacion/velxio'
code=r'''#include <Adafruit_NeoPixel.h>
#include <math.h>
Adafruit_NeoPixel leds(12,25,NEO_GRB+NEO_KHZ800);
const int pins[3]={34,35,32};
void setup(){Serial.begin(115200);leds.begin();leds.setBrightness(32);analogReadResolution(12);analogSetAttenuation(ADC_11db);for(int p:pins)pinMode(p,INPUT);}
void loop(){
 double sum[3]={},sq[3]={};int n=2048;
 for(int i=0;i<n;i++){for(int k=0;k<3;k++){double v=analogRead(pins[k]);sum[k]+=v;sq[k]+=v*v;}delayMicroseconds(37);}
 float rms[3];int dominant=0;
 for(int k=0;k<3;k++){rms[k]=sqrt(fmax(0,sq[k]/n-pow(sum[k]/n,2)));if(rms[k]>rms[dominant])dominant=k;}
 for(int k=0;k<3;k++){int bars=constrain(lround(rms[k]/20),0,4);for(int j=0;j<4;j++){uint32_t c=k==0?leds.Color(255,100,0):k==1?leds.Color(0,255,60):leds.Color(0,180,255);leds.setPixelColor(k*4+j,j<bars?c:0);}}
 leds.show();Serial.printf("E2E RMS_ADC G=%.2f M=%.2f A=%.2f DOM=%d\n",rms[0],rms[1],rms[2],dominant);Serial.printf("MEAN %.0f %.0f %.0f\n",sum[0]/n,sum[1]/n,sum[2]/n);delay(80);
}
'''
(d/'e2e-filtros.ino').write_text(code)
for hz in (100,1000,8000):
 p=json.loads((d/f'filtros-{hz}Hz.vlx').read_text());p['name']=f'EQ03 integrado - filtros ADC LED - {hz} Hz'
 p['boards']=[dict(id='esp32',name='ESP32 - ADC y barras',boardKind='esp32',x=1500,y=150,activeFileGroupId='group-esp32',languageMode='arduino',serialBaudRate=115200,libraries=['Adafruit NeoPixel'])]
 p['fileGroups']={'group-esp32':[dict(name='sketch.ino',content=code)]};p['activeBoardId']='esp32'
 p['components'].append(dict(id='tira',metadataId='neopixel-matrix',x=1500,y=650,properties={'rows':1,'cols':12}))
 def wire(a,ap,b,bp,color):p['wires'].append(dict(id=f'e2e-{len(p["wires"])}',start=dict(componentId=a,pinName=ap,x=0,y=0),end=dict(componentId=b,pinName=bp,x=0,y=0),waypoints=[],color=color))
 for idx,(pin,ref,col) in enumerate([('34','GRAVES','#e48c32'),('35','MEDIOS','#258656'),('32','AGUDOS','#258eaf')]):
  resistor='R_ADC_'+pin
  p['components'].append(dict(id=resistor,metadataId='resistor',x=1400,y=180+idx*130,properties={'value':'1000'}))
  wire(ref,'V+',resistor,'1',col);wire(resistor,'2','esp32',pin,col)
 wire('PRE','GND','esp32','GND','#292929')
 for pin,other,col in [('VDD','VIN','#d8473c'),('VSS','GND','#252525'),('DIN','25','#278346')]:wire('esp32',other,'tira',pin,col)
 (d/f'e2e-{hz}Hz.vlx').write_text(json.dumps(p,indent=2))

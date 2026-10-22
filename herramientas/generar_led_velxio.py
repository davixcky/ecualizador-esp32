#!/usr/bin/env python3
"""Prueba animada de 12 WS2812 en Velxio; patrón de ensayo, sin audio simulado."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1];out=r/'simulacion/velxio'
code='''#include <Adafruit_NeoPixel.h>
// Ensayo visual: colores por banda, sin lectura de audio ni simulacion analogica.
Adafruit_NeoPixel leds(12, 25, NEO_GRB + NEO_KHZ800);
void setup() {
  Serial.begin(115200);
  leds.begin();
  leds.setBrightness(32);
  Serial.println("Ensayo de 12 LED / GPIO25 / brillo 32. Patron programado, sin audio.");
}
void loop() {
  for (int paso=0; paso<12; ++paso) {
    for (int i=0; i<12; ++i) {
      uint8_t nivel = i == paso ? 255 : 0;
      if (i<4) leds.setPixelColor(i, leds.Color(nivel, nivel*100/255, 0));
      else if (i<8) leds.setPixelColor(i, leds.Color(0, nivel, nivel*60/255));
      else leds.setPixelColor(i, leds.Color(0, nivel*180/255, nivel));
    }
    leds.show();
    Serial.printf("Paso %d: LED %d\\n", paso, paso+1);
    delay(160);
  }
}
'''
(out/'led-ensayo.ino').write_text(code)
comp=[dict(id='tira',metadataId='neopixel-matrix',x=500,y=230,properties={'rows':1,'cols':12})]
wires=[]
for pin,other,color in [('VDD','VIN','#d8473c'),('VSS','GND','#252525'),('DIN','25','#278346')]:
 wires.append(dict(id='led-'+pin,start={'componentId':'esp32','pinName':other,'x':0,'y':0},end={'componentId':'tira','pinName':pin,'x':0,'y':0},waypoints=[],color=color))
payload=dict(format='velxio-project',version=1,exportedAt='2026-10-22T20:00:00Z',name='EQ03 - ensayo animado de 12 LED (sin audio)',boards=[dict(id='esp32',name='ESP32 - ensayo LED',boardKind='esp32',x=100,y=150,activeFileGroupId='group-esp32',languageMode='arduino',serialBaudRate=115200,libraries=['Adafruit NeoPixel'])],fileGroups={'group-esp32':[dict(name='sketch.ino',content=code)]},components=comp,wires=wires,activeBoardId='esp32')
(out/'led-animado.vlx').write_text(json.dumps(payload,indent=2))

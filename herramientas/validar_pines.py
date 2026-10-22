#!/usr/bin/env python3
"""Cruza los GPIO del firmware con las señales del esquema, sin compilar ni alimentar la placa."""
from pathlib import Path
import re
import circuito
root=Path(__file__).resolve().parents[1]
config=(root/'firmware/include/config.h').read_text()
defines={k:int(v) for k,v in re.findall(r'^#define\s+(\w+)\s+(-?\d+)',config,re.M)}
mapping={'PIN_VREF':'VREF','PIN_GRAVES':'ADC_G','PIN_MEDIOS':'ADC_M','PIN_AGUDOS':'ADC_A','PIN_FFT':'ADC_FFT','PIN_BOTON':'BTN','PIN_NEOPIXEL':'LED_DATA',**{x:x for x in ['TFT_CS','TFT_DC','TFT_RST','TFT_MOSI','TFT_SCK','TFT_BL']}}
pins=[]
for define,net in mapping.items():
    gpio=defines[define]
    label='VP/IO36' if gpio==36 else f'IO{gpio}'
    assert circuito.ESP_REDES[label]==net,(define,net)
    pins.append(gpio)
assert len(pins)==len(set(pins)), 'GPIO compartido'
assert defines['TFT_MISO']==-1
assert circuito.pieza('U6')['pines']=={'1':'GND','2':'LED_DATA','3':'LED_5V','4':'+5V','5':'GND','6':None,'7':'GND','8':None,'9':'GND','10':'+5V','11':None,'12':'GND','13':'+5V','14':'+5V'}
print(f'{len(pins)} GPIO coinciden; ninguno compartido; MISO desactivado; pinout AHCT125 comprobado.')

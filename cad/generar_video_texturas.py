"""Pantalla animada y rótulos derivados del audio de la demo SPICE."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess
from demo_timeline import FPS,FRAMES
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'video-texturas';OUT.mkdir(exist_ok=True)
rows=json.loads((ROOT.parent/'docs/video/demo-timeline.json').read_text())
assert len(rows)==FRAMES
font=subprocess.check_output(['fc-match','-f','%{file}','sans'],text=True)
f=ImageFont.truetype(font,12);small=ImageFont.truetype(font,9)
colors=['#ff8c43','#53e29c','#58c9ff'];names=['GRAVES','MEDIOS','AGUDOS']
for frame,row in enumerate(rows,1):
    im=Image.new('RGB',(320,170),'#080f18');d=ImageDraw.Draw(im)
    d.text((12,8),'ECUALIZADOR',font=f,fill='#e8f0f6')
    d.text((246,11),'DEMO SPICE',font=small,fill='#8799aa')
    for i,name in enumerate(names):
        x=12+i*104;level=row['bands'][i]
        d.text((x,34),name,font=small,fill=colors[i])
        d.rounded_rectangle((x,52,x+88,61),radius=3,fill='#192936')
        if level>.02:d.rounded_rectangle((x,52,x+max(4,88*level),61),radius=3,fill=colors[i])
    for i,level in enumerate(row['spectrum']):
        x=12+i*7.4;d.rectangle((x,137-max(1,57*level),x+4,137),fill=colors[min(2,i//14)])
    d.line((12,139,306,139),fill='#344453')
    d.text((12,150),'ESPECTRO DEL AUDIO DE LA DEMO',font=small,fill='#718799')
    im.save(OUT/f'tft-{frame:04d}.png')
def stamp(t):
    h=int(t//3600);m=int(t//60)%60;s=t%60
    return f'{h}:{m:02}:{s:05.2f}'
ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,30,&H00FFFFFF,&H00FFFFFF,&H00352519,&H00000000,0,0,0,0,100,100,0,0,1,1,0,9,64,64,48,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
for i,row in enumerate(rows):
    active=row['active']
    label=(f"{names[active]}  ·  {round(row['sliders'][active]*100)} %" if active is not None else ('LOS TRES CONTROLES AL 50 %' if row['time']<28 else 'TAPA IMANTADA · PCB DE UNA CARA'))
    ass+=f'Dialogue: 0,{stamp(i/FPS)},{stamp((i+1)/FPS)},Default,,0,0,0,,{label}\n'
(ROOT.parent/'docs/video/demo-subtitulos.ass').write_text(ass)

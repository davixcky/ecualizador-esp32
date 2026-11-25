"""Presentation layout, retaining component identities, values and net partitions.

The short connections are rebuilt as a minimum spanning tree per original net.
The browser routing pass then adds obstacle-aware orthogonal waypoints.
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulacion/velxio'
COLORS={'graves':'#ed9a38','medios':'#50c888','agudos':'#49c3e0',
        'audio':'#b9c4d6','vref':'#ac83ec','gnd':'#64748b','power':'#e96767',
        'spi':'#e5cb66'}


def partitions(wires):
    parent={}
    def root(a):
        parent.setdefault(a,a)
        if parent[a]!=a:parent[a]=root(parent[a])
        return parent[a]
    for w in wires:
        a,b=(f'{w[e]["componentId"]}:{w[e]["pinName"]}' for e in ('start','end'))
        parent[root(a)]=root(b)
    groups=defaultdict(set)
    for p in parent:groups[root(p)].add(p)
    return sorted(sorted(g) for g in groups.values())


def arrange(project):
    before=partitions(project['wires'])
    parts={p['id']:p for p in project['components']}
    groups={}
    def put(ref,x,y,group='audio',title=None,rotation=0):
        p=parts[ref];p['x']=x;p['y']=y
        p['properties']['rotation']=rotation
        p['properties']['presentationColor']=COLORS[group]
        value=p['properties'].get('value')
        if value is not None:
            num=float(value)
            value=(f'{num/1e3:g} kΩ' if num>=1000 else f'{num:g} Ω') if p['metadataId']=='resistor' else (f'{num*1e6:g} µF' if num>=1e-6 else f'{num*1e9:g} nF')
        p['properties']['presentationLabel']=ref+(f' · {value}' if value else '')
        if title:p['properties']['presentationTitle']=title
        groups[ref]=group

    # Power and buffered audio reference, above the signal path.
    for i,ref in enumerate(['R1','C1','C2','C4','C5','C6','C7']):
        put(ref,80+i*190,170,'power','01  ALIMENTACIÓN 3,3 V' if i==0 else None)
    put('R2',1480,140,'vref','02  VREF ≈ 1,65 V')
    put('R3',1480,250,'vref');put('C8',1690,250,'vref')
    put('U1A',1890,150,'vref');put('U4D',2110,150,'vref')
    # Input and preamplifier in a compact column.
    put('ENTRADA',50,710,'audio','03  ENTRADA Y PREAMPLIFICADOR')
    put('CANAL_R',50,1040,'audio')
    for ref,x,y in [('R4',240,710),('R5',240,1040),('RV1_SUP',430,710),
                    ('RV1_INF',430,1040),('C9',430,850),('R6',430,1200),
                    ('U1B',620,850),('R7',620,1060),('R8',620,1200),('C10',620,1340)]:put(ref,x,y)

    def lowpass(prefix,x,y,group,title=None):
        r1,r2,cf,cg,amp=prefix
        put(r1,x,y,group,title);put(r2,x+195,y,group)
        put(cf,x+110,y-100,group);put(cg,x+195,y+130,group,rotation=90)
        put(amp,x+390,y-30,group)
    def highpass(prefix,x,y,group,title=None):
        c1,c2,rf,rg,amp=prefix
        put(c1,x,y,group,title);put(c2,x+195,y,group)
        put(rf,x+110,y-100,group);put(rg,x+195,y+130,group,rotation=90)
        put(amp,x+390,y-30,group)

    lowpass(['R9','R10','C11','C12','U1C'],880,480,'graves','04  GRAVES · PASA BAJAS 239 Hz')
    highpass(['C13','C14','R11','R12','U1D'],880,900,'medios','05  MEDIOS · PASA ALTAS + PASA BAJAS')
    lowpass(['R13','R14','C15','C16','U2A'],1420,900,'medios')
    highpass(['C17','C18','R15','R16','U2B'],880,1320,'agudos','06  AGUDOS · PASA ALTAS 4026 Hz')
    for n,y,group in [(2,480,'graves'),(3,900,'medios'),(4,1320,'agudos')]:
        put(f'RV{n}_SUP',1990,y,group)
        put(f'RV{n}_INF',1990,y+160,group)
    # The three detector chains align with their corresponding filter.
    for y,group,det,diode,cap,res,buf,meter in [
        (480,'graves','U3A','D1','C22','R27','U3B','NIVEL_G'),
        (900,'medios','U3C','D2','C23','R28','U3D','NIVEL_M'),
        (1320,'agudos','U4A','D3','C24','R29','U4B','NIVEL_A')]:
        put(det,2240,y-30,group,'07  DETECTORES → ADC' if y==480 else None)
        put(diode,2390,y,group);put(cap,2390,y+120,group,rotation=90)
        put(res,2570,y+120,group,rotation=90);put(buf,2580,y-30,group)
        put(meter,2770,y-30,group)
    # Summing and output below all three bands.
    for ref,x,y in [('R17',880,1690),('R18',880,1850),('U4C',1080,1690),
        ('R19',1310,1580),('R20',1310,1720),('R21',1310,1860),
        ('U2C',1530,1690),('R22',1530,1860),('C19',1740,1690),
        ('R23',1940,1690),('R24',1940,1850),('RV5_SUP',2140,1690),
        ('RV5_INF',2140,1850),('SALIDA_LINEA',2340,1690)]:put(ref,x,y)
    parts['R17']['properties']['presentationTitle']='08  INVERSIÓN DE MEDIOS Y SUMA'
    lowpass(['R25','R26','C20','C21','U2D'],2550,1780,'audio','09  FILTRO PREVIO A FFT')
    put('TFT',3180,520,'spi','10  ESP32 Y PANTALLA',rotation=90)
    project['boards'][0].update(x=3070,y=1020)
    # Choose short pin-to-pin edges within each original electrical net.
    positions={**{k:(p['x'],p['y']) for k,p in parts.items()},'esp32':(3070,1020)}
    oldcolors={}
    for w in project['wires']:
        for side in ['start','end']:oldcolors[f'{w[side]["componentId"]}:{w[side]["pinName"]}']=w['color']
    wires=[]
    for net in before:
        pins=[p.rsplit(':',1) for p in net]
        attached=[pins.pop(0)]
        while pins:
            _,a,bi=min((abs(positions[a[0]][0]-positions[b[0]][0])+abs(positions[a[0]][1]-positions[b[0]][1]),a,i) for a in attached for i,b in enumerate(pins))
            b=pins.pop(bi);attached.append(b)
            original=oldcolors[net[0]]
            color=COLORS['vref'] if original=='#a060c0' else COLORS['gnd'] if original=='#292929' else COLORS['power'] if original=='#d84b40' else COLORS.get(groups.get(a[0],'audio'),COLORS['audio'])
            if a[0]=='TFT' or b[0]=='TFT':color=COLORS['spi'] if original not in ['#292929','#d84b40'] else color
            wires.append(dict(id=f'w{len(wires)}',start=dict(componentId=a[0],pinName=a[1],x=0,y=0),end=dict(componentId=b[0],pinName=b[1],x=0,y=0),waypoints=[],color=color))
    project['wires']=wires
    assert partitions(wires)==before,'Changed an electrical net'
    project['name']+=' / por etapas'
    return project


if __name__=='__main__':
    for hz in [100,1000,8000]:
        file=OUT/f'integrado-local-{hz}Hz.vlx'
        payload=json.loads(file.read_text())
        file.write_text(json.dumps(arrange(payload),indent=2))
    print('Tres casos ordenados; mismas particiones eléctricas.')

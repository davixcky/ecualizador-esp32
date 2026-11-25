"""Replace the fixed halves of RV2–RV4 with actual floating audio sliders."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'simulacion/velxio'


def add_controls(payload):
    replacements={}
    for ref,name,color in [('RV2','GRAVES','#ed9a38'),('RV3','MEDIOS','#50c888'),('RV4','AGUDOS','#49c3e0')]:
        upper=next(c for c in payload['components'] if c['id']==ref+'_SUP')
        payload['components']=[c for c in payload['components'] if c['id'] not in [ref+'_SUP',ref+'_INF']]
        payload['components'].append(dict(id=ref,metadataId='slide-potentiometer',x=upper['x'],y=upper['y']-30,
            properties=dict(total=10000,floatingTrack=True,value=50,min=0,max=100,step=1,travelLength=30,
                presentationLabel=f'{ref} · {name} · 10 kΩ',presentationColor=color)))
        if ref=='RV2':payload['components'][-1]['properties']['presentationTitle']='CONTROLES'
        replacements.update({(ref+'_SUP','1'):(ref,'VCC'),(ref+'_SUP','2'):(ref,'SIG'),
                             (ref+'_INF','1'):(ref,'SIG'),(ref+'_INF','2'):(ref,'GND')})
    wires=[]
    for wire in payload['wires']:
        changed=False
        for side in ['start','end']:
            key=(wire[side]['componentId'],wire[side]['pinName'])
            if key in replacements:
                ref,pin=replacements[key]
                wire[side]=dict(componentId=ref,pinName=pin,x=0,y=0)
                changed=True
        if wire['start']['componentId']==wire['end']['componentId'] and wire['start']['pinName']==wire['end']['pinName']:
            continue
        if changed:wire['waypoints']=[]
        wires.append(wire)
    payload['wires']=wires
    saved=OUT/'local/rutas-potenciometros.json'
    if saved.exists():
        routes=json.loads(saved.read_text())
        from ordenar_velxio import partitions
        if partitions(routes)!=partitions(wires):raise ValueError('Revisar rutas de los potenciómetros')
        payload['wires']=routes
    return payload


def multitone(payload):
    """Mix three real voltage sources through resistors, without faking ADCs."""
    from copy import deepcopy
    payload=deepcopy(payload)
    payload['name']='EQ03 / tres tonos y tres potenciómetros'
    def part(ref,kind,x,y,props):
        payload['components'].append(dict(id=ref,metadataId=kind,x=x,y=y,properties=props))
    def wire(ref,a,ap,b,bp,color='#b9c4d6'):
        payload['wires'].append(dict(id=ref,start=dict(componentId=a,pinName=ap,x=0,y=0),end=dict(componentId=b,pinName=bp,x=0,y=0),waypoints=[],color=color))
    # All former ENTRADA:SIG endpoints become the common mixer node.
    for w in payload['wires']:
        for e in ['start','end']:
            if w[e]['componentId']=='ENTRADA' and w[e]['pinName']=='SIG':
                w[e]=dict(componentId='MEZCLA_G',pinName='2',x=0,y=0)
                w['waypoints']=[]
    source=next(c for c in payload['components'] if c['id']=='ENTRADA')
    source.update(x=35,y=510)
    source['properties'].update(frequency=100,amplitude=.45,presentationLabel='100 Hz · graves')
    right=next(c for c in payload['components'] if c['id']=='CANAL_R')
    right.update(x=35,y=1420)
    right['properties']['frequency']=50  # 80 ms transient for responsive live controls.
    for ref,y,hz,color in [('TONO_M',830,1000,'#50c888'),('TONO_A',1150,8000,'#49c3e0')]:
        part(ref,'signal-generator',35,y,dict(waveform='sine',frequency=hz,amplitude=.45,offset=0,
             presentationLabel=f'{hz} Hz',presentationColor=color))
        wire('gnd_'+ref,ref,'GND','ENTRADA','GND','#64748b')
    for suffix,source,y in [('G','ENTRADA',510),('M','TONO_M',830),('A','TONO_A',1150)]:
        part('MEZCLA_'+suffix,'resistor',180,y,dict(value='1000',presentationLabel='Mezcla · 1 kΩ',presentationColor='#b9c4d6'))
        wire('entrada_'+suffix,source,'SIG','MEZCLA_'+suffix,'1')
        if suffix!='G':wire('suma_'+suffix,'MEZCLA_'+suffix,'2','MEZCLA_G','2')
    return payload


if __name__=='__main__':
    for hz in [100,1000,8000]:
        p=OUT/f'integrado-local-{hz}Hz.vlx'
        p.write_text(json.dumps(add_controls(json.loads(p.read_text())),indent=2))

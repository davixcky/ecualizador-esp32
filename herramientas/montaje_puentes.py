"""Asignación reproducible de cara de montaje y modelos de cables aislados.
La geometría del cable es orientativa; los extremos son los taladros reales.
"""
import math
from pathlib import Path

MAX_SUPERIOR = 20.0

def cara(j):
    return 'inferior' if j['terminal'] or any(math.dist(a,b)>MAX_SUPERIOR for a,b in j['alambres']) else 'superior'

def modelo(j, folder):
    """Malla tubular VRML en unidades de 0,1 pulgadas, como espera KiCad."""
    vertices=[];faces=[];lower=cara(j)=='inferior';radius=.42
    for a,b in j['alambres']:
        n=20;offset=len(vertices)
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        ux,uy=-dy/length,dx/length
        for i in range(n+1):
            t=i/n
            # Entrada al taladro y arco flexible, sin representar cobre superior.
            z=(-1.6-1.0-3.0*math.sin(math.pi*t)) if lower else (.4+1.4*math.sin(math.pi*t))
            for q in range(8):
                angle=2*math.pi*q/8
                vertices.append(((a[0]+dx*t+radius*ux*math.cos(angle))/2.54,
                                 -(a[1]+dy*t+radius*uy*math.cos(angle))/2.54,
                                 (z+radius*math.sin(angle))/2.54))
        for i in range(n):
            for q in range(8):
                u=offset+i*8+q;v=offset+i*8+(q+1)%8
                faces.append(f'{u}, {v}, {v+8}, {u+8}, -1')
    color='0.18 0.22 0.24' if lower else '0.72 0.76 0.78'
    folder.mkdir(parents=True,exist_ok=True);path=folder/(j['ref']+'.wrl')
    path.write_text('#VRML V2.0 utf8\nShape { appearance Appearance { material Material { diffuseColor '+color+' } } geometry IndexedFaceSet { solid FALSE coord Coordinate { point [\n'+',\n'.join('%.5f %.5f %.5f'%v for v in vertices)+'\n] } coordIndex [\n'+',\n'.join(faces)+'\n] } }\n')
    return path

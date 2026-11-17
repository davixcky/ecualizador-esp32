"""Postproceso reproducible de E.4: accesibilidad de puentes y alimentación perimetral.

Uso: python3 mejorar_soldadura_e4.py DIRECTORIO_CERRADO
"""
import json, math, sys
from pathlib import Path
import pcbnew as k
from pcbnew import FromMM as MM, ToMM, VECTOR2I

D = Path(sys.argv[1]); path = next(D.glob('*.kicad_pcb')); b = k.LoadBoard(str(path))

def xy(v): return (round(ToMM(v.x), 3), round(ToMM(v.y), 3))
def fp(ref): return next(f for f in b.GetFootprints() if f.GetReference() == ref)
def pad(ref, num): return next(p for p in fp(ref).Pads() if p.GetNumber() == num)
def mover_grafica(f, old, end):
    for s in f.GraphicalItems():
        if s.Type() != k.PCB_SHAPE_T: continue
        if math.dist(xy(s.GetStart()), old) < .01: s.SetStart(end)
        if math.dist(xy(s.GetEnd()), old) < .01: s.SetEnd(end)

def pista(a, z, net, ancho=.7):
    t = k.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(VECTOR2I(MM(z[0]), MM(z[1])))
    t.SetLayer(k.B_Cu); t.SetWidth(MM(ancho)); t.SetNet(net); b.Add(t)

def mover_pad(ref, old, new):
    f = fp(ref); p = min(f.Pads(), key=lambda q: math.dist(xy(q.GetPosition()), old))
    end = VECTOR2I(MM(new[0]), MM(new[1])); p.SetPosition(end); mover_grafica(f, old, end)
    return p

# Sustituye el alambre largo +5 V por una pista ancha en el perímetro superior.
j = fp('JP23'); net = list(j.Pads())[0].GetNet(); b.Remove(j)
pts = [(103.1932, 11.0623), (103.1932, 1.5), (25.0, 1.5), (25.0, 32.182), (33.1554, 32.182)]
for a, z in zip(pts, pts[1:]):
    pista(a, z, net, 1.0)
directos = [z for z in json.load(open(D / 'alambres-directos.json')) if z['ref'] != 'JP23']

# Lleva tres taladros propios a zonas abiertas mediante una pista de acceso inferior.
stubs = {
    'JP1': ((7.681, 78.213), (8.68, 74.21), None),
    'JP2': ((12.83, 83.91), (20.33, 93.41), (15.33, 85.41)),
    'JP7': ((36.299, 37.483), (30.30, 37.48), None),
}
moves = []
for ref, (old, new, bend) in stubs.items():
    p = min(fp(ref).Pads(), key=lambda q: math.dist(xy(q.GetPosition()), old))
    puntos = [old] + ([bend] if bend else []) + [new]
    for a, z in zip(puntos, puntos[1:]):
        pista(a, z, p.GetNet())
    mover_pad(ref, old, new); moves.append((ref, old, new))

# Regla E.4: todo puente tiene dos agujeros propios. Estos accesos sustituyen los
# extremos que en la primera iteracion compartian pads de componentes.
accesos = [
    # ref, posicion original del pad JP, origen electrico, destino propio, quiebres
    ('JP5',  (24.817, 78.606), ('R6', '2'),  (38.053, 97.886), []),
    ('JP6',  (37.319, 29.889), ('U3', '12'), (43.315, 29.642), []),
    ('JP24', (184.735, 55.220), ('R32', '1'), (182.735, 42.220), []),
    ('JP24', (179.002, 71.554), ('U5', '25'), (183.502, 71.554), []),
    ('JP25', (179.002, 61.394), ('U5', '21'), (183.502, 61.394), []),
    ('JP25', (175.690, 34.619), ('J4', '2'),  (169.690, 35.619), []),
]

# Libera la salida de U3.12: el extremo cercano de JP7 pasa junto a R35, con su
# propio agujero, y reemplaza el ramal antiguo de ADC_M_RAW.
for t in list(b.GetTracks()):
    if t.Type() != k.PCB_TRACE_T or t.GetNetname() != '/ADC_M_RAW': continue
    extremos = {xy(t.GetStart()), xy(t.GetEnd())}
    if extremos & {(47.339, 32.510), (44.871, 30.042), (43.740, 30.042)}:
        b.Delete(t)
old7, new7 = (43.740, 30.042), (47.000, 30.500)
p7 = mover_pad('JP7', old7, new7); pista((47.339, 32.510), new7, p7.GetNet())
moves.append(('JP7', old7, new7))

# Abre dos salidas horizontales para U5.21 y U5.25. La masa sigue siendo una
# pista inferior continua, pero ahora rodea los dos pads de puente dedicados.
for t in list(b.GetTracks()):
    if t.Type() != k.PCB_TRACE_T or t.GetNetname() != 'GND': continue
    a, z = xy(t.GetStart()), xy(t.GetEnd())
    if (math.dist(a, (181.204, 58.853)) < .01 or math.dist(z, (181.204, 58.853)) < .01 or
        math.dist(a, (181.204, 74.094)) < .01 or math.dist(z, (181.204, 74.094)) < .01 or
        math.dist(a, (181.204, 74.501)) < .01 or math.dist(z, (181.204, 74.501)) < .01):
        b.Delete(t)
gnd = pad('U5', '20').GetNet()
pista((179.002, 58.853), (186.501, 58.853), gnd, 1.0)
pista((186.501, 58.853), (186.501, 79.798), gnd, 1.0)
pista((179.002, 74.094), (186.501, 74.094), gnd, 1.0)

for ref, old, (cr, cn), new, bends in accesos:
    source = pad(cr, cn)
    # LED_DATA ya llega en cobre hasta este punto; solo se prolonga 0,84 mm.
    inicio = (182.668, 43.057) if ref == 'JP24' and old == (184.735, 55.220) else xy(source.GetPosition())
    puntos = [inicio] + bends + [new]
    for a, z in zip(puntos, puntos[1:]): pista(a, z, source.GetNet())
    mover_pad(ref, old, new); moves.append((ref, old, new))

# JP19 conserva su taladro propio original en (119.254, 89.492). Queda bajo el
# cuerpo de R25, por lo que se monta primero, pero no comparte el agujero de R25.

# Retira cada ramal muerto desde el antiguo taladro hasta su primera unión o pad real.
def podar_ramal(punto, red):
    actual = punto
    while True:
        incidentes = [t for t in b.GetTracks() if t.Type() == k.PCB_TRACE_T and t.GetNetname() == red
                      and (math.dist(xy(t.GetStart()), actual) < .01 or math.dist(xy(t.GetEnd()), actual) < .01)]
        if len(incidentes) != 1: return
        if any(p.GetNetname() == red and math.dist(xy(p.GetPosition()), actual) < .01
               for f in b.GetFootprints() if not f.GetReference().startswith('JP') for p in f.Pads()): return
        t = incidentes[0]; siguiente = xy(t.GetEnd()) if math.dist(xy(t.GetStart()), actual) < .01 else xy(t.GetStart())
        b.Delete(t); actual = siguiente
podar_ramal((24.817, 78.606), '/VREF')
podar_ramal((37.319, 29.889), '/G_W')

ruteados = json.load(open(D / 'puentes-ruteados.json'))
for z in ruteados:
    for ref, old, new in moves:
        if z['ref'] != ref: continue
        z['puntos'] = [list(new) if math.dist(q, old) < .01 else q for q in z['puntos']]
        z['alambres'] = [[list(new) if math.dist(a, old) < .01 else a,
                          list(new) if math.dist(c, old) < .01 else c] for a, c in z['alambres']]
json.dump(ruteados, open(D / 'puentes-ruteados.json', 'w'), indent=1)

# JP24 y JP25 nacieron como conexiones pad-a-pad; el CSV debe dejar claro que
# ahora terminan en taladros propios y reflejar su nueva longitud.
for z in directos:
    if z['ref'] not in ('JP24', 'JP25'): continue
    f = fp(z['ref']); pp = list(f.Pads()); a, c = xy(pp[0].GetPosition()), xy(pp[1].GetPosition())
    z['de'] = f"taladro propio {a[0]:.3f},{a[1]:.3f}"
    z['a'] = f"taladro propio {c[0]:.3f},{c[1]:.3f}"
    z['largo_mm'] = round(math.dist(a, c), 1)
    z['taladros_propios'] = True
json.dump(directos, open(D / 'alambres-directos.json', 'w'), indent=1)
b.Save(str(path))

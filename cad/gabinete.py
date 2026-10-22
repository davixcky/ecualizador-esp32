#!/usr/bin/env python3
"""Gabinete del ecualizador en CadQuery: cuerpo, tapa-panel, perillas, tapas de deslizables,
separadores, parlante, módulo PAM8403 y módulo TFT.

Sistema de coordenadas (mm): el mismo del modelo VRML que exporta KiCad de la placa, centrado
en la PCB: X = x_pcb − 100, Y = 60 − y_pcb, Z = 0 en la cara inferior de la PCB. Así la placa
exportada de KiCad cae exactamente dentro del gabinete y cada agujero del panel queda sobre su
pieza. Las posiciones mecánicas se conservan en ../hardware/3d/panel.json.
En D.1 los controles se sujetan al panel y se cablean a la placa; el USB usa extensión.

    python3 gabinete.py        → stl/*.stl y ecualizador-gabinete.step
"""
import json
import math
import os

import cadquery as cq

AQUI = os.path.dirname(os.path.abspath(__file__))
PANEL = json.load(open(os.path.join(AQUI, "..", "hardware", "3d", "panel.json")))
STL = os.path.join(AQUI, "stl")
FUENTE = os.environ.get("CAD_FONT", next((p for p in ("/usr/share/fonts/apple-fonts/SF-Pro-Display-Regular.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if os.path.exists(p)), ""))

# ---------------------------------------------------------------- cotas
PCB_W, PCB_H = PANEL["placa"]
HOLGURA = 1.5            # entre la PCB y la pared
PARED = 2.5
PISO = 2.5
Z_PCB_ARRIBA = 1.6
Z_TAPA = 18.0            # cara inferior de la tapa (por encima del ESP32 sobre su zócalo)
ESPESOR_TAPA = 3.0
Z_PISO = -26.0           # cara superior del piso (separadores de 26 mm bajo la PCB)
RADIO = 8.0

XI, YI = PCB_W / 2 + HOLGURA, PCB_H / 2 + HOLGURA          # medio interior
XE, YE = XI + PARED, YI + PARED                            # medio exterior


def p(x_pcb, y_pcb):
    """Coordenadas de la PCB (KiCad) → coordenadas del modelo."""
    return x_pcb - PCB_W / 2, PCB_H / 2 - y_pcb


def local(ref, lx, ly):
    """Punto local de una huella (KiCad: ángulo positivo antihorario en pantalla) → modelo."""
    q = PANEL["piezas"][ref]
    t = math.radians(q["rot"])
    x = q["x"] + lx * math.cos(t) + ly * math.sin(t)
    y = q["y"] - lx * math.sin(t) + ly * math.cos(t)
    return p(x, y)


AGUJEROS_PCB = [p(4, 4), p(PCB_W - 4, 4), p(4, PCB_H - 4), p(PCB_W - 4, PCB_H - 4)]
EJE_NIVEL = local("RV1", 7.5, 2.5)
EJE_VOLUMEN = local("RV5", 7.5, 2.5)
BOTON = local("SW1", 3.25, 2.25)
PALANCAS = [local(r, 21.75, 1.75) for r in ("RV2", "RV3", "RV4")]
RECORRIDO = 30.0
JACKS = [p(PCB_W, PANEL["piezas"][r]["y"]) for r in ("J1", "J2")]
Z_JACK = Z_PCB_ARRIBA + 2.6
USB_Y = p(0, PANEL["piezas"]["U5"]["y"] - 12.7)[1]
tx, ty, tw, th = PANEL["tft"]
TFT_CENTRO = p(tx + tw / 2, ty + th / 2)       # el vidrio está corrido hacia la derecha del conector
VENTANA = (43.6, 23.6)
# Dos tramos de 100 mm, 6 LED cada uno; canales verticales interiores.
LED_LARGO, LED_ANCHO, LED_HOLGURA = 102.0, 10.0, 0.6
LED_Z = 5.0
LED_Y = YI - 1.5
PARLANTE = p(45, 88)
# Cierre magnético: cuatro pares de discos 6 × 2 mm, fijados con adhesivo.
IMAN_DIAMETRO, IMAN_ESPESOR = 6.0, 2.0
BOLSILLO_D, BOLSILLO_H = 6.3, 2.2
IMANES = AGUJEROS_PCB



# ---------------------------------------------------------------- piezas
def cuerpo():
    caja = (cq.Workplane("XY").workplane(offset=Z_PISO - PISO)
            .rect(2 * XE, 2 * YE).extrude(Z_TAPA - (Z_PISO - PISO))
            .edges("|Z").fillet(RADIO).edges("<Z").fillet(1.5))
    hueco = (cq.Workplane("XY").workplane(offset=Z_PISO).rect(2 * XI, 2 * YI)
             .extrude(Z_TAPA - Z_PISO + 1).edges("|Z").fillet(RADIO - PARED))
    c = caja.cut(hueco)
    # separadores bajo la PCB
    for x, y in AGUJEROS_PCB:
        poste = (cq.Workplane("XY").workplane(offset=Z_PISO).center(x, y).circle(3.6).extrude(-Z_PISO)
                 .faces(">Z").workplane().hole(2.6, 10))
        c = c.union(poste)
    # jacks de entrada y salida (pared derecha)
    for _, y in JACKS:
        c = c.cut(cq.Workplane("YZ").workplane(offset=XI - 1).center(y, Z_JACK).circle(3.6).extrude(PARED + 2))
    # USB del ESP32: muesca abierta hacia arriba
    c = c.cut(cq.Workplane("XY").workplane(offset=11.0).center(XI + PARED / 2, USB_Y)
              .rect(PARED + 2, 13).extrude(Z_TAPA))
    # rejilla del parlante en el piso (agujeros en hexágono)
    xs, ys = PARLANTE
    puntos = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            x = i * 4.6 + (j % 2) * 2.3
            y = j * 4.0
            if math.hypot(x, y) < 17:
                puntos.append((xs + x, ys + y))
    c = c.cut(cq.Workplane("XY").workplane(offset=Z_PISO - PISO - 1).pushPoints(puntos).circle(1.4).extrude(PISO + 2))
    # postes del parlante
    for a in (45, 135, 225, 315):
        x = xs + 23 * math.cos(math.radians(a))
        y = ys + 23 * math.sin(math.radians(a))
        c = c.union(cq.Workplane("XY").workplane(offset=Z_PISO).center(x, y).circle(2.8).extrude(5)
                    .faces(">Z").workplane().hole(1.8, 5))
    # Alojamiento de la tira: 102 × 10,6 × 3 mm, con apoyo inferior y laterales.
    # Ventanas pasantes al exterior cubiertas por difusores opal de 1 mm.
    for side in (-1, 1):
        y = side * LED_Y
        apoyo = cq.Workplane("XY").workplane(offset=LED_Z-1.2).center(0,y).rect(LED_LARGO+2.4,5).extrude(12.8)
        canal = cq.Workplane("XY").workplane(offset=LED_Z).center(0,y).rect(LED_LARGO,3).extrude(10.6)
        c = c.union(apoyo).cut(canal)
        ventana = cq.Workplane("XY").workplane(offset=LED_Z+2).center(0,side*(YI+PARED/2)).rect(98,PARED+4).extrude(6)
        c = c.cut(ventana)
        # Salida abierta para tres hilos y puente entre tramos, hacia el lateral izquierdo.
        paso = cq.Workplane("XY").workplane(offset=LED_Z+1).center(-52,side*LED_Y).rect(6,6).extrude(5)
        c = c.cut(paso)
    # Dos clips de cable por pared izquierda: retorno LED separado del audio.
    for y in (-35,0,35):
        clip = cq.Workplane("XY").workplane(offset=7).center(-XI+2,y).rect(5,7).extrude(5)
        paso = cq.Workplane("XY").workplane(offset=8).center(-XI+2,y).rect(3,9).extrude(5)
        c = c.union(clip.cut(paso))
    # Acceso al borne J6, con cable externo y alivio de tensión por brida.
    c = c.cut(cq.Workplane("YZ").workplane(offset=XI-1).center(2,6).circle(3).extrude(PARED+2))
    # Torres unidas a las paredes, por encima de la PCB. Bolsillos ciegos desde arriba.
    for x,y in IMANES:
        torre = (cq.Workplane("XY").workplane(offset=10).center(x,y)
                 .rect(12,12).extrude(Z_TAPA-10).edges("|Z").fillet(2))
        c = c.union(torre)
        c = c.cut(cq.Workplane("XY").workplane(offset=Z_TAPA-BOLSILLO_H)
                  .center(x,y).circle(BOLSILLO_D/2).extrude(BOLSILLO_H+0.1))
    for x,y in [(-99,-52),(99,52)]:
        c = c.cut(cq.Workplane("XY").workplane(offset=Z_TAPA-2.3).center(x,y)
                  .circle(1.15).extrude(2.4))
    # Uñero posterior para separar la tapa sin hacer palanca en la pantalla.
    c = c.cut(cq.Workplane("XY").workplane(offset=Z_TAPA-1.5)
              .center(70,YE).rect(18,5).extrude(2))
    return c


def tapa():
    t = (cq.Workplane("XY").workplane(offset=Z_TAPA).rect(2 * XE, 2 * YE).extrude(ESPESOR_TAPA)
         .edges("|Z").fillet(RADIO).faces(">Z").edges().chamfer(1.0))
    # ventana de la pantalla
    t = t.cut(cq.Workplane("XY").workplane(offset=Z_TAPA - 1).center(*TFT_CENTRO).rect(*VENTANA)
              .extrude(ESPESOR_TAPA + 2).edges("|Z").fillet(2.5))
    # ranuras de los deslizables
    for x, y in PALANCAS:
        t = t.cut(cq.Workplane("XY").workplane(offset=Z_TAPA - 1).center(x, y).slot2D(RECORRIDO + 3.2, 3.2, 90)
                  .extrude(ESPESOR_TAPA + 2))
    for x, y in (EJE_NIVEL, EJE_VOLUMEN):
        t = t.cut(cq.Workplane("XY").workplane(offset=Z_TAPA - 1).center(x, y).circle(3.8).extrude(ESPESOR_TAPA + 2))
    t = t.cut(cq.Workplane("XY").workplane(offset=Z_TAPA - 1).center(*BOTON).circle(3.6).extrude(ESPESOR_TAPA + 2))
    # Bolsillos por la cara inferior: techo de 0,8 mm, sin tornillos visibles.
    for x,y in IMANES:
        t = t.cut(cq.Workplane("XY").workplane(offset=Z_TAPA-.1).center(x,y)
                  .circle(BOLSILLO_D/2).extrude(BOLSILLO_H+.1))
    # Dos tetones de registro: evitan que la tapa se desplace lateralmente.
    for x,y in [(-99,-52),(99,52)]:
        t = t.union(cq.Workplane("XY").workplane(offset=Z_TAPA-2).center(x,y)
                    .circle(.9).extrude(2))
    # textos grabados
    z = Z_TAPA + ESPESOR_TAPA

    def grabar(txt, x, y, tam, ang=0):
        nonlocal t
        s = (cq.Workplane("XY").workplane(offset=z - 0.6).center(x, y)
             .text(txt, tam, 1.0, fontPath=FUENTE, combine=False, halign="center", valign="center"))
        if ang:
            s = s.rotate((x, y, 0), (x, y, 1), ang)
        t = t.cut(s)
        relleno = s.intersect(cq.Workplane("XY").workplane(offset=z-.59).rect(2*XE,2*YE).extrude(.55))
        if "rotulos" in PIEZAS:
            PIEZAS["rotulos"] = PIEZAS["rotulos"].add(relleno)
        else:
            PIEZAS["rotulos"] = relleno

    for (x, y), nombre in zip(PALANCAS, ("GRAVES", "MEDIOS", "AGUDOS")):
        grabar(nombre, x, y - RECORRIDO / 2 - 6, 3.2)
        grabar("+", x - 5.5, y + RECORRIDO / 2 - 1, 3.5)
        grabar("-", x - 5.5, y - RECORRIDO / 2 + 1, 3.5)
        for k in range(7):                                   # marcas de escala
            yy = y - RECORRIDO / 2 + k * RECORRIDO / 6
            t = t.cut(cq.Workplane("XY").workplane(offset=z - 0.5).center(x + 4.5, yy).rect(2.5 if k % 3 else 4, 0.5)
                      .extrude(1))
    grabar("NIVEL", EJE_NIVEL[0], EJE_NIVEL[1] - 12, 3.2)
    grabar("VOLUMEN", EJE_VOLUMEN[0], EJE_VOLUMEN[1] - 12, 3.2)
    grabar("VISTA", BOTON[0], BOTON[1] - 9, 3.2)
    grabar("ENTRADA", XE - 7, JACKS[0][1], 2.6, 90)
    grabar("SALIDA", XE - 7, JACKS[1][1], 2.6, 90)
    grabar("EQ / 03", -57, -28, 8)
    grabar("ANALOG AUDIO  /  ESP32", -46, -39, 3.0)
    grabar("CUC   ·   ELECTRONICA II", -48, -48, 2.6)
    # tres franjas decorativas (se pintan de color en el render)
    for i in range(3):
        t = t.cut(cq.Workplane("XY").workplane(offset=z - 0.6).center(-40 + (i - 1) * 26, -16).rect(22, 2.2).extrude(1))
    return t


def franjas():
    """Relleno de color de las tres franjas grabadas (piezas aparte para el render)."""
    z = Z_TAPA + ESPESOR_TAPA
    return [cq.Workplane("XY").workplane(offset=z - 0.6).center(-40 + (i - 1) * 26, -16).rect(21.8, 2.0).extrude(0.55)
            for i in range(3)]


def perilla(x, y):
    base = Z_TAPA + ESPESOR_TAPA + 0.8
    k = (cq.Workplane("XY").workplane(offset=base).center(x, y).circle(8).workplane(offset=9).circle(7.6)
         .loft().faces(">Z").edges().fillet(1.5))
    for i in range(24):                                      # moleteado
        a = 2 * math.pi * i / 24
        k = k.cut(cq.Workplane("XY").workplane(offset=base + 2).center(x + 8.2 * math.cos(a), y + 8.2 * math.sin(a))
                  .circle(0.8).extrude(8))
    k = k.cut(cq.Workplane("XY").workplane(offset=base + 8.4).center(x, y + 4).rect(1.2, 5).extrude(1))
    return k


def tapa_deslizable(x, y):
    base = Z_TAPA + ESPESOR_TAPA + 1.0
    c = cq.Workplane("XY").workplane(offset=base).center(x, y).rect(10, 6).extrude(6).edges("|Z").fillet(1.2)
    c = c.faces(">Z").edges().fillet(1.0)
    for k in (-2, 0, 2):
        c = c.cut(cq.Workplane("XY").workplane(offset=base + 5.4).center(x, y + k).rect(11, 0.8).extrude(1))
    return c


def boton(x, y):
    return (cq.Workplane("XY").workplane(offset=Z_TAPA + ESPESOR_TAPA - 1).center(x, y).circle(3.2).extrude(4)
            .faces(">Z").edges().fillet(1.0))


def separadores():
    out = None
    for x, y in AGUJEROS_PCB:
        s = (cq.Workplane("XY").workplane(offset=Z_PCB_ARRIBA).center(x, y).polygon(6, 5.5 / math.cos(math.pi / 6))
             .extrude(4).faces(">Z").workplane().hole(3.0))
        out = s if out is None else out.union(s)
    return out


def parlante():
    x, y = PARLANTE
    marco = cq.Workplane("XY").workplane(offset=Z_PISO + 5).center(x, y).rect(50, 50).extrude(1.2).edges("|Z").fillet(4)
    marco = marco.cut(cq.Workplane("XY").workplane(offset=Z_PISO + 4).center(x, y).circle(18).extrude(4))
    # Canasta abierta y culata: el cono mira a la rejilla del piso.
    canasta = cq.Workplane("XY").workplane(offset=Z_PISO + 6.2).center(x,y).circle(19).circle(17).workplane(offset=7).circle(11).circle(9).loft()
    for ang in (0,90,180,270):
        ventana=cq.Workplane("XY").workplane(offset=Z_PISO+7).center(x,y+13).box(13,13,4,centered=(True,True,False)).rotate((x,y,0),(x,y,1),ang)
        canasta=canasta.cut(ventana)
    iman = cq.Workplane("XY").workplane(offset=Z_PISO + 13).center(x, y).circle(10).extrude(5)
    culata=cq.Workplane("XY").workplane(offset=Z_PISO+18).center(x,y).circle(10.8).circle(2).extrude(.8)
    return marco.union(canasta).union(iman).union(culata)



def pam8403():
    x, y = p(120, 100)
    b = cq.Workplane("XY").workplane(offset=Z_PISO + 6).center(x, y).rect(24, 21).extrude(1.6)
    for dx, dy in ((-10, -8.5), (10, -8.5), (-10, 8.5), (10, 8.5)):
        b = b.union(cq.Workplane("XY").workplane(offset=Z_PISO).center(x + dx, y + dy).circle(1.8).extrude(6))
    ci = cq.Workplane("XY").workplane(offset=Z_PISO + 7.6).center(x, y).rect(5, 6.5).extrude(1.6)
    return b, ci


def tft():
    """Envolvente nominal Waveshare 51,2 × 27,3; montaje en cuna, sin inventar taladros."""
    cx, cy = TFT_CENTRO
    placa = cq.Workplane("XY").workplane(offset=12.6).center(cx,cy).rect(tw,th).extrude(1.6)
    vidrio = cq.Workplane("XY").workplane(offset=14.2).center(cx,cy).rect(46.0,26.0).extrude(3.4)
    return placa, vidrio


def cuna_tft():
    cx,cy=TFT_CENTRO
    aro=cq.Workplane("XY").workplane(offset=11.4).center(cx,cy).rect(tw+3,th+3).extrude(6.6)
    hueco=cq.Workplane("XY").workplane(offset=12.6).center(cx,cy).rect(tw+0.6,th+0.6).extrude(7)
    paso=cq.Workplane("XY").workplane(offset=11).center(cx,cy).rect(44,22).extrude(9)
    # Ranura del cable GH1.25; la cuna se fija bajo la tapa con cinta de montaje.
    cable=cq.Workplane("XY").workplane(offset=11).center(cx-tw/2,cy).rect(8,14).extrude(6)
    return aro.cut(hueco).cut(paso).cut(cable)


def iluminacion(side):
    y=side*LED_Y
    tira=cq.Workplane("XY").workplane(offset=LED_Z+0.3).center(0,y).rect(100,0.8).extrude(10)
    difusor=cq.Workplane("XY").workplane(offset=LED_Z+1.5).center(0,side*(YI+PARED-0.6)).rect(100,1).extrude(7)
    chips=None
    for i in range(6):
        led=cq.Workplane("XY").workplane(offset=LED_Z+2.8).center(-41.667+i*16.667,y+side*0.8).rect(5,1.2).extrude(5)
        chips=led if chips is None else chips.union(led)
    return tira,difusor,chips


PIEZAS = {}


def construir():
    PIEZAS.clear()
    PIEZAS["cuerpo"] = cuerpo()
    PIEZAS["tapa"] = tapa()
    for i, f in enumerate(franjas()):
        PIEZAS[f"franja{i}"] = f
    PIEZAS["perilla-nivel"] = perilla(*EJE_NIVEL)
    PIEZAS["perilla-volumen"] = perilla(*EJE_VOLUMEN)
    for i, (x, y) in enumerate(PALANCAS):
        # posiciones de ejemplo de los deslizables (graves arriba, agudos abajo)
        PIEZAS[f"deslizable{i}"] = tapa_deslizable(x, y + (9, 2, -5)[i])
    PIEZAS["boton"] = boton(*BOTON)
    PIEZAS["separadores"] = separadores()
    PIEZAS["parlante"] = parlante()
    PIEZAS["pam8403"], PIEZAS["pam8403-ci"] = pam8403()
    PIEZAS["tft-placa"], PIEZAS["tft-vidrio"] = tft()
    PIEZAS["cuna-tft"] = cuna_tft()
    for i,side in enumerate((-1,1)):
        PIEZAS[f"tira{i}"],PIEZAS[f"difusor{i}"],PIEZAS[f"led{i}"] = iluminacion(side)
    for i,(x,y) in enumerate(IMANES):
        PIEZAS[f"iman-base{i}"] = cq.Workplane("XY").workplane(offset=Z_TAPA-2.1).center(x,y).circle(3).extrude(2)
        PIEZAS[f"iman-tapa{i}"] = cq.Workplane("XY").workplane(offset=Z_TAPA+.1).center(x,y).circle(3).extrude(2)
    return PIEZAS


if __name__ == "__main__":
    os.makedirs(STL, exist_ok=True)
    piezas = construir()
    ens = cq.Assembly()
    for nombre, s in piezas.items():
        cq.exporters.export(s, os.path.join(STL, f"{nombre}.stl"), tolerance=0.05, angularTolerance=0.1)
        ens.add(s, name=nombre)
    ens.save(os.path.join(AQUI, "ecualizador-gabinete.step"))
    bb = piezas["cuerpo"].val().BoundingBox()
    print(f"Gabinete: {bb.xlen:.1f} × {bb.ylen:.1f} × {bb.zlen + ESPESOR_TAPA:.1f} mm; piezas en {STL}")

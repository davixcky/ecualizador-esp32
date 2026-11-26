#!/usr/bin/env python3
"""Hoja de banco: el bloque VREF de la T1 con el valor que debe leer el DMM.

Dibuja el mismo circuito que `generar_esquematico.py` pone en la caja
"ALIMENTACION ANALOGICA Y VREF = 1,65 V" (R1-C1-C2, divisor R2/R3, C8 y el
seguidor U1A) y le anota la tension esperada en cada nodo, las medidas de
resistencia con la fuente desconectada y la lectura de 2,4 V que aparece si
R3 y R11 estan intercambiadas.

Formato vertical para imprimir en una hoja y dejarla junto al banco.
Sin dependencias: escribe SVG y lo convierte a PNG con qlmanage (macOS).
"""
from pathlib import Path
import subprocess

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "hardware/E5-perforadas/medidas-vref-T1.svg"

W, H = 1240, 2280

TINTA = "#16191d"          # cables y cuerpos
SUAVE = "#5b6472"          # referencias y valores de componente
MARCO = "#c6ccd4"          # bordes de panel y tabla
TITULO_BG = "#eef2f7"
DC_BG, DC_BORDE, DC_TXT = "#e6f0ff", "#1f6feb", "#0b3d91"
AVISO_BG, AVISO_BORDE = "#fff5e6", "#d97706"
FALLA = "#b4232a"
FILA_ALT = "#f6f8fa"

H_FONT = "Helvetica, Arial, sans-serif"

s = []


def add(linea):
    s.append(linea)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, t, size=13, fill=TINTA, anchor="start", weight="normal"):
    add(f'<text x="{x}" y="{y}" font-family="{H_FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">'
        f'{esc(t)}</text>')


def cable(*puntos, grosor=2.0):
    d = " ".join(("M" if i == 0 else "L") + f"{x} {y}"
                 for i, (x, y) in enumerate(puntos))
    add(f'<path d="{d}" fill="none" stroke="{TINTA}" stroke-width="{grosor}" '
        f'stroke-linecap="square"/>')


def nodo(x, y, r=4.5):
    add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{TINTA}"/>')


def panel(x, y, w, h, titulo):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
        f'fill="#ffffff" stroke="{MARCO}" stroke-width="1.5"/>')
    add(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="33" rx="5" '
        f'fill="{TITULO_BG}"/>')
    add(f'<path d="M{x} {y + 34} L{x + w} {y + 34}" stroke="{MARCO}" '
        f'stroke-width="1.5"/>')
    txt(x + 16, y + 23, titulo, 14, TINTA, weight="bold")


# ---------------------------------------------------------------- simbolos
def resistencia_h(x, y, w=62, h=24, ref="", val=""):
    add(f'<rect x="{x}" y="{y - h / 2}" width="{w}" height="{h}" '
        f'fill="#fff" stroke="{TINTA}" stroke-width="2"/>')
    cx = x + w / 2
    txt(cx, y - h / 2 - 10, ref, 14, TINTA, "middle", "bold")
    txt(cx, y + h / 2 + 22, val, 13, SUAVE, "middle")


def resistencia_v(x, y, w=28, h=60, ref="", val=""):
    add(f'<rect x="{x - w / 2}" y="{y}" width="{w}" height="{h}" '
        f'fill="#fff" stroke="{TINTA}" stroke-width="2"/>')
    txt(x + w / 2 + 12, y + 24, ref, 14, TINTA, "start", "bold")
    txt(x + w / 2 + 12, y + 43, val, 13, SUAVE, "start")


def cap_no_polar(x, y, ref="", val=""):
    """Dos placas rectas centradas en y; devuelve (y_arriba, y_abajo)."""
    a, b = y - 8, y + 8
    for yy in (a, b):
        add(f'<path d="M{x - 23} {yy} L{x + 23} {yy}" stroke="{TINTA}" '
            f'stroke-width="2.6"/>')
    txt(x + 32, y - 2, ref, 14, TINTA, "start", "bold")
    txt(x + 32, y + 17, val, 13, SUAVE, "start")
    return a, b


def cap_polar(x, y, ref="", val=""):
    """Placa recta arriba, placa curva abajo, marca + en la pata positiva."""
    a, b = y - 8, y + 8
    add(f'<path d="M{x - 23} {a} L{x + 23} {a}" stroke="{TINTA}" '
        f'stroke-width="2.6"/>')
    add(f'<path d="M{x - 23} {b} Q{x} {b + 13} {x + 23} {b}" fill="none" '
        f'stroke="{TINTA}" stroke-width="2.6"/>')
    txt(x - 30, a - 3, "+", 19, TINTA, "end", "bold")
    txt(x + 32, y - 2, ref, 14, TINTA, "start", "bold")
    txt(x + 32, y + 17, val, 13, SUAVE, "start")
    return a, b


def gnd(x, y):
    cable((x, y), (x, y + 14))
    for i, (semi, yy) in enumerate(((17, 14), (11, 20), (5, 26))):
        add(f'<path d="M{x - semi} {y + yy} L{x + semi} {y + yy}" '
            f'stroke="{TINTA}" stroke-width="{2.6 - i * 0.4}"/>')


def simbolo_potencia(x, y, nombre):
    """Simbolo de red de potencia: barra y nombre. Es una etiqueta global, no
    el PWR_FLAG de KiCad: todo lo que lleve este nombre es el mismo nodo.
    """
    cable((x, y), (x, y - 26))
    add(f'<path d="M{x - 20} {y - 26} L{x + 20} {y - 26}" stroke="{TINTA}" '
        f'stroke-width="3"/>')
    txt(x, y - 36, nombre, 14, TINTA, "middle", "bold")


def etiqueta_red(x, y, nombre, anchor="start"):
    txt(x, y, nombre, 13, DC_TXT, anchor, "bold")


def callout(x, y, valor, hacia, w=104, h=30):
    """Caja azul con el valor de DC y una linea guia punteada hasta el nodo."""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" '
        f'fill="{DC_BG}" stroke="{DC_BORDE}" stroke-width="1.6"/>')
    txt(x + w / 2, y + h / 2 + 6, valor, 17, DC_TXT, "middle", "bold")
    hx, hy = hacia
    sx = x + w / 2 if abs(hx - (x + w / 2)) < w / 2 else (x + w if hx > x else x)
    sy = y + h if hy > y + h else (y if hy < y else y + h / 2)
    add(f'<path d="M{sx} {sy} L{hx} {hy}" stroke="{DC_BORDE}" '
        f'stroke-width="1.4" stroke-dasharray="5 4"/>')
    add(f'<circle cx="{hx}" cy="{hy}" r="3.4" fill="{DC_BORDE}"/>')


def tabla(x, y, w, titulo, cabeceras, anchos, filas, nota=()):
    alto = [max(len(c) for c in f) * 19 + 17 for f in filas]
    h = 36 + 30 + sum(alto) + (len(nota) * 20 + 12 if nota else 0)
    panel(x, y, w, h, titulo)
    yy = y + 34
    add(f'<rect x="{x + 1}" y="{yy}" width="{w - 2}" height="30" '
        f'fill="#eff3f7"/>')
    cx = x + 16
    for cab, an in zip(cabeceras, anchos):
        txt(cx, yy + 20, cab, 13, TINTA, weight="bold")
        cx += an
    yy += 30
    for i, (fila, af) in enumerate(zip(filas, alto)):
        if i % 2:
            add(f'<rect x="{x + 1}" y="{yy}" width="{w - 2}" height="{af}" '
                f'fill="{FILA_ALT}"/>')
        add(f'<path d="M{x + 1} {yy} L{x + w - 1} {yy}" stroke="{MARCO}" '
            f'stroke-width="1"/>')
        cx = x + 16
        for j, (celda, an) in enumerate(zip(fila, anchos)):
            color = TINTA if j < 2 else SUAVE
            peso = "bold" if j == 1 else "normal"
            for k, linea in enumerate(celda):
                txt(cx, yy + 23 + k * 19, linea, 13, color, weight=peso)
            cx += an
        yy += af
    for k, linea in enumerate(nota):
        txt(x + 16, yy + 24 + k * 20, linea, 12.5, FALLA)
    return h


# ---------------------------------------------------------------- cabecera
# `s` guarda solo el cuerpo: luego se envuelve en el lienzo vertical (SVG) y
# en uno cuadrado (PNG), porque qlmanage recorta todo lo que no sea cuadrado.
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
add(f'<rect width="{W}" height="92" fill="{TITULO_BG}"/>')
add(f'<path d="M0 92 L{W} 92" stroke="{MARCO}" stroke-width="2"/>')
txt(30, 38, "T1 · VREF = 1,65 V — QUÉ DEBE LEER EL MULTÍMETRO", 24, TINTA,
    weight="bold")
txt(30, 62, "Etapa 2 de hardware/E5-perforadas/guia-pruebas-tarjetas.pdf "
            "(págs. 2-3). Circuito igual al de la caja «Alimentación "
            "analógica y VREF»", 13.5, SUAVE)
txt(30, 81, "del esquema maestro. Valores esperados según el modelo; cuente "
            "±2 % por las resistencias al 1 %.", 13.5, SUAVE)

# ================================================================ esquema
PA_Y, PA_H = 104, 492
panel(25, PA_Y, 1190, PA_H,
      "TENSIONES EN DC · FUENTE ENCENDIDA Y U1 EN EL ZÓCALO")

add('<g transform="translate(10,32)">')
YR, YG = 200, 430          # riel +3.3VA y nivel de masa

simbolo_potencia(80, YR, "+3V3")
txt(104, YR - 32, "(JBUS 3)", 12, SUAVE)
cable((80, YR), (140, YR))
resistencia_h(140, YR, 62, 24, "R1", "10 Ω")
cable((202, YR), (620, YR))
nodo(260, YR)
etiqueta_red(260, YR - 14, "+3.3VA", "middle")

a, b = cap_polar(330, 300, "C1", "100 µF")
cable((330, YR), (330, a))
cable((330, b), (330, YG))
gnd(330, YG)
a, b = cap_no_polar(420, 300, "C2", "100 nF")
cable((420, YR), (420, a))
cable((420, b), (420, YG))
gnd(420, YG)

cable((620, YR), (620, 240))
resistencia_v(620, 240, 28, 60, "R2", "10 kΩ")
cable((620, 300), (620, 360))
nodo(620, 330)
etiqueta_red(600, 324, "VDIV", "end")
resistencia_v(620, 360, 28, 60, "R3", "10 kΩ")
cable((620, 420), (620, YG))
gnd(620, YG)

cable((510, 330), (620, 330))
a, b = cap_polar(510, 378, "C8", "10 µF")
cable((510, 330), (510, a))
cable((510, b), (510, YG))
gnd(510, YG)
nodo(510, 330)

cable((620, 330), (830, 330), (830, 310), (860, 310))
add(f'<path d="M860 270 L860 390 L960 330 Z" fill="#fff" stroke="{TINTA}" '
    f'stroke-width="2.2"/>')
txt(874, 316, "+", 17, TINTA, "start", "bold")
txt(874, 362, "–", 19, TINTA, "start", "bold")
txt(896, 342, "U1A", 14, TINTA, "start", "bold")
txt(852, 304, "3", 13, SUAVE, "end")
txt(852, 366, "2", 13, SUAVE, "end")
txt(968, 322, "1", 13, SUAVE, "start")
cable((960, 330), (1090, 330))
nodo(1000, 330)
cable((1000, 330), (1000, 400), (830, 400), (830, 350), (860, 350))
txt(862, 416, "realimentación pin 1 → pin 2", 12, SUAVE)
etiqueta_red(1098, 326, "VREF")
txt(1098, 344, "(JBUS 4)", 12, SUAVE)

callout(36, 118, "3,30 V", (80, 174))
callout(196, 118, "≈ 3,30 V", (260, YR), w=124)
callout(400, 252, "1,65 V", (566, 330))
callout(990, 226, "1,65 V", (1045, 330))

txt(50, 486, "Seguidor de tensión: la salida copia VDIV, así que con U1 en "
             "el zócalo pin 3 = pin 2 = pin 1 = 1,65 V.", 13, TINTA)
txt(50, 508, "C1 y C8 son electrolíticos: la pata + va al nodo (+3.3VA y "
             "VDIV) y la – a GND. El divisor consume 165 µA, así que R1 "
             "cae menos de 2 mV.", 13, SUAVE)
add('</g>')

# ================================================================ patillaje
# Nets tomadas de circuito.py: AO(unidad, +, -, salida).
PB_Y, PB_H = 612, 390
panel(25, PB_Y, 1190, PB_H,
      "U1 · LM324N · QUÉ ES CADA PIN Y QUÉ DEBE MEDIR EN REPOSO (SIN SEÑAL)")

CUERPO_X1, CUERPO_X2 = 520, 720
CUERPO_Y1, CUERPO_Y2 = 676, 928
FILA_Y = [690 + i * 38 for i in range(7)]

add(f'<rect x="{CUERPO_X1}" y="{CUERPO_Y1}" width="{CUERPO_X2 - CUERPO_X1}" '
    f'height="{CUERPO_Y2 - CUERPO_Y1}" rx="5" fill="#fff" stroke="{TINTA}" '
    f'stroke-width="2.2"/>')
add(f'<path d="M609 {CUERPO_Y1} A11 11 0 0 0 631 {CUERPO_Y1}" fill="none" '
    f'stroke="{TINTA}" stroke-width="2.2"/>')
txt(620, 806, "U1", 20, TINTA, "middle", "bold")
txt(620, 826, "LM324N", 12.5, TINTA, "middle")
txt(620, 844, "vista desde arriba", 11.5, SUAVE, "middle")

# (pin, funcion del fabricante, red del proyecto, valor esperado)
PINES_IZQ = [
    (1, "OUT1", "VREF · salida del seguidor", "1,65 V"),
    (2, "IN1−", "VREF · realimentación de U1A", "1,65 V"),
    (3, "IN1+", "VDIV · divisor R2/R3", "1,65 V"),
    (4, "V+", "+5V · alimentación", "5,00 V"),
    (5, "IN2+", "PRE_IN · C9 y R6 (100 k) a VREF", "1,65 V"),
    (6, "IN2−", "PRE_FB · R7 (22 k) y R8 (10 k)", "1,65 V"),
    (7, "OUT2", "PRE · salida del preamplificador", "1,65 V"),
]
PINES_DER = [
    (14, "OUT4", "MED_HP · salida del pasa altas", "1,65 V"),
    (13, "IN4+", "MH2 · R12 (56 k) a VREF", "1,65 V"),
    (12, "IN4−", "MED_HP · realimentación de U1D", "1,65 V"),
    (11, "V−", "GND · masa", "0,00 V"),
    (10, "IN3+", "LB2 · R10 desde PRE, C12 a VREF", "1,65 V"),
    (9, "IN3−", "GRAVES · realimentación de U1C", "1,65 V"),
    (8, "OUT3", "GRAVES · salida del pasa bajas", "1,65 V"),
]

for (pin, func, red, val), y in zip(PINES_IZQ, FILA_Y):
    cable((CUERPO_X1, y), (CUERPO_X1 - 18, y), grosor=2.4)
    txt(CUERPO_X1 + 10, y + 5, str(pin), 13, TINTA, "start", "bold")
    txt(CUERPO_X1 - 26, y + 5, val, 13.5, DC_TXT, "end", "bold")
    txt(CUERPO_X1 - 86, y + 5, red, 13, TINTA, "end")
    txt(CUERPO_X1 - 86 - 258, y + 5, func, 12, SUAVE, "start")

for (pin, func, red, val), y in zip(PINES_DER, FILA_Y):
    cable((CUERPO_X2, y), (CUERPO_X2 + 18, y), grosor=2.4)
    txt(CUERPO_X2 - 10, y + 5, str(pin), 13, TINTA, "end", "bold")
    txt(CUERPO_X2 + 26, y + 5, val, 13.5, DC_TXT, "start", "bold")
    txt(CUERPO_X2 + 86, y + 5, red, 13, TINTA, "start")
    txt(CUERPO_X2 + 86 + 258, y + 5, func, 12, SUAVE, "start")

txt(50, 964, "Los cuatro amplificadores polarizan en VREF, así que en reposo "
             "las trece patillas de señal deben estar en 1,65 V: solo el pin 4 "
             "(5 V) y el pin 11 (0 V) se salen.", 13, TINTA)
txt(50, 986, "PIN 7 Y PIN 8 ESTÁN UNIDOS EN CONTINUA por R9 + R10 (10 k + "
             "10 k): en reposo tienen que leer lo mismo salvo unos pocos mV de "
             "diferencia (corriente de polarización). Si no, el montaje no es el del esquema.", 13.5,
    FALLA, weight="bold")

# ================================================================ tablas
FILAS_OHM = [
    (["VDIV ↔ GND"], ["≈ 10 kΩ"],
     ["Es R3. Si da 27 kΩ, la resistencia montada ahí es la de R11"]),
    (["VDIV ↔ +3.3VA"], ["≈ 10 kΩ"],
     ["Es R2. Abierto = soldadura fría o pata levantada"]),
    (["+3V3 ↔ +3.3VA"], ["≈ 10 Ω"],
     ["Es R1. Abierto = no llega el riel filtrado al divisor"]),
    (["+5V ↔ +3V3"], ["abierto"],
     ["Cualquier valor bajo, o un salto de diodo, explica que +3V3 "
      "suba a 4,4 V"]),
    (["+5V ↔ GND"], ["sin corto"],
     ["0 Ω = corto; no vuelva a encender hasta encontrarlo"]),
    (["VREF ↔ GND"], ["sin corto"],
     ["0 Ω = VREF a masa; revise C8 y la pista de VREF"]),
    (["Zócalo pin 4 ↔ +5V", "Zócalo pin 11 ↔ GND"], ["≈ 0 Ω"],
     ["Abierto = U1 se queda sin alimentación al insertarlo"]),
    (["Zócalo pin 5 ↔ pin 1"], ["≈ 100 kΩ"],
     ["Camino de R6: polariza en VREF el + del preamplificador"]),
    (["Zócalo pin 13 ↔ pin 1"], ["≈ 56 kΩ"],
     ["Camino de R12. Abierto = el pin 13 flota y el pin 14 miente"]),
    (["Zócalo pin 5 ↔ GND"], ["abierto"],
     ["Una fuga aquí baja el pin 5 por debajo de VREF"]),
]

TA_Y = 1020
h_a = tabla(25, TA_Y, 1190,
            "MEDIDAS EN OHMIOS · FUENTE APAGADA Y PINZAS DESCONECTADAS, U1 "
            "FUERA DEL ZÓCALO",
            ["Entre estos dos puntos", "Esperado", "Qué significa"],
            [330, 190, 660], FILAS_OHM,
            nota=["No basta apagar la fuente: retire también sus pinzas. Una "
                  "salida conectada puede tirar +3.3VA a 0 V y entonces "
                  "VDIV ↔ GND leería R2∥R3 ≈ 5 kΩ, que parece falla y no lo "
                  "es.",
                  "C1 y C8 se cargan con la corriente del ohmímetro: espere "
                  "a que la lectura se estabilice antes de anotarla."])

FILAS_DIAG = [
    (["Pin 7 y pin 14 = 1,02 V", "con pin 1 = 1,65 V"],
     ["Los dos se polarizan desde VREF, por R6",
      "(100 k) y R12 (56 k). Que ambos caigan al",
      "mismo valor apunta al riel VREF, no a los",
      "amplificadores"],
     ["Medir pin 5 y pin 13: si también dan 1,02 V",
      "el fallo está en la polarización. Seguir la",
      "pata lejana de R6 y de R12: deben dar",
      "1,65 V y tener continuidad con el pin 1"]),
    (["Pin 7 ≠ pin 8"],
     ["Imposible con el esquema: R9 + R10 los",
      "unen en continua. O hay un error de",
      "montaje en R9/R10/C12, o una de las dos",
      "salidas está oscilando y el multímetro",
      "promedia la oscilación"],
     ["Osciloscopio en AC y µs/div sobre pin 7 y",
      "pin 14. Si oscilan, revisar C4 entre los",
      "pines 4 y 11. Si no, medir R9 y R10 en",
      "ohmios y comprobar que C12 no esté en",
      "corto"]),
    (["El canal de 3,3 V sube", "al encender el de 5 V",
      "(4,42 V medidos)"],
     ["Algo inyecta +5V en la red +3V3. Una",
      "fuente en CV solo entrega corriente, no la",
      "absorbe, así que el riel se va hacia arriba"],
     ["Apagar el canal de 5 V: ¿vuelve a 3,3 V?",
      "Con todo desconectado, +5V ↔ +3V3 debe",
      "dar abierto en el ohmímetro"]),
    (["VDIV = la mitad exacta", "de +3.3VA"],
     ["El divisor está sano (R2 = R3): lo que",
      "falla es el riel, no las resistencias"],
     ["Arreglar primero el riel; VDIV se corrige",
      "solo cuando +3.3VA vuelva a 3,3 V"]),
    (["+3.3VA ≈ 3,3 V", "y VDIV = 2,4 V"],
     ["R3 vale 27 kΩ en vez de 10 kΩ: R3 y R11",
      "quedaron intercambiadas (R11 = 27 kΩ y",
      "también se monta en la T1)"],
     ["Apagar y medir VDIV ↔ GND. Si da 27 kΩ,",
      "poner la de 10 kΩ en R3 y la de 27 kΩ",
      "en R11 (filtro de medios de U1D)"]),
    (["VDIV = 1,65 V pero", "la salida = 2,4 V"],
     ["El seguidor no realimenta: falta el",
      "puente del pin 1 al pin 2"],
     ["Verificar ese puente y que VDIV entre",
      "por el pin 3, no por el pin 2"]),
    (["VDIV ≈ 0 V", "o inestable"],
     ["La masa del canal de 3,3 V no está unida",
      "a GND, o R2 está abierta"],
     ["Unir las masas de los dos canales de la",
      "fuente y medir R2"]),
]

TB_Y = TA_Y + h_a + 16
h_b = tabla(25, TB_Y, 1190, "SU LECTURA DE 2,4 V · QUÉ SIGNIFICA",
            ["Lo que mida ahora", "Diagnóstico", "Qué hacer"],
            [290, 420, 460], FILAS_DIAG)

# -------------------------------------------------------------- pie de orden
YB = TB_Y + h_b + 16
add(f'<rect x="25" y="{YB}" width="1190" height="104" rx="6" '
    f'fill="{AVISO_BG}" stroke="{AVISO_BORDE}" stroke-width="1.6"/>')
txt(45, YB + 28, "ORDEN DE TRABAJO:  1) comprobar que +3V3 se queda en 3,3 V "
                 "con el canal de 5 V encendido   →   2) medir +3.3VA   →   "
                 "3) medir VDIV", 15, TINTA, weight="bold")
txt(45, YB + 52, "→   4) solo con VREF = 1,65 V, inyectar señal. Toda la "
                 "cadena polariza sobre VREF: con la referencia mal, PRE, "
                 "GRAVES y MED_HP no significan nada.", 13, TINTA)
txt(45, YB + 82, "PELIGRO: con el riel en 4,4 V no conecte la T4. El ESP32 "
                 "es de 3,3 V y su máximo absoluto son 3,6 V: se destruye "
                 "antes de que pueda medir nada.", 13.5, FALLA,
    weight="bold")

txt(W - 30, YB + 130, "Generado por herramientas/generar_medidas_vref.py · "
                      "circuito según generar_esquematico.py", 11.5, SUAVE,
    "end")

CUERPO = "\n".join(s)
CABECERA = '<svg xmlns="http://www.w3.org/2000/svg"'

DESTINO.write_text(
    f'{CABECERA} width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
    f'{CUERPO}\n</svg>\n', encoding="utf-8")
print(f"escrito {DESTINO.relative_to(RAIZ)} · alto usado {YB + 112} de {H} px")

# PNG para pegar en el informe o mirar en el celular junto al banco.
# qlmanage hace recorte cuadrado, asi que la pagina va centrada en un lienzo
# ya cuadrado y no pierde ningun borde.
cuadrado = DESTINO.with_name(DESTINO.stem + "-cuadrado.svg")
cuadrado.write_text(
    f'{CABECERA} width="{H}" height="{H}" viewBox="0 0 {H} {H}">\n'
    f'<rect width="{H}" height="{H}" fill="#ffffff"/>\n'
    f'<g transform="translate({(H - W) / 2},0)">\n{CUERPO}\n</g>\n</svg>\n',
    encoding="utf-8")
try:
    subprocess.run(["qlmanage", "-t", "-s", "2000", "-o", str(DESTINO.parent),
                    str(cuadrado)], check=True, capture_output=True)
    bruto = DESTINO.parent / (cuadrado.name + ".png")
    if bruto.exists():
        bruto.replace(DESTINO.with_suffix(".png"))
        print(f"escrito {DESTINO.with_suffix('.png').relative_to(RAIZ)}")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("qlmanage no disponible: queda solo el SVG")
finally:
    cuadrado.unlink(missing_ok=True)

#!/usr/bin/env python3
"""Fuente geométrica única del ensamble E.5 en tarjetas perforadas.

Python puro (sin FreeCAD ni Blender). Lo importan:
  - generar_modelo.py  (FreeCAD: FCStd, STEP, STL, validación)
  - escena_blender.py  (Blender: vistas fijas y video)

Unidades: mm. Origen: esquina frontal izquierda inferior del gabinete.
X hacia la derecha, Y hacia atrás, Z hacia arriba. El frente (Y = 0) lleva la
borde sobre el que bascula la tapa imantada: los potenciómetros quedan a pocos centímetros de T1/T2.

Regla de honestidad: toda cota que no viene de una ficha publicada o de una
medición está en medidas-componentes.json con estado «conservadora» o
«supuesto» y aparece en la lista de pendientes de validacion-3d.json.
"""
from pathlib import Path
import json
import math

HERE = Path(__file__).resolve().parent
MEDIDAS = json.loads((HERE / "medidas-componentes.json").read_text(encoding="utf-8"))
M = MEDIDAS["componentes"]

# ------------------------------------------------------------------ gabinete
W, D, H = 278.0, 192.0, 61.0          # cuerpo; la tapa añade LID
WALL, FLOOR, LID = 2.5, 3.0, 3.0
R_ESQ = 6.0                           # radio de las esquinas verticales
Z_BOARD = 9.0                         # cara inferior de las perforadas
T_PCB = 1.6
ZT = Z_BOARD + T_PCB                  # cara superior de las perforadas
# La tapa no tiene bisagras: cierra con imanes y se abre basculando sobre su borde frontal.
PIVOT_Y, PIVOT_Z = 0.0, H
LID_OPEN_DEG = 100.0

# x, y, ancho, fondo, rótulo. Placas compradas completas, sin recortar.
BOARDS = {
    "T1": (5.5, 5.5, 90.0, 70.0, "ENTRADA + U1"),
    "T2": (105.0, 5.5, 120.0, 80.0, "FILTROS + U2"),
    "T3": (8.0, 100.0, 120.0, 80.0, "DETECTORES U3/U4"),
    "T4": (153.0, 100.0, 120.0, 80.0, "ESP32 + CONTROL"),
}

# ------------------------------------------------------------------ controles
POT = M["Potenciometro-B10K"]["envolvente"]
POT_A = M["Potenciometro-A10K"]["envolvente"]
# La fila se adelantó de y 26 a y 23 el 2026-11-24 para que quepa la pantalla de 3,5 pulgadas
# recibida (su PCB de 97,5 mm de fondo necesita el sitio). Además los cuerpos de RV2-RV4
# bloquean el deslizamiento frontal de la pantalla: son parte de su retención.
KNOB_Y = 23.0
# ref, función, tipo, x, estado de compra, color del indicador
CONTROLS = [
    ("RV1", "NIVEL", "A10K", 59.0, "pendiente", "knob_neutral"),
    ("RV2", "GRAVES", "B10K", 99.0, "declarada", "graves"),
    ("RV3", "MEDIOS", "B10K", 139.0, "declarada", "medios"),
    ("RV4", "AGUDOS", "B10K", 179.0, "declarada", "agudos"),
    ("RV5", "VOLUMEN", "A10K", 219.0, "pendiente", "knob_neutral"),
]
B10K_COMPRADOS = M["Potenciometro-B10K"]["cantidad_comprada"]
POT_TRAVEL_DEG = 300.0                # recorrido eléctrico típico; por medir


def knob_angle(p):
    """Ángulo (grados, antihorario visto desde arriba) para la posición 0..1."""
    return (0.5 - p) * POT_TRAVEL_DEG


# ------------------------------------------------------------------ tapa
# Pantalla: ESP32-3248S035 RECIBIDA el 2026-11-24 (la publicación anunciaba la 2432S028 de 2,8").
# Panel ST7796 de 3,5 pulgadas, 320 x 480, en VERTICAL (interfaz en retrato). El PCB de
# 56,5 x 97,5 cabe entre los parlantes (hueco de 66 mm) y, con la fila de perillas en y 23,
# entre esta y las barras de luz sin moverlas. El módulo queda al ras de la cara exterior,
# al ras del extremo frontal del PCB; la antena WROOM mira al borde trasero.
TFT = M["ESP32-3248S035-RECIBIDA"]
CYD_PCB_W, CYD_PCB_L, CYD_PCB_T = TFT["pcb"][1], TFT["pcb"][0], TFT["pcb"][2]   # 54,9 ancho x 101,5 fondo (publicado)
CYD_MOD_L, CYD_MOD_W, CYD_MOD_T = TFT["modulo_tft"]        # cristal 86,7 x 55,0 x 4,85 MEDIDO (S035C)
# ORIENTACIÓN (foto del comprador): la franja sin cristal (agujeros de montaje, micro-USB y
# USB-C) está en UN extremo corto; el cristal llega casi al otro. Se monta con el cristal hacia
# el frente (perillas) y la franja de conectores hacia las barras; el firmware gira la imagen.
CYD_MOD_OFF = 1.5                     # cristal a 1,5 mm del borde frontal: por comprobar en la probeta
TFT_ACTIVE = [TFT["area_activa"][1], TFT["area_activa"][0]]  # 48,96 x 73,44 en retrato (x, y)
CYD_X0, CYD_Y0 = 139.0 - 54.9 / 2, 32.5   # esquina frontal izquierda del PCB, centrado entre parlantes
TFT_C = (CYD_X0 + CYD_PCB_W / 2, CYD_Y0 + CYD_MOD_OFF + CYD_MOD_L / 2)   # centro del módulo y la ventana
TFT_WIN = (CYD_MOD_W + 1.0, CYD_MOD_L + 1.0)               # ventana pasante: cristal + 0,5 por lado (holgura real de impresión)
Z_CYD_TOP = H + LID - CYD_MOD_T       # cara superior del PCB para que el módulo quede al ras
SPK = M["Parlantes-WS-14595-8ohm-5W"]["envolvente_por_parlante"]   # 100 x 45 x 21 cada uno
SPK_CS = [(56.0, 96.0), (222.0, 96.0)]  # dos transductores del conjunto WS-14595
SPK_WEDGE = 2.3                       # las cuñas a 45° nacen a 2,3 mm del canto: 0,3 mm sobre un marco de 2 mm
SPK_PLUG = (200.0, 57.0)              # conector único del conjunto, sujeto bajo la tapa
SW_C = (249.0, 23.0)                  # SW1: pulsador 6x6 en cuna bajo la tapa, en la fila de perillas
                                      # (su sitio anterior, 139/60, queda bajo el PCB vertical de la pantalla)
STRIP = M["BTF-FCOB-WS2811-12V-720"]
PIXEL = STRIP["paso_pixel"]           # 50 mm por CI WS2811
PX_PER_BAND = 4
BAR_LEN = PIXEL * PX_PER_BAND         # 200 mm
STRIP_W = STRIP["ancho"]
BAR_X0 = (W - BAR_LEN) / 2
HEX = M["Difusor-hexagonal-impreso"]
HEX_WIN, HEX_PITCH, HEX_RIB, HEX_FLOOR, HEX_FLANGE = HEX["ventana_ancho"], HEX["paso_hexagono"], HEX["nervio"], HEX["fondo"], HEX["pestana"]
BARS = [("GRAVES", 136.0, "graves"), ("MEDIOS", 153.0, "medios"), ("AGUDOS", 170.0, "agudos")]
IMAN = M["Imanes-neodimio-6x2"]["envolvente"]     # diámetro, espesor
MAGNETS = [(30.0, 185.0), (154.0, 185.0), (248.0, 185.0), (79.0, 7.0)]   # cuatro pares cuerpo/tapa; el frontal va en una ménsula de la pared

COLORS = {
    "body": (0.10, 0.12, 0.15), "lid": (0.20, 0.22, 0.25),
    "tono_a": (0.62, 0.25, 0.14), "tono_b": (0.86, 0.85, 0.81),      # mitad izquierda terracota, mitad derecha blanco mármol
    "perf": (0.62, 0.48, 0.22), "pad": (0.80, 0.56, 0.20),
    "chip": (0.03, 0.03, 0.035), "socket": (0.09, 0.09, 0.10),
    "xh": (0.92, 0.90, 0.82), "header": (0.05, 0.05, 0.05),
    "metal": (0.72, 0.72, 0.74), "esp": (0.04, 0.06, 0.09),
    "res": (0.25, 0.50, 0.78), "film": (0.10, 0.42, 0.20),
    "cer": (0.80, 0.52, 0.14), "elec": (0.06, 0.07, 0.16),
    "diode": (0.85, 0.35, 0.10), "jack": (0.04, 0.04, 0.04),
    "terminal": (0.12, 0.45, 0.18), "pam": (0.55, 0.06, 0.06),
    "pot": (0.60, 0.61, 0.63), "pot_pend": (0.82, 0.62, 0.20),
    "knob": (0.80, 0.80, 0.82), "knob_neutral": (0.86, 0.86, 0.84),
    "graves": (1.0, 0.48, 0.24), "medios": (0.24, 0.86, 0.52), "agudos": (0.20, 0.71, 1.0),
    "screen": (0.01, 0.015, 0.02), "tft_pcb": (0.72, 0.52, 0.08), "tft_marco": (0.88, 0.88, 0.86),
    "speaker": (0.02, 0.02, 0.02), "cone": (0.10, 0.10, 0.11),
    "strip": (0.93, 0.93, 0.90), "diffuser": (0.92, 0.94, 0.95),
    "support": (0.16, 0.18, 0.20), "pending": (0.86, 0.66, 0.10),
    "block_p": (0.70, 0.08, 0.06), "block_n": (0.05, 0.05, 0.06),
    "w_red": (0.80, 0.05, 0.04), "w_black": (0.02, 0.02, 0.02),
    "w_white": (0.90, 0.90, 0.88), "w_yellow": (0.95, 0.78, 0.08),
    "w_green": (0.08, 0.60, 0.22), "w_blue": (0.08, 0.30, 0.85),
    "w_orange": (0.95, 0.42, 0.05), "w_violet": (0.50, 0.20, 0.70),
    "w_gray": (0.45, 0.46, 0.48), "w_brown": (0.35, 0.18, 0.08),
}

# ------------------------------------------------------------------ opción: dos mitades
# Por defecto cuerpo y tapa son de una pieza. Como opción (MITADES=1 en exportar_bambu.py) se parten en
# x = SEAM_X para imprimirlos acostados en una cama de 256 mm. La junta lleva colas de milano (macho en la mitad izquierda) que se ven en la
# tapa. Encajan bajando una mitad sobre la otra; cunas, la placa trasera de pantalla y la tarjeta T2
# cruzan la junta y la traban.
SEAM_X, SEAM_GAP = 139.0, 0.1
# (y, cuello, cabeza, fondo). La cola central va en la franja maciza entre la ventana de la
# pantalla 3,5" (termina en y 121,45 con el cristal medido) y la barra de GRAVES (y 130,5):
# solo caben 9 mm, así que esa cola es más pequeña que las otras dos.
# Colas de la tapa reforzadas donde hay sitio (2026-11-25): la delantera y la trasera pasan
# a cuello 8 / cabeza 12 / fondo 8; la central sigue pequeña (5/8/5) porque vive en la franja
# de 9 mm entre la ventana del cristal y la barra de GRAVES. La tapa además queda trabada por
# las piezas que cruzan la junta (pantalla con sus ganchos, cunas y tarjeta T2).
SEAM_KEYS_LID = [(8.0, 8.0, 12.0, 8.0), (126.0, 5.0, 8.0, 5.0), (183.0, 8.0, 12.0, 8.0)]
# Junta del cuerpo REFORZADA (2026-11-24, petición del comprador): tres colas de milano
# mayores en el piso (cuello 10, cabeza 16, fondo 10: ~2,6 veces la sección anterior) y dos
# columnas-espiga ocultas de cuello 6 / cabeza 10 / fondo 8 a toda altura dentro de los
# refuerzos interiores de las paredes. La junta ensambla igual (bajando una mitad sobre la
# otra) pero con mucho más área de apriete y cortante.
SEAM_KEYS_BODY = [(5.6, 6.0, 10.0, 8.0), (40.0, 10.0, 16.0, 10.0), (96.0, 10.0, 16.0, 10.0), (150.0, 10.0, 16.0, 10.0), (D - 5.6, 6.0, 10.0, 8.0)]

# ------------------------------------------------------------------ encastres
# Nada va pegado ni atornillado. Tres uniones impresas:
#   seta + ojo de cerradura: la tapa lleva setas (vástago, cono a 45° y cabeza); la pieza baja por el
#       ojo ancho y se corre KEY_D hasta el asiento, pasando un cuello 0,2 mm más estrecho que el vástago.
#   gancho en voladizo: sujeta por el canto las tarjetas, las borneras y el elevador.
#   apriete: nervios de 0,15 mm en los alojamientos de imán y pinza abierta para el portafusible.
STUD_R, STUD_HEAD_R = 2.0, 3.2
KEY_SEAT_R, KEY_ENTRY_R, KEY_NECK, KEY_D = 2.1, 3.45, 3.8, 5.0
EAR_T = 2.0
EAR_W = 2 * KEY_ENTRY_R + 3.1                    # 10 mm
EAR_BACK, EAR_FRONT = KEY_SEAT_R + 1.8, KEY_D + KEY_ENTRY_R + 1.5
LID_STUDS = []  # (x, y, espesor de la oreja)


def ear(x, y, axis, sign, t=EAR_T, width=EAR_W):
    """Oreja con ojo de cerradura. (x, y) es el asiento, donde queda la seta de la tapa; la pieza
    se presenta desplazada -sign * KEY_D en el eje y se corre en sentido sign hasta encajar.
    Devuelve (caja de la oreja, cortes)."""
    LID_STUDS.append((x, y, t))
    a0, a1 = sorted((-sign * EAR_BACK, sign * EAR_FRONT))
    z, h = H - t - .1, t + .2
    if axis == "x":
        body = box(x + a0, y - width / 2, H - t, a1 - a0, width, t)
        ex, ey = x + sign * KEY_D, y
        neck = box(min(x, ex), y - KEY_NECK / 2, z, KEY_D, KEY_NECK, h)
    else:
        body = box(x - width / 2, y + a0, H - t, width, a1 - a0, t)
        ex, ey = x, y + sign * KEY_D
        neck = box(x - KEY_NECK / 2, min(y, ey), z, KEY_NECK, KEY_D, h)
    return body, [cyl(x, y, z, KEY_SEAT_R, h), cyl(ex, ey, z, KEY_ENTRY_R, h), neck]


def stud(x, y, t):
    """Seta que cuelga de la cara interior de la tapa. Con la tapa impresa boca abajo crece hacia arriba."""
    z = H - t - .25
    return [cyl(x, y, z, STUD_R, t + .25), cone(x, y, z - 1.2, STUD_HEAD_R, STUD_R, 1.2), cyl(x, y, z - 2.0, STUD_HEAD_R, .8)]


def hook(x, y, nx, ny, ztop, width=6.0, t=1.2, lip=.6):
    """Gancho en voladizo desde el piso, por fuera del canto en (x, y) con normal exterior (nx, ny).
    La uña entra lip mm sobre la pieza, cuya cara superior está en ztop."""
    g = .25
    if nx:
        x0, x1 = sorted((x + nx * g, x + nx * (g + t)))
        l0, l1 = sorted((x - nx * lip, x + nx * g))
        return [box(x0, y - width / 2, FLOOR, x1 - x0, width, ztop + 1.2 - FLOOR), box(l0, y - width / 2, ztop + .15, l1 - l0, width, 1.05)]
    y0, y1 = sorted((y + ny * g, y + ny * (g + t)))
    l0, l1 = sorted((y - ny * lip, y + ny * g))
    return [box(x - width / 2, y0, FLOOR, width, y1 - y0, ztop + 1.2 - FLOOR), box(x - width / 2, l0, ztop + .15, width, l1 - l0, 1.05)]


def crush_ribs(x, y, z, depth, r):
    """Cuatro nervios de apriete dentro de un alojamiento de radio r + 0,15: dejan 0,3 mm menos que el imán."""
    return [box(x + dx * (r - .15) - (.3 if dy else 0) - (.6 if dx < 0 else 0), y + dy * (r - .15) - (.3 if dx else 0) - (.6 if dy < 0 else 0), z,
                .6, .6, depth) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]


PARTS = []      # {name, color, group, add:[prims], cut:[prims], meta}
WIRES = []      # {name, harness, color, dia, pts:[(x, y, z, 'b'|'l')]}
CONNECTORS = {} # nombre -> lista de terminales (x, y, z)
BOARD_PARTS = {k: [] for k in BOARDS}   # referencias montadas por tarjeta


def box(x, y, z, dx, dy, dz):
    return ("box", x, y, z, dx, dy, dz)


def cyl(x, y, z, r, h, axis="z"):
    return ("cyl", x, y, z, r, h, axis)


def cone(x, y, z, r1, r2, h):
    """Tronco de cono vertical: radio r1 en z y r2 en z + h."""
    return ("cone", x, y, z, r1, r2, h)


def prismx(x, dx, pts):
    """Prisma a lo largo de x con perfil pts = [(y, z), ...]; sirve para cuñas a 45° que se imprimen sin soportes."""
    return ("prismx", x, dx, tuple(pts))


def hexp(x, y, z, af, h):
    """Prisma hexagonal vertical; af = distancia entre caras, con dos caras mirando a +/-x."""
    return ("hex", x, y, z, af, h)


def stadium(x, y, z, dx, dy, dz):
    """Prisma con los dos extremos semicirculares (largo en x)."""
    r = dy / 2
    return [box(x + r, y, z, dx - 2 * r, dy, dz), cyl(x + r, y + r, z, r, dz), cyl(x + dx - r, y + r, z, r, dz)]


def rrect(x, y, z, dx, dy, dz, r, eps=0.0):
    """Prisma de esquinas redondeadas como unión de dos cajas y cuatro cilindros."""
    return [box(x + r, y, z, dx - 2 * r, dy, dz), box(x, y + r, z, dx, dy - 2 * r, dz)] + \
           [cyl(x + (r if i else dx - r), y + (r if j else dy - r), z - eps, r, dz + 2 * eps) for i in (0, 1) for j in (0, 1)]


def part(name, color, prims, group="interior", cut=None, **meta):
    PARTS.append({"name": name, "color": color, "group": group,
                  "add": list(prims), "cut": list(cut or []), "meta": meta})


def bxy(board, u, v):
    x, y = BOARDS[board][:2]
    return x + u, y + v


# ------------------------------------------------------------------ componentes de tarjeta
class Board:
    """Acumula primitivas por tipo para no crear cientos de objetos CAD."""

    def __init__(self, ref):
        self.ref = ref
        self.acc = {}
        self.refs = []

    def put(self, kind, color, prims, refs=()):
        self.acc.setdefault((kind, color), []).extend(prims)
        self.refs += list(refs)

    def dip(self, ref, u, v, pins=14):
        x, y = bxy(self.ref, u, v)
        n = pins // 2
        L = n * 2.54 + 1.5
        self.put("Zocalos_DIP", "socket", [box(x - L / 2, y - 5.1, ZT, L, 10.2, 4.2)], [f"zócalo {ref}"])
        self.put("Integrados_DIP", "chip", [box(x - L / 2 + .4, y - 3.3, ZT + 4.2, L - .8, 6.6, 3.4)], [ref])
        self.put("Muescas_DIP", "metal", [cyl(x - L / 2 + 1.6, y, ZT + 7.55, 0.9, 0.12)])

    def res(self, ref, u, v, rot=0):
        x, y = bxy(self.ref, u, v)
        ax = "x" if rot == 0 else "y"
        sx, sy = (1, 0) if rot == 0 else (0, 1)
        self.put("Resistencias_1pct", "res", [cyl(x - 3.15 * sx, y - 3.15 * sy, ZT + 1.7, 1.2, 6.3, ax)], [ref])
        self.put("Terminales_axiales", "metal", [cyl(x - 5.08 * sx, y - 5.08 * sy, ZT + 1.7, 0.3, 10.16, ax)])

    def diode(self, ref, u, v, rot=0):
        x, y = bxy(self.ref, u, v)
        ax = "x" if rot == 0 else "y"
        sx, sy = (1, 0) if rot == 0 else (0, 1)
        self.put("Diodos_1N4148", "diode", [cyl(x - 1.9 * sx, y - 1.9 * sy, ZT + 1.3, 0.9, 3.8, ax)], [ref])
        self.put("Terminales_axiales", "metal", [cyl(x - 3.81 * sx, y - 3.81 * sy, ZT + 1.3, 0.25, 7.62, ax)])

    def film(self, ref, u, v, rot=0, t=3.0, h=7.0, L=7.2):
        x, y = bxy(self.ref, u, v)
        dx, dy = (L, t) if rot == 0 else (t, L)
        self.put("Capacitores_pelicula", "film", [box(x - dx / 2, y - dy / 2, ZT + .6, dx, dy, h)], [ref])

    def cer(self, ref, u, v, rot=0):
        x, y = bxy(self.ref, u, v)
        dx, dy = (4.6, 2.4) if rot == 0 else (2.4, 4.6)
        self.put("Capacitores_ceramicos", "cer", [box(x - dx / 2, y - dy / 2, ZT + 1.0, dx, dy, 4.2)], [ref])

    def elec(self, ref, u, v, d=5.0, h=11.0):
        x, y = bxy(self.ref, u, v)
        self.put("Electroliticos", "elec", [cyl(x, y, ZT + .3, d / 2, h)], [ref])
        self.put("Tapas_electroliticos", "metal", [cyl(x, y, ZT + .3 + h, d / 2 - .5, 0.15)])

    def xh(self, name, u, v, n, vertical=False):
        """Cabezal JST-XH de n vías con su carcasa enchufada. Devuelve terminales."""
        x, y = bxy(self.ref, u, v)
        L = (n - 1) * 2.5 + 4.9
        dx, dy = (5.75, L) if vertical else (L, 5.75)
        self.put("Cabezales_XH", "xh", [box(x - dx / 2, y - dy / 2, ZT, dx, dy, 7.0)], [name])
        px, py = (dx - 1.6, dy - 1.2) if vertical else (dx - 1.2, dy - 1.6)
        self.put("Carcasas_XH", "w_white", [box(x - px / 2, y - py / 2, ZT + 7.0, px, py, 3.2)])
        pins = []
        for i in range(n):
            o = (i - (n - 1) / 2) * 2.5
            pins.append((x, y + o, ZT + 10.2) if vertical else (x + o, y, ZT + 10.2))
        CONNECTORS[f"{self.ref}.{name}"] = pins
        return pins

    def header(self, name, u, v, n, vertical=False):
        x, y = bxy(self.ref, u, v)
        L = n * 2.54
        dx, dy = (2.54, L) if vertical else (L, 2.54)
        self.put("Headers_2p54", "header", [box(x - dx / 2, y - dy / 2, ZT, dx, dy, 8.5)], [name])
        pins = []
        for i in range(n):
            o = (i - (n - 1) / 2) * 2.54
            pins.append((x, y + o, ZT + 8.5) if vertical else (x + o, y, ZT + 8.5))
        CONNECTORS[f"{self.ref}.{name}"] = pins
        return pins

    def pads(self, name, u, v, n, pitch=2.54, vertical=False):
        """Islas de soldadura para cables que llegan directo a la tarjeta."""
        x, y = bxy(self.ref, u, v)
        pins = []
        for i in range(n):
            o = (i - (n - 1) / 2) * pitch
            p = (x, y + o, ZT + .35) if vertical else (x + o, y, ZT + .35)
            pins.append(p)
            self.put("Puntos_de_soldadura", "metal", [cyl(p[0], p[1], ZT, 0.9, 0.7)])
        CONNECTORS[f"{self.ref}.{name}"] = pins
        return pins

    def flush(self):
        for (kind, color), prims in self.acc.items():
            part(f"{self.ref}_{kind}", color, prims)
        BOARD_PARTS[self.ref] = self.refs


# Dos ganchos por tarjeta, en los cantos oeste (-1) y este (+1): (fracción del fondo, lado).
BOARD_HOOKS = {"T1": [(.3, -1), (.5, 1)], "T2": [(.5, -1), (.5, 1)], "T3": [(.5, -1), (.5, 1)], "T4": [(.5, -1), (.8, 1)]}


def build_boards():
    posts, hooks = [], []
    for ref, (x, y, w, d, label) in BOARDS.items():
        holes = [(x + 3.5, y + 3.5), (x + w - 3.5, y + 3.5), (x + 3.5, y + d - 3.5), (x + w - 3.5, y + d - 3.5)]
        part(f"{ref}_Perforada_{int(w)}x{int(d)}", "perf", [box(x, y, Z_BOARD, w, d, T_PCB)],
             cut=[cyl(hx, hy, Z_BOARD - .5, 1.6, 3) for hx, hy in holes], board=ref, label=label)
        for hx, hy in holes:
            posts.append(cyl(hx, hy, FLOOR, 3.0, Z_BOARD - FLOOR))
            posts.append(cyl(hx, hy, Z_BOARD, 1.35, T_PCB))              # pin al ras que centra la tarjeta por su agujero
        for fx_, nx in BOARD_HOOKS[ref]:
            hooks += hook(x + (w if nx > 0 else 0), y + d * fx_, nx, 0, ZT)
    part("Postes_con_pin_tarjetas", "support", posts, group="body", fundir="cuerpo")
    part("Ganchos_de_presion_tarjetas", "support", hooks, group="body", fundir="cuerpo")

    # ---- T1: alimentación analógica, VREF, entrada, preamplificador, graves, pasa-altas de medios
    b = Board("T1")
    b.dip("U1 LM324", 45, 36)
    for i, r in enumerate(range(1, 7)):
        b.res(f"R{r}", 14 + i * 11.4, 54)
    for i, r in enumerate(range(7, 13)):
        b.res(f"R{r}", 14 + i * 11.4, 20)
    b.elec("C1 100uF", 14, 64, 6.3, 11)
    b.elec("C8 10uF", 26, 64)
    b.elec("C10 10uF bipolar", 36, 64)
    b.film("C9 1uF", 48, 64, t=5.0, h=10.0)
    for i, c in enumerate(("C11 100nF", "C12 47nF", "C13 10nF", "C14 10nF")):
        b.film(c, 22 + i * 12, 28.5)
    b.cer("C2 100nF", 60, 64)
    b.cer("C4 100nF", 45, 44.5)
    jx, jy = bxy("T1", 0, 45)
    part("T1_J1_Jack_PJ313D_entrada", "jack", [box(jx, jy - 6, ZT, 12, 12, 5.2), cyl(jx - 3.0, jy, ZT + 2.6, 2.5, 3.2, "x")])
    b.refs.append("J1")
    b.pads("RV1", 53.5, 3.0, 3, 5.0)
    b.xh("JAB", 85.5, 45, 4, vertical=True)
    b.xh("JBUS", 76, 66, 4)
    b.pads("PWR", 62, 66.5, 2, 5.08)
    b.flush()

    # ---- T2: pasa-bajas de medios, agudos, sumador, salida y antialiasing
    b = Board("T2")
    b.dip("U2 LM324", 52, 40)
    for i, r in enumerate((13, 14, 15, 16, 19, 20)):
        b.res(f"R{r}", 22 + i * 11.4, 58)
    for i, r in enumerate((21, 22, 23, 24, 25, 26)):
        b.res(f"R{r}", 22 + i * 11.4, 24)
    for i, c in enumerate(("C15 10nF", "C16 4.7nF", "C17 10nF", "C18 10nF", "C20 4.7nF", "C21 2.2nF")):
        b.film(c, 22 + i * 11.4, 66.5)
    b.cer("C5 100nF", 52, 48.5)
    b.elec("C19 10uF", 40, 14)
    b.elec("C3 470uF", 88, 16, 8.0, 12.0)
    jx, jy = bxy("T2", 60, 0)
    part("T2_J2_Jack_PJ313D_salida_linea", "jack", [box(jx - 6, jy, ZT, 12, 12, 5.2), cyl(jx, jy - 3.0, ZT + 2.6, 2.5, 3.2, "y")])
    b.refs.append("J2")
    j3 = b.header("J3", 107.5, 33.5, 4)
    px, py = bxy("T2", 97, 12)
    pam = M["PAM8403"]["envolvente"]
    part("T2_PAM8403_modulo_sobre_J3", "pam", [box(px, py, ZT + 2.6, pam[0], pam[1], 1.6)])
    part("T2_PAM8403_CI_y_bobinas", "chip", [box(px + 6.5, py + 6, ZT + 4.2, 6, 4, 1.6),
                                              box(px + 15, py + 3, ZT + 4.2, 3.5, 3.5, 2.2), box(px + 15, py + 11, ZT + 4.2, 3.5, 3.5, 2.2)])
    part("T2_PAM8403_pines_de_montaje", "metal", [cyl(px + 2 + i * 2.54, py + 1.5, ZT, .35, 2.6) for i in range(5)] +
         [cyl(px + 2 + i * 2.54, py + pam[1] - 1.5, ZT, .35, 2.6) for i in range(4)])
    CONNECTORS["T2.PAM_SPK"] = [(px + pam[0] - 2, py + 1.5 + i * 2.54, ZT + 4.3) for i in range(4)]
    CONNECTORS["T2.PAM_PWR"] = [(px + pam[0] - 2, py + 12.5, ZT + 4.3), (px + pam[0] - 2, py + 15.5, ZT + 4.3)]
    b.refs.append("PAM8403")
    b.pads("RV2", 4.5, 4.0, 3, 2.54, vertical=False)
    b.pads("RV3", 34.0, 3.0, 3, 5.0)
    b.pads("RV4", 74.0, 3.0, 3, 5.0)
    b.pads("RV5", 114.0, 3.0, 3, 2.54, vertical=True)
    b.xh("JAB", 4.5, 45, 4, vertical=True)
    b.xh("JBC", 12, 76, 5)
    b.xh("JBUS", 78, 76, 4)
    b.xh("JB4", 100, 76, 2)
    b.pads("PWR", 115.5, 52, 2, 5.08, vertical=True)
    b.flush()

    # ---- T3: inversor de medios y detectores de pico
    b = Board("T3")
    b.dip("U3 LM324", 34, 42)
    b.dip("U4 LM324", 74, 42)
    b.cer("C6 100nF", 34, 50.5)
    b.cer("C7 100nF", 74, 50.5)
    b.res("R17", 68, 28)
    b.res("R18", 82, 28)
    for i in range(3):
        u = 22 + i * 30
        b.diode(f"D{i + 1}", u, 64)
        b.res(f"R{27 + i}", u + 12, 64)
        b.film(f"C{22 + i} 100nF", u + 5, 71.5)
    b.xh("JBC", 109, 5, 5)
    b.xh("JC4", 115.5, 30, 4, vertical=True)
    b.xh("JBUS", 115.5, 55, 4, vertical=True)
    b.pads("PWR", 90, 4.5, 2, 5.08)
    b.flush()

    # ---- T4: ESP32 DevKit V1 (30 pines), protección ADC, pantalla, pulsador y adaptación de la tira
    b = Board("T4")
    esp = M["ESP32-DevKit-V1-30P"]["envolvente"]        # 52 x 28,5 conservadora; hileras a 22,86 supuesto
    row_sep = M["ESP32-DevKit-V1-30P"]["separacion_centros_hileras"]
    ex, ey = bxy("T4", 120 - esp[0], 30)        # micro-USB al ras del borde derecho
    zs = ZT + 8.5
    sock_l = 15 * 2.54 + 1.5
    sock_x = ex + (esp[0] - sock_l) / 2
    row_y = (ey + (esp[1] - row_sep) / 2, ey + (esp[1] + row_sep) / 2)
    part("T4_Zocalos_hembra_1x15_ESP32", "header", [box(sock_x, row_y[0] - 1.27, ZT, sock_l, 2.54, 8.5),
                                                      box(sock_x, row_y[1] - 1.27, ZT, sock_l, 2.54, 8.5)])
    part("T4_U5_ESP32_DevKitV1_PCB_52x28p5", "esp", [box(ex, ey, zs, esp[0], esp[1], 1.6)])
    part("T4_U5_DevKitV1_blindaje_RF", "metal", [box(ex + 7, ey + 5.3, zs + 1.6, 18, 18, 3.2)])
    part("T4_U5_DevKitV1_antena", "chip", [box(ex, ey + 5.3, zs + 1.6, 6.5, 18, 0.8)])
    part("T4_U5_DevKitV1_micro_USB", "metal", [box(ex + esp[0] - 5.2, ey + esp[1] / 2 - 4.0, zs + 1.6, 6.0, 8.0, 2.8)])
    part("T4_U5_DevKitV1_pulsadores_EN_BOOT", "chip", [box(ex + esp[0] - 9, ey + 3.0, zs + 1.6, 4, 3.5, 2.2),
                                                       box(ex + esp[0] - 9, ey + 22.0, zs + 1.6, 4, 3.5, 2.2)])
    part("T4_U5_DevKitV1_CP2102_y_regulador", "chip", [box(ex + 32, ey + 11, zs + 1.6, 5, 5, 1.0), box(ex + 39, ey + 13, zs + 1.6, 6.5, 3.5, 1.6)])
    b.refs += ["U5 ESP32 DevKit V1 30P", "zócalos 1x15 x2"]
    global USB_C
    USB_C = (ex + esp[0] + .8, ey + esp[1] / 2, zs + 3.0)
    b.dip("U6 74HCT245", 26, 50, pins=20)
    b.cer("C25 100nF", 26, 58.5)
    for i in range(8):
        b.res(f"R{33 + i}", 53, 24 + i * 5.08)
    for i, r in enumerate((30, 31, 32)):
        b.res(f"R{r}", 16 + i * 11.4, 36)
    b.elec("C26 1000uF", 100, 18, 10.0, 17.0)
    b.xh("JBUS_T1", 12, 5, 4)
    b.xh("JBUS_T2", 30, 5, 4)
    b.xh("JB4", 52, 5, 2)
    b.pads("SW1", 62, 4.5, 2)
    b.header("J5", 71, 5, 3)
    b.header("J7_pantalla_5V_y_UART_PROPUESTO", 88, 5, 4)
    b.xh("JBUS_T3", 4.5, 55, 4, vertical=True)
    b.xh("JC4", 4.5, 30, 4, vertical=True)
    x6, y6 = bxy("T4", 112, 6.5)
    part("T4_J6_Bornera_2P_5p08_entrada_5V", "terminal", [box(x6 - 5.1, y6 - 4, ZT, 10.2, 8, 10)])
    part("T4_J6_tornillos", "metal", [cyl(x6 - 2.54, y6, ZT + 10, 1.6, .3), cyl(x6 + 2.54, y6, ZT + 10, 1.6, .3)])
    CONNECTORS["T4.J6"] = [(x6 - 2.54, y6 - 4, ZT + 4), (x6 + 2.54, y6 - 4, ZT + 4)]
    b.refs.append("J6")
    b.flush()


PARTS_SCREWS = []
USB_C = None

# ------------------------------------------------------------------ zona de alimentación (frente derecho)
BLOCK = M["Bornera-puente-8P"]["envolvente"]       # largo, ancho, alto
BLK_Y0 = 26.0
BLK_P_X, BLK_N_X = 232.5, 245.5
ENTRY = (W - WALL, 20.0, 30.0)                      # pasacable del cable de la fuente externa
SWITCH = (W - WALL, 40.0, 26.0, 19.0, 13.0, 19.0)   # pared, y0, z0, largo y, alto z, fondo
_F = M["Portafusible-CON-183AC"]["envolvente"]
FUSE = (268.0, 6.0, FLOOR + _F["diametro"] / 2 + .4, _F["largo"], _F["diametro"] / 2)                # x, y0, z, largo, radio
BOOST = (257.0, 61.0, 17.0, 37.0)                   # x0, y0, ancho, largo (envolvente MT3608)


def block_term(x0, k, side):
    """Terminal k (0..7) de una bornera puente; side = -1 oeste, +1 este."""
    pitch = BLOCK[0] / 8
    return (x0 + BLOCK[1] / 2 + side * (BLOCK[1] / 2 + .3), BLK_Y0 + pitch * (k + .5), FLOOR + 7.0)


def build_power():
    for name, x0, col in (("Bornera_puente_8P_verde_rotulada_+5V", BLK_P_X, "terminal"), ("Bornera_puente_8P_verde_rotulada_GND", BLK_N_X, "terminal")):
        part(name, col, [box(x0, BLK_Y0, FLOOR, BLOCK[1], BLOCK[0], BLOCK[2])], estado="compra verificada; cota conservadora")
        part(name + "_rotulo", "block_p" if "+5V" in name else "block_n", [box(x0 + 1.5, BLK_Y0 - 6.5, FLOOR, BLOCK[1] - 3, 4.0, 5.0)])
        pitch = BLOCK[0] / 8
        part(name + "_tornillos", "metal", [cyl(x0 + BLOCK[1] / 2, BLK_Y0 + pitch * (k + .5), FLOOR + BLOCK[2], 2.0, .4) for k in range(8)])
    seat = []
    for x0 in (BLK_P_X, BLK_N_X):
        xm = x0 + BLOCK[1] / 2
        seat += hook(xm, BLK_Y0, 0, -1, FLOOR + BLOCK[2], width=5.0, t=1.4, lip=.8) + hook(xm, BLK_Y0 + BLOCK[0], 0, 1, FLOOR + BLOCK[2], width=5.0, t=1.4, lip=.8)
    for xr in (BLK_P_X - 1.45, (BLK_P_X + BLOCK[1] + BLK_N_X) / 2 - .75, BLK_N_X + BLOCK[1] + .25):      # guías laterales bajas
        seat += [box(xr, BLK_Y0 + o, FLOOR, 1.2 if xr != (BLK_P_X + BLOCK[1] + BLK_N_X) / 2 - .75 else 1.5, 5.0, 3.0) for o in (3.0, BLOCK[0] - 8.0)]
    part("Asiento_a_presion_borneras", "support", seat, "body", fundir="cuerpo")
    wy, y0, z0, ly, hz, depth = SWITCH
    part("Interruptor_general_5A_PENDIENTE_COMPRA", "pending", [box(wy - depth, y0, z0, depth, ly, hz)], estado="pendiente_compra")
    part("Interruptor_general_tecla", "chip", [box(W - .2, y0 + 1.5, z0 + 1.5, 3.2, ly - 3, hz - 3)], group="body")
    fx, fy, fz, fl, fr = FUSE
    part("Portafusible_CON183AC_5x20_fusible_rapido_3A", "socket", [cyl(fx, fy, fz, fr, fl, "y")])
    # Pinzas abiertas por arriba: el portafusible entra a presión pasando 0,7 mm por lado.
    part("Portafusible_pinzas_a_presion", "support", [box(fx - fr - 1.5, fy + o, FLOOR, 2 * fr + 3, 5.0, fz - FLOOR + 3.2) for o in (7.0, fl - 12.0)],
         "body", cut=[cyl(fx, fy - 1, fz, fr + .15, fl + 2, "y")], fundir="cuerpo")
    bx, by, bw_, bl = BOOST
    part("Elevador_5V_a_12V_tira_PENDIENTE_COMPRA", "pending", [box(bx, by, FLOOR + 3, bw_, bl, 1.6)],
         estado="pendiente_compra; la tira comprada es de 12 V")
    part("Elevador_5V_a_12V_bobina_y_trimmer", "chip", [box(bx + 4, by + 10, FLOOR + 4.6, 7, 7, 4), box(bx + 3, by + 24, FLOOR + 4.6, 10, 5, 5)])
    part("Elevador_5V_a_12V_asiento_a_presion", "support", [cyl(bx + 2.5, by + 2.5, FLOOR, 2.2, 3), cyl(bx + bw_ - 2.5, by + bl - 2.5, FLOOR, 2.2, 3),
                                                            box(bx + bw_ + .25, by + bl / 2 - 3, FLOOR, 1.2, 6.0, 5.0)]
         + hook(bx + bw_ / 2, by, 0, -1, FLOOR + 4.6, width=4.0, t=.9, lip=.4) + hook(bx + bw_ / 2, by + bl, 0, 1, FLOOR + 4.6, width=4.0, t=.9, lip=.4),
         group="body", fundir="cuerpo")
    part("Pasacable_fuente_externa_5V", "socket", [cyl(W - WALL - 2.5, ENTRY[1], ENTRY[2], 4.2, 7.5, "x")], group="body",
         cut=[cyl(W - WALL - 3, ENTRY[1], ENTRY[2], 2.6, 9, "x")])
    part("Cable_fuente_externa_5V_5A", "w_black", [cyl(W + 2.5, ENTRY[1], ENTRY[2], 2.5, 38, "x")], group="body")
    CONNECTORS["BOOST.IN"] = [(bx + 4, by + bl - 1.5, FLOOR + 4.8), (bx + bw_ - 4, by + bl - 1.5, FLOOR + 4.8)]
    CONNECTORS["BOOST.OUT"] = [(bx + 4, by + 1.5, FLOOR + 4.8), (bx + bw_ - 4, by + 1.5, FLOOR + 4.8)]


# ------------------------------------------------------------------ elementos montados en la tapa
def build_lid_parts():
    for ref, func, kind, x, estado, ind in CONTROLS:
        env = POT if kind == "B10K" else POT_A
        r_body, depth, shaft_len = env["diametro_cuerpo"] / 2, env["fondo_cuerpo"], env["largo_eje"]
        y = KNOB_Y
        tag = f"{ref}_{func}_{kind}_{'lineal' if kind == 'B10K' else 'log_PENDIENTE_COMPRA_candidato_P20K_sin_validar'}"
        col = "pot" if kind == "B10K" else "pot_pend"
        part(f"{tag}_cuerpo", col, [cyl(x, y, H - depth, r_body, depth)], "lid", ref=ref, tipo=kind, estado=estado, funcion=func)
        part(f"{ref}_buje_roscado_M7", "metal", [cyl(x, y, H, 3.5, LID + 4.0)], "lid")
        part(f"{ref}_tuerca_y_arandela", "metal", [cyl(x, y, H + LID, 5.6, 2.0)], "lid")
        lugs = []
        pins = []
        for i in (-1, 0, 1):
            lugs.append(box(x + i * 5.0 - .6, y - r_body - 5.5, H - 6.0, 1.2, 6.5, .5))
            pins.append((x + i * 5.0, y - r_body - 4.5, H - 6.0))
        part(f"{ref}_terminales", "metal", lugs, "lid")
        CONNECTORS[f"LID.{ref}"] = pins
        # Eje y perilla giran juntos: grupo propio para animarlos.
        g = f"knob:{ref}"
        z0 = H + LID + 2.6
        part(f"{ref}_eje_6mm", "metal", [cyl(x, y, H + LID + 2.0, 3.0, shaft_len - LID - 2.0)], g)
        part(f"Perilla_{func}_PENDIENTE_COMPRA", "knob", [cyl(x, y, z0, 9.6, 3.0), cyl(x, y, z0 + 3.0, 8.0, 12.5)], g,
             estado="pendiente_compra_local", ref=ref)
        part(f"Perilla_{func}_indicador", ind, [box(x - .8, y + 1.5, z0 + 15.5, 1.6, 6.6, .5), box(x - .8, y + 7.6, z0 + 3.0, 1.6, .7, 12.6)], g)

    # Pantalla: ESP32-3248S035 en vertical, con el módulo TFT al ras de la cara exterior y al ras
    # del extremo frontal del PCB. La franja de la antena WROOM (97,5 - 84 = 13,5 mm) queda bajo
    # la tapa, hacia las barras. Posiciones de USB, P1, TF y pulsadores: supuestas, por medir.
    # RETENCIÓN POR GANCHOS A PRESIÓN: el cristal medido cubre casi todo el ancho de la placa
    # (55,0 sobre 55,1), así que solo puede entrar en la ventana EN VERTICAL (0,25 mm de
    # holgura por lado: no hay sitio para inclinar ni correr la placa, lo que descarta las
    # uñas fijas con pestaña). Cuatro ganchos en voladizo fundidos con la tapa se flexionan
    # al bajar la placa y hacen clic sobre ella: dos frontales (en los huecos entre los
    # cuerpos de RV2/RV3 y RV3/RV4) y dos laterales sobre la franja trasera sin cristal.
    # Cada gancho nace dentro de una ranura de alivio en la tapa para ganar brazo de flexión.
    # Para retirar la placa: apartar los dos ganchos laterales con el dedo y levantarla.
    cx, cy = TFT_C
    x0_, y0_ = CYD_X0, CYD_Y0
    pw_, pd_ = CYD_PCB_W, CYD_PCB_L
    zt_ = Z_CYD_TOP                     # cara superior del PCB (el módulo sube desde aquí)
    zp = zt_ - CYD_PCB_T                # cara inferior del PCB
    part("CYD_3248S035_PCB_101p5x54p9", "tft_pcb", [box(x0_, y0_, zp, pw_, pd_, CYD_PCB_T)], "lid",
         estado="recibida; cotas publicadas, offset del modulo por medir")
    part("CYD_modulo_TFT_3p5_marco", "tft_marco", rrect(cx - CYD_MOD_W / 2, y0_ + CYD_MOD_OFF, zt_, CYD_MOD_W, CYD_MOD_L, CYD_MOD_T - .3, 1.5), "lid")
    part("CYD_tactil_cara_exterior", "screen",
         rrect(cx - CYD_MOD_W / 2 + .8, y0_ + CYD_MOD_OFF + .8, zt_ + CYD_MOD_T - .3, CYD_MOD_W - 1.6, CYD_MOD_L - 1.6, .3, 1.2, eps=.03), "lid")
    part("CYD_area_activa_320x480", "screen",
         [box(cx - TFT_ACTIVE[0] / 2, cy - TFT_ACTIVE[1] / 2, zt_ + CYD_MOD_T - .28, TFT_ACTIVE[0], TFT_ACTIVE[1], .32)], "lid",
         emisor=True)
    # Cara inferior (hacia el interior): WROOM con antena en la franja trasera, micro-USB al
    # frente, ranura TF en el canto derecho y P1 (serie, 4 vías) en la franja trasera.
    part("CYD_ESP_WROOM_32_blindaje", "metal", [box(cx - 9, y0_ + 5.0, zp - 3.2, 18, 12.4, 3.2)], "lid")
    part("CYD_antena_WROOM", "chip", [box(cx - 9, y0_ + .5, zp - .8, 18, 4.0, .8)], "lid")
    # Franja trasera (la del extremo sin cristal, según la foto del comprador): agujeros de
    # montaje, micro-USB y USB-C apuntando hacia atrás (sobresalen ~1,2 mm del canto) y P1.
    part("CYD_micro_USB", "metal", [box(cx - 11.0, y0_ + pd_ - 6.0, zp - 2.8, 8.0, 7.2, 2.8)], "lid")
    part("CYD_USB_C", "metal", [box(cx + 1.0, y0_ + pd_ - 6.0, zp - 3.2, 9.0, 7.2, 3.2)], "lid")
    part("CYD_pulsadores_RST_BOOT", "chip", [box(x0_ + 8, y0_ + pd_ - 10.0, zp - 2.0, 4, 3.5, 2.0),
                                             box(x0_ + 14, y0_ + pd_ - 10.0, zp - 2.0, 4, 3.5, 2.0)], "lid")
    part("CYD_ranura_TF", "metal", [box(x0_ + pw_ - 13.5, y0_ + pd_ - 26.0, zp - 2.0, 14.5, 12.0, 2.0)], "lid")
    part("CYD_P1_conector_serie_4v", "xh", [box(cx + 14.0, y0_ + pd_ - 12.5, zp - 3.4, 7.4, 4.5, 3.4)], "lid")
    pins = [(cx + 15.9 + i * 1.25, y0_ + pd_ - 10.2, zp - 3.0) for i in range(4)]
    CONNECTORS["LID.TFT"] = pins
    # Los cuatro ganchos. Cada uno: raíz dentro de su ranura de alivio (cortada en lid_cuts,
    # 0,2 mm de holgura alrededor para que flexione), hoja de 1,2 mm hasta el plano de la
    # placa y uña de 0,5 mm que la retiene con 0,1 mm de holgura. Los frontales llevan una
    # rampa a 45° para que el canto de la placa los apart e al bajar.
    hooks = []
    zu_ = zp - .15                      # cara superior de la uña: 0,15 bajo la placa
    for hx_ in (112.0, 160.0):          # ganchos frontales (huecos entre potenciómetros)
        hooks += [box(hx_, 31.1, H - .01, 8.0, 1.2, 2.5),                 # raíz: 0,5 mm anclados sobre la ranura
                  box(hx_, 31.1, zu_ - .5, 8.0, 1.2, H - zu_ + .5),       # hoja (0,4 por delante de la placa)
                  box(hx_ + 1.0, 32.3, zu_ - .5, 6.0, .9, .5),            # uña: 0,7 bajo la placa
                  prismx(hx_ + 1.0, 6.0, [(32.3, zu_ - .5), (33.2, zu_ - .5), (32.3, zu_ - 1.4)])]  # rampa
    for bx0_, lipx_ in ((x0_ - 1.6, x0_ - .4), (x0_ + pw_ + .4, x0_ + pw_ - .5)):
        # ganchos laterales sobre la franja trasera sin cristal
        hooks += [box(bx0_, 121.8, H - .01, 1.2, 6.5, 2.5),
                  box(bx0_, 121.8, zu_ - .5, 1.2, 6.5, H - zu_ + .5),
                  box(lipx_, 122.8, zu_ - .5, .9, 4.5, .5)]
    part("Ganchos_pantalla_CYD", "support", hooks, "lid", fundir="tapa")
    # Conjunto WS-14595: dos parlantes de 8 ohm / 5 W en un solo conector.
    sw_, sd_, sh_ = SPK
    retain = []
    for n, (sx, sy) in enumerate(SPK_CS, 1):
        tag = f"Parlante_{n}de2_WS14595_8ohm_5W"
        part(f"{tag}_marco_100x45", "speaker", [box(sx - sw_ / 2, sy - sd_ / 2, H - 2.0, sw_, sd_, 2.0)], "lid")
        part(f"{tag}_canasta", "speaker", [box(sx - sw_ / 2 + 8, sy - sd_ / 2 + 4, H - 11.0, sw_ - 16, sd_ - 8, 9.0)], "lid")
        part(f"{tag}_iman", "metal", [cyl(sx, sy, H - sh_, 15.0, sh_ - 11.0)], "lid")
        part(f"{tag}_cono", "cone", [box(sx - sw_ / 2 + 5, sy - sd_ / 2 + 4, H - .5, sw_ - 10, sd_ - 8, .5)], "lid")
        # Sin tornillos: el canto delantero entra bajo dos cuñas de la tapa y el trasero lo atrapan las
        # cuñas de la cuna de GRAVES al correrla. Dos topes fijan el parlante en x.
        yl = sy - sd_ / 2 - SPK_WEDGE
        retain += [prismx(sx + o - 7, 14.0, [(yl - 1.8, H), (yl, H), (yl + 3.8, H - 3.8), (yl + 3.8, H - 5.3), (yl - 1.8, H - 5.3)]) for o in (-30.0, 30.0)]
        retain += [box(sx - sw_ / 2 - 1.9, sy - 6, H - 2.0, 1.6, 12, 2.0), box(sx + sw_ / 2 + .3, sy - 6, H - 2.0, 1.6, 12, 2.0)]
        CONNECTORS[f"LID.SPK{n}"] = [(sx - 3, sy - sd_ / 2 + 6, H - 11.5), (sx + 3, sy - sd_ / 2 + 6, H - 11.5)]
    px, py = SPK_PLUG
    part("Conector_unico_parlantes_WS14595", "xh", [box(px - 6, py - 4, H - 7.5, 12, 8, 6.0)], "lid")
    part("Parlantes_cunas_y_topes_de_la_tapa", "support", retain, "lid", fundir="tapa")
    adds, cuts = [box(px - 8, py - 4, H - 9.5, 16, 8, 2.0), box(px - 8, py - 4, H - 9.5, 1.5, 8, 9.5), box(px + 6.5, py - 4, H - 9.5, 1.5, 8, 9.5)], []
    for ex_ in (px - 8 - EAR_W / 2, px + 8 + EAR_W / 2):
        b_, c_ = ear(ex_, py - 4 + EAR_BACK, "y", 1)
        adds.append(b_); cuts += c_
    part("Cuna_conector_parlantes", "support", adds, "lid", cut=cuts, pieza_impresa=True)
    CONNECTORS["LID.SPK_PLUG_IN"] = [(px - 3.75 + i * 2.5, py + 4, H - 4.5) for i in range(4)]
    CONNECTORS["LID.SPK_PLUG_OUT"] = [(px - 3.75 + i * 2.5, py - 4, H - 4.5) for i in range(4)]
    # SW1 en cuna, con capuchón a través de la tapa.
    bx, by = SW_C
    part("SW1_pulsador_6x6_en_cuna", "chip", [box(bx - 3, by - 3, H - 6.5, 6, 6, 3.5)], "lid")
    adds = [box(bx - 6.7, by - 6, H - 8.5, 13.4, 12, 2.0), box(bx - 6.7, by - 6, H - 8.5, 1.5, 12, 8.5), box(bx + 5.2, by - 6, H - 8.5, 1.5, 12, 8.5),
            box(bx - 3.1, by - 4.3, H - 6.5, 6.2, 1.0, 1.2), box(bx - 3.1, by + 3.3, H - 6.5, 6.2, 1.0, 1.2)]
    cuts = []
    for ex_ in (bx - 6.7 - EAR_W / 2, bx + 6.7 + EAR_W / 2):
        b_, c_ = ear(ex_, by - 6.5 + EAR_BACK, "y", 1)
        adds.append(b_); cuts += c_
    part("Cuna_SW1", "support", adds, "lid", cut=cuts, pieza_impresa=True)
    # El capuchón lleva un reborde en la base: no puede salirse por fuera de la tapa y se imprime sin voladizos.
    part("SW1_capuchon_VISTA", "knob_neutral", [cyl(bx, by, H - 3.0, 3.6, LID + 4.4), cyl(bx, by, H - 3.0, 4.8, 1.0)], "button", pieza_impresa=True)
    CONNECTORS["LID.SW1"] = [(bx - 2.5, by - 4.2, H - 7.5), (bx + 2.5, by - 4.2, H - 7.5)]
    # Tres barras FCOB WS2811 de 12 V: 4 píxeles de 50 mm por banda.
    for i, (name, y, col) in enumerate(BARS):
        x0 = BAR_X0
        zs = H - 8.0
        # Cuna: se corre en +x sobre dos setas. Las paredes llegan a la tapa por fuera y dejan un escalón
        # de 0,8 mm que aprieta la pestaña del difusor. Se imprime boca abajo (cara de la tapa en la cama).
        yw = STRIP_W / 2 + .4
        adds = [box(x0 - 3, y - yw - 1.6, zs - 2.0, BAR_LEN + 6, 2 * yw + 3.2, 2.0)]
        for o in (-1, 1):
            segs = [(x0 - 3, BAR_LEN + 6)]
            if i == 0 and o < 0:
                # Las paredes frontales de GRAVES se interrumpen sobre la franja trasera del PCB
                # de la pantalla 3,5" (x 110,75..167,25): la placa pasa por debajo de la cuna y
                # esta, al montarse, le bloquea el deslizamiento de salida.
                segs = [(x0 - 3, 107.0 - (x0 - 3)), (171.0, x0 + BAR_LEN + 3 - 171.0)]
            for sx0, sdx in segs:
                adds += [box(sx0, y + (yw + .8 if o > 0 else -yw - 1.6), zs, sdx, .8, 8.0),
                         box(sx0, y + (yw if o > 0 else -yw - .8), zs, sdx, .8, 8.0 - HEX_FLANGE)]
            adds += [box(x0 - 5, y + (yw - 1.4 if o > 0 else -yw - 1.6), zs - 2.0, 2.0, 3.0, 10.0), box(x0 + BAR_LEN + 3, y + (yw - 1.4 if o > 0 else -yw - 1.6), zs - 2.0, 2.0, 3.0, 10.0)]
            adds += [box(x0 + 8 + k * 46.0, y + (yw - .7 if o > 0 else -yw), zs + 1.0, 12.0, .7, .8) for k in range(5)
                     if not (i == 0 and o < 0 and k == 2)]     # uñas que retienen la tira (la central frontal de GRAVES cae en el hueco de la pantalla)
        cuts = []
        for seat_x in (x0 - 5 - EAR_FRONT, x0 + BAR_LEN + 3 + EAR_BACK):
            b_, c_ = ear(seat_x, y, "x", 1, width=2 * yw + 3.2)
            adds.append(b_); cuts += c_
        if i == 0:                       # cuñas a 45° que atrapan el canto trasero de los dos parlantes
            yr = SPK_CS[0][1] + SPK[1] / 2 + SPK_WEDGE
            for xt in (36.0, 88.0, 176.0, 206.0):
                adds.append(prismx(xt, 12.0, [(y - yw - 1.5, H), (yr, H), (yr - 3.8, H - 3.8), (yr - 3.8, H - 5.5), (y - yw - 1.5, H - 5.5)]))
        part(f"Cuna_tira_{name}", "support", adds, "lid", cut=cuts, pieza_impresa=True)
        part(f"Tira_FCOB_WS2811_12V_{name}_4px_200mm", "strip", [box(x0, y - STRIP_W / 2, zs, BAR_LEN, STRIP_W, .5)], "lid",
             pixeles=PX_PER_BAND, paso_mm=PIXEL, banda=name)
        part(f"Luz_{name}", col, [box(x0 + k * PIXEL + .6, y - 2.5, zs + .5, PIXEL - 1.2, 5.0, 1.3) for k in range(PX_PER_BAND)], "lid",
             emisor=True, banda=name)
        part(f"Pads_de_corte_{name}", "pad", [box(x0 + k * PIXEL - 1.0, y + o - 1.0, zs + .5, 2.0, 2.0, .1)
                                             for k in range(PX_PER_BAND + 1) for o in (-4.0, 0.0, 4.0)], "lid")
        # Difusor impreso con relieve hexagonal (idea del "3DHex" de Duality, geometría propia): pestaña
        # apretada entre la cuna y la tapa, marco hueco que cruza la ventana y lámina superior al ras.
        # Fondo de cada hexágono 0,5 mm, nervio 1,1 mm; el patrón se repite cada 25 mm (medio píxel).
        hw = HEX_WIN / 2
        # Extremos semicirculares: la ventana, el marco y la cavidad son "píldoras" concéntricas.
        cav = (x0 - .1, y - hw + .9, BAR_LEN + .2, HEX_WIN - 1.8)          # x, y, largo, ancho de la cavidad
        rc, rh = cav[3] / 2, (HEX_PITCH - HEX_RIB) / 3 ** .5               # radio de cavidad y de cada celda

        def inside(hx, hy):          # la celda completa cabe en la cavidad, con 0,1 mm de margen al borde
            ax = min(max(hx, cav[0] + rc), cav[0] + cav[2] - rc)
            return math.hypot(hx - ax, hy - y) + rh <= rc - .1

        centers = [(x0 + (k + .5 * r) * HEX_PITCH, y + (r - .5) * HEX_PITCH * 3 ** .5 / 2) for r in (0, 1) for k in range(int(BAR_LEN / HEX_PITCH) + 1 - r)]
        pockets = [hexp(hx, hy, H + LID - (HEX_RIB - HEX_FLOOR), HEX_PITCH - HEX_RIB, 1.0) for hx, hy in centers if inside(hx, hy)]
        part(f"Difusor_opalino_{name}", "diffuser",
             [box(x0 - 3, y - yw - .7, H - HEX_FLANGE, BAR_LEN + 6, 2 * yw + 1.4, HEX_FLANGE)]
             + stadium(x0 - .9, y - hw + .1, H, BAR_LEN + 1.8, HEX_WIN - .2, LID), "lid",
             cut=stadium(cav[0], cav[1], H - HEX_FLANGE - .1, cav[2], cav[3], LID + HEX_FLANGE + .1 - HEX_RIB) + pockets,
             pieza_impresa=True, difusor=True, banda=name, patron="hexagonal en relieve", paso_mm=HEX_PITCH)
        # Entrada por la derecha en la barra 0 y 2; la barra 1 va invertida (serpentina).
        left = [(x0 + 1.0, y + o, zs + .6) for o in (-4.0, 0.0, 4.0)]
        right = [(x0 + BAR_LEN - 1.0, y + o, zs + .6) for o in (-4.0, 0.0, 4.0)]
        CONNECTORS[f"LID.BAR{i}.L"], CONNECTORS[f"LID.BAR{i}.R"] = left, right
    # Cierre magnético: cuatro pares de discos de neodimio, sin bisagras ni tornillos.
    r, t = IMAN["diametro"] / 2, IMAN["espesor"]
    ribs_body, ribs_lid = [], []
    for n, (mx, my) in enumerate(MAGNETS, 1):
        # El poste nace del piso; la ménsula frontal es una cartela a 45° pegada a la pared, sin voladizo plano.
        base = [cyl(mx, my, FLOOR, 4.5, H - 3.0 - FLOOR), box(mx - 3.0, my, FLOOR, 6.0, D - WALL - my + .3, H - 3.0 - FLOOR)] if my > 50 else [prismx(mx - 5.5, 11.0, [(WALL - .2, H - 3.0), (my + 4.7, H - 3.0), (my + 4.7, H - 8.0),
                                                                                                   (WALL - .2, H - 8.0 - (my + 4.9 - WALL))])]
        part(f"{'Poste' if my > 50 else 'Mensula_frontal'}_iman_{n}", "support", base, "body", cut=[cyl(mx, my, H - 3.0 - t - .2, r + .15, t + .3)], fundir="cuerpo")
        ribs_body += crush_ribs(mx, my, H - 3.0 - t - .2, t + .2, r)
        ribs_lid += crush_ribs(mx, my, H - 3.0, t + .2, r)
        part(f"Iman_cuerpo_{n}_6x2_PENDIENTE_COMPRA", "metal", [cyl(mx, my, H - 3.0 - t, r, t)], "body", estado="pendiente_compra")
        part(f"Teton_iman_tapa_{n}", "support", [cyl(mx, my, H - 3.0, 4.5, 3.0)], "lid", cut=[cyl(mx, my, H - 3.1, r + .15, t + .3)], fundir="tapa")
        part(f"Iman_tapa_{n}_6x2_PENDIENTE_COMPRA", "metal", [cyl(mx, my, H - 3.0, r, t)], "lid", estado="pendiente_compra")
    part("Nervios_de_apriete_imanes_cuerpo", "support", ribs_body, "body", fundir="cuerpo")
    # Refuerzos interiores de las paredes en la junta: alojan una cola de milano que no se ve por fuera.
    # Pilastras interiores de la junta, agrandadas para alojar las columnas-espiga de 10 mm de
    # cabeza (la trasera se detiene antes de la base del poste de imán en x 151).
    part("Refuerzos_de_la_junta", "support", [box(SEAM_X - 12, WALL - .2, FLOOR, 24, 8.5, Z_BOARD - .5 - FLOOR),
                                              box(SEAM_X - 12, D - WALL - 8.7, FLOOR, 23.5, 8.9, H - 4.0 - FLOOR)], "body", fundir="cuerpo_mitades", solo_mitades=True)
    part("Nervios_de_apriete_imanes_tapa", "support", ribs_lid, "lid", fundir="tapa")
    # Setas de la tapa para todas las orejas definidas arriba.
    part("Setas_de_encastre_de_la_tapa", "support", [q for sx_, sy_, t_ in LID_STUDS for q in stud(sx_, sy_, t_)], "lid", fundir="tapa")


# ------------------------------------------------------------------ cables
def wire(name, harness, color, pts, dia=1.3):
    clean = []
    for p in pts:
        p = (float(p[0]), float(p[1]), float(p[2]), p[3] if len(p) > 3 else "b")
        if not clean or math.dist(p[:3], clean[-1][:3]) > 0.05:
            clean.append(p)
    WIRES.append({"name": name, "harness": harness, "color": color, "dia": dia, "pts": clean})


def L(p):
    return (p[0], p[1], p[2], "l")


Y_WALL = 4.0            # bajada de los cables de tapa junto a la pared frontal
Z_LIDW = H - 1.3        # cables pegados a la cara interior de la tapa


def lid_drop(p_lid_pts, x_cross):
    """Tramo de tapa hasta el cruce por el borde frontal y primer punto en el cuerpo."""
    pts = [L(p) for p in p_lid_pts]
    pts.append((x_cross, 8.0, Z_LIDW, "l"))
    pts.append((x_cross, Y_WALL, H - 6.0, "b"))
    return pts


def hop(a, b, z=None, lift=4.0):
    """Cable corto entre dos terminales: sube, cruza y baja."""
    z = z if z is not None else max(a[2], b[2]) + lift
    return [a, (a[0], a[1], z), (b[0], b[1], z), b]


def build_wires():
    sig3 = ("w_white", "w_yellow", "w_violet")
    gnd3 = ("w_white", "w_yellow", "w_black")
    # --- potenciómetros: tres hilos soldados, cruce directo por la bisagra
    for ref, func, kind, x, estado, ind in CONTROLS:
        board = "T1" if ref == "RV1" else "T2"
        pads = CONNECTORS[f"{board}.{ref}"]
        cols = gnd3 if ref in ("RV1", "RV5") else sig3
        for i, lug in enumerate(CONNECTORS[f"LID.{ref}"]):
            pad = pads[i]
            pts = lid_drop([lug, (lug[0], lug[1] - 2.5, Z_LIDW)], lug[0])
            pts += [(pad[0], Y_WALL, ZT + 6.0), (pad[0], pad[1], ZT + 3.0), pad]
            wire(f"{ref}_{func}_pin{i + 1}", f"Arnes_{ref}_{func}_{kind}", cols[i], pts)
    # --- parlantes: arnés de fábrica hasta el conector único y cuatro hilos al PAM8403.
    #     El comprador confirmó cuatro conductores (dos rojos y dos negros): un parlante por canal, L+/L- y R+/R-.
    #     Falta identificar con multímetro qué par rojo/negro corresponde a cada parlante.
    pin = CONNECTORS["LID.SPK_PLUG_IN"]
    for n in (1, 2):
        for i, t in enumerate(CONNECTORS[f"LID.SPK{n}"]):
            k = (n - 1) * 2 + i
            yl = 69.5 - k * 1.5
            zl = Z_LIDW - 1.4
            wire(f"Parlante{n}_{'+-'[i]}", "Arnes_fabrica_parlantes_WS14595", ("w_red", "w_black")[i],
                 [L(t), (t[0], yl, zl, "l"), (pin[k][0], yl, zl, "l"), (pin[k][0], pin[k][1] + 2, pin[k][2], "l"), L(pin[k])])
    pads = CONNECTORS["T2.PAM_SPK"]
    for k, t in enumerate(CONNECTORS["LID.SPK_PLUG_OUT"]):
        xl = 196.5 + k * 1.5
        pad = pads[k]
        pts = lid_drop([t, (t[0], t[1] - 3, Z_LIDW), (xl, t[1] - 9, Z_LIDW)], xl)
        pts += [(xl, Y_WALL, ZT + 12), (pad[0] + 4 + k * .2, Y_WALL + 1, ZT + 9), (pad[0] + 4, pad[1], ZT + 7), pad]
        wire(f"Parlantes_a_PAM_{('L+', 'L-', 'R+', 'R-')[k]}", "Arnes_parlantes_a_PAM8403_4_hilos", ("w_red", "w_black", "w_red", "w_black")[k], pts)
    # --- troncal este (entre T2 y las borneras) hacia T4: alimentación de la pantalla, SW1 y tira
    trunk = []          # (nombre, arnés, color, puntos de tapa, x de cruce, destino)
    # Los DATOS viajan por ESP-NOW (decisión 2026-11-24): a la pantalla solo llegan +5 V y GND
    # por el pin VIN/GND de P1. El arnés sale bajo el PCB vertical, corre pegado a él por el
    # hueco entre RV3 y RV4 y sube a la cara interior de la tapa pasado el borde frontal del PCB.
    link_cols = ("w_red", "w_black")
    link_sig = ("+5V_a_VIN", "GND")
    for i in range(2):
        t = CONNECTORS["LID.TFT"][i]
        xl = 152.0 + i * 1.5
        zlow = 52.8 - i * .4
        trunk.append((f"CYD_{link_sig[i]}", "Arnes_alimentacion_pantalla_J7", link_cols[i],
                      [t, (t[0], t[1], zlow), (xl, t[1], zlow), (xl, 31.0, zlow), (xl, 29.0, Z_LIDW)], xl, CONNECTORS["T4.J7_pantalla_5V_y_UART_PROPUESTO"][i]))
    for i, t in enumerate(CONNECTORS["LID.SW1"]):
        xl = 252.5 + i * 1.5
        trunk.append((f"SW1_{('BTN', 'GND')[i]}", "Arnes_SW1", ("w_brown", "w_black")[i],
                      [t, (t[0], t[1] - 2, t[2]), (xl, 16.0, Z_LIDW)], xl, CONNECTORS["T4.SW1"][i]))
    bar_in = CONNECTORS["LID.BAR0.R"]
    j5 = CONNECTORS["T4.J5"]
    for i, (sig, col, dest) in enumerate((("DIN", "w_green", j5[1]), ("GND_ref", "w_black", j5[2]))):
        xl = 269.6 + i * 1.5
        t = bar_in[1 + i]
        trunk.append((f"Tira_{sig}", "Arnes_tira_J5", col,
                      [t, (xl, t[1], t[2]), (xl, t[1] - 9, Z_LIDW)], xl, dest))
    lanes_x = (226.3, 227.7, 229.1, 230.5)
    for k, (name, harness, col, lid_pts, xc, dest) in enumerate(trunk):
        lx, lz = lanes_x[k % 4], 4.3 + 1.45 * (k // 4)
        ly = 88.5 + 1.45 * (k % 4) + 5.0 * (k // 4 % 3 == 1)
        pts = lid_drop(lid_pts, xc)
        pts += [(xc, Y_WALL, lz), (lx, Y_WALL, lz), (lx, ly, lz), (dest[0], ly, lz), (dest[0], dest[1] - 5.5, lz),
                (dest[0], dest[1] - 5.5, dest[2] + 3), (dest[0], dest[1], dest[2] + 3), dest]
        wire(name, harness, col, pts)
    # --- 12 V de la tira: desde el elevador (pendiente) por la pared frontal
    for i, (o, col) in enumerate(zip(CONNECTORS["BOOST.OUT"], ("w_orange", "w_black"))):
        xl = 272.6 + i * 1.5
        t = bar_in[0] if i == 0 else bar_in[2]
        pts = lid_drop([(t[0], t[1], t[2] - 1.2 * i), (xl, t[1], t[2] - 1.2 * i), (xl, t[1] - 9, Z_LIDW)], xl)
        pts += [(xl, Y_WALL, 20.0), (260.0 - i * 1.6, Y_WALL, 5.0), (260.0 - i * 1.6, o[1] - 4, 5.0), (o[0], o[1] - 4, o[2] + 2), o]
        wire(f"Tira_{('+12V', 'GND')[i]}", "Arnes_tira_12V", col, pts, dia=1.5)
    # --- puentes en serpentina entre barras (12 V, datos, GND), sobre la cara interior de la tapa
    for a, b_, side, xo in ((0, 1, "L", -6.0), (1, 2, "R", 6.0)):
        pa, pb = CONNECTORS[f"LID.BAR{a}.{side}"], CONNECTORS[f"LID.BAR{b_}.{side}"]
        for i, col in enumerate(("w_orange", "w_green", "w_black")):
            p, q = pa[i], pb[i]
            x_out = p[0] + xo + (i - 1) * 1.4 * (1 if xo > 0 else -1)
            wire(f"Puente_barras_{a}{b_}_{i}", "Puentes_tira", col,
                 [L(p), (x_out, p[1], p[2] - 3.5, "l"), (x_out, q[1], q[2] - 3.5, "l"), L(q)])
    # --- arneses XH entre tarjetas
    cols4 = ("w_red", "w_black", "w_orange", "w_violet")
    for i in range(4):  # JAB: PRE, GRAVES, MED_HP, GND
        a, b_ = CONNECTORS["T1.JAB"][i], CONNECTORS["T2.JAB"][i]
        wire(f"JAB_{('PRE', 'GRAVES', 'MED_HP', 'GND')[i]}", "Arnes_JAB_T1_T2", ("w_white", "w_orange", "w_green", "w_black")[i], hop(a, b_, lift=3 + i * .9))
    for i in range(5):  # JBC
        a, b_ = CONNECTORS["T2.JBC"][i], CONNECTORS["T3.JBC"][i]
        wire(f"JBC_{('G_W', 'M_W', 'A_W', 'M_INV', 'GND')[i]}", "Arnes_JBC_T2_T3", ("w_orange", "w_green", "w_blue", "w_yellow", "w_black")[i], hop(a, b_, lift=3 + i * .9))
    for i in range(2):  # JB4
        a, b_ = CONNECTORS["T2.JB4"][i], CONNECTORS["T4.JB4"][i]
        wire(f"JB4_{('ADC_FFT_RAW', 'GND')[i]}", "Arnes_JB4_T2_T4", ("w_violet", "w_black")[i], hop(a, b_, lift=3 + i * .9))
    for i in range(4):  # JC4
        a, b_ = CONNECTORS["T3.JC4"][i], CONNECTORS["T4.JC4"][i]
        wire(f"JC4_{('ADC_G_RAW', 'ADC_M_RAW', 'ADC_A_RAW', 'GND')[i]}", "Arnes_JC4_T3_T4", ("w_orange", "w_green", "w_blue", "w_black")[i], hop(a, b_, lift=3 + i * .9))
    for i in range(4):  # JBUS x3 desde T4
        a, b_ = CONNECTORS["T4.JBUS_T3"][i], CONNECTORS["T3.JBUS"][i]
        wire(f"JBUS_T3_{('+5V', 'GND', '+3V3', 'VREF')[i]}", "Arnes_JBUS_T4_T3", cols4[i], hop(a, b_, lift=3 + i * .9))
        a, b_ = CONNECTORS["T4.JBUS_T2"][i], CONNECTORS["T2.JBUS"][i]
        wire(f"JBUS_T2_{('+5V', 'GND', '+3V3', 'VREF')[i]}", "Arnes_JBUS_T4_T2", cols4[i], hop(a, b_, lift=3 + i * .9))
        a, b_ = CONNECTORS["T4.JBUS_T1"][i], CONNECTORS["T1.JBUS"][i]
        ly = 98.4 - i * 1.4
        zl = ZT + 14 + i * .8
        wire(f"JBUS_T1_{('+5V', 'GND', '+3V3', 'VREF')[i]}", "Arnes_JBUS_T4_T1", cols4[i],
             [a, (a[0], a[1], zl), (a[0], ly, zl), (b_[0], ly, zl), (b_[0], b_[1], zl), b_])
    # --- alimentación en estrella desde las dos borneras puente (22 AWG)
    pw = 1.8
    wy, sy0, sz0, sly, shz, sdepth = SWITCH
    sw_a, sw_b = (wy - sdepth, sy0 + 4.5, sz0 + 6.5), (wy - sdepth, sy0 + 14.5, sz0 + 6.5)
    fx, fy, fz, fl, fr = FUSE
    wire("Entrada_+5V_a_interruptor", "Alimentacion_entrada", "w_red",
         [(ENTRY[0] - 7, ENTRY[1] + 1, ENTRY[2]), (sw_a[0] - 3, ENTRY[1] + 1, ENTRY[2]), (sw_a[0] - 3, sw_a[1], sw_a[2]), sw_a], pw)
    wire("Interruptor_a_fusible", "Alimentacion_entrada", "w_red",
         [sw_b, (sw_b[0] - 5, sw_b[1], sw_b[2]), (sw_b[0] - 5, fy + fl + 4, fz + 9), (fx, fy + fl + 4, fz), (fx, fy + fl, fz)], pw)
    tin_p, tin_n = block_term(BLK_P_X, 0, -1), block_term(BLK_N_X, 0, 1)
    wire("Fusible_a_bornera_+5V", "Alimentacion_entrada", "w_red",
         [(fx, fy, fz), (fx - 8, fy - 1.5, fz - 4), (tin_p[0] - 2, fy - 1.5, 5.0), (tin_p[0] - 2, tin_p[1], 5.0), (tin_p[0] - 2, tin_p[1], tin_p[2]), tin_p], pw)
    wire("Entrada_GND_a_bornera_GND", "Alimentacion_entrada", "w_black",
         [(ENTRY[0] - 7, ENTRY[1] - 1, ENTRY[2]), (tin_n[0] + 3, ENTRY[1] - 1, ENTRY[2] - 4), (tin_n[0] + 3, tin_n[1], tin_n[2]), tin_n], pw)
    # Ramas: k, destino (+, -), ruta intermedia
    def branch(k, name, dp, dn, mids_p, mids_n):
        tp, tn = block_term(BLK_P_X, k, -1), block_term(BLK_N_X, k, -1)
        tn = (BLK_N_X - .3, tn[1] + 2.2, tn[2])
        wire(f"Estrella_{name}_+5V", f"Estrella_5V_{name}", "w_red", [tp] + mids_p + [dp], pw)
        wire(f"Estrella_{name}_GND", f"Estrella_5V_{name}", "w_black", [tn, (BLK_N_X - .9, tn[1], tn[2] + 8.5), (BLK_P_X - 1.2, tn[1], tn[2] + 8.5)] + mids_n + [dn], pw)
    p2 = CONNECTORS["T2.PWR"]
    branch(3, "T2", p2[1], p2[0], [(229.0, block_term(BLK_P_X, 3, -1)[1], 12), (p2[1][0], p2[1][1], ZT + 4)],
           [(229.0, block_term(BLK_P_X, 3, -1)[1] + 2.2, 14), (p2[0][0], p2[0][1], ZT + 4)])
    pp = CONNECTORS["T2.PAM_PWR"]
    branch(1, "PAM8403", pp[0], pp[1], [(228.5, block_term(BLK_P_X, 1, -1)[1], 13), (pp[0][0] + 3, pp[0][1], ZT + 7)],
           [(228.5, block_term(BLK_P_X, 1, -1)[1] + 2.2, 15), (pp[1][0] + 3, pp[1][1], ZT + 8)])
    j6 = CONNECTORS["T4.J6"]
    yk = block_term(BLK_P_X, 7, -1)[1]
    branch(7, "T4_J6", j6[0], j6[1], [(230.5, yk, 11), (230.5, 96.0, 11), (j6[0][0], 97.5, ZT + 6), (j6[0][0], j6[0][1] - 2, ZT + 4)],
           [(229.4, yk + 2.2, 13), (229.4, 97.5, 13), (j6[1][0], 99.0, ZT + 7), (j6[1][0], j6[1][1] - 2, ZT + 4)])
    p3 = CONNECTORS["T3.PWR"]
    yk = block_term(BLK_P_X, 6, -1)[1]
    branch(6, "T3", p3[1], p3[0], [(228.0, yk, 9), (228.0, 94.0, 7), (p3[1][0], 94.0, 7), (p3[1][0], p3[1][1], ZT + 5)],
           [(227.0, yk + 2.2, 10), (227.0, 95.6, 8.5), (p3[0][0], 95.6, 8.5), (p3[0][0], p3[0][1], ZT + 5)])
    p1 = CONNECTORS["T1.PWR"]
    yk = block_term(BLK_P_X, 5, -1)[1]
    branch(5, "T1", p1[1], p1[0], [(226.6, yk, 8), (226.6, 91.0, 6.5), (99.5, 91.0, 6.5), (99.5, 80.5, 6.5), (p1[1][0], 80.5, 8), (p1[1][0], p1[1][1], ZT + 5)],
           [(225.8, yk + 2.2, 9), (225.8, 92.5, 8), (101.0, 92.5, 8), (101.0, 82.0, 8), (p1[0][0], 82.0, 9.5), (p1[0][0], p1[0][1], ZT + 5)])
    bi = CONNECTORS["BOOST.IN"]
    tp, tn = block_term(BLK_P_X, 7, 1), block_term(BLK_N_X, 7, 1)
    wire("Estrella_tira_+5V_a_elevador", "Estrella_5V_tira", "w_red",
         [(BLK_P_X + BLOCK[1] / 2, tp[1] + 3.6, FLOOR + BLOCK[2]), (BLK_P_X + BLOCK[1] / 2, 93.0, 20), (bi[0][0], 101.0, 14), (bi[0][0], bi[0][1] + 2.5, bi[0][2] + 3), bi[0]], pw)
    wire("Estrella_tira_GND_a_elevador", "Estrella_5V_tira", "w_black",
         [(BLK_N_X + BLOCK[1] / 2, tn[1] + 3.6, FLOOR + BLOCK[2]), (BLK_N_X + BLOCK[1] / 2, 92.0, 18), (bi[1][0], 100.0, 13), (bi[1][0], bi[1][1] + 2.5, bi[1][2] + 3), bi[1]], pw)


# ------------------------------------------------------------------ aberturas de gabinete y tapa
def lid_cuts():
    cuts = []
    for ref, func, kind, x, estado, ind in CONTROLS:
        cuts.append(cyl(x, KNOB_Y, H - 1, 3.7, LID + 2))
    cx, cy = TFT_C
    # Ventana pasante del cristal de la pantalla: queda al ras por fuera; la placa, más larga
    # que la ventana, la retienen los cuatro ganchos a presión fundidos con la tapa.
    cuts += rrect(cx - TFT_WIN[0] / 2, cy - TFT_WIN[1] / 2, H - 1, TFT_WIN[0], TFT_WIN[1], LID + 2, 2.0)
    # Ranuras de alivio de los ganchos de la pantalla: 2 mm hacia dentro de la tapa (queda
    # 1 mm de piel hacia fuera) con 0,2 mm de holgura alrededor de cada raíz para que flexione.
    for hx_ in (112.0, 160.0):
        cuts.append(box(hx_ - .35, 30.75, H - .02, 8.7, 1.9, 2.0))
    for bx0_ in (CYD_X0 - 1.6, CYD_X0 + CYD_PCB_W + .4):
        cuts.append(box(bx0_ - .35, 121.45, H - .02, 1.9, 7.2, 2.0))
    for sx, sy in SPK_CS:           # rejilla de ranuras sobre cada parlante
        for k in range(-10, 11):
            half = 16.0 if abs(k) < 9 else 11.0
            cuts.append(box(sx + k * 4.2 - 1.0, sy - half, H - 1, 2.0, 2 * half, LID + 2))
    cuts.append(cyl(SW_C[0], SW_C[1], H - 1, 4.0, LID + 2))
    for name, y, col in BARS:
        cuts += stadium(BAR_X0 - 1, y - HEX_WIN / 2, H - 1, BAR_LEN + 2, HEX_WIN, LID + 2)
    return cuts


def body_cuts():
    cuts = []
    jx, jy = bxy("T1", 0, 45)
    cuts.append(cyl(-1, jy, ZT + 2.6, 3.3, WALL + 2, "x"))                     # J1 en la pared izquierda
    jx, jy = bxy("T2", 60, 0)
    cuts.append(cyl(jx, -1, ZT + 2.6, 3.3, WALL + 2, "y"))                     # J2 en la pared frontal
    cuts.append(box(W - WALL - 1, USB_C[1] - 7.0, USB_C[2] - 6.3, WALL + 2, 14.0, 9.4))  # USB-C
    cuts.append(cyl(W - WALL - 1, ENTRY[1], ENTRY[2], 4.2, WALL + 2, "x"))     # pasacable
    wy, y0, z0, ly, hz, depth = SWITCH
    cuts.append(box(W - WALL - 1, y0, z0, WALL + 2, ly, hz))                   # interruptor
    cuts.append(box(182.0, D - WALL - 1, H - 3.5, 24.0, WALL + 2, 4.0))        # uñero trasero para levantar la tapa
    return cuts


def build_all():
    PARTS.clear(); WIRES.clear(); CONNECTORS.clear(); PARTS_SCREWS.clear(); LID_STUDS.clear()
    build_boards()
    build_power()
    build_lid_parts()
    build_wires()
    return PARTS, WIRES


# ------------------------------------------------------------------ utilidades geométricas
def prim_bbox(p):
    if p[0] == "box":
        _, x, y, z, dx, dy, dz = p
        return (x, y, z, x + dx, y + dy, z + dz)
    if p[0] == "cone":
        _, x, y, z, r1, r2, h = p
        r = max(r1, r2)
        return (x - r, y - r, z, x + r, y + r, z + h)
    if p[0] == "prismx":
        _, x, dx, pts = p
        return (x, min(q[0] for q in pts), min(q[1] for q in pts), x + dx, max(q[0] for q in pts), max(q[1] for q in pts))
    if p[0] == "hex":
        _, x, y, z, af, h = p
        return (x - af / 2, y - af / 3 ** .5, z, x + af / 2, y + af / 3 ** .5, z + h)
    _, x, y, z, r, h, axis = p
    if axis == "z":
        return (x - r, y - r, z, x + r, y + r, z + h)
    if axis == "x":
        return (x, y - r, z - r, x + h, y + r, z + r)
    return (x - r, y, z - r, x + r, y + h, z + r)


def part_bbox(p):
    bbs = [prim_bbox(q) for q in p["add"]]
    return tuple(min(b[i] for b in bbs) for i in range(3)) + tuple(max(b[i] for b in bbs) for i in range(3, 6))


def lid_transform(angle_deg):
    """Devuelve f(x, y, z) para la tapa girada angle_deg sobre su borde frontal."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)

    def f(x, y, z):
        dy, dz = y - PIVOT_Y, z - PIVOT_Z
        return (x, PIVOT_Y + dy * c - dz * s, PIVOT_Z + dy * s + dz * c)
    return f


def fillet(pts, r=2.2, n=4):
    """Redondea las esquinas de una polilínea etiquetada conservando la etiqueta cuerpo/tapa."""
    out = [pts[0]]
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        if a[3] != b[3] or b[3] != c[3]:
            out.append(b)
            continue
        va = [a[i] - b[i] for i in range(3)]
        vc = [c[i] - b[i] for i in range(3)]
        la, lc = math.sqrt(sum(v * v for v in va)), math.sqrt(sum(v * v for v in vc))
        d = min(r, la / 2.2, lc / 2.2)
        if d < 0.3:
            out.append(b)
            continue
        p0 = [b[i] + va[i] / la * d for i in range(3)]
        p1 = [b[i] + vc[i] / lc * d for i in range(3)]
        for k in range(n + 1):
            t = k / n
            q = [(1 - t) ** 2 * p0[i] + 2 * t * (1 - t) * b[i] + t * t * p1[i] for i in range(3)]
            out.append((q[0], q[1], q[2], b[3]))
    out.append(pts[-1])
    return out


def export_layout():
    """Datos que consume Blender además de la malla teselada."""
    parts, wires = build_all() if not PARTS else (PARTS, WIRES)
    return {
        "W": W, "D": D, "H": H, "LID": LID, "magnets": [list(m) for m in MAGNETS], "pivot": [PIVOT_Y, PIVOT_Z], "lid_open_deg": LID_OPEN_DEG,
        "boards": {k: list(v[:4]) + [v[4]] for k, v in BOARDS.items()}, "z_board_top": ZT,
        "controls": [{"ref": r, "func": f, "kind": k, "x": x, "y": KNOB_Y, "estado": e} for r, f, k, x, e, _ in CONTROLS],
        "pot_travel_deg": POT_TRAVEL_DEG,
        "tft": {"center": list(TFT_C), "active": TFT_ACTIVE, "glass": list(TFT_WIN), "offset_x": 0.0, "pixels": [320, 480]},
        "speakers": [list(c) for c in SPK_CS], "speaker_env": SPK, "sw1": list(SW_C),
        "bars": [{"name": n, "y": y, "x0": BAR_X0, "len": BAR_LEN, "color": list(COLORS[c])} for n, y, c in BARS], "hex_rib_z": H + LID - (HEX_RIB - HEX_FLOOR) / 2,
        "pixel_mm": PIXEL, "colors": {k: list(v) for k, v in COLORS.items()},
        "wires": [{**w, "pts": [list(p) for p in fillet(w["pts"])]} for w in wires],
        "usb_c": list(USB_C),
    }


if __name__ == "__main__":
    parts, wires = build_all()
    print(f"{len(parts)} piezas, {len(wires)} cables")

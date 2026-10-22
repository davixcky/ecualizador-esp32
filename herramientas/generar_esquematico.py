#!/usr/bin/env python3
"""Genera el esquemático KiCad del ecualizador en ../hardware/ecualizador.kicad_sch.

Las piezas, los valores, las huellas y las redes salen de circuito.py. Este script solo
decide dónde se dibuja cada pieza: las etapas con amplificador operacional se dibujan con
cables (como en los libros), y las uniones entre etapas con etiquetas que llevan el nombre
de la red. Todo pin que no quede unido por un cable recibe automáticamente un trozo de cable
con su etiqueta o su símbolo de alimentación, así que el dibujo no puede omitir una conexión.

Después de generar el archivo se verifica con:

    kicad-cli sch erc ../hardware/ecualizador.kicad_sch
    python3 verificar_netlist.py      (compara la netlist de KiCad con circuito.py)

Coordenadas en milímetros sobre la grilla de 1,27 mm; el eje y crece hacia abajo.
"""
import math
import os
import sys
import uuid as _uuid
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuito as cto  # noqa: E402
from sexpr import Sym, dump, find, find1, parse  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(AQUI, "..", "hardware")
SALIDA = os.path.join(HW, "ecualizador.kicad_sch")
LIBS = "/usr/share/kicad/symbols/"
PROYECTO = "ecualizador"
S = Sym

_ns = _uuid.UUID("3b9e7c10-0000-4000-8000-0000000000e0")
_cont = Counter()


def uid(tag="x"):
    _cont[tag] += 1
    return str(_uuid.uuid5(_ns, f"{tag}-{_cont[tag]}"))


RAIZ = uid("raiz")
G = 1.27


def r(v):
    return round(v, 4)


# ---------------------------------------------------------------- símbolos de biblioteca
def cargar(lib, nombre, como=None):
    """Símbolo de la biblioteca de KiCad; resuelve `extends` copiando el símbolo base."""
    arbol = parse(open(LIBS + lib + ".kicad_sym", encoding="utf-8").read())[0]
    todos = {s[1]: s for s in find(arbol, "symbol")}
    s = todos[nombre]
    base = find1(s, "extends")
    if base:
        b = list(todos[base[1]])
        props = {p[1]: p for p in find(s, "property")}
        b = [props.get(x[1], x) if isinstance(x, list) and x and x[0] == "property" else x for x in b]
        s = b
        viejo = base[1]
    else:
        s = list(s)
        viejo = nombre
    nuevo = como or nombre
    s[1] = f"{lib}:{nuevo}"
    for x in s:
        if isinstance(x, list) and x and x[0] == "symbol":
            x[1] = x[1].replace(viejo, nuevo, 1)
    return s


def pines_de(simbolo):
    """{número: (x, y, ángulo, unidad)} con la convención de KiCad (y hacia arriba)."""
    pines = {}
    for u in find(simbolo, "symbol"):
        unidad = int(u[1].rsplit("_", 2)[-2])
        for p in find(u, "pin"):
            at = find1(p, "at")
            pines[find1(p, "number")[1]] = (float(at[1]), float(at[2]), float(at[3]), unidad)
    return pines


def efectos(tam=1.27, oculto=False, just=None):
    e = [S("effects"), [S("font"), [S("size"), tam, tam]]]
    if just:
        e.append([S("justify")] + [S(j) for j in just.split()])
    if oculto:
        e.append([S("hide"), S("yes")])
    return e


def prop(nombre, valor, x, y, ang=0, oculto=False, just=None):
    return [S("property"), nombre, valor, [S("at"), r(x), r(y), ang], efectos(oculto=oculto, just=just)]


def pin_def(tipo, x, y, ang, nombre, numero, largo=5.08):
    return [S("pin"), S(tipo), S("line"), [S("at"), x, y, ang], [S("length"), largo],
            [S("name"), nombre, efectos()], [S("number"), numero, efectos()]]


def sim_esp32():
    def tipo(n):
        if n == "3V3":
            return "power_out"
        if n in ("5V", "GND"):
            return "power_in"
        if n in ("VP/IO36", "VN/IO39", "IO34", "IO35", "EN"):
            return "input"
        return "bidirectional"
    pines = [pin_def(tipo(n), -17.78, r(22.86 - 2.54 * k), 0, n, str(k + 1)) for k, n in enumerate(cto.IZQ)]
    pines += [pin_def(tipo(n), 17.78, r(22.86 - 2.54 * k), 180, n, str(k + 20)) for k, n in enumerate(cto.DER)]
    graf = [[S("rectangle"), [S("start"), -12.7, 25.4], [S("end"), 12.7, -25.4],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]],
            [S("text"), "USB", [S("at"), 0, -23.5, 0], efectos()]]
    return [S("symbol"), "Ecualizador:ESP32-DevKitC-38", [S("pin_names"), [S("offset"), 1.016]],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
            prop("Reference", "U", 0, 27.94), prop("Value", "ESP32-DevKitC-38", 0, -27.94),
            prop("Footprint", "", 0, 0, oculto=True), prop("Datasheet", "", 0, 0, oculto=True),
            prop("Description", "Tarjeta ESP32-DevKitC V4 (ESP32-WROOM-32), 38 pines", 0, 0, oculto=True),
            [S("symbol"), "ESP32-DevKitC-38_0_1"] + graf, [S("symbol"), "ESP32-DevKitC-38_1_1"] + pines]


SIMBOLO = {"R": "Device:R", "C": "Device:C", "CP": "Device:C_Polarized", "POT": "Device:R_Potentiometer",
           "D": "Device:D", "JACK": "Connector_Audio:AudioJack3", "CONN4": "Connector_Generic:Conn_01x04",
           "CONN3": "Connector_Generic:Conn_01x03", "CONN2": "Connector_Generic:Conn_01x02",
           "BUFFER": "74xx:74AHCT125", "TFT": "Connector_Generic:Conn_01x08", "SW": "Switch:SW_Push", "OPAMP": "Amplifier_Operational:MCP6004",
           "ESP32": "Ecualizador:ESP32-DevKitC-38"}
POTENCIA = {"GND": "power:GND", "+3V3": "power:+3V3", "+5V": "power:+5V", "+3.3VA": "power:+3.3VA"}


# ---------------------------------------------------------------- el esquemático
class Esquematico:
    def __init__(self):
        self.lib = {}
        self.pines_lib = {}
        self.items = []
        self.cables = []
        self.pines = []          # (ref, num, (x, y), ángulo hacia afuera)
        self.pwr_n = 0
        self.flg_n = 0
        self.pines_pwr = []      # pines de los símbolos de alimentación y banderas

    def usar(self, lib_id):
        if lib_id not in self.lib:
            if lib_id == "Ecualizador:ESP32-DevKitC-38":
                d = sim_esp32()
            elif lib_id == "Amplifier_Operational:MCP6004":
                d = cargar("Amplifier_Operational", "MCP6004")
            else:
                d = cargar(*lib_id.split(":"))
            self.lib[lib_id] = d
            self.pines_lib[lib_id] = pines_de(d)
        return self.pines_lib[lib_id]

    def colocar(self, ref, x, y, rot=0, espejo_x=False, espejo_y=False, unidad=1, ref_at=None, val_at=None,
                lib_id=None, valor=None, ocultar_valor=False):
        """Coloca la pieza (o una unidad de ella) y devuelve {pin: (x, y)} en el esquemático."""
        es_power = lib_id is not None and lib_id.startswith("power:")
        if es_power:
            p = None
        else:
            p = cto.pieza(ref)
            lib_id = SIMBOLO[p["tipo"]]
            valor = valor or p["valor"]
        pines = self.usar(lib_id)
        pos = {}
        a = math.radians(rot)
        for num, (px, py, ang, u) in pines.items():
            if u not in (0, unidad):
                continue
            if espejo_y:
                px, ang = -px, 180 - ang
            if espejo_x:
                py, ang = -py, -ang
            rx = px * math.cos(a) - py * math.sin(a)
            ry = px * math.sin(a) + py * math.cos(a)
            pos[num] = (r(x + rx), r(y - ry))
            if not es_power:
                self.pines.append((ref, num, pos[num], (ang + rot + 180) % 360))
            else:
                self.pines_pwr.append(pos[num])
        # los textos de una pieza girada se guardan girados para que se lean horizontales y centrados
        ang_campos = rot if rot in (90, 270) else 0
        just = None if (es_power or rot) else "left"
        ra = ref_at or (x + 2.54, y - 1.27)
        va = val_at or (x + 2.54, y + 1.27)
        nodo = [S("symbol"), [S("lib_id"), lib_id], [S("at"), r(x), r(y), rot]]
        if espejo_x:
            nodo.append([S("mirror"), S("x")])
        if espejo_y:
            nodo.append([S("mirror"), S("y")])
        nodo += [[S("unit"), unidad], [S("exclude_from_sim"), S("no")], [S("in_bom"), S("no" if es_power else "yes")],
                 [S("on_board"), S("no" if es_power else "yes")], [S("dnp"), S("no")], [S("uuid"), uid("sym")],
                 prop("Reference", ref, ra[0], ra[1], ang_campos, oculto=es_power, just=just),
                 prop("Value", valor, va[0], va[1], ang_campos, oculto=ocultar_valor, just=just),
                 prop("Footprint", "" if es_power else p["huella"], x, y, 0, oculto=True),
                 prop("Datasheet", "", x, y, 0, oculto=True)]
        if p:
            nodo.append(prop("Description", p["funcion"], x, y, 0, oculto=True))
        for num in pos:
            nodo.append([S("pin"), num, [S("uuid"), uid("pin")]])
        nodo.append([S("instances"), [S("project"), PROYECTO,
                                      [S("path"), f"/{RAIZ}", [S("reference"), ref], [S("unit"), unidad]]]])
        self.items.append(nodo)
        return pos

    def ao(self, unidad, x, y, invertido=False, **kw):
        """Unidad de amplificador operacional: + arriba (o abajo si invertido). Devuelve (+, −, salida)."""
        ref, letra = unidad[:-1], unidad[-1]
        n = "ABCDE".index(letra) + 1
        pos = self.colocar(ref, x, y, unidad=n, espejo_x=invertido,
                           ref_at=kw.get("ref_at", (x + 1.27, y - (7.62 if not invertido else -7.62))),
                           val_at=kw.get("val_at", (x + 1.27, y - (5.08 if not invertido else -5.08))),
                           ocultar_valor=True)
        if letra == "E":
            return pos["4"], pos["11"]
        pm, pn, po = cto.PINES_UNIDAD[letra]
        return pos[pm], pos[pn], pos[po]

    def potencia(self, red, x, y, rot=0):
        self.pwr_n += 1
        # dirección del cuerpo del símbolo (abajo para GND, arriba para las fuentes), girada
        bx, by = (0, 1) if red == "GND" else (0, -1)
        a = math.radians(rot)
        bx, by = bx * math.cos(a) + by * math.sin(a), -bx * math.sin(a) + by * math.cos(a)
        d = 5.6 if abs(bx) > 0.5 else 3.6
        self.colocar(f"#PWR{self.pwr_n:03d}", x, y, rot, lib_id=POTENCIA[red], valor=red,
                     ref_at=(x, y), val_at=(x + d * bx, y + d * by))

    def bandera(self, x, y):
        self.flg_n += 1
        self.colocar(f"#FLG{self.flg_n:02d}", x, y, lib_id="power:PWR_FLAG", valor="PWR_FLAG",
                     ref_at=(x, y), val_at=(x, y - 4.5))

    def cable(self, *puntos):
        for a, b in zip(puntos, puntos[1:]):
            a, b = (r(a[0]), r(a[1])), (r(b[0]), r(b[1]))
            if a != b:
                assert a[0] == b[0] or a[1] == b[1], (a, b)
                self.cables.append((a, b))

    def etiqueta(self, nombre, x, y, ang=0):
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append([S("label"), nombre, [S("at"), r(x), r(y), ang], efectos(just=just), [S("uuid"), uid("lbl")]])

    def texto(self, t, x, y, tam=1.27, negrita=False):
        e = [S("effects"), [S("font"), [S("size"), tam, tam]] + ([[S("bold"), S("yes")]] if negrita else []),
             [S("justify"), S("left"), S("bottom")]]
        self.items.append([S("text"), t, [S("exclude_from_sim"), S("no")], [S("at"), r(x), r(y), 0], e,
                           [S("uuid"), uid("txt")]])

    def caja(self, x1, y1, x2, y2, titulo):
        self.items.append([S("rectangle"), [S("start"), r(x1), r(y1)], [S("end"), r(x2), r(y2)],
                           [S("stroke"), [S("width"), 0.25], [S("type"), S("dash")], [S("color"), 120, 120, 120, 1]],
                           [S("fill"), [S("type"), S("none")]], [S("uuid"), uid("rect")]])
        self.texto(titulo, x1 + 1.27, y1 + 3.81, 1.8, True)

    def no_conectar(self, p):
        self.items.append([S("no_connect"), [S("at"), p[0], p[1]], [S("uuid"), uid("nc")]])

    # ---------------- trozos automáticos para los pines sin cable
    def completar(self):
        extremos = Counter()
        for a, b in self.cables:
            extremos[a] += 1
            extremos[b] += 1
        for p in self.pines_pwr:
            extremos[p] += 1
        for ref, num, p, ang in self.pines:
            if extremos[p] or any(
                (a[0] == b[0] == p[0] and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])) or
                (a[1] == b[1] == p[1] and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]))
                for a, b in self.cables
            ):
                continue
            red = cto.pieza(ref)["pines"].get(num)
            if red is None:
                self.no_conectar(p)
                continue
            dx, dy = round(math.cos(math.radians(ang))), -round(math.sin(math.radians(ang)))
            fin = (r(p[0] + 2.54 * dx), r(p[1] + 2.54 * dy))
            self.cable(p, fin)
            if red in POTENCIA:
                # el símbolo apunta en la dirección del trozo, lejos de la pieza
                if red == "GND":
                    rot = {(1, 0): 90, (-1, 0): 270, (0, 1): 0, (0, -1): 180}[(dx, dy)]
                else:
                    rot = {(1, 0): 270, (-1, 0): 90, (0, -1): 0, (0, 1): 180}[(dx, dy)]
                self.potencia(red, fin[0], fin[1], rot)
            else:
                ang_lbl = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
                self.etiqueta(red, fin[0], fin[1], ang_lbl)

    def _partir(self):
        """Corta cada cable en los puntos donde termina otro cable o un pin (uniones en T)."""
        puntos = ({p for c in self.cables for p in c} | {p for _, _, p, _ in self.pines} | set(self.pines_pwr))
        nuevos = []
        for a, b in self.cables:
            if a[0] == b[0]:
                medio = sorted(p for p in puntos if p[0] == a[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1]))
                medio.sort(key=lambda p: p[1], reverse=a[1] > b[1])
            else:
                medio = sorted(p for p in puntos if p[1] == a[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]))
                medio.sort(key=lambda p: p[0], reverse=a[0] > b[0])
            cadena = [a] + medio + [b]
            nuevos += list(zip(cadena, cadena[1:]))
        vistos, self.cables = set(), []
        for a, b in nuevos:
            k = tuple(sorted((a, b)))
            if k not in vistos:
                vistos.add(k)
                self.cables.append((a, b))

    def _uniones(self):
        self._partir()
        cuenta = Counter()
        for a, b in self.cables:
            cuenta[a] += 1
            cuenta[b] += 1
        for p in [q for _, _, q, _ in self.pines] + self.pines_pwr:
            if p in cuenta:
                cuenta[p] += 1
        uniones = {p for p, n in cuenta.items() if n >= 3}
        for a, b in self.cables:
            for p in (a, b):
                for c, d in self.cables:
                    if p in (c, d):
                        continue
                    if c[0] == d[0] == p[0] and min(c[1], d[1]) < p[1] < max(c[1], d[1]):
                        uniones.add(p)
                    if c[1] == d[1] == p[1] and min(c[0], d[0]) < p[0] < max(c[0], d[0]):
                        uniones.add(p)
        return sorted(uniones)

    def guardar(self, ruta, titulo, papel="A2"):
        cab = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
               [S("generator_version"), "9.0"], [S("uuid"), RAIZ], [S("paper"), papel],
               [S("title_block"), [S("title"), titulo[0]], [S("date"), titulo[1]], [S("rev"), titulo[2]],
                [S("company"), titulo[3]]] + [[S("comment"), i + 1, c] for i, c in enumerate(titulo[4:])],
               [S("lib_symbols")] + list(self.lib.values())]
        cuerpo = []
        for p in self._uniones():
            cuerpo.append([S("junction"), [S("at"), p[0], p[1]], [S("diameter"), 0],
                           [S("color"), 0, 0, 0, 0], [S("uuid"), uid("jn")]])
        for a, b in self.cables:
            cuerpo.append([S("wire"), [S("pts"), [S("xy"), a[0], a[1]], [S("xy"), b[0], b[1]]],
                           [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid("w")]])
        doc = cab + cuerpo + self.items + [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
                                           [S("embedded_fonts"), S("no")]]
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        carpeta = os.path.dirname(ruta)
        propios = []
        for k, v in self.lib.items():
            if k.startswith("Ecualizador:"):
                v = list(v)
                v[1] = k.split(":")[1]
                propios.append(v)
        with open(os.path.join(carpeta, "Ecualizador.kicad_sym"), "w", encoding="utf-8") as f:
            f.write(dump([S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "kicad_symbol_editor"],
                          [S("generator_version"), "9.0"]] + propios) + "\n")
        with open(os.path.join(carpeta, "sym-lib-table"), "w", encoding="utf-8") as f:
            f.write('(sym_lib_table\n  (version 7)\n  (lib (name "Ecualizador")(type "KiCad")'
                    '(uri "${KIPRJMOD}/Ecualizador.kicad_sym")(options "")(descr "Símbolos propios"))\n)\n')
        with open(os.path.join(carpeta, "fp-lib-table"), "w", encoding="utf-8") as f:
            f.write('(fp_lib_table\n  (version 7)\n  (lib (name "Ecualizador")(type "KiCad")'
                    '(uri "${KIPRJMOD}/Ecualizador.pretty")(options "")(descr "Huellas propias"))\n)\n')
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(dump(doc) + "\n")


# ---------------------------------------------------------------- etapas dibujadas con cables
def pasivo_h(sch, ref, xc, y, arriba=True):
    """Resistencia o condensador horizontal centrado en (xc, y): devuelve (izquierda, derecha)."""
    yr, yv = (y - 4.06, y - 1.9) if arriba else (y + 2.54, y + 4.7)
    p = sch.colocar(ref, xc, y, rot=90, ref_at=(xc, yr), val_at=(xc, yv))
    return p["1"], p["2"]


def pasivo_v(sch, ref, x, yc, lado=1):
    """Pasivo vertical centrado en (x, yc), textos a la derecha (lado=1) o a la izquierda (-1)."""
    dx = 1.9 if lado > 0 else -10.2
    p = sch.colocar(ref, x, yc, ref_at=(x + dx, yc - 0.6), val_at=(x + dx, yc + 1.9))
    return p["1"], p["2"]


def vref(sch, p, abajo=True):
    q = (p[0], r(p[1] + (2.54 if abajo else -2.54)))
    sch.cable(p, q)
    sch.etiqueta("VREF", q[0], q[1], 270 if abajo else 90)


def entrada(sch, p, red, largo=2.54):
    q = (r(p[0] - largo), p[1])
    sch.cable(p, q)
    sch.etiqueta(red, q[0], q[1], 180)


def salida(sch, p, red, largo=2.54):
    q = (r(p[0] + largo), p[1])
    sch.cable(p, q)
    sch.etiqueta(red, q[0], q[1], 0)


def a_potencia(sch, p, red, desplazamientos, rot):
    """Cable desde el pin p por los desplazamientos (dx, dy) y símbolo de alimentación al final."""
    puntos = [p]
    for dx, dy in desplazamientos:
        puntos.append((r(puntos[-1][0] + dx), r(puntos[-1][1] + dy)))
    sch.cable(*puntos)
    sch.potencia(red, *puntos[-1], rot)


def sallen_key(sch, unidad, ox, oy, serie1, serie2, fb, tierra, red_in, red_out, etiquetas=True):
    """Sallen-Key de ganancia unitaria (pasa bajas: serie = R, fb y tierra = C; pasa altas: al revés)."""
    mas, menos, out = sch.ao(unidad, ox, oy)
    y = mas[1]
    a1, a2 = pasivo_h(sch, serie1, ox - 35.56, y)
    b1, b2 = pasivo_h(sch, serie2, ox - 20.32, y)
    nodo = (ox - 27.94, y)
    t1, t2 = pasivo_v(sch, tierra, ox - 12.7, y + 3.81, lado=-1)
    ytop = y - 10.16
    f1, f2 = pasivo_h(sch, fb, ox - 7.62, ytop)
    xs = ox + 12.7
    sch.cable(a2, nodo, b1)
    sch.cable(nodo, (nodo[0], ytop), f1)
    sch.cable(f2, (xs, ytop), (xs, out[1]))
    sch.cable(b2, t1, mas)
    sch.cable(menos, (ox - 10.16, menos[1]), (ox - 10.16, oy + 7.62), (xs, oy + 7.62), (xs, out[1]))
    sch.cable(out, (xs, out[1]))
    if etiquetas:
        salida(sch, (xs, out[1]), red_out, 5.08)
        entrada(sch, a1, red_in)
    vref(sch, t2)
    return a1, (xs, out[1])


def no_inversor(sch, unidad, ox, oy, rf, rg, cg, red_out):
    """Preamplificador no inversor: Rf de − a la salida, Rg y Cg de − a VREF."""
    mas, menos, out = sch.ao(unidad, ox, oy)
    xs = ox + 12.7
    nodo = (ox - 10.16, oy + 10.16)
    f1, f2 = pasivo_h(sch, rf, ox + 1.27, nodo[1], arriba=False)
    g1, g2 = pasivo_v(sch, rg, nodo[0], nodo[1] + 5.08, lado=-1)
    c1, c2 = pasivo_v(sch, cg, nodo[0], nodo[1] + 15.24, lado=-1)
    sch.cable(menos, (nodo[0], menos[1]), nodo, f1)
    sch.cable(nodo, g1)
    sch.cable(g2, c1)
    sch.cable(f2, (xs, nodo[1]), (xs, out[1]))
    sch.cable(out, (xs, out[1]))
    salida(sch, (xs, out[1]), red_out, 5.08)
    vref(sch, c2)
    return mas


def seguidor(sch, unidad, ox, oy, red_out=None):
    mas, menos, out = sch.ao(unidad, ox, oy)
    xs = ox + 10.16
    sch.cable(menos, (ox - 10.16, menos[1]), (ox - 10.16, oy + 7.62), (xs, oy + 7.62), (xs, out[1]))
    sch.cable(out, (xs, out[1]))
    if red_out:
        salida(sch, (xs, out[1]), red_out, 5.08)
    return mas, (xs, out[1])


def inversor(sch, unidad, ox, oy, entradas, rf, red_out):
    """Inversor / sumador referido a VREF. entradas = [(ref, red de entrada), ...]."""
    mas, menos, out = sch.ao(unidad, ox, oy, invertido=True)
    xb, xs = ox - 12.7, ox + 12.7
    yf = menos[1] - 7.62
    f1, f2 = pasivo_h(sch, rf, ox, yf)
    sch.cable((xb, yf), f1)
    sch.cable(f2, (xs, yf), (xs, out[1]))
    sch.cable(out, (xs, out[1]))
    salida(sch, (xs, out[1]), red_out, 5.08)
    ultimo = menos[1]
    for i, (ref, red) in enumerate(entradas):
        y = r(menos[1] + 7.62 * i)
        a, b = pasivo_h(sch, ref, xb - 6.35, y)
        sch.cable(b, (xb, y))
        entrada(sch, a, red)
        ultimo = y
    sch.cable((xb, yf), (xb, ultimo))
    sch.cable((xb, menos[1]), menos)
    q = (mas[0], r(mas[1] + 2.54))
    sch.cable(mas, q)
    sch.etiqueta("VREF", q[0], q[1], 270)


def detector(sch, det, seg, ox, oy, diodo, ch, rd, red_in, red_out):
    mas, menos, out = sch.ao(det, ox, oy, invertido=True)
    y = out[1]
    p = sch.colocar(diodo, ox + 13.97, y, rot=180, ref_at=(ox + 13.97, y - 4.06), val_at=(ox + 13.97, y - 1.9))
    nodo = (ox + 22.86, y)
    c1, c2 = pasivo_v(sch, ch, nodo[0], y + 3.81, lado=-1)
    xr = ox + 33.02
    r1, r2 = pasivo_v(sch, rd, xr, y + 3.81)
    smas, sout = seguidor(sch, seg, ox + 58.42, y + 2.54, red_out)
    sch.cable(out, p["2"])
    sch.cable(p["1"], nodo, (xr, y), smas)
    sch.cable(nodo, c1)
    sch.cable((xr, y), r1)
    sch.cable(menos, (ox - 10.16, menos[1]), (ox - 10.16, y - 10.16), (nodo[0], y - 10.16), nodo)
    entrada(sch, mas, red_in)
    vref(sch, c2)
    vref(sch, r2)


# ---------------------------------------------------------------- el dibujo completo
def construir():
    sch = Esquematico()

    # ================= fila 1 =================
    # ---------------- alimentación y referencia
    sch.caja(12.7, 15.24, 130.81, 96.52, "ALIMENTACIÓN ANALÓGICA Y VREF = 1,65 V")
    yv, yg = 27.94, 43.18
    sch.potencia("+3V3", 17.78, yv)
    r1a, r1b = pasivo_h(sch, "R1", 22.86, yv, arriba=False)
    sch.cable((17.78, yv), r1a)
    sch.cable(r1b, (124.46, yv))
    sch.potencia("+3.3VA", 30.48, yv)
    sch.bandera(124.46, yv)
    for ref, x, lado in (("C1", 33.02, -1), ("C2", 43.18, 1)):
        a, b = pasivo_v(sch, ref, x, (yv + yg) / 2, lado=lado)
        sch.cable((x, yv), a)
        sch.cable(b, (x, yg))
    for i, u in enumerate(("U1", "U2", "U3", "U4")):
        x = 53.34 + i * 19.05
        vmas, vmenos = sch.ao(u + "E", x + 2.54, (yv + yg) / 2, ref_at=(x + 3.0, (yv + yg) / 2 + 0.6),
                              val_at=(x + 3.0, (yv + yg) / 2 + 3))
        sch.cable((vmas[0], yv), vmas)
        sch.cable(vmenos, (vmenos[0], yg))
        a, b = pasivo_v(sch, f"C{4 + i}", x + 10.16, (yv + yg) / 2)
        sch.cable((x + 10.16, yv), a)
        sch.cable(b, (x + 10.16, yg))
    sch.cable((17.78, yg), (124.46, yg))
    sch.potencia("GND", 124.46, yg)
    sch.bandera(17.78, yg)
    sch.texto("Filtro RC R1–C1: fc ≈ 159 Hz. C4–C7: desacoplo local de los MCP6004.",
              15.24, 52.07, 1.0)
    # reserva de 5 V
    sch.potencia("+5V", 20.32, 60.96)
    sch.bandera(27.94, 60.96)
    c3a, c3b = pasivo_v(sch, "C3", 20.32, 67.31)
    sch.cable((20.32, 60.96), c3a)
    sch.cable((20.32, 60.96), (27.94, 60.96))
    sch.potencia("GND", *c3b)
    sch.texto("C3: picos del\nPAM8403 (J3)", 15.24, 85.09, 1.0)
    # divisor y seguidor de VREF
    x = 48.26
    sch.potencia("+3.3VA", x, 58.42)
    r2a, r2b = pasivo_v(sch, "R2", x, 64.77)
    r3a, r3b = pasivo_v(sch, "R3", x, 80.01)
    c8a, c8b = pasivo_v(sch, "C8", x + 10.16, 80.01)
    sch.cable((x, 58.42), r2a)
    nodo = (x, 72.39)
    sch.cable(r2b, nodo, r3a)
    sch.potencia("GND", *r3b)
    sch.potencia("GND", *c8b)
    mas, sal = seguidor(sch, "U1A", x + 33.02, nodo[1] + 2.54)
    sch.cable(nodo, (x + 10.16, nodo[1]), mas)
    sch.cable((x + 10.16, nodo[1]), c8a)
    salida(sch, sal, "VREF", 7.62)
    sch.texto("VREF es la tierra de señal: todas las etapas\noscilan alrededor de 1,65 V con 3,3 V.",
              71.12, 92.71, 1.0)

    # ---------------- entrada y preamplificador
    sch.caja(133.35, 15.24, 262.89, 96.52, "ENTRADA DE LÍNEA Y PREAMPLIFICADOR (G = 1 + R7/R8 = 3,2)")
    j1 = sch.colocar("J1", 143.51, 35.56, espejo_x=True, ref_at=(137.16, 27.94), val_at=(135.89, 45.72))
    a_potencia(sch, j1["S"], "GND", [(2.54, 0), (0, 2.54)], 0)
    r4a, r4b = pasivo_h(sch, "R4", 166.37, 30.48)
    r5a, r5b = pasivo_h(sch, "R5", 166.37, 40.64, arriba=False)
    entrada(sch, r4a, "IN_L")
    entrada(sch, r5a, "IN_R")
    xm = 175.26
    rv1 = sch.colocar("RV1", xm, 54.61, ref_at=(xm - 9.5, 53.34), val_at=(xm - 11.5, 55.88))
    sch.cable(r4b, (xm, 30.48), (xm, 40.64), rv1["1"])
    sch.cable(r5b, (xm, 40.64))
    sch.potencia("GND", *rv1["3"])
    yin = rv1["2"][1]
    c9a, c9b = pasivo_h(sch, "C9", 186.69, yin)
    sch.cable(rv1["2"], c9a)
    xp = 194.31
    r6a, r6b = pasivo_v(sch, "R6", xp, yin + 6.35, lado=-1)
    mas = no_inversor(sch, "U1B", 215.9, yin + 2.54, "R7", "R8", "C10", "PRE")
    sch.cable(c9b, (xp, yin), mas)
    sch.cable((xp, yin), r6a)
    vref(sch, r6b)
    sch.texto("R4–R5 mezclan a mono; RV1 ajusta el nivel. Con los deslizables al\nmáximo, la entrada debe ser ≤ 0,11 V de pico (la pantalla avisa CLIP).",
              135.89, 92.71, 1.0)

    # ---------------- microcontrolador, pantalla y pulsador
    sch.caja(265.43, 15.24, 407.67, 96.52, "MICROCONTROLADOR, PANTALLA TFT Y PULSADOR")
    sch.colocar("U5", 299.72, 55.88, ref_at=(297.18, 27.94), val_at=(289.56, 83.82))
    j4 = sch.colocar("J4", 365.76, 58.42, ref_at=(363.22, 38.1), val_at=(354.33, 80.01))
    a_potencia(sch, j4["1"], "+3V3", [(-5.08, 0), (0, -5.08)], 0)
    a_potencia(sch, j4["2"], "GND", [(-12.7, 0)], 270)
    pasivo_v(sch, "R30", 345.44, 30.48, lado=-1)
    sch.colocar("SW1", 391.16, 30.48, ref_at=(388.62, 25.4), val_at=(386.08, 35.56))
    sch.texto("J4 (adaptador): 1 VCC, 2 GND, 3 DIN, 4 CLK,\n5 CS, 6 DC, 7 RST, 8 BL. Waveshare 1,9 pulgadas.\nBL = GPIO19; datos LED = GPIO25.\nCablear por nombre; GH1.25 no tiene este orden.\nADC1 permite mantener el Wi-Fi activo.", 372.11, 50.8, 1.0)

    # ================= fila 2: filtros =================
    sch.caja(12.7, 99.06, 407.67, 151.13, "FILTROS ACTIVOS SALLEN-KEY DE SEGUNDO ORDEN (ganancia unitaria, Q ≈ 0,73)")
    oy = 128.27
    sallen_key(sch, "U1C", 60.96, oy, "R9", "R10", "C11", "C12", "PRE", "GRAVES")
    medios_in, medios_hp = sallen_key(sch, "U1D", 157.48, oy, "C13", "C14", "R11", "R12", "PRE", "MED_HP", etiquetas=False)
    medios_lp, medios_out = sallen_key(sch, "U2A", 254.0, oy, "R13", "R14", "C15", "C16", "MED_HP", "MEDIOS", etiquetas=False)
    entrada(sch, medios_in, "PRE")
    sch.cable(medios_hp, (190.5, medios_hp[1]), (190.5, medios_lp[1]), medios_lp)
    sch.etiqueta("MED_HP", 190.5, medios_lp[1])
    salida(sch, medios_out, "MEDIOS", 5.08)
    sallen_key(sch, "U2B", 350.52, oy, "C17", "C18", "R15", "R16", "PRE", "AGUDOS")
    yt = 146.05
    sch.texto("GRAVES, pasa bajas: fc = 1/(2π·10k·√(100n·47n)) = 232 Hz", 20.32, yt, 1.0)
    sch.texto("MEDIOS, pasa altas: fc = 1/(2π·10n·√(27k·56k)) = 409 Hz", 116.84, yt, 1.0)
    sch.texto("MEDIOS, pasa bajas: fc = 1/(2π·10k·√(10n·4n7)) = 2,3 kHz", 213.36, yt, 1.0)
    sch.texto("AGUDOS, pasa altas: fc = 1/(2π·10n·√(2k7·5k6)) = 4,1 kHz", 309.88, yt, 1.0)

    # ================= fila 3 =================
    # ---------------- ganancia por banda, inversor y sumador
    sch.caja(12.7, 153.67, 148.59, 248.92, "GANANCIA POR BANDA, INVERSOR Y SUMADOR")
    for i, (rv, banda, cursor) in enumerate((("RV2", "GRAVES", "G_W"), ("RV3", "MEDIOS", "M_W"),
                                            ("RV4", "AGUDOS", "A_W"))):
        x = 22.86 + 20.32 * i
        p = sch.colocar(rv, x, 175.26, ref_at=(x - 8.4, 173.99), val_at=(x - 9.5, 176.53))
        q = (x, r(p["1"][1] - 2.54))
        sch.cable(p["1"], q)
        sch.etiqueta(banda, q[0], q[1], 90)
        vref(sch, p["3"])
        salida(sch, p["2"], cursor)
    inversor(sch, "U4C", 132.08, 175.26, [("R17", "M_W")], "R18", "M_INV")
    inversor(sch, "U2C", 66.04, 213.36, [("R19", "G_W"), ("R20", "M_INV"), ("R21", "A_W")], "R22", "EQ_OUT")
    sch.texto("Deslizables de 10 kΩ lineales entre la salida de cada filtro y VREF; al 50 % la suma es plana.\n"
              "U4C invierte los medios para que los cruces de segundo orden queden en fase.\n"
              "EQ_OUT = VREF − (100k/47k)·[(G_W − VREF) + (M_INV − VREF) + (A_W − VREF)]", 15.24, 243.84, 1.0)

    # ---------------- salida de audio y antialiasing
    sch.caja(151.13, 153.67, 262.89, 248.92, "SALIDA DE AUDIO Y ANTIALIASING")
    y = 170.18
    q = (158.75, y)
    sch.etiqueta("EQ_OUT", q[0], q[1], 180)
    c19a, c19b = pasivo_h(sch, "C19", 166.37, y)
    sch.cable(q, c19a)
    r23a, r23b = pasivo_h(sch, "R23", 179.07, y)
    sch.cable(c19b, r23a)
    xl = 189.23
    r24a, r24b = pasivo_v(sch, "R24", xl, y + 6.35)
    sch.cable(r23b, (xl, y), (213.36, y), (213.36, y + 2.54))
    sch.cable((xl, y), r24a)
    sch.potencia("GND", *r24b)
    q = (xl, r(y - 2.54))
    sch.cable((xl, y), q)
    sch.etiqueta("LINEA", q[0], q[1], 90)
    rv5 = sch.colocar("RV5", 213.36, y + 6.35, ref_at=(203.2, y + 5.08), val_at=(201.93, y + 7.62))
    sch.potencia("GND", *rv5["3"])
    j2 = sch.colocar("J2", 238.76, y + 1.27, espejo_x=True, ref_at=(232.41, y - 5.08), val_at=(219.71, y + 12.7))
    a_potencia(sch, j2["S"], "GND", [(2.54, 0), (0, 2.54)], 0)
    j3 = sch.colocar("J3", 250.19, y + 22.86, ref_at=(252.73, y + 16.51), val_at=(252.73, y + 30.48))
    a_potencia(sch, j3["1"], "+5V", [(-5.08, 0), (0, -5.08)], 0)
    a_potencia(sch, j3["2"], "GND", [(-12.7, 0)], 270)
    a_potencia(sch, j3["4"], "GND", [(-2.54, 0), (0, 2.54)], 0)
    sch.texto("J2: salida de línea. J3: módulo PAM8403 y parlante;\nRV5 = volumen. R23 protege la salida de un corto.",
              154.94, 205.74, 1.0)
    sallen_key(sch, "U2D", 228.6, 226.06, "R25", "R26", "C20", "C21", "EQ_OUT", "ADC_FFT")
    sch.texto("Antialiasing: fc = 1/(2π·10k·√(4n7·2n2)) = 4,95 kHz; fs = 20 kS/s.", 154.94, 245.11, 1.0)

    # ---------------- detectores
    sch.caja(265.43, 153.67, 407.67, 248.92, "DETECTORES DE PICO DE PRECISIÓN Y SEGUIDORES")
    for i, (det, seg, d, ch, rd, cursor, adc) in enumerate((
            ("U3A", "U3B", "D1", "C22", "R27", "G_W", "ADC_G"),
            ("U3C", "U3D", "D2", "C23", "R28", "M_W", "ADC_M"),
            ("U4A", "U4B", "D3", "C24", "R29", "A_W", "ADC_A"))):
        detector(sch, det, seg, 284.48, 172.72 + 25.4 * i, d, ch, rd, cursor, adc)
    mas, sal = seguidor(sch, "U4D", 392.43, 168.91)
    entrada(sch, mas, "VREF")
    sch.texto("U4D: libre,\nseguidor de VREF.", 383.54, 182.88, 1.0)
    sch.texto("Diodo dentro del lazo: Ch se carga al pico real sin la caída de 0,6 V.\n"
              "τ = Rd·Ch = 220k·100n = 22 ms. ADC_x − VREF = pico de la banda.", 267.97, 245.11, 1.0)

    sch.caja(12.7, 254, 407.67, 335.28, "ILUMINACIÓN NEOPIXEL · 12 LED · FUENTE EXTERNA 5 V / 3 A")
    sch.colocar("J6", 30.48, 274.32)
    for unit, x in enumerate((76.2, 137.16, 198.12, 259.08), 1):
        sch.colocar("U6", x, 279.4, unidad=unit)
    sch.colocar("U6", 320.04, 279.4, unidad=5)
    pasivo_v(sch, "C25", 345.44, 279.4)
    pasivo_v(sch, "C26", 375.92, 279.4)
    pasivo_h(sch, "R31", 76.2, 304.8)
    pasivo_v(sch, "R32", 137.16, 304.8)
    sch.colocar("J5", 198.12, 304.8)
    sch.texto("J6 alimenta la placa, el PAM8403 y los LED. No conectar simultáneamente VBUS del USB.\nJ5: 1 = 5 V, 2 = DIN, 3 = GND. R31 cerca del primer LED; C26 junto a J5.\nU6 debe ser AHCT (umbral TTL): un 74HC125 a 5 V no garantiza reconocer 3,3 V.\nLa tira vuelve a GND de potencia; no usar VREF como retorno.", 218.44, 307.34, 1.27)

    sch.completar()
    return sch


if __name__ == "__main__":
    e = construir()
    e.guardar(SALIDA, ["Ecualizador de audio de tres bandas con visualizador ESP32", "2026-10-22", "D.2",
                       "Electrónica II — Universidad de la Costa", "Amplificadores operacionales MCP6004 (riel a riel, 3,3 V)",
                       "Generado desde herramientas/circuito.py"])
    print("Esquemático escrito en", os.path.normpath(SALIDA))

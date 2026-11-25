#!/usr/bin/env python3
"""Modelo mecánico E.5: tarjetas perforadas, controles rotativos y arneses.

Ejecutar desde la raíz del repositorio:
    freecadcmd hardware/E5-perforadas/3d/generar_modelo.py

Toda la geometría sale de e5_layout.py y medidas-componentes.json. Escribe:
    ecualizador-E5-perforadas.FCStd / .step
    stl/*.stl                 (piezas imprimibles)
    pruebas-de-ajuste/*.stl   (probetas recortadas de la tapa, el cuerpo y las barras)
    validacion-3d.json        (comprobaciones dimensionales y pendientes)
    .render/ensamble.json     (malla + trazado de cables para Blender)
"""
from pathlib import Path
import json
import math
import sys

import FreeCAD as App
import Import
import MeshPart
import Part

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e5_layout as E  # noqa: E402

OUT = HERE
STL = OUT / "stl"
FIT = OUT / "pruebas-de-ajuste"
TEMP = OUT / ".render"
STL.mkdir(parents=True, exist_ok=True)
TEMP.mkdir(exist_ok=True)


def vec(p):
    return App.Vector(*p)


AXES = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}


def prim(p):
    if p[0] == "box":
        _, x, y, z, dx, dy, dz = p
        return Part.makeBox(dx, dy, dz, vec((x, y, z)))
    if p[0] == "cone":
        _, x, y, z, r1, r2, h = p
        return Part.makeCone(r1, r2, h, vec((x, y, z)))
    if p[0] == "prismx":
        _, x, dx, pts = p
        pts = list(pts) + [pts[0]]
        return Part.Face(Part.makePolygon([vec((x, y, z)) for y, z in pts])).extrude(vec((dx, 0, 0)))
    if p[0] == "hex":
        _, x, y, z, af, h = p
        r = af / math.sqrt(3)
        pts = [vec((x + r * math.cos(math.radians(90 + 60 * k)), y + r * math.sin(math.radians(90 + 60 * k)), z)) for k in range(7)]
        return Part.Face(Part.makePolygon(pts)).extrude(vec((0, 0, h)))
    _, x, y, z, r, h, axis = p
    return Part.makeCylinder(r, h, vec((x, y, z)), vec(AXES[axis]))


def shape_of(part):
    shapes = [prim(p) for p in part["add"]]
    if part["cut"]:
        base = shapes[0]
        for s in shapes[1:]:
            base = base.fuse(s)
        for c in part["cut"]:
            base = base.cut(prim(c))
        return base
    return shapes[0] if len(shapes) == 1 else Part.makeCompound(shapes)


def rounded_prism(x0, y0, x1, y1, r, z, h):
    """Prisma de planta rectangular con esquinas verticales redondeadas."""
    pts = [(x0 + r, y0), (x1 - r, y0), (x1, y0 + r), (x1, y1 - r), (x1 - r, y1), (x0 + r, y1), (x0, y1 - r), (x0, y0 + r)]
    cen = [(x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r), (x0 + r, y0 + r)]
    edges = []
    for i in range(4):
        a, b = pts[2 * i], pts[2 * i + 1]
        edges.append(Part.makeLine(vec((*a, z)), vec((*b, z))))
        c = cen[i]
        nxt = pts[(2 * i + 2) % 8]
        ang = -45 + 90 * i
        mid = (c[0] + r * math.cos(math.radians(ang)), c[1] + r * math.sin(math.radians(ang)))
        edges.append(Part.Arc(vec((*b, z)), vec((*mid, z)), vec((*nxt, z))).toShape())
    return Part.Face(Part.Wire(edges)).extrude(vec((0, 0, h)))


def tube(points, radius):
    pieces = []
    for a, b in zip(points, points[1:]):
        av, bv = vec(a[:3]), vec(b[:3])
        delta = bv.sub(av)
        if delta.Length > 0.05:
            pieces.append(Part.makeCylinder(radius, delta.Length, av, delta))
    for p in points[1:-1]:
        pieces.append(Part.makeSphere(radius, vec(p[:3])))
    return pieces


def add(doc, name, shape, color, group, meta=None):
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name.replace("+", "mas").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    obj = doc.addObject("Part::Feature", safe)
    obj.Label = name.replace("_", " ")
    obj.Shape = shape
    obj.addProperty("App::PropertyString", "ColorRGB", "Render").ColorRGB = ",".join(f"{v:.4f}" for v in E.COLORS[color])
    obj.addProperty("App::PropertyString", "ColorKey", "Render").ColorKey = color
    obj.addProperty("App::PropertyString", "AssemblyGroup", "Render").AssemblyGroup = group
    obj.addProperty("App::PropertyString", "Meta", "Render").Meta = json.dumps(meta or {}, ensure_ascii=False)
    return obj


def enclosure(doc):
    W, D, H, WALL, FLOOR, LID, R = E.W, E.D, E.H, E.WALL, E.FLOOR, E.LID, E.R_ESQ
    body = rounded_prism(0, 0, W, D, R, 0, H).cut(rounded_prism(WALL, WALL, W - WALL, D - WALL, R - WALL, FLOOR, H))
    for c in E.body_cuts():
        body = body.cut(prim(c))
    lid = rounded_prism(0, 0, W, D, R, H, LID)
    for c in E.lid_cuts():
        lid = lid.cut(prim(c))
    add(doc, "Gabinete_E5_cuerpo", body, "body", "body")
    add(doc, "Tapa_E5_imantada", lid, "lid", "lid")
    return body, lid


def split(shape, keys):
    """Parte una pieza en x = SEAM_X con colas de milano; el macho queda en la mitad izquierda."""
    x0, g, big = E.SEAM_X, E.SEAM_GAP, 1000.0

    def key(y, neck, head, depth, grow):
        pts = [(x0 - 1, y - neck / 2 - grow), (x0, y - neck / 2 - grow), (x0 + depth + grow, y - head / 2 - grow), (x0 + depth + grow, y + head / 2 + grow),
               (x0, y + neck / 2 + grow), (x0 - 1, y + neck / 2 + grow)]
        return Part.Face(Part.makePolygon([App.Vector(px, py, -5) for px, py in pts + [pts[0]]])).extrude(App.Vector(0, 0, 200))

    males = [key(*k, 0) for k in keys]
    sockets = [key(*k, g) for k in keys]
    left = shape.common(Part.makeBox(big, big, big, App.Vector(x0 - big, -big / 2, -big / 2)))
    left = left.multiFuse([shape.common(m) for m in males]).removeSplitter()
    right = shape.common(Part.makeBox(big, big, big, App.Vector(x0 + g, -big / 2, -big / 2)))
    for s_ in sockets:
        right = right.cut(s_)
    assert left.isValid() and right.isValid() and len(left.Solids) == 1 and len(right.Solids) == 1, (len(left.Solids), len(right.Solids))
    return left, right


def solid(shape):
    """Las piezas hechas de varias cajas se funden en cuerpos cerrados."""
    return shape.Solids[0].multiFuse(shape.Solids[1:]).removeSplitter() if len(shape.Solids) > 1 else shape


def fused(doc, shape, key):
    """Cuerpo o tapa con sus encastres (postes, ganchos, setas, cuñas, alojamientos de imán) en una sola pieza."""
    keys = key if isinstance(key, tuple) else (key,)
    extra = [solid(o.Shape) for o in doc.Objects if hasattr(o, "Meta") and json.loads(o.Meta).get("fundir") in keys]
    return shape.multiFuse(extra).removeSplitter() if extra else shape


def fit_coupons(doc, lid, body, halves):
    """Probetas de ajuste: recortes de la geometría real para comprobar encajes antes de imprimir cuerpo y tapa."""
    W, H, LID, WALL = E.W, E.H, E.LID, E.WALL
    get = lambda name: solid(doc.getObject(name).Shape)
    clip = lambda shape, x0, y0, z0, x1, y1, z1: shape.common(Part.makeBox(x1 - x0, y1 - y0, z1 - z0, App.Vector(x0, y0, z0)))
    px = E.CONTROLS[1][3]                       # RV2: B10K comprado
    bx0, by = E.BAR_X0, E.BARS[0][1]
    bar = (bx0 - 23, by - 11, bx0 + 41, by + 11)
    mx, my = E.MAGNETS[0]
    uy, uz = E.USB_C[1], E.USB_C[2]
    _, jy = E.bxy("T1", 0, 45)
    fx, fy, fz, fl, fr = E.FUSE
    zl = H - 6                                  # las probetas de tapa incluyen lo que cuelga de ella
    out = {
        "tapa_potenciometro_B10K": clip(lid, px - 13, E.KNOB_Y - 13, zl, px + 13, E.KNOB_Y + 13, H + LID),
        # Ventana de la pantalla 3,5" con sus cuatro uñas fijas: prueba la ventana completa, el
        # apoyo del módulo al ras y el encaje corredizo del PCB bajo las uñas.
        "tapa_pantalla_CYD": clip(lid, 104, 27, H - 8, 174, 130.0, H + LID),
        "tapa_SW1": clip(lid, E.SW_C[0] - 15, E.SW_C[1] - 13, zl, E.SW_C[0] + 15, E.SW_C[1] + 13, H + LID),
        "tapa_ventana_barra_LED": clip(lid, bar[0], bar[1], zl, bar[2], bar[3], H + LID),
        "barra_difusor_tramo": clip(get("Difusor_opalino_GRAVES"), bar[0], bar[1], 0, bar[2], bar[3], H + LID + 1),
        "barra_cuna_tramo": clip(get("Cuna_tira_GRAVES"), bar[0], bar[1], 0, bar[2], bar[3], H + LID + 1),
        "tapa_teton_iman": clip(lid, mx - 9, my - 9, zl, mx + 9, E.D, H + LID),
        "cuerpo_poste_iman_punta": clip(body, mx - 6, my - 6, H - 13, mx + 6, my + 4.4, H),
        "cuerpo_esquina_tarjeta_T1": clip(body, 0, 0, 0, 18, 34, 13.5),
        "cuerpo_pinza_portafusible": clip(body, fx - fr - 3, fy + 5, 0, W, fy + 14, 18),
        "pared_der_interruptor_y_pasacable": clip(body, W - WALL, 10, 19, W, 66, 46),
        "pared_der_USB_C": clip(body, W - WALL, uy - 15, uz - 12, W, uy + 15, uz + 9),
        "pared_izq_jack_3p5": clip(body, 0, jy - 11, 4, WALL, jy + 11, 23),
    }
    ky = E.SEAM_KEYS_LID[1][0]                  # una cola de milano de la junta, en sus dos colores
    out["union_cola_de_milano_macho"] = clip(halves["tapa_e5_imantada_mitad_izquierda"], E.SEAM_X - 14, ky - 10, H, E.SEAM_X + 8, ky + 10, H + LID)
    out["union_cola_de_milano_hembra"] = clip(halves["tapa_e5_imantada_mitad_derecha"], E.SEAM_X, ky - 10, H, E.SEAM_X + 16, ky + 10, H + LID)
    FIT.mkdir(exist_ok=True)
    for old in FIT.glob("*.stl"):
        old.unlink()
    for name, shape in out.items():
        assert shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 50, (name, len(shape.Solids))
        MeshPart.meshFromShape(Shape=shape, LinearDeflection=.12, AngularDeflection=.35).write(str(FIT / f"{name}.stl"))
    return len(out)


def validate(parts, wires):
    W, D, H, WALL = E.W, E.D, E.H, E.WALL
    issues, checks = [], []

    def check(name, ok, detail):
        checks.append({"comprobacion": name, "cumple": bool(ok), "detalle": detail})
        if not ok:
            issues.append(f"{name}: {detail}")

    rects = []
    for ref, (x, y, w, d, _) in E.BOARDS.items():
        inside = x >= WALL + 2 and y >= WALL + 2 and x + w <= W - WALL - 2 and y + d <= D - WALL - 2
        check(f"{ref} dentro del volumen útil", inside, f"x {x}..{x + w}, y {y}..{y + d}")
        for other, ox, oy, ow, od in rects:
            check(f"{ref} sin solape con {other}", not (x < ox + ow and x + w > ox and y < oy + od and y + d > oy), "planta")
        rects.append((ref, x, y, w, d))
    # Zona de alimentación fuera de las tarjetas.
    zone = [("bornera +5V", E.BLK_P_X, E.BLK_Y0, E.BLOCK[1], E.BLOCK[0]), ("bornera GND", E.BLK_N_X, E.BLK_Y0, E.BLOCK[1], E.BLOCK[0]),
            ("elevador 12 V", E.BOOST[0], E.BOOST[1], E.BOOST[2], E.BOOST[3])]
    for name, x, y, w, d in zone:
        clash = [r[0] for r in rects if x < r[1] + r[3] and x + w > r[1] and y < r[2] + r[4] and y + d > r[2]]
        check(f"{name} sin solape con tarjetas", not clash and x + w <= W - WALL, f"x {x}..{x + w}, y {y}..{y + d} {clash}")
    # Altura: lo montado en la tapa no toca lo montado en las tarjetas.
    interior = [p for p in parts if p["group"] == "interior"]
    lidp = [p for p in parts if p["group"] == "lid"]
    worst = None
    for lp in lidp:
        lb = E.part_bbox(lp)
        if lb[2] >= H:
            continue
        for ip in interior:
            ib = E.part_bbox(ip)
            if lb[0] < ib[3] and lb[3] > ib[0] and lb[1] < ib[4] and lb[4] > ib[1]:
                gap = lb[2] - ib[5]
                if worst is None or gap < worst[0]:
                    worst = (gap, lp["name"], ip["name"])
    check("holgura vertical tapa/tarjetas >= 5 mm", worst is None or worst[0] >= 5.0,
          f"mínima {worst[0]:.1f} mm entre {worst[1]} y {worst[2]}" if worst else "sin superposición en planta")
    top_interior = max(E.part_bbox(p)[5] for p in interior)
    check("componentes interiores bajo la tapa", top_interior < H - 1, f"cota máxima interior {top_interior:.1f} mm; cara interior de tapa {H} mm")
    # Controles.
    names = [p["name"] for p in parts]
    b10k = [p for p in parts if p["meta"].get("tipo") == "B10K"]
    a10k = [p for p in parts if p["meta"].get("tipo") == "A10K"]
    check("exactamente tres B10K montados", len(b10k) == 3, ", ".join(p["meta"]["ref"] for p in b10k))
    check("un B10K queda como repuesto sin montar", E.B10K_COMPRADOS - len(b10k) == 1, f"declarados {E.B10K_COMPRADOS}, montados {len(b10k)}")
    check("dos posiciones A10K marcadas pendientes", len(a10k) == 2 and all("PENDIENTE" in p["name"] for p in a10k), ", ".join(p["name"] for p in a10k))
    check("cinco controles rotativos", len(E.CONTROLS) == 5 and sum(n.startswith("Perilla_") and n.endswith("PENDIENTE_COMPRA") for n in names) == 5, "NIVEL, GRAVES, MEDIOS, AGUDOS, VOLUMEN")
    bad = [n for n in names + [w["name"] for w in wires] if any(t in n.lower() for t in ("desliz", "slider", "slide"))]
    check("ningún potenciómetro deslizable", not bad, str(bad))
    xs = [c[3] for c in E.CONTROLS]
    pitch = min(b - a for a, b in zip(xs, xs[1:]))
    check("separación entre perillas >= 30 mm", pitch >= 30, f"{pitch} mm entre ejes")
    free = E.M["Potenciometro-A10K"]["reserva_en_tapa"]["diametro_libre"]
    check("reserva libre alrededor de cada A10K", pitch - E.POT["diametro_cuerpo"] / 2 >= free / 2, f"cilindro libre de {free} mm")
    # Tira LED.
    check("tres barras de 4 píxeles = 12 píxeles lógicos", len(E.BARS) * E.PX_PER_BAND == 12, f"{len(E.BARS)} x {E.PX_PER_BAND} píxeles de {E.PIXEL} mm")
    check("barra de 200 mm cabe en la tapa", E.BAR_X0 >= 20 and E.BAR_LEN == 200.0, f"x {E.BAR_X0}..{E.BAR_X0 + E.BAR_LEN}")
    # Parlantes.
    sp = [p for p in parts if "WS14595" in p["name"] and p["name"].endswith("marco_100x45")]
    mag = [p for p in parts if p["name"].startswith("Iman_")]
    check("cuatro pares de imanes y ninguna bisagra", len(mag) == 8 and not [n for n in names if "bisagra" in n.lower()], f"{len(mag)} imanes")
    check("dos parlantes del conjunto WS-14595", len(sp) == 2, f"{len(sp)} transductores, un conector")
    # USB del DevKit frente a su ventana.
    check("micro-USB del ESP32 DevKit V1 alineado con la pared derecha", abs(E.USB_C[0] - (W - WALL)) <= 2.5, f"boca en x = {E.USB_C[0]:.1f}; pared interior en {W - WALL}")
    # Cables: extremos dentro del gabinete y cruces solo en la bisagra.
    outside = []
    for w in wires:
        for x, y, z, tag in w["pts"]:
            if not (WALL - .1 <= x <= W - WALL + .1 and WALL - .1 <= y <= D - WALL + .1 and E.FLOOR - .1 <= z <= H + .1):
                outside.append(w["name"])
                break
    check("cables dentro del gabinete cerrado", not outside, str(sorted(set(outside))))
    crossing = [w["name"] for w in wires if len({p[3] for p in w["pts"]}) == 2]
    check("cables tapa-cuerpo cruzan junto al borde frontal", all(any(a[3] != b[3] and max(a[1], b[1]) <= 9 for a, b in zip(w["pts"], w["pts"][1:])) for w in wires if w["name"] in crossing),
          f"{len(crossing)} conductores cruzan por el frente")
    pot_len = {}
    for w in wires:
        if w["name"].startswith("RV"):
            pot_len[w["name"]] = round(sum(math.dist(a[:3], b[:3]) for a, b in zip(w["pts"], w["pts"][1:])), 1)
    check("cables de potenciómetros <= 120 mm", max(pot_len.values()) <= 120, f"máximo {max(pot_len.values())} mm")
    tft_len = max(sum(math.dist(a[:3], b[:3]) for a, b in zip(w["pts"], w["pts"][1:])) for w in wires if w["name"].startswith("CYD_"))

    mounted = {"T1": "U1; R1-R12; C1-C2; C4; C8-C14; J1; RV1 (en tapa, 3 hilos)", "T2": "U2; R13-R16; R19-R26; C3; C5; C15-C21; J2; J3; PAM8403; RV2-RV5 (en tapa)",
               "T3": "U3; U4; R17-R18; R27-R29; C6-C7; C22-C24; D1-D3", "T4": "U5 ESP32 DevKit V1 30P; U6 74HCT245; R30-R40; C25-C26; J5; J6; J7 alimentación de la pantalla +5V/GND (datos por ESP-NOW; UART de respaldo, propuesto); SW1 (en tapa, 2 hilos)"}
    counts = {}
    for ref, refs in E.BOARD_PARTS.items():
        counts[ref] = {"R": sum(r.startswith("R") and r[1:].isdigit() for r in refs), "C": sum(r.startswith("C") and r[1].isdigit() for r in refs),
                       "D": sum(r.startswith("D") and r[1:].isdigit() for r in refs), "U": sum(r.startswith("U") for r in refs)}
    tot = {k: sum(c[k] for c in counts.values()) for k in "RCDU"}
    check("40 resistencias, 26 capacitores, 3 diodos, 6 integrados/módulos U", tot == {"R": 40, "C": 26, "D": 3, "U": 6}, json.dumps(tot))

    pendientes = [
        "A10K de RV1 (NIVEL) y RV5 (VOLUMEN): NO comprados. Envolvente supuesta igual al B10K; cota pendiente de medir. Los dos P-20K logarítmicos comprados son candidatos sin validar eléctricamente.",
        "B10K de RV2-RV4: el comprador declara 4 unidades (3 montadas + 1 repuesto); falta factura o albarán en COMPONENTES-COMPRADOS-VERIFICADOS.md y falta medir cuerpo, eje y rosca.",
        "Tira BTF-LIGHTING B0BW5T6HW4: es FCOB WS2811 de 12 V. El equipo solo tiene 5 V: el elevador 5→12 V modelado no está comprado ni en el esquema.",
        "Firmware: usa NEO_GRB; la tira publica orden BRG. Los 12 píxeles lógicos se conservan (3 barras × 4 CI), pero el orden de color debe probarse en la tira real.",
        "Parlantes WS-14595: la envolvente 100×45×21 mm se aplicó a cada parlante (falta medir). El conector trae 4 hilos (2 rojos, 2 negros): un parlante por canal del PAM8403. El esquema solo alimenta una entrada (AMP_IN): hay que puentear L y R en el módulo y actualizar el esquema.",
        "ESP32 DevKit V1 30P: NO comprado (decisión 2026-11-24; sustituye al ESP32S V1.1 USB-C de 38 pines, que queda liberado como repuesto). Envolvente conservadora: las fichas de los clones discrepan y la separación de hileras de 22,86 mm es supuesta. El esquema E.5 sigue dibujando el ESP32S de 38 pines: revisar pines usados antes de perforar T4.",
        "PAM8403, perforadas y fuente: figuran en carritos o los declara el comprador; sin albarán verificado. Medir antes de perforar.",
        "Difusores: relieve hexagonal impreso (fondo 0,5 mm, nervio 1,1 mm, celdas de 5 mm, patrón repetido cada 25 mm). Geometría propia inspirada en el Duality Infinity 3DHex de Andy Huot; no se usan sus archivos (pista de unos 36 mm de ancho frente a 17 mm entre barras, y licencia de uso personal). Difusión real con la tira FCOB sin probar.",
        "Pantalla ESP32-3248S035 (RECIBIDA el 2026-11-24; la publicación anunciaba la 2432S028 de 2,8\"): panel ST7796 de 3,5\" 320x480 confirmado empíricamente con el firmware. Cotas del PCB (97,5 x 56,5) conservadoras de la comunidad; módulo de 84 x 55 x 4 al ras del extremo frontal SUPUESTO, por medir antes de imprimir la tapa definitiva. Montada en VERTICAL; para que quepa, la fila de perillas se adelantó a y 23 y la retención son cuatro uñas fijas (la cuna de GRAVES bloquea la salida). Los DATOS viajan por ESP-NOW (decisión del usuario); el arnés dibujado solo lleva +5 V/GND a VIN de P1, con el UART de P1 como respaldo por cable. Nada de esto está en el esquema eléctrico. SW1 está en la fila de perillas (249, 23).",
        "Borneras puente, portafusible e interruptor: envolventes conservadoras; interruptor general de 5 A DC sin comprar.",
        "Perillas e imanes de 6×2 mm (4 pares): sin comprar; geometría supuesta. La tapa no tiene bisagras: nada la sostiene abierta y la fuerza de los imanes no está comprobada.",
        "Documentos en conflicto: BOM/LISTA piden pares +5V/GND propios desde las borneras para T1-T3, y conexiones-entre-tarjetas.csv también lleva +5V/GND por JBUS desde T4. El modelo dibuja ambos; hay que elegir uno antes de cablear.",
        f"Alimentación de la pantalla: el arnés de dos hilos dibujado mide {tft_len:.0f} mm por el borde frontal. El consumo de la 3248S035 a 5 V está por medir; el enlace ESP-NOW debe probarse con las dos placas encendidas.",
        "Colocación agujero por agujero de cada tarjeta: no realizada. Las posiciones de componentes son representativas, no una guía de soldadura.",
        "Gabinete y tapa no impresos ni probados: holguras de impresión, rigidez y ventilación sin validar.",
    ]
    report = {
        "revision": "E.5", "fecha_fuente": E.MEDIDAS["revision"],
        "gabinete_mm": [W, D, H + E.LID], "tapa": {"cierre": "4 pares de imanes 6x2 mm, sin bisagras", "apertura": "bascula sobre el borde frontal", "apertura_grados_en_el_video": E.LID_OPEN_DEG},
        "tarjetas": {k: list(v[:4]) for k, v in E.BOARDS.items()}, "montaje_por_tarjeta": mounted, "conteo_por_tarjeta": counts,
        "controles": [{"ref": r, "funcion": f, "tipo": k, "x": x, "y": E.KNOB_Y, "compra": e} for r, f, k, x, e, _ in E.CONTROLS],
        "b10k": {"declarados": E.B10K_COMPRADOS, "montados": len(b10k), "repuesto_no_modelado": E.B10K_COMPRADOS - len(b10k)},
        "a10k": {"comprados": 0, "posiciones": len(a10k), "estado": "pendiente; candidato P-20K sin validar"},
        "deslizables": 0,
        "tira_led": {"producto": "BTF-LIGHTING FCOB WS2811 12 V 720 LED/m", "tramos": len(E.BARS), "mm_por_tramo": E.BAR_LEN, "pixeles_logicos": 12, "mm_por_pixel": E.PIXEL},
        "parlantes": 2, "cables": len(wires), "longitud_cables_potenciometro_mm": pot_len, "longitud_arnes_UART_CYD_mm": round(tft_len, 1),
        "comprobaciones": checks, "issues": issues, "valid": not issues,
        "pendientes_y_supuestos": pendientes,
        "alcance": "Validación geométrica por envolventes. No sustituye pruebas eléctricas, mecánicas ni la presentación física de las piezas.",
    }
    (OUT / "validacion-3d.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if issues:
        raise RuntimeError("\n".join(issues))
    return report


def main():
    parts, wires = E.build_all()
    validate(parts, wires)
    doc = App.newDocument("Ecualizador_E5_Perforadas")
    body0, lid0 = enclosure(doc)
    hidden = []
    for p in parts:
        obj = add(doc, p["name"], shape_of(p), p["color"], p["group"], p["meta"])
        if p["meta"].get("solo_mitades"):
            hidden.append(obj.Name)
    harness = {}
    for w in wires:
        key = (w["harness"], w["color"])
        harness.setdefault(key, []).extend(tube(w["pts"], w["dia"] / 2))
    for (name, color), pieces in harness.items():
        add(doc, f"{name}__{color[2:]}", Part.makeCompound(pieces), color, "wire")
    doc.recompute()
    doc.saveAs(str(OUT / "ecualizador-E5-perforadas.FCStd"))
    objects = [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull() and o.Name not in hidden]
    Import.export(objects, str(OUT / "ecualizador-E5-perforadas.step"))
    for old in STL.glob("*.stl"):
        old.unlink()
    # Piezas imprimibles: el cuerpo y la tapa llevan fundidos sus encastres; el resto son piezas sueltas que encajan.
    lid, body = fused(doc, lid0, "tapa"), fused(doc, body0, "cuerpo")
    printable = {"gabinete_e5_cuerpo": body, "tapa_e5_imantada": lid}       # de una pieza (por defecto)
    # Opción en dos mitades con cola de milano; solo ellas llevan los refuerzos de la junta.
    for name, shape, keys in (("gabinete_e5_cuerpo", fused(doc, body0, ("cuerpo", "cuerpo_mitades")), E.SEAM_KEYS_BODY), ("tapa_e5_imantada", lid, E.SEAM_KEYS_LID)):
        printable[f"{name}_mitad_izquierda"], printable[f"{name}_mitad_derecha"] = split(shape, keys)
    halves = {k: v for k, v in printable.items() if "tapa" in k and "mitad" in k}
    printable.update({o.Name.lower(): solid(o.Shape) for o in objects if json.loads(o.Meta).get("pieza_impresa")})
    for name, shape in printable.items():
        assert shape.isValid() and len(shape.Solids) == 1, (name, len(shape.Solids))
        MeshPart.meshFromShape(Shape=shape, LinearDeflection=.12, AngularDeflection=.35).write(str(STL / f"{name}.stl"))
    coupons = fit_coupons(doc, lid, body, halves)
    # Malla para Blender. Los cables no se teselan: Blender los reconstruye como curvas.
    data = []
    for obj in objects:
        if obj.AssemblyGroup == "wire":
            continue
        vertices, faces = obj.Shape.tessellate(.12)
        data.append({"name": obj.Name, "label": obj.Label, "vertices": [tuple(round(c, 4) for c in v) for v in vertices], "faces": faces,
                     "color": obj.ColorKey, "group": obj.AssemblyGroup, "meta": json.loads(obj.Meta)})
    (TEMP / "ensamble.json").write_text(json.dumps({"layout": E.export_layout(), "objects": data}), encoding="utf-8")
    print(f"E.5 CAD: {len(objects)} objetos, {len(wires)} cables; {E.W} x {E.D} x {E.H + E.LID} mm; {len(printable)} STL; {coupons} probetas de ajuste")


main()

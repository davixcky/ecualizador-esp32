#!/usr/bin/env python3
"""Genera la guía consolidada de montaje y pruebas por tarjeta (E.5).

Para cada tarjeta T1-T4: recortes del esquema maestro, lista de componentes
(lista-por-tarjeta.csv cruzada con BOM-precision.csv) y procedimiento de
prueba en banco con DDS y osciloscopio. Los valores de ganancia y tensión son
esperados según el modelo ideal, no medidas de placa.
"""
import csv
import re
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware" / "E5-perforadas"
SRC = HW / "proyecto" / "ecualizador-perforadas-maestro.pdf"
OUT = HW / "guia-pruebas-tarjetas.pdf"

A4L = (842, 595)
M = 30
BLUE = (0.05, 0.18, 0.55)
GREEN = (0.05, 0.45, 0.25)
GRAY = (0.35, 0.35, 0.35)
DARK = (0.1, 0.1, 0.1)

TOTAL_PAGES = 10

# Caracteres fuera de Latin-1 que la fuente Helvetica imprimiría como "?".
_SUBS = {
    "≈": "aprox. ", "–": "-", "—": "-", "×": "x",
    "Ω": " ohm", "μ": "u", "→": "->", "←": "<-",
    "≤": "<=", "≥": ">=", "π": "pi", "√": "sqrt",
    "…": "...", "’": "'", "‘": "'", "“": '"',
    "”": '"', "τ": "tau",
}


def sanitize(text):
    for bad, good in _SUBS.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def mmrect(src_page, x1, y1, x2, y2):
    sx = src_page.rect.width / 594.0
    sy = src_page.rect.height / 420.0
    return fitz.Rect(x1 * sx, y1 * sy, x2 * sx, y2 * sy)


def page(doc, title, subtitle=""):
    p = doc.new_page(width=A4L[0], height=A4L[1])
    p.insert_text((M, 27), sanitize(title), fontsize=16, fontname="hebo", color=BLUE)
    if subtitle:
        p.insert_text((M, 44), sanitize(subtitle), fontsize=8.5, color=GRAY)
    p.draw_line((M, 51), (A4L[0] - M, 51), color=BLUE, width=0.8)
    p.insert_text((A4L[0] - 150, A4L[1] - 15),
                  "E.5 · tarjetas perforadas", fontsize=7, color=GRAY)
    n = len(doc)
    p.insert_text((M, A4L[1] - 15), "pág. %d/%d" % (n, TOTAL_PAGES),
                  fontsize=7, color=GRAY)
    return p


def clip(p, src, target, coords, caption):
    p.insert_text((target.x0, target.y0 - 4), sanitize(caption),
                  fontsize=8.5, fontname="hebo", color=GREEN)
    body = fitz.Rect(target.x0, target.y0 + 2, target.x1, target.y1)
    p.show_pdf_page(body, src.parent, 0, clip=mmrect(src, *coords),
                    keep_proportion=True)
    p.draw_rect(body, color=(0.75, 0.75, 0.75), width=0.4)


def text_box(p, rect, title, lines, size=8.5, lineheight=1.15, gap=True):
    p.draw_rect(rect, color=(0.65, 0.65, 0.65), fill=(0.98, 0.98, 0.98), width=0.5)
    p.insert_text((rect.x0 + 8, rect.y0 + 14), sanitize(title),
                  fontsize=9.5, fontname="hebo", color=BLUE)
    sep = "\n\n" if gap else "\n"
    body = sanitize(sep.join(lines))
    inner = fitz.Rect(rect.x0 + 8, rect.y0 + 23, rect.x1 - 8, rect.y1 - 6)
    leftover = p.insert_textbox(inner, body, fontsize=size,
                                lineheight=lineheight, color=DARK)
    if leftover < 0:
        raise SystemExit("Texto recortado en la caja '%s' (faltan %.0f pt)"
                         % (title, -leftover))
    return leftover


def fit_cell(text, width, fontsize):
    text = sanitize(text)
    if fitz.get_text_length(text, fontsize=fontsize) <= width:
        return text
    while text and fitz.get_text_length(text + "...", fontsize=fontsize) > width:
        text = text[:-1]
    return text + "..."


def table(p, x, y, widths, headers, rows, fs=7.0, row_h=10.5):
    total_w = sum(widths)
    head_h = 13.0
    p.draw_rect(fitz.Rect(x, y, x + total_w, y + head_h),
                color=(0.5, 0.5, 0.5), fill=(0.88, 0.91, 0.97), width=0.5)
    cx = x
    for w, h in zip(widths, headers):
        p.insert_text((cx + 3, y + 9.5), sanitize(h), fontsize=fs,
                      fontname="hebo", color=BLUE)
        cx += w
    yy = y + head_h
    for i, row in enumerate(rows):
        fill = (0.975, 0.975, 0.975) if i % 2 else (1, 1, 1)
        p.draw_rect(fitz.Rect(x, yy, x + total_w, yy + row_h),
                    color=(0.8, 0.8, 0.8), fill=fill, width=0.3)
        cx = x
        for w, cell in zip(widths, row):
            p.insert_text((cx + 3, yy + 7.5), fit_cell(str(cell), w - 6, fs),
                          fontsize=fs, color=DARK)
            cx += w
        yy += row_h
    p.draw_rect(fitz.Rect(x, y, x + total_w, yy), color=(0.5, 0.5, 0.5), width=0.6)
    return yy


# ---------------------------------------------------------------- datos CSV

REF_RX = re.compile(r"^([A-Z]+)(\d+)(?:-[A-Z]*(\d+))?$")


def expand_refs(field, seps=" ;,"):
    for ch in seps:
        field = field.replace(ch, " ")
    out = []
    for tok in field.split():
        m = REF_RX.match(tok.strip())
        if not m:
            continue
        pre, a, b = m.group(1), int(m.group(2)), m.group(3)
        b = int(b) if b else a
        out.extend("%s%d" % (pre, n) for n in range(a, b + 1))
    return out


def compress_refs(refs):
    """['R19','R20','R21','R24'] -> 'R19-R21, R24'"""
    def key(r):
        m = REF_RX.match(r)
        return (m.group(1), int(m.group(2)))
    refs = sorted(set(refs), key=key)
    parts, run = [], [refs[0]]
    for r in refs[1:]:
        p0, n0 = key(run[-1])
        p1, n1 = key(r)
        if p0 == p1 and n1 == n0 + 1:
            run.append(r)
        else:
            parts.append(run)
            run = [r]
    parts.append(run)
    return ", ".join(r[0] if len(r) == 1 else "%s-%s" % (r[0], r[-1])
                     for r in parts)


def load_bom():
    ref_db = {}
    with open(HW / "BOM-precision.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for ref in expand_refs(row["referencias"]):
                # Primera aparición gana: los zócalos (Mecanico) comparten
                # referencia con los circuitos integrados que alojan.
                ref_db.setdefault(ref, (row["categoria"], row["valor"],
                                        row["especificacion"]))
    return ref_db


def load_boards():
    boards = {}
    with open(HW / "lista-por-tarjeta.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            boards[row["tarjeta"]] = expand_refs(row["componentes"])
    return boards


def load_harness():
    with open(HW / "conexiones-entre-tarjetas.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# Notas por referencia (la primera que coincida dentro de un grupo).
NOTES = {
    "U5": "Esquema: DevKitC 38P; se usará DevKit V1 30P (pendiente de compra)",
    "J4": "Enlace TFT de la rev. anterior; pantalla actual por ESP-NOW",
    "RV1": "NIVEL; rotativo log (A10K sin comprar)",
    "RV5": "VOLUMEN; rotativo log (A10K sin comprar)",
    "RV2": "Rotativos B10K ('deslizables' en el maestro = rev. anterior)",
    "C3": "Montar junto a J3 (PAM8403); polaridad",
    "C4": "Directo entre pines 4 y 11 de U1",
    "C5": "Desacople de U2 (el maestro lo dibuja en la zona T1-A)",
    "C6": "Desacoples de U3/U4 (dibujados en la zona T1-A del maestro)",
    "R2": "Divisor VDIV del VREF; pareja crítica",
    "R17": "Inversor de medios, ganancia -1",
    "R33": "Atenuadores ADC = VREF + (RAW-VREF)/2; junto al ESP32",
    "R27": "Descarga de los detectores (tau = 22 ms con 100 nF)",
    "D1": "Banda (cátodo) según esquema; diodo dentro del lazo",
    "C22": "Retención de pico de los detectores",
    "J6": "Con fusible 3 A e interruptor en serie",
    "SW1": "Pulsador BTN: alto en reposo, 0 V pulsado",
    "J1": "Entrada de línea 3,5 mm (T-R-S por nombre)",
    "J2": "Salida de línea 3,5 mm",
    "J3": "Al modulo PAM8403",
    "J5": "A la tira WS2812B: 1 = 5V, 2 = DIN, 3 = GND",
    "U6": "DIR pin 1 a +5V; /OE pin 19 a GND",
    "C26": "Junto a J5; polaridad",
    "R31": "En serie con DIN, cerca del primer LED",
}

ORDER = {"U": 0, "R": 1, "C": 2, "D": 3, "RV": 4, "J": 5, "SW": 6}


def board_rows(refs, ref_db):
    groups = {}
    order = []
    for ref in refs:
        if ref not in ref_db:
            raise SystemExit("Referencia sin entrada en BOM-precision.csv: " + ref)
        key = ref_db[ref]
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(ref)

    def sort_key(key):
        first = groups[key][0]
        m = REF_RX.match(first)
        return (ORDER.get(m.group(1), 9), m.group(1), int(m.group(2)))

    rows = []
    for key in sorted(order, key=sort_key):
        cat, val, spec = key
        refs_g = groups[key]
        note = next((NOTES[r] for r in refs_g if r in NOTES), "")
        rows.append((compress_refs(refs_g), str(len(refs_g)), val,
                     "%s; %s" % (cat, spec), note))
    return rows


# ------------------------------------------------------------------ páginas

def page_overview(doc):
    p = page(doc, "Guía de montaje y pruebas por tarjeta",
             "Ecualizador LM324 + ESP32 · cuatro tarjetas perforadas "
             "comprobables de forma independiente")
    boxes = [
        (fitz.Rect(30, 70, 220, 168), "T1 · ENTRADA + U1",
         ["VREF 1,65 V", "PRE (G = 3,2)", "GRAVES fc 232 Hz", "MED_HP fc 409 Hz"]),
        (fitz.Rect(228, 70, 418, 168), "T2 · FILTROS + U2",
         ["MEDIOS fc 2,3 kHz", "AGUDOS fc 4,1 kHz", "SUMADOR + SALIDA",
          "ANTIALIAS 4,95 kHz"]),
        (fitz.Rect(426, 70, 616, 168), "T3 · U3 + U4",
         ["INVERSOR MEDIOS", "3 DETECTORES", "tau = 22 ms", "ADC_x_RAW"]),
        (fitz.Rect(624, 70, 812, 168), "T4 · CONTROL",
         ["ESP32 (30P, por comprar)", "R33-R40 (ADC)", "74HCT245 + LED",
          "Pantalla vía ESP-NOW"]),
    ]
    for rect, title, lines in boxes:
        text_box(p, rect, title, lines, 7.6, gap=False)

    text_box(p, fitz.Rect(30, 186, 400, 348),
             "BUS DE ALIMENTACIÓN EN ESTRELLA · JBUS",
             ["1  +5V    desde la fuente externa / T4",
              "2  GND    retorno común de potencia y señal",
              "3  +3V3   hacia T1 (solo para generar VREF)",
              "4  VREF   1,65 V generado en T1 para T2/T3/T4",
              "VREF no reemplaza GND. +5V y GND con cable más grueso que "
              "las señales."], 8.3, gap=False, lineheight=1.5)

    text_box(p, fitz.Rect(412, 186, 812, 348), "SEGURIDAD Y TÉCNICA DE MEDIDA",
             ["Masa del DDS y pinzas del osciloscopio siempre a GND; VREF "
              "(1,65 V) es una referencia, nunca un retorno.",
              "Sondas x10 con el factor ajustado en el instrumento. Acoplo DC "
              "para ver el centro de 1,65 V; AC para comparar amplitudes.",
              "Generador en carga Hi-Z: si el DDS asume 50 ohm, la amplitud "
              "real sobre el circuito se duplica.",
              "Los LM324 trabajan a +5 V (pin 4) y GND (pin 11); VREF se "
              "genera en T1 desde +3.3VA. Documentos antiguos citan MCP6004 a "
              "3,3 V y potenciómetros deslizables: la revisión vigente usa "
              "LM324 a 5 V y potenciómetros rotativos B10K."],
             7.6, gap=False, lineheight=1.25)

    text_box(p, fitz.Rect(30, 364, 812, 528),
             "ORDEN DE PRUEBA RECOMENDADO · cada tarjeta sola antes de interconectar",
             ["1. T1 (págs. 2-3): VREF = 1,65 V, preamplificador y filtros de "
              "graves y medios (pasa-altas).",
              "2. T2 (págs. 4-5): filtros finales, potenciómetros, sumador y "
              "salida, tomando VREF de la T1 ya validada.",
              "3. T3 (págs. 6-7): inversor de medios y detectores de pico.",
              "4. T4 (págs. 8-9): tensiones y atenuadores SIN el ESP32; el "
              "DevKit se inserta al final (aún está pendiente de compra).",
              "5. Integración por etapas según la página 10.",
              "Mientras no exista el ESP32, la línea +3V3 de JBUS debe salir "
              "de una fuente de banco de 3,3 V. Todos los valores de esta "
              "guía son esperados según el modelo ideal: ninguno ha sido "
              "medido en placa todavía."], 8.4, gap=False, lineheight=1.45)
    return p


def page_schematic(doc, title, subtitle, clips, src, note_box=None,
                   bottom_note=None):
    p = page(doc, title, subtitle)
    for target, coords, caption in clips:
        clip(p, src, target, coords, caption)
    if note_box:
        rect, btitle, lines, size = note_box
        text_box(p, rect, btitle, lines, size, gap=False, lineheight=1.3)
    if bottom_note:
        rect, text = bottom_note
        leftover = p.insert_textbox(rect, sanitize(text), fontsize=8.2,
                                    lineheight=1.2, color=DARK, align=1)
        if leftover < 0:
            raise SystemExit("Nota inferior recortada en '%s'" % title)
    return p


def page_procedure(doc, board, title, rows, harness_note, cols, failures):
    p = page(doc, "%s · componentes y prueba en banco" % board, title)
    widths = [86, 28, 118, 262, 288]
    headers = ["Referencias", "Cant.", "Valor / parte", "Tipo y especificación",
               "Nota"]
    bottom = table(p, M, 64, widths, headers, rows)
    p.insert_text((M, bottom + 10), sanitize(harness_note), fontsize=7.2,
                  color=GRAY)
    top = bottom + 20
    if top > 300:
        raise SystemExit("Tabla de %s demasiado alta" % board)
    col_x = [(30, 287), (297, 554), (564, 812)]
    titles = ["1 · ANTES DE ENERGIZAR", "2 · ENCENDIDO (MULTÍMETRO)",
              "3 · SEÑAL (DDS + OSCILOSCOPIO)"]
    for (x0, x1), btitle, lines in zip(col_x, titles, cols):
        text_box(p, fitz.Rect(x0, top, x1, 516), btitle, lines, 7.4,
                 gap=False, lineheight=1.28)
    text_box(p, fitz.Rect(30, 524, 812, 572), "FIRMAS DE FALLO COMUNES",
             [failures], 7.2, gap=False, lineheight=1.15)
    return p


def page_integration(doc, harness, pendientes):
    p = page(doc, "Integración de las cuatro tarjetas",
             "Cablear por nombre de señal; una sola ruta de alimentación; "
             "pendientes declarados al pie")
    rows = [(h["arnes"], h["pin"], h["senal"],
             "%s -> %s" % (h["origen"], h["destino"]), h["nota"])
            for h in harness]
    widths = [38, 24, 88, 68, 234]
    table(p, M, 64, widths, ["Arnés", "Pin", "Señal", "Ruta", "Nota"],
          rows, fs=6.6, row_h=10.0)

    text_box(p, fitz.Rect(30, 300, 482, 408), "PANTALLA Y ALIMENTACIÓN · AVISOS",
             ["Pantalla: el maestro y la BOM aún dibujan el enlace por cable "
              "(J4 SPI a la Waveshare; UART como respaldo). Decisión vigente: "
              "pantalla ESP32-3248S035 separada, datos por ESP-NOW, y su arnés "
              "solo lleva +5V y GND (no figura en conexiones-entre-tarjetas.csv).",
              "Alimentación: la BOM/LISTA piden pares +5V/GND propios desde "
              "las borneras para T1-T3 y este CSV también los lleva por JBUS "
              "desde T4. Elegir UNA sola ruta antes de cablear para evitar "
              "lazos de masa."], 7.3, gap=True, lineheight=1.22)

    text_box(p, fitz.Rect(494, 64, 812, 408), "ORDEN DE ENCENDIDO INTEGRADO",
             ["1. T4 sin ESP32: sin cortos; tensiones y atenuadores "
              "verificados (pág. 9).",
              "2. T1 sola: VREF = 1,65 V y reposo de sus salidas.",
              "3. T1 + T2 (JBUS + JAB): respuesta de las tres bandas y "
              "EQ_OUT con el puente M_W-M_INV provisional.",
              "4. Añadir T3 (JBC): QUITAR el puente; medir M_INV y los "
              "tres ADC_x_RAW.",
              "5. Conectar JB4 y JC4 a T4; revalidar los divisores con "
              "señal real; solo entonces insertar el ESP32.",
              "6. Al final: PAM8403 (J3), tira LED (J5) y pantalla por "
              "ESP-NOW (+5V/GND).",
              "Prueba de conjunto: música o barrido del DDS en J1; cada "
              "ADC_x debe seguir la envolvente de su banda y la pantalla "
              "remota debe reflejarlo (esperado según el modelo)."],
             7.5, gap=False, lineheight=1.42)

    half = (len(pendientes) + 1) // 2
    text_box(p, fitz.Rect(30, 418, 418, 574),
             "PENDIENTES · NI MEDIDO NI COMPRADO (validacion-3d.json)",
             pendientes[:half], 6.9, gap=False, lineheight=1.18)
    text_box(p, fitz.Rect(426, 418, 812, 574), "PENDIENTES (continuación)",
             pendientes[half:], 6.9, gap=False, lineheight=1.18)
    return p


# ---------------------------------------------------------------- contenido

T1_COLS = [
    ["- Sin alimentar y con el zócalo de U1 vacío: revisar soldaduras, "
     "puentes y la muesca del zócalo DIP-14.",
     "- Continuidad: ningún corto entre +5V-GND, +3V3-GND ni VREF-GND.",
     "- +5V llega al pin 4 del zócalo y GND al pin 11; C4 (100 nF) "
     "directo entre ambos.",
     "- Nodo VDIV (union R2/R3): aprox. 10 kohm contra GND (R3) y "
     "aprox. 10 kohm contra +3.3VA (R2).",
     "- J1 y RV1 (rotativo, terminales 1-2-3) cableados por nombre; "
     "C9 (1 uF film) en serie con la entrada."],
    ["- Alimentar +5V y +3V3 desde la fuente de banco (el +3V3 "
     "definitivo lo dará el ESP32 de T4, aún sin comprar).",
     "- Con el zócalo vacío: pin 4 = 5,0 V, pin 11 = 0 V; +3.3VA "
     "aprox. 3,3 V tras R1; VDIV = 1,65 V (esperado según el modelo: "
     "3,3 V x R3/(R2+R3)).",
     "- Apagar, insertar U1 (LM324N), reencender: VREF = 1,65 V a la "
     "salida de U1A.",
     "- Sin señal: PRE, GRAVES y MED_HP en reposo cerca de 1,65 V.",
     "- Consumo de pocos mA; si la fuente limita corriente, buscar "
     "un corto antes de seguir."],
    ["- DDS: seno, 50 mVpp, offset 1,65 V, carga Hi-Z, al jack J1 "
     "(puentear punta y anillo para mono). Sondas x10; masas a GND.",
     "- CH1 en PRE: con RV1 al máximo, PRE aprox. 3,2 x Ventrada "
     "(G = 1 + R7/R8; esperado según el modelo).",
     "- Ajustar el DDS hasta 200 mVpp medidos en PRE. A 100 Hz "
     "(2 ms/div): CH2 en GRAVES = 0,9-1,0 x PRE (LP fc aprox. 232 Hz).",
     "- A 1 kHz (0,2 ms/div): GRAVES cae a aprox. 0,05 x PRE; "
     "MED_HP aprox. 1,0 x PRE (HP fc aprox. 409 Hz).",
     "- A 100 Hz: MED_HP aprox. 0,06 x PRE. Registrar Vpp de entrada "
     "y salida y calcular la ganancia de cada punto."],
]
T1_FAIL = ("Sin VREF (R2/R3 o U1A mal): todas las salidas pegadas a un riel. "
           "Recorte: en PRE solo aparece con entradas muy grandes; el límite "
           "real del sistema es ~0,11 V de pico con las bandas al máximo "
           "(por encima, la cadena satura más adelante y la pantalla "
           "avisa CLIP). Pinza de masa olvidada o puesta en VREF: zumbido de 60 Hz "
           "montado en la traza. C4 lejos de los pines 4/11: oscilación de "
           "alta frecuencia en las salidas.")

T2_COLS = [
    ["- Zócalo de U2 vacío y con la muesca correcta; C5 (100 nF) entre "
     "los pines 4 y 11.",
     "- RV2-RV4 (rotativos B10K) y RV5 cableados 1-2-3 por nombre; el "
     "texto 'deslizables' del maestro es de la revisión anterior.",
     "- C3 (470 uF) junto a J3 y C19 (10 uF) con la polaridad correcta.",
     "- Continuidad de JAB y JBC por nombre de señal, no por posición.",
     "- Ningún corto entre +5V-GND ni VREF-GND."],
    ["- Alimentar +5V/GND por JBUS; VREF desde la T1 ya probada (o un "
     "divisor 10k/10k con seguidor en el banco).",
     "- Zócalo vacío: pin 4 = 5 V, pin 11 = 0 V. Apagar e insertar U2.",
     "- Sin señal: MEDIOS, AGUDOS, EQ_OUT y LINEA cerca de 1,65 V.",
     "- Puente provisional en JBC: unir pin 2 (M_W) con pin 4 (M_INV) "
     "para cerrar el lazo del sumador sin T3. Los medios quedan SIN "
     "invertir: solo sirve para comprobar amplitud. Quitar el puente "
     "antes de integrar con T3."],
    ["- DDS: seno, 200 mVpp, offset 1,65 V, Hi-Z. En JAB-3 (MED_HP) a "
     "1 kHz: CH2 en MEDIOS (U2A) aprox. 1,0x (LP fc 2,3 kHz); a 8 kHz "
     "cae a aprox. 0,08x.",
     "- En JAB-1 (PRE) a 8 kHz (20 us/div): AGUDOS (U2B) = 0,9-1,0x "
     "(HP fc 4,1 kHz); a 1 kHz aprox. 0,06x.",
     "- Con RV2-RV4 al 50 % y señal en una sola banda: EQ_OUT aprox. "
     "1x la salida del filtro, invertida respecto a VREF (sumador "
     "100k/47k; esperado según el modelo).",
     "- ADC_FFT_RAW (JB4-1) a 1 kHz: casi igual a EQ_OUT "
     "(antialiasing fc 4,95 kHz); a 8 kHz ya baja a aprox. 0,35-0,4x.",
     "- RV5 debe variar AMP_IN sin alterar LINEA (J2)."],
]
T2_FAIL = ("Sin puente M_W-M_INV (o sin T3): la rama de medios no llega al "
           "sumador y EQ_OUT pierde la banda central. Medios sin invertir en "
           "el montaje final: hundimientos en los cruces de 409 Hz y 2,3 kHz. "
           "Sin VREF: todo al riel. C3 invertido: calentamiento y zumbido en "
           "el PAM8403.")

T3_COLS = [
    ["- Zócalos de U3 y U4 vacíos y orientados; C6 y C7 (100 nF) entre "
     "los pines 4 y 11 de cada uno.",
     "- Polaridad de D1-D3 (1N4148, banda = cátodo) según el esquema: "
     "el diodo queda dentro del lazo del operacional.",
     "- R17 = R18 = 47k (inversor de ganancia -1); R27-R29 de 220k del "
     "mismo lote; C22-C24 de 100 nF film.",
     "- Continuidad de JBC y JC4 por nombre; sin cortos +5V-GND ni "
     "VREF-GND."],
    ["- Alimentar +5V/GND por JBUS y VREF desde T1.",
     "- Zócalos vacíos: pin 4 = 5 V y pin 11 = 0 V en U3 y en U4. "
     "Apagar e insertar los dos LM324.",
     "- Sin señal: M_INV, ADC_G_RAW, ADC_M_RAW y ADC_A_RAW en reposo "
     "cerca de 1,65 V (esperado según el modelo).",
     "- U4D es un seguidor de VREF: su salida también debe medir "
     "1,65 V."],
    ["- DDS: seno, 200 mVpp, offset 1,65 V, Hi-Z, en JBC-2 (M_W) a "
     "1 kHz: CH2 en M_INV = misma amplitud invertida 180 grados "
     "respecto a VREF (R17 = R18).",
     "- CH2 con acoplo DC en ADC_M_RAW: sube a aprox. VREF + pico = "
     "1,65 + 0,10 = 1,75 V con rizado pequeño (tau = 220k x 100n = "
     "22 ms).",
     "- Repetir en JBC-1 (G_W) a 100 Hz mirando ADC_G_RAW (rizado "
     "mayor por la frecuencia baja) y en JBC-3 (A_W) a 8 kHz mirando "
     "ADC_A_RAW.",
     "- Al quitar la señal, cada ADC_x_RAW cae hacia 1,65 V con tau "
     "aprox. 22 ms.",
     "- No conectar aún los RAW al ESP32: antes validar T4 y los "
     "atenuadores R33-R40."],
]
T3_FAIL = ("Diodo invertido o abierto: el detector no sube con la señal. Sin "
           "VREF: salidas al riel. El detector sigue el pico negativo en vez "
           "del positivo: entradas +/- de U3/U4 intercambiadas. Rizado enorme "
           "o caída instantánea: condensador de retención (100 nF) mal "
           "soldado.")

T4_COLS = [
    ["- El DevKit V1 de 30 pines está PENDIENTE DE COMPRA y el maestro "
     "dibuja el DevKitC de 38: verificar la correspondencia de pines "
     "antes de perforar y soldar T4.",
     "- Zócalos del ESP32 y DIP-20 (U6) orientados; C26 (1000 uF) con "
     "polaridad correcta junto a J5.",
     "- Fusible de 3 A e interruptor general en serie con J6.",
     "- R33-R40 en parejas de 10k (0,1 % recomendado) lo más cerca "
     "posible de los pines ADC.",
     "- Ningún corto entre +5V-GND."],
    ["- Alimentar 5 V por J6 SIN el ESP32: +5V en el pin 5V del "
     "zócalo, en U6 pin 20 y en J5-1; la red +3V3 queda a 0 V (la "
     "genera el regulador del DevKit).",
     "- Aplicar VREF de banco (1,65 V) a la red VREF y una tensión "
     "conocida a cada ADC_x_RAW: el pin ADC debe leer VREF + "
     "(RAW - VREF)/2. Esperado según el modelo: RAW 1,65 -> 1,65 V; "
     "RAW 3,0 -> 2,33 V; RAW 0 -> 0,83 V; RAW 5,0 -> 3,33 V.",
     "- Con DDS (seno 1 Vpp, offset 1,65 V) en un RAW: CH1 = RAW y "
     "CH2 = pin ADC con la mitad de amplitud, centrado en 1,65 V."],
    ["- Con el DevKit ya comprado: insertarlo sin periféricos y "
     "comprobar 3,3 V en su pin 3V3. Alimentar por J6 o por USB, "
     "NUNCA ambos a la vez.",
     "- U6 (74HCT245): DIR pin 1 a +5V y /OE pin 19 a GND; LED_DATA "
     "(3,3 V) entra por A0 (pin 2) y J5-2 entrega niveles de 5 V "
     "(verificar con el osciloscopio).",
     "- SW1: el pin BTN alto en reposo y 0 V al pulsar.",
     "- La pantalla ESP32-3248S035 va FUERA de T4, enlazada por "
     "ESP-NOW: solo requiere +5V y GND. El conector J4 (TFT SPI por "
     "cable) pertenece a la revisión anterior."],
]
T4_FAIL = ("Sin VREF en los divisores: lecturas ADC corridas (RAW = 1,65 V "
           "se leería aprox. 0,83 V con VREF a 0). J6 y USB a la vez: "
           "prohibido, dos fuentes en conflicto. U6 con DIR u /OE mal "
           "cableados: la tira no recibe datos. C26 lejos de J5 o R31 lejos "
           "del primer LED: fallos aleatorios en la tira.")

PENDIENTES = [
    "- ESP32 DevKit V1 30P: NO comprado; el esquema sigue dibujando el "
    "DevKitC de 38 pines (revisar pines antes de perforar T4).",
    "- Potenciómetros A10K (RV1 NIVEL, RV5 VOLUMEN): no comprados; los "
    "P-20K log comprados están sin validar eléctricamente.",
    "- B10K RV2-RV4: declarados comprados (3+1) pero sin albarán verificado "
    "ni medidas de cuerpo, eje y rosca.",
    "- Tira LED comprada: FCOB WS2811 de 12 V; el equipo solo tiene 5 V y "
    "el elevador 5->12 V no está comprado ni en el esquema. Orden de color "
    "BRG frente a NEO_GRB del firmware: probar en la tira real.",
    "- Parlantes: hay que puentear L y R del PAM8403 (el esquema solo "
    "alimenta AMP_IN) y el esquema no está actualizado.",
    "- PAM8403, tarjetas perforadas y fuente de 5 V: sin albarán "
    "verificado; medir antes de perforar.",
    "- Consumo de la pantalla 3248S035 a 5 V y enlace ESP-NOW con ambas "
    "placas encendidas: sin probar.",
    "- Interruptor general de 5 A, perillas e imanes: sin comprar.",
    "- Colocación agujero por agujero de cada tarjeta: no realizada; las "
    "posiciones del modelo 3D son representativas, no guía de soldadura.",
    "- Ninguna tensión ni ganancia de esta guía ha sido medida en placa: "
    "todos los valores son esperados según el modelo ideal.",
]

HARNESS_BY_BOARD = {
    "T1": "Además de la tabla: conectores JST-XH de arneses en esta tarjeta: "
          "JBUS (4 vías) y JAB (4 vías).",
    "T2": "Además de la tabla: conectores JST-XH de arneses: JBUS (4), "
          "JAB (4), JBC (5) y JB4 (2 vías).",
    "T3": "Además de la tabla: conectores JST-XH de arneses: JBUS (4), "
          "JBC (5) y JC4 (4 vías).",
    "T4": "Además de la tabla: conectores JST-XH de arneses: JBUS (4), "
          "JB4 (2) y JC4 (4 vías).",
}


def main():
    master = fitz.open(SRC)
    src = master[0]
    ref_db = load_bom()
    boards = load_boards()
    harness = load_harness()
    doc = fitz.open()

    page_overview(doc)

    # --- T1
    page_schematic(
        doc, "T1 · alimentación analógica, entrada y U1",
        "Probar primero VREF; después preamplificador, graves y pasa-altas "
        "de medios",
        [(fitz.Rect(30, 68, 410, 300), (10, 13, 264, 98),
          "T1-A · alimentación, VREF y preamplificador"),
         (fitz.Rect(30, 330, 570, 525), (10, 98, 205, 153),
          "T1-B · U1C graves y U1D pasa-altas de medios")],
        src,
        note_box=(fitz.Rect(590, 82, 815, 525), "QUÉ IDENTIFICAR EN T1",
                  ["- JBUS: +5V, GND, +3V3 y VREF. JAB: PRE, GRAVES, MED_HP "
                   "y GND.",
                   "- U1 pin 4 = +5V y pin 11 = GND; C4 (100 nF) directo "
                   "entre ambos.",
                   "- R1-C1 filtran +3.3VA solo para VREF; los cuatro LM324 "
                   "usan +5 V.",
                   "- Ojo: el recorte T1-A muestra C3, C5, C6 y C7 porque el "
                   "maestro dibuja junta toda la alimentación; físicamente "
                   "C3 y C5 van en T2, y C6/C7 en T3.",
                   "- RV1 es rotativo (A10K, pendiente de compra), no "
                   "deslizable.",
                   "- Preamplificador: G = 1 + R7/R8 = 3,2.",
                   "- Filtros Sallen-Key (Q aprox. 0,73): GRAVES pasa-bajas "
                   "fc aprox. 232 Hz; MEDIOS pasa-altas fc aprox. 409 Hz."],
                  7.5))
    page_procedure(doc, "T1",
                   "Lista desde lista-por-tarjeta.csv + BOM-precision.csv · "
                   "valores esperados según el modelo",
                   board_rows(boards["T1"], ref_db), HARNESS_BY_BOARD["T1"],
                   T1_COLS, T1_FAIL)

    # --- T2
    page_schematic(
        doc, "T2 · filtros finales, controles, sumador y salida",
        "U2 completo en esta tarjeta; U4C del inversor está físicamente "
        "en T3",
        [(fitz.Rect(30, 68, 810, 240), (202, 98, 409, 153),
          "T2-A · pasa-bajas de medios y pasa-altas de agudos"),
         (fitz.Rect(30, 270, 410, 522), (10, 152, 150, 250),
          "T2-B · potenciómetros y sumador U2C"),
         (fitz.Rect(430, 270, 810, 522), (149, 152, 264, 250),
          "T2-C · salida de audio y antialiasing U2D")],
        src,
        bottom_note=(fitz.Rect(45, 528, 795, 575),
                     "U4C, R17 y R18 se dibujan aquí pero se montan en T3. "
                     "Cortes esperados según el modelo: MEDIOS pasa-bajas "
                     "2,3 kHz; AGUDOS pasa-altas 4,1 kHz; antialiasing "
                     "4,95 kHz (fs = 20 kS/s). RV2-RV5 son rotativos: el "
                     "texto 'deslizables' del maestro es de la revisión "
                     "anterior."))
    page_procedure(doc, "T2",
                   "Lista desde lista-por-tarjeta.csv + BOM-precision.csv · "
                   "valores esperados según el modelo",
                   board_rows(boards["T2"], ref_db), HARNESS_BY_BOARD["T2"],
                   T2_COLS, T2_FAIL)

    # --- T3
    page_schematic(
        doc, "T3 · inversor de medios y detectores",
        "Los tres cursores llegan por JBC; M_INV vuelve a T2 por el mismo "
        "arnés",
        [(fitz.Rect(30, 70, 310, 250), (72, 152, 150, 202),
          "T3-A · U4C, R17 y R18"),
         (fitz.Rect(330, 70, 812, 445), (264, 152, 409, 250),
          "T3-B · detectores de graves, medios y agudos")],
        src,
        note_box=(fitz.Rect(30, 280, 310, 445), "QUÉ IDENTIFICAR EN T3",
                  ["- Diodo dentro del lazo: la retención se carga al pico "
                   "real, sin la caída de 0,6 V.",
                   "- tau = Rd x Ch = 220k x 100n = 22 ms.",
                   "- ADC_x - VREF = pico de cada banda (esperado según el "
                   "modelo).",
                   "- U4D queda libre y se usa como seguidor de VREF.",
                   "- JBC: 1 G_W, 2 M_W, 3 A_W, 4 M_INV, 5 GND.",
                   "- JC4: 1 ADC_G_RAW, 2 ADC_M_RAW, 3 ADC_A_RAW, 4 GND."],
                  7.4),
        bottom_note=(fitz.Rect(45, 465, 795, 540),
                     "Antes de conectar el ESP32: medir ADC_G_RAW, ADC_M_RAW "
                     "y ADC_A_RAW con el osciloscopio. Deben descansar cerca "
                     "de VREF y subir con el pico de cada banda. Primero "
                     "comprobar T4 y los atenuadores R33-R40."))
    page_procedure(doc, "T3",
                   "Lista desde lista-por-tarjeta.csv + BOM-precision.csv · "
                   "valores esperados según el modelo",
                   board_rows(boards["T3"], ref_db), HARNESS_BY_BOARD["T3"],
                   T3_COLS, T3_FAIL)

    # --- T4
    page_schematic(
        doc, "T4 · ESP32, protección ADC y salida NeoPixel",
        "Los atenuadores se montan aquí, lo más cerca posible de los pines "
        "ADC del ESP32",
        [(fitz.Rect(30, 70, 810, 305), (263, 13, 409, 98),
          "T4-A · ESP32, R33-R40, TFT y pulsador (según el maestro)"),
         (fitz.Rect(30, 335, 810, 520), (10, 252, 409, 337),
          "T4-B · fuente, 74HCT245 y salida NeoPixel")],
        src,
        bottom_note=(fitz.Rect(45, 528, 795, 575),
                     "El maestro dibuja un ESP32 DevKitC V4 de 38 pines y la "
                     "pantalla Waveshare por J4: la revisión vigente usa un "
                     "DevKit V1 de 30 pines (pendiente de compra) y la "
                     "pantalla ESP32-3248S035 por ESP-NOW (+5V/GND). "
                     "Verificar los pines usados antes de perforar. "
                     "Atenuadores: ADC = VREF + (RAW - VREF)/2."))
    page_procedure(doc, "T4",
                   "Lista desde lista-por-tarjeta.csv + BOM-precision.csv · "
                   "valores esperados según el modelo",
                   board_rows(boards["T4"], ref_db), HARNESS_BY_BOARD["T4"],
                   T4_COLS, T4_FAIL)

    page_integration(doc, harness, PENDIENTES)

    assert len(doc) == TOTAL_PAGES, "Se esperaban %d páginas" % TOTAL_PAGES
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({
        "title": "E.5 · guía de montaje y pruebas por tarjeta",
        "author": "Electrónica II · Universidad de la Costa",
        "subject": "Esquema, componentes y prueba en banco de T1-T4",
    })
    doc.save(OUT, garbage=4, deflate=True)

    # Verificación: reabrir, contar páginas y buscar glifos perdidos.
    check = fitz.open(OUT)
    assert len(check) == TOTAL_PAGES
    for i in range(len(check)):
        txt = check[i].get_text()
        own = txt.replace("E.5 · tarjetas perforadas", "")
        if "?" in own:
            raise SystemExit("Glifo perdido ('?') en la página %d" % (i + 1))
        if "Mecanico;" in txt:
            raise SystemExit("Fila de zócalo filtrada en la página %d" % (i + 1))
    print(OUT)
    for t in ("T1", "T2", "T3", "T4"):
        print("%s: %d referencias" % (t, len(boards[t])))


if __name__ == "__main__":
    main()

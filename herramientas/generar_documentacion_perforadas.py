#!/usr/bin/env python3
"""Genera el esquema modular E.5 a partir del esquema lógico maestro vectorial."""
from pathlib import Path

import pymupdf as fitz


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "hardware" / "E5-perforadas" / "proyecto" / "ecualizador-perforadas-maestro.pdf"
OUT = ROOT / "hardware" / "E5-perforadas" / "esquema-modular-perforadas.pdf"

A4L = (842, 595)
M = 30
BLUE = (0.05, 0.18, 0.55)
GREEN = (0.05, 0.45, 0.25)
GRAY = (0.35, 0.35, 0.35)

# Caracteres fuera de Latin-1 que Helvetica imprimiría como "?".
_SUBS = {"≈": "aprox. ", "–": "-", "—": "-", "−": "-", "×": "x", "…": "..."}


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
    p.insert_text((M, 27), sanitize(title), fontsize=17, fontname="hebo", color=BLUE)
    if subtitle:
        p.insert_text((M, 44), sanitize(subtitle), fontsize=8.5, color=GRAY)
    p.draw_line((M, 51), (A4L[0] - M, 51), color=BLUE, width=0.8)
    p.insert_text((A4L[0] - 150, A4L[1] - 15), "E.5 · tarjetas perforadas", fontsize=7, color=GRAY)
    return p


def clip(p, src, target, coords, caption):
    p.insert_text((target.x0, target.y0 - 4), sanitize(caption), fontsize=8.5, fontname="hebo", color=GREEN)
    body = fitz.Rect(target.x0, target.y0 + 2, target.x1, target.y1)
    p.show_pdf_page(body, src.parent, 0, clip=mmrect(src, *coords), keep_proportion=True)
    p.draw_rect(body, color=(0.75, 0.75, 0.75), width=0.4)


def text_box(p, rect, title, lines, size=8.5):
    p.draw_rect(rect, color=(0.65, 0.65, 0.65), fill=(0.98, 0.98, 0.98), width=0.5)
    p.insert_text((rect.x0 + 8, rect.y0 + 15), sanitize(title), fontsize=10, fontname="hebo", color=BLUE)
    p.insert_textbox(fitz.Rect(rect.x0 + 8, rect.y0 + 29, rect.x1 - 8, rect.y1 - 7),
                     sanitize("\n\n".join(lines)), fontsize=size, lineheight=1.15,
                     color=(0.1, 0.1, 0.1))


def main():
    master = fitz.open(SRC)
    src = master[0]
    doc = fitz.open()

    p = page(doc, "Arquitectura modular para montaje manual",
             "Mismo circuito LM324; cuatro placas comprobables de forma independiente")
    boxes = [
        (fitz.Rect(45, 95, 210, 215), "T1 · ENTRADA + U1", ["VREF 1,65 V", "PRE", "GRAVES", "MED_HP"]),
        (fitz.Rect(245, 95, 410, 215), "T2 · FILTROS + U2", ["MEDIOS / AGUDOS", "SUMADOR", "SALIDA / FFT"]),
        (fitz.Rect(445, 95, 610, 215), "T3 · U3 + U4", ["INVERSOR MEDIOS", "3 DETECTORES", "ADC_*_RAW"]),
        (fitz.Rect(645, 95, 810, 215), "T4 · CONTROL", ["ESP32 30P", "R33–R40", "J7 pantalla / LED"]),
    ]
    for rect, title, lines in boxes:
        text_box(p, rect, title, lines, 8)
    for x1, x2, label in ((210, 245, "JAB"), (410, 445, "JBC"), (610, 645, "JC4")):
        p.draw_line((x1, 155), (x2, 155), color=GREEN, width=1.3)
        p.insert_text(((x1 + x2) / 2 - 9, 146), label, fontsize=7, color=GREEN)
    p.draw_line((328, 215), (328, 265), color=GREEN, width=1.2)
    p.draw_line((328, 265), (728, 265), color=GREEN, width=1.2)
    p.draw_line((728, 265), (728, 215), color=GREEN, width=1.2)
    p.insert_text((480, 256), "JB4 · ADC_FFT_RAW", fontsize=7, color=GREEN)
    text_box(p, fitz.Rect(45, 310, 810, 505), "BUS DE ALIMENTACIÓN EN ESTRELLA · JBUS",
             ["1  +5V      desde la fuente externa / T4",
              "2  GND      retorno común de potencia y señal",
              "3  +3V3     desde ESP32 hacia T1; no alimentar cargas",
              "4  VREF     1,65 V generado en T1 y distribuido a T2/T3/T4",
              "VREF no reemplaza GND. Llevar +5V y GND con cable más grueso que las señales."], 10)

    p = page(doc, "T1 · alimentación analógica, entrada y U1",
             "Probar primero VREF; después preamplificador, graves y pasa-altas de medios")
    clip(p, src, fitz.Rect(30, 68, 410, 300), (10, 13, 264, 98), "T1-A · alimentación, VREF y preamplificador")
    clip(p, src, fitz.Rect(30, 330, 570, 525), (10, 98, 205, 153), "T1-B · U1C graves y U1D pasa-altas de medios")
    text_box(p, fitz.Rect(590, 82, 815, 525), "CONEXIONES Y PRUEBAS",
             ["JBUS: +5V, GND, +3V3 y VREF.", "JAB: PRE, GRAVES, MED_HP y GND.",
              "U1 pin 4 = +5V; pin 11 = GND.", "C4: 100 nF directamente entre pines 4 y 11.",
              "Sin señal: VREF, PRE, GRAVES y MED_HP deben quedar cerca de 1,65 V.",
              "Inyectar primero una senoide pequeña: 50 mVpp a 1 kHz."], 8.2)

    p = page(doc, "T2 · filtros finales, controles, sumador y salida",
             "U2 permanece completo en esta tarjeta; U4C del inversor está físicamente en T3")
    clip(p, src, fitz.Rect(30, 68, 810, 240), (202, 98, 409, 153), "T2-A · pasa-bajas de medios y pasa-altas de agudos")
    clip(p, src, fitz.Rect(30, 270, 410, 525), (10, 152, 150, 250), "T2-B · potenciómetros y sumador U2C")
    clip(p, src, fitz.Rect(430, 270, 810, 525), (149, 152, 264, 250), "T2-C · salida de audio y antialiasing U2D")

    p = page(doc, "T3 · inversor de medios y detectores",
             "Los tres cursores llegan por JBC; M_INV vuelve a T2 por el mismo arnés")
    clip(p, src, fitz.Rect(30, 70, 310, 250), (72, 152, 150, 202), "T3-A · U4C, R17 y R18")
    clip(p, src, fitz.Rect(330, 70, 812, 445), (264, 152, 409, 250), "T3-B · detectores de graves, medios y agudos")
    text_box(p, fitz.Rect(30, 465, 812, 545), "PRUEBA ANTES DE CONECTAR EL ESP32",
             ["Medir ADC_G_RAW, ADC_M_RAW y ADC_A_RAW con osciloscopio. Deben descansar cerca de VREF y subir con el pico de cada banda. No conectarlos todavía al ESP32: primero comprobar T4 y los atenuadores R33–R40."], 8.5)

    p = page(doc, "T4 · ESP32 DevKit V1 30P, protección ADC, enlace de pantalla y NeoPixel",
             "Los atenuadores se montan aquí, lo más cerca posible de los pines ADC; la pantalla recibe los datos por ESP-NOW")
    clip(p, src, fitz.Rect(30, 70, 810, 305), (263, 13, 409, 98), "T4-A · ESP32 DevKit V1, R33–R40, J7 (pantalla) y pulsador")
    clip(p, src, fitz.Rect(30, 335, 810, 520), (10, 252, 409, 337), "T4-B · fuente, 74HCT245 y salida NeoPixel")
    p.insert_textbox(fitz.Rect(45, 530, 795, 575),
                     "Antes de insertar el ESP32: comprobar +5V, +3V3 y GND; aplicar una tensión conocida a cada ADC_*_RAW y verificar ADC = VREF + (RAW - VREF)/2.",
                     fontsize=8.5, color=(0.15, 0.15, 0.15), align=1)

    p = page(doc, "Pinout de arneses y puesta en marcha",
             "Cablear siempre por nombre de señal, no por posición visual")
    text_box(p, fitz.Rect(30, 70, 400, 275), "ARNÉSES DE SEÑAL",
             ["JAB  1 PRE · 2 GRAVES · 3 MED_HP · 4 GND",
              "JBC  1 G_W · 2 M_W · 3 A_W · 4 M_INV · 5 GND",
              "JB4  1 ADC_FFT_RAW · 2 GND",
              "JC4  1 ADC_G_RAW · 2 ADC_M_RAW · 3 ADC_A_RAW · 4 GND"], 9)
    text_box(p, fitz.Rect(430, 70, 812, 275), "ORDEN DE ENCENDIDO",
             ["1. T4 sin ESP32: ausencia de cortos y tensiones.",
              "2. T1: VREF = 1,65 V y reposo de sus salidas.",
              "3. T1 + T2: respuesta de las tres bandas y EQ_OUT.",
              "4. Añadir T3 y medir los cuatro ADC_*_RAW.",
              "5. Validar R33–R40; solo entonces insertar ESP32.",
              "6. Al final: PAM8403, LED y pantalla (ESP-NOW; J7 solo 5V/GND)."], 8.5)
    text_box(p, fitz.Rect(30, 310, 812, 525), "PUNTOS DE CONTROL",
             ["Alimentación: LM324 pin 4 ≈ 5 V; pin 11 = 0 V.",
              "Referencia: VDIV ≈ 1,65 V y VREF ≈ 1,65 V.",
              "Reposo analógico: PRE, GRAVES, MED_HP, MEDIOS, AGUDOS y EQ_OUT ≈ VREF.",
              "ADC protegido: para RAW = 1,65 V, ADC ≈ 1,65 V; para RAW = 3,0 V, ADC ≈ 2,33 V.",
              "Nunca alimentar el PAM8403 o la tira LED desde +3V3; nunca usar VREF como retorno."], 9)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({"title": "E.5 · esquema modular para tarjetas perforadas",
                      "author": "Electrónica II · Universidad de la Costa",
                      "subject": "División comprobable del ecualizador LM324"})
    doc.save(OUT, garbage=4, deflate=True)
    print(OUT)


if __name__ == "__main__":
    main()

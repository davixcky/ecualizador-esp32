#!/usr/bin/env python3
"""Dibuja la distribución sugerida del montaje en protoboard (../img/protoboard-zonas.png).

Dos protoboards de 830 puntos: la A lleva toda la parte analógica (U1–U4 y sus pasivos), en el
orden de la señal, y la B el ESP32-DevKitC (que ocupa las dos mitades: se usan dos medias
protoboards unidas, dejando una fila libre de cada lado) con el conector de la pantalla.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

AQUI = os.path.dirname(os.path.abspath(__file__))
P = 2.54
COLS = 63


def protoboard(ax, x0, y0, titulo):
    w, h = COLS * P + 6, 22 * P
    ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=2", fc="#f4f4f0", ec="#9a9a92"))
    for fila in range(10):
        y = y0 + 4 * P + fila * P + (2 * P if fila >= 5 else 0)
        for c in range(COLS):
            ax.add_patch(Rectangle((x0 + 3 + c * P - 0.4, y - 0.4), 0.8, 0.8, fc="#8f8f88", ec="none"))
    for k, (yy, col) in enumerate(((y0 + 1.2 * P, "#2e6fd8"), (y0 + 2.2 * P, "#d83a2e"),
                                   (y0 + 19.8 * P, "#2e6fd8"), (y0 + 20.8 * P, "#d83a2e"))):
        ax.plot([x0 + 3, x0 + w - 3], [yy, yy], color=col, lw=1.2)
    ax.text(x0, y0 + h + 2.5, titulo, fontsize=11, weight="bold", color="#2b2f3a")
    return x0 + 3, y0 + 4 * P


def dip(ax, x, y, nombre, sub):
    """DIP-14 que cruza el canal central: x = columna del pin 1 (izquierda)."""
    ax.add_patch(FancyBboxPatch((x - 1.2, y + 3.4 * P), 7 * P, 3.2 * P, boxstyle="round,pad=0,rounding_size=0.6",
                                fc="#1d1f24", ec="#000"))
    ax.add_patch(plt.Circle((x + 0.3, y + 4.0 * P), 0.6, color="#666"))
    ax.text(x + 3 * P, y + 5.2 * P, nombre, color="white", ha="center", va="center", fontsize=8, weight="bold")
    ax.text(x + 3 * P, y + 4.3 * P, sub, color="#c9cbd2", ha="center", va="center", fontsize=6)


def zona(ax, x, y, w, h, color, texto, piezas):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.5", fc=color, ec="none",
                                alpha=0.28))
    ax.text(x + w / 2, y - 3.3, texto, ha="center", va="top", fontsize=7.5, weight="bold", color="#2b2f3a")
    ax.text(x + w / 2, y - 6.6, piezas, ha="center", va="top", fontsize=6.3, color="#4c5263")


def main():
    fig, ax = plt.subplots(figsize=(15, 9.6))
    ax.set_aspect("equal")
    ax.axis("off")

    # ---------------- protoboard A: analógica
    xa, ya = protoboard(ax, 0, 70, "Protoboard A — etapa analógica (alimentación 3V3A en los rieles; VREF en una fila libre)")
    filas = [ya - 1.2, 11 * P + 2.4]
    zonas = [
        (0, 12, "#5e81ac", "Alimentación y VREF", "R1, C1, C2, R2, R3, C8, U1A"),
        (12, 14, "#4c9be8", "Entrada y preamplificador", "R4–R8, C9, C10, U1B (G = 3,2)"),
        (26, 18, "#e4572e", "Graves y medios (pasa altas)", "U1C: R9, R10, C11, C12 · U1D: C13, C14, R11, R12"),
        (44, 19, "#29a35a", "Medios (pasa bajas), agudos y suma", "U2A–U2D: R13–R16, C15–C18, R19–R26, C19–C21"),
    ]
    for c0, n, col, t, pz in zonas:
        zona(ax, xa + c0 * P - 1.2, ya - 1.5, n * P, 12 * P, col, t, pz)
    dip(ax, xa + 15 * P, ya, "U1", "MCP6004 · A B C D")
    dip(ax, xa + 48 * P, ya, "U2", "MCP6004 · A B C D")

    # ---------------- protoboard A2: detectores (media protoboard)
    xb, yb = protoboard(ax, 0, 0, "Protoboard B — detectores de pico, inversor de medios y ESP32")
    zona(ax, xb - 1.2, yb - 1.5, 30 * P, 12 * P, "#8e44ad", "Detectores de pico e inversor",
         "U3A–U3D, U4A–U4C: D1–D3, C22–C24, R27–R29, R17, R18")
    dip(ax, xb + 5 * P, yb, "U3", "graves · medios")
    dip(ax, xb + 18 * P, yb, "U4", "agudos · inversor")
    # ESP32 DevKit en la mitad derecha (19 pines por lado, 25,4 mm entre filas)
    ex = xb + 33 * P
    zona(ax, ex - 1.2, yb - 1.5, 29 * P, 12 * P, "#d08c2e", "ESP32-DevKitC", "GPIO32–36 analógicas · TFT por SPI · SW1")
    ax.add_patch(FancyBboxPatch((ex, yb - 1.2), 19 * P, 12.6 * P, boxstyle="round,pad=0,rounding_size=1", fc="#1f2a44",
                                ec="#000"))
    ax.add_patch(Rectangle((ex + 2, yb + 2.5), 14, 18, fc="#e6e6e6", ec="#999"))
    ax.add_patch(Rectangle((ex + 19 * P - 4, yb + 9), 5, 8, fc="#cfcfcf", ec="#888"))
    ax.text(ex + 30, yb + 13, "ESP32\nDevKitC", color="white", ha="center", va="center", fontsize=9, weight="bold")

    # ---------------- fuera de las protoboards
    ox = COLS * P + 16
    ax.text(ox, 128, "Fuera de la protoboard (con cables Dupont)", fontsize=10, weight="bold", color="#2b2f3a")
    lineas = ["• J1, J2: jacks de 3,5 mm (entrada y salida)",
              "• RV1 nivel y RV5 volumen (10 kΩ log)",
              "• RV2–RV4: deslizables de 10 kΩ lin (graves, medios, agudos)",
              "• Pantalla TFT ILI9341: 9 cables (VCC, GND, CS, RST, DC,",
              "   SDI, SCK, LED, SDO) → GPIO5, 22, 21, 23, 18, 19",
              "• Módulo PAM8403 + parlante (5 V del pin 5V del DevKitC)",
              "• SW1 a GPIO27 y GND",
              "",
              "Rieles: A = +3,3 VA (después de R1) y GND;",
              "B = +3V3 del DevKitC y GND. Unir los GND de A y B",
              "en un solo punto, junto a C1.",
              "",
              "Orden de montaje y prueba:",
              "1. Alimentación y VREF → medir 1,65 V",
              "2. Preamplificador → G = 3,2 con 100 mV a 1 kHz",
              "3. Un filtro a la vez → barrido con el generador",
              "4. Deslizables, inversor y sumador → respuesta plana",
              "5. Detectores → ADC_x − VREF = pico de la banda",
              "6. ESP32 y pantalla → firmware y prueba de 1 kHz"]
    for i, l in enumerate(lineas):
        ax.text(ox, 120 - i * 5.0, l, fontsize=8.6, color="#2b2f3a", va="top")

    ax.set_xlim(-4, ox + 95)
    ax.set_ylim(-14, 140)
    fig.tight_layout()
    fig.savefig(os.path.join(AQUI, "..", "img", "protoboard-zonas.png"), dpi=140)
    print("Escrita ../img/protoboard-zonas.png")


if __name__ == "__main__":
    main()

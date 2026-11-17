#!/usr/bin/env python3
"""Genera el esquema maestro lógico de la variante modular E.5."""
from pathlib import Path

import generar_esquematico as g


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "E5-perforadas" / "proyecto" / "ecualizador-perforadas.kicad_sch"

g.PROYECTO = "ecualizador-perforadas"
g.SALIDA = str(OUT)

# U6 de la variante perforada usa una pieza HCT disponible localmente. El
# símbolo 74HC245 de KiCad tiene el mismo pinout; el valor y la familia reales
# siguen siendo 74HCT245. DIR=1 selecciona A→B y /OE=0 habilita las salidas.
u6 = next(p for p in g.cto.PIEZAS if p["ref"] == "U6")
u6.update(
    tipo="BUFFER245",
    valor="74HCT245",
    pines={
        "1": "+5V", "2": "LED_DATA",
        "3": "GND", "4": "GND", "5": "GND", "6": "GND",
        "7": "GND", "8": "GND", "9": "GND", "10": "GND",
        "11": None, "12": None, "13": None, "14": None,
        "15": None, "16": None, "17": None, "18": "LED_5V",
        "19": "GND", "20": "+5V",
    },
    huella="Package_DIP:DIP-20_W7.62mm_Socket",
    funcion="Adaptador lógico local 3,3 a 5 V; DIR=1, /OE=0, canal A0→B0",
)
next(p for p in g.cto.PIEZAS if p["ref"] == "C25")["funcion"] = "Desacople del 74HCT245"

e = g.construir()
e.guardar(
    str(OUT),
    [
        "Ecualizador E.5 — esquema maestro para cuatro tarjetas perforadas",
        "2026-11-16",
        "E.5-perforadas",
        "Electrónica II — Universidad de la Costa",
        "Misma topología LM324 validada; división física documentada en esquema-modular-perforadas.pdf",
        "Montar y probar T1, T2, T3 y T4 por separado antes de unir los arneses",
    ],
)
print(OUT)

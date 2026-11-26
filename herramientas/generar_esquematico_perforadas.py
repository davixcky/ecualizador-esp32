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

# --- U5: ESP32 DevKit V1 de 30 pines (decisión del 2026-11-24; unidad en mano según
# 3d/medidas-componentes.json). Columnas numeradas de arriba hacia abajo con el USB abajo,
# igual que el símbolo histórico de 38 pines. Las redes siguen el mapa e5cyd de
# firmware/include/config.h y la auditoría firmware/PINES-DEVKIT-V1.md.
g.ESP_SIMBOLO = "ESP32-DevKit-V1-30"
g.ESP_DESCRIPCION = "Tarjeta ESP32 DevKit V1 (ESP32-WROOM-32), 30 pines, USB micro-B"
g.cto.IZQ[:] = ["EN", "VP/IO36", "VN/IO39", "IO34", "IO35", "IO32", "IO33", "IO25",
                "IO26", "IO27", "IO14", "IO12", "IO13", "GND", "VIN"]
g.cto.DER[:] = ["3V3", "GND", "IO15", "IO2", "IO4", "RX2/IO16", "TX2/IO17", "IO5",
                "IO18", "IO19", "IO21", "RXD0/IO3", "TXD0/IO1", "IO22", "IO23"]
REDES_E5 = {"3V3": "+3V3", "VIN": "+5V", "IO35": "VREF", "VN/IO39": "ADC_G",
            "VP/IO36": "ADC_M", "IO32": "ADC_A", "IO34": "ADC_FFT", "IO13": "BTN",
            "IO5": "LED_DATA", "TX2/IO17": "CYD_TX", "RX2/IO16": "CYD_RX"}
u5 = next(p for p in g.cto.PIEZAS if p["ref"] == "U5")
u5.update(
    valor="ESP32 DevKit V1 (30P)",
    pines={str(k + 1): ("GND" if n == "GND" else REDES_E5.get(n))
           for k, n in enumerate(g.cto.IZQ + g.cto.DER)},
    huella="Ecualizador:ESP32-DevKit-V1-30P_Zocalo",
    funcion="Microcontrolador: ADC1, FFT, NeoPixel y ESP-NOW hacia la pantalla",
)

# --- Pantalla: la ESP32-3248S035 va en la tapa y recibe los DATOS por ESP-NOW
# (firmware/include/enlace_cyd.h). Desaparecen la TFT SPI J4 y su R30 (apagaba la
# retroiluminación TFT_BL durante el arranque); queda J7 con +5V/GND y el UART2
# de respaldo (PROPUESTO: aún sin probar en el montaje real).
g.cto.PIEZAS[:] = [p for p in g.cto.PIEZAS if p["ref"] not in ("J4", "R30")]
g.cto.parte("J7", "CONN4", "Pantalla 5V + UART respaldo (PROPUESTO)",
            {"1": "+5V", "2": "GND", "3": "CYD_TX", "4": "CYD_RX"}, g.cto.H_AMP,
            "Alimentación de la pantalla ESP32-3248S035; datos por ESP-NOW; UART2 solo de respaldo")

e = g.construir()
e.guardar(
    str(OUT),
    [
        "Ecualizador E.5 — esquema maestro para cuatro tarjetas perforadas",
        "2026-11-26",
        "E.5-perforadas",
        "Electrónica II — Universidad de la Costa",
        "Misma topología LM324 validada; división física documentada en esquema-modular-perforadas.pdf",
        "U5 = DevKit V1 30P; pantalla ESP32-3248S035 por ESP-NOW; J7 = 5V/GND + UART2 respaldo (PROPUESTO)",
    ],
)
print(OUT)

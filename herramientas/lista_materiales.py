#!/usr/bin/env python3
"""Imprime la lista de materiales en Markdown, agrupada por valor y tipo, desde circuito.py."""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuito as cto  # noqa: E402

DESC = {
    "R": "Resistencia de película metálica 1/4 W",
    "C": "Condensador",
    "CP": "Condensador electrolítico",
    "POT": "Potenciómetro",
    "D": "Diodo de señal",
    "JACK": "Jack hembra estéreo 3,5 mm para PCB",
    "CONN4": "Espadín macho 1 × 4",
    "TFT": "Zócalo hembra 1 × 14 (pantalla)",
    "SW": "Pulsador táctil 6 × 6 mm (eje largo)",
    "OPAMP": "Amplificador operacional cuádruple riel a riel MCP6004-I/P (DIP-14) + zócalo",
    "ESP32": "Tarjeta ESP32-DevKitC V4 (38 pines) + 2 zócalos hembra 1 × 19",
}


def clave(r):
    m = re.match(r"([A-Z]+)(\d+)", r)
    return m.group(1), int(m.group(2))


def rango(refs):
    refs = sorted(refs, key=clave)
    out, ini, prev = [], refs[0], refs[0]
    for r in refs[1:] + [None]:
        if r and clave(r)[0] == clave(prev)[0] and clave(r)[1] == clave(prev)[1] + 1:
            prev = r
            continue
        out.append(ini if ini == prev else (f"{ini}, {prev}" if clave(prev)[1] == clave(ini)[1] + 1 else f"{ini}–{prev}"))
        ini = prev = r
    return ", ".join(out)


grupos = {}
for p in cto.PIEZAS:
    k = (p["tipo"], p["valor"], p["huella"].split(":")[1])
    grupos.setdefault(k, []).append(p["ref"])

orden = ["OPAMP", "ESP32", "R", "C", "CP", "POT", "D", "JACK", "CONN4", "TFT", "SW"]
filas = sorted(grupos.items(), key=lambda kv: (orden.index(kv[0][0]), kv[0][1]))
print("| # | Referencias | Descripción | Valor | Cant. |")
print("|---:|---|---|---|---:|")
n = 0
for (tipo, valor, huella), refs in filas:
    n += 1
    d = DESC[tipo]
    if tipo == "C":
        d = "Condensador de película (poliéster)" if "film" in valor else "Condensador cerámico"
    if tipo == "POT":
        d = "Potenciómetro deslizable 30 mm (Bourns PTA3043)" if "Slide" in huella else "Potenciómetro rotativo 9 mm (Alps RK09K), eje 20 mm"
    v = valor.replace(" film", "").replace("u", " µ").replace("n", " n") if tipo in ("C", "CP") else valor
    if tipo in ("JACK", "CONN4", "TFT", "SW", "ESP32", "OPAMP"):
        v = "—"
    print(f"| {n} | {rango(refs)} | {d} | {v} | {len(refs)} |")
for ref, d, c, uso in cto.FUERA:
    n += 1
    print(f"| {n} | — | {d} | — | {c} |")

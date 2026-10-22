#!/usr/bin/env python3
"""Compara la netlist que exporta KiCad del esquemático con las redes de circuito.py.

Cada red de circuito.py debe aparecer en KiCad con exactamente los mismos pines, y al revés.
Así se comprueba que el dibujo del esquemático no tiene cables de más ni de menos.

    python3 verificar_netlist.py
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuito as cto  # noqa: E402
from sexpr import find, find1, parse  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(AQUI, "..", "hardware", "ecualizador.kicad_sch")


def _arbol(ruta_sch=SCH):
    with tempfile.TemporaryDirectory() as tmp:
        salida = os.path.join(tmp, "n.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", salida, ruta_sch],
                       check=True, capture_output=True)
        return parse(open(salida, encoding="utf-8").read())[0]


def netlist_kicad(ruta_sch=SCH):
    """({(ref, pin): red}, {ref: uuid del símbolo}) según KiCad, con los nombres de red de KiCad."""
    arbol = _arbol(ruta_sch)
    pin_red = {}
    for n in find(find1(arbol, "nets"), "net"):
        for x in find(n, "node"):
            pin_red[(find1(x, "ref")[1], find1(x, "pin")[1])] = find1(n, "name")[1]
    sellos = {find1(c, "ref")[1]: find1(c, "tstamps")[1] for c in find(find1(arbol, "components"), "comp")}
    return pin_red, sellos


def redes_kicad(ruta_sch=SCH):
    arbol = _arbol(ruta_sch)
    redes = {}
    for n in find(find1(arbol, "nets"), "net"):
        nombre = find1(n, "name")[1]
        nodos = frozenset((find1(x, "ref")[1], find1(x, "pin")[1]) for x in find(n, "node"))
        if nombre.startswith("unconnected-"):
            continue
        redes[nodos] = nombre
    return redes


def main():
    kicad = redes_kicad()
    propias = {frozenset(v): k for k, v in cto.redes().items()}
    faltan = [(n, sorted(v)) for v, n in propias.items() if v not in kicad]
    sobran = [(n, sorted(v)) for v, n in kicad.items() if v not in propias]
    for nombre, nodos in faltan:
        print("En circuito.py pero no en KiCad:", nombre, nodos)
    for nombre, nodos in sobran:
        print("En KiCad pero no en circuito.py:", nombre, nodos)
    nombres = sum(1 for v, n in propias.items() if kicad.get(v, "").lstrip("/") == n)
    print(f"{len(propias)} redes en circuito.py, {len(kicad)} en KiCad; {len(propias) - len(faltan)} coinciden "
          f"pin a pin ({nombres} también por nombre).")
    return 1 if faltan or sobran else 0


if __name__ == "__main__":
    sys.exit(main())

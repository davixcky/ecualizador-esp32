#!/usr/bin/env python3
"""Genera la PCB de dos capas del ecualizador en ../hardware/ecualizador.kicad_pcb.

La placa es también el panel superior del gabinete: la pantalla TFT, los tres deslizables,
las dos perillas y el pulsador quedan hacia el usuario, y los jacks y el USB del ESP32 salen
por los bordes. Las piezas, huellas y redes salen de circuito.py (las mismas del esquemático).

Pasos:
  1. Ubica cada huella (posiciones fijas para el panel, empaquetado por bloques para el resto).
  2. Exporta la placa a Specctra DSN, la rutea con Freerouting y vuelve a importar el ruteo.
  3. Agrega los planos de GND en las dos caras y verifica con el DRC de KiCad.

    python3 generar_pcb.py              (ubica y rutea; necesita java y freerouting.jar)
    python3 generar_pcb.py --sin-rutear (solo ubica)
"""
import json
import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuito as cto  # noqa: E402
from verificar_netlist import netlist_kicad  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(AQUI, "..", "hardware")
SALIDA = os.path.join(HW, "ecualizador.kicad_pcb")
FREEROUTING = os.environ.get("FREEROUTING", "/opt/freerouting/fr.jar")
LIBS = "/usr/share/kicad/footprints"

ANCHO, ALTO = 200.0, 120.0
MM = pcbnew.FromMM

# Waveshare horizontal; soporte en la tapa y cable, sin taladros supuestos en PCB.
TFT_X, TFT_Y = 25.4, 17.35
TFT_W, TFT_H = 51.2, 27.3
TFT_AGUJEROS = []

# ---------------------------------------------------------------- posiciones fijas (x, y, rotación)
FIJAS = {
    "J4": (10.6, 14.5, 0),
    "U6": (8, 57, 90),
    "J5": (186, 78, 90),
    "J6": (185, 58, 0),
    "RV2": (106.0, 9.0, -90),
    "RV3": (122.0, 9.0, -90),
    "RV4": (138.0, 9.0, -90),
    "RV1": (158.0, 8.0, 0),
    "RV5": (158.0, 30.0, 0),
    "SW1": (157.0, 50.0, 0),
    "J1": (191.0, 14.0, 90),
    "J2": (191.0, 36.0, 90),
    "U5": (148.0, 111.0, 90),
    "J3": (189.0, 66.0, 90),
}

# ---------------------------------------------------------------- bloques empaquetados
# (región x0, y0, x1, y1, piezas en orden de la señal). El primer elemento es el CI.
BLOQUES = [
    ((40, 44, 98, 61), [ "C25", "R31", "R32", "C26"]),
    ((16, 8, 96, 42), ["U3", "C6", "D1", "C22", "R27", "D2", "C23", "R28",
                        "U4", "C7", "D3", "C24", "R29", "R17", "R18"]),
    ((4, 62, 72, 117), ["U1", "C4", "R2", "R3", "C8", "C9", "R6", "R7", "R8", "C10", "R9", "R10", "C11", "C12",
                        "C13", "C14", "R11", "R12"]),
    ((74, 62, 140, 117), ["U2", "C5", "R13", "R14", "C15", "C16", "C17", "C18", "R15", "R16", "R19", "R20", "R21",
                          "R22", "R25", "R26", "C20", "C21", "C19", "R23", "R24"]),
    ((146, 62, 182, 80), ["C3", "R1", "C1", "C2", "R30"]),
    ((166, 44, 182, 58), ["R4", "R5"]),
]


def cargar_huella(huella):
    lib, nombre = huella.split(":")
    ruta = os.path.join(HW, "Ecualizador.pretty") if lib == "Ecualizador" else os.path.join(LIBS, lib + ".pretty")
    fp = pcbnew.FootprintLoad(ruta, nombre)
    if fp is None:
        raise SystemExit(f"No se encontró la huella {huella}")
    fp.SetFPID(pcbnew.LIB_ID(lib, nombre))
    return fp


def caja(fp):
    """Rectángulo de cortesía (courtyard) de la huella en su posición actual, en mm."""
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()), pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


def mover(fp, x, y, rot=0):
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))


def empaquetar(huellas, region):
    """Coloca las huellas en filas dentro de la región: el CI primero y luego los pasivos
    de pie (girados 90°), de izquierda a derecha y de arriba abajo."""
    x0, y0, x1, y1 = region
    x, y, alto_fila = x0, y0, 0.0
    for fp in huellas:
        ref = fp.GetReference()
        rot = 0 if ref.startswith(("U", "J", "SW")) or str(fp.GetFPID().GetLibItemName()).startswith("CP_") else 90
        mover(fp, 0, 0, rot)
        bx0, by0, bx1, by1 = caja(fp)
        w, h = bx1 - bx0, by1 - by0
        if x + w > x1 + 0.01:
            x, y = x0, y + alto_fila + 2.5
            alto_fila = 0.0
        if y + h > y1 + 0.01:
            raise SystemExit(f"El bloque {region} no alcanza para {ref}")
        mover(fp, x - bx0, y - by0, rot)
        x += w + (2.4 if str(fp.GetFPID().GetLibItemName()).startswith("C_Rect") else 1.4)
        alto_fila = max(alto_fila, h)


def linea(board, capa, puntos, ancho=0.15):
    for a, b in zip(puntos, puntos[1:]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        s.SetLayer(capa)
        s.SetWidth(MM(ancho))
        board.Add(s)


def texto(board, t, x, y, tam=1.5, capa=pcbnew.F_SilkS, rot=0):
    tx = pcbnew.PCB_TEXT(board)
    tx.SetText(t)
    tx.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    tx.SetLayer(capa)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(tam), MM(tam)))
    tx.SetTextThickness(MM(tam * 0.15))
    tx.SetTextAngleDegrees(rot)
    board.Add(tx)


def agujero(board, x, y, diam=3.2):
    fp = cargar_huella("MountingHole:MountingHole_3.2mm_M3")
    fp.SetReference(f"H{len([f for f in board.GetFootprints() if f.GetReference().startswith('H')]) + 1}")
    fp.Reference().SetVisible(False)
    fp.SetBoardOnly(True)
    fp.SetExcludedFromBOM(True)
    mover(fp, x, y)
    board.Add(fp)


def zona_gnd(board, capa, red):
    z = pcbnew.ZONE(board)
    z.SetLayer(capa)
    z.SetNet(red)
    z.SetLocalClearance(MM(0.4))
    z.SetMinThickness(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.4))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0.5, 0.5), (ANCHO - 0.5, 0.5), (ANCHO - 0.5, ALTO - 0.5), (0.5, ALTO - 0.5)):
        o.Append(MM(x), MM(y))
    board.Add(z)
    return z


def construir():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = MM(0.25)
    ds.m_MinClearance = MM(0.2)
    ds.m_ViasMinSize = MM(0.6)

    # clases de red: alimentación más ancha
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetTrackWidth(MM(0.3))
    nc.SetClearance(MM(0.25))
    nc.SetViaDiameter(MM(0.8))
    nc.SetViaDrill(MM(0.4))

    # Redes y sellos de tiempo tomados de la netlist que KiCad exporta del esquemático (ya
    # verificada contra circuito.py), para que la PCB quede sincronizada con el esquemático.
    pin_red, sellos = netlist_kicad()
    redes = {}
    for nombre in sorted(set(pin_red.values())):
        n = pcbnew.NETINFO_ITEM(board, nombre)
        board.Add(n)
        redes[nombre] = n
    redes["GND"] = redes.get("GND")

    huellas = {}
    for p in cto.PIEZAS:
        fp = cargar_huella(p["huella"])
        fp.SetReference(p["ref"])
        fp.SetValue(p["valor"])
        fp.SetPath(pcbnew.KIID_PATH("/" + sellos[p["ref"]]))
        fp.SetExcludedFromBOM(False)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() == pcbnew.Edge_Cuts:       # recortes de panel de los jacks
                fp.Remove(item)
        for campo in (fp.Reference(), fp.Value()):
            campo.SetTextSize(pcbnew.VECTOR2I(MM(0.9), MM(0.9)))
            campo.SetTextThickness(MM(0.14))
        for pad in fp.Pads():
            red = pin_red.get((p["ref"], pad.GetNumber()))
            if red:
                pad.SetNet(redes[red])
        board.Add(fp)
        huellas[p["ref"]] = fp

    for ref, (x, y, rot) in FIJAS.items():
        mover(huellas[ref], x, y, rot)
    usadas = set(FIJAS)
    for region, refs in BLOQUES:
        empaquetar([huellas[r] for r in refs], region)
        usadas |= set(refs)
    faltan = set(huellas) - usadas
    if faltan:
        raise SystemExit(f"Piezas sin ubicar: {sorted(faltan)}")

    # borde, agujeros de montaje y del módulo TFT
    linea(board, pcbnew.Edge_Cuts, [(0, 0), (ANCHO, 0), (ANCHO, ALTO), (0, ALTO), (0, 0)], 0.1)
    for x, y in ((4, 4), (ANCHO - 4, 4), (4, ALTO - 4), (ANCHO - 4, ALTO - 4)):
        agujero(board, x, y)
    for dx, dy in TFT_AGUJEROS:
        agujero(board, TFT_X + dx, TFT_Y + dy)

    # serigrafía de guía
    linea(board, pcbnew.F_SilkS, [(TFT_X, TFT_Y), (TFT_X + TFT_W, TFT_Y), (TFT_X + TFT_W, TFT_Y + TFT_H),
                                  (TFT_X, TFT_Y + TFT_H), (TFT_X, TFT_Y)], 0.12)
    texto(board, "WAVESHARE 1,9 (en tapa)", TFT_X + 26, TFT_Y + TFT_H - 2.0, 1.2)
    for x, t in ((106, "GRAVES"), (122, "MEDIOS"), (138, "AGUDOS")):
        texto(board, t, x, 58.0, 1.3)
    texto(board, "NIVEL", 151.5, 12.0, 1.2, rot=90)
    texto(board, "VOLUMEN", 151.5, 34.0, 1.2, rot=90)
    texto(board, "VISTA", 150.0, 52.3, 1.2)
    texto(board, "ENTRADA", 184.0, 25.0, 1.1, rot=90)
    texto(board, "SALIDA", 184.0, 47.0, 1.1, rot=90)
    texto(board, "Ecualizador de 3 bandas · ESP32 · Electrónica II · CUC 2026", 80.0, 118.0, 1.2)
    return board, huellas, redes


def rutear(board):
    dsn = os.path.join(HW, "ecualizador.dsn")
    ses = os.path.join(HW, "ecualizador.ses")
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise SystemExit("No se pudo exportar el DSN")
    r = subprocess.run(["java", "-jar", FREEROUTING, "-de", dsn, "-do", ses, "-mp", "40", "-host", "KiCad"],
                       capture_output=True, text=True, timeout=3000)
    if not os.path.exists(ses):
        raise SystemExit("Freerouting no produjo el archivo SES:\n" + r.stdout[-3000:] + r.stderr[-3000:])
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise SystemExit("No se pudo importar el SES")
    os.remove(ses)
    os.remove(dsn)


def quitar_colgantes(board):
    """Borra los trozos de pista que Freerouting deja con un extremo suelto."""
    while True:
        con = board.GetConnectivity()
        sueltas = [t for t in board.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T
                   and con.TestTrackEndpointDangling(t, False)]
        if not sueltas:
            return
        for t in sueltas:
            board.Remove(t)
        board.BuildConnectivity()


def main():
    board, huellas, redes = construir()
    if "--sin-rutear" not in sys.argv:
        rutear(board)
    for capa in (pcbnew.F_Cu, pcbnew.B_Cu):
        zona_gnd(board, capa, redes["GND"])
    # El relleno de zonas necesita una placa cargada desde archivo (con su proyecto).
    board.Save(SALIDA)
    board = pcbnew.LoadBoard(SALIDA)
    board.BuildConnectivity()
    quitar_colgantes(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(SALIDA)
    huellas = {f.GetReference(): f for f in board.GetFootprints()}
    # posiciones de las piezas del panel para el modelo del gabinete
    panel = {}
    for ref in ("RV1", "RV2", "RV3", "RV4", "RV5", "SW1", "J1", "J2", "J4", "U5"):
        fp = huellas[ref]
        x0, y0, x1, y1 = caja(fp)
        panel[ref] = dict(x=pcbnew.ToMM(fp.GetPosition().x), y=pcbnew.ToMM(fp.GetPosition().y),
                          rot=fp.GetOrientationDegrees(), caja=[x0, y0, x1, y1])
    os.makedirs(os.path.join(HW, "3d"), exist_ok=True)
    json.dump(dict(placa=[ANCHO, ALTO], tft=[TFT_X, TFT_Y, TFT_W, TFT_H], piezas=panel),
              open(os.path.join(HW, "3d", "panel.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(AQUI, "finalizar_pcb.py")], check=True)
    print("PCB escrita en", os.path.normpath(SALIDA))


if __name__ == "__main__":
    main()

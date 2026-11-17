#!/usr/bin/env python3
"""Genera una vista 3D del retrofit D.3-LM324 sobre la PCB D.2 existente.

Este archivo es deliberadamente un modelo de ensamblaje, no una PCB D.3 reruteada ni
un paquete de fabricación. Las conexiones eléctricas de los ocho resistores y los cables
de alimentación se ejecutan según hardware/RETROFIT-LM324.md.
"""
from pathlib import Path
import subprocess

import pcbnew as k

import pcb_legado_b1 as base


ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "hardware"
OUT = HW / "3d"
SOURCE = HW / "ecualizador.kicad_pcb"
BOARD = HW / "ecualizador-D3-retrofit-3d.kicad_pcb"
RESISTOR = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"

# Zona central libre de la placa D.2. R34 se desplaza para no invadir J4.
POSITIONS = {
    "R33": (84.0, 25.0),
    "R34": (70.0, 38.0),
    "R35": (84.0, 35.0),
    "R36": (96.0, 35.0),
    "R37": (84.0, 45.0),
    "R38": (96.0, 45.0),
    "R39": (84.0, 55.0),
    "R40": (96.0, 55.0),
}


def mm(x: float) -> int:
    return k.FromMM(x)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    board = k.LoadBoard(str(SOURCE))
    title = board.GetTitleBlock()
    title.SetTitle("Ecualizador D.3-LM324 — modelo 3D del retrofit sobre PCB D.2")
    title.SetRevision("D.3-RETROFIT-3D")
    title.SetDate("2026-11-05")

    for ref in ("U1", "U2", "U3", "U4"):
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise RuntimeError(f"Falta {ref} en {SOURCE}")
        fp.SetValue("LM324N")

    for ref, (x, y) in POSITIONS.items():
        fp = base.cargar_huella(RESISTOR)
        fp.SetReference(ref)
        fp.SetValue("10k 1% (retrofit ADC)")
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetPosition(k.VECTOR2I(mm(x), mm(y)))
        fp.Reference().SetVisible(True)
        fp.Value().SetVisible(False)
        board.Add(fp)

    base.texto(board, "D.3 LM324 · RETROFIT 3D · VER GUÍA DE CABLEADO", 74, 63, 1.2)
    board.Save(str(BOARD))

    common = ["--subst-models", "--force"]
    # Los puentes D.2 usan modelos VRML generados localmente. GLB/VRML/render los aceptan,
    # pero STEP solo admite BREP/STEP/IGES; se excluyen del STEP sin quitarlos de las vistas.
    step_refs = ",".join(fp.GetReference() for fp in board.GetFootprints()
                         if not fp.GetReference().startswith("JP"))
    subprocess.run(["kicad-cli", "pcb", "export", "step", str(BOARD),
                    "-o", str(OUT / "ecualizador-D3-retrofit.step"),
                    "--component-filter", step_refs, *common], check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "glb", str(BOARD),
                    "-o", str(OUT / "ecualizador-D3-retrofit.glb"), *common], check=True)
    subprocess.run(["kicad-cli", "pcb", "export", "vrml", str(BOARD),
                    "-o", str(OUT / "ecualizador-D3-retrofit.wrl"), "--units", "mm", "-f"], check=True)
    subprocess.run(["kicad-cli", "pcb", "render", str(BOARD),
                    "-o", str(OUT / "ecualizador-D3-retrofit.png"),
                    "--width", "1800", "--height", "1100", "--quality", "high",
                    "--background", "opaque", "--rotate", "'-45,0,30'", "--zoom", "0.9"], check=True)
    subprocess.run(["kicad-cli", "pcb", "render", str(BOARD),
                    "-o", str(OUT / "ecualizador-D3-retrofit-inferior.png"),
                    "--width", "1800", "--height", "1100", "--quality", "high",
                    "--background", "opaque", "--side", "bottom", "--zoom", "0.9"], check=True)
    # KiCad crea metadatos de proyecto junto al PCB durante algunos exportes. Este modelo
    # usa las reglas del proyecto principal y no necesita archivos .kicad_pro/.kicad_prl propios.
    for suffix in (".kicad_pro", ".kicad_prl"):
        BOARD.with_suffix(suffix).unlink(missing_ok=True)
    print(OUT / "ecualizador-D3-retrofit.step")


if __name__ == "__main__":
    main()

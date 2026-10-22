#!/usr/bin/env python3
"""La revisión D.2 se genera con plano GND; comprobar continuidad y paridad."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[1]
subprocess.run(['kicad-cli','pcb','drc','--schematic-parity',str(r/'hardware/ecualizador.kicad_pcb'),'-o',str(r/'hardware/drc.rpt')],check=True)

#!/usr/bin/env bash
# Regenera el modelo del gabinete y las vistas renderizadas.
#   1. exporta la PCB de KiCad a VRML (con sus modelos 3D)
#   2. construye las piezas del gabinete en CadQuery (stl/ y STEP)
#   3. renderiza en Blender (Cycles): ../img/3d-gabinete-*.png
set -euo pipefail
cd "$(dirname "$0")"
kicad-cli pcb export vrml ../hardware/ecualizador.kicad_pcb -o ../hardware/3d/ecualizador-placa.wrl --units mm -f
kicad-cli pcb export glb ../hardware/ecualizador.kicad_pcb -o ../hardware/3d/ecualizador-placa.glb --user-origin 100x60mm --subst-models --force
kicad-cli pcb export glb ../hardware/archivo/B1/ecualizador.kicad_pcb -o ../hardware/3d/panel-controles.glb --user-origin 100x60mm --subst-models --force --no-board-body --component-filter "RV1,RV2,RV3,RV4,RV5,J1,J2,SW1"
"${PYTHON:-../.venv/bin/python}" gabinete.py
MUESTRAS=${MUESTRAS:-96} blender -b -P render_blender.py -- cerrado abierto planta debajo canales

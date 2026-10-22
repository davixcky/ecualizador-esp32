#!/usr/bin/env bash
# Exporta los archivos de fabricación de la PCB (Gerber, taladros, posición) y el PDF del esquemático.
set -euo pipefail
cd "$(dirname "$0")/../hardware"
F=fabricacion
rm -rf "$F/gerber" && mkdir -p "$F/gerber"
kicad-cli pcb export gerbers ecualizador.kicad_pcb -o "$F/gerber/" \
  -l F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts >/dev/null
kicad-cli pcb export drill ecualizador.kicad_pcb -o "$F/gerber/" >/dev/null
(cd "$F/gerber" && zip -q -r ../gerbers-ecualizador.zip .)
kicad-cli pcb export pdf ecualizador.kicad_pcb -o "$F/serigrafia-arriba.pdf" -l F.Cu,F.Silkscreen,Edge.Cuts >/dev/null
kicad-cli pcb export step ecualizador.kicad_pcb -o 3d/ecualizador-placa.step --subst-models --force >/dev/null 2>&1 || true
kicad-cli sch export pdf ecualizador.kicad_sch -o ecualizador.pdf >/dev/null
kicad-cli sch export bom ecualizador.kicad_sch -o fabricacion/bom.csv --fields "Reference,Value,Footprint,\${QUANTITY}" --group-by Value,Footprint >/dev/null
kicad-cli pcb drc ecualizador.kicad_pcb -o drc.rpt --schematic-parity >/dev/null || true
kicad-cli sch erc ecualizador.kicad_sch -o erc.rpt >/dev/null || true
echo "Archivos de fabricación en hardware/$F"

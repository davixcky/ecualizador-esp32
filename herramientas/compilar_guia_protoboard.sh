#!/usr/bin/env bash
# Ejecutar desde cualquier carpeta; requiere Python del proyecto, KiCad CLI y LuaLaTeX.
set -euo pipefail
cd "$(dirname "$0")/.."
"${PYTHON:-.venv/bin/python}" herramientas/generar_guia_protoboard.py
"${PYTHON:-.venv/bin/python}" herramientas/figuras_protoboard.py
cd docs/latex
lualatex -interaction=nonstopmode -halt-on-error prototipo-protoboard.tex
lualatex -interaction=nonstopmode -halt-on-error prototipo-protoboard.tex
cp prototipo-protoboard.pdf ../protoboard/guia-prototipo-protoboard.pdf

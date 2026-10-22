#!/usr/bin/env bash
# Requiere TeX Live (latex-extra, lang-spanish, fonts-recommended, luatex), pandoc y Python con pymupdf/python-pptx.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"
python3 herramientas/generar_presentacion_filtros.py
cd docs/latex
for doc in informe presentacion presentacion-filtros; do
  lualatex -interaction=nonstopmode -halt-on-error "$doc.tex"
  lualatex -interaction=nonstopmode -halt-on-error "$doc.tex"
done
lualatex -interaction=nonstopmode -halt-on-error -jobname=presentacion-notas '\def\connotas{1}\input{presentacion.tex}'
lualatex -interaction=nonstopmode -halt-on-error -jobname=presentacion-animada '\def\animada{1}\input{presentacion.tex}'
lualatex -interaction=nonstopmode -halt-on-error -jobname=presentacion-animada '\def\animada{1}\input{presentacion.tex}'
pandoc informe.tex --lua-filter=imagenes-docx.lua --resource-path=../../img:. -o ../informe-fase2.docx
pandoc informe.tex --lua-filter=imagenes-docx.lua --resource-path=../../img:. -t gfm -o ../informe-fase2.md
cd "$ROOT"
"${PYTHON:-.venv/bin/python}" herramientas/exportar_pptx.py

"${PYTHON:-.venv/bin/python}" herramientas/exportar_filtros.py

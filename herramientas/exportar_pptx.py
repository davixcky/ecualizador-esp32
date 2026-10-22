#!/usr/bin/env python3
"""Arma docs/presentacion/presentacion-fase2.pptx: una diapositiva 16:9 por PNG (las que dibuja
exportar_documentos.js) con sus notas del orador. El texto queda como imagen; para editarlo se
usan las fuentes HTML de docs/presentacion/fuente/ o la presentación en línea."""
import json
import os

from pptx import Presentation
from pptx.util import Emu

AQUI = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(AQUI, "..", "docs", "presentacion")

notas = json.load(open(os.path.join(DECK, "notas.json"), encoding="utf-8"))
prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)      # 16:9
vacia = prs.slide_layouts[6]
for i, ident in enumerate(notas["orden"]):
    s = prs.slides.add_slide(vacia)
    png = os.path.join(DECK, "png", f"{i + 1:02d}-{ident}.png")
    s.shapes.add_picture(png, 0, 0, width=prs.slide_width, height=prs.slide_height)
    s.notes_slide.notes_text_frame.text = notas["notas"].get(ident, "")
prs.save(os.path.join(DECK, "presentacion-fase2.pptx"))
print("PPTX con", len(notas["orden"]), "diapositivas")

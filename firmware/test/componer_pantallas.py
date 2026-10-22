#!/usr/bin/env python3
"""Convierte las pantallas PPM a PNG ampliadas y arma una lámina con las cuatro vistas dentro
de un marco que imita el módulo TFT de 2,8"."""
import os
import sys

from PIL import Image, ImageDraw

entrada, salida = sys.argv[1], sys.argv[2]
os.makedirs(salida, exist_ok=True)
nombres = ["arranque", "bandas", "espectro", "onda", "recorte"]
img = {}
for n in nombres:
    im = Image.open(os.path.join(entrada, n + ".ppm")).convert("RGB")
    grande = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    grande.save(os.path.join(salida, f"ui-tft-{n}.png"))
    img[n] = grande


def marco(im):
    m = 26
    fondo = Image.new("RGB", (im.width + 2 * m + 40, im.height + 2 * m), (176, 30, 40))
    d = ImageDraw.Draw(fondo)
    d.rounded_rectangle((m - 8, m - 8, m + im.width + 8, m + im.height + 8), 10, fill=(12, 12, 14))
    for k in range(14):                      # conector de 14 pines
        y = fondo.height // 2 - 7 * 18 + k * 18
        d.rectangle((fondo.width - 28, y, fondo.width - 16, y + 10), fill=(212, 175, 55))
    fondo.paste(im, (m, m))
    return fondo


cuadros = [marco(img[n]) for n in ["arranque", "bandas", "espectro", "onda"]]
w, h = cuadros[0].size
lamina = Image.new("RGB", (2 * w + 30, 2 * h + 30), (255, 255, 255))
for i, c in enumerate(cuadros):
    lamina.paste(c, (10 + (i % 2) * (w + 10), 10 + (i // 2) * (h + 10)))
lamina.save(os.path.join(salida, "ui-tft-vistas.png"))
print("PNG escritos en", salida)

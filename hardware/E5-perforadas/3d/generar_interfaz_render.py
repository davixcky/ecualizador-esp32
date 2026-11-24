#!/usr/bin/env python3
"""Genera la interfaz vertical estática usada únicamente por los renders E.5.

La pantalla recibida (ESP32-3248S035) va montada en vertical: la interfaz es de
320 x 480 y se dibuja a 1,5x (480 x 720) para que el texto del render quede legible.
"""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 480, 720


def font(bold, size):
    family = "DejaVu Sans:bold" if bold else "DejaVu Sans"
    path = subprocess.check_output(["fc-match", "-f", "%{file}", family], text=True)
    return ImageFont.truetype(path, size)


im = Image.new("RGB", (W, H), (2, 5, 8))
d = ImageDraw.Draw(im)
fg, muted = (238, 242, 245), (115, 128, 140)
colors = ((255, 122, 51), (64, 214, 128), (64, 164, 255))
d.text((24, 22), "ECUALIZADOR E.5", font=font(False, 17), fill=muted)
d.text((456, 22), "ESP-NOW", font=font(False, 17), fill=muted, anchor="ra")
d.text((24, 48), "TRES BANDAS", font=font(True, 32), fill=fg)
d.line((24, 98, 456, 98), fill=(35, 43, 50), width=2)
for i, (name, db, mv, color) in enumerate(zip(("GRAVES", "MEDIOS", "AGUDOS"), (-32, -19, -28), (152, 196, 168), colors)):
    y0 = 117 + i * 180
    d.rounded_rectangle((24, y0, 456, y0 + 162), 12, fill=tuple(int(c * .13) for c in color), outline=tuple(int(c * .45) for c in color), width=2)
    d.text((40, y0 + 16), name, font=font(True, 22), fill=color)
    d.text((440, y0 + 14), f"{db} dB", font=font(True, 28), fill=fg, anchor="ra")
    bar_y = y0 + 62
    d.rounded_rectangle((40, bar_y, 440, bar_y + 38), 8, fill=(18, 23, 28))
    level = int(400 * (db + 60) / 60)
    d.rounded_rectangle((40, bar_y, 40 + level, bar_y + 38), 8, fill=color)
    d.text((40, bar_y + 52), f"{mv} mV", font=font(True, 23), fill=fg)
    d.text((440, bar_y + 56), "PICO", font=font(False, 15), fill=muted, anchor="ra")
d.text((240, 684), "Valores de ejemplo - interfaz propuesta (320 x 480)", font=font(False, 15), fill=muted, anchor="ma")
im.save(HERE / "tft-render-vertical.png")

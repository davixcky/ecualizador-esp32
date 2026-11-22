#!/usr/bin/env python3
"""Genera la interfaz horizontal estática usada únicamente por los renders E.5."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 600, 450


def font(bold, size):
    family = "DejaVu Sans:bold" if bold else "DejaVu Sans"
    path = subprocess.check_output(["fc-match", "-f", "%{file}", family], text=True)
    return ImageFont.truetype(path, size)


im = Image.new("RGB", (W, H), (2, 5, 8))
d = ImageDraw.Draw(im)
fg, muted = (238, 242, 245), (115, 128, 140)
colors = ((255, 122, 51), (64, 214, 128), (64, 164, 255))
d.text((28, 24), "ECUALIZADOR E.5", font=font(False, 18), fill=muted)
d.text((572, 24), "Wi-Fi", font=font(False, 18), fill=muted, anchor="ra")
d.text((28, 51), "TRES BANDAS", font=font(True, 34), fill=fg)
d.line((28, 99, 572, 99), fill=(35, 43, 50), width=2)
for i, (name, db, mv, color) in enumerate(zip(("GRAVES", "MEDIOS", "AGUDOS"), (-32, -19, -28), (152, 196, 168), colors)):
    x0 = 28 + i * 184
    d.rounded_rectangle((x0, 122, x0 + 168, 374), 12, fill=tuple(int(c * .13) for c in color), outline=tuple(int(c * .45) for c in color), width=2)
    d.text((x0 + 16, 140), name, font=font(True, 20), fill=color)
    d.text((x0 + 152, 138), f"{db} dB", font=font(True, 26), fill=fg, anchor="ra")
    bar_y = 215
    d.rounded_rectangle((x0 + 16, bar_y, x0 + 152, bar_y + 38), 8, fill=(18, 23, 28))
    level = int(136 * (db + 60) / 60)
    d.rounded_rectangle((x0 + 16, bar_y, x0 + 16 + level, bar_y + 38), 8, fill=color)
    d.text((x0 + 16, 281), f"{mv} mV", font=font(True, 23), fill=fg)
    d.text((x0 + 16, 321), "PICO", font=font(False, 15), fill=muted)
    d.line((x0 + 70, 332, x0 + 150, 332), fill=fg, width=3)
d.text((300, 414), "Valores ilustrativos · interfaz propuesta", font=font(False, 16), fill=muted, anchor="ma")
im.save(HERE / "tft-render-horizontal.png")

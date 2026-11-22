"""Fotogramas de la pantalla (LilyGO T4-S3, 450 x 600 en vertical) y subtítulos del video E.5.

Los VALORES salen del código del firmware: tft_firmware.cpp se compila contra firmware/lib/{interfaz,dsp}.
El DIBUJO es una propuesta de interfaz a pantalla completa hecha aquí con Pillow, porque el firmware
de la T4-S3 todavía no existe. Requiere las bibliotecas de PlatformIO: `pio pkg install -d firmware`.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORK = HERE / ".trabajo"
TFT = ROOT / "docs/video/tft-fotogramas"      # se versionan: el .blend los enlaza con ruta relativa
TFT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))
from timeline import FPS, FRAMES, caption  # noqa: E402

fw = ROOT / "firmware"
gfx = fw / ".pio/libdeps/esp32dev/Adafruit GFX Library"
exe = WORK / "tft_firmware"
subprocess.run(["g++", "-std=c++17", "-O2", "-DARDUINO=100", f"-I{fw / 'test/arduino'}", f"-I{gfx}", f"-I{fw / 'lib/interfaz'}", f"-I{fw / 'lib/dsp'}",
                "-o", str(exe), str(HERE / "tft_firmware.cpp"), str(fw / "lib/dsp/dsp.cpp")], check=True)
for old in TFT.glob("tft-*.p*"):
    old.unlink()
print(subprocess.check_output([str(exe), str(WORK / "tft-entrada.bin"), str(WORK / "pantalla-valores.bin"), str(FPS)], text=True).strip())
raw = np.fromfile(WORK / "pantalla-valores.bin", dtype=np.float32)
NB = 32
edges, rows = raw[:NB + 1], raw[NB + 1:].reshape(-1, 13 + 2 * NB)
assert len(rows) == FRAMES, len(rows)

Wp, Hp = 450, 600


def font(bold, size):
    path = subprocess.check_output(["fc-match", "-f", "%{file}", "DejaVu Sans:bold" if bold else "DejaVu Sans"], text=True)
    return ImageFont.truetype(path, size)


F_T, F_S, F_N, F_L, F_X = font(True, 34), font(False, 17), font(True, 40), font(True, 22), font(False, 15)
BG, FG, MUT, GRID = (0, 0, 0), (236, 240, 244), (120, 130, 140), (34, 40, 46)
COL = [(255, 122, 51), (64, 214, 128), (64, 164, 255)]       # naranja, verde, azul: como las tres barras LED
NAMES = ("GRAVES", "MEDIOS", "AGUDOS")


def dim(c, k):
    return tuple(int(v * k) for v in c)


def header(d, title):
    d.text((24, 22), "ECUALIZADOR E.5", font=F_S, fill=MUT)
    d.text((Wp - 24, 22), "Wi-Fi", font=F_S, fill=MUT, anchor="ra")
    d.text((24, 46), title, font=F_T, fill=FG)
    d.line((24, 96, Wp - 24, 96), fill=GRID, width=2)


def frame(r):
    im = Image.new("RGB", (Wp, Hp), BG)
    d = ImageDraw.Draw(im)
    vista = int(r[0])
    y0, y1 = 190, 520                      # escala de 0 a -60 dB
    if vista == 0:
        header(d, "TRES BANDAS")
        for b in range(3):
            xc = 85 + b * 140
            db, pk, mv = r[2 + b], r[5 + b], r[8 + b]
            d.text((xc, 112), NAMES[b], font=F_L, fill=COL[b], anchor="ma")
            d.text((xc, 140), f"{db:.0f}", font=F_N, fill=FG, anchor="ma")
            d.rounded_rectangle((xc - 42, y0, xc + 42, y1), 8, fill=dim(COL[b], .13))
            for g in range(1, 6):
                yy = y0 + (y1 - y0) * g / 6
                d.line((xc - 42, yy, xc + 42, yy), fill=BG, width=2)
            h = (max(-60.0, min(0.0, db)) + 60) / 60 * (y1 - y0)
            if h > 2:
                d.rounded_rectangle((xc - 42, y1 - h, xc + 42, y1), 8 if h > 16 else 2, fill=COL[b])
            yp = y1 - (max(-60.0, min(0.0, pk)) + 60) / 60 * (y1 - y0)
            d.rectangle((xc - 42, yp - 2, xc + 42, yp + 2), fill=FG)
            d.text((xc, y1 + 12), f"{mv:.0f} mV", font=F_S, fill=MUT, anchor="ma")
        d.text((Wp / 2, 566), "dB · pico por banda respecto a VREF", font=F_X, fill=MUT, anchor="ma")
    else:
        header(d, "ESPECTRO")
        d.text((24, 112), f"Pico {r[-2]:.0f} Hz", font=F_L, fill=FG)
        d.text((Wp - 24, 112), f"{r[-1]:.1f} dBFS", font=F_L, fill=MUT, anchor="ra")
        for g in range(7):
            yy = y0 + (y1 - y0) * g / 6
            d.line((24, yy, Wp - 24, yy), fill=GRID, width=1)
        bw = (Wp - 48) / NB
        for j in range(NB):
            fc = (edges[j] * edges[j + 1]) ** .5 if edges[j] > 0 else edges[j + 1] / 2
            c = COL[0 if fc < 300 else 1 if fc < 3000 else 2]
            x = 24 + j * bw
            h = (max(-60.0, min(0.0, r[11 + j])) + 60) / 60 * (y1 - y0)
            d.rectangle((x + 1.5, y1 - max(h, 2), x + bw - 1.5, y1), fill=c)
            yp = y1 - (max(-60.0, min(0.0, r[11 + NB + j])) + 60) / 60 * (y1 - y0)
            d.rectangle((x + 1.5, yp - 1.5, x + bw - 1.5, yp + 1.5), fill=FG)
        for txt, xx, an in (("30 Hz", 24, "la"), ("300", 24 + (Wp - 48) * .42, "ma"), ("1 k", 24 + (Wp - 48) * .67, "ma"), ("5 kHz", Wp - 24, "ra")):
            d.text((xx, y1 + 12), txt, font=F_S, fill=MUT, anchor=an)
        d.text((Wp / 2, 566), "0 a -60 dBFS · salida ecualizada", font=F_X, fill=MUT, anchor="ma")
    if r[1] > .5:
        d.rounded_rectangle((Wp - 110, 46, Wp - 24, 86), 6, fill=(230, 40, 40))
        d.text((Wp - 67, 66), "CLIP", font=F_L, fill=FG, anchor="mm")
    return im


for i, r in enumerate(rows, 1):
    frame(r).save(TFT / f"tft-{i:04d}.png")


def stamp(t):
    return f"{int(t // 3600)}:{int(t // 60) % 60:02}:{t % 60:05.2f}"


ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,28,&H00FFFFFF,&H00FFFFFF,&H00201810,&H00000000,1,0,0,0,100,100,0,0,1,2,0,9,64,64,48,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
start, last = 0, caption(0)
for i in range(1, FRAMES + 1):
    cur = caption(i / FPS) if i < FRAMES else None
    if cur != last:
        ass += f"Dialogue: 0,{stamp(start / FPS)},{stamp(i / FPS)},Default,,0,0,0,,{last}\n"
        start, last = i, cur
(ROOT / "docs/video/demo-subtitulos.ass").write_text(ass, encoding="utf-8")
print(f"{FRAMES} PNG en {TFT} y subtítulos")

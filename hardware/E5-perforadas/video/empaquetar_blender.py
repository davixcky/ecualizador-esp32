"""ZIP con la escena editable del video E.5 y todo lo que enlaza por ruta relativa."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[3]
out = root / "docs/video"
files = [out / n for n in ("ecualizador-animado.blend", "ecualizador-animado.mp4", "README.md", "REVIEW.md", "demo-audio.wav", "demo-timeline.json", "validacion-audio.json")]
files += sorted((out / "tft-fotogramas").glob("*.png"))
with ZipFile(out / "ecualizador-blender.zip", "w", ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(root))
    z.writestr("ABRIR.txt", "Extraer todo conservando las carpetas. Abrir docs/video/ecualizador-animado.blend en Blender 5.1.\n"
               "La pantalla usa la secuencia docs/video/tft-fotogramas/; el audio es docs/video/demo-audio.wav.\n"
               "Tapa_pivote abre la tapa; Perilla_RV1..RV5 giran los controles. La barra espaciadora reproduce.\n"
               "Motor: Cycles en GPU; elegir CPU u otra GPU si hace falta.\n"
               "Montaje E.5 en tarjetas perforadas: cinco controles rotativos, sin deslizables.\n")
print(out / "ecualizador-blender.zip")

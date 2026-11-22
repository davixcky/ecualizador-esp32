#!/usr/bin/env python3
"""Valida que las vistas fijas E.5 existan, decodifiquen y sean actuales."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageStat

HERE = Path(__file__).resolve().parent
EXPECTED = {
    "ecualizador-E5-cerrado.png": (2000, 1300),
    "ecualizador-E5-detalle-controles.png": (2000, 1300),
    "ecualizador-E5-abierto.png": (2000, 1300),
    "ecualizador-E5-planta.png": (1500, 2100),
    "ecualizador-E5-pantalla-soporte-explotado.png": (1800, 1350),
}
SOURCES = [HERE / ".render/ensamble.json", HERE / "render_modelo.py", HERE / "escena_blender.py", HERE / "tft-render-horizontal.png"]
fresh_after = max(p.stat().st_mtime for p in SOURCES)
issues, files = [], []
for name, expected_size in EXPECTED.items():
    path = HERE / name
    row = {"file": name, "expected_pixels": list(expected_size)}
    if not path.exists():
        issues.append(f"falta {name}")
        files.append(row)
        continue
    try:
        with Image.open(path) as im:
            im.load()
            actual = im.size
            deviation = round(ImageStat.Stat(im.convert("L").resize((256, 256))).stddev[0], 2)
        row.update({"pixels": list(actual), "bytes": path.stat().st_size,
                    "grayscale_stddev": deviation,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "fresh": path.stat().st_mtime >= fresh_after})
        if actual != expected_size: issues.append(f"{name}: resolución {actual}, esperada {expected_size}")
        if path.stat().st_size < 50_000: issues.append(f"{name}: archivo demasiado pequeño")
        if deviation < 8: issues.append(f"{name}: imagen posiblemente vacía")
        if not row["fresh"]: issues.append(f"{name}: anterior a sus fuentes")
    except Exception as exc:
        issues.append(f"{name}: no decodifica: {exc}")
    files.append(row)

report = {
    "revision": "E.5", "valid": not issues, "issues": issues, "files": files,
    "scope": "Integridad, resolución, contenido no vacío y vigencia de renders fijos.",
    "does_not_prove": "Encaje físico, imprimibilidad, funcionamiento eléctrico ni fidelidad óptica.",
}
(HERE / "validacion-renders.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print("RENDERS_E5_OK" if not issues else "RENDERS_E5_ERROR")
for issue in issues: print("-", issue)
raise SystemExit(bool(issues))

"""Validación de la entrega E.5: CAD, escena de Blender, MP4, audio y textos vigentes.

    .venv/bin/python hardware/E5-perforadas/video/validar_entrega.py

Escribe docs/validacion/video-dispositivo.json y docs/video/hoja-de-contacto.jpg.
Mide; no escucha: el audio se evalúa solo con métricas y decodificación.
"""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from timeline import FPS, FRAMES, DURATION, BAND_START  # noqa: E402

V = ROOT / "docs/video"
E5 = ROOT / "hardware/E5-perforadas"
video = V / "ecualizador-animado.mp4"
SLIDER = re.compile(r"desliz|slider|slide[ -]?pot", re.I)
report = {}

# ---------------------------------------------------------------- CAD
with zipfile.ZipFile(E5 / "3d/ecualizador-E5-perforadas.FCStd") as z:
    xml = z.read("Document.xml").decode("utf-8")
cad_names = re.findall(r'<Object type="[^"]+" name="([^"]+)"', xml)
step = (E5 / "3d/ecualizador-E5-perforadas.step").read_text(errors="ignore")
stl = sorted(p.name for p in (E5 / "3d/stl").glob("*.stl"))
b10k = sorted(n for n in cad_names if "_B10K_" in n and n.endswith("_cuerpo"))
a10k = sorted(n for n in cad_names if "_A10K_" in n and n.endswith("_cuerpo"))
val3d = json.loads((E5 / "3d/validacion-3d.json").read_text(encoding="utf-8"))
medidas = json.loads((E5 / "3d/medidas-componentes.json").read_text(encoding="utf-8"))["componentes"]
assert not [n for n in cad_names + stl if SLIDER.search(n)] and not SLIDER.search(step)
assert len(b10k) == 3 and medidas["Potenciometro-B10K"]["cantidad_comprada"] - len(b10k) == 1
assert len(a10k) == 2 and all("PENDIENTE" in n for n in a10k)
assert val3d["valid"] and val3d["deslizables"] == 0
report["cad"] = {"objetos": len(cad_names), "deslizables": 0, "B10K_montados": b10k, "B10K_repuesto_sin_montar": 1, "A10K_pendientes": a10k,
                 "perillas": sorted(n for n in cad_names if n.startswith("Perilla_") and n.endswith("PENDIENTE_COMPRA")),
                 "tarjetas": sorted(n for n in cad_names if "_Perforada_" in n), "stl": stl,
                 "comprobaciones_dimensionales": f"{sum(c['cumple'] for c in val3d['comprobaciones'])}/{len(val3d['comprobaciones'])} cumplen",
                 "gabinete_mm": val3d["gabinete_mm"]}

# ---------------------------------------------------------------- Blender
out = subprocess.run(["blender", "-b", str(V / "ecualizador-animado.blend"), "-P", str(HERE / "validar_blender.py")], capture_output=True, text=True)
line = next((l for l in out.stdout.splitlines() if l.startswith("E5_BLEND_JSON ")), None)
assert line, out.stdout[-3000:] + out.stderr[-3000:]
blend = json.loads(line.split(" ", 1)[1])
assert not blend["nombres_con_deslizable"] and len(blend["B10K"]) == 3 and len(blend["A10K_pendientes"]) == 2 and len(blend["parlantes"]) == 2
report["blender"] = blend

# ---------------------------------------------------------------- MP4
probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(video)]))
v = next(s for s in probe["streams"] if s["codec_type"] == "video")
a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
assert (v["width"], v["height"]) == (1920, 1080) and v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p"
assert v["r_frame_rate"] == f"{FPS}/1" and int(v["nb_read_frames"]) == FRAMES
assert a["codec_name"] == "aac" and int(a["sample_rate"]) == 48000
assert abs(float(probe["format"]["duration"]) - DURATION) < .06
dec = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(video), "-f", "null", "-"], capture_output=True, text=True)
assert dec.returncode == 0 and not dec.stderr.strip(), dec.stderr
decoded = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(video), "-map", "0:a:0", "-ac", "1", "-f", "f32le", "-acodec", "pcm_f32le", "-"]), dtype=np.float32)
sr, wav = wavfile.read(V / "demo-audio.wav")
wav = wav.astype(float) / 32768
n = min(len(wav), len(decoded))
lag = int(np.argmax(signal.correlate(decoded[:sr * 5], wav[:sr * 5], mode="full")) - (sr * 5 - 1))
dd = decoded[max(0, lag):][:n - abs(lag)]
ww = wav[max(0, -lag):][:len(dd)]
corr = float(np.corrcoef(ww, dd[:len(ww)])[0, 1])
assert corr > .99, corr
loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-map", "0:a:0", "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
lj = json.loads(loud[loud.rindex("{"):loud.rindex("}") + 1])
silence = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-map", "0:a:0", "-af", "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-"], capture_output=True, text=True).stderr
# Efecto de cada control rotativo medido en el audio decodificado del MP4, por banda.
bands = []
for band, (lo, hi) in enumerate([(20, 300), (300, 3000), (3000, 18000)]):
    y = signal.sosfilt(signal.butter(4, [lo, hi], fs=sr, btype="bandpass", output="sos"), decoded.astype(float))
    def rms_db(t0, t1):
        seg = y[round((BAND_START[band] + t0) * sr):round((BAND_START[band] + t1) * sr)]
        return float(10 * np.log10(np.mean(seg ** 2) + 1e-20))
    mn, mx = rms_db(1.0, 1.95), rms_db(3.95, 4.9)
    assert mx - mn > 5, (band, mn, mx)
    bands.append({"banda": ("graves", "medios", "agudos")[band], "control": f"RV{band + 2}", "filtro_Hz": [lo, hi],
                  "nivel_con_control_al_minimo_dB": round(mn, 2), "nivel_con_control_al_maximo_dB": round(mx, 2), "diferencia_dB": round(mx - mn, 2)})
report["video"] = {"archivo": "docs/video/ecualizador-animado.mp4", "codec": v["codec_name"], "perfil": v.get("profile"), "pix_fmt": v["pix_fmt"],
                   "pixeles": [v["width"], v["height"]], "fps": FPS, "fotogramas_decodificados": int(v["nb_read_frames"]),
                   "duracion_s": float(probe["format"]["duration"]), "tamano_bytes": video.stat().st_size, "decodificacion_completa_sin_errores": True,
                   "sha256": hashlib.sha256(video.read_bytes()).hexdigest()}
report["audio"] = {"codec": a["codec_name"], "canales": int(a["channels"]), "frecuencia_muestreo": int(a["sample_rate"]), "duracion_s": float(a["duration"]),
                   "correlacion_con_wav_del_modelo": round(corr, 5), "desfase_muestras": lag, "pico_decodificado": round(float(np.max(abs(decoded))), 4),
                   "muestras_en_recorte": int(np.sum(abs(decoded) >= 1)), "LUFS_integrado": float(lj["input_i"]), "pico_real_dBTP": float(lj["input_tp"]),
                   "LRA_LU": float(lj["input_lra"]), "silencios_mayores_a_0p5s": silence.count("silence_start"), "efecto_por_control": bands,
                   "metodo": "respuestas AC de ngspice (macromodelo LM324) aplicadas por ventanas; no es grabación del prototipo",
                   "escucha_humana": False}

# ---------------------------------------------------------------- hoja de contacto desde el MP4 final
sheet = V / "hoja-de-contacto.jpg"
times = [0.0, 2.0, 5.0, 6.5, 8.0, 9.0, 11.5, 15.5, 18.5, 22.5, 25.5, 28.7, 30.0, 32.0, 33.2, 34.5, 36.5, 39.5, 41.5, 43.0, 45.0, 46.5, 48.0, 49.9]
tmp = HERE / ".trabajo/contacto"
tmp.mkdir(parents=True, exist_ok=True)
for i, t in enumerate(times):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(video), "-frames:v", "1", "-vf",
                    f"scale=640:360,drawtext=text='{t:04.1f} s':x=10:y=10:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6", str(tmp / f"c{i:02d}.png")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", str(tmp / "c%02d.png"), "-vf", "tile=4x6", "-frames:v", "1", "-q:v", "3", "-update", "1", str(sheet)], check=True)
report["hoja_de_contacto"] = {"archivo": "docs/video/hoja-de-contacto.jpg", "instantes_s": times}

# ---------------------------------------------------------------- textos vigentes
vigentes = [ROOT / "README.md", ROOT / "hardware/COMPONENTES-COMPRADOS-VERIFICADOS.md", ROOT / "docs/presentacion/LEEME.md", *sorted(V.glob("*.md")), V / "demo-subtitulos.ass",
            *sorted(p for p in E5.rglob("*") if p.is_file() and p.suffix in {".md", ".csv", ".json", ".py", ".sh", ".cpp"} and ".trabajo" not in p.parts and ".render" not in p.parts
                    and "validacion" not in p.name and p.name not in {"validar_entrega.py", "validar_blender.py", "generar_modelo.py", "PROMPT-CLAUDE-CARRITOS.md"})]
hits = {}
for p in vigentes:
    if not p.exists():
        continue
    for i, text in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        # Se admite la palabra solo en frases que NIEGAN el deslizable.
        if SLIDER.search(text) and not re.search(r"\b(no|sin|ning[uú]n|ninguna|ni|antigu|anterior|archiv|D\.2|retir)", text, re.I):
            hits.setdefault(str(p.relative_to(ROOT)), []).append(i)
assert not hits, hits
report["textos_vigentes"] = {"archivos_revisados": len([p for p in vigentes if p.exists()]), "afirmaciones_de_controles_deslizables": 0,
                             "nota": "Los informes de la Fase 2 (docs/latex, docs/informe-fase2.*, docs/presentacion) describen la revisión D.2 archivada y llevan aviso."}
report["alcance"] = "Render y audio de un modelo de diseño. No sustituye pruebas eléctricas ni mecánicas; nadie escuchó el audio: solo se midió."
(ROOT / "docs/validacion/video-dispositivo.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in ("video", "audio")}, indent=2, ensure_ascii=False))
print("ENTREGA_E5_OK")

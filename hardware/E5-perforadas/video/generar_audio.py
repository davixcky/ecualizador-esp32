"""Audio y datos de pantalla del video E.5.

Composición original → respuestas AC de ngspice del circuito LM324 → WAV y bloques ADC.
Es una aproximación cuasiestática de pequeña señal; NO es audio grabado del prototipo.

    python hardware/E5-perforadas/video/generar_audio.py      # cualquier Python con NumPy y SciPy

Si docs/video/respuestas-spice.npz existe se reutiliza (las respuestas de banda no cambian
con NIVEL ni VOLUMEN, que aquí son ganancias escalares); ngspice solo hace falta para
recalcularlo. RV1 (NIVEL) y RV5 (VOLUMEN) son A10K logarítmicos NO COMPRADOS: se les aplica
una ley dB-lineal SUPUESTA de 30 dB de recorrido, como desviación respecto al punto
RV1 = RV5 = 0,5 con el que se calculó el banco SPICE (±15 dB entre extremos). NIVEL actúa
ANTES de los filtros (cambia el audio Y los medidores); VOLUMEN va de LINEA a AMP_IN,
DESPUÉS del punto de medida (cambia solo el audio).

Salidas en docs/video/: demo-audio.wav, demo-entrada.wav, respuestas-spice.npz,
demo-timeline.json, validacion-audio.json y, en .trabajo/, tft-entrada.bin para el
programa que dibuja la pantalla con el código del firmware.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "docs/video"
WORK = HERE / ".trabajo"
WORK.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(HERE))
from timeline import FPS, DURATION, FRAMES, BAND_START, SWEEP_START, state, view  # noqa: E402

SR = 48000
V_IN = 0.11                      # pico de entrada en J1 (el máximo previsto es 0,11 V)
NODES = ("LINEA", "G_W", "M_W", "A_W", "ADC_FFT_RAW")
POS = np.linspace(0, 1, 11)
NSEG, NOV = 4096, 3616

# ---- respuestas complejas del circuito: 3 bandas x 11 posiciones x 5 nodos (RV1 = RV5 = 0,5)
NPZ = OUT / "respuestas-spice.npz"
if NPZ.exists():
    data = np.load(NPZ)
    freq, H = data["frecuencia"], data["respuesta"]
    assert list(data["nodos"]) == list(NODES) and np.allclose(data["posiciones"], POS)
    spice_bank = "reutilizado de respuestas-spice.npz"
else:
    from simulacion import netlist, OPAMP_LIB
    bank = np.empty((3, len(POS), len(NODES)), dtype=object)
    with tempfile.TemporaryDirectory(prefix="eq-e5-spice-") as tmp:
        tmp = Path(tmp)
        (tmp / "lm324.lib").write_text(OPAMP_LIB)
        cols = " ".join(f"real(v({n})-v(VREF)) imag(v({n})-v(VREF))" if n != "LINEA" else "real(v(LINEA)) imag(v(LINEA))" for n in NODES)
        for band in range(3):
            for j, pos in enumerate(POS):
                pots = {"RV1": .5, "RV2": .5, "RV3": .5, "RV4": .5, "RV5": .5}
                pots[f"RV{band + 2}"] = float(pos)
                (tmp / "audio.cir").write_text("* Video E.5\n" + netlist(pots) + f"\n.control\nset wr_singlescale\nset wr_vecnames\nac dec 100 5 24000\nwrdata respuesta.dat {cols}\n.endc\n.end\n")
                r = subprocess.run(["ngspice", "-b", "audio.cir"], cwd=tmp, capture_output=True, text=True)
                if r.returncode:
                    raise RuntimeError(r.stdout + r.stderr)
                d = np.loadtxt(tmp / "respuesta.dat", skiprows=1)
                assert d.shape[1] == 1 + 2 * len(NODES), d.shape
                freq = d[:, 0]
                for k in range(len(NODES)):
                    bank[band, j, k] = d[:, 1 + 2 * k] + 1j * d[:, 2 + 2 * k]
    H = np.array([[[bank[b, j, k] for k in range(len(NODES))] for j in range(len(POS))] for b in range(3)])   # banda, pos, nodo, f
    np.savez_compressed(NPZ, frecuencia=freq, respuesta=H, posiciones=POS, nodos=np.array(NODES))
    spice_bank = "recalculado con ngspice"
assert np.all(np.isfinite(H))

# ---- ley SUPUESTA de los A10K (no comprados): dB-lineal, 30 dB de recorrido, 0 dB al 50 %
A10K_DB_SPAN = 30.0


def a10k_gain(pos):
    return 10 ** (A10K_DB_SPAN * (pos - .5) / 20)


# ---- composición original y reproducible (bajo, melodía, bombo y platillo); el motivo dura 7 s
t = np.arange(SR * DURATION) / SR
beat = .4375
rng = np.random.default_rng(2048)
high = signal.sosfilt(signal.butter(3, 4500, fs=SR, btype="high", output="sos"), rng.normal(0, 1, len(t)))
x = np.zeros(len(t))
notes = [82.4069, 98, 110, 73.4162]
for onset in np.arange(0, DURATION, beat):
    age = t - onset
    mask = (age >= 0) & (age < beat)
    k = int(round(onset / beat))
    f = notes[(k // 4) % 4]
    a = age[mask]
    bass = (np.sin(2 * np.pi * f * a) + .2 * np.sin(2 * np.pi * 2 * f * a)) * np.exp(-a * 4) * (1 - np.exp(-a * 180))
    melody = (np.sin(2 * np.pi * f * 8 * a) + .28 * np.sin(2 * np.pi * f * 12 * a)) * np.exp(-a * 9) * (1 - np.exp(-a * 250))
    kick = np.sin(2 * np.pi * (48 * a + 4 * (1 - np.exp(-a * 25)))) * np.exp(-a * 20)
    x[mask] += .34 * bass + .18 * melody + (.22 * kick if k % 2 == 0 else 0)
for onset in np.arange(0, DURATION, beat / 2):
    age = t - onset
    mask = (age >= 0) & (age < .12)
    x[mask] += .13 * high[mask] * np.exp(-age[mask] * 42)
x = x / max(abs(x)) * V_IN

# ---- filtrado por ventanas con la respuesta de la posición instantánea del potenciómetro.
# NIVEL (RV1) multiplica la señal ANTES de los filtros: escala los cinco nodos, es decir,
# el audio Y lo que miden la pantalla y los detectores de banda.
f, tt, Z = signal.stft(x, fs=SR, nperseg=NSEG, noverlap=NOV, boundary="zeros")
interp = np.empty((3, len(POS), len(NODES), len(f)), complex)
for b in range(3):
    for p in range(len(POS)):
        for k in range(len(NODES)):
            interp[b, p, k] = np.interp(f, freq, H[b, p, k].real) + 1j * np.interp(f, freq, H[b, p, k].imag)
            interp[b, p, k, 0] = 0
Y = np.empty((len(NODES),) + Z.shape, complex)
for j, tj in enumerate(tt):
    values, active = state(float(tj))
    band = active - 1 if active in (1, 2, 3) else 0
    p = values[band + 1] * 10
    lo = min(9, int(p))
    u = p - lo
    Y[:, :, j] = (interp[band, lo] * (1 - u) + interp[band, lo + 1] * u) * Z[:, j] * a10k_gain(values[0])
node = {}
for k, n in enumerate(NODES):
    _, y = signal.istft(Y[k], fs=SR, nperseg=NSEG, noverlap=NOV, boundary=True)
    node[n] = y[:len(x)]

# ---- WAV: una sola ganancia para todo el clip (no se normaliza por tramos).
# VOLUMEN (RV5) va de LINEA a AMP_IN, DESPUÉS del punto de medida: cambia solo lo que suena.
grid = np.arange(0, DURATION + .01, .005)
vol = np.interp(t, grid, [a10k_gain(state(float(g))[0][4]) for g in grid])
y = node["LINEA"] * vol
gain = .87 / max(abs(y))
fade = np.minimum(1, t / .12) * np.minimum(1, (DURATION - t) / .6)
audio = y * gain * fade
wavfile.write(OUT / "demo-audio.wav", SR, np.round(audio * 32767).astype(np.int16))
wavfile.write(OUT / "demo-entrada.wav", SR, np.round(x / V_IN * .7 * 32767).astype(np.int16))

# ---- lo que vería el ESP32: bloque de 1024 muestras a 20 kS/s y tres detectores de pico
FS_ADC, N_ADC = 20000, 1024
adc = signal.resample_poly(node["ADC_FFT_RAW"], 5, 12)          # 48 kHz → 20 kHz
tau = 220e3 * 100e-9                                            # R27-R29 con C22-C24
decay = np.exp(-1 / (SR * tau))
peaks = []
for n in ("G_W", "M_W", "A_W"):
    env = np.empty(len(x))
    v = 0.0
    for i, s in enumerate(np.abs(node[n])):
        v = s if s > v else v * decay
        env[i] = v
    peaks.append(env * 1000)                                    # mV respecto a VREF
VREF = 1.65
rows = []
with open(WORK / "tft-entrada.bin", "wb") as fh:
    for frame in range(FRAMES):
        tf = frame / FPS
        end = min(len(adc), max(N_ADC, int(round(tf * FS_ADC))))
        block = (VREF + adc[end - N_ADC:end]).astype("<f4")
        i = min(len(x) - 1, int(round(tf * SR)))
        mv = np.array([p[i] for p in peaks], dtype="<f4")       # lectura instantánea, como el firmware
        fh.write(np.array([view(tf)], dtype="<i4").tobytes() + mv.tobytes() + block.tobytes())
        values, active = state(tf)
        rows.append({"time": tf, "pots": values, "active": active, "view": view(tf), "band_mV": [float(v) for v in mv]})
(OUT / "demo-timeline.json").write_text(json.dumps(rows, separators=(",", ":")))

checks = []
for band, fx in enumerate((100, 1000, 8000)):
    lo = abs(np.interp(fx, freq, H[band, 0, 0].real) + 1j * np.interp(fx, freq, H[band, 0, 0].imag))
    hi = abs(np.interp(fx, freq, H[band, 10, 0].real) + 1j * np.interp(fx, freq, H[band, 10, 0].imag))
    delta = float(20 * np.log10(hi / lo))
    assert delta > 6, (band, delta)
    checks.append({"band": band, "control": f"RV{band + 2} B10K rotativo", "frequency_Hz": fx, "max_vs_min_dB": delta})


# ---- efecto de NIVEL y VOLUMEN: RMS en la meseta del mínimo (t0+1..1,95) y del máximo (t0+3,95..4,9)
def seg_db(sig, start, t0, t1):
    seg = sig[round((start + t0) * SR):round((start + t1) * SR)]
    return float(10 * np.log10(np.mean(seg ** 2) + 1e-20))


a10k_tests = []
for ref, name, start in (("RV1", "NIVEL", SWEEP_START[0]), ("RV5", "VOLUMEN", SWEEP_START[4])):
    d_audio = seg_db(audio, start, 3.95, 4.9) - seg_db(audio, start, 1.0, 1.95)
    d_adc = seg_db(node["ADC_FFT_RAW"], start, 3.95, 4.9) - seg_db(node["ADC_FFT_RAW"], start, 1.0, 1.95)
    a10k_tests.append({"control": f"{ref} {name} A10K log PENDIENTE DE COMPRA", "sweep_start_s": start,
                       "audio_max_vs_min_dB": round(d_audio, 2), "adc_node_max_vs_min_dB": round(d_adc, 2)})
assert a10k_tests[0]["audio_max_vs_min_dB"] > 20 and a10k_tests[0]["adc_node_max_vs_min_dB"] > 20       # NIVEL mueve audio y medidores
assert a10k_tests[1]["audio_max_vs_min_dB"] > 20 and abs(a10k_tests[1]["adc_node_max_vs_min_dB"]) < 6   # VOLUMEN no mueve los medidores
assert a10k_tests[1]["audio_max_vs_min_dB"] - a10k_tests[1]["adc_node_max_vs_min_dB"] > 20

report = {"method": "SPICE AC (macromodelo LM324) + interpolación STFT cuasiestática", "duration_s": DURATION, "sample_rate": SR, "samples": len(audio),
          "input_peak_V": V_IN, "peak": float(max(abs(audio))), "clipped_samples": int(np.sum(abs(audio) >= 1)), "single_playback_gain": float(gain),
          "adc_fft_raw_peak_V": float(max(abs(node["ADC_FFT_RAW"]))), "band_detector_peak_mV": [float(p.max()) for p in peaks],
          "rotary_control_tests": checks, "a10k_control_tests": a10k_tests,
          "a10k_gain_law": "SUPUESTA (A10K no comprados ni medidos): dB-lineal, 30 dB de recorrido, aplicada como ±15 dB respecto al punto RV1 = RV5 = 0,5 del banco SPICE",
          "spice_bank": spice_bank, "band_start_s": list(BAND_START), "sweep_start_s": list(SWEEP_START),
          "source": "composición procedimental original", "hardware_recording": False, "human_listening": False,
          "circuit_sha256": hashlib.sha256((ROOT / "herramientas/circuito.py").read_bytes()).hexdigest()}
(OUT / "validacion-audio.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False))

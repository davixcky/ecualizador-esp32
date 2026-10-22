#!/usr/bin/env python3
"""Simulación SPICE (ngspice) de la cadena analógica completa del ecualizador.

La netlist se arma desde circuito.py, de modo que se simula exactamente el circuito del
esquemático y de la PCB. Cada caso escribe su netlist en ../simulacion/ (se puede abrir en
ngspice o en LTspice y repetir a mano), la corre con `ngspice -b`, lee los datos con `wrdata`
y compara el resultado con el criterio de diseño. Imprime la tabla de resultados en Markdown
(../simulacion/resultados.md) y dibuja ../img/sim-*.png.

Supuestos del modelo:
- MCP6004: macromodelo propio (../simulacion/mcp6004.lib) con ganancia de 100 dB, producto
  ganancia-ancho de banda de 1 MHz, rapidez de cambio de 0,6 V/µs y salida riel a riel limitada
  a 20 mV de cada riel, que son los datos típicos de la hoja de datos de Microchip.
- 1N4148: modelo estándar de diodo de pequeña señal.
- Los potenciómetros son dos resistencias; la posición 1 es el cursor en el extremo 1 (máximo).
- La entrada del ADC del ESP32 se modela como 10 MΩ; el módulo PAM8403 como 20 kΩ.
"""
import math
import os
import re
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import circuito as cto  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.join(AQUI, "..", "simulacion")
IMG = os.path.join(AQUI, "..", "img")

OPAMP_LIB = """* Macromodelo riel a riel tipo MCP6004 (Microchip): A0 = 100 dB, GBW = 1 MHz,
* SR = 0,6 V/us, salida limitada a 20 mV de los rieles, Iq = 100 uA.
* Pines: entrada +, entrada -, V+, V-, salida.
.subckt MCP6004 inp inn vdd vss out
Rq vdd vss 33k
Emid mid 0 vdd vss 0.5
* Etapa de transconductancia con corriente limitada (fija la rapidez de cambio)
Bgm mid n1 I=0.0954*tanh((V(inp)-V(inn))/0.0954)
R1 n1 mid 1e5
C1 n1 mid 159.2n
* Recortadores del nodo interno: evitan que el integrador se sature lejos de los rieles
Dh n1 vdd DCL
Dl vss n1 DCL
Bo o1 0 V=min(max(V(n1), V(vss)+0.02), V(vdd)-0.02)
Ro o1 out 25
.model DCL D(IS=1e-12 N=1)
.ends
"""
MODELOS = ".model D1N4148 D(IS=2.52n RS=0.568 N=1.752 CJO=4p M=0.4 TT=20n BV=100 IBV=100u)\n"

VREF = 1.65
ADC_MAX = 2.45        # límite superior de la zona lineal del ADC con 11 dB de atenuación
ADC_MIN = 0.15


def valor_spice(v):
    v = v.split()[0]
    m = re.fullmatch(r"(\d+)([pnumkM])(\d+)", v)       # 4n7, 2k7, 5k6
    if m:
        v = f"{m.group(1)}.{m.group(3)}{m.group(2)}"
    return v.replace("M", "Meg")


def valor_num(v):
    s = valor_spice(v)
    mult = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3, "Meg": 1e6}
    for k, f in mult.items():
        if s.endswith(k):
            return float(s[:-len(k)]) * f
    return float(s)


def nodo(red):
    return "0" if red == "GND" else red.replace("+", "P").replace(".", "_")


def netlist(pots=None, fuente="AC 1", extra=""):
    """Netlist del circuito. pots = {ref: posición 0..1}; fuente = señal de la entrada J1."""
    pots = pots or {}
    lineas = [".include mcp6004.lib", "V5 P5V 0 5", "V33 P3V3 0 3.3"]
    for p in cto.PIEZAS:
        ref, t, n = p["ref"], p["tipo"], {k: nodo(v) for k, v in p["pines"].items() if v}
        if t == "R" and ref not in ("R30", "R31", "R32"):
            lineas.append(f"{ref} {n['1']} {n['2']} {valor_spice(p['valor'])}")
        elif t in ("C", "CP") and ref not in ("C25", "C26"):
            lineas.append(f"{ref} {n['1']} {n['2']} {valor_spice(p['valor'])}")
        elif t == "POT":
            total = valor_num(p["valor"])
            a = min(max(pots.get(ref, 0.5), 1e-4), 1 - 1e-4)
            lineas.append(f"{ref}a {n['1']} {n['2']} {total * (1 - a):.6g}")
            lineas.append(f"{ref}b {n['2']} {n['3']} {total * a:.6g}")
        elif t == "D":
            lineas.append(f"{ref} {n['2']} {n['1']} D1N4148")
        elif t == "OPAMP":
            for letra, (pm, pn, po) in cto.PINES_UNIDAD.items():
                lineas.append(f"X{ref}{letra} {n[pm]} {n[pn]} {n['4']} {n['11']} {n[po]} MCP6004")
    lineas += [f"VIN IN_L 0 {fuente}", "Rin_r IN_R IN_L 1m",
               "Ramp AMP_IN 0 20k"] + [f"Radc_{a} {a} 0 10Meg" for a in ("ADC_G", "ADC_M", "ADC_A", "ADC_FFT")]
    # El macromodelo recorta en los rieles, así que el punto de operación tiene soluciones
    # espurias con las salidas pegadas a 0 V. Se le indica a ngspice el reposo esperado.
    senal = sorted({nodo(r) for r in cto.redes() if r not in ("GND", "+5V", "+3V3", "+3.3VA", "IN_L", "IN_R", "MIX",
                                                               "NIVEL", "LINEA", "AMP_IN") and not r.startswith(("TFT", "LED"))
                    and r not in ("BTN", "DO_G", "DO_M", "DO_A")})
    lineas.append(".nodeset " + " ".join(f"v({x})={VREF}" for x in senal))
    return "\n".join(lineas) + "\n" + MODELOS + extra


def correr(nombre, cuerpo, analisis, columnas):
    os.makedirs(SIM, exist_ok=True)
    with open(os.path.join(SIM, "mcp6004.lib"), "w") as f:
        f.write(OPAMP_LIB)
    datos = f"{nombre}.dat"
    ruta = os.path.join(SIM, f"{nombre}.cir")
    with open(ruta, "w") as f:
        f.write(f"* {nombre} — ecualizador de tres bandas (generado por herramientas/simulacion.py)\n"
                f"{cuerpo}{analisis}\n.control\nset wr_singlescale\nset wr_vecnames\nrun\n"
                f"wrdata {datos} {' '.join(columnas)}\n.endc\n.end\n")
    r = subprocess.run(["ngspice", "-b", f"{nombre}.cir"], capture_output=True, text=True, cwd=SIM)
    if r.returncode != 0 or not os.path.exists(os.path.join(SIM, datos)):
        raise SystemExit(f"ngspice falló en {nombre}:\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    d = np.loadtxt(os.path.join(SIM, datos), skiprows=1)
    os.remove(os.path.join(SIM, datos))
    return d


def ac(nombre, pots, nodos):
    """Respuesta en frecuencia (dB respecto a la entrada J1) de los nodos pedidos."""
    cols = [f"vdb({nodo(x)})" for x in nodos]
    d = correr(nombre, netlist(pots), ".ac dec 60 10 40k", cols)
    # wrdata con escala única: frecuencia y una columna por vector
    return d[:, 0], {x: d[:, 1 + i] for i, x in enumerate(nodos)}


def corte(f, db, ref_db, tipo):
    """Frecuencia donde la curva cae 3 dB respecto a ref_db (interpolación logarítmica)."""
    obj = ref_db - 3
    idx = range(len(f) - 1) if tipo == "lp" else range(len(f) - 1, 0, -1)
    for i in idx:
        j = i + 1 if tipo == "lp" else i - 1
        if (db[i] - obj) * (db[j] - obj) <= 0 and db[i] != db[j]:
            t = (obj - db[i]) / (db[j] - db[i])
            return 10 ** (math.log10(f[i]) + t * (math.log10(f[j]) - math.log10(f[i])))
    return float("nan")


def en(f, y, fx):
    return float(np.interp(math.log10(fx), np.log10(f), y))


def tran(nombre, pots, fuente, nodos, t_fin=0.08, paso=2e-6, t_ini=0.0):
    cols = [f"v({nodo(x)})" for x in nodos]
    d = correr(nombre, netlist(pots, fuente), f".tran {paso} {t_fin} {t_ini} {paso}", cols)
    return d[:, 0], {x: d[:, 1 + i] for i, x in enumerate(nodos)}


def main():
    os.makedirs(IMG, exist_ok=True)
    filas = []

    def fila(caso, resultado, criterio, ok):
        if not isinstance(ok, str):
            ok = "Cumple" if bool(ok) else "**No cumple**"
        filas.append((caso, resultado.replace(".", ","), criterio, ok))

    # ------------------------------------------------ 1. punto de operación
    d = correr("op_reposo", netlist(), ".op", ["v(VREF)", "v(PRE)", "v(EQ_OUT)", "v(ADC_G)", "v(ADC_FFT)", "v(P3_3VA)"])
    # wrdata en .op: una fila con valores
    vref, vpre, veq, vadc_g, vfft, v3a = d[1:7]
    fila("VREF en reposo", f"{vref:.4f} V", "+3.3VA / 2 ± 0,5 %", abs(vref / (v3a / 2) - 1) < 0.005)
    fila("Salidas en reposo (PRE, EQ_OUT, ADC_FFT)", f"{vpre:.3f} V, {veq:.3f} V, {vfft:.3f} V",
         "VREF ± 10 mV", max(abs(vpre - vref), abs(veq - vref), abs(vfft - vref)) < 0.01)
    fila("Detector de graves sin señal (ADC_G)", f"{vadc_g:.3f} V", "VREF a VREF + 50 mV",
         -0.005 < vadc_g - vref < 0.05)
    fila("Alimentación analógica +3.3VA (4 × MCP6004)", f"{v3a:.3f} V", "≥ 3,25 V (caída en R1 < 50 mV)", v3a >= 3.25)

    # ------------------------------------------------ 2. respuesta en frecuencia de cada etapa
    nodos = ["NIVEL", "PRE", "GRAVES", "MED_HP", "MEDIOS", "AGUDOS", "EQ_OUT", "ADC_FFT"]
    f, db = ac("ac_plano", {"RV1": 1.0}, nodos)
    rel = {x: db[x] - db["PRE"] for x in nodos}            # filtros respecto a la salida del preamp
    g_pre = en(f, db["PRE"] - db["NIVEL"], 1000)
    fila("Ganancia del preamplificador a 1 kHz", f"{10 ** (g_pre / 20):.2f} ({g_pre:.2f} dB)",
         "3,2 ± 5 % (1 + 22k/10k)", abs(10 ** (g_pre / 20) - 3.2) < 0.16)
    disenos = [("Graves, pasa bajas", "GRAVES", "lp", 1 / (2 * math.pi * 10e3 * math.sqrt(100e-9 * 47e-9)), rel["GRAVES"]),
               ("Medios, pasa altas", "MED_HP", "hp", 1 / (2 * math.pi * 10e-9 * math.sqrt(27e3 * 56e3)),
                db["MED_HP"] - db["PRE"]),
               ("Medios, pasa bajas", "MEDIOS", "lp", 1 / (2 * math.pi * 10e3 * math.sqrt(10e-9 * 4.7e-9)),
                db["MEDIOS"] - db["MED_HP"]),
               ("Agudos, pasa altas", "AGUDOS", "hp", 1 / (2 * math.pi * 10e-9 * math.sqrt(2.7e3 * 5.6e3)), rel["AGUDOS"]),
               ("Antialiasing, pasa bajas", "ADC_FFT", "lp", 1 / (2 * math.pi * 10e3 * math.sqrt(4.7e-9 * 2.2e-9)),
                db["ADC_FFT"] - db["EQ_OUT"])]
    cortes = {}
    for nombre, n, tipo, fd, curva in disenos:
        fc = corte(f, curva, 0.0, tipo)
        cortes[n] = fc
        fila(f"Frecuencia de corte: {nombre.lower()}", f"{fc:.0f} Hz", f"{fd:.0f} Hz ± 10 %", abs(fc / fd - 1) < 0.10)
    aa = db["ADC_FFT"] - db["EQ_OUT"]
    fila("Antialiasing: atenuación a 15 kHz", f"{en(f, aa, 15000):.1f} dB", "≤ −15 dB (señal plegada sobre 5 kHz)",
         en(f, aa, 15000) <= -15)

    # suma plana con los tres deslizables en la mitad
    banda = (f >= 20) & (f <= 20000)
    plano = db["EQ_OUT"] - db["PRE"]
    rizado = plano[banda].max() - plano[banda].min()
    fila("Respuesta plana (deslizables al 50 %), 20 Hz–20 kHz", f"{plano[banda].min():+.2f} a {plano[banda].max():+.2f} dB "
         f"(rizado {rizado:.2f} dB)", "rizado ≤ 1,5 dB", rizado <= 1.5)

    # misma prueba con los valores de la Fase 1 (sin inversor de medios) para documentar el cambio
    cuerpo = netlist({"RV1": 1.0})
    fase1 = cuerpo
    for a, b in (("R11 MH1 MED_HP 27k", "R11 MH1 MED_HP 22k"), ("R12 MH2 VREF 56k", "R12 MH2 VREF 47k"),
                 ("C16 ML2 VREF 4.7n", "C16 ML2 VREF 5.6n"), ("R20 M_INV SUM_N 47k", "R20 M_W SUM_N 47k")):
        assert a in fase1, a
        fase1 = fase1.replace(a, b)
    d1 = correr("ac_fase1", fase1, ".ac dec 60 10 40k", ["vdb(EQ_OUT)", "vdb(PRE)"])
    plano1 = d1[:, 1] - d1[:, 2]
    fila("Valores de la Fase 1 (sin inversor), deslizables al 50 %",
         f"{plano1[banda].min():+.1f} a {plano1[banda].max():+.1f} dB (rizado {plano1[banda].max() - plano1[banda].min():.1f} dB)",
         "rizado ≤ 1,5 dB", "No cumple: motivó el rediseño")

    # familia de curvas al mover cada deslizable
    familias = {}
    for rv, nombre in (("RV2", "graves"), ("RV3", "medios"), ("RV4", "agudos")):
        familias[nombre] = []
        for pos in (0.0, 0.25, 0.5, 0.75, 1.0):
            pots = {"RV1": 1.0, rv: pos}
            fx, dbx = ac(f"ac_{nombre}_{int(pos * 100):03d}", pots, ["PRE", "EQ_OUT"])
            familias[nombre].append((pos, dbx["EQ_OUT"] - dbx["PRE"]))
    fcen = {"graves": 60, "medios": 1000, "agudos": 12000}
    for nombre, curvas in familias.items():
        mx = en(f, curvas[-1][1], fcen[nombre]) - en(f, curvas[2][1], fcen[nombre])
        mn = en(f, curvas[1][1], fcen[nombre]) - en(f, curvas[2][1], fcen[nombre])
        fila(f"Rango de ajuste de {nombre} en {fcen[nombre]} Hz", f"{mx:+.1f} dB al 100 %, {mn:+.1f} dB al 25 %",
             "≥ +5 dB y ≤ −5 dB respecto al 50 %", mx >= 5 and mn <= -5)

    # ------------------------------------------------ 3. detectores: selectividad
    amp_in = 0.15     # V de pico en J1 → ≈ 0,48 V de pico a la salida del preamplificador
    pots_max = {"RV1": 1.0, "RV2": 1.0, "RV3": 1.0, "RV4": 1.0}
    selec = {}
    for ftono, banda_esp in ((100, "G"), (1000, "M"), (8000, "A")):
        t, v = tran(f"tran_tono_{ftono}", pots_max, f"SIN(0 {amp_in} {ftono})",
                    ["ADC_G", "ADC_M", "ADC_A", "PRE", "EQ_OUT"], t_fin=0.08)
        m = t > 0.06
        selec[ftono] = {k: float(v[f"ADC_{k}"][m].mean() - vref) for k in "GMA"}
        selec[ftono]["PRE"] = float((v["PRE"][m].max() - v["PRE"][m].min()) / 2)
        orden = sorted("GMA", key=lambda k: -selec[ftono][k])
        otras = [selec[ftono][k] for k in "GMA" if k != banda_esp]
        relacion = selec[ftono][banda_esp] / max(max(otras), 1e-3)
        nombre = {"G": "graves", "M": "medios", "A": "agudos"}[banda_esp]
        fila(f"Selectividad: tono de {ftono} Hz", "G {G:.0f} mV · M {M:.0f} mV · A {A:.0f} mV".format(
            **{k: abs(1000 * selec[ftono][k]) for k in "GMA"}), f"solo sube la barra de {nombre} (≥ 4 veces las otras)",
            orden[0] == banda_esp and relacion >= 4)

    # ------------------------------------------------ 4. detector: linealidad a 1 kHz y respuesta temporal
    lin = []
    for a in (0.03, 0.06, 0.1, 0.15, 0.2, 0.25):
        t, v = tran(f"tran_lin_{int(a * 1000):03d}", pots_max, f"SIN(0 {a} 1000)", ["ADC_M", "M_W"], t_fin=0.06)
        m = t > 0.04
        pico = float(v["M_W"][m].max() - vref)
        det = float(v["ADC_M"][m].mean() - vref)
        lin.append((a, pico, det))
    err = max(abs(d_ / p_ - 1) for _, p_, d_ in lin if p_ > 0.1)
    fila("Detector de medios: linealidad entre 0,1 y 0,5 V de pico", f"error máximo {100 * err:.1f} %",
         "≤ 10 % (descarga entre picos incluida)", err <= 0.10)
    # paquete de tono: 1 kHz durante 40 ms y silencio, para ver el ataque y la descarga
    cuerpo = netlist(pots_max, "0").replace(
        "VIN IN_L 0 0", f"BIN IN_L 0 V={amp_in}*sin(6.283185307*1000*time)*(time<0.04)")
    d = correr("tran_ataque", cuerpo, ".tran 5u 0.1 0 5u", ["v(ADC_M)", "v(M_W)", "v(DO_M)"])
    t_at, adc_at, mw_at = d[:, 0], d[:, 1], d[:, 2]
    pico_final = adc_at[(t_at > 0.03) & (t_at < 0.04)].mean() - vref
    t90 = t_at[np.argmax(adc_at - vref >= 0.9 * pico_final)]
    caida = adc_at[np.argmin(abs(t_at - 0.062))] - vref
    fila("Detector: tiempo de ataque (90 %)", f"{1000 * t90:.2f} ms", "≤ 5 ms (sigue la música)", t90 <= 0.005)
    fila("Detector: descarga 22 ms después del silencio", f"{100 * caida / pico_final:.0f} % del pico",
         "≈ 37 % (τ = Rd·Ch = 22 ms)", abs(caida / pico_final - 0.37) < 0.08)

    # ------------------------------------------------ 5. margen del ADC con todo al máximo
    t, v = tran("tran_maximo", pots_max, "SIN(0 0.11 1000)", ["ADC_M", "EQ_OUT", "ADC_FFT", "PRE"], t_fin=0.05)
    m = t > 0.03
    fila("Entrada de 0,11 V de pico (máxima), deslizables al 100 %: ADC_M",
         f"{v['ADC_M'][m].max():.3f} V", "≤ 2,45 V (zona lineal del ADC)", v["ADC_M"][m].max() <= ADC_MAX)
    fila("Ídem: ADC_FFT", f"{v['ADC_FFT'][m].min():.3f} a {v['ADC_FFT'][m].max():.3f} V",
         "0,15 a 2,45 V", ADC_MIN <= v["ADC_FFT"][m].min() and v["ADC_FFT"][m].max() <= ADC_MAX)

    # Curva dedicada a la sustentación: ejes y leyenda legibles al proyectar.
    fig, ax = plt.subplots(figsize=(10, 4.1))
    linea_revisada, = ax.semilogx(f, plano, color="#A3161A", lw=2.8, label="Diseño revisado")
    ax.semilogx(d1[:, 0], plano1, color="#595959", lw=2.3, ls="--", label="Fase 1: sin inversión de medios")
    ax.axhspan(-1, 1, color="#C9A227", alpha=.10)
    ax.set(xlabel="Frecuencia (Hz)", ylabel="Ganancia respecto a PRE (dB)", xlim=(20, 20000), ylim=(-12, 3))
    ax.grid(True, which="both", alpha=.2)
    ax.legend(loc="lower left", frameon=False, fontsize=12)
    ax.tick_params(labelsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "sim-comparacion-fase.png"), dpi=180)
    linea_revisada.set_visible(False)
    fig.savefig(os.path.join(IMG, "sim-comparacion-fase-inicial.png"), dpi=180)
    plt.close(fig)

    # ------------------------------------------------ figuras
    estilo = {"GRAVES": ("#e4572e", "Graves (pasa bajas)"), "MEDIOS": ("#29a35a", "Medios (pasa banda)"),
              "AGUDOS": ("#2e86de", "Agudos (pasa altas)")}
    fig, ejes = plt.subplots(2, 2, figsize=(13, 8.5))
    ax = ejes[0][0]
    for n, (c, et) in estilo.items():
        ax.semilogx(f, rel[n], color=c, lw=2, label=et)
    ax.semilogx(f, plano, color="k", lw=2.2, label="Salida sumada (deslizables al 50 %)")
    ax.semilogx(f, aa, color="#8e44ad", lw=1.4, ls="--", label="Antialiasing hacia el ADC")
    ax.set(title="a) Respuesta de cada banda respecto a la salida del preamplificador", xlabel="Frecuencia (Hz)",
           ylabel="Ganancia (dB)", ylim=(-30, 10), xlim=(10, 40000))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="lower center")
    ax = ejes[0][1]
    ax.semilogx(f, plano, color="k", lw=2.2, label="Diseño final (medios invertidos, 409 Hz / 2,3 kHz)")
    ax.semilogx(d1[:, 0], plano1, color="#c0392b", lw=1.6, ls="--", label="Valores de la Fase 1 (sin inversor)")
    ax.set(title="b) Salida con los tres deslizables al 50 %", xlabel="Frecuencia (Hz)", ylabel="Ganancia (dB)",
           ylim=(-12, 12), xlim=(10, 40000))
    ax.axvspan(20, 20000, color="#f1c40f", alpha=0.08)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="lower center")
    ax = ejes[1][0]
    for (nombre, curvas), c in zip(familias.items(), ("#e4572e", "#29a35a", "#2e86de")):
        for pos, curva in curvas:
            ax.semilogx(f, curva, color=c, lw=1.0 + (pos == 1.0), alpha=0.35 + 0.65 * pos,
                        label=f"{nombre}" if pos == 1.0 else None)
    ax.set(title="c) Ecualización: cada deslizable en 0, 25, 50, 75 y 100 %", xlabel="Frecuencia (Hz)",
           ylabel="Ganancia (dB)", ylim=(-25, 15), xlim=(10, 40000))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, loc="lower center", ncol=3)
    ax = ejes[1][1]
    m = t_at < 0.1
    ax.plot(1000 * t_at[m], mw_at[m], color="#29a35a", lw=0.5, alpha=0.6, label="Cursor de medios (M_W)")
    ax.plot(1000 * t_at[m], adc_at[m], color="k", lw=2, label="Salida del detector (ADC_M → GPIO35)")
    ax.axhline(vref, color="gray", ls=":", lw=1)
    ax.axhline(ADC_MAX, color="#c0392b", ls="--", lw=1, label="Límite lineal del ADC (2,45 V)")
    ax.set(title="d) Detector de picos: paquete de 1 kHz de 40 ms", xlabel="Tiempo (ms)", ylabel="Tensión (V)",
           ylim=(0.9, 2.6))
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "sim-ecualizador.png"), dpi=130)
    plt.close(fig)

    fig, ejes = plt.subplots(1, 2, figsize=(13, 4.2))
    ax = ejes[0]
    x = np.arange(3)
    for i, (ftono, c) in enumerate(((100, "#e4572e"), (1000, "#29a35a"), (8000, "#2e86de"))):
        ax.bar(x + (i - 1) * 0.27, [1000 * selec[ftono][k] for k in "GMA"], 0.27, color=c,
               label=f"Tono de {ftono} Hz")
    ax.set_xticks(x, ["Barra de graves", "Barra de medios", "Barra de agudos"])
    ax.set(title="e) Selectividad: tensión de cada detector sobre VREF", ylabel="mV")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    ax = ejes[1]
    ax.plot([p for _, p, _ in lin], [d_ for _, _, d_ in lin], "o-", color="k", label="Simulado")
    lim = max(p for _, p, _ in lin) * 1.05
    ax.plot([0, lim], [0, lim], "--", color="gray", label="Ideal (salida = pico)")
    ax.set(title="f) Linealidad del detector de medios a 1 kHz", xlabel="Pico en el cursor M_W (V)",
           ylabel="ADC_M − VREF (V)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "sim-detectores.png"), dpi=130)
    plt.close(fig)

    # ------------------------------------------------ tabla
    tabla = ["| # | Caso | Resultado de la simulación | Criterio | Estado |", "|---:|---|---|---|---|"]
    for i, (a, b, c, e) in enumerate(filas, 1):
        tabla.append(f"| {i} | {a} | {b} | {c} | {e} |")
    texto = "\n".join(tabla)
    with open(os.path.join(SIM, "resultados.md"), "w") as fh:
        fh.write("# Resultados de la simulación (ngspice)\n\nGenerado por `herramientas/simulacion.py`.\n\n" + texto + "\n")
    print(texto)


if __name__ == "__main__":
    main()

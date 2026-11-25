"""Compare Falstad measurements with independently calculated transfer functions."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'simulacion/falstad'


def lp(f, r, cfb, cg):
    s = 2j*np.pi*np.asarray(f)
    return 1/(1 + s*2*r*cg + s*s*r*r*cfb*cg)


def hp(f, c, rfb, rg):
    s = 2j*np.pi*np.asarray(f)
    return s*s*c*c*rfb*rg/(1 + s*2*c*rfb + s*s*c*c*rfb*rg)


def bands(f):
    return np.array([lp(f, 1e4, 100e-9, 47e-9),
                     hp(f, 10e-9, 27000, 56000)*lp(f, 1e4, 10e-9, 4.7e-9),
                     hp(f, 10e-9, 2700, 5600)])


results = []
for case in json.loads((OUT/'muestras.json').read_text()):
    d = np.array(case['rows'])
    d = d[d[:, 0] > .025]
    t = d[:, 0]
    w = 2*np.pi*case['hz']
    x = np.array([np.ones(len(t)), np.sin(w*t), np.cos(w*t)]).T
    b = np.linalg.lstsq(x, d[:, 1:], rcond=None)[0]
    amp = np.hypot(b[1], b[2])
    measured = (b[1, 1:]+1j*b[2, 1:])/(b[1, 0]+1j*b[2, 0])
    expected = bands(case['hz'])
    rel = np.abs(measured/expected-1)
    dominant = {100:0, 1000:1, 8000:2}[case['hz']]
    result = dict(hz=case['hz'], amplitude_peak_v=amp[1:].tolist(),
                  gain=np.abs(measured).tolist(),
                  phase_degrees=np.angle(measured, deg=True).tolist(),
                  expected_gain=np.abs(expected).tolist(),
                  complex_relative_error=rel.tolist(),
                  pass_validation=bool(len(t)>100 and np.all(rel<.03)
                       and np.argmax(amp[1:])==dominant))
    results.append(result)
(OUT/'validacion.json').write_text(json.dumps(results, indent=2))
for r in results:
    print(r['hz'], 'Hz:', 'OK' if r['pass_validation'] else 'FAIL',
          'ganancias', [round(v, 4) for v in r['gain']])

f = np.geomspace(20, 20000, 1600)
h = bands(f)
colors = ['#de8131', '#329f69', '#28a6c0']
names = ['Graves', 'Medios', 'Agudos']
fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                       gridspec_kw={'height_ratios':[1.4, 1]})
for i in range(3):
    ax[0].semilogx(f, 20*np.log10(np.abs(h[i])), c=colors[i], label=names[i], lw=2)
    ax[1].semilogx(f, np.degrees(np.unwrap(np.angle(h[i]))), c=colors[i], lw=2)
for r in results:
    for i in range(3):
        ax[0].scatter(r['hz'], 20*np.log10(r['gain'][i]), color=colors[i], edgecolor='black', zorder=5)
for a in ax:
    a.grid(True, which='both', alpha=.2)
    for v in [100, 1000, 8000]: a.axvline(v, color='grey', ls=':', alpha=.4)
ax[0].set_ylim(-65, 4)
ax[0].set_ylabel('Ganancia respecto a PRE [dB]')
ax[0].legend(loc='lower center', ncol=3)
ax[1].set_ylabel('Fase [grados]')
ax[1].set_xlabel('Frecuencia [Hz]')
fig.suptitle('EQ / 03 — lo que deja pasar cada filtro\nCurvas: cálculo ideal · Puntos: tensiones medidas en Falstad', fontsize=14)
fig.tight_layout()
fig.savefig(OUT/'respuesta-filtros.png', dpi=180)
fig.savefig(OUT/'respuesta-filtros.pdf')
if not all(r['pass_validation'] for r in results):
    raise SystemExit('Falstad no coincide con el cálculo independiente.')

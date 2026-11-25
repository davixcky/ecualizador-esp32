"""Export the schematic's four Sallen-Key sections to CircuitJS/Falstad.

Native editable circuits, with a real 1.65 V reference and 0–3.3 V ideal
op-amp limits. This model does not include MCP6004 bandwidth/slew rate.
"""
from pathlib import Path
import json
from html import escape
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'simulacion/falstad'
OUT.mkdir(exist_ok=True)


def circuit(hz=1000, antialias=False):
    lines = ['$ 1 0.000001 50.0 50 5 50 0.000001']
    elements = []

    def e(kind, x1, y1, x2, y2, flags=0, extra=''):
        index = len(elements)
        if kind == 'c':
            extra += ' 0 0'
        line = f'{kind} {x1} {y1} {x2} {y2} {flags} {extra}'.rstrip()
        elements.append(line)
        lines.append(line)
        return index

    def wire(x1, y1, x2, y2):
        return e('w', x1, y1, x2, y2)

    def label(x, y, name, dx=-48):
        return e('207', x, y, x+dx, y, 0, name)

    def text(x, y, message):
        e('x', x, y, x+100, y, 0, '15 '+message)

    def section(x, y, mode, v1, v2, inp, out, title):
        # Positive input is y; negative input is y+32 (swap flag=1).
        label(x, y, inp)
        kind = 'r' if mode == 'lp' else 'c'
        val = v1 if mode == 'lp' else v2
        e(kind, x, y, x+96, y, 0, str(val))
        e(kind, x+96, y, x+192, y, 0, str(val))
        wire(x+192, y, x+256, y)
        amp = e('a', x+256, y+16, x+352, y+16, 1, '3.3 0 1000000 1.65 1.65 100000')
        wire(x+256, y+32, x+256, y+80)
        wire(x+256, y+80, x+352, y+80)
        wire(x+352, y+80, x+352, y+16)
        wire(x+96, y, x+96, y-64)
        e('c' if mode == 'lp' else 'r', x+96, y-64, x+352, y-64, 0, str(v2 if mode == 'lp' else v1))
        wire(x+352, y-64, x+352, y+16)
        e('c' if mode == 'lp' else 'r', x+192, y, x+192, y+80, 0, str(v2*.47 if mode == 'lp' else v1*56/27))
        label(x+192, y+80, 'VREF', 48)
        label(x+352, y+16, out, 64)
        text(x, y-96, title)
        # A differential probe plots the audio relative to VREF, whereas an
        # op-amp's default scope value is its tiny differential input voltage.
        wire(x+352, y+16, x+432, y+16)
        probe = e('p', x+432, y+16, x+432, y+80)
        label(x+432, y+80, 'VREF', 48)
        return probe

    text(48, 24, 'EQ03 / Sallen-Key / modelo ideal, limites 0 a 3.3 V')
    source = e('v', 64, 224, 64, 128, 0, f'1 {hz} 0.1 1.65 0 0.5')
    e('g', 64, 224, 64, 240)
    label(64, 128, 'PRE', 48)
    e('v', 64, 464, 64, 368, 0, '0 40 1.65 0 0 0.5')
    e('g', 64, 464, 64, 480)
    label(64, 368, 'VREF', 64)
    text(32, 272, f'PRE: {hz} Hz / 200 mVpp / offset 1.65 V')
    scopes = [('PRE', source)]
    if antialias:
        # C21 is 2.2 nF, not exactly 0.47*C20.
        amp = section(224, 160, 'lp', 10000, 4.7e-9, 'PRE', 'ADC_FFT', 'U2D: previo al ADC / R25 R26 C20 C21')
        # Replace the rounded ratio with the actual schematic value.
        lines = [s.replace('2.209e-09', '2.2e-09') for s in lines]
        scopes.append(('ADC_FFT', amp))
    else:
        scopes.append(('GRAVES', section(224, 160, 'lp', 10000, 100e-9, 'PRE', 'GRAVES', 'GRAVES / U1C / 10k + 100n / 47n')))
        section(224, 384, 'hp', 27000, 10e-9, 'PRE', 'MED_HP', 'MEDIOS PA / U1D / 10n + 27k / 56k')
        scopes.append(('MEDIOS', section(752, 384, 'lp', 10000, 10e-9, 'MED_HP', 'MEDIOS', 'MEDIOS PB / U2A / 10k + 10n / 4n7')))
        scopes.append(('AGUDOS', section(224, 608, 'hp', 2700, 10e-9, 'PRE', 'AGUDOS', 'AGUDOS / U2B / 10n + 2k7 / 5k6')))
    text(736, 112, 'Misma senoidal PRE en las tres ramas')
    text(736, 144, 'VREF centra el audio; no es GND')
    text(736, 176, 'Abajo: trazas AC; comparar amplitud y fase')
    speed = {100:256, 1000:32, 8000:4}.get(hz, 32)
    # Per-plot flag 1 gives AC coupling, without removing the circuit offset.
    for position, (name, index) in enumerate(scopes):
        lines.append(f'o {index} {speed} 0 283394 0.125 0.1 {position} 1 1 {name}')
    return '\n'.join(lines)+'\n'


cases = []
for hz in (100, 1000, 8000):
    name = f'filtros-{hz}Hz.txt'
    data = circuit(hz)
    (OUT/name).write_text(data)
    cases.append(dict(name=name, hz=hz, url='https://www.falstad.com/circuit/circuitjs.html?ctz='+''))
    cases[-1]['url'] = 'https://www.falstad.com/circuit/circuitjs.html?cct='+quote(data, safe='')
data = circuit(1000, antialias=True)
(OUT/'antialias-1000Hz.txt').write_text(data)
(OUT/'casos.json').write_text(json.dumps(cases, indent=2))
links=''.join(f'<li><a target="_blank" rel="noopener" href="{escape(c["url"],quote=True)}">{c["hz"]} Hz — {band}</a> · <a href="{c["name"]}">archivo editable</a></li>' for c,band in zip(cases,['graves','medios','agudos']))
(OUT/'index.html').write_text('''<!doctype html><html lang="es"><meta charset="utf-8"><title>EQ / 03 — Falstad</title>
<style>body{font:18px/1.6 system-ui;max-width:850px;margin:50px auto;padding:24px;color:#20252b}a{color:#9b2226}li{margin:16px 0}img{width:100%}</style>
<h1>Escucha la idea, observa el filtro</h1><p>La misma senoidal entra en las tres ramas. Cambian la amplitud y la fase; la frecuencia se conserva.</p><ul>'''+links+'''</ul><p>PRE: 200 mVpp, offset 1,65 V. Operacionales ideales con límites de salida 0–3,3 V. Las trazas se comparan respecto a VREF.</p><p><a href="respuesta-filtros.pdf">Curvas de amplitud y fase</a> · <a href="antialias-1000Hz.txt">Filtro previo al ADC</a> · <a href="http://localhost:3080/editor/?esp32sim=qemu">ESP32 + TFT en Docker local</a></p><img src="respuesta-filtros.png" alt="Respuesta de graves, medios y agudos y puntos medidos en Falstad"></html>''')
print('Falstad: tres bancos de filtros y un filtro previo al ADC.')

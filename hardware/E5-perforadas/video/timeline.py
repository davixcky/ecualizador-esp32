"""Reloj único del video E.5: controles, audio, pantalla, tapa y cámara.

Sin dependencias: lo importan el generador de audio, el de pantalla, Blender y la validación.
Los cinco controles son potenciómetros ROTATIVOS y los cinco se mueven en el video:
RV2-RV4 (bandas) son B10K comprados; RV1 (NIVEL) y RV5 (VOLUMEN) son A10K logarítmicos
PENDIENTES DE COMPRA. La posición 0..1 es la fracción de recorrido del cursor, igual que
en la netlist SPICE.
"""
FPS = 24
DURATION = 64
FRAMES = FPS * DURATION
# RV1 NIVEL, RV2 GRAVES, RV3 MEDIOS, RV4 AGUDOS, RV5 VOLUMEN: siete segundos cada uno.
SWEEP_START = (7.0, 14.0, 21.0, 28.0, 38.0)
BAND_START = SWEEP_START[1:4]       # compatibilidad: los tres B10K de banda
BAND_LEN = SWEEP_LEN = 7.0
# Centro → mínimo → máximo → centro.
KEYS = [(0, .5), (.9, 0), (2, 0), (3.8, 1), (5, 1), (6.5, .5), (7, .5)]
BUTTON_T = 35.6                     # pulsación de SW1: la pantalla pasa de BANDAS a ESPECTRO
LID = [(0, 0), (45.0, 0), (48.0, 100.0), (58.0, 100.0), (61.0, 0), (DURATION, 0)]   # grados
SECTIONS = [
    (0.0, 4.0, "PRODUCTO CERRADO · GABINETE E.5 DE TARJETAS PERFORADAS"),
    (4.0, 7.0, "CINCO CONTROLES ROTATIVOS · NIVEL Y VOLUMEN (A10K) PENDIENTES DE COMPRA"),
    (7.0, 35.0, None),               # rótulo dinámico: NIVEL y las tres bandas
    (35.0, 38.0, "PULSADOR VISTA · ESPECTRO EN LA PANTALLA ESP32-3248S035 DE 3,5\" · LED FIJOS"),
    (38.0, 45.0, None),              # rótulo dinámico: VOLUMEN
    (45.0, 48.0, "TAPA CON CIERRE DE IMANES · SIN BISAGRAS"),
    (48.0, 52.0, "CUATRO TARJETAS PERFORADAS · ARNESES XH · BUS ESTRELLA +5 V / GND"),
    (52.0, 55.0, "T2: LM324, PAM8403 Y SALIDA · DOS PARLANTES DE 8 Ω EN LA TAPA"),
    (55.0, 58.0, "T4: ESP32 DEVKIT V1 30P PENDIENTE DE COMPRA · 74HCT245 · DATOS POR ESP-NOW"),
    (58.0, 64.0, "MODELO DE DISEÑO · NO SUSTITUYE PRUEBAS ELÉCTRICAS NI MECÁNICAS"),
]
NAMES = ("NIVEL", "GRAVES", "MEDIOS", "AGUDOS", "VOLUMEN")


def smooth(u):
    return u * u * (3 - 2 * u)


def piecewise(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            return a + (b - a) * smooth((t - ta) / (tb - ta)) if tb > ta else b
    return keys[-1][1]


def state(t):
    """Posición 0..1 de RV1..RV5 y control activo (índice 0..4, o None)."""
    values = [.5] * 5
    active = next((i for i, s in enumerate(SWEEP_START) if s <= t < s + SWEEP_LEN), None)
    if active is not None:
        values[active] = piecewise(KEYS, t - SWEEP_START[active])
    return values, active


def lid_angle(t):
    return piecewise(LID, t)


def view(t):
    """0 = BANDAS, 1 = ESPECTRO (índices de interfaz::Vista)."""
    return 1 if t >= BUTTON_T else 0


def button_press(t):
    """Carrera del capuchón de SW1 en mm (negativa = hundido)."""
    d = t - BUTTON_T
    return -1.2 * max(0.0, 1 - abs(d) / .18) if abs(d) < .18 else 0.0


def caption(t):
    values, active = state(t)
    if active is not None:
        pct = round(values[active] * 100)
        if active == 0:
            return f"NIVEL · A10K PENDIENTE DE COMPRA · {pct} % DEL RECORRIDO\\NCAMBIA LO QUE SUENA Y LO QUE MIDE LA PANTALLA"
        if active == 4:
            return f"VOLUMEN · A10K PENDIENTE DE COMPRA · {pct} % DEL RECORRIDO\\NCAMBIA LO QUE SUENA, NO LO QUE MIDE LA PANTALLA"
        return f"{NAMES[active]} · B10K ROTATIVO · {pct} % DEL RECORRIDO"
    for a, b, text in SECTIONS:
        if a <= t < b:
            return text or "LOS CINCO CONTROLES AL 50 %"
    return SECTIONS[-1][2]

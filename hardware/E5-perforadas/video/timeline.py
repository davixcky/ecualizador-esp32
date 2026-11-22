"""Reloj único del video E.5: controles, audio, pantalla, tapa y cámara.

Sin dependencias: lo importan el generador de audio, el de pantalla, Blender y la validación.
Los tres controles de banda son potenciómetros ROTATIVOS B10K (RV2-RV4); la posición 0..1
es la fracción de recorrido del cursor, igual que en la netlist SPICE.
"""
FPS = 24
DURATION = 50
FRAMES = FPS * DURATION
BAND_START = (7.0, 14.0, 21.0)      # graves, medios, agudos: siete segundos cada uno
BAND_LEN = 7.0
# Centro → mínimo → máximo → centro.
KEYS = [(0, .5), (.9, 0), (2, 0), (3.8, 1), (5, 1), (6.5, .5), (7, .5)]
BUTTON_T = 28.6                     # pulsación de SW1: la pantalla pasa de BANDAS a ESPECTRO
LID = [(0, 0), (31.0, 0), (34.0, 100.0), (44.0, 100.0), (47.0, 0), (DURATION, 0)]   # grados
SECTIONS = [
    (0.0, 4.0, "PRODUCTO CERRADO · GABINETE E.5 DE TARJETAS PERFORADAS"),
    (4.0, 7.0, "CINCO CONTROLES ROTATIVOS · NIVEL Y VOLUMEN (A10K) PENDIENTES DE COMPRA"),
    (7.0, 28.0, None),               # rótulo dinámico: banda y porcentaje de recorrido
    (28.0, 31.0, "PULSADOR VISTA · ESPECTRO EN LA PANTALLA T4-S3 · LED FIJOS POR BANDA"),
    (31.0, 34.0, "TAPA CON CIERRE DE IMANES · SIN BISAGRAS"),
    (34.0, 38.0, "CUATRO TARJETAS PERFORADAS · ARNESES XH · BUS ESTRELLA +5 V / GND"),
    (38.0, 41.0, "T2: LM324, PAM8403 Y SALIDA · DOS PARLANTES DE 8 Ω EN LA TAPA"),
    (41.0, 44.0, "T4: ESP32S V1.1 USB-C, 74HCT245 Y ENLACE UART A LA PANTALLA (PROPUESTO)"),
    (44.0, 50.0, "MODELO DE DISEÑO · NO SUSTITUYE PRUEBAS ELÉCTRICAS NI MECÁNICAS"),
]
NAMES = ("GRAVES", "MEDIOS", "AGUDOS")


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
    """Posición 0..1 de RV2, RV3, RV4 y banda activa (o None)."""
    values = [.5, .5, .5]
    active = next((i for i, s in enumerate(BAND_START) if s <= t < s + BAND_LEN), None)
    if active is not None:
        values[active] = piecewise(KEYS, t - BAND_START[active])
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
        return f"{NAMES[active]} · B10K ROTATIVO · {round(values[active] * 100)} % DEL RECORRIDO"
    for a, b, text in SECTIONS:
        if a <= t < b:
            return text or "LOS TRES CONTROLES DE BANDA AL 50 %"
    return SECTIONS[-1][2]

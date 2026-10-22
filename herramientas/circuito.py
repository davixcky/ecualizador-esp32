"""Descripción única del circuito del ecualizador: piezas, valores, huellas y redes.

De este archivo salen la simulación (simulacion.py), el esquemático (generar_esquematico.py),
la PCB (generar_pcb.py) y la lista de materiales. Si se cambia un valor aquí, se regeneran
los tres y no quedan desalineados.

Redes de alimentación: +5V (USB del DevKitC), +3V3 (regulador del DevKitC), +3.3VA (+3V3
filtrada para los amplificadores operacionales) y GND. VREF = 1,65 V es la tierra de señal.
"""

# ---------------------------------------------------------------- huellas
H_R = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
H_C = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
H_CF = "Capacitor_THT:C_Rect_L7.2mm_W3.0mm_P5.00mm_FKS2_FKP2_MKS2_MKP2"
H_CP5 = "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
H_CP6 = "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"
H_CP8 = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
H_D = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
H_DIP = "Package_DIP:DIP-14_W7.62mm_Socket"
H_POT = "Potentiometer_THT:Potentiometer_Alps_RK09K_Single_Vertical"
H_SLIDE = "Potentiometer_THT:Potentiometer_Bourns_PTA3043_Single_Slide"
H_JACK = "Connector_Audio:Jack_3.5mm_CUI_SJ1-3523N_Horizontal"
H_TFT = "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical"
H_AMP = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
H_SW = "Button_Switch_THT:SW_PUSH_6mm_H5mm"
H_ESP = "Ecualizador:ESP32-DevKitC-38_Zocalo"

# ---------------------------------------------------------------- piezas
# (referencia, tipo, valor, {pin: red}, huella, función)
PIEZAS = []


def parte(ref, tipo, valor, pines, huella, funcion):
    PIEZAS.append(dict(ref=ref, tipo=tipo, valor=valor, pines=pines, huella=huella, funcion=funcion))


def R(ref, valor, a, b, funcion, huella=H_R):
    parte(ref, "R", valor, {"1": a, "2": b}, huella, funcion)


def C(ref, valor, a, b, funcion, huella=H_C):
    parte(ref, "C", valor, {"1": a, "2": b}, huella, funcion)


def CP(ref, valor, pos, neg, funcion, huella=H_CP5):
    parte(ref, "CP", valor, {"1": pos, "2": neg}, huella, funcion)


def POT(ref, valor, extremo1, cursor, extremo3, funcion, huella=H_POT):
    parte(ref, "POT", valor, {"1": extremo1, "2": cursor, "3": extremo3}, huella, funcion)


# Unidades de los MCP6004 (pines de DIP-14): (+, −, salida)
PINES_UNIDAD = {"A": ("3", "2", "1"), "B": ("5", "6", "7"), "C": ("10", "9", "8"), "D": ("12", "13", "14")}
UNIDADES = {}   # "U1A": (+, −, salida, función)


def AO(unidad, mas, menos, salida, funcion):
    UNIDADES[unidad] = (mas, menos, salida, funcion)


# --- alimentación
R("R1", "10", "+3V3", "+3.3VA", "Filtro RC de la alimentación analógica (con C1)")
CP("C1", "100u 10V", "+3.3VA", "GND", "Filtro de la alimentación analógica", H_CP6)
C("C2", "100n", "+3.3VA", "GND", "Desacople de alta frecuencia de +3.3VA")
CP("C3", "470u 10V", "+5V", "GND", "Reserva de 5 V para el amplificador de potencia", H_CP8)
for i, u in enumerate(("U1", "U2", "U3", "U4")):
    C(f"C{4 + i}", "100n", "+3.3VA", "GND", f"Desacople de {u}")

# --- referencia de señal
R("R2", "10k 1%", "+3.3VA", "VDIV", "Divisor de VREF")
R("R3", "10k 1%", "VDIV", "GND", "Divisor de VREF")
CP("C8", "10u 16V", "VDIV", "GND", "Filtro del divisor de VREF")
AO("U1A", "VDIV", "VREF", "VREF", "Seguidor de VREF = 1,65 V")

# --- entrada de línea y preamplificador
parte("J1", "JACK", "Entrada de línea 3,5 mm", {"T": "IN_L", "R": "IN_R", "S": "GND"}, H_JACK,
      "Entrada estéreo (celular o PC)")
R("R4", "10k", "IN_L", "MIX", "Mezcla del canal izquierdo a mono")
R("R5", "10k", "IN_R", "MIX", "Mezcla del canal derecho a mono")
POT("RV1", "10k log", "MIX", "NIVEL", "GND", "Nivel de entrada")
C("C9", "1u film", "NIVEL", "PRE_IN", "Acople de entrada", H_CF)
R("R6", "100k", "PRE_IN", "VREF", "Polarización de la entrada en VREF")
AO("U1B", "PRE_IN", "PRE_FB", "PRE", "Preamplificador no inversor, G = 3,2")
R("R7", "22k 1%", "PRE_FB", "PRE", "Realimentación del preamplificador")
R("R8", "10k 1%", "PRE_FB", "PRE_G", "Resistencia de ganancia del preamplificador")
CP("C10", "10u 16V", "PRE_G", "VREF", "Ganancia unitaria en continua")

# --- graves: Sallen-Key pasa bajas, fc = 232 Hz
R("R9", "10k 1%", "PRE", "LB1", "Pasa bajas de graves")
R("R10", "10k 1%", "LB1", "LB2", "Pasa bajas de graves")
C("C11", "100n film", "LB1", "GRAVES", "Pasa bajas de graves (realimentación)", H_CF)
C("C12", "47n film", "LB2", "VREF", "Pasa bajas de graves", H_CF)
AO("U1C", "LB2", "GRAVES", "GRAVES", "Pasa bajas Sallen-Key de graves")

# --- medios: pasa altas 409 Hz + pasa bajas 2,3 kHz
C("C13", "10n film", "PRE", "MH1", "Pasa altas de medios", H_CF)
C("C14", "10n film", "MH1", "MH2", "Pasa altas de medios", H_CF)
R("R11", "27k 1%", "MH1", "MED_HP", "Pasa altas de medios (realimentación)")
R("R12", "56k 1%", "MH2", "VREF", "Pasa altas de medios")
AO("U1D", "MH2", "MED_HP", "MED_HP", "Pasa altas Sallen-Key de medios")
R("R13", "10k 1%", "MED_HP", "ML1", "Pasa bajas de medios")
R("R14", "10k 1%", "ML1", "ML2", "Pasa bajas de medios")
C("C15", "10n film", "ML1", "MEDIOS", "Pasa bajas de medios (realimentación)", H_CF)
C("C16", "4n7 film", "ML2", "VREF", "Pasa bajas de medios", H_CF)
AO("U2A", "ML2", "MEDIOS", "MEDIOS", "Pasa bajas Sallen-Key de medios")

# --- agudos: Sallen-Key pasa altas, fc = 4,1 kHz
C("C17", "10n film", "PRE", "AH1", "Pasa altas de agudos", H_CF)
C("C18", "10n film", "AH1", "AH2", "Pasa altas de agudos", H_CF)
R("R15", "2k7 1%", "AH1", "AGUDOS", "Pasa altas de agudos (realimentación)")
R("R16", "5k6 1%", "AH2", "VREF", "Pasa altas de agudos")
AO("U2B", "AH2", "AGUDOS", "AGUDOS", "Pasa altas Sallen-Key de agudos")

# --- ganancia por banda (deslizables)
POT("RV2", "10k lin", "GRAVES", "G_W", "VREF", "Ganancia de graves", H_SLIDE)
POT("RV3", "10k lin", "MEDIOS", "M_W", "VREF", "Ganancia de medios", H_SLIDE)
POT("RV4", "10k lin", "AGUDOS", "A_W", "VREF", "Ganancia de agudos", H_SLIDE)

# --- inversor de medios y sumador
R("R17", "47k 1%", "M_W", "INV_N", "Entrada del inversor de medios")
R("R18", "47k 1%", "INV_N", "M_INV", "Realimentación del inversor de medios")
AO("U4C", "VREF", "INV_N", "M_INV", "Inversor de medios (corrige la fase en los cruces)")
R("R19", "47k 1%", "G_W", "SUM_N", "Entrada de graves al sumador")
R("R20", "47k 1%", "M_INV", "SUM_N", "Entrada de medios al sumador")
R("R21", "47k 1%", "A_W", "SUM_N", "Entrada de agudos al sumador")
R("R22", "100k 1%", "SUM_N", "EQ_OUT", "Realimentación del sumador")
AO("U2C", "VREF", "SUM_N", "EQ_OUT", "Sumador inversor")

# --- salida de audio
CP("C19", "10u 16V", "EQ_OUT", "OUT_AC", "Acople de salida")
R("R23", "100", "OUT_AC", "LINEA", "Protección de la salida contra cortocircuito")
R("R24", "47k", "LINEA", "GND", "Descarga de C19")
parte("J2", "JACK", "Salida de línea 3,5 mm", {"T": "LINEA", "R": "LINEA", "S": "GND"}, H_JACK,
      "Salida para audífonos activos o parlante con amplificador")
POT("RV5", "10k log", "LINEA", "AMP_IN", "GND", "Volumen del parlante")
parte("J3", "CONN4", "PAM8403", {"1": "+5V", "2": "GND", "3": "AMP_IN", "4": "GND"}, H_AMP,
      "Módulo amplificador PAM8403 (+5V, GND, entrada, GND)")

# --- filtro antialiasing hacia el ADC (espectro)
R("R25", "10k 1%", "EQ_OUT", "AA1", "Antialiasing")
R("R26", "10k 1%", "AA1", "AA2", "Antialiasing")
C("C20", "4n7 film", "AA1", "ADC_FFT", "Antialiasing (realimentación)", H_CF)
C("C21", "2n2 film", "AA2", "VREF", "Antialiasing", H_CF)
AO("U2D", "AA2", "ADC_FFT", "ADC_FFT", "Pasa bajas Sallen-Key antialiasing, fc = 4,95 kHz")

# --- detectores de pico de precisión
for banda, cursor, d, ch, rd, det, seg in (("graves", "G_W", "D1", "C22", "R27", "U3A", "U3B"),
                                            ("medios", "M_W", "D2", "C23", "R28", "U3C", "U3D"),
                                            ("agudos", "A_W", "D3", "C24", "R29", "U4A", "U4B")):
    k = banda[0].upper()
    AO(det, cursor, f"DET_{k}", f"DO_{k}", f"Detector de picos de {banda}")
    parte(d, "D", "1N4148", {"1": f"DET_{k}", "2": f"DO_{k}"}, H_D, f"Diodo del detector de {banda}")
    C(ch, "100n film", f"DET_{k}", "VREF", f"Retención del detector de {banda}", H_CF)
    R(rd, "220k", f"DET_{k}", "VREF", f"Descarga del detector de {banda} (τ = 22 ms)")
    AO(seg, f"DET_{k}", f"ADC_{k}", f"ADC_{k}", f"Seguidor del detector de {banda}")

# --- amplificador libre de U4 (entradas a VREF, salida en seguidor)
AO("U4D", "VREF", "U4D_OUT", "U4D_OUT", "Unidad libre: seguidor de VREF (reserva)")

# --- pantalla y pulsador
# J4 es un adaptador de paso 2,54 mm; el cable GH1.25 se conecta por nombre.
parte("J4", "TFT", 'Waveshare 1.9 ST7789V2',
      {"1": "+3V3", "2": "GND", "3": "TFT_MOSI", "4": "TFT_SCK", "5": "TFT_CS",
       "6": "TFT_DC", "7": "TFT_RST", "8": "TFT_BL"}, H_TFT,
      "Cable adaptador: VCC GND DIN CLK CS DC RST BL; no insertar el módulo directamente")
R("R30", "10k", "TFT_BL", "GND", "Apaga la retroiluminación durante el arranque")
# LED: fuente externa común de 5 V; la corriente de la tira no atraviesa el DevKit.
parte("J5", "CONN3", "NeoPixel 5V DIN GND", {"1": "+5V", "2": "LED_DIN", "3": "GND"},
      "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "Salida hacia 12 LED WS2812B")
parte("J6", "CONN2", "Entrada 5V 3A", {"1": "+5V", "2": "GND"},
      "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal", "Fuente regulada externa; desconectar VBUS USB")
parte("U6", "BUFFER", "74AHCT125", {"1":"GND", "2":"LED_DATA", "3":"LED_5V",
      "4":"+5V", "5":"GND", "6":None, "7":"GND", "8":None, "9":"GND", "10":"+5V",
      "11":None, "12":"GND", "13":"+5V", "14":"+5V"}, H_DIP, "Adaptador lógico 3,3 a 5 V; no sustituir por HC")
R("R31", "330", "LED_5V", "LED_DIN", "Serie de datos; junto al conector de la tira")
R("R32", "10k", "LED_DATA", "GND", "Mantiene DIN bajo durante reset")
C("C25", "100n", "+5V", "GND", "Desacople del 74AHCT125")
CP("C26", "1000u 10V", "+5V", "GND", "Reserva para los LED", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm")
parte("SW1", "SW", "Pulsador", {"1": "BTN", "2": "GND"}, H_SW, "Cambia la vista de la pantalla")

# --- ESP32-DevKitC V4 (38 pines). Lado izquierdo: pines 1–19; lado derecho: 20–38.
IZQ = ["3V3", "EN", "VP/IO36", "VN/IO39", "IO34", "IO35", "IO32", "IO33", "IO25",
       "IO26", "IO27", "IO14", "IO12", "GND", "IO13", "SD2/IO9", "SD3/IO10", "CMD/IO11", "5V"]
DER = ["GND", "IO23", "IO22", "TXD0/IO1", "RXD0/IO3", "IO21", "GND", "IO19", "IO18", "IO5",
       "IO17", "IO16", "IO4", "IO0", "IO2", "IO15", "SD1/IO8", "SD0/IO7", "CLK/IO6"]
ESP_REDES = {"3V3": "+3V3", "VP/IO36": "VREF", "IO34": "ADC_G", "IO35": "ADC_M", "IO32": "ADC_A",
             "IO33": "ADC_FFT", "IO27": "BTN", "5V": "+5V", "IO23": "TFT_MOSI", "IO22": "TFT_RST",
             "IO21": "TFT_DC", "IO19": "TFT_BL", "IO25": "LED_DATA", "IO18": "TFT_SCK", "IO5": "TFT_CS"}
_pines_esp = {}
for k, n in enumerate(IZQ + DER):
    _pines_esp[str(k + 1)] = "GND" if n == "GND" else ESP_REDES.get(n)
parte("U5", "ESP32", "ESP32-DevKitC V4", _pines_esp, H_ESP, "Microcontrolador: ADC1, FFT, pantalla y Wi-Fi")

# Los amplificadores operacionales como piezas DIP-14
for u in ("U1", "U2", "U3", "U4"):
    pines = {"4": "+3.3VA", "11": "GND"}
    for letra, (pm, pn, po) in PINES_UNIDAD.items():
        mas, menos, sal, _ = UNIDADES[u + letra]
        pines.update({pm: mas, pn: menos, po: sal})
    parte(u, "OPAMP", "MCP6004", pines, H_DIP, "Cuatro amplificadores operacionales riel a riel")

# Material que no va en la placa (para la lista de materiales)
FUERA = [
    ("—", "Tira WS2812B de 10 mm, 60 LED/m: dos tramos de 100 mm (12 LED)", 1, "Iluminación del gabinete"),
    ("—", "Módulo amplificador PAM8403 (2 × 3 W, 5 V)", 1, "Amplificador del parlante (se conecta a J3)"),
    ("—", "Parlante de 3 W, 4 Ω, 40–50 mm", 1, "Salida de sonido del gabinete"),
    ("—", "Waveshare 1,9 pulgadas 170 × 320 SPI ST7789V2", 1, "Visualización mediante cable adaptador en J4"),
    ("—", "Perillas para potenciómetro de eje D y tapas para deslizable", 5, "Panel"),
    ("—", "Fuente regulada de 5 V, 3 A y cable USB sin VBUS", 1, "Alimentación"),
    ("—", "Cable de audio 3,5 mm macho-macho", 1, "Entrada desde el celular o el PC"),
]


def redes():
    """{red: [(referencia, pin), ...]} de todas las piezas."""
    out = {}
    for p in PIEZAS:
        for pin, red in p["pines"].items():
            if red:
                out.setdefault(red, []).append((p["ref"], pin))
    return out


def pieza(ref):
    return next(p for p in PIEZAS if p["ref"] == ref)


if __name__ == "__main__":
    for red, nodos in sorted(redes().items()):
        if len(nodos) < 2:
            print("¡Red con un solo nodo!", red, nodos)
    print(len(PIEZAS), "piezas,", len(redes()), "redes")

# D.1: terminales de panel y patas adaptadas a PCB de una cara.
# El inventario original de huellas permanece en hardware/una-cara/componentes-base.json.
from pathlib import Path as _Path
import json as _json
_una_cara = _Path(__file__).resolve().parents[1] / 'hardware/una-cara/huellas.json'
if _una_cara.exists():
    _huellas = _json.loads(_una_cara.read_text())
    for _pieza in PIEZAS:
        _pieza['huella'] = _huellas.get(_pieza['ref'], _pieza['huella'])

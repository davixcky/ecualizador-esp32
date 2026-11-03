"""Single board E.2: same circuit, more single-sided freedom.

Levers (all electrically equivalent):
  * resistors and diodes on 10.16 mm leads, ceramic 100n on 7.5 mm leads -> two/one tracks pass under each part
  * op-amp sections reassigned freely among U1..U4, buffers among U6 gates
  * ESP32 GPIOs reassigned inside their allowed sets (firmware config.h regenerated)
  * cable headers (pots, jacks, PAM8403, NeoPixel, button, TFT) take any pin order
"""
import os, sys, json
HERR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, HERR)
import pcbnew as k
from pcbnew import FromMM as MM, ToMM, VECTOR2I
import verificar_netlist, pcb_freerouting as pf, pcb_legado_b1 as base, motor_freerouting as motor

W, H = 200.0, 120.0
HOLES = [(4, 4), (196, 4), (4, 116), (196, 116)]
CER = {'C2', 'C4', 'C5', 'C6', 'C7', 'C25'}

_orig = verificar_netlist.netlist_kicad
def netlist_base():
    """Original netlist with the earlier U2D<->U4C exchange (antialias on U4D, inverter on U2D)."""
    pn, st = _orig(); pn = dict(pn)
    u2d = {p: pn[('U2', p)] for p in ('12', '13', '14')}
    u4c = {p: pn[('U4', p)] for p in ('8', '9', '10')}
    pn[('U4', '12')], pn[('U4', '13')], pn[('U4', '14')] = u2d['12'], u2d['13'], u2d['14']
    pn[('U2', '12')], pn[('U2', '13')], pn[('U2', '14')] = u4c['10'], u4c['9'], u4c['8']
    pn[('U4', '10')] = '/VREF'; pn[('U4', '9')] = 'Net-(U4C-out)'; pn[('U4', '8')] = 'Net-(U4C-out)'
    return pn, st

# ---------------- swap classes: each member is a tuple of (ref, pad); members of a class exchange nets
SEC = {'A': ('1', '2', '3'), 'B': ('7', '6', '5'), 'C': ('8', '9', '10'), 'D': ('14', '13', '12')}   # out, -, +
OPAMP = [tuple((u, p) for p in SEC[s]) for u in ('U1', 'U2', 'U3', 'U4') for s in 'ABCD']
BUF = [tuple(('U6', p) for p in t) for t in (('1', '2', '3'), ('4', '5', '6'), ('10', '9', '8'), ('13', '12', '11'))]  # OE, A, Y
# DevKitC V4 pad -> GPIO
GPIO = {3: 36, 4: 39, 5: 34, 6: 35, 7: 32, 8: 33, 9: 25, 10: 26, 11: 27, 12: 14, 13: 12, 15: 13,
        21: 23, 22: 22, 25: 21, 27: 19, 28: 18, 29: 5, 30: 17, 31: 16, 32: 4, 33: 0, 34: 2, 35: 15}
ADC_PADS = [3, 4, 5, 6, 7, 8]                     # ADC1 only (ADC2 dies with Wi-Fi)
DIG_PADS = [9, 10, 11, 12, 15, 22, 25, 27, 29, 32]  # no strapping 0/2/12/15, no 16/17 (PSRAM on WROVER); 18/23 stay (VSPI IOMUX)
HEADERS = ['RV1', 'RV2', 'RV3', 'RV4', 'RV5', 'J1', 'J2', 'J3', 'J5', 'SW1', 'J4']

def clases(pads_de):
    """pads_de(ref) -> list of pad numbers of that footprint."""
    c = [OPAMP, BUF, [(('U5', str(p)),) for p in ADC_PADS], [(('U5', str(p)),) for p in DIG_PADS]]
    for r in HEADERS:
        c.append([((r, p),) for p in pads_de(r)])
    return c

_overrides = {}
def netlist_actual():
    pn, st = netlist_base()
    for (r, p), n in _overrides.items():
        if n is None: pn.pop((r, p), None)
        else: pn[(r, p)] = n
    return pn, st

def _huella(h):
    nombre = h.split(':')[-1]
    ref = nombre.replace('UnaCara_', '')
    if ref[0] == 'R' and ref[1].isdigit():
        return base.cargar_huella('Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal')
    if ref[0] == 'D' and ref[1].isdigit():
        return base.cargar_huella('Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal')
    if ref in CER:
        return base.cargar_huella('Capacitor_THT:C_Rect_L10.0mm_W2.5mm_P7.50mm_MKS4')
    return _cargar(h)
_cargar = base.cargar_huella
pf.netlist_kicad = netlist_actual
pf.base.cargar_huella = _huella

def construir(overrides=None):
    _overrides.clear(); _overrides.update(overrides or {})
    os.environ.pop('GRUPO', None)
    b = pf.construir()
    for f in list(b.GetFootprints()):
        if f.GetReference().startswith('H') and 'Mounting' in f.GetFPID().GetLibItemName().wx_str(): b.Remove(f)
    for d in list(b.GetDrawings()):
        if d.GetLayer() == k.Edge_Cuts: b.Remove(d)
    return b

def colocar(b, col):
    for f in b.GetFootprints():
        q = col['partes'][f.GetReference()]
        f.SetOrientationDegrees(q['rot']); f.SetPosition(VECTOR2I(MM(q['x']), MM(q['y'])))
        f.Reference().SetPosition(f.GetPosition() + VECTOR2I(MM(1), MM(-2)))
    for xy in HOLES: base.agujero(b, *xy)
    base.linea(b, k.Edge_Cuts, [(0, 0), (W, 0), (W, H), (0, H), (0, 0)], .1)
    t = b.GetTitleBlock(); t.SetTitle('Ecualizador - PCB CNC de una cara (placa única)'); t.SetRevision('E.2'); t.SetCompany('CUC')

def overrides_de(col):
    return {(r, p): n for r, p, n in col['pines']}

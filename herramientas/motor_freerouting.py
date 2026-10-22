"""Ruteo de una cara; adaptado del flujo de medidor-energia-esp32 del mismo repositorio de trabajo."""
import os,re
import pcbnew
from pcbnew import FromMM as MM,ToMM,VECTOR2I
W,H=200.0,120.0
SEP=1.1
BORDE=1.5
COSTO_VIA=int(os.environ.get('VIA_COST',400))
COSTO_PUENTE=float(os.environ.get('JUMPER_COST',20))

def agrandar_pads(fp):
    """Pads de al menos 2 mm (ovalados en filas de 2,54 mm) sin romper la separación."""
    pads = list(fp.Pads())
    pos = [(ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)) for p in pads]
    for p, (x, y) in zip(pads, pos):
        if p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH:
            continue
        dx = min([abs(x - a) for a, b in pos if abs(y - b) < 0.1 and abs(x - a) > 0.1] or [99])
        dy = min([abs(y - b) for a, b in pos if abs(x - a) < 0.1 and abs(y - b) > 0.1] or [99])
        s = p.GetSize(pcbnew.F_Cu)
        sx, sy = ToMM(s.x), ToMM(s.y)
        tx = min(max(sx, 2.0), dx - SEP - 0.04)
        ty = min(max(sy, 2.0), dy - SEP - 0.04)
        if dy < 3 and dx >= 5:
            tx = max(tx, 2.4)
        if dx < 3 and dy >= 5:
            ty = max(ty, 2.4)
        # No se achica por debajo de la biblioteca salvo que haga falta para la separación mínima.
        tx = max(tx, min(sx, dx - SEP - 0.04))
        ty = max(ty, min(sy, dy - SEP - 0.04))
        if abs(tx - ty) > 0.01 and p.GetShape(pcbnew.F_Cu) == pcbnew.PAD_SHAPE_CIRCLE:
            p.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_OVAL)
        p.SetSize(pcbnew.F_Cu, VECTOR2I(MM(tx), MM(ty)))

def bloques(texto, cabeza):
    """(inicio, fin) de cada bloque «(cabeza ...» con paréntesis balanceados."""
    out, i = [], 0
    while True:
        i = texto.find("(" + cabeza, i)
        if i < 0:
            return out
        prof, j = 0, i
        while True:
            if texto[j] == "(":
                prof += 1
            elif texto[j] == ")":
                prof -= 1
                if prof == 0:
                    break
            j += 1
        out.append((i, j + 1))
        i = j + 1

def preparar_dsn(texto):
    """Una sola cara: los pads existen solo en B.Cu; F.Cu queda como capa de puentes."""
    piezas, ult = [], 0
    for a, z in bloques(texto, "padstack "):
        bloque = texto[a:z]
        if "Via[" not in bloque:
            for sa, sz in reversed(bloques(bloque, "shape (")):
                if "F.Cu" in bloque[sa:sz]:
                    bloque = bloque[:sa] + bloque[sz:]
        piezas += [texto[ult:a], bloque]
        ult = z
    piezas.append(texto[ult:])
    texto = "".join(piezas)
    e = BORDE * 1000
    caja = "(path pcb 0  %d %d  %d %d  %d %d  %d %d  %d %d)" % (
        W * 1000 - e, -H * 1000 + e, e, -H * 1000 + e, e, -e, W * 1000 - e, -e, W * 1000 - e, -H * 1000 + e)
    texto = re.sub(r"\(boundary\s*\(path pcb 0[^)]*\)", "(boundary\n      " + caja, texto, count=1)
    ajustes = """    (autoroute_settings
      (fanout off) (autoroute on) (postroute on) (vias on)
      (via_costs %d) (plane_via_costs 5) (start_ripup_costs 100)
      (layer_rule F.Cu (active on) (preferred_direction horizontal)
        (preferred_direction_trace_costs %g) (against_preferred_direction_trace_costs %g))
      (layer_rule B.Cu (active on) (preferred_direction vertical)
        (preferred_direction_trace_costs 1) (against_preferred_direction_trace_costs 1))
    )
""" % (COSTO_VIA, COSTO_PUENTE, COSTO_PUENTE)
    a, z = bloques(texto, "structure")[0]
    return texto[:z - 1] + ajustes + "  " + texto[z - 1:]

def hacer_puentes(b):
    """Cada grupo de tramos de F.Cu entre vías se convierte en un puente de alambre JPn."""
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    tramos = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu]
    # Un ramal puede tocar el interior de otro tramo o el anillo de una vía.
    # Unir solo extremos perdía esas conexiones al retirar F.Cu.
    from shapely.geometry import LineString, Point
    from shapely.strtree import STRtree
    items=tramos+vias
    shapes=[]
    for item in items:
        if item.Type()==pcbnew.PCB_VIA_T:
            p=item.GetPosition();shapes.append(Point(ToMM(p.x),ToMM(p.y)).buffer(ToMM(item.GetWidth(pcbnew.F_Cu))/2))
        else:
            a,end=item.GetStart(),item.GetEnd()
            shapes.append(LineString([(ToMM(a.x),ToMM(a.y)),(ToMM(end.x),ToMM(end.y))]).buffer(ToMM(item.GetWidth())/2))
    parent=list(range(len(items)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    tree=STRtree(shapes)
    for i,shape in enumerate(shapes):
        for j in tree.query(shape.buffer(.00001)):
            j=int(j)
            if items[i].GetNetCode()==items[j].GetNetCode() and shape.distance(shapes[j])<=.00001:
                parent[root(i)]=root(j)
    grupos={}
    for i,via in enumerate(vias,start=len(tramos)):
        p=via.GetPosition();key=(round(ToMM(p.x),3),round(ToMM(p.y),3))
        grupos.setdefault(root(i),{})[key]=via
    n = alambres = 0
    lista = []
    for vs in sorted(grupos.values(), key=lambda g: sorted(g)[0]):
        pts = sorted(vs)
        if len(pts) < 2:
            continue
        red = next(iter(vs.values())).GetNet()
        hechos, aristas = [0], []
        while len(hechos) < len(pts):
            _, i, j = min(((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2, i, j)
                          for i in hechos for j in range(len(pts)) if j not in hechos)
            hechos.append(j)
            aristas.append((pts[i], pts[j]))
        n += 1
        alambres += len(aristas)
        agregar_puente(b, f"JP{n}", red, pts, aristas)
        lista.append((f"JP{n}", red.GetNetname(), pts, aristas))
    for t in vias + tramos:
        b.Delete(t)
    print(f"puentes: {n} ({alambres} alambres)")
    return lista

def agregar_puente(b, ref, red, pts, aristas):
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference(ref)
    fp.SetValue("puente")
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
    fp.SetDuplicatePadNumbersAreJumpers(True)
    fp.SetFPID(pcbnew.LIB_ID("Ecualizador", "Puente_alambre"))
    b.Add(fp)
    fp.SetPosition(VECTOR2I(MM(pts[0][0]), MM(pts[0][1])))
    for x, y in pts:
        p = pcbnew.PAD(fp)
        p.SetNumber("1")
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        p.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
        p.SetSize(pcbnew.F_Cu, VECTOR2I(MM(2.0), MM(2.0)))
        p.SetDrillSize(VECTOR2I(MM(0.8), MM(0.8)))
        p.SetLayerSet(pcbnew.PAD.PTHMask())
        fp.Add(p)
        p.SetPosition(VECTOR2I(MM(x), MM(y)))
        p.SetNet(red)
    for p1, p2 in aristas:
        s = pcbnew.PCB_SHAPE(fp)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(VECTOR2I(MM(p1[0]), MM(p1[1])))
        s.SetEnd(VECTOR2I(MM(p2[0]), MM(p2[1])))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(MM(0.4))
        fp.Add(s)
    (x1, y1), (x2, y2) = aristas[0]
    fp.Reference().SetPosition(VECTOR2I(MM((x1 + x2) / 2), MM((y1 + y2) / 2 - 1.2)))
    fp.Reference().SetTextSize(VECTOR2I(MM(0.9), MM(0.9)))
    fp.Reference().SetTextThickness(MM(0.15))
    fp.Value().SetVisible(False)

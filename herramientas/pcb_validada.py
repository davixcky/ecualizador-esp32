#!/usr/bin/env python3
"""Reconstruye D.2 desde colocación y ruteo aprobados: B.Cu + puentes físicos."""
import json,subprocess
import pcbnew as k
from pcbnew import FromMM as MM,VECTOR2I
import pcb_freerouting as p
from montaje_puentes import cara,modelo

def vec(xy):return VECTOR2I(MM(xy[0]),MM(xy[1]))
def main():
 b=p.construir();data=json.loads((p.HW/'ruteo-validado.json').read_text())
 for t in data['pistas']:
  item=k.PCB_TRACK(b);item.SetStart(vec(t['a']));item.SetEnd(vec(t['b']));item.SetWidth(MM(t['ancho']));item.SetLayer(k.B_Cu);item.SetNet(b.FindNet(t['red']));b.Add(item)
 for j in data['puentes']:
  fp=k.FOOTPRINT(b);fp.SetReference(j['ref']);fp.SetValue('Puente a terminal' if j['terminal'] else 'Puente aislado');fp.SetAttributes(k.FP_THROUGH_HOLE|k.FP_BOARD_ONLY|k.FP_EXCLUDE_FROM_BOM);fp.SetDuplicatePadNumbersAreJumpers(True);b.Add(fp)
  for q in j['pads']:
   pad=k.PAD(fp);pad.SetNumber('1');pad.SetAttribute(k.PAD_ATTRIB_PTH);pad.SetShape(k.F_Cu,q['shape']);pad.SetSize(k.F_Cu,vec(q['size']));pad.SetDrillSize(vec(q['drill']));pad.SetDrillShape(q['drillshape']);pad.SetLayerSet(k.PAD.PTHMask());fp.Add(pad);pad.SetPosition(vec(q['xy']));pad.SetOrientationDegrees(q['angulo']);pad.SetNet(b.FindNet(j['red']))
  for a,c in j['alambres']:
   s=k.PCB_SHAPE(fp);s.SetShape(k.SHAPE_T_SEGMENT);s.SetStart(vec(a));s.SetEnd(vec(c));s.SetWidth(MM(.3));s.SetLayer(k.F_Fab if cara(j)=='superior' else k.B_Fab);fp.Add(s)
  modelo(j,p.HW/'3d/puentes');model=k.FP_3DMODEL();model.m_Filename='${KIPRJMOD}/3d/puentes/'+j['ref']+'.wrl';fp.Add3DModel(model)
  a,c=j['alambres'][0];fp.Reference().SetLayer(k.F_SilkS if cara(j)=='superior' else k.B_SilkS);fp.Reference().SetPosition(vec([a[0],a[1]-1.6]));fp.Reference().SetTextSize(vec([.8,.8]));fp.Reference().SetTextThickness(MM(.12));fp.Value().SetVisible(False)
 b.BuildConnectivity();p.relleno_gnd(b)
 path=p.HW/'ecualizador.kicad_pcb';b.Save(str(path));p.reglas(path.with_suffix('.kicad_pro'))
 subprocess.run(['kicad-cli','pcb','drc',str(path),'--refill-zones','--save-board','--schematic-parity','--severity-error','--exit-code-violations','--format','json','-o',str(p.HW/'drc.json')],check=True)
 print('D.2: solo B.Cu; 79 grupos de puentes, 80 alambres; DRC sin errores ni conexiones abiertas.')
if __name__=='__main__':main()

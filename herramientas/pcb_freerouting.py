#!/usr/bin/env python3
"""PCB CNC: colocación guardada, DSN a Freerouting y conversión de F.Cu en alambres."""
import os,sys,json,subprocess,shutil,re
from pathlib import Path
import pcbnew as k
from pcbnew import FromMM as MM,ToMM,VECTOR2I
import motor_freerouting as motor
import pcb_legado_b1 as base
from verificar_netlist import netlist_kicad
ROOT=Path(__file__).resolve().parents[1];HW=ROOT/'hardware';WORK=Path(os.environ.get('PCB_ROUTE_WORK',str(HW/'ruteo-trabajo')));WORK.mkdir(exist_ok=True)
POS=HW/'una-cara/colocacion.json';SES=HW/'ruteo-freerouting.ses'

def construir():
 import circuito
 placement=json.loads(POS.read_text());pinnets,stamps=netlist_kicad();b=k.BOARD();b.SetCopperLayerCount(2)
 ds=b.GetDesignSettings();ds.m_MinClearance=MM(1.1);ds.m_TrackMinWidth=MM(.9);ds.m_CopperEdgeClearance=MM(.5);ds.m_ViasMinSize=MM(2);ds.m_MinThroughDrill=MM(.8)
 nc=ds.m_NetSettings.GetDefaultNetclass();nc.SetTrackWidth(MM(.9));nc.SetClearance(MM(1.1));nc.SetViaDiameter(MM(2));nc.SetViaDrill(MM(.8))
 power=k.NETCLASS('Alimentacion');power.SetTrackWidth(MM(1.2));power.SetClearance(MM(1.1));power.SetViaDiameter(MM(2));power.SetViaDrill(MM(.8));ds.m_NetSettings.SetNetclass('Alimentacion',power)
 for name in ['GND','+5V','+3V3','+3.3VA']:ds.m_NetSettings.SetNetclassPatternAssignment(name,'Alimentacion')
 nets={}
 for name in sorted(set(pinnets.values())):
  n=k.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
 grupo=os.environ.get('GRUPO');G={}
 G['A']=set('R1 C1 C2 C3 C4 C5 R2 R3 C8 J1 R4 R5 RV1 C9 R6 R7 R8 C10 R9 R10 C12 C11 C13 C14 R12 R11 R13 R14 C16 C15 C17 C18 R16 R15 RV2 RV3 RV4 R17 R18 R19 R20 R21 R22 C19 R23 R24 J2 RV5 J3 U1 U2'.split())
 G['B']=set('C6 C7 R25 R26 C21 C20 D1 C22 R27 D2 C23 R28 D3 C24 R29 U3 U4'.split())
 G['C']=set('J4 R30 J5 J6 U6 R31 R32 C25 C26 SW1 U5'.split())
 if grupo:
  dentro=G[grupo];fuera=set(placement)-dentro
  netin={pinnets[k] for k in pinnets if k[0] in dentro};netout={pinnets[k] for k in pinnets if k[0] in fuera}
  cruce=sorted(n for n in netin&netout if not n.startswith('unconnected'))
  placement={r:c for r,c in placement.items() if r in dentro}
 for ref,c in placement.items():
  fp=base.cargar_huella(c['huella']);fp.SetReference(ref);fp.SetValue(circuito.pieza(ref)['valor']);fp.SetPath(k.KIID_PATH('/'+stamps[ref]));b.Add(fp)
  motor.agrandar_pads(fp)
  for pad in fp.Pads():
   name=pinnets.get((ref,pad.GetNumber()))
   if name:pad.SetNet(nets[name])
  fp.SetPosition(VECTOR2I(MM(c['xy'][0]),MM(c['xy'][1])));fp.SetOrientationDegrees(c['rot']);fp.Reference().SetVisible(True);fp.Value().SetVisible(False)
  fp.Reference().SetTextSize(VECTOR2I(MM(.9),MM(.9)));fp.Reference().SetTextThickness(MM(.15));fp.Reference().SetPosition(fp.GetPosition()+VECTOR2I(MM(1),MM(-2)))
 if grupo:
  # Conector entre placas: un pin por red compartida, ordenado por la altura media de sus pads.
  pads=[p for f in b.GetFootprints() for p in f.Pads()]
  def ymed(n):
   ys=[ToMM(p.GetPosition().y) for p in pads if p.GetNetname()==n];return sum(ys)/len(ys)
  def xs(n):return [ToMM(p.GetPosition().x) for p in pads if p.GetNetname()==n]
  cruce.sort(key=ymed)
  bb=[ToMM(v) for f in b.GetFootprints() for v in (f.GetBoundingBox(False).GetLeft(),f.GetBoundingBox(False).GetRight())]
  lado=os.environ.get('LADO','der');x=(max(bb)+6) if lado=='der' else (min(bb)-6)
  ys=[ymed(n) for n in cruce];y0=sum(ys)/len(ys)-(len(cruce)-1)*2.54/2
  hd=base.cargar_huella(f'Connector_PinHeader_2.54mm:PinHeader_1x{len(cruce):02d}_P2.54mm_Vertical');hd.SetReference('JX');b.Add(hd);motor.agrandar_pads(hd)
  for pad in hd.Pads():
   n=cruce[int(pad.GetNumber())-1];pad.SetNet(nets[n])
  hd.SetPosition(VECTOR2I(MM(x),MM(y0)))
  print('conector',grupo,len(cruce),cruce,'x=%.1f'%x,flush=True)
 for xy in [(4,4),(196,4),(4,116),(196,116)]:base.agujero(b,*xy)
 base.linea(b,k.Edge_Cuts,[(0,0),(200,0),(200,120),(0,120),(0,0)],.1)
 t=b.GetTitleBlock();t.SetTitle('Ecualizador - PCB CNC de una cara');t.SetRevision('D.2');t.SetCompany('CUC');t.SetDate('2026-10-22')
 return b

def reglas(path):
 pro=json.loads((HW/'ecualizador.kicad_pro').read_text());ds=pro['board']['design_settings'];ds['rules'].update(min_clearance=1.0,min_track_width=.9)
 ds['rule_severities'].update(lib_footprint_mismatch='ignore',pth_inside_courtyard='warning')
 pro['net_settings']['classes'][0].update(clearance=1.0,track_width=.9,via_diameter=2.0,via_drill=.8)
 for nc in pro['net_settings']['classes']:nc['clearance']=1.0
 path.write_text(json.dumps(pro,indent=2))

def relleno_gnd(b):
 z=k.ZONE(b);z.SetLayer(k.B_Cu);z.SetNet(b.FindNet('GND'))
 outline=z.Outline();outline.NewOutline()
 for x,y in [(1.5,1.5),(198.5,1.5),(198.5,118.5),(1.5,118.5)]:outline.Append(MM(x),MM(y))
 z.SetPadConnection(k.ZONE_CONNECTION_FULL);z.SetLocalClearance(MM(1.0));z.SetMinThickness(MM(.9));z.SetThermalReliefGap(MM(1.0));z.SetThermalReliefSpokeWidth(MM(1.0));z.SetIslandRemovalMode(k.ISLAND_REMOVAL_MODE_ALWAYS);b.Add(z)
 # Antena: extremo superior del ESP32, sin plano debajo.
 antenna=k.ZONE(b);antenna.SetIsRuleArea(True);antenna.SetLayer(k.B_Cu);antenna.SetDoNotAllowZoneFills(True)
 antenna.SetDoNotAllowTracks(False);antenna.SetDoNotAllowVias(False);antenna.SetDoNotAllowPads(False);antenna.SetDoNotAllowFootprints(False)
 outline=antenna.Outline();outline.NewOutline()
 for x,y in [(155.5,50.5),(184.1,50.5),(184.1,65.5),(155.5,65.5)]:outline.Append(MM(x),MM(y))
 b.Add(antenna)

def main():
 mode=sys.argv[1] if len(sys.argv)>1 else 'importar';b=construir()
 if mode=='colocar':
  b.Save(str(WORK/'colocacion.kicad_pcb'));reglas(WORK/'colocacion.kicad_pro');return
 if mode=='rutear':
  dsn=WORK/'ecualizador.dsn';k.ExportSpecctraDSN(b,str(dsn));dsn.write_text(motor.preparar_dsn(dsn.read_text()));ses=WORK/'ecualizador.ses'
  if ses.exists():ses.unlink()
  jar=os.environ.get('FREEROUTING_JAR',str(Path.home()/'.local/share/freerouting/freerouting.jar'))
  with (WORK/'freerouting.log').open('w') as log:
   subprocess.run(['java','-Xmx3G','-jar',jar,'-de',str(dsn),'-do',str(ses),'-mp',os.environ.get('FR_PASES','30'),'-mt','4','--gui.enabled=false','--router.automatic_neckdown='+os.environ.get('FR_NECKDOWN','false'),'--router.fanout.enabled='+os.environ.get('FR_FANOUT','true'),'--router.autorouter.algorithm='+os.environ.get('FR_ALGORITHM','freerouting-router'),'--router.optimizer.max_passes=8','--router.optimizer.max_threads=4'],stdout=log,stderr=subprocess.STDOUT,check=True)
   logtext=(WORK/'freerouting.log').read_text()
  completed=re.findall(r'final score:.*?\((\d+) unrouted and (\d+) violations\)',logtext)
  if completed and completed[-1] != ('0','0') and not os.environ.get('EXPERIMENTO'):
   raise RuntimeError(f'Ruteo rechazado: {completed[-1][0]} conexiones abiertas, {completed[-1][1]} violaciones. No se genera una placa entregable.')
 else:ses=SES
 if not k.ImportSpecctraSES(b,str(ses)):raise RuntimeError('No se pudo importar '+str(ses))
 bridges=motor.hacer_puentes(b)
 out=WORK/'resultado.kicad_pcb';b.Save(str(out));reglas(out.with_suffix('.kicad_pro'))
 (WORK/'puentes.json').write_text(json.dumps([dict(ref=ref,red=net,puntos=pts,alambres=edges) for ref,net,pts,edges in bridges],indent=2))
  # El informe de KiCad es el criterio final, incluso al importar una sesión guardada.
 report=WORK/'drc.json'
 subprocess.run(['kicad-cli','pcb','drc',str(out),'--format','json','--severity-error','--exit-code-violations','-o',str(report)],check=not os.environ.get('EXPERIMENTO'))
 assert not any(t.Type()==k.PCB_VIA_T or t.GetLayer()==k.F_Cu for t in b.GetTracks()), 'Quedó cobre superior o una vía'
 print(out,flush=True)
if __name__=='__main__':main()

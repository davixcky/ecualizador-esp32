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
 for ref,c in placement.items():
  fp=base.cargar_huella(c['huella']);fp.SetReference(ref);fp.SetValue(circuito.pieza(ref)['valor']);fp.SetPath(k.KIID_PATH('/'+stamps[ref]));b.Add(fp)
  motor.agrandar_pads(fp)
  for pad in fp.Pads():
   name=pinnets.get((ref,pad.GetNumber()))
   if name:pad.SetNet(nets[name])
  fp.SetPosition(VECTOR2I(MM(c['xy'][0]),MM(c['xy'][1])));fp.SetOrientationDegrees(c['rot']);fp.Reference().SetVisible(True);fp.Value().SetVisible(False)
  fp.Reference().SetTextSize(VECTOR2I(MM(.9),MM(.9)));fp.Reference().SetTextThickness(MM(.15));fp.Reference().SetPosition(fp.GetPosition()+VECTOR2I(MM(1),MM(-2)))
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
  if completed and completed[-1] != ('0','0'):
   raise RuntimeError(f'Ruteo rechazado: {completed[-1][0]} conexiones abiertas, {completed[-1][1]} violaciones. No se genera una placa entregable.')
 else:ses=SES
 if not k.ImportSpecctraSES(b,str(ses)):raise RuntimeError('No se pudo importar '+str(ses))
 bridges=motor.hacer_puentes(b)
 out=WORK/'resultado.kicad_pcb';b.Save(str(out));reglas(out.with_suffix('.kicad_pro'))
 (WORK/'puentes.json').write_text(json.dumps([dict(ref=ref,red=net,puntos=pts,alambres=edges) for ref,net,pts,edges in bridges],indent=2))
  # El informe de KiCad es el criterio final, incluso al importar una sesión guardada.
 report=WORK/'drc.json'
 subprocess.run(['kicad-cli','pcb','drc',str(out),'--format','json','--severity-error','--exit-code-violations','-o',str(report)],check=True)
 assert not any(t.Type()==k.PCB_VIA_T or t.GetLayer()==k.F_Cu for t in b.GetTracks()), 'Quedó cobre superior o una vía'
 print(out,flush=True)
if __name__=='__main__':main()

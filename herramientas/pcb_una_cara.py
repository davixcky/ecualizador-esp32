#!/usr/bin/env python3
"""PCB D.1: cobre inferior y cables aislados superiores.

Genera una propuesta separada; solo se promueve tras verificar geometría y conexiones.
Los controles del panel se representan por sus terminales de cable, no por huellas
incompatibles con la rejilla. El esquema conserva las referencias eléctricas.
"""
import json, math, heapq, sys, os
from pathlib import Path
import pcbnew as k
import pcb_legado_b1 as base
from verificar_netlist import netlist_kicad
from sexpr import parse, dump, find, find1, Sym
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'hardware/una-cara'; OUT.mkdir(exist_ok=True)
P=1.27; NX=149; NY=85; X0=(200-(NX-1)*P)/2; Y0=(120-(NY-1)*P)/2
mm=k.FromMM

def xy(q): return (X0+q[0]*P,Y0+q[1]*P)
def vec(p):return k.VECTOR2I(mm(p[0]),mm(p[1]))
def grid(p):return (round((k.ToMM(p.x)-X0)/P),round((k.ToMM(p.y)-Y0)/P))
def layers():
 return k.PAD.PTHMask()  # KiCad representa el agujero con anillos; no define otra cara de ruteo.

def bottom_layers():
 s=k.LSET();s.AddLayer(k.B_Cu);s.AddLayer(k.B_Mask);return s

def main():
 board=k.BOARD();board.GetDesignSettings().SetCopperLayerCount(2)
 title=board.GetTitleBlock();title.SetTitle('Ecualizador - PCB de una cara');title.SetRevision('D.1');title.SetCompany('CUC');title.SetDate('2026-10-22')
 pin_net,stamps=netlist_kicad();nets={}
 for name in sorted(set(pin_net.values())):
  n=k.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
 import circuito
 originals={p['ref']:p['huella'] for p in json.loads((OUT/'componentes-base.json').read_text())}
 parts=[dict(p,huella=originals[p['ref']]) for p in circuito.PIEZAS];fps={};panel={}
 for p in parts:
  ref=p['ref'];fp=base.cargar_huella(p['huella'])
  if ref.startswith('RV') or ref in ('J1','J2','SW1'):
   pins=list(p['pines']);fp=base.cargar_huella(f'Connector_PinHeader_2.54mm:PinHeader_1x{len(pins):02d}_P2.54mm_Vertical')
   for pad in fp.Pads():pad.SetNumber(pins[int(pad.GetNumber())-1])
   panel[ref]={'pines':p['pines'],'montaje':'En panel; cable a cabecera en placa'}
  if ref.startswith('U') and ref!='U5':
   model=k.FP_3DMODEL();model.m_Filename='${KICAD10_3DMODEL_DIR}/Package_DIP.3dshapes/DIP-14_W7.62mm.step';model.m_Offset=k.VECTOR3D(0,0,4.0);fp.Add3DModel(model)
  fp.SetReference(ref);fp.SetValue(p['valor']);fp.GetField(k.FIELD_T_DESCRIPTION).SetText(p['funcion']);fp.SetPath(k.KIID_PATH('/'+stamps[ref]));board.Add(fp);fps[ref]=fp
  for pad in fp.Pads():
   name=pin_net.get((ref,pad.GetNumber()))
   if name:pad.SetNet(nets[name])
  for field in (fp.Reference(),fp.Value()):field.SetVisible(False)
 # ESP32 a la derecha; módulos analógicos agrupados a la izquierda.
 fixed={'U5':(157,64,0),'J4':(103,9,0),'U6':(119,13,0),'J5':(190,32,0),'J6':(190,49,0),'J3':(190,65,0)}
 for i,ref in enumerate(['RV1','RV2','RV3','RV4','RV5','SW1','J1','J2']):fixed[ref]=(149+(i%2)*23,10+(i//2)*13,0)
 for ref,(x,y,rot) in fixed.items():base.mover(fps[ref],x,y,rot)
 groups=[((7,8,98,44),['U3','C6','D1','C22','R27','D2','C23','R28','U4','C7','D3','C24','R29','R17','R18']),
 ((7,48,100,59),['C3','R1','C1','C2','R30','R4','R5']),
 ((7,63,74,113),['U1','C4','R2','R3','C8','C9','R6','R7','R8','C10','R9','R10','C11','C12','C13','C14','R11','R12']),
 ((78,63,146,113),['U2','C5','R13','R14','C15','C16','C17','C18','R15','R16','R19','R20','R21','R22','R25','R26','C20','C21','C19','R23','R24']),
 ((111,39,143,58),['C25','R31','R32','C26'])]
 for region,refs in groups:
  if os.environ.get('PCB_LAYOUT','clusters')!='clusters':
   base.empaquetar([fps[r] for r in refs],region);continue
  x0,y0,x1,y1=region; boxes=[];placed_refs=[]
  for ref in refs:
   fp=fps[ref];best=None
   for rot in ([0] if ref.startswith('U') else [0,90]):
    base.mover(fp,0,0,rot);bx0,by0,bx1,by1=base.caja(fp);w,h=bx1-bx0,by1-by0
    for ix in range(int((x1-x0-w)/2)+1):
     for iy in range(int((y1-y0-h)/2)+1):
      x=x0+ix*2;y=y0+iy*2;box=(x,y,x+w,y+h)
      if any(not (box[2]+1<=o[0] or box[0]>=o[2]+1 or box[3]+1<=o[1] or box[1]>=o[3]+1) for o in boxes):continue
      cx,cy=x+w/2,y+h/2
      mine={p.GetNetname() for p in fp.Pads()}-{'GND','+3.3VA','VREF','+5V','+3V3'}
      related=[o for old,o in placed_refs if mine & {p.GetNetname() for p in fps[old].Pads()}]
      score=sum(abs(cx-(o[0]+o[2])/2)+abs(cy-(o[1]+o[3])/2) for o in related) if related else abs(cx-(x0+x1)/2)+abs(cy-(y0+y1)/2)
      score+=.02*(cy-y0)+.01*(cx-x0)
      candidate=(score,x-bx0,y-by0,rot,box)
      if best is None or candidate<best:best=candidate
   if best is None:raise ValueError(('Sin sitio en bloque',ref,region))
   _,x,y,rot,box=best;base.mover(fp,x,y,rot);boxes.append(box);placed_refs.append((ref,box))
 # Anclar pad 1 y adaptar solo patas flexibles de pasivos al agujero cercano.
 holes={};terminals={};adjusted=[]; placed=[]
 for ref in sorted(fps,key=lambda r:(r not in fixed,not r.startswith('U'),r)):
  fp=fps[ref]
  pad1=next((p for p in fp.Pads() if p.GetNumber()=='1'),next(iter(fp.Pads())))
  anchor=vec(xy(grid(pad1.GetPosition())));fp.Move(anchor-pad1.GetPosition())
  initial=fp.GetPosition()
  for dx,dy in sorted(((a,b) for a in range(-6,7) for b in range(-6,7)),key=lambda t:(t[0]**2+t[1]**2,t)):
   fp.SetPosition(initial+vec((dx*P,dy*P)));box=base.caja(fp)
   if box[0]<5 or box[1]<5 or box[2]>195 or box[3]>115:continue
   if all(box[2]+.1<=o[0] or box[0]>=o[2]+.1 or box[3]+.1<=o[1] or box[1]>=o[3]+.1 for o in placed):break
  else:raise ValueError(('Sin lugar libre',ref))
  placed.append(box)
  for pad in fp.Pads():
   if pad.GetAttribute()!=k.PAD_ATTRIB_PTH:continue
   q=grid(pad.GetPosition());dest=vec(xy(q));dist=(dest-pad.GetPosition()).EuclideanNorm()/1e6
   if dist>.05:
    if not ref.startswith(('R','C','D')):raise ValueError(('No adaptable',ref,pad.GetNumber(),dist))
    if dist>1.5:raise ValueError(('Pata demasiado alejada',ref,dist))
    adjusted.append([ref,pad.GetNumber(),round(dist,3)])
   pad.SetPosition(dest);pad.SetSize(vec((1.7,1.7)));pad.SetDrillSize(vec((1,1)));pad.SetShape(k.PAD_SHAPE_CIRCLE);pad.SetLayerSet(layers())
   if q in holes:raise ValueError(('Colisión de agujero',q,ref,holes[q]))
   if not(0<=q[0]<NX and 0<=q[1]<NY):raise ValueError(('Fuera de placa',ref,q))
   name=pad.GetNetname();holes[q]=name or f'NC:{ref}:{pad.GetNumber()}'
   terminals[(ref,pad.GetNumber())]=q
 # La ruta usa centros de agujeros, sin cruces de redes en el estaño.
 occupied=dict(holes);paths=[];jumpers=[];reserve={}
 # Separación de 0,25 mm entre pistas de 0,9 mm y pads de 1,7 mm.
 for q,net in holes.items():
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   n=(q[0]+dx,q[1]+dy)
   if n in holes:continue
   occupied[n]=net if occupied.get(n,net)==net else '#BLOCK'
 for q,net in holes.items():
  if net.startswith('NC:') or net.startswith('unconnected'):continue
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   mid=(q[0]+dx,q[1]+dy);n=(q[0]+2*dx,q[1]+2*dy)
   if 0<=n[0]<NX and 0<=n[1]<NY and occupied.get(mid,net)==net and n not in occupied and all(math.dist(n,h)*P>=1.95 for h in holes):
    occupied[n]=net;occupied[mid]=net;reserve[q]=[q,mid,n];break
  else:raise ValueError(('Sin espacio para punto de puente',q,net))
 def astar(start,targets,net):
  frontier=[(0,0,start)];seen={start:0};prev={}
  while frontier:
   _,cost,q=heapq.heappop(frontier)
   if q in targets:
    path=[q]
    while q!=start:q=prev[q];path.append(q)
    return path[::-1]
   if cost>320:continue
   for d in ((1,0),(-1,0),(0,1),(0,-1)):
    n=(q[0]+d[0],q[1]+d[1])
    if not(0<=n[0]<NX and 0<=n[1]<NY) or occupied.get(n,net)!=net:continue
    c=cost+1
    if c<seen.get(n,999):
     seen[n]=c;prev[n]=q;h=min(abs(n[0]-t[0])+abs(n[1]-t[1]) for t in targets);heapq.heappush(frontier,(c+h,c,n))
  return None
 bynet={}
 for rp,q in terminals.items():
  name=pin_net.get(rp)
  if name and not name.startswith('unconnected'):bynet.setdefault(name,[]).append(q)
 # Local nets first, power distribution last.
 order=os.environ.get('PCB_ROUTE_ORDER','long')
 def route_key(t):
  net,pts=t;power=net.lstrip('/') in ('GND','VREF','+5V','+3V3','+3.3VA')
  if order=='long':return (-len(pts),net)
  if order=='power':return (not power,len(pts),net)
  if order=='vref':return (net.lstrip('/')!='VREF',len(pts),net)
  if order=='ground':return (net!='GND',len(pts),net)
  return (len(pts)>10,len(pts),net)
 for net,points in sorted(bynet.items(),key=route_key):
  connected={points[0]};todo=set(points[1:])
  while todo:
   _,a,b=min((abs(a[0]-b[0])+abs(a[1]-b[1]),a,b) for a in todo for b in connected)
   path=astar(a,connected,net)
   if path:
    paths.append({'red':net,'puntos':path});connected.update(path)
    for q in path:occupied[q]=net
   else:
    jumpers.append({'ref':f'W{len(jumpers)+1}','red':net,'a':a,'b':b});connected.add(a)
   todo-=connected
 # Cada puente termina en su propio taladro, separado de las patas de componentes.
 used_holes=set(holes)
 for jumper in jumpers:
  for key in ('a','b'):
   original=tuple(jumper[key]);net=jumper['red']
   candidates=[]
   if original in reserve:candidates.append((0,reserve[original]))
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    for length in range(1,5):
     route=[(original[0]+dx*i,original[1]+dy*i) for i in range(length+1)]
     end=route[-1]
     if all(0<=q[0]<NX and 0<=q[1]<NY and occupied.get(q,net)==net for q in route) and end not in holes and all(math.dist(end,h)*P>=1.95 for h in holes):
      candidates.append((length,route))
   if not candidates:raise ValueError(('Puente sin taladro propio',jumper,key))
   _,route=min(candidates);end=route[-1];used_holes.add(end)
   for q in route:occupied[q]=net
   paths.append({'red':net,'puntos':route});jumper[key]=end
 for path in paths:
  for a,b in zip(path['puntos'],path['puntos'][1:]):
   t=k.PCB_TRACK(board);t.SetStart(vec(xy(a)));t.SetEnd(vec(xy(b)));t.SetLayer(k.B_Cu);t.SetWidth(mm(.9));t.SetNet(nets[path['red']]);board.Add(t)
 jumper_holes=set()
 for j in jumpers:
  fp=k.FOOTPRINT(board);fp.SetReference(j['ref']);fp.SetValue('Cable aislado '+j['red']);fp.SetBoardOnly(True);fp.SetExcludedFromBOM(True);board.Add(fp);fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
  for n,key in enumerate(('a','b'),1):
   pad=k.PAD(fp);pad.SetNumber(str(n));pad.SetAttribute(k.PAD_ATTRIB_PTH);pad.SetShape(k.PAD_SHAPE_CIRCLE);pad.SetSize(vec((1.0,1.0)));pad.SetDrillSize(vec((.6,.6)));pad.SetLayerSet(layers());pad.SetNet(nets[j['red']]);fp.Add(pad);pad.SetPosition(vec(xy(j[key])))
   point=tuple(j[key])
   if point in jumper_holes:pad.SetAttribute(k.PAD_ATTRIB_SMD);pad.SetDrillSize(vec((0,0)));pad.SetLayerSet(bottom_layers())
   jumper_holes.add(point)
  base.linea(board,k.F_Fab,[xy(j['a']),xy(j['b'])],.12)
 base.linea(board,k.Edge_Cuts,[(0,0),(200,0),(200,120),(0,120),(0,0)],.1)
 for a in ((4,4),(196,4),(4,116),(196,116)):base.agujero(board,*a)
 for ref,fp in fps.items():
  pos=fp.GetPosition();base.texto(board,ref,k.ToMM(pos.x)+1,k.ToMM(pos.y)-2,1)
 # Huellas locales adaptadas: el esquema y la placa apuntan a la misma biblioteca.
 library=ROOT/'hardware/Ecualizador.pretty';overrides={}
 for ref,fp in fps.items():
  name='UnaCara_'+ref;fp.SetFPID(k.LIB_ID('Ecualizador',name));overrides[ref]='Ecualizador:'+name
  copy=k.Cast_to_FOOTPRINT(fp.Duplicate(False));copy.SetOrientationDegrees(0);copy.SetPosition(vec((0,0)))
  for pad in copy.Pads():pad.SetNetCode(0)
  k.PCB_IO_KICAD_SEXPR().FootprintSave(str(library),copy)
 (OUT/'huellas.json').write_text(json.dumps(overrides,indent=2))
 filename=OUT/'ecualizador-D1.kicad_pcb';board.Save(str(filename))
 tree=parse(filename.read_text())[0]
 for fp in find(tree,'footprint'):
  ref=next((x[2] for x in find(fp,'property') if x[1]=='Reference'),'')
  if ref.startswith('W'):fp.append([Sym('jumper_pad_groups'),['1','2']])
 filename.write_text(dump(tree)+'\n')
 data={'revision':'D.1','estado':'continuidad digital verificada; montaje físico pendiente','ancho':200,'alto':120,'paso':P,'columnas':NX,'filas':NY,'origen':[X0,Y0],'pines':{f'{r}.{p}':q for (r,p),q in terminals.items()},'redes':{name:pts for name,pts in bynet.items()},'pistas':paths,'puentes':jumpers,'panel':panel,'patas_ajustadas_mm':adjusted}
 (OUT/'montaje.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
 print(f'{len(fps)} componentes; {len(paths)} rutas inferiores; {len(jumpers)} cables; {len(terminals)} terminales')
if __name__=='__main__':main()

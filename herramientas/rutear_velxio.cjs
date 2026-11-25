// Use Velxio's own obstacle-aware orthogonal router on measured pin geometry.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const router=require(process.env.VELXIO_ROUTER||'/tmp/eq-router.cjs');
const geometry=JSON.parse(fs.readFileSync(path.join(root,'simulacion/velxio/local/geometria-componentes.json')));
const byId=new Map(geometry.map(g=>[g.id,g]));
const file=path.join(root,'simulacion/velxio/integrado-local-1000Hz.vlx');
const project=JSON.parse(fs.readFileSync(file));
function pin(e){
 const g=byId.get(e.componentId);
 const p=g.pins.find(p=>p.name===e.pinName)||g.pins.find(p=>p.name===e.pinName+'.1')||g.pins.find(p=>p.name===({36:'VP',39:'VN'}[e.pinName]));
 if(!p)throw Error('Pin absent: '+JSON.stringify(e));
 return {x:p.x,y:p.y};
}
// Local signal connections first; shared rail trees last.
const wires=project.wires.map(w=>({...w,start:{...w.start,...pin(w.start)},end:{...w.end,...pin(w.end)}}));
function length(w){return Math.abs(w.start.x-w.end.x)+Math.abs(w.start.y-w.end.y)}
wires.sort((a,b)=>Number(['#64748b','#ac83ec','#e96767'].includes(a.color))-Number(['#64748b','#ac83ec','#e96767'].includes(b.color))||length(a)-length(b));
const segments=[];let direct=0;
for(const [i,w] of wires.entries()){
 const x0=Math.min(w.start.x,w.end.x)-160,y0=Math.min(w.start.y,w.end.y)-160;
 const x1=Math.max(w.start.x,w.end.x)+160,y1=Math.max(w.start.y,w.end.y)+160;
 const obstacles=geometry.filter(g=>g.id!==w.start.componentId&&g.id!==w.end.componentId)
   .map(g=>g.rect).filter(r=>r.x<x1&&r.y<y1&&r.x+r.w>x0&&r.y+r.h>y0);
 const points=router.routeAroundObstacles(w.start,w.end,obstacles,segments.slice(-24));
 w.waypoints=points||[];
 w.autoRouted=false;
 if(!points)direct++;
 const full=[w.start,...w.waypoints,w.end];
 for(let j=1;j<full.length;j++){
   const a=full[j-1],b=full[j],dx=Math.abs(a.x-b.x),dy=Math.abs(a.y-b.y);
   if(dx&&dy){const elbow=dx>=dy?{x:b.x,y:a.y}:{x:a.x,y:b.y};segments.push({a,b:elbow},{a:elbow,b})}
   else segments.push({a,b});
 }
 if(i%40===0)console.log('Conexiones trazadas:',i);
}
for(const hz of [100,1000,8000]){
 const f=path.join(root,`simulacion/velxio/integrado-local-${hz}Hz.vlx`);
 const p=JSON.parse(fs.readFileSync(f));p.wires=wires;
 fs.writeFileSync(f,JSON.stringify(p,null,2));
}
fs.writeFileSync(path.join(root,'simulacion/velxio/local/rutas-presentacion.json'),JSON.stringify(wires,null,2));
console.log(wires.length,'conexiones; rutas directas:',direct);

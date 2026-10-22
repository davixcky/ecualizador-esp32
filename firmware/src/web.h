// Página que sirve el ESP32 en http://192.168.4.1 (red Wi-Fi "Ecualizador-ESP32").
// Pide /datos diez veces por segundo y dibuja las bandas y el espectro en un <canvas>.
#pragma once
#include <pgmspace.h>

static const char PAGINA_WEB[] PROGMEM = R"HTML(<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ecualizador ESP32</title>
<style>
:root{--f:#080a14;--c:#121628;--t:#ebeef5;--m:#78809a;--g:#ff7a3d;--md:#3ddc84;--a:#33b5ff}
body{margin:0;background:var(--f);color:var(--t);font-family:system-ui,sans-serif}
header{background:var(--c);padding:12px 16px;display:flex;justify-content:space-between;align-items:center}
h1{font-size:18px;margin:0}#clip{background:#eb3c3c;border-radius:6px;padding:2px 8px;font-weight:700;visibility:hidden}
main{padding:12px 16px;max-width:720px;margin:auto}
.fila{display:flex;gap:16px;flex-wrap:wrap}.dato{color:var(--m);font-size:13px}.dato b{color:var(--t);font-size:20px;display:block}
canvas{width:100%;background:var(--c);border-radius:10px;margin-top:12px}
</style></head><body>
<header><h1>Ecualizador de 3 bandas</h1><span id="clip">CLIP</span></header>
<main>
<div class="fila"><div class="dato">Nivel<b id="rms">--</b></div><div class="dato">Tono dominante<b id="pico">--</b></div></div>
<canvas id="bandas" width="640" height="260"></canvas>
<canvas id="espectro" width="640" height="260"></canvas>
</main>
<script>
const C=['#ff7a3d','#3ddc84','#33b5ff'],N=['Graves','Medios','Agudos'];
const pico=new Array(32).fill(-60);
function mezcla(t){const a=t<.5?[255,122,61]:[61,220,132],b=t<.5?[61,220,132]:[51,181,255],k=t<.5?t*2:(t-.5)*2;
 return `rgb(${a.map((v,i)=>Math.round(v+(b[i]-v)*k)).join(',')})`}
function bandas(d){const c=document.getElementById('bandas').getContext('2d');c.clearRect(0,0,640,260);
 for(let i=0;i<3;i++){const x=60+i*200,f=Math.max(0,Math.min(1,(d.b[i]+40)/40));
  for(let s=0;s<20;s++){c.fillStyle=s<f*20?C[i]:C[i]+'22';c.fillRect(x,200-s*9,80,7)}
  c.fillStyle='#ebeef5';c.font='bold 18px system-ui';c.textAlign='center';
  c.fillText(d.b[i]<=-60?'--':d.b[i].toFixed(0)+' dB',x+40,20);
  c.fillStyle=C[i];c.font='14px system-ui';c.fillText(N[i]+' · '+d.mv[i]+' mV',x+40,240)}}
function espectro(d){const c=document.getElementById('espectro').getContext('2d');c.clearRect(0,0,640,260);
 const w=600/32;for(let j=0;j<32;j++){const v=d.s[j];pico[j]=Math.max(v,pico[j]-2);
  const h=Math.max(0,(v+60)/60)*220,hp=Math.max(0,(pico[j]+60)/60)*220;
  c.fillStyle=mezcla(j/31);c.fillRect(20+j*w,240-h,w-3,h);c.fillStyle='#ebeef5';c.fillRect(20+j*w,240-hp-2,w-3,2)}}
async function ciclo(){try{const d=await (await fetch('/datos')).json();
 document.getElementById('rms').textContent=d.rms.toFixed(1)+' dBFS';
 document.getElementById('pico').textContent=d.pico>=1000?(d.pico/1000).toFixed(2)+' kHz':d.pico+' Hz';
 document.getElementById('clip').style.visibility=d.clip?'visible':'hidden';bandas(d);espectro(d)}catch(e){}
 setTimeout(ciclo,100)}
ciclo();
</script></body></html>)HTML";

// Prueba real del editor: no inyecta lecturas ni modifica el simulador.
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),hz=Number(process.argv[2]||1000),expected={100:0,1000:1,8000:2}[hz];
if(expected===undefined)throw Error('Usar 100, 1000 u 8000 Hz');
(async()=>{const b=await chromium.launch({headless:true});try{
 const p=await b.newPage({viewport:{width:3200,height:2000}});p.setDefaultTimeout(1800);
 await p.goto('https://velxio.dev/editor?esp32sim=qemu',{waitUntil:'networkidle',timeout:60000});
 for(const name of ['Got it','Cancel'])await p.getByRole('button',{name,exact:true}).click().catch(()=>{});
 await p.locator('input[type=file][accept*=".vlx"]').first().setInputFiles(path.join(root,`simulacion/velxio/integrado-${hz}Hz.vlx`));
 await p.getByRole('button',{name:'Minimize chat'}).click().catch(()=>{});await p.getByTitle('Hide file explorer').click().catch(()=>{});await p.getByRole('button',{name:'Circuit',exact:true}).click().catch(()=>{});
 await p.getByTitle('Reset view').click().catch(()=>{});await p.getByTitle('Run (auto-compiles if needed)').click();
 let serial='',rows=[];
 for(let i=0;i<180;i++){
  if(await p.getByRole('button',{name:'Run anyway',exact:true}).isVisible().catch(()=>false)){
   const debug=await p.evaluate(()=>window.__spiceDebug?.());
   if(!debug?.converged)throw Error('El solver no converge: '+debug?.error);
   // La comprobación previa puede conservar el aviso de una red incompleta
   // durante la importación. Solo continuar si el resultado actual converge.
   await p.getByRole('button',{name:'Run anyway',exact:true}).click();
  }
  serial=await p.locator('body').innerText();
  rows=[...serial.matchAll(/CADENA G=([-\d.]+) M=([-\d.]+) A=([-\d.]+) DOM=(\d) REF=([\d.]+) FFT_HZ=([\d.]+) FFT_SPAN=(\d+) TFT=OK/g)].map(m=>({levels_v:m.slice(1,4).map(Number),dominant:+m[4],reference_adc:+m[5],fft_hz_diagnostic:+m[6],fft_span:+m[7]}));
  if(rows.length>=3)break;
  if(/Compilation failed/.test(serial))throw Error('Falló la compilación');
  await p.waitForTimeout(1000);
 }
 const debug=await p.evaluate(()=>window.__spiceDebug?.());
 const pass=debug?.converged&&rows.length>=2&&rows.slice(-2).every(r=>r.dominant===expected&&r.levels_v[expected]>.005&&r.levels_v[expected]>2*Math.max(...r.levels_v.filter((_,i)=>i!==expected))&&r.fft_span>0);
 await p.getByRole('button',{name:'Switch to light theme',exact:true}).click().catch(()=>{});await p.getByTitle('Reset view').click().catch(()=>{});
 await p.screenshot({path:path.join(root,`img/velxio-integrado-${hz}Hz.png`)});
 await p.locator('wokwi-ili9341').first().screenshot({path:path.join(root,`img/velxio-tft-${hz}Hz.png`)});
 fs.writeFileSync(path.join(root,`simulacion/velxio/validacion-integrado-${hz}Hz.json`),JSON.stringify({timestamp:new Date().toISOString(),url:p.url(),frequency_hz:hz,pass_levels:!!pass,pass_fft_frequency:false,rows,debug,scope:'Entrada, preamplificador, filtros, detectores, ADC ESP32 y TFT. AO/diodos ideales; FFT no calibrada; sin PAM8403 ni AHCT/NeoPixel.'},null,2));
 if(!pass)throw Error('La cadena no cumple la selectividad esperada.');console.log(`${hz} Hz: ADC y TFT verificados; FFT no calibrada.`);
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

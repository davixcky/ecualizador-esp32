// End-to-end checks against local Docker: actual firmware, ADC and TFT pixels.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const out=path.join(root,'simulacion/velxio/local');
(async()=>{
 const browser=await chromium.connectOverCDP(process.env.CDP_URL||'http://127.0.0.1:9233');
 try {
  const context=browser.contexts()[0];
  const page=context.pages().find(p=>p.url().includes('localhost:3080'))||await context.newPage();
  const cdp=await context.newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
  await page.goto('http://localhost:3080/editor/?esp32sim=qemu&revision='+Date.now(),{waitUntil:'domcontentloaded'});
  page.setDefaultTimeout(2000);
  const results=[];
  for(const hz of [100,1000,8000]) {
   await page.goto('http://localhost:3080/editor/?esp32sim=qemu&case='+hz+'&revision='+Date.now(),{waitUntil:'domcontentloaded'});
   await page.locator('input[type=file][accept*=".vlx"]').first().setInputFiles(path.join(root,`simulacion/velxio/integrado-local-${hz}Hz.vlx`));
   await page.waitForTimeout(2500);
   await page.getByRole('button',{name:'Clear',exact:true}).click().catch(()=>{});
   await page.getByTitle('Run (auto-compiles if needed)',{exact:true}).click();
   let rows=[];
   for(let attempt=0;attempt<240;attempt++) {
    if(await page.getByRole('button',{name:'Run anyway',exact:true}).isVisible().catch(()=>false))
      throw Error('El circuito aún requiere omitir una comprobación: '+(await page.locator('body').innerText()).slice(-1800));
    const body=await page.locator('body').innerText();
    rows=[...body.matchAll(/CADENA G=([-\d.]+) M=([-\d.]+) A=([-\d.]+) DOM=(\d) REF=([\d.]+) FFT_HZ=([\d.]+) FFT_SPAN=(\d+) TFT=OK/g)].map(m=>({levels_v:m.slice(1,4).map(Number),dominant:+m[4],reference_adc:+m[5],fft_hz_diagnostic:+m[6],fft_span:+m[7]}));
    if(rows.length>=4&&rows.slice(-3).every(r=>r.dominant==={100:0,1000:1,8000:2}[hz]))break;
    if(/Compilation failed/.test(body))throw Error('Falló la compilación');
    await page.waitForTimeout(1000);
   }
   const debug=await page.evaluate(()=>{
    const d=window.__spiceDebug?.();
    return {converged:d?.converged,error:d?.error,analysisMode:d?.analysisMode,nodeVoltageCount:d?.nodeVoltageCount};
   });
   const display=await page.locator('wokwi-ili9341').evaluate(el=>{
    const canvas=el.shadowRoot.querySelector('canvas');
    const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
    let lit=0;const colors=new Set();
    for(let i=0;i<pixels.length;i+=4)if(pixels[i]||pixels[i+1]||pixels[i+2]){lit++;colors.add(`${pixels[i]},${pixels[i+1]},${pixels[i+2]}`)}
    return {litPixels:lit,colorCount:colors.size,png:canvas.toDataURL('image/png')};
   });
   fs.writeFileSync(path.join(out,`tft-${hz}Hz.png`),Buffer.from(display.png.split(',')[1],'base64'));
   const expected={100:0,1000:1,8000:2}[hz];
   const pass=debug.converged&&rows.length>=3&&rows.slice(-3).every(r=>r.dominant===expected&&r.levels_v[expected]>.005&&r.levels_v[expected]>2*Math.max(...r.levels_v.filter((_,i)=>i!==expected))&&r.fft_span>0)&&display.litPixels>1000&&display.colorCount>=4;
   const result={hz,pass,rows:rows.slice(-4),debug,display:{litPixels:display.litPixels,colorCount:display.colorCount},fftFrequencyValidated:false,timestamp:new Date().toISOString()};
   results.push(result);
   fs.writeFileSync(path.join(out,'validacion-navegador.json'),JSON.stringify(results,null,2));
   console.log(JSON.stringify(result));
   if(!pass)throw Error(`${hz} Hz no cumple la comprobación integrada.`);
  }
  // Leave the central-band demonstration running for the presentation.
  await page.getByTitle('Stop',{exact:true}).click();
  await page.locator('input[type=file][accept*=".vlx"]').first().setInputFiles(path.join(root,'simulacion/velxio/integrado-local-1000Hz.vlx'));
  await page.waitForTimeout(2500);
  await page.getByTitle('Run (auto-compiles if needed)',{exact:true}).click();
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

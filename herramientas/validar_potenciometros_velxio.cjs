// Drag the actual slider widgets; verify the real QEMU serial/ADC response.
const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),out=path.join(root,'simulacion/velxio/local');
(async()=>{
 const browser=await chromium.connectOverCDP(process.env.CDP_URL||'http://127.0.0.1:9233');
 try{
  const p=browser.contexts()[0].pages().find(p=>p.url().includes('localhost:3080'));
  await p.setViewportSize({width:1700,height:1050});
  const cdp=await p.context().newCDPSession(p);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
  await p.goto('http://localhost:3080/editor/?esp32sim=qemu&pots='+Date.now(),{waitUntil:'domcontentloaded'});
  await p.locator('input[type=file][accept*=".vlx"]').first().setInputFiles(path.join(root,'simulacion/velxio/integrado-local-multitono.vlx'));
  await p.waitForTimeout(2000);
  await p.getByTitle('Run (auto-compiles if needed)',{exact:true}).click();
  await p.getByRole('button',{name:'View',exact:true}).click();await p.getByRole('menuitemradio',{name:/Circuit/}).click();
  await p.getByTitle('Hide file explorer').click().catch(()=>{});
  await p.getByTitle('Reset view (click to reset)',{exact:true}).click();
  for(let i=0;i<8;i++)await p.getByTitle('Zoom out',{exact:true}).click();
  async function readings(predicate){
   for(let i=0;i<90;i++){
    const text=await p.locator('body').innerText();
    if(await p.getByRole('button',{name:'Run anyway',exact:true}).isVisible().catch(()=>false))throw Error(text.slice(-1500));
    const rows=[...text.matchAll(/CADENA G=([-\d.]+) M=([-\d.]+) A=([-\d.]+).*?TFT=OK/g)].map(m=>m.slice(1,4).map(Number));
    if(rows.length>=3&&rows.slice(-3).every(predicate)){
     const ok=await p.evaluate(()=>window.__spiceDebug?.().converged);
     if(ok)return rows.slice(-3);
    }
    await p.waitForTimeout(1000);
   }
   throw Error('No llegaron lecturas que respondan al deslizador');
  }
  const initial=await readings(v=>v.every(x=>x>.005));
  const result={initial,controls:[],timestamp:new Date().toISOString()};
  for(const [index,ref] of ['RV2','RV3','RV4'].entries()){
   const base=initial.at(-1)[index],states=[];
   for(const value of [0,100,50]){
    await p.getByRole('button',{name:'Clear',exact:true}).click();
    const widget=p.locator('#'+ref),tip=await widget.locator('#tip').boundingBox(),svg=await widget.locator('svg').first().boundingBox();
    await p.mouse.move(tip.x+tip.width/2,tip.y+tip.height/2);
    await p.mouse.down();
    await p.mouse.move(svg.x+svg.width*(12.5+30*value/100)/55,tip.y+tip.height/2,{steps:1});
    await p.mouse.up();
    const actual=await widget.evaluate(e=>e.value);
    if(Math.abs(actual-value)>2)throw Error(`${ref}: pointer value ${actual}, expected ${value}`);
    const rows=await readings(v=>value===0?Math.abs(v[index])<.003:value===100?v[index]>1.4*base:v[index]>.5*base&&v[index]<1.5*base);
    states.push({value:actual,rows});
    console.log(ref,value,JSON.stringify(rows.at(-1)));
   }
   result.controls.push({ref,states,pass:true});
   fs.writeFileSync(path.join(out,'validacion-potenciometros-navegador.json'),JSON.stringify(result,null,2));
  }
  await p.screenshot({path:path.join(out,'demo-potenciometros.png')});
  await p.bringToFront();
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

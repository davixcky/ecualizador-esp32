const {chromium}=require('playwright');const fs=require('fs');
const root=require('path').resolve(__dirname,'..');
(async()=>{const b=await chromium.launch({headless:true});const p=await b.newPage({viewport:{width:1900,height:1100}});p.setDefaultTimeout(1800);
await p.goto('https://velxio.dev/editor',{waitUntil:'networkidle',timeout:60000});
await p.getByText('Got it',{exact:true}).click().catch(()=>{});await p.getByRole('button',{name:'Cancel',exact:true}).click().catch(()=>{});
await p.getByRole('button',{name:'Minimize chat'}).click().catch(()=>{});
await p.getByRole('button',{name:'Switch to light theme',exact:true}).click().catch(()=>{});
await p.getByRole('button',{name:'Circuit',exact:true}).click().catch(()=>{});
await p.getByTitle('Hide file explorer').click().catch(()=>{});
const results=[];
for(const hz of [100,1000,8000]){
await p.locator('input[type=file][accept*=".vlx"]').first().setInputFiles(`${root}/simulacion/velxio/filtros-${hz}Hz.vlx`);
await p.getByRole('button',{name:'Cancel',exact:true}).click().catch(()=>{});
await p.waitForTimeout(4000);
const txt=await p.locator('body').innerText();
const rms=[...txt.matchAll(/RMS ([\d.]+) (mV|V)/g)].map(m=>Number(m[1])*(m[2]==='V'?1000:1));
const expected=hz===100?0:hz===1000?1:2;
const pass=rms.length===3 && rms[expected]===Math.max(...rms);
results.push({hz,rms_mV:rms,bandOrder:['graves','medios','agudos'],expectedDominant:expected,pass,engineStatus:txt.match(/SPICE[^\n]*/)?.[0],model:'opamp-ideal; entrada PRE 0.1 V pico + VREF 1.65 V',source:'https://velxio.dev/editor',timestamp:new Date().toISOString()});
console.log(results.at(-1));
await p.screenshot({path:`${root}/img/velxio-${hz}Hz.png`});
}
fs.writeFileSync(`${root}/simulacion/velxio/validacion.json`,JSON.stringify(results,null,2));await b.close();if(results.some(x=>!x.pass))process.exitCode=1;
})();

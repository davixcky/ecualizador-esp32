// Measure actual CircuitJS voltages at the simulator's own time coordinates.
// The Python analysis fits sinusoidal amplitude/phase after transients.
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
(async () => {
  const browser = await chromium.connectOverCDP(process.env.CDP_URL || 'http://127.0.0.1:9233');
  try {
    const page = browser.contexts()[0].pages().find(p => p.url().includes('falstad.com/circuit/'));
    if (!page) throw Error('Open Falstad in the presentation browser first.');
    const results = [];
    for (const hz of [100, 1000, 8000]) {
      const data = fs.readFileSync(path.join(root, `simulacion/falstad/filtros-${hz}Hz.txt`), 'utf8');
      await page.evaluate(data => {
        CircuitJS1.importCircuit(data, false);
        CircuitJS1.setSimRunning(true);
      }, data);
      const rows = await page.evaluate(async () => {
        const rows = [], nodes = ['PRE', 'GRAVES', 'MEDIOS', 'AGUDOS'];
        const start = performance.now();
        while (performance.now() - start < 8000) {
          await new Promise(r => setTimeout(r, 13));
          rows.push([CircuitJS1.getTime(), ...nodes.map(n => CircuitJS1.getNodeVoltage(n))]);
        }
        return rows;
      });
      const body = await page.locator('body').innerText();
      if (/convergence failed|singular matrix|exception|error/i.test(body)) throw Error(body);
      const count = await page.evaluate(() => CircuitJS1.getElements().filter(e => e.getType() === 'CapacitorElm').length);
      if (count !== 8) throw Error(`Expected eight capacitors; got ${count}`);
      results.push({hz, nodes:['PRE','GRAVES','MEDIOS','AGUDOS'], rows});
      await page.screenshot({path:path.join(root, `simulacion/falstad/filtros-${hz}Hz.png`)});
      console.log(`${hz} Hz: ${rows.length} samples, t=${rows.at(-1)[0].toFixed(3)} s`);
    }
    fs.writeFileSync(path.join(root,'simulacion/falstad/muestras.json'), JSON.stringify(results));
    await page.evaluate(data => CircuitJS1.importCircuit(data,false), fs.readFileSync(path.join(root,'simulacion/falstad/filtros-1000Hz.txt'),'utf8'));
  } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exitCode=1});

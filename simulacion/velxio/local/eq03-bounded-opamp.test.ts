import {describe, it, expect} from 'vitest';
import fs from 'node:fs';
import {buildInputFromStore} from '../simulation/spice/storeAdapter';
import {buildNetlist} from '../simulation/spice/NetlistBuilder';
import {runNetlist} from './helpers/testSolver';

const filename = process.env.EQ03_PROJECT;
describe.skipIf(!filename)('EQ03 output-limited ideal op-amps', () => {
  it('solves the complete detector chain in DC and preserves band selectivity', async () => {
    const report:any[] = [];
    const project = JSON.parse(fs.readFileSync(filename!, 'utf8'));
    for (const component of project.components) {
      if (component.metadataId === 'opamp-ideal') {
        Object.assign(component.properties, {model:'eq03-mcp6004',detector:['U3A','U3C','U4A'].includes(component.id)});
      }
    }
    for (const hz of [100, 1000, 8000]) {
      project.components.find((c:any) => c.id === 'ENTRADA').properties.frequency = hz;
      const input = buildInputFromStore({...project,
        boards:project.boards.map((b:any) => ({...b, pinStates:{}}))});
      const dc = buildNetlist({...input, analysis:{kind:'op'}});
      const op = await runNetlist(dc.netlist);
      const reference = dc.pinNetMap.get('esp32:36')!;
      expect(op.dcValue(`v(${reference})`)).toBeCloseTo(1.65, 2);
      const transient = buildNetlist(input);
      const result = await runNetlist(transient.netlist);
      const times = result.vec('time') as number[];
      expect(times[times.length-1]).toBeGreaterThanOrEqual(.399);
      const ref = result.vec(`v(${reference})`) as number[];
      const levels = ['34','35','32'].map(pin => {
        const values = result.vec(`v(${transient.pinNetMap.get('esp32:'+pin)})`) as number[];
        const start = Math.floor(values.length*.8);
        return values.slice(start).reduce((sum,v,i) => sum+v-ref[start+i],0)/(values.length-start);
      });
      const dominant = {100:0,1000:1,8000:2}[hz]!;
      console.log(hz, 'Hz, detector levels:', levels);
      report.push({hz,levels});
      expect(levels[dominant]).toBeGreaterThan(.005);
      expect(levels[dominant]).toBeGreaterThan(2*Math.max(...levels.filter((_,i)=>i!==dominant)));
      for (const pin of ['34','35','32','33']) {
        const values = result.vec(`v(${transient.pinNetMap.get('esp32:'+pin)})`) as number[];
        expect(values.reduce((a,b)=>Math.min(a,b),Infinity)).toBeGreaterThanOrEqual(-.001);
        expect(values.reduce((a,b)=>Math.max(a,b),-Infinity)).toBeLessThanOrEqual(3.301);
      }
    }
    fs.writeFileSync('/tmp/eq03-bounded-results.json',JSON.stringify(report));
  }, 60000);
});

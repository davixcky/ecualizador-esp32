import {describe,it,expect} from 'vitest';
import {buildNetlist} from '../simulation/spice/NetlistBuilder';
import {buildInputFromStore} from '../simulation/spice/storeAdapter';
import {runNetlist} from './helpers/testSolver';
import fs from 'node:fs';

describe('EQ03 floating audio potentiometers',()=>{
 it('keeps VREF floating and divides between the two actual terminal voltages',async()=>{
  for(const value of [0,50,100]){
   const wire=(id:string,a:string,ap:string,b:string,bp:string)=>({id,start:{componentId:a,pinName:ap},end:{componentId:b,pinName:bp}});
   const input:any={components:[
    {id:'top',metadataId:'signal-generator',properties:{waveform:'dc',offset:1.75}},
    {id:'ref',metadataId:'signal-generator',properties:{waveform:'dc',offset:1.65}},
    {id:'pot',metadataId:'slide-potentiometer',properties:{floatingTrack:true,total:10000,value,min:0,max:100}},
    {id:'load',metadataId:'resistor',properties:{value:'1e9'}},
   ],boards:[],analysis:{kind:'op'},wires:[wire('a','top','SIG','pot','VCC'),wire('b','ref','SIG','pot','GND'),wire('c','top','GND','ref','GND'),wire('d','pot','SIG','load','1'),wire('e','load','2','ref','GND')]};
   const deck=buildNetlist(input);const result=await runNetlist(deck.netlist);
   const get=(pin:string)=>result.dcValue(`v(${deck.pinNetMap.get('pot:'+pin)})`);
   expect(get('VCC')).toBeCloseTo(1.75,4);expect(get('GND')).toBeCloseTo(1.65,4);
   expect(get('SIG')).toBeCloseTo(1.65+.1*value/100,4);
   expect(deck.pinNetMap.get('pot:GND')).not.toBe('0');
  }
 });
 it('changes actual detector levels in the full analog chain',async()=>{
  const project=JSON.parse(fs.readFileSync(process.env.EQ03_PROJECT!,'utf8'));
  const report:any[]=[];
  for(const [ref,hz,adc] of [['RV2',100,'34'],['RV3',1000,'35'],['RV4',8000,'32']] as const){
   const levels:number[]=[];
   for(const value of [0,50,100]){
    project.components.find((c:any)=>c.id==='ENTRADA').properties.frequency=hz;
    project.components.find((c:any)=>c.id===ref).properties.value=value;
    const input=buildInputFromStore({...project,boards:project.boards.map((b:any)=>({...b,pinStates:{}}))});
    const deck=buildNetlist(input);const result=await runNetlist(deck.netlist);
    const times=result.vec('time') as number[];expect(times.at(-1)).toBeGreaterThanOrEqual(.399);
    const v=result.vec(`v(${deck.pinNetMap.get('esp32:'+adc)})`) as number[],r=result.vec(`v(${deck.pinNetMap.get('esp32:36')})`) as number[];
    const start=Math.floor(v.length*.8);levels.push(v.slice(start).reduce((s,x,i)=>s+x-r[start+i],0)/(v.length-start));
   }
   expect(Math.abs(levels[0])).toBeLessThan(.002);
   expect(levels[1]).toBeGreaterThan(.005);
   expect(levels[2]).toBeGreaterThan(1.5*levels[1]);
   report.push({ref,hz,positions:[0,50,100],levels_v:levels});
   project.components.find((c:any)=>c.id===ref).properties.value=50;
  }
  fs.writeFileSync('/tmp/eq03-pot-spice-results.json',JSON.stringify(report,null,2));
 },60000);
});

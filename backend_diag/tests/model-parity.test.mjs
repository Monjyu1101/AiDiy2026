// Checked-in goldens come from the original standalone Python implementation.
// Normal tests need Node only; generator is optional, offline reference tooling.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as catalog from '../runtime/model_catalog.mjs';
const fixtures=JSON.parse(readFileSync(new URL('./reference/model-golden.json',import.meta.url),'utf8'));
for(const fixture of fixtures){
 test(`${fixture.timezone}: Python parity: ${fixture.name}`,()=>{
  const oldTZ=process.env.TZ;
  try{
   process.env.TZ=fixture.timezone;
   const now=new Date(fixture.now);
   const fn=catalog[`${fixture.kind}Catalog`];
   const actual=fixture.kind==='google'?fn(fixture.source,fixture.router):
    ['openai','claude'].includes(fixture.kind)?fn(fixture.source,fixture.router,now):fn(fixture.source,now);
   assert.deepEqual(JSON.parse(JSON.stringify(actual)),fixture.expected);
   assert.deepEqual(Object.keys(actual),fixture.order,'Preserve Python insertion order, including duplicate replacement');
  }finally{if(oldTZ===undefined)delete process.env.TZ;else process.env.TZ=oldTZ;}
 });
}

import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {stopRevision,watchStop} from '../起動/lifecycle.mjs';
test('cleanup marker persists across short cleanup, old marker does not stop new instance',async()=>{
 const directory=await mkdtemp(path.join(os.tmpdir(),'diag-stop-')),file=path.join(directory,'stop');let stop=()=>{};
 try {await writeFile(file,'a'.repeat(32));const initial=await stopRevision(file);let closed=0;stop=watchStop(initial,()=>closed++,file,10);await new Promise(r=>setTimeout(r,30));assert.equal(closed,0);await writeFile(file,'b'.repeat(32));await new Promise(r=>setTimeout(r,40));assert.equal(closed,1);assert.equal(await stopRevision(file),'b'.repeat(32));}
 finally {stop();await rm(directory,{recursive:true,force:true});}
});

import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
const root="C:\\Users\\admin\\Desktop\\AiDiy2026_dev";
const results=[];
for (const item of [{name:'avatar',folder:'frontend_avatar',entry:'dist-electron/._identity_probe.cjs'},{name:'diag',folder:'backend_diag',entry:'起動/._identity_probe.cjs'}]) {
 const result=await new Promise((resolve,reject)=>{const p=spawn(root+'/'+item.folder+'/node_modules/electron/dist/electron.exe',[root+'/'+item.folder+'/'+item.entry],{windowsHide:true,stdio:['ignore','pipe','pipe']});let out='',err='';p.stdout.on('data',x=>out+=x);p.stderr.on('data',x=>err+=x);p.on('error',reject);p.on('exit',code=>resolve({name:item.name,code,out,err}));});results.push(result);
}
await fs.writeFile(new URL('./electron-identity.json',import.meta.url),JSON.stringify(results,null,2));console.log(JSON.stringify(results));

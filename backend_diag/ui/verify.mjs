import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('.',import.meta.url));
async function files(directory){const result=[];for(const entry of await readdir(directory,{withFileTypes:true})){const filename=path.join(directory,entry.name);if(entry.name==='checks' && entry.isDirectory())continue;if(entry.isDirectory())result.push(...await files(filename));else result.push(filename);}return result;}
export async function manifest(directory=root){
  const names=[path.join(directory,'../../frontend_ide/src/共通表示/シアンバー.css'),...await files(path.join(directory,'src')),...await files(path.join(directory,'../runtime')),path.join(directory,'../モデル試行/defaults.mjs'),path.join(directory,'build.mjs'),path.join(directory,'package.json'),path.join(directory,'package-lock.json'),path.join(directory,'tsconfig.runtime.json'),...['app.js','style.css','index.html','AiDiy_diag.png',...['avatar','ide','term','code','live','discord'].map(id=>`AiDiy_${id}.png`)].map(name=>path.join(directory,'../static',name))];
  // Git の Windows checkout による CRLF だけを正規化。将来の画像等は生バイトで比較する。
  const entries=await Promise.all(names.map(async name=>{
    const relative=path.relative(directory,name).replaceAll('\\','/');
    const bytes=await readFile(name);
    const content=/\.(?:vue|ts|[cm]?js|css|html|json)$/.test(relative)?Buffer.from(bytes.toString('utf8').replace(/\r\n/g,'\n')):bytes;
    return [relative,createHash('sha256').update(content).digest('hex')];
  }));
  return Object.fromEntries(entries.sort(([a],[b])=>a<b?-1:a>b?1:0));
}
export async function verify(directory=root){
  try {
    const actual=await manifest(directory),expected=JSON.parse(await readFile(path.join(directory,'../static/build-manifest.json'),'utf8'));
    return expected!==null && typeof expected==='object' && !Array.isArray(expected) && Object.keys(actual).length===Object.keys(expected).length && Object.entries(actual).every(([name,hash])=>Object.hasOwn(expected,name) && expected[name]===hash);
  }catch{return false;}
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){if(!await verify()){console.error('Vue UI のソースと配布物が一致しません。backend_diag/ui で npm ci && npm run build を実行してください。');process.exitCode=1;}else console.log('Vue UI のソースと配布物は一致しています。');}

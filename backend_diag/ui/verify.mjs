import { createHash } from 'node:crypto';
import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('.',import.meta.url));
async function files(directory){const result=[];for(const entry of await readdir(directory,{withFileTypes:true})){const filename=path.join(directory,entry.name);if(entry.isDirectory())result.push(...await files(filename));else result.push(filename);}return result;}
export async function manifest(){const names=[...await files(path.join(root,'src')),path.join(root,'build.mjs'),path.join(root,'package.json'),path.join(root,'package-lock.json'),...['app.js','style.css','index.html'].map(name=>path.join(root,'../static',name))].sort();return Object.fromEntries(await Promise.all(names.map(async name=>[path.relative(root,name).replaceAll('\\','/'),createHash('sha256').update(await readFile(name)).digest('hex')])));}
export async function verify(){try{return JSON.stringify(await manifest())===JSON.stringify(JSON.parse(await readFile(path.join(root,'../static/build-manifest.json'),'utf8')));}catch{return false;}}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){if(!await verify()){console.error('Vue UI のソースと配布物が一致しません。backend_diag/ui で npm ci && npm run build を実行してください。');process.exitCode=1;}else console.log('Vue UI のソースと配布物は一致しています。');}

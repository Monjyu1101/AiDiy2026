// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import { build } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { mkdir, readFile, readdir, writeFile, cp } from 'node:fs/promises';
const root=fileURLToPath(new URL('../',import.meta.url));
await build({root,plugins:[vue()],define:{'process.env.NODE_ENV':JSON.stringify('production'),__VUE_OPTIONS_API__:true,__VUE_PROD_DEVTOOLS__:false,__VUE_PROD_HYDRATION_MISMATCH_DETAILS__:false},build:{emptyOutDir:false,lib:{entry:join(root,'src/main.js'),formats:['iife'],name:'AiDiyDevelopment',fileName:()=> 'app.js',cssFileName:'app'},rollupOptions:{output:{banner:'/*! COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors. Licensed under "AiDiy 公開利用ライセンス v1.1". Commercial use requires prior written consent from all copyright holders. See LICENSE for full terms. Thank you for keeping the rules. https://github.com/monjyu1101/AiDiy2026 */'}}}});
const template=await readFile(join(root,'index.html'),'utf8');
await writeFile(join(root,'dist/index.html'),template.replace('<script type="module" src="/src/main.js"></script>','<link rel="stylesheet" href="/development/app.css"><script src="/development/app.js" defer></script>'));
const notices=[];
for(const name of ['vue','@vue/shared','@vue/reactivity','@vue/runtime-core','@vue/runtime-dom','markdown-it','entities','linkify-it','mdurl','punycode.js','uc.micro']){
 const folder=join(root,'node_modules',name);let metadata;try{metadata=JSON.parse(await readFile(join(folder,'package.json'),'utf8'));}catch{continue;}
 for(const file of (await readdir(folder)).filter(name=>/^licen[sc]e/i.test(name)))notices.push(`${name} ${metadata.version}\n${await readFile(join(folder,file),'utf8')}`);
}
await writeFile(join(root,'dist/THIRD_PARTY_NOTICES.txt'),notices.join('\n\n'));
await cp(join(root,'LICENSE'),join(root,'dist/LICENSE'));
// 拡張には同じVue bundleを収録する。IDE専用の拡張は作らない。
const chatImages = ['sending.png', 'abort.png', 'speaker.png', 'microphone.png'];
for (const file of chatImages) await cp(join(root, ['speaker.png', 'microphone.png'].includes(file) ? 'host/aidiy_live/media' : 'host/media', file), join(root, 'dist', file));
for(const target of ['../host/dist/development','../host/aidiy_live/dist/development']){
 const output=fileURLToPath(new URL(target+'/',import.meta.url));await mkdir(output,{recursive:true});
 for(const file of ['app.js','app.css','AiDiy.png',...chatImages,'THIRD_PARTY_NOTICES.txt','LICENSE'])await cp(join(root,'dist',file),join(output,file));
}

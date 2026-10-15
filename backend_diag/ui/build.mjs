import { build } from 'esbuild';
import { parse, compileScript } from '@vue/compiler-sfc';
import { readFile, writeFile, copyFile, unlink } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { manifest } from './verify.mjs';
const root=fileURLToPath(new URL('.',import.meta.url));
// 配布用TSを既存esbuildで生成。利用者のNodeにTS実行機能は要求しない。
await build({entryPoints:['model_catalog','model_probe','model_runner'].map(name=>path.join(root,'../runtime',name+'.ts')),outdir:path.join(root,'../runtime'),outExtension:{'.js':'.mjs'},bundle:true,format:'esm',platform:'node',target:'node18'});
await build({entryPoints:[path.join(root,'src/main.js')],outfile:path.join(root,'../static/app.js'),bundle:true,minify:true,format:'esm',target:'es2020',legalComments:'eof',define:{'process.env.NODE_ENV':'"production"',__VUE_OPTIONS_API__:'false',__VUE_PROD_DEVTOOLS__:'false',__VUE_PROD_HYDRATION_MISMATCH_DETAILS__:'false'},plugins:[{name:'vue-sfc',setup(build){build.onLoad({filter:/\.vue$/},async({path:filename})=>{const source=await readFile(filename,'utf8');const {descriptor,errors}=parse(source,{filename});if(errors.length) throw errors[0];const compiled=compileScript(descriptor,{id:path.basename(filename),inlineTemplate:true});return {contents:compiled.content,loader:'js',resolveDir:path.dirname(filename)};});}}]});
await copyFile(path.join(root,'../static/app.css'),path.join(root,'../static/style.css'));
await unlink(path.join(root,'../static/app.css')); 
await copyFile(path.join(root,'src/index.html'),path.join(root,'../static/index.html'));
await writeFile(path.join(root,'../static/build-manifest.json'),JSON.stringify(await manifest(),null,2)+'\n');
console.log('Vue UI を static/ に生成しました。');

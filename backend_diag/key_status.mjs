// 診断専用 Python モデル判定を呼ぶ固定 bridge。Node は設定ファイル・APIキーを読み取らない。
import { access, stat, mkdtemp, rm } from 'node:fs/promises';
import { constants } from 'node:fs';
import { spawn } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
const ROOT=fileURLToPath(new URL('../',import.meta.url));
const SCRIPT=fileURLToPath(new URL('./model_probe.py',import.meta.url));
const active=new Set();
let stopping=false;
export const PYTHON_TIMEOUT=25000, OUTPUT_LIMIT=1024*1024;
export const KEY_PROVIDERS = Object.freeze([
  ['gemini','Gemini','gemini_key_id','google'],
  ['freeai','FreeAI（Gemini）','freeai_key_id','google'],
  ['claude','Claude','claude_key_id','anthropic'],
  ['openai','OpenAI API','openai_key_id','openai'],
  ['azure','Azure OpenAI','azure_key_id',null],
  ['copilot','GitHub Copilot','copilot_key_id',null],
  ['openrt','OpenRouter','openrt_key_id','openrouter'],
  ['ollama','Ollama Cloud','ollama_key_id','ollama'],
  ['huggingface_read','Hugging Face 読取','huggingface_key_read',null],
  ['huggingface_write','Hugging Face 書込','huggingface_key_write',null],
  ['discord','Discord Bot','DISCORD_BOT_TOKEN',null],
].map(([id,名前,キー名,probe]) => Object.freeze({id,名前,キー名,probe})));

export async function resolvePython(options={}) {
  const platform=options.platform || process.platform, env=options.env || process.env, root=options.root || ROOT;
  const suffix=platform==='win32'?'Scripts/python.exe':'bin/python';
  const candidates=[path.join(root,'backend_diag','.venv',suffix)];
  for(const directory of (env.PATH || '').split(platform==='win32'?';':':').filter(Boolean)) {
    for(const name of platform==='win32'?['python.exe','python3.exe']:['python3','python']) candidates.push(path.resolve(directory,name));
  }
  for(const candidate of candidates) {
    if(/[\\/]Microsoft[\\/]WindowsApps[\\/]python[^\\/]*\.exe$/i.test(candidate))continue;
    try{await access(candidate,platform==='win32'?constants.F_OK:constants.X_OK);if((await stat(candidate)).isFile())return candidate;}catch{}
  }
  return null;
}
export function pythonEnvironment(directory,env=process.env){
  const result={};for(const key of ['PATH','SystemRoot','WINDIR','LANG','LC_ALL'])if(env[key])result[key]=env[key];
  return {...result,HOME:directory,USERPROFILE:directory,XDG_CONFIG_HOME:directory,XDG_CACHE_HOME:directory,TEMP:directory,TMP:directory,TMPDIR:directory,NO_COLOR:'1',CI:'1'};
}
export function cancelKeyProbes(){stopping=true;for(const cancel of [...active])cancel();}
export async function runPython(action,id,options={}) {
  if(!['status','test','public'].includes(action) || (action==='test' && !KEY_PROVIDERS.some(p=>p.id===id)))return {error:'unsupported'};
  if(stopping)return {error:'stopped'};
  if(active.size>=2)return {error:'busy'};
  let directory;
  try {
    const executable=await (options.resolve || resolvePython)();
    if(!executable)return {error:'missing'};
    directory=await mkdtemp(path.join(os.tmpdir(),'aidiy-diag-model-'));
    if(stopping)return {error:'stopped'};
    if(active.size>=2)return {error:'busy'};
    return await new Promise(resolve=>{
      let child,timer,ended=false,size=0;const chunks=[];
      const kill=()=>{if(!child?.pid)return;try{if(process.platform!=='win32')(options.kill || process.kill)(-child.pid,'SIGKILL');else child.kill('SIGKILL');}catch{}};
      const finish=result=>{if(ended)return;ended=true;clearTimeout(timer);active.delete(cancel);kill();child?.stdout?.destroy();child?.stderr?.destroy();child?.unref();resolve(result);};
      const cancel=()=>finish({error:'stopped'});active.add(cancel);
      let input;try{input=action==='test'?JSON.stringify(options.input || {公開モデル:{},公開状態:'未取得'}):null;if(input && Buffer.byteLength(input)>OUTPUT_LIMIT)return finish({error:'input'});child=(options.spawn || spawn)(executable,['-I','-S','-B',SCRIPT,action,...(action==='test'?[id]:[])],{shell:false,cwd:directory,env:pythonEnvironment(directory),stdio:[action==='test'?'pipe':'ignore','pipe','pipe'],detached:process.platform!=='win32',windowsHide:true});}
      catch{return finish({error:'launch'});}
      if(action==='test'){try{child.stdin?.on('error',()=>finish({error:'input'}));child.stdin?.end(input);}catch{return finish({error:'input'});}}
      timer=setTimeout(()=>finish({error:'timeout'}),options.timeout ?? PYTHON_TIMEOUT);
      const read=(chunk,stdout)=>{if(ended)return;size+=chunk.length;if(size>(options.outputLimit ?? OUTPUT_LIMIT))return finish({error:'output'});if(stdout)chunks.push(chunk);};
      child.stdout.on('data',chunk=>read(chunk,true));child.stderr.on('data',chunk=>read(chunk,false));
      child.on('error',()=>finish({error:'launch'}));child.on('exit',kill);
      child.on('close',code=>{if(ended)return;if(code!==0)return finish({error:'failed'});try{finish({data:JSON.parse(Buffer.concat(chunks).toString('utf8'))});}catch{finish({error:'invalid'});}});
    });
  }catch{return {error:'launch'};}
  finally{if(directory)await rm(directory,{recursive:true,force:true,maxRetries:0}).catch(()=>{});}
}
const reason=code=>({missing:'Python が見つかりません。Python を準備してから再実行してください。',timeout:'Python のモデル確認がタイムアウトしました。',output:'Python の応答が上限を超えました。',busy:'別のキー確認が実行中です。',stopped:'診断を終了しました。'}[code] || 'Python の確認処理を利用できません。Python 環境と配布ファイルを確認してください。');
const text=(value,limit=1000)=>typeof value==='string'?value.slice(0,limit):'';
export async function getKeyStatus(options={}) {
  const response=await (options.run || runPython)('status');
  if(response.error || !Array.isArray(response.data?.項目))return {設定状態:'確認不可',説明:reason(response.error),項目:KEY_PROVIDERS.map(p=>({id:p.id,名前:p.名前,キー名:p.キー名,設定済み:null,状態:'未実施',キー不要:p.id==='openrt',説明:'設定有無は未確認です。',テスト可能:false,理由:reason(response.error)})),モデル:[]};
  return {設定状態:['読込済み','未作成','読込不可'].includes(response.data.設定状態)?response.data.設定状態:'読込不可',項目:KEY_PROVIDERS.map(p=>{
    const row=response.data.項目.find(r=>r && r.id===p.id) || {};
    return {id:p.id,名前:p.名前,キー名:p.キー名,設定済み:typeof row.設定済み==='boolean'?row.設定済み:null,状態:'未実施',キー不要:row.キー不要===true,説明:text(row.説明),テスト可能:row.テスト可能===true,理由:text(row.理由)};
  }),モデル:[]};
}
export async function testKey(id,options={}) {
  const result={id,状態:'未実施',説明:'未対応の項目です。',モデル:[],モデル詳細:[],確認日時:null};
  if(!KEY_PROVIDERS.some(p=>p.id===id && p.probe))return result;
  const response=await (options.run || runPython)('test',id,{input:options.publicCache || {公開モデル:{},公開状態:'未取得'}});
  if(response.error)return {...result,説明:reason(response.error)};
  const data=response.data;
  if(!data || data.id!==id || !['未実施','OK','NG'].includes(data.状態) || !Array.isArray(data.モデル))return {...result,説明:reason('invalid')};
  const models=[...new Set(data.モデル.filter(v=>typeof v==='string' && /^[a-zA-Z0-9][a-zA-Z0-9._:/@+\-]{0,199}$/.test(v)))].slice(0,500);
  const details=Array.isArray(data.モデル詳細)?data.モデル詳細.filter(row=>row && models.includes(row.model_id)).slice(0,500).map(row=>({model_id:row.model_id,作成日:text(row.作成日,20),トークン数:text(String(row.トークン数 ?? ''),30),モダリティ:text(row.モダリティ,200)})):[];
  return {...result,状態:data.状態,説明:text(data.説明),モデル:models,モデル詳細:details,確認日時:typeof data.確認日時==='string' && Number.isFinite(Date.parse(data.確認日時))?data.確認日時:null,一覧範囲:text(data.一覧範囲),補完:text(data.補完),警告:Array.isArray(data.警告)?data.警告.map(v=>text(v)).slice(0,5):[]};
}

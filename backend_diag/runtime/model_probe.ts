// 診断サーバー専用。固定設定の読取・モデル一覧GETのみ。キーを戻り値やログへ出さない。
import {open,stat} from 'node:fs/promises';
import {constants} from 'node:fs';
import {fileURLToPath} from 'node:url';
import https from 'node:https';
import {openrouterCatalog,googleCatalog,openaiCatalog,claudeCatalog,ollamaCatalog,pythonString,type Catalog} from './model_catalog';
export const CONFIG_LIMIT=128*1024, RESPONSE_LIMIT=1024*1024;
const CONFIG_PATH=fileURLToPath(new URL('../../_config/AiDiy_key.json',import.meta.url));
export const KEY_PROVIDERS=Object.freeze([
 ['gemini','Gemini','gemini_key_id','google'],['freeai','FreeAI（Gemini）','freeai_key_id','google'],
 ['claude','Claude','claude_key_id','anthropic'],['openai','OpenAI API','openai_key_id','openai'],
 ['azure','Azure OpenAI','azure_key_id',null],['copilot','GitHub Copilot','copilot_key_id',null],
 ['openrt','OpenRouter','openrt_key_id','openrouter'],['ollama','Ollama Cloud','ollama_key_id','ollama'],
 ['huggingface_read','Hugging Face 読取','huggingface_key_read',null],['huggingface_write','Hugging Face 書込','huggingface_key_write',null],
 ['discord','Discord Bot','DISCORD_BOT_TOKEN',null],
].map(([id,名前,キー名,probe])=>Object.freeze({id:id!,名前:名前!,キー名:キー名!,probe})));
export type Dictionary=Record<string,unknown>;
const record=(value:unknown):value is Dictionary=>value!==null&&typeof value==='object'&&!Array.isArray(value);
export type Reader=(path:string)=>Promise<string|Uint8Array>|string|Uint8Array;
export async function readConfig(reader?:Reader):Promise<[string,Dictionary]> {
 try {
  let raw:string|Uint8Array;
  if(reader)raw=await reader(CONFIG_PATH);
  else {
   // FIFO/device は開かない。事前確認後の置換も非blocking openとhandle側確認で防ぐ。
   const before=await stat(CONFIG_PATH);if(!before.isFile()||before.size>CONFIG_LIMIT)throw new Error('file');
   const handle=await open(CONFIG_PATH,constants.O_RDONLY|(constants.O_NONBLOCK??0));
   try{
    const info=await handle.stat();if(!info.isFile()||info.size>CONFIG_LIMIT)throw new Error('file');
    const bytes=Buffer.alloc(CONFIG_LIMIT+1);let total=0;
    while(total<bytes.length){const {bytesRead}=await handle.read(bytes,total,bytes.length-total,total);if(!bytesRead)break;total+=bytesRead;}
    raw=bytes.subarray(0,total);
   }finally{await handle.close();}
  }
  const bytes=typeof raw==='string'?Buffer.from(raw):Buffer.from(raw);
  if(bytes.length>CONFIG_LIMIT)throw new Error('size');
  const value:unknown=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes).replace(/^\uFEFF/,''));
  if(!record(value))throw new Error('shape');return ['読込済み',value];
 }catch(error){return [(error as NodeJS.ErrnoException)?.code==='ENOENT'?'未作成':'読込不可',{}];}
}
export function configured(value:unknown,id:string):value is string {return typeof value==='string'&&!!value.trim()&&!value.trim().startsWith('<')&&!(id==='ollama'&&value.trim().toLowerCase()==='ollama');}
export async function status({reader}:{reader?:Reader}={}) {
 const [state,values]=await readConfig(reader);
 return {設定状態:state,項目:KEY_PROVIDERS.map(p=>{
  const present=state==='読込不可'?null:configured(values[p.キー名],p.id),publicRow=p.id==='openrt';
  const reason=state==='読込不可'?'設定を読み取れません。':!present&&!publicRow?'キーが未設定です。':!p.probe?'この項目の接続テストは未対応です。':'';
  return {id:p.id,名前:p.名前,キー名:p.キー名,設定済み:present,キー不要:publicRow,状態:'未実施',理由:reason,テスト可能:state!=='読込不可'&&!!p.probe&&(!!present||publicRow),説明:publicRow?'起動時の公開モデル一覧キャッシュを表示します。キーの有効性は確認しません。':'設定有無のみ。接続は未確認です。'};
 }),モデル:[]};
}
const ENDPOINTS:Record<string,readonly [string,string]>={google:['generativelanguage.googleapis.com','/v1beta/models'],anthropic:['api.anthropic.com','/v1/models'],openai:['api.openai.com','/v1/models'],openrouter:['openrouter.ai','/api/v1/models'],ollama:['ollama.com','/v1/models']};
export type Fetch=(provider:string,headers:Record<string,string>,pageToken?:unknown,signal?:AbortSignal)=>Promise<Dictionary>;
export const fetchMetadata:Fetch=(provider,headers,pageToken,signal)=>new Promise((resolve,reject)=>{
 const endpoint=ENDPOINTS[provider];if(!endpoint)return reject(new Error('provider'));
 let pathname=endpoint[1];
 if(pageToken){if(provider!=='google'||typeof pageToken!=='string'||pageToken.length>4096)return reject(new Error('pagination'));pathname+='?'+new URLSearchParams({pageToken});}
 if(signal?.aborted)return reject(new Error('stopped'));
 let settled=false,size=0;const chunks:Buffer[]=[];
 // 専用 Agent を使わず agent:false。環境 proxy・globalAgent・redirect にキーを渡さない。
 const request=https.request({hostname:endpoint[0],path:pathname,port:443,method:'GET',agent:false,rejectUnauthorized:true,headers:{Accept:'application/json',...headers}},response=>{
  if(!response.statusCode||response.statusCode<200||response.statusCode>=300){response.destroy();return finish(new Error('http'));}
  response.on('data',(chunk:Buffer)=>{size+=chunk.length;if(size>RESPONSE_LIMIT)return finish(new Error('size'));chunks.push(chunk);});
  response.on('error',()=>finish(new Error('response')));
  response.on('end',()=>{try{const body:unknown=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(!record(body))throw new Error('shape');finish(undefined,body);}catch{finish(new Error('json'));}});
 });
 const cancel=()=>finish(new Error('stopped'));
 const timer=setTimeout(()=>finish(new Error('timeout')),8000);
 function finish(error?:Error,value?:Dictionary){if(settled)return;settled=true;clearTimeout(timer);signal?.removeEventListener('abort',cancel);request.destroy();if(error)reject(error);else resolve(value!);}
 signal?.addEventListener('abort',cancel,{once:true});request.on('error',()=>finish(new Error('network')));request.end();
});
export function safeDetails(models:Dictionary,secrets:string[],limit:number|null=500) {
 const result:Record<string,string|null>[]=[];
 for(const [id,entry] of Object.entries(models)) {
  if(!/^[A-Za-z0-9][A-Za-z0-9._:/@+\-]{0,199}$/.test(id)||!record(entry))continue;
  const values={...entry,model_id:id},cleaned:Record<string,string|null>={};
  for(const name of ['model_id','作成日','トークン数','モダリティ']){const value=values[name as keyof typeof values];let val=value==null?null:pythonString(value);if(val!==null&&(val.length>512||secrets.some(secret=>val!.includes(secret))))val=null;cleaned[name]=val;}
  if(cleaned.model_id!==null)result.push(cleaned);
 }
 return limit===null?result:result.slice(0,limit);
}
export function validatedCache(cache:unknown):[Catalog,boolean] {
 if(!record(cache)||cache.公開状態!=='取得済'||!record(cache.公開モデル)||Object.values(cache.公開モデル).some(value=>!record(value)))return [{},false];
 return [Object.fromEntries(safeDetails(cache.公開モデル,[],null).map(item=>[item.model_id,item])) as Catalog,true];
}
export async function publicCatalog({fetch=fetchMetadata,now,signal}:{fetch?:Fetch;now?:Date;signal?:AbortSignal}={}) {
 const timestamp=new Date().toISOString();
 try {
  const body=await fetch('openrouter',{},undefined,signal);if(!Array.isArray(body.data))throw new Error('shape');
  const details=safeDetails(openrouterCatalog(body,now),[],null);
  const result={状態:'OK',公開モデル:Object.fromEntries(details.map(item=>[item.model_id,item])),確認日時:timestamp,説明:'公開OpenRouter一覧の匿名取得成功。キーの有効性は未確認です。'};
  if(Buffer.byteLength(JSON.stringify(result))>RESPONSE_LIMIT)throw new Error('size');return result;
 }catch{return {状態:'NG',公開モデル:{},確認日時:timestamp,説明:'公開OpenRouter一覧を取得できませんでした。'};}
}
export async function probe(id:string,{reader,fetch=fetchMetadata,now,cache,signal}:{reader?:Reader;fetch?:Fetch;now?:Date;cache?:unknown;signal?:AbortSignal}={}) {
 const output={id,状態:'未実施',説明:'未対応の項目です。',モデル:[] as string[],モデル詳細:[] as Record<string,string|null>[],確認日時:null as string|null,警告:[] as string[]};
 const selected=KEY_PROVIDERS.find(row=>row.id===id);if(!selected?.probe)return output;
 const [router,ready]=validatedCache(cache);
 if(id==='openrt'){
  if(!ready)return {...output,説明:'起動時の公開OpenRouter一覧がまだ利用できません。キーのテストは未実施です。'};
  const details=safeDetails(router,[]);
  return {...output,状態:'OK',説明:'起動時の匿名取得結果を表示。キーの有効性・生成可否・課金状態は未確認です。',モデル:details.map(item=>item.model_id!),モデル詳細:details,確認日時:record(cache)&&typeof cache.確認日時==='string'?cache.確認日時:null,一覧範囲:'公開一覧のキャッシュ。最大500件。'};
 }
 const [state,values]=await readConfig(reader);if(state==='読込不可')return {...output,説明:'設定を読み取れません。'};
 const keyValue=values[selected.キー名];if(!configured(keyValue,id))return {...output,説明:'キーが未設定です。'};
 const key=keyValue.trim(),provider=selected.probe,timestamp=new Date().toISOString();
 const warnings=['google','openai','anthropic'].includes(provider)&&!ready?['起動時の公開OpenRouter一覧が利用できません。元のモデル処理と同じ空一覧時の処理で、日付・対応情報の補完なしで続行しました。']:[];
 try {
  const headers:Record<string,string>=provider==='google'?{'x-goog-api-key':key}:provider==='anthropic'?{'x-api-key':key,'anthropic-version':'2023-06-01'}:{Authorization:'Bearer '+key};
  if(provider==='openai'&&configured(values.openai_organization,''))headers['OpenAI-Organization']=values.openai_organization.trim();
  let body=await fetch(provider,headers,undefined,signal),models:Catalog;
  if(provider==='google'){
   if(!Array.isArray(body.models))throw new Error('shape');const entries=[...body.models];let token=body.nextPageToken,pages=1;
   while(token){if(pages>=20)throw new Error('pages');body=await fetch(provider,headers,token,signal);if(!Array.isArray(body.models))throw new Error('shape');entries.push(...body.models);token=body.nextPageToken;pages++;}
   models=googleCatalog(entries.map(item=>{if(!record(item)||typeof item.name!=='string'||(item.supportedGenerationMethods!==undefined&&(!Array.isArray(item.supportedGenerationMethods)||item.supportedGenerationMethods.some(x=>typeof x!=='string'))))throw new Error('shape');return {name:item.name,supported_actions:item.supportedGenerationMethods??[],input_token_limit:item.inputTokenLimit??null};}),router);
  }else {
   if(!Array.isArray(body.data))throw new Error('shape');
   if(provider==='openai')models=openaiCatalog(body.data.map(item=>{if(!record(item)||typeof item.id!=='string'||typeof item.created!=='number')throw new Error('shape');return {id:item.id,created:item.created};}),router,now);
   else if(provider==='anthropic')models=claudeCatalog({data:body.data.map(item=>{if(!record(item)||typeof item.id!=='string')throw new Error('shape');return {id:item.id,created_at:item.created_at};})},router,now);
   else models=ollamaCatalog(body,now);
  }
  const secrets=KEY_PROVIDERS.map(p=>values[p.キー名]).filter((value):value is string=>configured(value,'')).map(value=>value.trim());if(configured(values.openai_organization,''))secrets.push(values.openai_organization.trim());
  const details=safeDetails(models,secrets);
  return {...output,状態:'OK',モデル:details.map(item=>item.model_id!),モデル詳細:details,確認日時:timestamp,警告:warnings,説明:'モデル一覧API取得成功。元のモデル処理と同じ絞り込み・補完を適用。生成可否・課金状態は未確認です。',一覧範囲:'元のモデル処理を移植した取得モデルの絞り込み結果、表示は最大500件。静的・OAuth候補は含みません。',補完:['google','openai','anthropic'].includes(provider)?'起動時の公開OpenRouter一覧キャッシュを利用。テスト時の追加取得は行いません。':''};
 }catch{return {...output,状態:'NG',説明:'モデル一覧APIの通信または診断用モデル処理に失敗しました。',確認日時:timestamp,警告:warnings};}
}

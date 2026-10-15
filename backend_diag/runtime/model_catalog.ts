// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// AiDiy 公開利用ライセンス v1.1。詳細はリポジトリの LICENSE を参照。
// backend_server/conf/conf_model.py (blob 7b70e037c3c9e5624509a6a7678f6d104c188f9a)
// 由来の診断専用移植。I/O・OAuth・静的候補の補充なし。日付は元実装と同じローカル時刻。
export type Model = {model_id:string; トークン数:unknown; モダリティ:unknown; 作成日:string|null};
export type Catalog = Record<string,Model>;
const empty = ():Catalog => Object.create(null);
export const pythonString = (value:unknown):string => value === null || value === undefined ? 'None' : value === true ? 'True' : value === false ? 'False' : String(value);
function dateLabel(date:Date):string {
  if (!Number.isFinite(date.getTime())) throw new Error('date');
  return `${String(date.getFullYear()).padStart(4,'0')}/${String(date.getMonth()+1).padStart(2,'0')}/${String(date.getDate()).padStart(2,'0')}`;
}
// Python naive datetime - timedelta はローカル暦の日数演算（DST境界も維持）。
function cutoff(now:Date,days:number):number {const date=new Date(now);date.setDate(date.getDate()-days);return date.getTime()/1000;}
type RawRow = Record<string,unknown>;
function row(value:unknown):RawRow {if(value===null||typeof value!=='object'||Array.isArray(value))throw new Error('shape');return value as RawRow;}
function entries(body:unknown):unknown[] {const items=row(body).data??[];if(!Array.isArray(items))throw new Error('shape');return items;}
function number(value:unknown):number {if(typeof value!=='number'||!Number.isFinite(value))throw new Error('number');return value;}
function string(value:unknown):string {if(typeof value!=='string')throw new Error('string');return value;}
export function openrouterCatalog(body:unknown,now=new Date()):Catalog {
 const out=empty();
 for(const entry of entries(body)) {
  const item=row(entry);
  const id=string(item.id ?? ''),provider=id.includes('/')?id.split('/')[0].toLowerCase():'';
  const days=provider==='perplexity'?365:['google','openai','anthropic','x-ai'].includes(provider)?240:90;
  const created=number(Object.hasOwn(item,'created')?item.created:0);if(created<cutoff(now,days))continue;
  out[id]={model_id:id,トークン数:pythonString(Object.hasOwn(item,'context_length')?item.context_length:0),モダリティ:Object.hasOwn(row(Object.hasOwn(item,'architecture')?item.architecture:{}),'modality') ? row(item.architecture).modality : 'unknown',作成日:dateLabel(new Date(created*1000))};
 }
 return out;
}
export function googleCatalog(models:{name:string;supported_actions:string[];input_token_limit?:unknown}[],router:Catalog={}):Catalog {
 const out=empty();
 for(const model of models) {
  if(!model.supported_actions.includes('generateContent'))continue;
  const id=model.name.replaceAll('models/','');
  out[id]={model_id:id,トークン数:pythonString(Object.hasOwn(model,'input_token_limit')?model.input_token_limit:0),モダリティ:model.supported_actions.join(','),作成日:null};
 }
 if(Object.keys(router).length)for(const id of Object.keys(out)){
  const key=`google/${id}`;
  if(Object.hasOwn(router,key))out[id].作成日=router[key].作成日;
  else if(!id.toLowerCase().includes('live'))delete out[id];
 }
 return out;
}
export function openaiCatalog(models:{id:string;created:number}[],router:Catalog={},now=new Date()):Catalog {
 const out=empty();
 for(const model of models){if(model.created<cutoff(now,240))continue;out[model.id]={model_id:model.id,トークン数:'0',モダリティ:null,作成日:dateLabel(new Date(model.created*1000))};}
 if(Object.keys(router).length)for(const id of Object.keys(out)){
  const key=`openai/${id}`;
  if(Object.hasOwn(router,key)){out[id].トークン数=router[key].トークン数;out[id].モダリティ=router[key].モダリティ;}
  if(!id.toLowerCase().includes('realtime')&&out[id].トークン数==='0')delete out[id];
 }
 return out;
}
function claudeDate(value:unknown):{timestamp:number|null;label:string|null}{
 if(!value)return {timestamp:null,label:null};
 try {
  if(value instanceof Date)return {timestamp:value.getTime()/1000,label:dateLabel(value)};
  // ISO の作成日は UTC への変換前の日付。fromisoformat と同様、不正な日付は不明扱い。
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/.test(value))throw new Error('date');
  const [year,month,day]=value.slice(0,10).split('-').map(Number);
  const check=new Date(Date.UTC(year,month-1,day));
  if(check.getUTCFullYear()!==year||check.getUTCMonth()!==month-1||check.getUTCDate()!==day)throw new Error('date');
  const parsed=new Date(value.length===10?value+'T00:00:00':value);
  if(!Number.isFinite(parsed.getTime()))throw new Error('date');
  return {timestamp:parsed.getTime()/1000,label:value.slice(0,10).replaceAll('-','/')};
 }catch{return {timestamp:null,label:null};}
}
export function claudeCatalog(models:{data:{id:string;created_at?:unknown}[]},router:Catalog={},now=new Date()):Catalog {
 const out=empty();
 for(const model of models.data){const created=claudeDate(model.created_at);if(created.timestamp!==null&&created.timestamp<cutoff(now,240))continue;out[model.id]={model_id:model.id,トークン数:'0',モダリティ:null,作成日:created.label};}
 if(Object.keys(router).length)for(const id of Object.keys(out)){
  let normalized=id;
  if(normalized.length>=9&&normalized.slice(-9,-8)==='-'&&normalized.slice(-8,-6)==='20')normalized=normalized.slice(0,-9);
  if(normalized.length>=3&&normalized.at(-2)==='-'&&['3','4','5'].includes(normalized.at(-3)!)&&/^\p{Nd}$/u.test(normalized.at(-1)!))normalized=normalized.slice(0,-3)+normalized.at(-3)+'.'+normalized.at(-1);
  const key=`anthropic/${normalized}`;
  if(Object.hasOwn(router,key)){out[id].トークン数=router[key].トークン数;out[id].モダリティ=router[key].モダリティ;}
 }
 return out;
}
export function ollamaCatalog(body:unknown,now=new Date()):Catalog {
 const out=empty();
 const models=entries(body).filter((item):item is RawRow=>item!==null&&typeof item==='object'&&!Array.isArray(item));
 models.sort((a,b)=>number(b.created||0)-number(a.created||0));
 for(const model of models){if(!model.id||!model.created||number(model.created)<cutoff(now,240))continue;const id=string(model.id);let label='yyyy/mm/dd';try{label=dateLabel(new Date(Math.trunc(number(model.created))*1000));}catch{}out[id]={model_id:id,トークン数:'0',モダリティ:null,作成日:label};}
 return out;
}

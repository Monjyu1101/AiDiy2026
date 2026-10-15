// 期限・同時実行・キャンセルをすべてのモデル処理に適用。子プロセスやPython不要。
import {status,probe,publicCatalog,KEY_PROVIDERS,RESPONSE_LIMIT,type Reader,type Fetch} from './model_probe';
export type RunOptions={reader?:Reader;fetch?:Fetch;input?:unknown;now?:Date;timeout?:number;signal?:AbortSignal};
type Response={data?:unknown;error?:string};
export function createModelRunner(){
 const active=new Set<AbortController>();let stopping=false;
 const cancel=()=>{stopping=true;for(const controller of active)controller.abort();};
 const run=async(action:string,id?:string,options:RunOptions={}):Promise<Response>=>{
  if(!['status','public','test'].includes(action)||(action==='test'&&!KEY_PROVIDERS.some(p=>p.id===id)))return {error:'unsupported'};
  if(stopping||options.signal?.aborted)return {error:'stopped'};
  if(active.size>=2)return {error:'busy'};
  const controller=new AbortController();active.add(controller);
  let timeout=false,timer:ReturnType<typeof setTimeout>|undefined;
  const externalAbort=()=>controller.abort();options.signal?.addEventListener('abort',externalAbort,{once:true});
  try {
   if(action==='test'&&Buffer.byteLength(JSON.stringify(options.input??{}))>RESPONSE_LIMIT)return {error:'input'};
   return await new Promise<Response>(resolve=>{
    let ended=false;
    const finish=(result:Response)=>{if(ended)return;ended=true;controller.signal.removeEventListener('abort',aborted);resolve(result);};
    const aborted=()=>finish({error:timeout?'timeout':'stopped'});
    controller.signal.addEventListener('abort',aborted,{once:true});
    timer=setTimeout(()=>{timeout=true;controller.abort();},options.timeout??25000);
    const injected={...options,cache:options.input,signal:controller.signal};
    Promise.resolve().then<unknown>(()=>action==='status'?status(injected):action==='public'?publicCatalog(injected):probe(id!,injected)).then(data=>{
     try {if(Buffer.byteLength(JSON.stringify(data))>RESPONSE_LIMIT)return finish({error:'output'});finish({data});}catch{finish({error:'output'});}
    },()=>finish({error:'failed'}));
   });
  }catch{return {error:'input'};}
  finally{clearTimeout(timer);options.signal?.removeEventListener('abort',externalAbort);active.delete(controller);controller.abort();}
 };
 return {run,cancel};
}
const runner=createModelRunner();
export const runModels=runner.run,cancelKeyProbes=runner.cancel;

// 手動の config モデル試行専用。起動・全診断・headless からは呼ばない。
import http from 'node:http';
import {createHmac, randomBytes} from 'node:crypto';
import {readConfig} from '../runtime/model_probe.mjs';
import {getToolsStatus} from '../診断/tools_status.mjs';
import {createAudioStore,validateAudio} from './audio_store.mjs';
import {FREEAI_DECISION_MODEL} from '../モデル情報/decisions_info.mjs';

// Live: 接続20秒 + 安定待ち10秒 + 応答30秒 + cleanup9秒 + 通信余裕。
export const LIVE_HTTP_TIMEOUT_MS=75000;
export const TRIAL_ROW_TIMEOUT_MS=90000;
export const TRIAL_RUN_TTL_MS=30*60*1000;

const CHAT = {gemini_chat:'GEMINI',freeai_chat:'FREEAI',openrt_chat:'OPENRT',openai_chat:'OPENAI',openai_oauth:'OPENAI',ollama_chat:'OLLAMA',local_chat:'LOCAL'};
const LIVE = {gemini_live:'GEMINI',freeai_live:'FREEAI',openai_live:'OPENAI'};
const DECISION = new Set(['auto','openai_oauth','openai_jsonchat','freeai_chat','openai_decisions','gemini_chat']);
export const DECISION_CHOICES=Object.freeze(['high','medium','low']);
const decisionQuestions=()=>[{type:'choice',name:'politeness',instructions:'入力の挨拶としての丁寧さをhigh（丁寧）、medium（普通）、low（くだけた表現）から選んでください。',choices:DECISION_CHOICES.map(value=>({value}))}];
const CODE = new Set(['auto','same','claude_sdk','claude_cli','claude_ollama','copilot_cli','codex_cli','codex_ollama','antigravity_cli','grok_cli','opencode_cli','aidiy_hermes']);
const text = value => typeof value === 'string' ? value.trim() : '';
const label = value => /^[\w./:@+-]{1,180}$/.test(text(value)) && !/^(?:sk-|AIza|Bearer )/i.test(text(value)) ? text(value) : '';
const failure = (message, status=409) => Object.assign(new Error(message),{status,trialFailure:true});
const sharedKey = row => JSON.stringify([row.区分==='CHAT'?'chat':row.区分==='LIVE'?'live':row.区分==='DECISION'?'decision':'code',row.プロバイダ,row.モデル,row.音声]);
function portOf(config) {const value=config.PORT_TOOLS ?? 8095;const port=Number(value);return /^(?:[1-9]\d*)$/.test(String(value)) && Number.isInteger(port) && port<=65535 ? port : 0;}
export function configRows(config) {
  const rows=[];
  const secrets=new Set(Object.entries(config).filter(([key,value])=>/key|token|secret|password/i.test(key) && typeof value==='string' && value.length>=4).map(([,value])=>value));
  function add(id, family, role, provider, model, voice='', inherited='') {
    const safe=value=>[...secrets].some(secret=>text(value).includes(secret))?'':label(value);
    provider=safe(provider);model=safe(model);voice=safe(voice);
    const supported=family==='CHAT' ? Object.hasOwn(CHAT,provider) : family==='LIVE' ? Object.hasOwn(LIVE,provider) : family==='DECISION' ? DECISION.has(provider) : CODE.has(provider);
    const state=provider && !supported ? '未対応' : !provider || !model || (family==='LIVE' && !voice) ? '未設定' : '未実行';
    rows.push({id,区分:family,役割:role,プロバイダ:provider,モデル:model,音声:voice,継承元:inherited,状態:state,説明:state==='未設定'?'設定値が不足または不正です。':state==='未対応'?'このプロバイダは試行に対応していません。':''});
  }
  const chat=text(config.CHAT_AI_NAME),live=text(config.LIVE_AI_NAME);
  add('CHAT','CHAT','会話',chat,config[`CHAT_${CHAT[chat]}_MODEL`]);
  add('LIVE','LIVE','音声会話',live,config[`LIVE_${LIVE[live]}_MODEL`],config[`LIVE_${LIVE[live]}_VOICE`]);
  const decision=text(config.DECISION_AI_NAME)||'auto';
  add('DECISION','DECISION','挨拶の丁寧さ',decision,decision==='freeai_chat'?FREEAI_DECISION_MODEL:text(config.DECISION_AI_MODEL)||'auto');
  for(let i=1;i<=6;i++){const inherit=i>1 && config[`CODE_AI${i}_NAME`]==='auto';const n=inherit?1:i;add(`CODE${i}`,'CODE',`CODE${i}`,config[`CODE_AI${n}_NAME`],config[`CODE_AI${n}_MODEL`],'',inherit?'CODE1':'');}
  for(const family of ['TASK','TEAM'])for(const phase of ['plan','do','check'])add(`${family}_${phase}`,family,phase,config[`${family}_AI_NAME`],config[`${family}_AI_MODEL_${phase}`]);
  return rows.map(row=>({...row,共有対象:rows.filter(other=>other.id===row.id || (row.状態==='未実行' && other.状態==='未実行' && sharedKey(other)===sharedKey(row))).map(other=>other.id)}));
}

// Tools の文字列戻り値は MCPServer が structuredContent: {result: '<JSON>'} に包む。
// オブジェクト形式や従来のテキスト形式も、内側の会話結果を取り出して判定する。
function toolPayload(result) {
  const object=value=>value && typeof value==='object' && !Array.isArray(value);
  if(object(result?.structuredContent)){
    const structured=result.structuredContent;
    if(typeof structured.status==='string')return structured;
    if(typeof structured.result==='string')try{const parsed=JSON.parse(structured.result);if(object(parsed))return parsed;}catch{}
  }
  for(const content of result?.content || [])if(content.type==='text')try{const parsed=JSON.parse(content.text);if(object(parsed))return parsed;}catch{}
  throw failure('MCP の試行結果を読み取れません。');
}

// 固定 loopback、リダイレクトなし、応答上限。JSON と MCP SSE の双方を処理する。
export function localRequest({port,path,method='POST',body,headers={},signal,id,timeoutMs=TRIAL_ROW_TIMEOUT_MS,responseLimit=1024*1024}) {
  return new Promise((resolve,reject)=>{
    let req,res,done=false,size=0,buffer='';
    const finish=(error,value)=>{if(done)return;done=true;clearTimeout(timer);signal?.removeEventListener('abort',abort);res?.destroy();req?.destroy();error?reject(error):resolve(value);};
    const abort=()=>finish(failure('試行を中止しました。'));
    const timer=setTimeout(()=>finish(failure('応答が制限時間を超えました。')),timeoutMs);
    signal?.addEventListener('abort',abort,{once:true});if(signal?.aborted)return abort();
    const bytes=body===undefined?undefined:Buffer.from(JSON.stringify(body));
    req=http.request({hostname:'127.0.0.1',port,path,method,agent:false,maxHeaderSize:8192,headers:{Accept:'application/json, text/event-stream',...(bytes?{'Content-Type':'application/json','Content-Length':bytes.length}:{}),...headers}},incoming=>{
      res=incoming;
      if(incoming.statusCode<200 || incoming.statusCode>=300)return finish(failure('Tools が要求を受け付けませんでした。'));
      const session=incoming.headers['mcp-session-id'];
      if(session!==undefined && (typeof session!=='string' || !/^[\x21-\x7e]{1,256}$/.test(session)))return finish(failure('MCP セッションが不正です。'));
      const sse=String(incoming.headers['content-type']).includes('text/event-stream');
      const accept=value=>{if(id!==undefined && value?.id!==id)return false;finish(null,{body:value,session});return true;};
      incoming.setEncoding('utf8');
      incoming.on('data',chunk=>{
        size+=Buffer.byteLength(chunk);if(size>responseLimit)return finish(failure('Tools 応答が上限を超えました。'));
        buffer+=chunk;
        if(sse){buffer=buffer.replace(/\r\n/g,'\n');let end;while((end=buffer.indexOf('\n\n'))>=0){const event=buffer.slice(0,end);buffer=buffer.slice(end+2);const data=event.split('\n').filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trimStart()).join('\n');if(data)try{if(accept(JSON.parse(data)))return;}catch{return finish(failure('MCP 応答を読み取れません。'));}}}
      });
      incoming.on('end',()=>{if(done)return;if(!buffer.trim() && id===undefined)return finish(null,{body:null,session});try{if(!sse && accept(JSON.parse(buffer)))return;}catch{}finish(failure('MCP 応答を読み取れません。'));});
      incoming.on('error',()=>finish(failure('Tools との通信が切断されました。')));
      incoming.on('aborted',()=>finish(failure('Tools との通信が切断されました。')));
    });
    req.on('error',()=>finish(failure('Tools に接続できません。')));req.end(bytes);
  });
}
export async function callMcp(row, config, {signal,request=localRequest}={}) {
  const chat=row.区分==='CHAT',decision=row.区分==='DECISION',path=decision?'/aidiy_decisions_check/mcp':chat?'/aidiy_chat_llms/mcp':'/aidiy_code_agents/mcp',port=portOf(config);
  let session,protocol='2024-11-05';
  const headers=()=>({'MCP-Protocol-Version':protocol,...(session?{'Mcp-Session-Id':session}:{})});
  const rpc=async(id,method,params)=>{const response=await request({port,path,signal,id,headers:headers(),body:{jsonrpc:'2.0',...(id===undefined?{}:{id}),method,params}});session=response.session || session;if(id!==undefined && response.body?.jsonrpc!=='2.0')throw failure('MCP 応答が不正です。');if(response.body?.error)throw failure('MCP ツールの実行に失敗しました。');return response.body?.result;};
  try {
    const init=await rpc(1,'initialize',{protocolVersion:protocol,capabilities:{},clientInfo:{name:'aidiy-diag',version:'1.0'}});
    if(!init || !['2024-11-05','2025-03-26','2025-06-18'].includes(init.protocolVersion))throw failure('MCP 初期化に失敗しました。');protocol=init.protocolVersion;
    await rpc(undefined,'notifications/initialized',{});
    // 既存 MCP の通常契約だけを使う。診断専用 provider / CLI / 認証経路は作らない。
    const option=(key,allowed,fallback='auto')=>allowed.includes(config[key])?config[key]:fallback;
    const args=decision?{input:'おはよう',questions:decisionQuestions(),ai_name:row.プロバイダ,ai_model:row.モデル,timeout_sec:60}:{prompt:'おはよう',ai_name:row.プロバイダ,ai_model:row.モデル,resume:false,timeout_sec:60,...(chat?{use_tools:false,session_id:`diag_${randomBytes(12).toString('hex')}`}:{code_permissions:option('CODE_PERMISSIONS',['auto','full','none']),self_check_loop:0})};
    const result=await rpc(2,'tools/call',{name:decision?'decisions_check':chat?'chat_llms_run':'code_agents_run',arguments:args});
    if(result?.isError)throw failure('MCP ツールがエラーを返しました。');
    return toolPayload(result);
  } finally {
    // 中止時も独立した短い期限でセッションを破棄する。
    if(session)try{await request({port,path,method:'DELETE',headers:headers(),timeoutMs:1500});}catch{}
  }
}
// MCP成功だけではOKにしない。選択値は3値すべてを許容し、意味的な正解は固定しない。
export function decisionAnswer(payload) {
  const answers=payload?.data?.answers;
  const invalid=()=>failure('判断応答のJSON形式が不正です。high / medium / low のchoice回答を確認できませんでした。');
  if(payload?.status!=='OK'||!Array.isArray(answers)||answers.length!==1)throw invalid();
  const answer=answers[0],probability=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=1;
  if(answer?.type!=='choice'||answer.name!=='politeness'||!DECISION_CHOICES.includes(answer.choice)||!probability(answer.confidence)||!Array.isArray(answer.probabilities)||answer.probabilities.length!==3)throw invalid();
  if(new Set(answer.probabilities.map(item=>item?.value)).size!==3||answer.probabilities.some(item=>!DECISION_CHOICES.includes(item?.value)||!probability(item?.probability))||Math.abs(answer.probabilities.reduce((sum,item)=>sum+item.probability,0)-1)>1e-4)throw invalid();
  return {type:answer.type,name:answer.name,choice:answer.choice,probabilities:answer.probabilities.map(({value,probability})=>({value,probability})),confidence:answer.confidence};
}
function redact(value,config) {
  let result=text(value);
  for(const [key,secret] of Object.entries(config))if(/key|token|secret|password/i.test(key) && typeof secret==='string' && secret.length>=4)result=result.split(secret).join('[非表示]');
  return result.replace(/\b(?:sk-[\w-]{8,}|AIza[\w-]{15,}|Bearer\s+\S+)\b/gi,'[非表示]').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'').slice(0,1500);
}
export function createModelTrials({reader,statusFn=getToolsStatus,request=localRequest,timeoutMs=TRIAL_ROW_TIMEOUT_MS,audioStore=createAudioStore()}={}) {
  const salt=randomBytes(32);let run;
  const snapshot=async()=>{const [state,config]=await readConfig(reader);const version=createHmac('sha256',salt).update(JSON.stringify(config)).digest('hex');return {state,config,version,rows:configRows(config)};};
  const publicSnapshot=s=>({版:s.version,項目:s.rows});
  function cancel(preserveAudio=false){if(run){const id=run.id;run.controller.abort();clearTimeout(run.timer);run=null;if(!preserveAudio)void audioStore.clear(id).catch(()=>{});}}
  return {
    async snapshot(){return publicSnapshot(await snapshot());},
    async start({signal,rowId}={}) {
      if(run)throw failure('前の試行を終了してから開始してください。');
      // 準備中も占有し、同時の開始を拒否する。
      const current={id:randomBytes(16).toString('hex'),controller:new AbortController(),cache:new Map(),index:0,busy:false};run=current;
      const abort=()=>current.controller.abort();signal?.addEventListener('abort',abort,{once:true});
      try {await audioStore.clear();if(signal?.aborted)abort();const s=await snapshot();if(s.state!=='読込済み' || !portOf(s.config))throw failure('設定ファイルを読み取れません。');const queue=rowId===undefined?s.rows:s.rows.filter(row=>row.id===rowId);if(!queue.length)throw failure('設定項目が見つかりません。',404);if(!(await statusFn({signal:current.controller.signal})).online || current.controller.signal.aborted)throw failure('Tools に接続してください。');Object.assign(current,s,{queue});current.timer=setTimeout(cancel,TRIAL_RUN_TTL_MS);current.timer.unref?.();return {実行ID:current.id,実行順:queue.map(row=>row.id),...publicSnapshot(s)};}
      catch(error){if(run===current)cancel();throw error;}finally{signal?.removeEventListener('abort',abort);}
    },
    cancel(id){if(run?.id!==id)throw failure('試行が見つかりません。',404);cancel();return {状態:'中止'};},
    async next(id,rowId,{signal}={}) {
      const current=run;if(!current || current.id!==id || !current.rows)throw failure('試行が見つかりません。',404);
      if(current.busy)throw failure('モデル試行は順番に実行してください。');
      const row=current.queue[current.index];if(row?.id!==rowId)throw failure('モデル試行の順序が一致しません。');
      const key=sharedKey(row);
      current.busy=true;const started=Date.now(),abort=()=>current.controller.abort();signal?.addEventListener('abort',abort,{once:true});
      let timedOut=false;const timer=setTimeout(()=>{timedOut=true;abort();},timeoutMs);if(signal?.aborted)abort();
      try {
        const latest=await snapshot();if(latest.version!==current.version){cancel();throw Object.assign(failure('設定が変更されました。読み直して開始してください。'),{configChanged:true});}
        const base={id:row.id,状態:row.状態,応答:'',実行モデル:'',共有元:'',所要ms:0,説明:row.説明};
        if(current.controller.signal.aborted)throw failure('試行を中止しました。');
        if(row.状態!=='未実行')return base;
        // 同じ設定版・固定オプションでのみ共有。CHAT/LIVE は CODE 系と混ぜない。
        if(current.cache.has(key)){const prior=current.cache.get(key);return {...prior,id:row.id,共有元:prior.id,所要ms:0};}
        let payload;
        if(row.区分==='LIVE')payload=(await request({port:portOf(current.config),path:'/internal/live_model_check',body:{},headers:{'X-AiDiy-Diag':'model-trial'},signal:current.controller.signal,timeoutMs:LIVE_HTTP_TIMEOUT_MS,responseLimit:3*1024*1024})).body;
        else payload=await callMcp(row,current.config,{signal:current.controller.signal,request});
        if(current.controller.signal.aborted)throw failure('試行を中止しました。');
        if((await snapshot()).version!==current.version){cancel();throw Object.assign(failure('設定が変更されました。読み直して開始してください。'),{configChanged:true});}
        if(row.区分==='DECISION'){
          const answer=decisionAnswer(payload);
          const result={...base,状態:'OK',判断結果:answer.choice,応答:JSON.stringify(answer,null,2),実行モデル:label(redact(payload.data.model||payload.data.ai_model,current.config)),所要ms:Date.now()-started,説明:`挨拶の丁寧さ: ${answer.choice}（JSON回答形式を確認。選択内容の正誤判定は行いません）`};
          current.cache.set(key,result);return result;
        }
        const answer=text(payload?.result ?? payload?.reply),textOk=payload?.status==='OK' && !!answer && !['（応答なし）','(応答なし)','!'].includes(answer) && !/^(?:(?:api|ClaudeSDK|Copilot|subprocess)?実行エラー:|(?:Local |Ollama )?ChatAIが停止状態です。|処理タイムアウト\([0-9.]+秒\)が発生しました。|処理がキャンセルされました。|OpenAI OAuth 初期化エラー:|エラー[:：]|error[:：]|exception[:：]|traceback|APIエラー[:：]|認証エラー[:：]|接続エラー[:：]|\[error\])/i.test(answer);
        let audio;
        const live=row.区分==='LIVE';
        if(live && payload?.status==='OK')try{validateAudio(payload.audio);audio=await audioStore.put(payload.audio,current.id);}catch{}
        if(current.controller.signal.aborted || run!==current){await audioStore.clear(current.id);throw failure('試行を中止しました。');}
        if((await snapshot()).version!==current.version){cancel();throw Object.assign(failure('設定が変更されました。読み直して開始してください。'),{configChanged:true});}
        const ok=textOk || (live && !!audio);
        const actual=row.区分==='LIVE'?payload?.model:row.区分==='CHAT'?payload?.ai_model:payload?.selected_model;
        const result={...base,状態:ok?'OK':payload?.status==='UNSUPPORTED'?'未対応':'NG',応答:ok && textOk?redact(answer,current.config):'',...(audio?{音声ファイル:audio}:{}),実行モデル:['auto','same'].includes(text(actual))?'':label(redact(actual,current.config)),所要ms:Date.now()-started,説明:ok?(audio?'音声応答を確認しました。':''):live?'有効な会話応答または1秒以上の音声応答を確認できませんでした。':payload?.status==='UNSUPPORTED'?'接続先 MCP はこのプロバイダに対応していません。':`有効な会話応答を確認できませんでした。${answer?`（${redact(answer,current.config).slice(0,300)}）`:''}`};
        current.cache.set(key,result);return result;
      }catch(error){if(error?.configChanged)throw error;if(current.controller.signal.aborted){if(run===current)cancel();const timeout=timedOut&&row.区分==='DECISION';return {id:row.id,状態:timeout?'NG':'中止',...(timeout?{実行終了:true}:{}),応答:'',実行モデル:'',共有元:'',所要ms:Date.now()-started,説明:timeout?'判断試行が制限時間を超えました。':'試行を中止しました。'};}if(run!==current)throw error;const result={id:row.id,状態:'NG',応答:'',実行モデル:'',共有元:'',所要ms:Date.now()-started,説明:error?.trialFailure?error.message:row.区分==='DECISION'?'Tools から判断応答を取得できませんでした。':'Tools から会話応答を取得できませんでした。'};current.cache.set(key,result);return result;}
      finally {clearTimeout(timer);signal?.removeEventListener('abort',abort);current.busy=false;current.index++;if(current.index>=current.queue.length && run===current)cancel(true);}
    },
    audio:id=>audioStore.get(id),
    close(){cancel();return audioStore.close().catch(()=>{});},
  };
}

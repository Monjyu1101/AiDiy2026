import {createServer} from '../diag_main.mjs';
import {catalog} from '../probes.mjs';
const entries=await catalog();
const publicCache={snapshot:()=>({状態:'取得済',件数:1,世代:2,説明:'公開モデル取得済（synthetic）'}),input:()=>({公開モデル:{'fixture/model':{model_id:'fixture/model'}},公開状態:'取得済',確認日時:new Date().toISOString()}),refresh:async()=>publicCache.snapshot()};
const server=createServer({publicCache,token:'synthetic-ui-test',prefix:'/proxy/8097/',entries,coverage:{complete:true,sourceTargetFiles:3333,scannedSourceFiles:3333},scanFn:async()=>{await new Promise(r=>setTimeout(r,100));return entries.map(e=>({id:e.id,状態:'OK',説明:'synthetic'}));},keyStatusFn:async()=>({設定状態:'読込済み',項目:[{id:'openai',名前:'OpenAI API',キー名:'openai_key_id',設定済み:true,説明:'設定有無のみ。',テスト可能:true},{id:'azure',名前:'Azure OpenAI',キー名:'azure_key_id',設定済み:false,テスト可能:false,理由:'キーが未設定です。'},{id:'openrt',名前:'OpenRouter',キー名:'openrt_key_id',設定済み:true,キー不要:true,説明:'公開一覧取得、キーの有効性は未確認。',テスト可能:true}]}),keyTestFn:async id=>{await new Promise(r=>setTimeout(r,100));return {id,状態:'OK',説明:'synthetic API success',モデル:['gpt-synthetic','<script>alert(1)</script>'],確認日時:new Date().toISOString()};}});
server.listen(0,'127.0.0.1',()=>console.log(server.address().port));
process.on('SIGTERM',()=>{server.close();server.closeAllConnections();});

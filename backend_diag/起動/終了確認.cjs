'use strict';
const http=require('node:http');

function 起動状態を読む(value){
 const url=new URL(value),token=new URLSearchParams(url.hash.slice(1)).get('token');
 if(url.protocol!=='http:'||url.hostname!=='127.0.0.1'||!url.port||!token)throw new Error('invalid status URL');
 const endpoint=new URL('api/'+encodeURIComponent('起動'),url);endpoint.hash='';
 return new Promise((resolve,reject)=>{
  const request=http.get(endpoint,{agent:false,headers:{Authorization:'Bearer '+token}},response=>{
   if(response.statusCode!==200){response.resume();reject(new Error('status unavailable'));return;}
   let body='';response.setEncoding('utf8');response.on('data',chunk=>{body+=chunk;if(body.length>65536)request.destroy(new Error('status too large'));});
   response.on('error',reject);response.on('end',()=>{try{const state=JSON.parse(body);if(typeof state.終了時停止あり!=='boolean')throw new Error('invalid status');resolve(state);}catch(error){reject(error);}});
  });
  const timer=setTimeout(()=>request.destroy(new Error('status timeout')),3000);
  request.on('error',reject);request.on('close',()=>clearTimeout(timer));
 });
}

function 終了確認を作成({window,状態取得,確認}){
 let allowed=false,pending=false;
 async function check(){
  try{
   let running;
   try{const state=await 状態取得();if(typeof state?.終了時停止あり!=='boolean')throw new Error('invalid status');running=state.終了時停止あり;}catch{running=null;}
   if(allowed||window.isDestroyed())return;
   if(running!==false){
    const result=await 確認(window,{
     type:'question',title:'AiDiy Diag の終了',
     message:running===true?'起動中のプロセスを停止して Diag を閉じますか？':'起動状態を確認できません。Diag を閉じますか？',
     detail:'この Diag から起動したプロセスも停止します。',
     buttons:['停止して閉じる','キャンセル'],defaultId:1,cancelId:1,noLink:true,
    });
    if(result.response!==0)return;
   }
   if(!window.isDestroyed()){allowed=true;window.close();}
  }catch{
   // 確認画面を表示できなければ閉じず、次の操作で再試行する。
  }finally{pending=false;}
 }
 window.on('close',event=>{if(allowed)return;event.preventDefault();if(!pending){pending=true;void check();}});
 return {許可(){allowed=true;}};
}

module.exports={起動状態を読む,終了確認を作成};

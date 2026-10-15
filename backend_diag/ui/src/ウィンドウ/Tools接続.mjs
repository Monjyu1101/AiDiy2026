// Term と同じ ping のみ。無効化・切断・画面破棄時は古い応答を反映しない。
export function Tools接続を作成({api,反映,間隔=10000,setTimer=setTimeout,clearTimer=clearTimeout}) {
 let enabled=true,connected=false,disposed=false,generation=0,timer,controller;
 const reset=()=>{generation++;clearTimer(timer);controller?.abort();controller=undefined;反映({online:false,checking:false});};
 async function refresh(){
  reset();if(disposed||!enabled||!connected)return;
  const current=generation;controller=new AbortController();反映({online:false,checking:true});
  try{const data=await api('api/tools-status','GET',controller.signal);if(current===generation&&!disposed)反映({online:data.online===true,checking:false});}
  catch{if(current===generation&&!disposed)反映({online:false,checking:false});}
  finally{if(current===generation&&!disposed&&enabled&&connected){controller=undefined;timer=setTimer(refresh,間隔);}}
 }
 return {refresh,接続(value){connected=value;void refresh();},有効(value){enabled=value;void refresh();},終了(){disposed=true;reset();}};
}

'use strict';
const {Macメニューを設定:共通メニュー}=require('../../frontend_ide/host/scripts/MacOS-Menu.cjs');

const アプリ名='AiDiy 診断';

function Macメニューを設定({app,Menu,window,icon,platform=process.platform}){
 if(platform!=='darwin')return;
 const 閉じる=()=>{if(!window.isDestroyed())window.close();};
 共通メニュー({app,Menu,名前:アプリ名,閉じる,icon,platform});
}

module.exports={アプリ名,Macメニューを設定};

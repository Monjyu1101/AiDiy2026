// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// 予測用は判断用と同じ候補・認証条件で生成する。実行・設定変更は行わない。
// 候補はCodeの合成結果から派生。実行権限を付与するファイルではない。
export const NAVI_MODELS_FILE='navi_models_info.json';
const providers=['aidiy_hermes','codex_cli','copilot_cli'];
const nestedCLI=/^(?:[a-z0-9_-]*_cli|codex|copilot|claude|claude-code|codex-cli|copilot-cli|opencode|opencode-cli|antigravity|grok)[/:]/i;
export function naviModelsInfo(code,{now=()=>new Date()}={}){
 const result={_meta:{schema:1,readOnly:true,generatedAt:now().toISOString()}};
 for(const provider of providers){
  const source=code?.[provider]?.models;if(!source||typeof source!=='object'||Array.isArray(source))continue;
  const models=Object.fromEntries(Object.entries(source).filter(([id,label])=>id&&id.length<=300&&!/[\x00-\x1f]/.test(id)&&typeof label==='string'&&(provider!=='aidiy_hermes'||!nestedCLI.test(id))));
  if(Object.keys(models).length)result[provider]={models};
 }
 return result;
}

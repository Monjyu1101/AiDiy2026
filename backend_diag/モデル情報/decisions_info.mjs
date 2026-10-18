// 判断用候補は認証付き取得一覧だけから合成する。生成・課金APIは呼ばない。
import {readConfig,configured,currentDecisionModels} from '../runtime/model_probe.mjs';

// backend_server/AIコア/AI判断共通.py と同じ公式alias（parity testで照合）。
export const FREEAI_DECISION_MODEL = 'gemini-flash-lite-latest';
export const DECISIONS_MODELS_FILE = 'decisions_models_info.json';
const hasKey = (config,id) => configured(config[`${id}_key_id`],id)
  && !['""',"''",'“”','‘’'].includes(config[`${id}_key_id`].trim());
const preferred = (config, first, second) => hasKey(config,first) ? first
  : hasKey(config,second) ? second : first;
// 一覧APIはJSON/Decisions対応可否を保証しない。明らかな専用モデルを除いた候補であり、
// 実行可否は既存の判断起動チェックが決める。公開モデルや設定値の補充は行わない。
export function decisionModelCandidate(id, google) {
  if (typeof id !== 'string') return false;
  const name=id.toLowerCase();
  if (/(?:audio|live|realtime|image|vision-only|tts|transcrib|translat|embedding|robotics|computer-use|nano-banana|lyria)/.test(name)) return false;
  return google ? /^gemini-/.test(name) : /^(?:gpt-|o[1-9](?:-|$))/.test(name);
}

export async function decisionsModelsInfo(providers,results,{configReader,oauthReader}={}) {
  const [,config]=await readConfig(configReader);
  const sources={openai_oauth:'openai_oauth',freeai_chat:preferred(config,'freeai','gemini'),
    openai_decisions:'openai',gemini_chat:preferred(config,'gemini','freeai')};
  const output={};
  for (const [name,id] of Object.entries(sources)) {
    if (!providers.some(row=>row.id===id&&row.設定済み===true)) continue;
    if (id!=='openai_oauth'&&!hasKey(config,id)) continue;
    const rows=await currentDecisionModels(results[id],id,configReader,oauthReader);
    const models=Object.fromEntries(rows.filter(row=>name==='freeai_chat' ? row.model_id===FREEAI_DECISION_MODEL : decisionModelCandidate(row.model_id,id==='gemini'||id==='freeai'))
      .map(row=>[row.model_id,`${/^\d{4}\/\d{2}\/\d{2}$/.test(row.作成日??'')?row.作成日:'yyyy/mm/dd'} - ${row.model_id}`]));
    if (Object.keys(models).length) output[name]={models};
  }
  return output;
}

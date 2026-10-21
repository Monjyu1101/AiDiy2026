// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
// 予測用は判断用と同じ候補・認証条件で生成する。実行・設定変更は行わない。
import {decisionsModelsInfo} from './decisions_info.mjs';
import {PREDICTION_CLI_PROVIDERS} from '../モデル試行/defaults.mjs';

export const PREDICTION_MODELS_FILE = 'prediction_models_info.json';
// 候補の絞り込みは共用し、OpenAI APIの区分だけ実行先のChatAI名に合わせる。
// CLI方式は合成済みのCode候補（導入済みCLIのみ）から auto / same を除いて載せる。
export async function predictionModelsInfo(providers, results, {codeModels = {}, ...options} = {}) {
  const info = await decisionsModelsInfo(providers, results, options);
  const output = Object.fromEntries(Object.entries(info).map(([name, entry]) =>
    [name === 'openai_decisions' ? 'openai_chat' : name, entry]));
  for (const name of PREDICTION_CLI_PROVIDERS) {
    const models = Object.fromEntries(Object.entries(codeModels?.[name]?.models ?? {})
      .filter(([model, label]) => !['auto', 'same'].includes(model) && typeof label === 'string'));
    if (Object.keys(models).length) output[name] = {models};
  }
  return output;
}

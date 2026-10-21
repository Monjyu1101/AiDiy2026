// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
// 予測用は判断用と同じ候補・認証条件で生成する。実行・設定変更は行わない。
import {decisionsModelsInfo} from './decisions_info.mjs';

export const PREDICTION_MODELS_FILE = 'prediction_models_info.json';
// 候補の絞り込みは共用し、OpenAI APIの区分だけ実行先のChatAI名に合わせる。
export async function predictionModelsInfo(providers, results, options = {}) {
  const info = await decisionsModelsInfo(providers, results, options);
  return Object.fromEntries(Object.entries(info).map(([name, entry]) =>
    [name === 'openai_decisions' ? 'openai_chat' : name, entry]));
}

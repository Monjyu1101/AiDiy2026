// 設定モデルの固定試行と、AIモデルの編集可能な初期入力を共通化する。
export const TRIAL_PROMPT='おはよう';
export const DECISION_CHOICES=Object.freeze(['high','medium','low']);
export const decisionQuestions=()=>[{type:'choice',name:'politeness',instructions:'入力の挨拶としての丁寧さをhigh（丁寧）、medium（普通）、low（くだけた表現）から選んでください。',choices:DECISION_CHOICES.map(value=>({value}))}];

export const TRIAL_FAMILIES=Object.freeze(['CHAT','LIVE','PREDICTION','DECISION','CODE']);
export const PREDICTION_PROVIDERS=Object.freeze(['openai_oauth','freeai_chat','openai_chat','gemini_chat']);
export const PREDICTION_AUTO_PROVIDERS=Object.freeze(['openai_oauth','freeai_chat','gemini_chat']);
// ブラウザではサーバー確認済みの同一方式・同一モデルのChat成功だけを使う。
export const predictionChatPassed=(successes,provider,model)=>Array.isArray(successes)&&successes.some(item=>item.provider===provider&&item.model===model);

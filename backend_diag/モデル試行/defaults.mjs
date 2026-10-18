// 設定モデルの固定試行と、AIモデルの編集可能な初期入力を共通化する。
export const TRIAL_PROMPT='おはよう';
export const DECISION_CHOICES=Object.freeze(['high','medium','low']);
export const decisionQuestions=()=>[{type:'choice',name:'politeness',instructions:'入力の挨拶としての丁寧さをhigh（丁寧）、medium（普通）、low（くだけた表現）から選んでください。',choices:DECISION_CHOICES.map(value=>({value}))}];

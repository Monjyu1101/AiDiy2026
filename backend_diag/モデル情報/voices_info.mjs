// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
export const LIVE_VOICES_FILE = 'live_voices_info.json';

const LIVE_GEMINI_VOICES = Object.freeze({
  "Zephyr": "(2.5) Zephyr Female",
  "Puck": "(2.0) Puck",
  "Charon": "(2.0) Charon",
  "Kore": "(2.0) Kore Female",
  "Fenrir": "(2.0) Fenrir",
  "Leda": "(2.5) Leda Female",
  "Orus": "(2.5) Orus",
  "Aoede": "(2.0) Aoede Female",
  "Callirrhoe": "Callirrhoe Female",
  "Autonoe": "Autonoe Female",
  "Enceladus": "Enceladus",
  "Lapetus": "Lapetus",
  "Umbriel": "Umbriel",
  "Algieba": "Algieba",
  "Despina": "Despina Female",
  "Erinome": "Erinome Female",
  "Algenib": "Algenib",
  "Rasalgethi": "Rasalgethi",
  "Laomedeia": "Laomedeia Female",
  "Achernar": "Achernar Female",
  "Alnilam": "Alnilam",
  "Schedar": "Schedar",
  "Gacrux": "Gacrux Female",
  "Pulcherrima": "Pulcherrima",
  "Achird": "Achird",
  "Zubenelgenubi": "Zubenelgenubi",
  "Vindemiatrix": "Vindemiatrix Female",
  "Sadachbia": "Sadachbia",
  "Sadaltager": "Sadaltager",
  "Sulafat": "Sulafat Female"
});

const LIVE_OPENAI_VOICES = Object.freeze({
  "marin": "Marin Female",
  "alloy": "Alloy Female",
  "ash": "Ash",
  "ballad": "Ballad Female",
  "cedar": "Cedar",
  "coral": "Coral Female",
  "echo": "Echo",
  "fable": "Fable",
  "nova": "Nova Female",
  "onyx": "Onyx",
  "sage": "Sage Female",
  "shimmer": "Shimmer Female",
  "verse": "Verse Female"
});

// キー確認に成功した区分だけ固定の声を公開する。FreeAIはGeminiと同じ定義。
export function liveVoicesInfo(providers, results) {
  const voices = {};
  for (const id of ['freeai', 'gemini', 'openai']) {
    const provider = providers.find(row => row.id === id);
    if (!provider || provider.設定済み === false || provider.テスト可能 === false
        || results[id]?.状態 !== 'OK') continue;
    voices[id + '_live'] = {voices:{...(id === 'openai' ? LIVE_OPENAI_VOICES : LIVE_GEMINI_VOICES)}};
  }
  return voices;
}

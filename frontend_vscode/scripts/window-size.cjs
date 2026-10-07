'use strict';
// aidiy_code / aidiy_live / aidiy_discord の専用ウィンドウとブラウザ版（アプリ表示）の大きさ。
// 幅は3本とも aidiy_code 基準。高さは2種類だけ: 会話画面の aidiy_code / aidiy_live と、設定パネルの aidiy_discord。
// 各 desktop.cjs と launch-project.mjs はここの値だけを使い、個別に数値を書かない。
module.exports = Object.freeze({
  幅: 476,
  最小幅: 360,
  会話高さ: 602,
  会話最小高さ: 480,
  パネル高さ: 414,
});

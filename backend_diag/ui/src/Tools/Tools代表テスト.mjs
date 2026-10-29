// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE.
// 通常のChrome tool APIを固定セッションで実行する。任意URL・コマンドは受け付けない。
export const Tools代表テスト={
 aidiy_chrome_devtools:{
  label:'専用ブラウザの起動',
  description:'初回・停止後は白紙のChromeを専用セッション diag-tools-test で起動します。稼働中のセッションを再利用するため、headless条件を変更した場合は専用ブラウザを終了してから再テストしてください。普段のブラウザや有料APIは使いません。終了ボタンもこの専用セッションだけを対象にします。',
  defaults:{headless:false},
  async run({call,input}){await call('Tools/representative',{operation:'open',headless:input.headless===true});return{status:'OK',message:'専用ブラウザの起動に成功しました。不要になったら「専用ブラウザを終了」を押してください。'};},
  async close({call}){await call('Tools/representative',{operation:'close',headless:false});return{status:'OK',message:'専用ブラウザを終了しました。'};},
 },
};

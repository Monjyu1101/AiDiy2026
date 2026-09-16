import { CLI実行, type 実行要求 } from './runner';

// AIコード.vue / AIコード.py / AIコード_cli.py と同じメッセージ項目・識別子。
// 転送路は VS Code の Webview IPC。AiDiy サーバーの起動は不要。
export interface コードパケット {
  セッションID: string;
  チャンネル: string;
  メッセージ識別: 'input_text' | 'input_request' | 'cancel_run' | 'output_stream' | 'output_text';
  メッセージ内容: string;
  ファイル名?: null;
  サムネイル画像?: null;
  出力元?: 'stdout' | 'stderr';
}

export function コード要求実行(要求: コードパケット, 設定: Omit<実行要求, '本文' | 'ストリーム'>, 受信: (packet: コードパケット) => void) {
  if (!['input_text', 'input_request'].includes(要求.メッセージ識別)) throw new Error('コード要求の識別子が不正です。');
  const 送信 = (メッセージ識別: コードパケット['メッセージ識別'], メッセージ内容: string, 出力元?: 'stdout' | 'stderr') => 受信({
    セッションID: 要求.セッションID, チャンネル: 要求.チャンネル,
    メッセージ識別, メッセージ内容, ファイル名: null, サムネイル画像: null, ...(出力元 ? { 出力元 } : {})
  });
  送信('output_stream', '<<< 処理開始 >>>');
  const job = CLI実行({ ...設定, 本文: 要求.メッセージ内容, ストリーム: (line, source) => 送信('output_stream', line, source) });
  const 完了 = job.完了.then(result => {
    送信('output_stream', result.停止理由 ? '<<< 処理中断 >>>' : result.終了コード !== 0 ? '!' : '<<< 処理終了 >>>');
    if (result.回答) 送信('output_text', result.回答);
    return result;
  }, error => { 送信('output_stream', '!'); throw error; });
  return { 完了, 停止: job.停止 };
}

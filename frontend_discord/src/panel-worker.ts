import { Discordパネル } from './panel';
import { 設定エラー } from './config';

const send = (data: object) => { if (process.connected) process.send?.(data); };
const panel = new Discordパネル(state => send({ type: 'state', state }));
const timer = setInterval(() => panel.接続確認(), 1000);
let closing = false;
async function shutdown() {
  if (closing) return;
  closing = true; clearInterval(timer);
  try { await panel.終了(); process.exit(0); }
  catch { process.exit(1); }
}
process.on('message', async (message: { id?: number; action?: string; value?: unknown }) => {
  if (message.action === 'shutdown') { void shutdown(); return; }
  try {
    let result: unknown;
    switch (message.action) {
      case 'initial': result = await panel.初期情報(); break;
      case 'select': result = panel.選択保存(message.value); break;
      case 'select-code': result = panel.コード選択保存(message.value); break;
      case 'catalog-code': result = await panel.コード候補(message.value); break;
      case 'start': await panel.開始(); break;
      case 'stop': await panel.停止(); break;
      default: throw new Error();
    }
    send({ id: message.id, result });
  } catch (error) {
    // 予期しない API / OS エラーの本文を Renderer やログへ流さない。
    send({ id: message.id, error: error instanceof 設定エラー ? error.message : '操作できませんでした。設定・保存先を確認して再試行してください。' });
  }
});
process.on('disconnect', () => { void shutdown(); });
process.on('SIGINT', () => { void shutdown(); });
process.on('SIGTERM', () => { void shutdown(); });

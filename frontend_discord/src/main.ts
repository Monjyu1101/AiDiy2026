import { 設定読込 } from './config';
import { DiscordBot } from './bot';
import { 起動解決 } from './vscode';
import { 接続失敗案内, 接続エラー詳細, type 接続段階 } from './connection-error';

let bot: DiscordBot | undefined;
let stage: 接続段階 = '設定読込';
let token = '';
const startedAt = Date.now();
try {
  const config = 設定読込();
  token = config.token;
  if (process.argv.includes('--check')) {
    stage = 'Hermes確認';
    起動解決(config.cli, config.python, config.folder);
    console.log('Discord 設定・Hermes 起動パス: OK（外部接続は行っていません）');
  } else {
    stage = 'Bot作成';
    bot = new DiscordBot(config);
    const shutdown = () => { void bot?.終了().catch(() => { process.exitCode = 1; }); };
    process.once('SIGINT', shutdown); process.once('SIGTERM', shutdown);
    stage = 'Discord接続'; await bot.起動();
  }
} catch (error) {
  console.error(`[Discord] 起動失敗（${stage}）: ${接続失敗案内(error, stage)}`);
  console.error(接続エラー詳細(error, stage, token, Date.now() - startedAt));
  await bot?.終了(); process.exitCode = 1;
}

import { 設定読込, 設定エラー } from './config';
import { DiscordBot } from './bot';
import { 起動解決 } from './vscode';

let bot: DiscordBot | undefined;
try {
  const config = 設定読込();
  if (process.argv.includes('--check')) {
    起動解決(config.cli, config.python, config.folder);
    console.log('Discord 設定・Hermes 起動パス: OK（外部接続は行っていません）');
  } else {
    bot = new DiscordBot(config);
    const shutdown = () => { void bot?.終了().catch(() => { process.exitCode = 1; }); };
    process.once('SIGINT', shutdown); process.once('SIGTERM', shutdown);
    await bot.起動();
  }
} catch (error) {
  console.error(error instanceof 設定エラー ? error.message : 'Discord を起動できません。設定、Bot トークン、Message Content Intent、Hermes の導入を確認してください。');
  await bot?.終了(); process.exitCode = 1;
}

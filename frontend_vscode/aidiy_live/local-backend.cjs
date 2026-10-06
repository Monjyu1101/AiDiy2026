const { existsSync, readFileSync } = require('node:fs');
const { dirname, join, resolve } = require('node:path');

// 接続先ホストはローカル固定。AiDiy配置先を優先し、共通設定のポートだけ読む。
function ローカル接続先(...folders) {
  const visited = new Set();
  for (const folder of folders) {
    if (!folder) continue;
    let current = resolve(folder);
    while (!visited.has(current)) {
      visited.add(current);
      const file = join(current, '_config', 'AiDiy_key.json');
      if (existsSync(file)) {
        let settings;
        try { settings = JSON.parse(readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
        catch { throw new Error('共通設定 AiDiy_key.json を読み込めません。'); }
        const port = Number(settings.PORT_CORE ?? 8091);
        if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('共通設定 PORT_CORE は1〜65535の整数で指定してください。');
        return `http://127.0.0.1:${port}`;
      }
      const parent = dirname(current);
      if (parent === current) break;
      current = parent;
    }
  }
  // 配布済みVS Code拡張など、AiDiyの配置先を参照できない場合の既定値。
  return 'http://127.0.0.1:8091';
}
module.exports = { ローカル接続先 };

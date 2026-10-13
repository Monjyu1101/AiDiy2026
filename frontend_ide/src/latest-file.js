// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// 最終更新表示・自動追跡だけに適用する。ツリー表示・バックアップ・Gitの対象は変えない。
const EXCLUDED_DIRS = new Set(['_AIDIY', '_data', '_datas']);

export function latestFile(tree) {
  let latest = null;
  function walk(node, prefix) {
    if (!node) return;
    for (const [name, , mtime] of node.f) {
      if (!latest || mtime > latest.mtime) latest = { name, path: prefix ? `${prefix}/${name}` : name, mtime };
    }
    for (const dir of node.d) {
      if (!EXCLUDED_DIRS.has(dir.n)) walk(dir, prefix ? `${prefix}/${dir.n}` : dir.n);
    }
  }
  walk(tree, '');
  return latest;
}

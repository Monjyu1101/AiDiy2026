// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// UTCの日付文字列で比較せず、閲覧端末の年・月・日を使う。
export function fileDateInfo(mtime, now = Date.now()) {
  if (typeof mtime !== 'number' || !Number.isFinite(mtime)) return { text: '—', today: false, iso: undefined, title: '更新日時不明' };
  const date = new Date(mtime), current = new Date(now);
  if (!Number.isFinite(date.getTime())) return { text: '—', today: false, iso: undefined, title: '更新日時不明' };
  const today = date.getFullYear() === current.getFullYear() && date.getMonth() === current.getMonth() && date.getDate() === current.getDate();
  const title = date.toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  return { text: today ? '今日 ' + date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }) : title, today, iso: date.toISOString(), title };
}
export function nextLocalMidnight(now = Date.now()) {
  const next = new Date(now); next.setHours(24, 0, 0, 0); return next.getTime();
}

// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// falseはxtermの変換だけを止める。コピー・貼付けはブラウザーの既定動作と
// xtermのcopy/pasteイベントへ任せ、権限付きClipboard APIや二重貼付けを避ける。
export function terminalKeyHandler(send) {
  return event => {
    if (event.isComposing || event.keyCode === 229) return true;
    const key = event.key.toLowerCase();
    if ((event.ctrlKey || event.metaKey) && !event.altKey && (key === 'c' || key === 'v')) return false;
    if (key === 'enter' && !event.ctrlKey && !event.metaKey && (event.altKey || event.shiftKey)) {
      event.preventDefault();
      event.stopPropagation();
      if (event.type === 'keydown') {
        // Alt+Enterは従来のESC+CR。Shift+EnterはEnterと区別できるCSI-u。
        // 両方押した場合も修飾を失わない（1 + Shift 1 + Alt 2）。
        send(event.shiftKey ? `\x1b[13;${event.altKey ? 4 : 2}u` : '\x1b\r');
      }
      return false;
    }
    return true;
  };
}

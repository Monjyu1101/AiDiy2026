// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

// Web 版と画面を共用する。ファイル操作や汎用 IPC は公開しない。
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('aidiyDesktop', {
  windowAction: action => {
    if (['minimize', 'close'].includes(action)) return ipcRenderer.invoke('aidiy-ide:window', action);
  },
});

/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('aidiyLiveDesktop', {
  windowAction: action => {
    if (['minimize', 'close'].includes(action)) return ipcRenderer.invoke('aidiy-live:window', action);
  },
  onState: callback => {
    const listener = (_event, state) => callback({ opening: Boolean(state.opening) });
    ipcRenderer.on('aidiy-live:window-state', listener);
    return () => ipcRenderer.removeListener('aidiy-live:window-state', listener);
  },
});

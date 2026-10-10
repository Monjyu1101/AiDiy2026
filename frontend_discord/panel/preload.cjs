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
contextBridge.exposeInMainWorld('discordPanel', {
  initial: () => ipcRenderer.invoke('discord:request', 'initial'),
  select: value => ipcRenderer.invoke('discord:request', 'select', value),
  selectFeatures: value => ipcRenderer.invoke('discord:request', 'select-features', value),
  selectCode: value => ipcRenderer.invoke('discord:request', 'select-code', value),
  catalogCode: provider => ipcRenderer.invoke('discord:request', 'catalog-code', provider),
  start: () => ipcRenderer.invoke('discord:request', 'start'),
  stop: () => ipcRenderer.invoke('discord:request', 'stop'),
  monitor: on => ipcRenderer.invoke('discord:request', 'monitor', on),
  window: action => ipcRenderer.invoke('discord:window', action),
  onState: callback => { ipcRenderer.on('discord:state', (_event, state) => callback(state)); },
  onAudio: callback => { ipcRenderer.on('discord:audio', (_event, audio) => callback(audio)); },
  onMeter: callback => { ipcRenderer.on('discord:meter', (_event, meter) => callback(meter)); },
  onActivity: callback => { ipcRenderer.on('discord:activity', (_event, activity) => callback(activity)); },
});

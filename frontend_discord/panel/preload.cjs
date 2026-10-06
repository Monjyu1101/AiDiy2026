const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('discordPanel', {
  initial: () => ipcRenderer.invoke('discord:request', 'initial'),
  select: value => ipcRenderer.invoke('discord:request', 'select', value),
  selectCode: value => ipcRenderer.invoke('discord:request', 'select-code', value),
  catalogCode: provider => ipcRenderer.invoke('discord:request', 'catalog-code', provider),
  start: () => ipcRenderer.invoke('discord:request', 'start'),
  stop: () => ipcRenderer.invoke('discord:request', 'stop'),
  window: action => ipcRenderer.invoke('discord:window', action),
  onState: callback => { ipcRenderer.on('discord:state', (_event, state) => callback(state)); },
});

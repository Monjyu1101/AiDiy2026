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

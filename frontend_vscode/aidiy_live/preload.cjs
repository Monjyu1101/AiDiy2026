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

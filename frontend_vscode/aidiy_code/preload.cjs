const { contextBridge, ipcRenderer } = require('electron');

// 描画側に公開するのはウィンドウ操作だけ。汎用 IPC や Node.js API は渡さない。
contextBridge.exposeInMainWorld('aidiyWindow', {
  minimize: () => ipcRenderer.invoke('aidiy:window', 'minimize'),
  maximize: () => ipcRenderer.invoke('aidiy:window', 'maximize'),
  close: () => ipcRenderer.invoke('aidiy:window', 'close'),
  onState: callback => {
    const listener = (_event, state) => callback({ maximized: Boolean(state.maximized), opening: Boolean(state.opening) });
    ipcRenderer.on('aidiy:window-state', listener);
    return () => ipcRenderer.removeListener('aidiy:window-state', listener);
  },
});

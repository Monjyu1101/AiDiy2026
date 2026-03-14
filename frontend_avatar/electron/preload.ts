import { contextBridge, ipcRenderer } from 'electron'

type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type WindowMode = 'login' | 'core'
type WindowRole = WindowMode | PanelKey | 'settings'
type WindowBounds = { x: number; y: number; width: number; height: number }
type WindowMetrics = WindowBounds & { minWidth: number; minHeight: number }
type DisplaySourceKind = 'screen' | 'window'
type DisplaySourceInfo = {
  id: string
  name: string
  kind: DisplaySourceKind
  thumbnailDataUrl: string | null
}

const api = {
  versions: {
    chrome: process.versions.chrome,
    electron: process.versions.electron,
    node: process.versions.node,
  },
  getWindowRole: () => ipcRenderer.invoke('window:get-role') as Promise<WindowRole>,
  getWindowBounds: () => ipcRenderer.invoke('window:get-bounds') as Promise<WindowMetrics>,
  setWindowBounds: (bounds: WindowBounds) => ipcRenderer.invoke('window:set-bounds', bounds),
  setWindowInteractive: (interactive: boolean) => ipcRenderer.invoke('window:set-interactive', interactive) as Promise<boolean>,
  setWindowMode: (mode: WindowMode) => ipcRenderer.invoke('window:set-mode', mode),
  openCoreWindow: () => ipcRenderer.invoke('window:open-core') as Promise<WindowMode>,
  openLoginWindow: () => ipcRenderer.invoke('window:open-login') as Promise<WindowMode>,
  closeCurrentWindow: () => ipcRenderer.invoke('window:close-self'),
  minimizeCurrentWindow: () => ipcRenderer.invoke('window:minimize-self'),
  togglePanel: (panel: PanelKey) => ipcRenderer.invoke('panel:toggle', panel),
  applyPanelStates: (states: Record<PanelKey, boolean>) => ipcRenderer.invoke('panel:apply-states', states) as Promise<Record<PanelKey, boolean>>,
  getPanelStates: () => ipcRenderer.invoke('panel:get-states') as Promise<Record<PanelKey, boolean>>,
  listDisplaySources: () => ipcRenderer.invoke('desktop:list-sources') as Promise<DisplaySourceInfo[]>,
  setDisplaySource: (sourceId: string | null) => ipcRenderer.invoke('desktop:set-source', sourceId),
  openSettingsWindow: (sessionId: string) => ipcRenderer.invoke('settings:open', sessionId),
  closeSettingsWindow: () => ipcRenderer.invoke('settings:close'),
  onSettingsPrepare: (callback: (sessionId: string) => void) => {
    const handler = (_event: unknown, sessionId: string) => callback(sessionId)
    ipcRenderer.on('settings:session-id', handler)
    return () => { ipcRenderer.removeListener('settings:session-id', handler) }
  },
  onPanelStatesChanged: (callback: (states: Record<PanelKey, boolean>) => void) => {
    const handler = (_event: unknown, states: Record<PanelKey, boolean>) => callback(states)
    ipcRenderer.on('panel:states-changed', handler)
    return () => {
      ipcRenderer.removeListener('panel:states-changed', handler)
    }
  },
  onWindowShown: (callback: () => void) => {
    const handler = () => callback()
    ipcRenderer.on('window:shown', handler)
    return () => {
      ipcRenderer.removeListener('window:shown', handler)
    }
  },
}

contextBridge.exposeInMainWorld('desktopApi', api)

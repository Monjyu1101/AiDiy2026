import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const isDev = Boolean(process.env.VITE_DEV_SERVER_URL)
const shouldOpenDevTools = process.env.VITE_OPEN_DEVTOOLS === '1'

type WindowMode = 'login' | 'core'
type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type WindowRole = WindowMode | PanelKey
type WindowBounds = { x: number; y: number; width: number; height: number }

type BoundsPreset = {
  width: number
  height: number
  minWidth: number
  minHeight: number
}

const LOGIN_BOUNDS: BoundsPreset = { width: 320, height: 240, minWidth: 320, minHeight: 240 }
const CORE_BOUNDS: BoundsPreset = { width: 560, height: 720, minWidth: 520, minHeight: 640 }
const CHAT_BASE_BOUNDS: BoundsPreset = { width: 520, height: 620, minWidth: 440, minHeight: 420 }
const PANEL_BOUNDS: Record<PanelKey, BoundsPreset> = {
  chat: CHAT_BASE_BOUNDS,
  file: CHAT_BASE_BOUNDS,
  image: CHAT_BASE_BOUNDS,
  code1: CHAT_BASE_BOUNDS,
  code2: CHAT_BASE_BOUNDS,
  code3: CHAT_BASE_BOUNDS,
  code4: CHAT_BASE_BOUNDS,
}

const panelStates: Record<PanelKey, boolean> = {
  chat: false,
  file: false,
  image: false,
  code1: false,
  code2: false,
  code3: false,
  code4: false,
}

let primaryWindow: BrowserWindow | null = null
const panelWindows = new Map<PanelKey, BrowserWindow>()
const windowRoles = new Map<number, WindowRole>()

function getRendererUrl(): string {
  if (isDev) {
    return process.env.VITE_DEV_SERVER_URL as string
  }
  return pathToFileURL(path.resolve(__dirname, '../dist/index.html')).toString()
}

function createBaseWindow(bounds: BoundsPreset, role: WindowRole, show = true): BrowserWindow {
  const appPath = app.getAppPath()
  const window = new BrowserWindow({
    width: bounds.width,
    height: bounds.height,
    minWidth: bounds.minWidth,
    minHeight: bounds.minHeight,
    show,
    backgroundColor: '#00000000',
    transparent: true,
    hasShadow: false,
    frame: false,
    resizable: true,
    autoHideMenuBar: true,
    title: 'AiDiy Avatar',
    icon: path.join(appPath, 'public', 'icons', 'AiDiy.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: false,
    },
  })

  windowRoles.set(window.id, role)

  if (isDev) {
    window.loadURL(getRendererUrl())
    if (shouldOpenDevTools) {
      window.webContents.openDevTools({ mode: 'detach' })
    }
  } else {
    window.loadURL(getRendererUrl())
  }

  return window
}

function clampWindowBounds(window: BrowserWindow, nextBounds: WindowBounds): WindowBounds {
  const [minWidth, minHeight] = window.getMinimumSize()
  const currentBounds = window.getBounds()
  const clampedWidth = Math.max(minWidth || 0, Math.round(nextBounds.width))
  const clampedHeight = Math.max(minHeight || 0, Math.round(nextBounds.height))

  return {
    x: Math.round(nextBounds.x ?? currentBounds.x),
    y: Math.round(nextBounds.y ?? currentBounds.y),
    width: clampedWidth,
    height: clampedHeight,
  }
}

function notifyPanelStates() {
  const payload = { ...panelStates }
  BrowserWindow.getAllWindows().forEach((window) => {
    if (!window.isDestroyed()) {
      window.webContents.send('panel:states-changed', payload)
    }
  })
}

function setPanelVisibility(panel: PanelKey, visible: boolean) {
  const window = panelWindows.get(panel)
  if (!window || window.isDestroyed()) {
    panelStates[panel] = false
    notifyPanelStates()
    return
  }

  if (visible) {
    window.show()
    window.focus()
  } else {
    window.hide()
  }

  panelStates[panel] = visible
  notifyPanelStates()
}

function closePanelWindow(panel: PanelKey) {
  const window = panelWindows.get(panel)
  if (window && !window.isDestroyed()) {
    window.destroy()
  }
  panelWindows.delete(panel)
  panelStates[panel] = false
  notifyPanelStates()
}

function closeAllPanelWindows() {
  ;(Object.keys(panelStates) as PanelKey[]).forEach((panel) => {
    closePanelWindow(panel)
  })
}

function applyPrimaryMode(window: BrowserWindow, mode: WindowMode) {
  const bounds = mode === 'login' ? LOGIN_BOUNDS : CORE_BOUNDS
  windowRoles.set(window.id, mode)
  window.setMinimumSize(bounds.minWidth, bounds.minHeight)
  window.setResizable(mode === 'core')
  window.setSize(bounds.width, bounds.height, true)
  window.center()
}

function createPanelWindow(panel: PanelKey) {
  const existing = panelWindows.get(panel)
  if (existing && !existing.isDestroyed()) {
    setPanelVisibility(panel, panelStates[panel])
    return existing
  }

  const bounds = PANEL_BOUNDS[panel]
  const window = createBaseWindow(bounds, panel, false)
  if (primaryWindow && !primaryWindow.isDestroyed()) {
    const [primaryX, primaryY] = primaryWindow.getPosition()
    window.setPosition(primaryX + 44, primaryY + 44)
  }

  panelWindows.set(panel, window)
  panelStates[panel] = false

  window.on('closed', () => {
    panelWindows.delete(panel)
    panelStates[panel] = false
    windowRoles.delete(window.id)
    notifyPanelStates()
  })

  notifyPanelStates()
  return window
}

function ensureAllPanelWindows() {
  ;(Object.keys(panelStates) as PanelKey[]).forEach((panel) => {
    createPanelWindow(panel)
  })
}

function createPrimaryWindow() {
  primaryWindow = createBaseWindow(LOGIN_BOUNDS, 'login')
  applyPrimaryMode(primaryWindow, 'login')

  primaryWindow.on('closed', () => {
    closeAllPanelWindows()
    if (primaryWindow) {
      windowRoles.delete(primaryWindow.id)
    }
    primaryWindow = null
  })

  return primaryWindow
}

app.whenReady().then(() => {
  ipcMain.handle('window:get-role', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return 'login'
    return windowRoles.get(window.id) ?? 'login'
  })

  ipcMain.handle('window:set-mode', (event, mode: WindowMode) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return mode

    if (mode === 'login') {
      closeAllPanelWindows()
    } else {
      ensureAllPanelWindows()
    }

    applyPrimaryMode(window, mode)
    return mode
  })

  ipcMain.handle('window:close-self', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return
    const role = windowRoles.get(window.id)
    if (role && role !== 'login' && role !== 'core') {
      setPanelVisibility(role, false)
      return
    }
    window.close()
  })

  ipcMain.handle('window:get-bounds', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) {
      return { x: 0, y: 0, width: 0, height: 0, minWidth: 0, minHeight: 0 }
    }
    const bounds = window.getBounds()
    const [minWidth, minHeight] = window.getMinimumSize()
    return {
      ...bounds,
      minWidth,
      minHeight,
    }
  })

  ipcMain.handle('window:set-bounds', (event, nextBounds: WindowBounds) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return

    const bounds = clampWindowBounds(window, nextBounds)
    window.setBounds(bounds)
    return bounds
  })

  ipcMain.handle('panel:toggle', (_event, panel: PanelKey) => {
    createPanelWindow(panel)
    setPanelVisibility(panel, !panelStates[panel])
    return { ...panelStates }
  })

  ipcMain.handle('panel:get-states', () => ({ ...panelStates }))

  createPrimaryWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createPrimaryWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

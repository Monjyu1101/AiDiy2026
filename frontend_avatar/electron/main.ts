import { app, BrowserWindow, desktopCapturer, ipcMain, screen, session } from 'electron'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const isDev = Boolean(process.env.VITE_DEV_SERVER_URL)
const shouldOpenDevTools = process.env.VITE_OPEN_DEVTOOLS === '1'
const APP_USER_MODEL_ID = 'AiDiy.frontend_avatar'

type WindowMode = 'login' | 'core'
type PanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type WindowRole = WindowMode | PanelKey | 'settings'
type WindowBounds = { x: number; y: number; width: number; height: number }
type DisplaySourceKind = 'screen' | 'window'
type DisplaySourceInfo = {
  id: string
  name: string
  kind: DisplaySourceKind
  thumbnailDataUrl: string | null
}

type BoundsPreset = {
  width: number
  height: number
  minWidth: number
  minHeight: number
}

const LOGIN_BOUNDS: BoundsPreset = { width: 320, height: 240, minWidth: 320, minHeight: 240 }
const CORE_BOUNDS: BoundsPreset = { width: 520, height: 620, minWidth: 440, minHeight: 420 }
const CHAT_BASE_BOUNDS: BoundsPreset = { width: 520, height: 620, minWidth: 440, minHeight: 420 }
const SETTINGS_BOUNDS: BoundsPreset = { width: 760, height: 700, minWidth: 600, minHeight: 400 }
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

let loginWindow: BrowserWindow | null = null
let coreWindow: BrowserWindow | null = null
let settingsWindow: BrowserWindow | null = null
const panelWindows = new Map<PanelKey, BrowserWindow>()
const windowRoles = new Map<number, WindowRole>()
let selectedDisplaySourceId: string | null = null
// Electronのバグ回避: getMinimumSize()が初期サイズを返す場合があるため独自管理
const windowMinSizes = new Map<number, { minWidth: number; minHeight: number }>()

function getWorkArea() {
  return screen.getPrimaryDisplay().workArea
}

function getBottomRightPosition(
  width: number,
  height: number,
  margins: { right?: number; bottom?: number } = {},
) {
  const area = getWorkArea()
  const right = margins.right ?? 24
  const bottom = margins.bottom ?? 0
  return {
    x: area.x + Math.max(0, area.width - width - right),
    y: area.y + Math.max(0, area.height - height - bottom),
  }
}

function getBottomLeftPosition(_width: number, height: number, margin = 24) {
  const area = getWorkArea()
  return {
    x: area.x + margin,
    y: area.y + Math.max(margin, area.height - height - margin),
  }
}

function getCenteredPosition(width: number, height: number) {
  const area = getWorkArea()
  return {
    x: area.x + Math.round((area.width - width) / 2),
    y: area.y + Math.round((area.height - height) / 2),
  }
}

function getPanelInitialPosition(panel: PanelKey, width: number, height: number) {
  if (panel === 'chat') {
    return getCenteredPosition(width, height)
  }
  if (panel === 'image') {
    return getBottomLeftPosition(width, height)
  }

  const area = getWorkArea()
  const baseX = area.x + 24
  const baseY = area.y + 24
  const orderMap: Record<Exclude<PanelKey, 'image' | 'chat'>, number> = {
    file: 0,
    code1: 1,
    code2: 2,
    code3: 3,
    code4: 4,
  }
  const step = 48
  const order = orderMap[panel as Exclude<PanelKey, 'image' | 'chat'>] ?? 0

  return {
    x: baseX + (step * order),
    y: baseY + (step * order),
  }
}

function resolveDisplaySourceKind(sourceId: string): DisplaySourceKind {
  return sourceId.startsWith('window:') ? 'window' : 'screen'
}

async function listDisplaySources(): Promise<DisplaySourceInfo[]> {
  const sources = await desktopCapturer.getSources({
    types: ['screen', 'window'],
    thumbnailSize: { width: 320, height: 180 },
    fetchWindowIcons: true,
  })

  return sources.map((source) => ({
    id: source.id,
    name: source.name,
    kind: resolveDisplaySourceKind(source.id),
    thumbnailDataUrl: source.thumbnail.isEmpty() ? null : source.thumbnail.toDataURL(),
  }))
}

function getRendererUrl(role: WindowRole): string {
  const baseUrl = isDev
    ? (process.env.VITE_DEV_SERVER_URL as string)
    : pathToFileURL(path.resolve(__dirname, '../dist/index.html')).toString()

  const url = new URL(baseUrl)
  url.searchParams.set('role', role)
  return url.toString()
}

function createBaseWindow(bounds: BoundsPreset, role: WindowRole, show = true): BrowserWindow {
  const appPath = app.getAppPath()
  const iconPath = path.join(appPath, 'public', 'icons', 'AiDiy.ico')
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
    icon: iconPath,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: false,
      backgroundThrottling: false,
    },
  })

  windowRoles.set(window.id, role)

  // min サイズを独自管理し、ロード後に再適用（Electron Windowsバグ対策）
  windowMinSizes.set(window.id, { minWidth: bounds.minWidth, minHeight: bounds.minHeight })
  window.webContents.once('did-finish-load', () => {
    if (!window.isDestroyed()) {
      window.setMinimumSize(bounds.minWidth, bounds.minHeight)
    }
  })
  window.on('closed', () => {
    windowMinSizes.delete(window.id)
  })

  if (isDev) {
    window.loadURL(getRendererUrl(role))
    if (shouldOpenDevTools) {
      window.webContents.openDevTools({ mode: 'detach' })
    }
  } else {
    window.loadURL(getRendererUrl(role))
  }

  return window
}

function waitForReady(window: BrowserWindow) {
  if (window.isDestroyed()) {
    return Promise.resolve()
  }
  if (!window.webContents.isLoading()) {
    return Promise.resolve()
  }
  return new Promise<void>((resolve) => {
    window.once('ready-to-show', () => resolve())
    window.webContents.once('did-finish-load', () => resolve())
  })
}

function clampWindowBounds(window: BrowserWindow, nextBounds: WindowBounds): WindowBounds {
  const minSizes = windowMinSizes.get(window.id) ?? { minWidth: 100, minHeight: 100 }
  const currentBounds = window.getBounds()
  const clampedWidth = Math.max(minSizes.minWidth, Math.round(nextBounds.width))
  const clampedHeight = Math.max(minSizes.minHeight, Math.round(nextBounds.height))

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
    window.webContents.send('window:shown')
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
  const position = mode === 'core'
    ? getBottomRightPosition(bounds.width, bounds.height, { right: 24, bottom: 0 })
    : getCenteredPosition(bounds.width, bounds.height)

  windowRoles.set(window.id, mode)
  window.setMinimumSize(bounds.minWidth, bounds.minHeight)
  window.setResizable(mode === 'core')
  window.setBounds({
    x: position.x,
    y: position.y,
    width: bounds.width,
    height: bounds.height,
  }, false)
}

function createPanelWindow(panel: PanelKey) {
  const existing = panelWindows.get(panel)
  if (existing && !existing.isDestroyed()) {
    setPanelVisibility(panel, panelStates[panel])
    return existing
  }

  const bounds = PANEL_BOUNDS[panel]
  const window = createBaseWindow(bounds, panel, false)
  const { x, y } = getPanelInitialPosition(panel, bounds.width, bounds.height)
  window.setPosition(x, y)

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

function createLoginWindow(show = true) {
  if (loginWindow && !loginWindow.isDestroyed()) {
    applyPrimaryMode(loginWindow, 'login')
    if (loginWindow.isMinimized()) {
      loginWindow.restore()
    }
    loginWindow.center()
    if (show) loginWindow.show()
    return loginWindow
  }

  loginWindow = createBaseWindow(LOGIN_BOUNDS, 'login', show)
  applyPrimaryMode(loginWindow, 'login')

  loginWindow.on('closed', () => {
    if (loginWindow) {
      windowRoles.delete(loginWindow.id)
    }
    loginWindow = null
  })

  return loginWindow
}

function createCoreWindow(show = true) {
  if (coreWindow && !coreWindow.isDestroyed()) {
    applyPrimaryMode(coreWindow, 'core')
    if (show) coreWindow.show()
    return coreWindow
  }

  coreWindow = createBaseWindow(CORE_BOUNDS, 'core', show)
  applyPrimaryMode(coreWindow, 'core')

  coreWindow.on('closed', () => {
    closeAllPanelWindows()
    if (coreWindow) {
      windowRoles.delete(coreWindow.id)
    }
    coreWindow = null
  })

  return coreWindow
}

async function openCoreWindow(sourceWindow?: BrowserWindow | null) {
  const nextCoreWindow = createCoreWindow(false)
  ensureAllPanelWindows()
  await waitForReady(nextCoreWindow)
  if (!nextCoreWindow.isDestroyed()) {
    nextCoreWindow.show()
    nextCoreWindow.focus()
    nextCoreWindow.webContents.send('window:shown')
  }

  if (loginWindow && !loginWindow.isDestroyed()) {
    loginWindow.hide()
  } else if (sourceWindow && !sourceWindow.isDestroyed() && sourceWindow !== nextCoreWindow) {
    sourceWindow.hide()
  }

  return 'core' as const
}

async function openLoginWindow(sourceWindow?: BrowserWindow | null) {
  closeAllPanelWindows()
  const nextLoginWindow = createLoginWindow(false)
  await waitForReady(nextLoginWindow)
  if (!nextLoginWindow.isDestroyed()) {
    if (nextLoginWindow.isMinimized()) {
      nextLoginWindow.restore()
    }
    nextLoginWindow.center()
    nextLoginWindow.show()
    nextLoginWindow.focus()
    nextLoginWindow.webContents.send('window:shown')
  }

  if (coreWindow && !coreWindow.isDestroyed()) {
    coreWindow.close()
  }

  return 'login' as const
}

function openSettingsWindow(sessionId: string) {
  if (settingsWindow && !settingsWindow.isDestroyed()) {
    settingsWindow.webContents.send('settings:session-id', sessionId)
    settingsWindow.show()
    settingsWindow.focus()
    settingsWindow.webContents.send('window:shown')
    return
  }

  const appPath = app.getAppPath()
  const iconPath = path.join(appPath, 'public', 'icons', 'AiDiy.ico')

  settingsWindow = new BrowserWindow({
    width: SETTINGS_BOUNDS.width,
    height: SETTINGS_BOUNDS.height,
    minWidth: SETTINGS_BOUNDS.minWidth,
    minHeight: SETTINGS_BOUNDS.minHeight,
    show: false,
    backgroundColor: '#f8fafc',
    transparent: false,
    frame: false,
    resizable: true,
    autoHideMenuBar: true,
    title: 'AiDiy Avatar',
    icon: iconPath,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: false,
      backgroundThrottling: false,
    },
  })

  windowRoles.set(settingsWindow.id, 'settings')
  windowMinSizes.set(settingsWindow.id, { minWidth: SETTINGS_BOUNDS.minWidth, minHeight: SETTINGS_BOUNDS.minHeight })

  settingsWindow.once('ready-to-show', () => {
    if (settingsWindow && !settingsWindow.isDestroyed()) {
      settingsWindow.setMinimumSize(SETTINGS_BOUNDS.minWidth, SETTINGS_BOUNDS.minHeight)
      settingsWindow.center()
      settingsWindow.webContents.send('settings:session-id', sessionId)
      settingsWindow.show()
      settingsWindow.focus()
      settingsWindow.webContents.send('window:shown')
    }
  })

  settingsWindow.on('closed', () => {
    if (settingsWindow) {
      windowRoles.delete(settingsWindow.id)
      windowMinSizes.delete(settingsWindow.id)
    }
    settingsWindow = null
  })

  const baseUrl = isDev
    ? (process.env.VITE_DEV_SERVER_URL as string)
    : pathToFileURL(path.resolve(__dirname, '../dist/index.html')).toString()
  const url = new URL(baseUrl)
  url.searchParams.set('role', 'settings')
  void settingsWindow.loadURL(url.toString())
}

app.whenReady().then(() => {
  if (process.platform === 'win32') {
    app.setAppUserModelId(APP_USER_MODEL_ID)
  }

  session.defaultSession.setDisplayMediaRequestHandler(
    async (_request, callback) => {
      const sourceId = selectedDisplaySourceId
      selectedDisplaySourceId = null
      if (!sourceId) {
        callback({})
        return
      }

      try {
        const sources = await desktopCapturer.getSources({ types: ['screen', 'window'] })
        const selectedSource = sources.find((source) => source.id === sourceId)
        if (!selectedSource) {
          console.error('[desktop-capture] selected source not found:', sourceId)
          callback({})
          return
        }
        callback({ video: selectedSource })
      } catch (error) {
        console.error('[desktop-capture] source resolve failed:', error)
        callback({})
      }
    },
    { useSystemPicker: false },
  )

  ipcMain.handle('window:get-role', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return 'login'
    return windowRoles.get(window.id) ?? 'login'
  })

  ipcMain.handle('window:set-mode', async (event, mode: WindowMode) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return mode

    if (mode === 'core') {
      return openCoreWindow(window)
    }
    return openLoginWindow(window)
  })

  ipcMain.handle('window:open-core', async (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    return openCoreWindow(window)
  })

  ipcMain.handle('window:open-login', async (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    return openLoginWindow(window)
  })

  ipcMain.handle('window:close-self', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return
    const role = windowRoles.get(window.id)
    if (role && role !== 'login' && role !== 'core' && role !== 'settings') {
      setPanelVisibility(role as PanelKey, false)
      return
    }
    window.close()
  })

  ipcMain.handle('window:minimize-self', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return
    window.minimize()
  })

  ipcMain.handle('window:get-bounds', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) {
      return { x: 0, y: 0, width: 0, height: 0, minWidth: 100, minHeight: 100 }
    }
    const bounds = window.getBounds()
    const minSizes = windowMinSizes.get(window.id) ?? { minWidth: 100, minHeight: 100 }
    return {
      ...bounds,
      minWidth: minSizes.minWidth,
      minHeight: minSizes.minHeight,
    }
  })

  ipcMain.handle('window:set-bounds', (event, nextBounds: WindowBounds) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return

    const bounds = clampWindowBounds(window, nextBounds)
    window.setBounds(bounds)
    return bounds
  })

  ipcMain.handle('window:set-interactive', (event, interactive: boolean) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (!window) return false

    window.setIgnoreMouseEvents(!interactive, { forward: true })
    if (interactive) {
      window.setFocusable(true)
    } else {
      window.blur()
      window.setFocusable(false)
    }
    return interactive
  })

  ipcMain.handle('panel:toggle', (_event, panel: PanelKey) => {
    createPanelWindow(panel)
    setPanelVisibility(panel, !panelStates[panel])
    return { ...panelStates }
  })

  ipcMain.handle('panel:apply-states', (_event, states: Record<PanelKey, boolean>) => {
    ;(Object.keys(states) as PanelKey[]).forEach((panel) => {
      createPanelWindow(panel)
      setPanelVisibility(panel, Boolean(states[panel]))
    })
    return { ...panelStates }
  })

  ipcMain.handle('panel:get-states', () => ({ ...panelStates }))

  ipcMain.handle('settings:open', (_event, sessionId: string) => {
    openSettingsWindow(sessionId)
  })

  ipcMain.handle('settings:close', (event) => {
    const window = BrowserWindow.fromWebContents(event.sender)
    if (window && !window.isDestroyed()) {
      window.hide()
    }
  })

  ipcMain.handle('desktop:list-sources', async () => listDisplaySources())

  ipcMain.handle('desktop:set-source', (_event, sourceId: string | null) => {
    selectedDisplaySourceId = sourceId
    return selectedDisplaySourceId
  })

  createLoginWindow()

  app.on('activate', () => {
    if (!loginWindow && !coreWindow && BrowserWindow.getAllWindows().length === 0) {
      createLoginWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

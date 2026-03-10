/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CORE_BASE_URL?: string
  readonly VITE_CORE_WS_URL?: string
}

type AvatarPanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
type AvatarWindowMode = 'login' | 'core'
type AvatarWindowRole = AvatarWindowMode | AvatarPanelKey
type AvatarWindowBounds = { x: number; y: number; width: number; height: number }
type AvatarWindowMetrics = AvatarWindowBounds & { minWidth: number; minHeight: number }

declare global {
  interface Window {
    desktopApi?: {
      versions: {
        chrome: string
        electron: string
        node: string
      }
      getWindowRole?: () => Promise<AvatarWindowRole>
      getWindowBounds?: () => Promise<AvatarWindowMetrics>
      setWindowBounds?: (bounds: AvatarWindowBounds) => Promise<AvatarWindowBounds>
      setWindowMode?: (mode: AvatarWindowMode) => Promise<AvatarWindowMode>
      closeCurrentWindow?: () => Promise<void>
      togglePanel?: (panel: AvatarPanelKey) => Promise<Record<AvatarPanelKey, boolean>>
      getPanelStates?: () => Promise<Record<AvatarPanelKey, boolean>>
      onPanelStatesChanged?: (
        callback: (states: Record<AvatarPanelKey, boolean>) => void,
      ) => () => void
    }
  }
}

export {}

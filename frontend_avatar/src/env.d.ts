// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CORE_BASE_URL?: string
  readonly VITE_CORE_WS_URL?: string
}

declare global {
  type AvatarPanelKey = 'chat' | 'file' | 'image' | 'code1' | 'code2' | 'code3' | 'code4'
  type AvatarWindowMode = 'login' | 'core'
  type AvatarWindowRole = AvatarWindowMode | AvatarPanelKey
  type AvatarWindowBounds = { x: number; y: number; width: number; height: number }
  type AvatarWindowMetrics = AvatarWindowBounds & { minWidth: number; minHeight: number }
  type AvatarDisplaySourceKind = 'screen' | 'window'
  type AvatarDisplaySource = {
    id: string
    name: string
    kind: AvatarDisplaySourceKind
    thumbnailDataUrl: string | null
  }

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
      setWindowInteractive?: (interactive: boolean) => Promise<boolean>
      setWindowMode?: (mode: AvatarWindowMode) => Promise<AvatarWindowMode>
      openCoreWindow?: () => Promise<AvatarWindowMode>
      openLoginWindow?: () => Promise<AvatarWindowMode>
      closeCurrentWindow?: () => Promise<void>
      minimizeCurrentWindow?: () => Promise<void>
      togglePanel?: (panel: AvatarPanelKey) => Promise<Record<AvatarPanelKey, boolean>>
      applyPanelStates?: (states: Record<AvatarPanelKey, boolean>) => Promise<Record<AvatarPanelKey, boolean>>
      getPanelStates?: () => Promise<Record<AvatarPanelKey, boolean>>
      listDisplaySources?: () => Promise<AvatarDisplaySource[]>
      setDisplaySource?: (sourceId: string | null) => Promise<string | null>
      onPanelStatesChanged?: (
        callback: (states: Record<AvatarPanelKey, boolean>) => void,
      ) => () => void
      onWindowShown?: (callback: () => void) => () => void
    }
  }
}

export {}

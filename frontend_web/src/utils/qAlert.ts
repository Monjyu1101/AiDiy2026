// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

// ダイアログコンポーネントのインスタンス型定義
interface AlertDialogInstance {
  show: (message: string) => Promise<void>
}

interface ConfirmDialogInstance {
  show: (message: string) => Promise<boolean>
}

interface ColorPickerDialogInstance {
  show: (initialColor: string, title: string) => Promise<string | null>
}

let alertInstance: AlertDialogInstance | null = null
let confirmInstance: ConfirmDialogInstance | null = null
let colorPickerInstance: ColorPickerDialogInstance | null = null

export function setAlertInstance(instance: AlertDialogInstance): void {
  alertInstance = instance
}

export function setConfirmInstance(instance: ConfirmDialogInstance): void {
  confirmInstance = instance
}

export function setColorPickerInstance(instance: ColorPickerDialogInstance): void {
  colorPickerInstance = instance
}

export async function qAlert(message: string): Promise<void> {
  if (!alertInstance) {
    console.error('qAlertDialog not initialized. Please add qAlertDialog to your App.vue')
    alert(message) // フォールバック
    return
  }
  await alertInstance.show(message)
}

export async function qConfirm(message: string): Promise<boolean> {
  if (!confirmInstance) {
    console.error('qConfirm not initialized. Please map confirm handler in App.vue')
    return confirm(message) // フォールバック
  }
  return await confirmInstance.show(message)
}

export async function qColorPicker(initialColor = '#000000', title = '色選択'): Promise<string | null> {
  if (!colorPickerInstance) {
    console.error('qColorPickerDialog not initialized. Please add qColorPickerDialog to your App.vue')
    return null
  }
  return await colorPickerInstance.show(initialColor, title)
}


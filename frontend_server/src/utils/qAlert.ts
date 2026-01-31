// -*- coding: utf-8 -*-

// ------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU.
// This software is licensed under the MIT License.
// https://github.com/monjyu1101
// Thank you for keeping the rules.
// ------------------------------------------------

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
    console.error('qConfirmDialog not initialized. Please add qConfirmDialog to your App.vue')
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


// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス（非商用） v1.0".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101
// -------------------------------------------------------------------------

import * as monaco from 'monaco-editor'
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

self.MonacoEnvironment = {
  getWorker(_: unknown, label: string) {
    if (label === 'json') return new jsonWorker()
    if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker()
    if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker()
    if (label === 'typescript' || label === 'javascript') return new tsWorker()
    return new editorWorker()
  },
}

const EXTENSION_TO_LANGUAGE: Record<string, string> = {
  py: 'python',
  vue: 'html',
  html: 'html',
  htm: 'html',
  css: 'css',
  scss: 'scss',
  less: 'less',
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  json: 'json',
  md: 'markdown',
  yml: 'yaml',
  yaml: 'yaml',
  sh: 'shell',
  bat: 'bat',
  cmd: 'bat',
  ps1: 'powershell',
  sql: 'sql',
  xml: 'xml',
  svg: 'xml',
  ini: 'ini',
  env: 'ini',
  toml: 'ini',
  txt: 'plaintext',
  log: 'plaintext',
  csv: 'plaintext',
}

export const モナコ言語推定 = (fileName: string): string => {
  const dotIndex = fileName.lastIndexOf('.')
  if (dotIndex < 0) {
    const baseName = fileName.split('/').pop()?.split('\\').pop()?.toLowerCase() ?? ''
    return baseName === 'dockerfile' ? 'dockerfile' : 'plaintext'
  }

  return EXTENSION_TO_LANGUAGE[fileName.slice(dotIndex + 1).toLowerCase()] ?? 'plaintext'
}

export { monaco }
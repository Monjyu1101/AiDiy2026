// -*- coding: utf-8 -*-

// -------------------------------------------------------------------------
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
// -------------------------------------------------------------------------

const MONACO_LANG = {
  py: 'python', vue: 'html', html: 'html', htm: 'html', css: 'css', scss: 'scss', sass: 'scss', less: 'less',
  js: 'javascript', jsx: 'javascript', mjs: 'javascript', cjs: 'javascript', ts: 'typescript', tsx: 'typescript', mts: 'typescript',
  json: 'json', md: 'markdown', yml: 'yaml', yaml: 'yaml', sh: 'shell', bash: 'shell', bat: 'bat', cmd: 'bat', ps1: 'powershell',
  sql: 'sql', xml: 'xml', svg: 'xml', ini: 'ini', env: 'ini', toml: 'ini', cfg: 'ini', conf: 'ini', dockerfile: 'dockerfile',
};
export function monacoLanguage(name) {
  const lower = name.toLowerCase();
  if (lower === 'dockerfile') return 'dockerfile';
  const dot = lower.lastIndexOf('.');
  return dot > 0 ? MONACO_LANG[lower.slice(dot + 1)] ?? 'plaintext' : 'plaintext';
}
let monacoReady = null;
export function loadMonaco() {
  monacoReady ??= new Promise(resolve => {
    const script = document.createElement('script');
    script.src = '/monaco/vs/loader.js';
    script.onload = () => {
      window.require.config({ paths: { vs: '/monaco/vs' } });
      window.require(['vs/editor/editor.main'], () => {
        window.monaco.editor.defineTheme('aidiy-space', {
          base: 'vs-dark', inherit: true, rules: [],
          colors: { 'editor.background': '#05070f', 'editorGutter.background': '#070a16', 'minimap.background': '#05070f', 'editorLineNumber.foreground': '#48536f' },
        });
        resolve(window.monaco);
      }, () => resolve(null));
    };
    script.onerror = () => resolve(null);
    document.head.append(script);
  });
  return monacoReady;
}

// -*- coding: utf-8 -*-
// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

if (window.aidiyDesktop) {
  document.body.classList.add('desktop');
  document.getElementById('window-controls').hidden = false;
  document.querySelectorAll('[data-window]').forEach(button => {
    button.onclick = () => window.aidiyDesktop.windowAction(button.dataset.window);
  });
}

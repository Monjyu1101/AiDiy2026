/*!
 * -*- coding: utf-8 -*-
 *
 * -------------------------------------------------------------------------
 * COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
 * Licensed under "AiDiy 公開利用ライセンス v1.1".
 * Commercial use requires prior written consent from all copyright holders.
 * See LICENSE for full terms. Thank you for keeping the rules.
 * https://github.com/monjyu1101/AiDiy2026
 * -------------------------------------------------------------------------
 */

const { test } = require('node:test');
const assert = require('node:assert/strict');
const { audioPermission, audioRequest } = require('../permissions.cjs');

test('専用画面のマイク: Electron の末尾 / 付き origin を許可する', () => {
  const contents = {}, url = 'http://127.0.0.1:59997/private/';
  const details = { isMainFrame: true, requestingUrl: url, mediaType: 'audio' };
  for (const origin of ['http://127.0.0.1:59997', 'http://127.0.0.1:59997/']) {
    assert.equal(audioPermission(contents, contents, 'media', origin, details, url), true);
  }
  assert.equal(audioRequest(contents, contents, 'media', { ...details, mediaTypes: ['audio'] }, url), true);
});

test('マイク許可をカメラ・別画面・子フレーム・別 origin に広げない', () => {
  const contents = {}, url = 'http://127.0.0.1:59997/private/';
  const details = { isMainFrame: true, requestingUrl: url, mediaType: 'audio' };
  assert.equal(audioPermission({}, contents, 'media', 'http://127.0.0.1:59997/', details, url), false);
  for (const origin of ['http://127.0.0.1:59998/', 'https://example.com', 'invalid']) {
    assert.equal(audioPermission(contents, contents, 'media', origin, details, url), false);
  }
  for (const change of [{ mediaType: 'video' }, { mediaType: 'unknown' }, { isMainFrame: false }, { requestingUrl: url + 'other' }]) {
    assert.equal(audioPermission(contents, contents, 'media', 'http://127.0.0.1:59997/', { ...details, ...change }, url), false);
  }
  for (const types of [['video'], ['audio', 'video'], []]) {
    assert.equal(audioRequest(contents, contents, 'media', { ...details, mediaTypes: types }, url), false);
  }
});

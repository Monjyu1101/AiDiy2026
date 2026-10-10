// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
function liveFrame(requestingUrl, origin) {
  try {
    const target = new URL(requestingUrl);
    return target.origin === origin && /^\/panels\/live\/[a-f0-9]{48}\/$/.test(target.pathname) && !target.search && !target.hash;
  } catch { return false; }
}
function audioRequest(contents, expected, permission, details, origin) {
  return contents === expected && permission === 'media' && details?.isMainFrame === false
    && liveFrame(details.requestingUrl, origin) && details.mediaTypes?.length === 1 && details.mediaTypes[0] === 'audio';
}
function audioCheck(contents, expected, permission, requestingOrigin, details, origin) {
  try {
    return contents === expected && permission === 'media' && new URL(requestingOrigin).origin === origin
      && details?.isMainFrame === false && details.mediaType === 'audio' && liveFrame(details.requestingUrl, origin);
  } catch { return false; }
}
module.exports = { audioRequest, audioCheck };

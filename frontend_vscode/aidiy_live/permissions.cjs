// Electron は requestingOrigin を末尾 / 付きで渡す場合がある。
// URL の origin で比較し、許可先を専用画面の音声入力だけに限定する。
function audioPermission(contents, expectedContents, permission, requestingOrigin, details, pageUrl) {
  if (contents !== expectedContents || permission !== 'media' || details?.isMainFrame !== true
      || details.requestingUrl !== pageUrl || details.mediaType !== 'audio') return false;
  try { return new URL(requestingOrigin).origin === new URL(pageUrl).origin; }
  catch { return false; }
}

function audioRequest(contents, expectedContents, permission, details, pageUrl) {
  return contents === expectedContents && permission === 'media' && details?.isMainFrame === true
    && details.requestingUrl === pageUrl && details.mediaTypes?.length === 1 && details.mediaTypes[0] === 'audio';
}

module.exports = { audioPermission, audioRequest };

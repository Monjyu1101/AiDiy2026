// Console と同じローカル Tools の ping のみ。設定・応答・例外の内容は公開しない。
import http from 'node:http';
import {readConfig} from '../runtime/model_probe.mjs';

// AI/CLI の初期化時に生じる短い応答遅延を接続断と誤判定しない。
// 接続拒否などの確定した通信失敗は、期限を待たずに従来どおり返す。
export const TOOLS_TIMEOUT_MS = 5000;
export const TOOLS_RESPONSE_LIMIT = 16 * 1024;

function checkTools({reader, timeoutMs, signal}) {
  return new Promise(resolve => {
    let request, response, finished = false;
    const finish = (online = false) => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      signal.removeEventListener('abort', abort);
      response?.destroy();
      request?.destroy();
      resolve({online});
    };
    const abort = () => finish();
    const timer = setTimeout(abort, timeoutMs);
    signal.addEventListener('abort', abort, {once:true});
    if (signal.aborted) return finish();
    void readConfig(reader).then(([state, config]) => {
      if (finished) return;
      if (state === '読込不可') return finish();
      const value = config.PORT_TOOLS ?? 8095;
      if (!(typeof value === 'number' || (typeof value === 'string' && /^\d+$/.test(value.trim())))) return finish();
      const port = Number(value);
      if (!Number.isInteger(port) || port < 1 || port > 65535) return finish();
      // node:http はリダイレクトを追跡せず、プロキシ・Cookie・API キーも使わない。
      request = http.request({hostname:'127.0.0.1', port, path:'/aidiy_code_agents/ping', method:'GET', agent:false, maxHeaderSize:8192, headers:{Accept:'application/json'}}, incoming => {
        response = incoming;
        incoming.on('error', abort);
        incoming.on('aborted', abort);
        if (finished) return incoming.destroy();
        if (incoming.statusCode < 200 || incoming.statusCode >= 300) return finish();
        const chunks = [];
        let size = 0;
        incoming.on('data', chunk => {
          if (finished) return;
          size += chunk.length;
          if (size > TOOLS_RESPONSE_LIMIT) return finish();
          chunks.push(chunk);
        });
        incoming.on('end', () => {
          if (finished) return;
          try {
            const body = JSON.parse(new TextDecoder('utf-8', {fatal:true}).decode(Buffer.concat(chunks)).replace(/^\uFEFF/, ''));
            finish(body?.status === 'ok' && body?.name === 'aidiy_code_agents');
          } catch { finish(); }
        });
        incoming.on('close', () => { if (!incoming.complete) finish(); });
      });
      request.on('error', abort);
      request.end();
    }).catch(abort);
  });
}

// 同時の画面更新は一つの ping を共有し、最後の待機者が切断したら通信を止める。
export function createToolsStatusChecker({reader, timeoutMs = TOOLS_TIMEOUT_MS} = {}) {
  timeoutMs = Number.isFinite(timeoutMs) ? Math.max(1, Math.min(TOOLS_TIMEOUT_MS, timeoutMs)) : TOOLS_TIMEOUT_MS;
  let flight;
  return function getStatus({signal} = {}) {
    if (signal?.aborted) return Promise.resolve({online:false});
    if (!flight) {
      const current = {controller:new AbortController(), waiters:new Set()};
      flight = current;
      current.promise = checkTools({reader, timeoutMs, signal:current.controller.signal}).then(result => {
        if (flight === current) flight = undefined;
        for (const finish of [...current.waiters]) finish(result);
      });
    }
    const current = flight;
    return new Promise(resolve => {
      const finish = result => {
        signal?.removeEventListener('abort', abort);
        current.waiters.delete(finish);
        resolve({...result});
      };
      const abort = () => {
        finish({online:false});
        if (!current.waiters.size) {
          if (flight === current) flight = undefined;
          current.controller.abort();
        }
      };
      current.waiters.add(finish);
      signal?.addEventListener('abort', abort, {once:true});
      if (signal?.aborted) abort();
    });
  };
}

export const getToolsStatus = createToolsStatusChecker();

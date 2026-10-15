// backend_diag/runtime/model_probe.ts
import { open, stat } from "node:fs/promises";
import { constants } from "node:fs";
import { fileURLToPath } from "node:url";
import https from "node:https";

// backend_diag/runtime/model_catalog.ts
var empty = () => /* @__PURE__ */ Object.create(null);
var pythonString = (value) => value === null || value === void 0 ? "None" : value === true ? "True" : value === false ? "False" : String(value);
function dateLabel(date) {
  if (!Number.isFinite(date.getTime())) throw new Error("date");
  return `${String(date.getFullYear()).padStart(4, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${String(date.getDate()).padStart(2, "0")}`;
}
function cutoff(now, days) {
  const date = new Date(now);
  date.setDate(date.getDate() - days);
  return date.getTime() / 1e3;
}
function row(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error("shape");
  return value;
}
function entries(body) {
  const items = row(body).data ?? [];
  if (!Array.isArray(items)) throw new Error("shape");
  return items;
}
function number(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error("number");
  return value;
}
function string(value) {
  if (typeof value !== "string") throw new Error("string");
  return value;
}
function openrouterCatalog(body, now = /* @__PURE__ */ new Date()) {
  const out = empty();
  for (const entry of entries(body)) {
    const item = row(entry);
    const id = string(item.id ?? ""), provider = id.includes("/") ? id.split("/")[0].toLowerCase() : "";
    const days = provider === "perplexity" ? 365 : ["google", "openai", "anthropic", "x-ai"].includes(provider) ? 240 : 90;
    const created = number(Object.hasOwn(item, "created") ? item.created : 0);
    if (created < cutoff(now, days)) continue;
    out[id] = { model_id: id, \u30C8\u30FC\u30AF\u30F3\u6570: pythonString(Object.hasOwn(item, "context_length") ? item.context_length : 0), \u30E2\u30C0\u30EA\u30C6\u30A3: Object.hasOwn(row(Object.hasOwn(item, "architecture") ? item.architecture : {}), "modality") ? row(item.architecture).modality : "unknown", \u4F5C\u6210\u65E5: dateLabel(new Date(created * 1e3)) };
  }
  return out;
}
function googleCatalog(models, router = {}) {
  const out = empty();
  for (const model of models) {
    if (!model.supported_actions.includes("generateContent")) continue;
    const id = model.name.replaceAll("models/", "");
    out[id] = { model_id: id, \u30C8\u30FC\u30AF\u30F3\u6570: pythonString(Object.hasOwn(model, "input_token_limit") ? model.input_token_limit : 0), \u30E2\u30C0\u30EA\u30C6\u30A3: model.supported_actions.join(","), \u4F5C\u6210\u65E5: null };
  }
  if (Object.keys(router).length) for (const id of Object.keys(out)) {
    const key = `google/${id}`;
    if (Object.hasOwn(router, key)) out[id].\u4F5C\u6210\u65E5 = router[key].\u4F5C\u6210\u65E5;
    else if (!id.toLowerCase().includes("live")) delete out[id];
  }
  return out;
}
function openaiCatalog(models, router = {}, now = /* @__PURE__ */ new Date()) {
  const out = empty();
  for (const model of models) {
    if (model.created < cutoff(now, 240)) continue;
    out[model.id] = { model_id: model.id, \u30C8\u30FC\u30AF\u30F3\u6570: "0", \u30E2\u30C0\u30EA\u30C6\u30A3: null, \u4F5C\u6210\u65E5: dateLabel(new Date(model.created * 1e3)) };
  }
  if (Object.keys(router).length) for (const id of Object.keys(out)) {
    const key = `openai/${id}`;
    if (Object.hasOwn(router, key)) {
      out[id].\u30C8\u30FC\u30AF\u30F3\u6570 = router[key].\u30C8\u30FC\u30AF\u30F3\u6570;
      out[id].\u30E2\u30C0\u30EA\u30C6\u30A3 = router[key].\u30E2\u30C0\u30EA\u30C6\u30A3;
    }
    if (!id.toLowerCase().includes("realtime") && out[id].\u30C8\u30FC\u30AF\u30F3\u6570 === "0") delete out[id];
  }
  return out;
}
function claudeDate(value) {
  if (!value) return { timestamp: null, label: null };
  try {
    if (value instanceof Date) return { timestamp: value.getTime() / 1e3, label: dateLabel(value) };
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/.test(value)) throw new Error("date");
    const [year, month, day] = value.slice(0, 10).split("-").map(Number);
    const check = new Date(Date.UTC(year, month - 1, day));
    if (check.getUTCFullYear() !== year || check.getUTCMonth() !== month - 1 || check.getUTCDate() !== day) throw new Error("date");
    const parsed = new Date(value.length === 10 ? value + "T00:00:00" : value);
    if (!Number.isFinite(parsed.getTime())) throw new Error("date");
    return { timestamp: parsed.getTime() / 1e3, label: value.slice(0, 10).replaceAll("-", "/") };
  } catch {
    return { timestamp: null, label: null };
  }
}
function claudeCatalog(models, router = {}, now = /* @__PURE__ */ new Date()) {
  const out = empty();
  for (const model of models.data) {
    const created = claudeDate(model.created_at);
    if (created.timestamp !== null && created.timestamp < cutoff(now, 240)) continue;
    out[model.id] = { model_id: model.id, \u30C8\u30FC\u30AF\u30F3\u6570: "0", \u30E2\u30C0\u30EA\u30C6\u30A3: null, \u4F5C\u6210\u65E5: created.label };
  }
  if (Object.keys(router).length) for (const id of Object.keys(out)) {
    let normalized = id;
    if (normalized.length >= 9 && normalized.slice(-9, -8) === "-" && normalized.slice(-8, -6) === "20") normalized = normalized.slice(0, -9);
    if (normalized.length >= 3 && normalized.at(-2) === "-" && ["3", "4", "5"].includes(normalized.at(-3)) && new RegExp("^\\p{Nd}$", "u").test(normalized.at(-1))) normalized = normalized.slice(0, -3) + normalized.at(-3) + "." + normalized.at(-1);
    const key = `anthropic/${normalized}`;
    if (Object.hasOwn(router, key)) {
      out[id].\u30C8\u30FC\u30AF\u30F3\u6570 = router[key].\u30C8\u30FC\u30AF\u30F3\u6570;
      out[id].\u30E2\u30C0\u30EA\u30C6\u30A3 = router[key].\u30E2\u30C0\u30EA\u30C6\u30A3;
    }
  }
  return out;
}
function ollamaCatalog(body, now = /* @__PURE__ */ new Date()) {
  const out = empty();
  const models = entries(body).filter((item) => item !== null && typeof item === "object" && !Array.isArray(item));
  models.sort((a, b) => number(b.created || 0) - number(a.created || 0));
  for (const model of models) {
    if (!model.id || !model.created || number(model.created) < cutoff(now, 240)) continue;
    const id = string(model.id);
    let label = "yyyy/mm/dd";
    try {
      label = dateLabel(new Date(Math.trunc(number(model.created)) * 1e3));
    } catch {
    }
    out[id] = { model_id: id, \u30C8\u30FC\u30AF\u30F3\u6570: "0", \u30E2\u30C0\u30EA\u30C6\u30A3: null, \u4F5C\u6210\u65E5: label };
  }
  return out;
}

// backend_diag/runtime/model_probe.ts
var CONFIG_LIMIT = 128 * 1024;
var RESPONSE_LIMIT = 1024 * 1024;
var PUBLIC_RESPONSE_LIMIT = 16 * 1024 * 1024;
function publicFailureDescription(code) {
  const reasons = { size: "\u516C\u958B\u4E00\u89A7\u306E\u53D7\u4FE1\u30B5\u30A4\u30BA\u304C\u4E0A\u9650\u3092\u8D85\u3048\u307E\u3057\u305F\u3002", output: "\u6574\u5F62\u3057\u305F\u516C\u958B\u4E00\u89A7\u304C\u51FA\u529B\u4E0A\u9650\u3092\u8D85\u3048\u307E\u3057\u305F\u3002", timeout: "\u516C\u958B\u4E00\u89A7\u306E\u901A\u4FE1\u304C\u30BF\u30A4\u30E0\u30A2\u30A6\u30C8\u3057\u307E\u3057\u305F\u3002", dns: "\u516C\u958B\u4E00\u89A7\u30B5\u30FC\u30D0\u30FC\u306E\u540D\u524D\u89E3\u6C7A\u306B\u5931\u6557\u3057\u307E\u3057\u305F\u3002", tls: "\u516C\u958B\u4E00\u89A7\u30B5\u30FC\u30D0\u30FC\u306ETLS\u8A3C\u660E\u66F8\u3092\u691C\u8A3C\u3067\u304D\u307E\u305B\u3093\u3067\u3057\u305F\u3002", http: "\u516C\u958B\u4E00\u89A7\u30B5\u30FC\u30D0\u30FC\u304C\u6B63\u5E38\u306AHTTP\u5FDC\u7B54\u3092\u8FD4\u3057\u307E\u305B\u3093\u3067\u3057\u305F\u3002", json: "\u516C\u958B\u4E00\u89A7\u306E\u5FDC\u7B54\u3092JSON\u3068\u3057\u3066\u8AAD\u307F\u53D6\u308C\u307E\u305B\u3093\u3067\u3057\u305F\u3002", shape: "\u516C\u958B\u4E00\u89A7\u306E\u30C7\u30FC\u30BF\u5F62\u5F0F\u304C\u60F3\u5B9A\u3068\u7570\u306A\u308A\u307E\u3059\u3002", network: "\u516C\u958B\u4E00\u89A7\u30B5\u30FC\u30D0\u30FC\u3078\u63A5\u7D9A\u3067\u304D\u307E\u305B\u3093\u3067\u3057\u305F\u3002\u30CD\u30C3\u30C8\u30EF\u30FC\u30AF\u3084\u30D7\u30ED\u30AD\u30B7\u8A2D\u5B9A\u3092\u78BA\u8A8D\u3057\u3066\u304F\u3060\u3055\u3044\u3002", response: "\u516C\u958B\u4E00\u89A7\u306E\u53D7\u4FE1\u304C\u9014\u4E2D\u3067\u5207\u65AD\u3055\u308C\u307E\u3057\u305F\u3002", stopped: "\u516C\u958B\u4E00\u89A7\u306E\u53D6\u5F97\u3092\u4E2D\u6B62\u3057\u307E\u3057\u305F\u3002", busy: "\u5225\u306E\u30E2\u30C7\u30EB\u78BA\u8A8D\u304C\u5B9F\u884C\u4E2D\u3067\u3059\u3002" };
  return typeof code === "string" && Object.hasOwn(reasons, code) ? reasons[code] : "\u516C\u958B\u4E00\u89A7\u306E\u53D6\u5F97\u51E6\u7406\u306B\u5931\u6557\u3057\u307E\u3057\u305F\u3002";
}
var CONFIG_PATH = fileURLToPath(new URL("../../_config/AiDiy_key.json", import.meta.url));
var KEY_PROVIDERS = Object.freeze([
  ["gemini", "Gemini", "gemini_key_id", "google"],
  ["freeai", "FreeAI\uFF08Gemini\uFF09", "freeai_key_id", "google"],
  ["claude", "Claude", "claude_key_id", "anthropic"],
  ["openai", "OpenAI API", "openai_key_id", "openai"],
  ["azure", "Azure OpenAI", "azure_key_id", null],
  ["copilot", "GitHub Copilot", "copilot_key_id", null],
  ["openrt", "OpenRouter", "openrt_key_id", "openrouter"],
  ["ollama", "Ollama Cloud", "ollama_key_id", "ollama"],
  ["huggingface_read", "Hugging Face \u8AAD\u53D6", "huggingface_key_read", null],
  ["huggingface_write", "Hugging Face \u66F8\u8FBC", "huggingface_key_write", null],
  ["discord", "Discord Bot", "DISCORD_BOT_TOKEN", null]
].map(([id, \u540D\u524D, \u30AD\u30FC\u540D, probe2]) => Object.freeze({ id, \u540D\u524D, \u30AD\u30FC\u540D, probe: probe2 })));
var record = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
async function readConfig(reader) {
  try {
    let raw;
    if (reader) raw = await reader(CONFIG_PATH);
    else {
      const before = await stat(CONFIG_PATH);
      if (!before.isFile() || before.size > CONFIG_LIMIT) throw new Error("file");
      const handle = await open(CONFIG_PATH, constants.O_RDONLY | (constants.O_NONBLOCK ?? 0));
      try {
        const info = await handle.stat();
        if (!info.isFile() || info.size > CONFIG_LIMIT) throw new Error("file");
        const bytes2 = Buffer.alloc(CONFIG_LIMIT + 1);
        let total = 0;
        while (total < bytes2.length) {
          const { bytesRead } = await handle.read(bytes2, total, bytes2.length - total, total);
          if (!bytesRead) break;
          total += bytesRead;
        }
        raw = bytes2.subarray(0, total);
      } finally {
        await handle.close();
      }
    }
    const bytes = typeof raw === "string" ? Buffer.from(raw) : Buffer.from(raw);
    if (bytes.length > CONFIG_LIMIT) throw new Error("size");
    const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes).replace(/^\uFEFF/, ""));
    if (!record(value)) throw new Error("shape");
    return ["\u8AAD\u8FBC\u6E08\u307F", value];
  } catch (error) {
    return [error?.code === "ENOENT" ? "\u672A\u4F5C\u6210" : "\u8AAD\u8FBC\u4E0D\u53EF", {}];
  }
}
function configured(value, id) {
  return typeof value === "string" && !!value.trim() && !value.trim().startsWith("<") && !(id === "ollama" && value.trim().toLowerCase() === "ollama");
}
async function status({ reader } = {}) {
  const [state, values] = await readConfig(reader);
  return { \u8A2D\u5B9A\u72B6\u614B: state, \u9805\u76EE: KEY_PROVIDERS.map((p) => {
    const present = state === "\u8AAD\u8FBC\u4E0D\u53EF" ? null : configured(values[p.\u30AD\u30FC\u540D], p.id), publicRow = p.id === "openrt";
    const reason = state === "\u8AAD\u8FBC\u4E0D\u53EF" ? "\u8A2D\u5B9A\u3092\u8AAD\u307F\u53D6\u308C\u307E\u305B\u3093\u3002" : !present && !publicRow ? "\u30AD\u30FC\u304C\u672A\u8A2D\u5B9A\u3067\u3059\u3002" : !p.probe ? "\u3053\u306E\u9805\u76EE\u306E\u63A5\u7D9A\u30C6\u30B9\u30C8\u306F\u672A\u5BFE\u5FDC\u3067\u3059\u3002" : "";
    return { id: p.id, \u540D\u524D: p.\u540D\u524D, \u30AD\u30FC\u540D: p.\u30AD\u30FC\u540D, \u8A2D\u5B9A\u6E08\u307F: present, \u30AD\u30FC\u4E0D\u8981: publicRow, \u72B6\u614B: "\u672A\u5B9F\u65BD", \u7406\u7531: reason, \u30C6\u30B9\u30C8\u53EF\u80FD: state !== "\u8AAD\u8FBC\u4E0D\u53EF" && !!p.probe && (!!present || publicRow), \u8AAC\u660E: publicRow ? "\u8D77\u52D5\u6642\u306E\u516C\u958B\u30E2\u30C7\u30EB\u4E00\u89A7\u30AD\u30E3\u30C3\u30B7\u30E5\u3092\u8868\u793A\u3057\u307E\u3059\u3002\u30AD\u30FC\u306E\u6709\u52B9\u6027\u306F\u78BA\u8A8D\u3057\u307E\u305B\u3093\u3002" : "\u8A2D\u5B9A\u6709\u7121\u306E\u307F\u3002\u63A5\u7D9A\u306F\u672A\u78BA\u8A8D\u3067\u3059\u3002" };
  }), \u30E2\u30C7\u30EB: [] };
}
var ENDPOINTS = { google: ["generativelanguage.googleapis.com", "/v1beta/models"], anthropic: ["api.anthropic.com", "/v1/models"], openai: ["api.openai.com", "/v1/models"], openrouter: ["openrouter.ai", "/api/v1/models"], ollama: ["ollama.com", "/v1/models"] };
var fetchMetadata = (provider, headers, pageToken, signal) => new Promise((resolve, reject) => {
  const endpoint = ENDPOINTS[provider];
  if (!endpoint) return reject(new Error("provider"));
  let pathname = endpoint[1];
  if (pageToken) {
    if (provider !== "google" || typeof pageToken !== "string" || pageToken.length > 4096) return reject(new Error("pagination"));
    pathname += "?" + new URLSearchParams({ pageToken });
  }
  if (signal?.aborted) return reject(new Error("stopped"));
  const responseLimit = provider === "openrouter" && Object.keys(headers).length === 0 ? PUBLIC_RESPONSE_LIMIT : RESPONSE_LIMIT;
  let settled = false, size = 0;
  const chunks = [];
  const request = https.request({ hostname: endpoint[0], path: pathname, port: 443, method: "GET", agent: false, rejectUnauthorized: true, headers: { Accept: "application/json", ...headers } }, (response) => {
    if (!response.statusCode || response.statusCode < 200 || response.statusCode >= 300) {
      response.destroy();
      return finish(new Error("http"));
    }
    response.on("data", (chunk) => {
      if (settled) return;
      size += chunk.length;
      if (size > responseLimit) return finish(new Error("size"));
      chunks.push(chunk);
    });
    response.on("error", () => finish(new Error("response")));
    response.on("aborted", () => finish(new Error("response")));
    response.on("end", () => {
      if (settled) return;
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        if (!record(body)) return finish(new Error("shape"));
        finish(void 0, body);
      } catch {
        finish(new Error("json"));
      }
    });
  });
  const cancel = () => finish(new Error("stopped"));
  const timer = setTimeout(() => finish(new Error("timeout")), 8e3);
  function finish(error, value) {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    signal?.removeEventListener("abort", cancel);
    request.destroy();
    if (error) reject(error);
    else resolve(value);
  }
  signal?.addEventListener("abort", cancel, { once: true });
  request.on("error", (error) => {
    const code = error.code ?? "";
    const reason = ["ENOTFOUND", "EAI_AGAIN"].includes(code) ? "dns" : ["CERT_HAS_EXPIRED", "DEPTH_ZERO_SELF_SIGNED_CERT", "SELF_SIGNED_CERT_IN_CHAIN", "UNABLE_TO_VERIFY_LEAF_SIGNATURE", "UNABLE_TO_GET_ISSUER_CERT_LOCALLY", "ERR_TLS_CERT_ALTNAME_INVALID"].includes(code) ? "tls" : "network";
    finish(new Error(reason));
  });
  request.end();
});
function safeDetails(models, secrets, limit = 500) {
  const result = [];
  for (const [id, entry] of Object.entries(models)) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._:/@+\-]{0,199}$/.test(id) || !record(entry)) continue;
    const values = { ...entry, model_id: id }, cleaned = {};
    for (const name of ["model_id", "\u4F5C\u6210\u65E5", "\u30C8\u30FC\u30AF\u30F3\u6570", "\u30E2\u30C0\u30EA\u30C6\u30A3"]) {
      const value = values[name];
      let val = value == null ? null : pythonString(value);
      if (val !== null && (val.length > 512 || secrets.some((secret) => val.includes(secret)))) val = null;
      cleaned[name] = val;
    }
    if (cleaned.model_id !== null) result.push(cleaned);
  }
  return limit === null ? result : result.slice(0, limit);
}
function validatedCache(cache) {
  if (!record(cache) || cache.\u516C\u958B\u72B6\u614B !== "\u53D6\u5F97\u6E08" || !record(cache.\u516C\u958B\u30E2\u30C7\u30EB) || Object.values(cache.\u516C\u958B\u30E2\u30C7\u30EB).some((value) => !record(value))) return [{}, false];
  return [Object.fromEntries(safeDetails(cache.\u516C\u958B\u30E2\u30C7\u30EB, [], null).map((item) => [item.model_id, item])), true];
}
async function publicCatalog({ fetch = fetchMetadata, now, signal } = {}) {
  const timestamp = (/* @__PURE__ */ new Date()).toISOString();
  try {
    const body = await fetch("openrouter", {}, void 0, signal);
    if (!Array.isArray(body.data)) throw new Error("shape");
    const details = safeDetails(openrouterCatalog(body, now), [], null);
    const result = { \u72B6\u614B: "OK", \u516C\u958B\u30E2\u30C7\u30EB: Object.fromEntries(details.map((item) => [item.model_id, item])), \u78BA\u8A8D\u65E5\u6642: timestamp, \u8AAC\u660E: "\u516C\u958BOpenRouter\u4E00\u89A7\u306E\u533F\u540D\u53D6\u5F97\u6210\u529F\u3002\u30AD\u30FC\u306E\u6709\u52B9\u6027\u306F\u672A\u78BA\u8A8D\u3067\u3059\u3002" };
    if (Buffer.byteLength(JSON.stringify(result)) > RESPONSE_LIMIT) throw new Error("output");
    return result;
  } catch (error) {
    const candidate = error instanceof Error ? error.message : "";
    const code = ["size", "output", "timeout", "dns", "tls", "http", "json", "network", "response", "stopped"].includes(candidate) ? candidate : "shape";
    return { \u72B6\u614B: "NG", \u516C\u958B\u30E2\u30C7\u30EB: {}, \u78BA\u8A8D\u65E5\u6642: timestamp, \u5931\u6557\u7406\u7531: code, \u8AAC\u660E: publicFailureDescription(code) };
  }
}
async function probe(id, { reader, fetch = fetchMetadata, now, cache, signal } = {}) {
  const output = { id, \u72B6\u614B: "\u672A\u5B9F\u65BD", \u8AAC\u660E: "\u672A\u5BFE\u5FDC\u306E\u9805\u76EE\u3067\u3059\u3002", \u30E2\u30C7\u30EB: [], \u30E2\u30C7\u30EB\u8A73\u7D30: [], \u78BA\u8A8D\u65E5\u6642: null, \u8B66\u544A: [] };
  const selected = KEY_PROVIDERS.find((row2) => row2.id === id);
  if (!selected?.probe) return output;
  const [router, ready] = validatedCache(cache);
  if (id === "openrt") {
    if (!ready) return { ...output, \u8AAC\u660E: "\u8D77\u52D5\u6642\u306E\u516C\u958BOpenRouter\u4E00\u89A7\u304C\u307E\u3060\u5229\u7528\u3067\u304D\u307E\u305B\u3093\u3002\u30AD\u30FC\u306E\u30C6\u30B9\u30C8\u306F\u672A\u5B9F\u65BD\u3067\u3059\u3002" };
    const details = safeDetails(router, []);
    return { ...output, \u72B6\u614B: "OK", \u8AAC\u660E: "\u8D77\u52D5\u6642\u306E\u533F\u540D\u53D6\u5F97\u7D50\u679C\u3092\u8868\u793A\u3002\u30AD\u30FC\u306E\u6709\u52B9\u6027\u30FB\u751F\u6210\u53EF\u5426\u30FB\u8AB2\u91D1\u72B6\u614B\u306F\u672A\u78BA\u8A8D\u3067\u3059\u3002", \u30E2\u30C7\u30EB: details.map((item) => item.model_id), \u30E2\u30C7\u30EB\u8A73\u7D30: details, \u78BA\u8A8D\u65E5\u6642: record(cache) && typeof cache.\u78BA\u8A8D\u65E5\u6642 === "string" ? cache.\u78BA\u8A8D\u65E5\u6642 : null, \u4E00\u89A7\u7BC4\u56F2: "\u516C\u958B\u4E00\u89A7\u306E\u30AD\u30E3\u30C3\u30B7\u30E5\u3002\u6700\u5927500\u4EF6\u3002" };
  }
  const [state, values] = await readConfig(reader);
  if (state === "\u8AAD\u8FBC\u4E0D\u53EF") return { ...output, \u8AAC\u660E: "\u8A2D\u5B9A\u3092\u8AAD\u307F\u53D6\u308C\u307E\u305B\u3093\u3002" };
  const keyValue = values[selected.\u30AD\u30FC\u540D];
  if (!configured(keyValue, id)) return { ...output, \u8AAC\u660E: "\u30AD\u30FC\u304C\u672A\u8A2D\u5B9A\u3067\u3059\u3002" };
  const key = keyValue.trim(), provider = selected.probe, timestamp = (/* @__PURE__ */ new Date()).toISOString();
  const warnings = ["google", "openai", "anthropic"].includes(provider) && !ready ? ["\u8D77\u52D5\u6642\u306E\u516C\u958BOpenRouter\u4E00\u89A7\u304C\u5229\u7528\u3067\u304D\u307E\u305B\u3093\u3002\u5143\u306E\u30E2\u30C7\u30EB\u51E6\u7406\u3068\u540C\u3058\u7A7A\u4E00\u89A7\u6642\u306E\u51E6\u7406\u3067\u3001\u65E5\u4ED8\u30FB\u5BFE\u5FDC\u60C5\u5831\u306E\u88DC\u5B8C\u306A\u3057\u3067\u7D9A\u884C\u3057\u307E\u3057\u305F\u3002"] : [];
  try {
    const headers = provider === "google" ? { "x-goog-api-key": key } : provider === "anthropic" ? { "x-api-key": key, "anthropic-version": "2023-06-01" } : { Authorization: "Bearer " + key };
    if (provider === "openai" && configured(values.openai_organization, "")) headers["OpenAI-Organization"] = values.openai_organization.trim();
    let body = await fetch(provider, headers, void 0, signal), models;
    if (provider === "google") {
      if (!Array.isArray(body.models)) throw new Error("shape");
      const entries2 = [...body.models];
      let token = body.nextPageToken, pages = 1;
      while (token) {
        if (pages >= 20) throw new Error("pages");
        body = await fetch(provider, headers, token, signal);
        if (!Array.isArray(body.models)) throw new Error("shape");
        entries2.push(...body.models);
        token = body.nextPageToken;
        pages++;
      }
      models = googleCatalog(entries2.map((item) => {
        if (!record(item) || typeof item.name !== "string" || item.supportedGenerationMethods !== void 0 && (!Array.isArray(item.supportedGenerationMethods) || item.supportedGenerationMethods.some((x) => typeof x !== "string"))) throw new Error("shape");
        return { name: item.name, supported_actions: item.supportedGenerationMethods ?? [], input_token_limit: item.inputTokenLimit ?? null };
      }), router);
    } else {
      if (!Array.isArray(body.data)) throw new Error("shape");
      if (provider === "openai") models = openaiCatalog(body.data.map((item) => {
        if (!record(item) || typeof item.id !== "string" || typeof item.created !== "number") throw new Error("shape");
        return { id: item.id, created: item.created };
      }), router, now);
      else if (provider === "anthropic") models = claudeCatalog({ data: body.data.map((item) => {
        if (!record(item) || typeof item.id !== "string") throw new Error("shape");
        return { id: item.id, created_at: item.created_at };
      }) }, router, now);
      else models = ollamaCatalog(body, now);
    }
    const secrets = KEY_PROVIDERS.map((p) => values[p.\u30AD\u30FC\u540D]).filter((value) => configured(value, "")).map((value) => value.trim());
    if (configured(values.openai_organization, "")) secrets.push(values.openai_organization.trim());
    const details = safeDetails(models, secrets);
    return { ...output, \u72B6\u614B: "OK", \u30E2\u30C7\u30EB: details.map((item) => item.model_id), \u30E2\u30C7\u30EB\u8A73\u7D30: details, \u78BA\u8A8D\u65E5\u6642: timestamp, \u8B66\u544A: warnings, \u8AAC\u660E: "\u30E2\u30C7\u30EB\u4E00\u89A7API\u53D6\u5F97\u6210\u529F\u3002\u5143\u306E\u30E2\u30C7\u30EB\u51E6\u7406\u3068\u540C\u3058\u7D5E\u308A\u8FBC\u307F\u30FB\u88DC\u5B8C\u3092\u9069\u7528\u3002\u751F\u6210\u53EF\u5426\u30FB\u8AB2\u91D1\u72B6\u614B\u306F\u672A\u78BA\u8A8D\u3067\u3059\u3002", \u4E00\u89A7\u7BC4\u56F2: "\u5143\u306E\u30E2\u30C7\u30EB\u51E6\u7406\u3092\u79FB\u690D\u3057\u305F\u53D6\u5F97\u30E2\u30C7\u30EB\u306E\u7D5E\u308A\u8FBC\u307F\u7D50\u679C\u3001\u8868\u793A\u306F\u6700\u5927500\u4EF6\u3002\u9759\u7684\u30FBOAuth\u5019\u88DC\u306F\u542B\u307F\u307E\u305B\u3093\u3002", \u88DC\u5B8C: ["google", "openai", "anthropic"].includes(provider) ? "\u8D77\u52D5\u6642\u306E\u516C\u958BOpenRouter\u4E00\u89A7\u30AD\u30E3\u30C3\u30B7\u30E5\u3092\u5229\u7528\u3002\u30C6\u30B9\u30C8\u6642\u306E\u8FFD\u52A0\u53D6\u5F97\u306F\u884C\u3044\u307E\u305B\u3093\u3002" : "" };
  } catch {
    return { ...output, \u72B6\u614B: "NG", \u8AAC\u660E: "\u30E2\u30C7\u30EB\u4E00\u89A7API\u306E\u901A\u4FE1\u307E\u305F\u306F\u8A3A\u65AD\u7528\u30E2\u30C7\u30EB\u51E6\u7406\u306B\u5931\u6557\u3057\u307E\u3057\u305F\u3002", \u78BA\u8A8D\u65E5\u6642: timestamp, \u8B66\u544A: warnings };
  }
}
export {
  CONFIG_LIMIT,
  KEY_PROVIDERS,
  PUBLIC_RESPONSE_LIMIT,
  RESPONSE_LIMIT,
  configured,
  fetchMetadata,
  probe,
  publicCatalog,
  publicFailureDescription,
  readConfig,
  safeDetails,
  status,
  validatedCache
};

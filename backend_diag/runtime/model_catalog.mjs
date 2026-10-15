// ../runtime/model_catalog.ts
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
export {
  claudeCatalog,
  googleCatalog,
  ollamaCatalog,
  openaiCatalog,
  openrouterCatalog,
  pythonString
};

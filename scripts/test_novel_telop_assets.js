const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "../frontend_web/public/Xビデオ");
let pages = 0;
let tracks = 0;
for (const name of fs.readdirSync(root)) {
  const page = path.join(root, name);
  if (!fs.statSync(page).isDirectory()) continue;
  const index = path.join(page, "index.html");
  if (!fs.existsSync(index)) continue;
  const html = fs.readFileSync(index, "utf8");
  if (!html.includes("novel_telop_timing.js")) continue;
  for (const script of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (!script[2].trim() || /type="(?:module|importmap)"/.test(script[1])) continue;
    new vm.Script(script[2], { filename: index });
  }
  const scenario = JSON.parse(fs.readFileSync(path.join(page, "scenario.json"), "utf8"));
  const timings = JSON.parse(fs.readFileSync(path.join(page, "telop_timing.json"), "utf8"));
  const timingTag = html.indexOf("novel_telop_timing.js");
  const helperTag = html.indexOf("booklove_telop.js");
  if (helperTag >= 0) assert(timingTag < helperTag, `${name}: script order`);
  for (const scene of scenario.scenes) {
    for (const mode of ["short", "long"]) {
      const anchors = timings[scene.id]?.[mode];
      if (!anchors) continue;
      const narration = String(scene[`${mode}_narration`] || "").replace(/""/g, "").trim();
      const sentenceCount = (narration.match(/[^。！？!?]+[。！？!?]?/g) || []).length;
      assert.equal(anchors.length, sentenceCount, `${name}/${scene.id}/${mode}: sentence count`);
      let previous = 0;
      for (const [start, end] of anchors) {
        assert(start >= previous && end > start, `${name}/${scene.id}/${mode}: cue order`);
        assert(end <= scene[`${mode}_duration_sec`] + 0.5, `${name}/${scene.id}/${mode}: cue duration`);
        previous = end;
      }
      tracks++;
    }
  }
  pages++;
}
assert.equal(pages, 57);
console.log(`novel telop assets: ${pages} pages, ${tracks} aligned tracks OK`);

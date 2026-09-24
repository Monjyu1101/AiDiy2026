const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../frontend_web/public/Xビデオ/_common/novel_telop_timing.js"), "utf8");
const window = {};
let fetchCount = 0;
const context = {
  window,
  fetch: async () => {
    fetchCount++;
    return { ok: true, json: async () => ({ scene_000: { long: [[0, 2], [2.8, 5]] } }) };
  },
  URL,
  location: { href: "http://localhost/Xビデオ/test/index.html" },
};
vm.runInNewContext(source, context);

setImmediate(() => {
  const timing = window.NovelTelopTiming;
  const scene = {
    id: "scene_000",
    long_audio: "audio/long_scene_000.mp3",
    pause_after_speech_text: "",
    pause_after_sec: 1,
  };
  const audio = { currentSrc: "http://localhost/Xビデオ/test/audio/long_scene_000.mp3" };
  const grouped = timing.groups("前半の説明はまだ続いています。後半の説明です。", 8);
  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].length, 1);
  assert.equal(timing.select(scene, "long", audio, grouped, 0.1, 6), "");
  assert.equal(timing.select(scene, "long", audio, grouped, 0.2, 6), grouped[0][0]);
  assert.equal(timing.select(scene, "long", audio, grouped, 1.9, 6), grouped[0][0]);
  assert.equal(timing.select(scene, "long", audio, grouped, 2.3, 6), "");
  assert.equal(timing.select(scene, "long", audio, grouped, 3, 6), grouped[1][0]);
  assert.equal(timing.select(scene, "long", audio, grouped, 5.5, 6), "");
  const blob = { currentSrc: "blob:http://localhost/tts" };
  assert.notEqual(timing.select(scene, "long", blob, grouped, 1, 6), "");
  assert.equal(timing.select(scene, "long", blob, grouped, 5.5, 6), "");
  assert.equal(fetchCount, 1, "playback must not fetch or decode audio");
  console.log("novel telop timing: OK");
});

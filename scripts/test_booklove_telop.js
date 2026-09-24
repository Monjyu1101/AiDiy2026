const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../frontend_web/public/Xビデオ/_common/booklove_telop.js"), "utf8");
const listeners = {};
const classes = new Set();
let textValue = "";
let textWrites = 0;
const subtitle = {
  get textContent() { return textValue; },
  set textContent(value) { textValue = value; textWrites++; },
  classList: {
    add(name) { classes.add(name); },
    remove(name) { classes.delete(name); },
  },
};
const frame = { getAttribute: () => "scene_000.html" };
const modeButton = { textContent: "ロング", addEventListener() {} };
const audio = {
  paused: true,
  ended: false,
  readyState: 4,
  currentTime: 0,
  duration: 6,
  addEventListener(name, callback) { listeners[name] = callback; },
};
const context = {
  document: { getElementById(id) { return { subtitle, sceneFrame: frame, modeBtn: modeButton }[id]; } },
  window: {
    SCENARIO: { scenes: [{ id: "scene_000", long_narration: "テストです。" }] },
    audioPlayer: audio,
    innerWidth: 1200,
    NovelTelopTiming: {
      groups: () => [["テストです。"]],
      select: (_scene, _mode, _audio, _groups, elapsed) => elapsed < 3 ? "テストです。" : "",
    },
  },
  Map,
  WeakMap,
};
vm.runInNewContext(source, context);
assert.equal(subtitle.textContent, "");
audio.paused = false;
audio.currentTime = 1;
listeners.playing();
assert.equal(subtitle.textContent, "テストです。");
assert(classes.has("telop-active"));
const writesAfterStart = textWrites;
listeners.timeupdate();
assert.equal(textWrites, writesAfterStart);
audio.currentTime = 4;
listeners.timeupdate();
assert.equal(subtitle.textContent, "");
audio.currentTime = 1;
listeners.timeupdate();
assert.equal(subtitle.textContent, "テストです。");
audio.paused = true;
listeners.pause();
assert.equal(subtitle.textContent, "");
console.log("booklove telop playback: OK");

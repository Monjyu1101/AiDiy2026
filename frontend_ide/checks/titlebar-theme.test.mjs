// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,compileStyle} from '@vue/compiler-sfc';
const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
const tokens=read('../src/共通表示/タイトルバー配色.css');
const shared=read('../src/共通表示/会話表示.css');
function rules(css){const result=compileStyle({source:css,id:'titlebar-check',scoped:false});assert.deepEqual(result.errors,[]);return result.rawResult.root.nodes.filter(node=>node.type==='rule');}
function values(css,selector){const rule=rules(css).find(rule=>rule.selector===selector);assert.ok(rule,selector);return Object.fromEntries(rule.nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));}
function luminance(hex){const [r,g,b]=hex.slice(1).match(/../g).map(value=>parseInt(value,16)/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4);return .2126*r+.7152*g+.0722*b;}

test('通常タイトル行: 共通tokenは黒に近いグレーと白寄りの文字で本文色を変更しない',()=>{
 const theme=values(tokens,':root');
 assert.deepEqual(theme,{'--aidiy-titlebar-background':'#181b20','--aidiy-titlebar-foreground':'#f3f5f7','--aidiy-titlebar-secondary':'#e1e6ed'});
 assert.equal(rules(tokens).length,1,'配色tokenだけを共有し本文へスタイルを追加しない');
 for(const color of [theme['--aidiy-titlebar-foreground'],theme['--aidiy-titlebar-secondary']])assert.ok((luminance(color)+.05)/(luminance(theme['--aidiy-titlebar-background'])+.05)>12,'通常タイトル行の文字コントラストを確保する');
});

test('通常タイトル行: desktop条件なしの共通ルールで単独窓とIDE内Webを同じ配色にする',()=>{
 assert.match(shared,/@import "\.\/タイトルバー配色\.css";/);
 const header=values(shared,'.panel-brand');
 assert.equal(header.background,'var(--aidiy-titlebar-background)');assert.equal(header.color,'var(--aidiy-titlebar-foreground)');
 assert.equal(header['--surface'],'var(--aidiy-titlebar-background)','最大化アイコンの重なりも新しい背景色へ揃える');
 assert.equal(header['--muted'],'var(--aidiy-titlebar-secondary)','窓操作の補助文字もタイトル行だけ明るくする');
 assert.equal(values(shared,'.panel-brand .connection-label').color,'var(--aidiy-titlebar-secondary)');
 assert.equal(values(shared,':root')['--muted'],'#9aa7b8','本文の補助文字は従来どおり');
 for(const file of ['../src/main.js','../src/タスクチーム/起動.js'])assert.match(read(file),/共通表示\/会話表示\.css/);
 for(const file of ['../src/App.vue','../src/コード/コードパネル.vue','../src/ライブ/ライブパネル.vue','../src/ターミナル/ターミナルパネル.vue','../src/ブラウザ/ブラウザパネル.vue','../src/タスクチーム/タスクチームパネル.vue','../src/ファイル閲覧/閲覧ウィンドウ.vue'])assert.match(read(file),/<StatusBar\b/);
 assert.match(read('../src/App.vue'),/<aside v-if="!desktop"[\s\S]*<CodePanel[\s\S]*<LivePanel[\s\S]*<ConsolePanel/,'IDE内のWebパネルも同じ部品へ進む');
});

test('通常タイトル行: ピンのON/OFFとシアン接続バーの状態色は維持する',()=>{
 assert.equal(values(shared,'.window-actions .window-pin').color,'#748091');
 assert.equal(values(shared,'.window-actions .window-pin.pin-active').color,'#a7f6ff');
 assert.equal(values(shared,'.window-actions .window-all[aria-pressed=true]').color,'#a7f6ff');
 assert.doesNotMatch(tokens,/connection-bar|activity-bar|keyframes/);
});

test('全画面Browserガラス: 通常タイトル配色を継承せず透明背景と黒文字を維持する',()=>{
 const {descriptor}=parse(read('../src/ブラウザ/ブラウザパネル.vue'));
 const glass=values(descriptor.styles[0].content,'.development-app.browser-header-only');
 assert.equal(glass['--aidiy-titlebar-background'],'transparent');
 assert.equal(glass['--aidiy-titlebar-foreground'],'#102c32');
 assert.equal(glass['--aidiy-titlebar-secondary'],'#102c32');
 assert.equal(values(descriptor.styles[0].content,'.browser-header-only .browser-chrome').color,'#102c32');
});

// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,compileStyle} from '@vue/compiler-sfc';

test('Browser全画面ヘッダー: 角丸なし・背景だけを透過し文字と通常表示を保つ',()=>{
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8'));
 const style=compileStyle({source:descriptor.styles[0].content,id:'data-v-browser-header',scoped:true});
 assert.deepEqual(style.errors,[]);
 const rules=style.rawResult.root.nodes.filter(node=>node.type==='rule');
 const values=selector=>Object.fromEntries(rules.find(rule=>rule.selector.startsWith(selector)).nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));
 const header=values('.browser-header-only .browser-chrome');
 assert.equal(header['border-radius'],'0');
 assert.equal(header.background,'linear-gradient(135deg,#17243f66,#2530524d)');
 assert.equal(header.opacity,undefined,'内容全体のopacityは下げない');
 assert.equal(header['text-shadow'],'0 1px 2px #000c','透けた明るいページ上でも文字の輪郭を残す');
 assert.equal(header['backdrop-filter'],'blur(24px) saturate(145%)');
 assert.equal(values('.browser-chrome').background,'#080c1a','通常表示の背景は変えない');
 assert.equal(values('.browser-header-only .browser-toolbar input').background,'#07132266','URL入力の背景は維持する');
});

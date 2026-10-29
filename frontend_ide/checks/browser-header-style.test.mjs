// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,compileStyle} from '@vue/compiler-sfc';

test('Browser全画面ヘッダー: 薄いシアンの四角い厚縁・中央ぼかしなし・黒系文字で通常表示を保つ',()=>{
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8'));
 const style=compileStyle({source:descriptor.styles[0].content,id:'data-v-browser-header',scoped:true});
 assert.deepEqual(style.errors,[]);
 const rules=style.rawResult.root.nodes.filter(node=>node.type==='rule');
 const values=selector=>Object.fromEntries(rules.find(rule=>rule.selector.replaceAll('[data-v-browser-header]','').startsWith(selector)).nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));
 const header=values('.browser-header-only .browser-chrome');
 assert.equal(header['border-radius'],'0');
 assert.equal(header.background,'linear-gradient(135deg,#b9f7fa1f,#dafeff0f)');
 assert.equal(header.opacity,undefined,'内容全体のopacityは下げない');
 assert.equal(header.color,'#102c32');
 assert.equal(header['text-shadow'],'0 1px 1px #efffffe6,0 0 3px #efffffc2','暗いページ上でも黒文字の輪郭を残す');
 assert.equal(header['backdrop-filter'],'none','中央をすりガラスにしない');
 const bevel=values('.browser-header-only .browser-chrome::after');
 assert.equal(bevel['mask-composite'],'exclude','装飾の光沢は縁に限定する');
 assert.equal(bevel['pointer-events'],'none','装飾でボタンやドラッグを遮らない');
 assert.equal(bevel.padding,'8px');
 assert.equal(bevel.border,'0','inset反射影を縁の外端から描く');
 assert.match(bevel.mask,/content-box/,'中央だけを除いて厚み影と反射を残す');
 assert.equal(bevel['border-radius'],'0');
 assert.equal(bevel['z-index'],'0','厚い反射は文字・操作面より下に置く');
 assert.match(bevel['box-shadow'],/inset 0 -3px 1px #14505b99/,'下面の厚みは屈折SVGより上に残す');
 assert.equal(header['box-shadow'],undefined,'不透明な屈折標本の下へ厚み影を隠さない');
 const controls=rules.find(rule=>rule.selector.includes('.browser-header-only')&&rule.selector.includes('.reload-control.refresh-button')&&!rule.selector.includes(':hover'));
 assert.equal(controls.nodes.find(node=>node.prop==='border-radius').value,'0');
 assert.equal(values('.browser-header-only .browser-toolbar input')['border-radius'],'0');
 assert.equal(values('.browser-chrome').background,'#000','通常表示の操作面は黒基準に揃える');
 assert.equal(values('.browser-header-only .browser-toolbar input').background,'#efffffcc','入力欄は局所的な明るい下地で黒文字を読めるようにする');
});

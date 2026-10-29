// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,compileStyle} from '@vue/compiler-sfc';

test('Browser全画面ヘッダー: 薄いシアンの四角いすりガラス・黒系文字で通常表示を保つ',()=>{
 const {descriptor}=parse(readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8'));
 const style=compileStyle({source:descriptor.styles[0].content,id:'data-v-browser-header',scoped:true});
 assert.deepEqual(style.errors,[]);
 const rules=style.rawResult.root.nodes.filter(node=>node.type==='rule');
 const values=selector=>Object.fromEntries(rules.find(rule=>rule.selector.replaceAll('[data-v-browser-header]','').startsWith(selector)).nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));
 const header=values('.browser-header-only .browser-chrome');
 assert.equal(header['border-radius'],'0');
 assert.equal(header.background,'rgba(221,247,250,.72)');
 assert.equal(header.opacity,undefined,'内容全体のopacityは下げない');
 assert.equal(header.color,'#102c32');
 assert.equal(header['text-shadow'],'none','強い光沢や文字縁を重ねない');
 assert.equal(header['backdrop-filter'],'blur(16px)');
 assert.equal(header['-webkit-backdrop-filter'],'blur(16px)');
 assert.equal(header.border,'1px solid #4b929f70');
 assert.equal(header['box-shadow'],undefined);
 assert.ok(!rules.some(rule=>rule.selector.includes('.browser-chrome::')),'屈折や板厚を模した疑似要素を足さない');
 const panel=values('.development-app.browser-header-only');
 assert.equal(panel.width,'100%','800 DIPのnative窓へrendererを追従させる');
 assert.equal(panel['max-width'],'none','renderer側で別の固定幅を重ねない');
 const controls=rules.find(rule=>rule.selector.includes('.browser-header-only')&&rule.selector.includes('.reload-control.refresh-button')&&!rule.selector.includes(':hover'));
 assert.equal(controls.nodes.find(node=>node.prop==='border-radius').value,'0');
 assert.equal(values('.browser-header-only .browser-toolbar input')['border-radius'],'0');
 assert.equal(values('.browser-chrome').background,'#000','通常表示の操作面は黒基準に揃える');
 assert.equal(values('.browser-header-only .browser-toolbar input').background,'#efffffcc','入力欄は局所的な明るい下地で黒文字を読めるようにする');
});

test('Browserすりガラス: 黒い背景でも薄シアンの下地と黒文字のコントラストを確保する',()=>{
 const luminance=rgb=>rgb.map(value=>value/255).map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
 const source=readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8');
 assert.match(source,/background:rgba\(221,247,250,\.72\)/);assert.match(source,/color:#102c32/);
 const foreground=luminance([16,44,50]);
 for(const backdrop of [0,255]){const background=luminance([221,247,250].map(value=>value*.72+backdrop*.28));assert.ok((background+.05)/(foreground+.05)>=4.5,'OSの明暗材質に関わらず小さい文字を読みやすくする');}
});


test('Browserすりガラス: 800 DIPを高倍率や狭い画面で表示しても操作列を折り返す',()=>{
 const source=readFileSync(new URL('../src/ブラウザ/ブラウザパネル.vue',import.meta.url),'utf8');
 const {descriptor}=parse(source),style=compileStyle({source:descriptor.styles[0].content,id:'browser-header-wrap',scoped:false});assert.deepEqual(style.errors,[]);
 const container=style.rawResult.root.nodes.find(node=>node.type==='atrule'&&node.name==='container'&&node.params==='browser-header (max-width:640px)');assert.ok(container);
 const values=selector=>Object.fromEntries(container.nodes.find(rule=>rule.selector===selector).nodes.filter(node=>node.type==='decl').map(node=>[node.prop,node.value]));
 assert.match(source,/container:browser-header \/ inline-size;width:100%/);
 assert.equal(values('.browser-header-only :deep(.panel-brand)')['grid-template-columns'],'minmax(0,1fr)');
 for(const [selector,row] of [['strong','1'],['.connection-label','2'],['.window-actions','3']])assert.equal(values(`.browser-header-only :deep(.panel-brand>${selector})`)['grid-row'],row);
 assert.equal(values('.browser-header-only :deep(.panel-brand>.connection-label)')['white-space'],'normal');
 for(const selector of ['.browser-header-only :deep(.panel-brand>.connection-label)','.browser-header-only :deep(.panel-brand>.window-actions)','.browser-header-only .browser-window-sizes,.browser-header-only .browser-toolbar'])assert.equal(values(selector)['flex-wrap'],'wrap');
 assert.match(source,/if\(chrome.value\)observer.observe\(chrome.value\)/,'折返し後の高さを再測定する');
 assert.match(source,/browserAction\('header-size',chromeHeight.value\)/,'renderer高さをnative窓へ返す');
});

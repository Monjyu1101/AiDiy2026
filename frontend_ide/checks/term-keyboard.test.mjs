// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026

import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { terminalKeyHandler } from '../src/ターミナル/キー入力.js';
const event=(key,extra={})=>({type:'keydown',key,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;},...extra});
test('Term clipboard: 全キー段階でOSのコピー・貼付けを妨げず、制御文字も送らない',()=>{
 const sent=[],handle=terminalKeyHandler(data=>sent.push(data));
 for(const type of ['keydown','keypress','keyup'])for(const key of ['c','C','v','V'])for(const modifier of ['ctrlKey','metaKey'])for(const shiftKey of [false,true]){
  const e=event(key,{type,[modifier]:true,shiftKey});assert.equal(handle(e),false);assert.equal(e.prevented,undefined);
 }
 assert.deepEqual(sent,[]);
});
test('Term modified Enter: Alt・Shiftを区別し、keyup/keypressは二重送信しない',()=>{
 const sent=[],handle=terminalKeyHandler(data=>sent.push(data));
 for(const [modifiers,expected] of [[{altKey:true},'\x1b\r'],[{shiftKey:true},'\x1b[13;2u'],[{altKey:true,shiftKey:true},'\x1b[13;4u']]){
  for(const type of ['keydown','keypress','keyup']){const e=event('Enter',{...modifiers,type});assert.equal(handle(e),false);assert.ok(e.prevented&&e.stopped);}
  assert.equal(sent.at(-1),expected);
 }
 assert.equal(sent.length,3);
});
test('Term IMEと通常キー: 変換確定・AltGr・既存の端末制御をxtermへ委ねる',()=>{
 const handle=terminalKeyHandler(()=>assert.fail('unexpected input'));
 for(const e of [event('Enter'),event('Enter',{shiftKey:true,isComposing:true}),event('Enter',{altKey:true,keyCode:229}),event('c',{ctrlKey:true,altKey:true}),event('d',{ctrlKey:true}),event('Tab'),event('ArrowUp'),event('Enter',{ctrlKey:true,shiftKey:true})]){assert.equal(handle(e),true);assert.equal(e.prevented,undefined);}
});


test('Term clipboard: 実xtermのcopy/paste経路は選択モデル・日本語・bracketed pasteを保持する',()=>{
 const require=createRequire(import.meta.url),{transformSync}=require('esbuild'),module={exports:{}};
 const source=readFileSync(new URL('../node_modules/@xterm/xterm/src/browser/Clipboard.ts',import.meta.url),'utf8');
 vm.runInNewContext(transformSync(source,{loader:'ts',format:'cjs'}).code,{module});
 const {copyHandler,handlePasteEvent}=module.exports;
 const copied=[];let prevented=false;
 copyHandler({clipboardData:{setData:(...args)=>copied.push(args)},preventDefault(){prevented=true;}},{selectionText:'xtermの選択'});
 assert.deepEqual(copied,[['text/plain','xtermの選択']]);assert.ok(prevented);
 for(const bracketedPasteMode of [false,true]){
  const sent=[],textarea={value:'old'};let stopped=false;
  handlePasteEvent({stopPropagation(){stopped=true;},clipboardData:{getData:type=>{assert.equal(type,'text/plain');return '日本語\n2行目';}}},textarea,{decPrivateModes:{bracketedPasteMode},triggerDataEvent:(data,user)=>sent.push([data,user])},{rawOptions:{}});
  assert.deepEqual(sent,[[bracketedPasteMode?'\x1b[200~日本語\r2行目\x1b[201~':'日本語\r2行目',true]]);assert.equal(textarea.value,'');assert.ok(stopped);
 }
});

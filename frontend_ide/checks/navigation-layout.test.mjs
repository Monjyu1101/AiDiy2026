// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1".
// Commercial use requires prior written consent from all copyright holders.
// See LICENSE for full terms. Thank you for keeping the rules.
// https://github.com/monjyu1101/AiDiy2026
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parse,compileTemplate} from '@vue/compiler-sfc';
import {baseParse} from '@vue/compiler-dom';
const source=readFileSync(new URL('../src/components/開発スペース/Navigationパネル.vue',import.meta.url),'utf8');
const {descriptor,errors}=parse(source);
const compiled=compileTemplate({source:descriptor.template.content,filename:'Navigationパネル.vue',id:'navi-layout'});
const attr=(node,name)=>node.props?.find(prop=>prop.type===6&&prop.name===name)?.value?.content;
const hasClass=(node,name)=>attr(node,'class')?.split(' ').includes(name);
const elements=node=>(node.children||[]).filter(child=>child.type===1);
test('総合評価・おすすめプロンプト・モデル欄を明細スクロール外に順序どおり固定する',()=>{
 assert.deepEqual(errors,[]);assert.deepEqual(compiled.errors,[]);
 const panel=elements(baseParse(descriptor.template.content))[0],children=elements(panel);
 const positions=['navigation-display','navigation-overall','navigation-next','navigation-model-footer'].map(name=>children.findIndex(node=>hasClass(node,name)));
 assert.ok(positions.every(index=>index>=0));assert.deepEqual([...positions].sort((a,b)=>a-b),positions);
 const overall=children[positions[1]],next=children[positions[2]];
 for(const node of [overall,next])assert.equal(node.props.find(prop=>prop.type===7&&prop.name==='if').exp.content,'result&&!history');
 assert.match(source,/\.navigation-panel>\.navigation-overall\{flex:none;/);
 assert.match(source,/\.navigation-overall>\.navigation-disclosure\{min-height:0;overflow:auto\}/);
 assert.match(source,/>目標<\/label>/);assert.doesNotMatch(descriptor.template.content,/未評価|>開発目標<\/label>/);
 assert.match(source,/:aria-valuenow="overall.progress"/);assert.match(source,/:aria-valuenow="item.progress"/);
});

const walk=node=>[node,...(node.children||[]).flatMap(walk)];
test('明細と総合の理由は独立したネイティブ開閉で、初期は折りたたむ',()=>{
 const nodes=walk(baseParse(descriptor.template.content));
 const disclosures=nodes.filter(node=>node.tag==='details');
 assert.equal(disclosures.length,2);
 for(const details of disclosures){
  assert.equal(hasClass(details,'navigation-disclosure'),true);
  assert.ok(details.props.every(prop=>!['open','name'].includes(prop.name)));
  const [summary,reasons]=elements(details);
  assert.equal(summary.tag,'summary');assert.equal(hasClass(reasons,'navigation-reasons'),true);
  assert.ok(summary.props.every(prop=>!['role','tabindex'].includes(prop.name)));
  const arrow=walk(summary).find(node=>hasClass(node,'navigation-disclosure-arrow'));
  assert.equal(attr(arrow,'aria-hidden'),'true');
  assert.ok(walk(summary).some(node=>attr(node,'role')==='progressbar'));
 }
 assert.match(source,/content:'▶'/);assert.match(source,/\[open\]>summary .*content:'▽'/);
 assert.match(source,/>summary:focus-visible/);
 assert.equal((source.match(/:key="result.navigationId\|\|result.requestId"/g)||[]).length,2);
});

test('おすすめプロンプトはAI本文をそのまま表示し機械的な説明を付けない',()=>{
 const nodes=walk(baseParse(descriptor.template.content)),section=nodes.find(node=>hasClass(node,'navigation-next'));
 assert.equal(attr(section,'aria-label'),'おすすめプロンプト(案)');
 const heading=walk(section).find(node=>node.tag==='h2');assert.equal(heading.children[0].content,'おすすめプロンプト(案)');
 const prompt=walk(section).find(node=>hasClass(node,'navigation-prompt'));
 const body=elements(prompt)[0];assert.equal(body.children[0].content.content,'recommendedPrompt');
 assert.equal(body.props.find(prop=>prop.type===7&&prop.name==='if').exp.content,'nextItem');
 assert.doesNotMatch(descriptor.template.content,/navigation-purpose|navigation-target|次の一歩/);
 assert.match(source,/clipboard\.writeText\(text\)/);
 assert.doesNotMatch(descriptor.template.content,/プロンプト案です。/);
 const alert=walk(section).find(node=>hasClass(node,'navigation-copy-error'));assert.equal(attr(alert,'role'),'alert');
});

test('CODE/LIVEへは見出しのすぐ右に置き同じ窓内の共通ダイアログで選択する',()=>{
 const nodes=walk(baseParse(descriptor.template.content)),row=nodes.find(node=>hasClass(node,'navigation-prompt-actions'));
 const children=elements(row);assert.equal(children[0].tag,'h2');assert.equal(children[1].children[0].content,'CODE/LIVEへ');
 assert.equal(children[1].props.find(p=>p.type===7&&p.name==='if').exp.content,'nextItem');
 const dialog=nodes.find(node=>node.tag==='DraftHandoffDialog');assert.ok(dialog);assert.match(source,/:insert-draft="draftActions.insertDraft"/);assert.match(source,/:load-targets="draftActions.loadTargets"/);
 assert.doesNotMatch(source,/postMessage|BroadcastChannel|localStorage/);
});

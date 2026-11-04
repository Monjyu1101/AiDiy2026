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
test('総合評価・次の一歩・モデル欄を明細スクロール外に順序どおり固定する',()=>{
 assert.deepEqual(errors,[]);assert.deepEqual(compiled.errors,[]);
 const panel=elements(baseParse(descriptor.template.content))[0],children=elements(panel);
 const positions=['navigation-display','navigation-overall','navigation-next','navigation-model-footer'].map(name=>children.findIndex(node=>hasClass(node,name)));
 assert.ok(positions.every(index=>index>=0));assert.deepEqual([...positions].sort((a,b)=>a-b),positions);
 const overall=children[positions[1]],next=children[positions[2]];
 for(const node of [overall,next])assert.equal(node.props.find(prop=>prop.type===7&&prop.name==='if').exp.content,'result&&!history');
 assert.match(source,/\.navigation-panel>\.navigation-overall\{flex:none;/);
 assert.match(source,/\.navigation-overall>\.navigation-overall-reason\{min-height:0;overflow:auto\}/);
 assert.match(source,/>目標<\/label>/);assert.doesNotMatch(descriptor.template.content,/未評価|>開発目標<\/label>/);
 assert.match(source,/:aria-valuenow="overall.progress"/);assert.match(source,/:aria-valuenow="item.progress"/);
});

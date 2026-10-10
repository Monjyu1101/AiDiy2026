<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue';
const props = defineProps({ tree: Object, root: String, selected: String, current: String, startedAt: Number, open: Boolean, color: { type: Function, default: () => '#bac7da' } });
const emit = defineEmits(['update:open', 'select', 'clear', 'marks']);
const expanded = ref(new Set()), cursor = ref(''), mode = ref('since'), since = ref(props.startedAt), preset = ref('start');
const query = ref(''), caseSensitive = ref(false), matches = ref(new Set()), status = ref(''), treeElement = ref();
const rootExpanded = ref(true), searching = ref(false);
let controller, generation = 0;
const pad = n => String(n).padStart(2, '0');
const dateInput = computed(() => { if (since.value == null) return ''; const d = new Date(since.value); return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; });
const marked = file => mode.value === 'grep' ? matches.value.has(file.path) : since.value != null && file.mtime >= since.value;
const counts = computed(() => {
  const result = new Map();
  function walk(node, prefix) {
    let count = node.f.reduce((n, [name, size, mtime]) => n + (marked({ path: prefix ? `${prefix}/${name}` : name, mtime }) ? 1 : 0), 0);
    for (const dir of node.d) count += walk(dir, prefix ? `${prefix}/${dir.n}` : dir.n);
    result.set(prefix, count); return count;
  }
  if (props.tree) walk(props.tree, ''); return result;
});
const rows = computed(() => {
  const result = [];
  const compare = (a,b) => a.localeCompare(b,'ja',{numeric:true});
  function walk(node, prefix, depth) {
    for (const dir of [...node.d].sort((a,b)=>compare(a.n,b.n))) {
      const path = prefix ? `${prefix}/${dir.n}` : dir.n;
      result.push({ type:'dir',name:dir.n,path,depth,open:expanded.value.has(path),fresh:counts.value.get(path)||0 });
      if (expanded.value.has(path)) walk(dir,path,depth+1);
    }
    for (const [name,size,mtime] of [...node.f].sort((a,b)=>compare(a[0],b[0]))) {
      const path = prefix ? `${prefix}/${name}` : name;
      result.push({ type:'file',name,path,depth,size,mtime,fresh:marked({path,mtime}) });
    }
  }
  if (props.tree && rootExpanded.value) walk(props.tree,'',0); return result;
});
function save() { if (props.root) try { localStorage.setItem(`aidiy_ide:explorer:${props.root}`,JSON.stringify({expanded:[...expanded.value]})); } catch {} }
function toggle(row) { const next=new Set(expanded.value); next.has(row.path)?next.delete(row.path):next.add(row.path); expanded.value=next; save(); }
function reveal(path = props.selected || props.current) {
  if (!path || searching.value) return;
  rootExpanded.value=true;
  const next=new Set(expanded.value), parts=path.split('/');
  for(let i=1;i<parts.length;i++)next.add(parts.slice(0,i).join('/'));
  expanded.value=next;cursor.value=path;save();
  nextTick(()=>treeElement.value?.querySelector(`[data-path="${CSS.escape(path)}"]`)?.scrollIntoView({block:'nearest'}));
}
function select(row, toggleSelection=false) {
  if(toggleSelection&&row.type==='file'&&props.selected===row.path){cursor.value='';emit('clear');return;}
  cursor.value=row.path;
  if(row.type==='dir'){expanded.value=new Set([...expanded.value,row.path]);save();}
  emit('select',{type:row.type,path:row.path});
}
function emitMarks() { emit('marks',{mode:mode.value,since:since.value,paths:[...matches.value]}); }
function clearSearch() { generation++; controller?.abort();matches.value=new Set();status.value='';searching.value=false;rootExpanded.value=true; }
function scrollToTop() { if(treeElement.value)treeElement.value.scrollTop=0; }
function choose(value) {
  preset.value=value;
  if(value==='start')since.value=props.startedAt;
  else if(value==='ten')since.value=Date.now()-600000;
  else if(value==='hour')since.value=Date.now()-3600000;
  else if(value==='today'){const d=new Date();d.setHours(0,0,0,0);since.value=d.getTime();}
  else since.value=null;
}
async function grep() {
  clearSearch();expanded.value=new Set();cursor.value='';save();scrollToTop();
  if(!query.value.trim())return;
  const run=generation;controller=new AbortController();status.value='検索中…';searching.value=true;rootExpanded.value=false;
  try {
    const response=await fetch('/api/grep?'+new URLSearchParams({q:query.value,case:caseSensitive.value?'1':'0'}),{signal:controller.signal});
    if(!response.ok)throw Error(await response.text());const result=await response.json();
    if(run!==generation)return;
    matches.value=new Set(result.paths);
    const next=new Set();
    for(const path of result.paths){const parts=path.split('/');for(let i=1;i<parts.length;i++)next.add(parts.slice(0,i).join('/'));}
    expanded.value=next;save();
    status.value=`${result.paths.length}ファイル一致（検索 ${result.checked}・対象外 ${result.skipped}）${result.truncated?' ※一部の結果':''}`;
  }catch(e){if(run===generation)status.value=`検索できません: ${e.message}`;}
  finally{if(run===generation){searching.value=false;rootExpanded.value=true;nextTick(scrollToTop);}}
}
function key(event) {
  const index=rows.value.findIndex(row=>row.path===cursor.value), row=rows.value[index];let next=index;
  if(event.key==='ArrowDown')next=Math.min(rows.value.length-1,index+1);
  else if(event.key==='ArrowUp')next=Math.max(0,index-1);
  else if(event.key==='Home')next=0;
  else if(event.key==='End')next=rows.value.length-1;
  else if(event.key==='ArrowRight'&&row?.type==='dir'&&!row.open)toggle(row);
  else if(event.key==='ArrowLeft'&&row?.type==='dir'&&row.open)toggle(row);
  else if(event.key==='Enter'&&row)select(row);
  else return;
  event.preventDefault();event.stopPropagation();if(rows.value[next]){cursor.value=rows.value[next].path;reveal(cursor.value);}
}
watch(()=>props.root,()=>{try{expanded.value=new Set(JSON.parse(localStorage.getItem(`aidiy_ide:explorer:${props.root}`)||'{}').expanded||[]);}catch{expanded.value=new Set();}},{immediate:true});
watch(()=>[props.selected,props.current,props.open],()=>{if(props.open)reveal();});
watch(()=>props.startedAt,()=>{mode.value='since';choose('start');clearSearch();});
watch(mode,clearSearch);
watch([mode,since,matches],emitMarks,{immediate:true});
onBeforeUnmount(()=>{generation++;controller?.abort();});
defineExpose({reveal});
</script>
<template>
  <div class="explorer-component" data-component="FileExplorer">
    <button v-if="!open" class="explorer-toggle" aria-label="エクスプローラーを開く" :aria-expanded="false" @click="emit('update:open',true)">☰</button>
    <aside v-show="open" class="explorer-panel" aria-label="ファイルエクスプローラー">
      <header><button aria-label="エクスプローラーを閉じる" :aria-expanded="true" @click="emit('update:open',false)">☰</button><span>エクスプローラー</span><button title="選択位置を表示" @click="reveal()">◎</button><button title="すべて閉じる" @click="expanded=new Set();save()">⊟</button></header>
      <section class="explorer-search"><small>表示中: {{ current || tree?.n }}</small>
        <fieldset><legend class="sr-only">検索方法</legend><label><input v-model="mode" type="radio" value="since">起点検索</label><label><input v-model="mode" type="radio" value="grep">grep検索</label></fieldset>
        <div v-if="mode==='since'"><label>起点 <input type="datetime-local" step="1" :value="dateInput" @change="since=$event.target.value?new Date($event.target.value).getTime():null;preset='custom'"></label><div class="since-presets"><button v-for="[value,label] in [['start','起動'],['ten','10分'],['hour','1時間'],['today','今日'],['clear','解除']]" :key="value" :aria-pressed="preset===value" @click="choose(value)">{{ label }}</button></div></div>
        <form v-else @submit.prevent>
          <label class="grep-query">ファイル内容<input v-model="query" type="search" maxlength="256" placeholder="検索する文字列"></label>
          <label><input v-model="caseSensitive" type="checkbox">大文字・小文字を区別</label>
          <div><button type="button" @click="grep">検索</button><button type="button" @click="query='';clearSearch()">解除</button></div>
          <p role="status">{{ status }}</p>
        </form>
      </section>
      <button class="explorer-root" :title="root" :aria-expanded="rootExpanded" :disabled="searching" @click="rootExpanded=!rootExpanded"><span>{{ rootExpanded?'▾':'▸' }}</span> {{ rootExpanded?'📂':'📁' }} {{ tree?.n }}</button>
      <ul ref="treeElement" role="tree" tabindex="0" @keydown="key"><li v-for="row in rows" :key="row.path" role="treeitem" :aria-expanded="row.type==='dir'?row.open:undefined" :aria-selected="selected===row.path" :data-path="row.path" :style="{'--depth':row.depth}" :class="{fresh:row.fresh,selected:selected===row.path,cursor:cursor===row.path}" @click="select(row,true)">
        <button v-if="row.type==='dir'" class="chevron" :aria-label="row.open?'折りたたむ':'展開する'" @click.stop="toggle(row)">{{ row.open?'▾':'▸' }}</button><span v-else class="chevron"></span><span v-if="row.type==='dir'">{{ row.open?'📂':'📁' }}</span><span v-else class="file-dot" :style="{color:color(row.name)}">●</span><span class="file-name">{{ row.name }}</span><span class="file-meta">{{ row.type==='dir'?(row.fresh?`更新 ${row.fresh}`:''):new Date(row.mtime).toLocaleTimeString('ja-JP',{hour:'2-digit',minute:'2-digit'}) }}</span><span v-if="row.fresh">●</span>
      </li></ul>
    </aside>
  </div>
</template>

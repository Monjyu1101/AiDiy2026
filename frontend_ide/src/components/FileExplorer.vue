<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, shallowRef, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import AISearchPanel from './AISearchPanel.vue';
const props = defineProps({ tree: Object, root: String, selected: String, current: String, navigating: Boolean, startedAt: Number, open: Boolean, viewHistory: { type: Array, default: () => [] }, filter: { type: Boolean, default: true }, color: { type: Function, default: () => '#bac7da' } });
const emit = defineEmits(['update:open', 'select', 'clear', 'marks', 'latest', 'route']);
// 一覧は宇宙と同じ（props.tree）。フィルター（星空画面の左下）が ON なら、宇宙もこの一覧もバックアップ対象だけになる。
const tree = computed(() => props.tree);
// 今の一覧の中で一番新しく更新されたファイル（最下部に表示）。
// 一覧から求めた値に加え、約1分ごとにサーバーへ最新だけを問い合わせて差し替える（一覧そのものは取り直さない）。
const listLatest = computed(() => {
  let best = null;
  (function walk(node, prefix) {
    if (!node) return;
    for (const [name, size, mtime] of node.f) if (!best || mtime > best.mtime) best = { name, path: prefix ? `${prefix}/${name}` : name, mtime };
    for (const dir of node.d) walk(dir, prefix ? `${prefix}/${dir.n}` : dir.n);
  })(tree.value, '');
  return best;
});
const polled = shallowRef(null);
let latestRun = 0;
async function pollLatest() {
  if (document.hidden) return;   // 裏に隠れている間は問い合わせない
  const run = ++latestRun, forFilter = props.filter;
  try {
    const response = await fetch('/api/latest?' + new URLSearchParams(forFilter ? { filter: 'backup' } : {}), { cache: 'no-store' });
    if (!response.ok) return;
    const { latest } = await response.json();
    if (run === latestRun && forFilter === props.filter) polled.value = latest ? { ...latest, filter: forFilter } : null;
  } catch { /* 次の周期で再試行 */ }
}
const latest = computed(() => {
  const fromList = listLatest.value, fromPoll = polled.value?.filter === props.filter ? polled.value : null;
  return !fromPoll || (fromList && fromList.mtime >= fromPoll.mtime) ? fromList : fromPoll;
});
const latestTimer = setInterval(pollLatest, 60_000);
// 最終更新を外へ知らせる（視点移動中の「最終更新ファイルの表示」に使う）。フィルター ON の時だけ（OFF はデータベースなどが毎分変わるため）。
// 起動直後の最初の値（前日などの最終更新でも）と、その後「より新しいファイル」に変わった時に知らせる。フィルター切替直後は基準を覚えるだけ。
let latestBase = null, initialSent = false;
watch(latest, value => {
  if (!value) return;
  const initial = props.filter && !initialSent;
  const newer = props.filter && latestBase && latestBase.filter === props.filter && value.mtime > latestBase.mtime;
  latestBase = { filter: props.filter, mtime: value.mtime };
  if (initial) initialSent = true;
  if (initial || newer) emit('latest', { path: value.path, mtime: value.mtime, initial });
}, { immediate: true });
watch(() => props.filter, () => { polled.value = null; void pollLatest(); });
const latestTime = computed(() => latest.value ? new Date(latest.value.mtime).toLocaleString('ja-JP', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '');
const expanded = ref(new Set()), cursor = ref(''), mode = ref('since'), since = ref(props.startedAt), preset = ref('start');
const aiResult=shallowRef(null),routeMode=ref('view');
const aiFiles=computed(()=>new Map((aiResult.value?.files||[]).map(file=>[file.path,file.reason])));
const aiRoute=computed(()=>aiResult.value?.route||[]);
const routeListOpen=ref(false),routeElement=ref(),viewRoute=ref([]);
const viewedFiles=computed(()=>props.viewHistory.filter(entry=>entry?.type==='file'&&typeof entry.path==='string'));
function syncViewRoute(){viewRoute.value=[...new Set(viewedFiles.value.map(entry=>entry.path))];}
watch(viewedFiles,entries=>{
  const paths=[...new Set(entries.map(entry=>entry.path))];
  // 一覧から再訪しても表示順を入れ替えず、前・次で同じ2件を往復するのを防ぐ。
  viewRoute.value=routeListOpen.value&&routeMode.value==='view'
    ? [...paths.filter(path=>!viewRoute.value.includes(path)),...viewRoute.value.filter(path=>paths.includes(path))] : paths;
},{immediate:true});
const routePaths=computed(()=>routeMode.value==='ai'?aiRoute.value:viewRoute.value);
const viewedAt=path=>{const at=viewedFiles.value.find(entry=>entry.path===path)?.at;return Number.isFinite(at)?new Date(at).toLocaleString('ja-JP',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'';};
function closeRouteList(event){if(!routeElement.value?.contains(event.target))routeListOpen.value=false;}
onMounted(()=>document.addEventListener('pointerdown',closeRouteList));
const hiddenAI=computed(()=>{
  const paths=new Set();
  function walk(node,prefix=''){if(!node)return;for(const [name] of node.f)paths.add(prefix+name);for(const dir of node.d)walk(dir,prefix+dir.n+'/');}
  walk(tree.value);return aiRoute.value.filter(path=>!paths.has(path)).length;
});
const routeIndex=computed(()=>routePaths.value.indexOf(cursor.value||props.selected));
function chooseRoute(value){
  const opening=routeMode.value!==value||!routeListOpen.value;
  routeMode.value=value;routeListOpen.value=opening;
  if(value==='ai')mode.value='ai';else if(opening)syncViewRoute();
}
function stepRoute(offset){const index=routeIndex.value<0?(offset>0?0:routePaths.value.length-1):routeIndex.value+offset;const path=routePaths.value[index];if(path)select({type:'file',path});}
function acceptAI(result,activate=true){
  aiResult.value=result;if(activate){mode.value='ai';routeMode.value='ai';}
  if(!result)return;
  if(pendingSince&&!activate)return;
  cancelSinceExpansion();
  // 結果の到着では移動しない。一覧に関連ファイルの親だけを展開する。
  const next=new Set(expanded.value);
  for(const path of result.route){const parts=path.split('/');for(let i=1;i<parts.length;i++)next.add(parts.slice(0,i).join('/'));}
  expanded.value=next;rootExpanded.value=true;save();
}
const query = ref(''), caseSensitive = ref(false), matches = ref(new Set()), status = ref(''), treeElement = ref();
const rootExpanded = ref(true), searching = ref(false);
const leavingRows=new Set();
let pendingSince=null,sinceExpandTimer;
function cancelSinceExpansion(){clearTimeout(sinceExpandTimer);pendingSince=null;}
function finishSinceCollapse(){
  clearTimeout(sinceExpandTimer);
  if(!pendingSince||leavingRows.size)return;
  // 全行の折りたたみが終わってから、ルートだけの状態を挟んで展開する。
  sinceExpandTimer=setTimeout(()=>{
    if(!pendingSince||leavingRows.size)return;
    expanded.value=pendingSince;pendingSince=null;rootExpanded.value=true;save();nextTick(scrollToTop);
  },matchMedia('(prefers-reduced-motion: reduce)').matches?0:60);
}
function beforeTreeLeave(element){leavingRows.add(element);}
function afterTreeLeave(element){leavingRows.delete(element);finishSinceCollapse();}
let controller, generation = 0;
const pad = n => String(n).padStart(2, '0');
const dateInput = computed(() => { if (since.value == null) return ''; const d = new Date(since.value); return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; });
const marked = file => mode.value === 'ai' ? aiFiles.value.has(file.path) : mode.value === 'grep' ? matches.value.has(file.path) : since.value != null && file.mtime >= since.value;
const counts = computed(() => {
  const result = new Map();
  function walk(node, prefix) {
    let count = node.f.reduce((n, [name, size, mtime]) => n + (marked({ path: prefix ? `${prefix}/${name}` : name, mtime }) ? 1 : 0), 0);
    for (const dir of node.d) count += walk(dir, prefix ? `${prefix}/${dir.n}` : dir.n);
    result.set(prefix, count); return count;
  }
  if (tree.value) walk(tree.value, ''); return result;
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
  if (tree.value && rootExpanded.value) walk(tree.value,'',0); return result;
});
function save() { if (props.root) try { localStorage.setItem(`aidiy_ide:explorer:${props.root}`,JSON.stringify({expanded:[...expanded.value]})); } catch {} }
function toggle(row) { cancelSinceExpansion();const next=new Set(expanded.value); next.has(row.path)?next.delete(row.path):next.add(row.path); expanded.value=next; save(); }
function reveal(path = props.selected || props.current) {
  if (!path || searching.value || pendingSince) return;
  rootExpanded.value=true;
  const next=new Set(expanded.value), parts=path.split('/');
  for(let i=1;i<parts.length;i++)next.add(parts.slice(0,i).join('/'));
  expanded.value=next;cursor.value=path;save();
  nextTick(()=>treeElement.value?.querySelector(`[data-path="${CSS.escape(path)}"]`)?.scrollIntoView({block:'nearest'}));
}
function select(row, toggleSelection=false) {
  cancelSinceExpansion();
  if(toggleSelection&&!props.navigating&&row.type==='file'&&props.selected===row.path){cursor.value='';emit('clear');return;}
  cursor.value=row.path;
  if(row.type==='dir'){if(row.path==='')rootExpanded.value=true;else expanded.value=new Set([...expanded.value,row.path]);save();}
  emit('select',{type:row.type,path:row.path});
}
function emitMarks() { emit('marks',{mode:mode.value,since:since.value,paths:mode.value==='ai'?[...aiFiles.value.keys()]:[...matches.value]}); }
function clearSearch() { cancelSinceExpansion();generation++; controller?.abort();matches.value=new Set();status.value='';searching.value=false;rootExpanded.value=true; }
function scrollToTop() { if(treeElement.value)treeElement.value.scrollTop=0; }
function expandSinceMatches() {
  // 以前の手動展開を引き継がず、一致ファイルにつながるフォルダだけを開く。
  cancelSinceExpansion();
  pendingSince=new Set([...counts.value].filter(([path,count])=>path&&count>0).map(([path])=>path));
  expanded.value=new Set();rootExpanded.value=false;cursor.value='';
  nextTick(()=>{scrollToTop();finishSinceCollapse();});
}
function choose(value) {
  preset.value=value;
  if(value==='start')since.value=props.startedAt;
  else if(value==='ten')since.value=Date.now()-600000;
  else if(value==='hour')since.value=Date.now()-3600000;
  else if(value==='today'){const d=new Date();d.setHours(0,0,0,0);since.value=d.getTime();}
  else since.value=null;
  expandSinceMatches();
}
function chooseDate(value) { since.value=value?new Date(value).getTime():null;preset.value='custom';expandSinceMatches(); }
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
watch(()=>props.root,()=>{
  aiResult.value=null;routeMode.value='view';
  routeListOpen.value=false;
},{immediate:true});
watch([routeMode,aiRoute],()=>emit('route',{mode:routeMode.value,paths:aiRoute.value}),{immediate:true});
watch(()=>[props.selected,props.current,props.open],()=>{if(props.open&&!props.navigating)reveal();});
watch(()=>props.startedAt,()=>{mode.value='since';clearSearch();since.value=props.startedAt;preset.value='start';});
watch(mode,clearSearch);
watch([mode,since,matches,aiResult],emitMarks,{immediate:true});
onBeforeUnmount(()=>{cancelSinceExpansion();generation++;controller?.abort();clearInterval(latestTimer);latestRun++;document.removeEventListener('pointerdown',closeRouteList);});
defineExpose({reveal});
</script>
<template>
  <div class="explorer-component" data-component="FileExplorer">
    <button v-if="!open" class="explorer-toggle" aria-label="エクスプローラーを開く" :aria-expanded="false" @click="emit('update:open',true)">☰</button>
    <div ref="routeElement" class="explorer-routes" :class="{'explorer-collapsed':!open}" role="group" aria-label="軌跡表示" @keydown.esc.stop.prevent="routeListOpen=false">
      <button class="route-choice" :aria-pressed="routeMode==='view'" :aria-expanded="routeMode==='view'&&routeListOpen" aria-controls="route-file-list" @click="chooseRoute('view')">閲覧軌跡</button><button class="route-choice" :aria-pressed="routeMode==='ai'" :aria-expanded="routeMode==='ai'&&routeListOpen" aria-controls="route-file-list" @click="chooseRoute('ai')">AiDiy検索軌跡</button>
      <button title="プロジェクトルートへ" @click="select({type:'dir',path:''})">ルート</button><button :aria-label="routeMode==='ai'?'前の関連ファイル':'前の閲覧ファイル'" :disabled="!routePaths.length||routeIndex===0" @click="stepRoute(-1)">&lt;</button><button :aria-label="routeMode==='ai'?'次の関連ファイル':'次の閲覧ファイル'" :disabled="!routePaths.length||routeIndex===routePaths.length-1" @click="stepRoute(1)">&gt;</button>
      <section v-if="routeListOpen" id="route-file-list" class="route-file-list" :aria-label="routeMode==='ai'?'AiDiy検索軌跡のファイル一覧':'閲覧軌跡のファイル一覧'">
        <p v-if="routeMode==='ai'&&aiResult" class="ai-route-title" :title="aiResult.query">{{ aiResult.title || aiResult.query }}</p>
        <p>{{ routeMode==='ai'?'AiDiy検索軌跡':'閲覧軌跡（最近開いた順）' }} · {{ routePaths.length }}件</p>
        <ol v-if="routePaths.length"><li v-for="path in routePaths" :key="path"><button :data-route-path="path" :aria-current="path===selected?'true':undefined" :title="routeMode==='ai'?aiFiles.get(path):path" @click="select({type:'file',path})"><span>{{ path }}</span><small v-if="routeMode==='ai'">{{ aiFiles.get(path) }}</small><small v-else>{{ viewedAt(path) }}</small></button></li></ol>
        <p v-else>{{ routeMode==='ai'?'AiDiy検索の結果を選ぶと、ここに表示します。':'ファイルを開くと、ここに表示します。' }}</p>
      </section>
    </div>
    <aside v-show="open" class="explorer-panel" :class="{'ai-search-mode':mode==='ai'}" aria-label="ファイルエクスプローラー">
      <header><button aria-label="エクスプローラーを閉じる" :aria-expanded="true" @click="emit('update:open',false)">☰</button><span>エクスプローラー</span><button v-show="mode!=='ai'" title="選択位置を表示" @click="cancelSinceExpansion();reveal()">◎</button><button v-show="mode!=='ai'" title="すべて閉じる" @click="cancelSinceExpansion();rootExpanded=true;expanded=new Set();save()">⊟</button></header>
      <section class="explorer-search"><small>表示中: {{ current || tree?.n }}</small>
        <fieldset><legend class="sr-only">検索方法</legend><label><input v-model="mode" type="radio" value="since">起点検索</label><label><input v-model="mode" type="radio" value="grep">grep検索</label><label><input v-model="mode" type="radio" value="ai">AiDiy検索</label></fieldset>
        <div v-if="mode==='since'"><label>起点 <input type="datetime-local" step="1" :value="dateInput" @change="chooseDate($event.target.value)"></label><div class="since-presets"><button v-for="[value,label] in [['start','起動'],['ten','10分'],['hour','1時間'],['today','今日'],['clear','解除']]" :key="value" :aria-pressed="preset===value" @click="choose(value)">{{ label }}</button></div></div>
        <form v-else-if="mode==='grep'" @submit.prevent>
          <label class="grep-query">ファイル内容<input v-model="query" type="search" maxlength="256" placeholder="検索する文字列"></label>
          <label><input v-model="caseSensitive" type="checkbox">大文字・小文字を区別</label>
          <div><button type="button" @click="grep">検索</button><button type="button" @click="query='';clearSearch()">解除</button></div>
          <p role="status">{{ status }}</p>
        </form>
        <AISearchPanel :key="root" :root="root" v-show="mode==='ai'" @result="acceptAI" />
        <div v-if="mode==='ai'&&aiResult" class="ai-route-results"><p v-if="hiddenAI">{{ hiddenAI }}件は現在の一覧にありません。フィルターをOFFにするか一覧を更新してください。</p><p :title="aiResult.query">{{ aiResult.title || aiResult.query }} · {{ aiRoute.length }}件</p><ol><li v-for="path in aiRoute" :key="path"><button :title="aiFiles.get(path)" @click="select({type:'file',path})">{{ path }}</button><small>{{ aiFiles.get(path) }}</small></li></ol></div>
      </section>
      <div class="explorer-root" :title="root">
        <button class="chevron" :aria-label="rootExpanded?'ルートフォルダを折りたたむ':'ルートフォルダを展開する'" :aria-expanded="rootExpanded" :disabled="searching" @click="cancelSinceExpansion();rootExpanded=!rootExpanded">{{ rootExpanded?'▾':'▸' }}</button>
        <button class="explorer-root-name" :disabled="searching" @click="select({type:'dir',path:''})"><span aria-hidden="true">{{ rootExpanded?'📂':'📁' }}</span><span class="file-name">{{ tree?.n }}</span></button>
      </div>
      <ul ref="treeElement" role="tree" tabindex="0" @keydown="key"><TransitionGroup name="explorer-branch" @before-leave="beforeTreeLeave" @after-leave="afterTreeLeave" @leave-cancelled="afterTreeLeave"><li v-for="row in rows" :key="row.path" role="treeitem" :aria-expanded="row.type==='dir'?row.open:undefined" :aria-selected="selected===row.path" :data-path="row.path" :title="mode==='ai'?aiFiles.get(row.path):undefined" :style="{'--depth':row.depth}" :class="{fresh:row.fresh,selected:selected===row.path,cursor:cursor===row.path}" @click="select(row,true)">
        <button v-if="row.type==='dir'" class="chevron" :aria-label="row.open?'折りたたむ':'展開する'" @click.stop="toggle(row)">{{ row.open?'▾':'▸' }}</button><span v-else class="chevron"></span><span v-if="row.type==='dir'">{{ row.open?'📂':'📁' }}</span><span v-else class="file-dot" :style="{color:color(row.name)}">●</span><span class="file-name">{{ row.name }}</span><span class="file-meta">{{ row.type==='dir'?(row.fresh?`${mode==='ai'?'関連':'更新'} ${row.fresh}`:''):new Date(row.mtime).toLocaleTimeString('ja-JP',{hour:'2-digit',minute:'2-digit'}) }}</span><span v-if="row.fresh">●</span>
      </li></TransitionGroup></ul>
      <!-- 最下部: 今の一覧で最後に更新されたファイル（フィルターは星空画面の左下） -->
      <footer class="explorer-footer">
        
        <button v-if="latest" class="explorer-latest" :title="`最終更新: ${latest.path}`" @click="select({type:'file',path:latest.path})"><small>最終更新</small><span class="file-dot" :style="{color:color(latest.name)}">●</span><span class="file-name">{{ latest.name }}</span><span class="file-meta">{{ latestTime }}</span></button>
      </footer>

    </aside>
  </div>
</template>

<!-- COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
Licensed under "AiDiy 公開利用ライセンス v1.1".
Commercial use requires prior written consent from all copyright holders.
See LICENSE for full terms. Thank you for keeping the rules.
https://github.com/monjyu1101/AiDiy2026 -->
<script setup>
import { ref, shallowRef, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { createRouteExpansion } from '../ファイル閲覧/軌跡パネル展開.js';
import { createPanelWindow, fadePanel } from '../ファイル閲覧/パネル別窓.js';
import AISearchPanel from '../ファイル検索/AI検索パネル.vue';
import FileTypeIcon from '../ファイル閲覧/ファイル種別アイコン.vue';
import { latestFiles, createLatestUpdates } from '../ファイル閲覧/最新ファイル.js';
import { scanWarning } from '../ファイル閲覧/走査警告.js';
import { searchRouteRecords } from '../開発スペース/経路記録.js';
import { routeTreeRows, viewTreeRecords, routeNavigationSteps } from '../開発スペース/軌跡ツリー.js';
const props = defineProps({ tree: Object, scan: Object, root: String, selected: String, current: String, navigating: Boolean, startedAt: Number, open: Boolean, allDisplays: Boolean, viewHistory: { type: Array, default: () => [] }, viewVoyages: { type: Object, default: () => ({}) }, filter: { type: Boolean, default: true }, color: { type: Function, default: () => '#bac7da' } });
const emit = defineEmits(['update:open', 'select', 'clear', 'marks', 'latest', 'freshness', 'route', 'clear-view-history', 'detached']);
const panel=ref(),detached=ref(false),pinError=ref('');
let panelWindow,routeWindow;
// 軌跡バーはエクスプローラーと同じく、最初は閉じて縦三本の正方形ボタンだけを出す。
const routeDetached=ref(false),routeClosed=ref(true),preparingAll=ref(false);
function pinRoutes(){
  routeClosed.value=false;
  routeWindow??=createPanelWindow({element:()=>routeElement.value,title:'軌跡',kind:'panel-routes',className:'routes-window',
    rectangle:()=>({getBoundingClientRect:()=>{const rect=routeElement.value.getBoundingClientRect();return{left:rect.left,top:rect.top,width:360,height:routeMeasure().bar};}}),
    changed:value=>{routeDetached.value=value;},closed:()=>{routeClosed.value=true;routeListOpen.value=false;},
    moved:()=>syncRouteDocument(),report:message=>{pinError.value=message;}});
  return routeWindow.pin();
}
function openRoutes(){if(!routeWindow?.focus())routeClosed.value=false;}
function closeRoutes(){if(routeDetached.value)routeWindow.dismiss();else{routeClosed.value=true;routeListOpen.value=false;}}
function pinExplorer(){
  panelWindow??=createPanelWindow({element:()=>panel.value,changed:value=>{detached.value=value;emit('detached',value);},closed:()=>emit('update:open',false),report:message=>{pinError.value=message;}});
  return panelWindow.pin();
}
function closeExplorer(){if(detached.value)panelWindow.dismiss();else emit('update:open',false);}
watch(()=>props.allDisplays,(active,previous)=>{
  if(previous&&!active){
    // DOM・履歴を本体へ回収してから別窓を閉じ、通常画面では閉じた状態へ戻す。
    closeExplorer();closeRoutes();
  }
});
async function pinForAll(){
  // 非表示の矩形を測らない。元の窓サイズのまま開いてから、別窓の表示完了を待つ。
  // Explorerを切り離した後も、軌跡の位置はExplorerの右側に保つ。
  preparingAll.value=true;
  try{
    emit('update:open',true);await nextTick();
    if(!await pinExplorer())throw Error(pinError.value||'エクスプローラーをピン留めできませんでした。');
    routeClosed.value=false;await nextTick();
    if(!await pinRoutes())throw Error(pinError.value||'軌跡バーをピン留めできませんでした。');
  }finally{preparingAll.value=false;}
}
watch([()=>props.open,detached],async([open,away])=>{if(open&&!away){await nextTick();fadePanel(panel.value);}});
// 一覧は宇宙と同じ（props.tree）。フィルター（星空画面の左下）が ON なら、宇宙もこの一覧もバックアップ対象だけになる。
const tree = computed(() => props.tree);
// 前回の最新日時以降を更新順で表示する。更新なしなら前回の一覧を保持する。
const recentUpdates = shallowRef([]);
let latestRun = 0, latestController, latestDisposed = false, updates = createLatestUpdates(), switchingFilter = false, initialSent = false;
const latestScan = shallowRef(null);
const treeWarning = computed(() => scanWarning(props.scan, '一覧'));
const latestWarning = computed(() => scanWarning(latestScan.value, '最終更新'));
function acceptUpdates(files) {
  const baseline = updates.since === null, changed = updates.accept(files);
  if (!changed.length) return changed;
  recentUpdates.value = changed;
  if (props.filter && (!initialSent || !baseline)) {
    const initial = !initialSent; initialSent = true;
    emit('latest', { ...changed.at(-1), files: changed, initial });
  }
  return changed;
}
async function pollLatest() {
  if (latestDisposed || (panel.value?.ownerDocument||document).hidden || latestController) return;   // 裏に隠れている間と前回取得中は問い合わせない
  const run = ++latestRun, forFilter = props.filter, request = new AbortController();
  latestController = request;
  try {
    const params = { ...(forFilter ? { filter: 'backup' } : {}), ...(updates.since === null ? {} : { since: String(updates.since) }) };
    const response = await fetch('/api/latest?' + new URLSearchParams(params), { cache: 'no-store', signal: request.signal });
    if (!response.ok) return;
    const result = await response.json();
    if (!latestDisposed && run === latestRun && forFilter === props.filter) {
      latestScan.value = result.scan || result;
      const changed = acceptUpdates(result.files || []); switchingFilter = false;
      // 最新の一覧を取り込むことと、自動で移動することは独立させる。
      if (changed.length) emit('freshness', { files: changed });
    }
  } catch { /* 次の周期で再試行 */ }
  finally { if (latestController === request) latestController = null; }
}
const latestTimer = setInterval(pollLatest, 60_000);
function resetLatest() { latestRun++; latestController?.abort(); latestController = null; updates = createLatestUpdates(); latestScan.value = null; recentUpdates.value = []; switchingFilter = true; }
watch(() => props.filter, () => { resetLatest(); void pollLatest(); });
watch(tree, value => { if (!switchingFilter) acceptUpdates(latestFiles(value, updates.since)); }, { immediate: true });
const latestTime = value => new Date(value.mtime).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const expanded = ref(new Set()), cursor = ref(''), mode = ref('since'), since = ref(props.startedAt), preset = ref('start');
const aiResult=shallowRef(null),routeMode=ref('view');
// 検索方法の切替や失敗で、前回確定した別分類の経路を消さない。
const searchRoute=shallowRef([]),searchKind=ref(''),searchTitle=ref('');
const aiFiles=computed(()=>new Map((aiResult.value?.files||[]).map(file=>[file.path,file.reason])));
const aiRoute=computed(()=>aiResult.value?.route||[]);
const routeListOpen=ref(false),routeElement=ref(),viewRoute=ref([]);
const routeMotionState=shallowRef({height:0,visible:false,phase:'closed'});
let routeDocumentCleanup=()=>{},routeDisposed=false;
function routeMeasure(){
  const node=routeElement.value,view=node?.ownerDocument?.defaultView||window;
  const bar=Math.ceil(node?.querySelector?.('.route-controls')?.getBoundingClientRect?.().height||64)+2;
  const away=!!node&&node.ownerDocument!==document;
  const top=node?.getBoundingClientRect?.().top||0,available=Math.max(0,(view.innerHeight||768)-top-bar-(away?0:8));
  return{bar,target:away?300:Math.min(300,available),available};
}
const routeMotion=createRouteExpansion({measure:routeMeasure,
  schedule:(fn,delay)=>{const view=routeElement.value?.ownerDocument?.defaultView||window;return{view,id:view.setTimeout?view.setTimeout(fn,delay):setTimeout(fn,delay)};},
  cancel:timer=>{if(timer)try{timer.view.clearTimeout?timer.view.clearTimeout(timer.id):clearTimeout(timer.id);}catch{}},
  reserve:async height=>{const node=routeElement.value;if(routeDetached.value&&node?.ownerDocument!==document)return routeWindow.reserveRouteHeight(height);return{height:routeMeasure().bar+routeMeasure().available};},
  reduced:()=>!!(routeElement.value?.ownerDocument?.defaultView||window).matchMedia?.('(prefers-reduced-motion: reduce)').matches,
  changed:value=>{routeMotionState.value=value;},report:message=>{pinError.value=message;}});
function syncRouteDocument(){
  routeDocumentCleanup();if(routeDisposed)return;
  const view=routeElement.value?.ownerDocument?.defaultView||window,media=view.matchMedia?.('(prefers-reduced-motion: reduce)');
  const resize=()=>routeMotion.refresh(),motion=()=>void routeMotion.set(routeListOpen.value&&!routeClosed.value,{restart:true});
  view.addEventListener('resize',resize);media?.addEventListener?.('change',motion);
  routeDocumentCleanup=()=>{view.removeEventListener('resize',resize);media?.removeEventListener?.('change',motion);};
  void routeMotion.set(routeListOpen.value&&!routeClosed.value,{restart:true});
}
watch([routeListOpen,routeClosed],async()=>{await nextTick();if(!routeDisposed)void routeMotion.set(routeListOpen.value&&!routeClosed.value);});
onMounted(syncRouteDocument);

watch([routeClosed,routeDetached],async([closed,away])=>{if(!closed&&!away){await nextTick();fadePanel(routeElement.value);}});
const viewedFiles=computed(()=>props.viewHistory.filter(entry=>entry?.type==='file'&&typeof entry.path==='string'));
function syncViewRoute(){viewRoute.value=[...new Set(viewedFiles.value.map(entry=>entry.path))];}
watch(viewedFiles,entries=>{
  const paths=[...new Set(entries.map(entry=>entry.path))];
  // 一覧から再訪しても表示順を入れ替えず、前・次で同じ2件を往復するのを防ぐ。
  viewRoute.value=routeListOpen.value&&routeMode.value==='view'
    ? [...paths.filter(path=>!viewRoute.value.includes(path)),...viewRoute.value.filter(path=>paths.includes(path))] : paths;
},{immediate:true});
const routePaths=computed(()=>routeMode.value==='ai'?aiRoute.value:routeMode.value==='search'?searchRoute.value:viewRoute.value);
const routeLabel=computed(()=>routeMode.value==='ai'?'AiDiy検索軌跡':routeMode.value==='search'?'検索軌跡':'閲覧軌跡');
const routeRows=computed(()=>routeTreeRows(routeMode.value==='view'?viewTreeRecords(props.viewVoyages,viewRoute.value,props.viewHistory.filter(entry=>entry?.type==='dir').map(entry=>entry.path))
  :routeMode.value==='search'?searchRoute.value.map(path=>({from:null,to:'f:'+path}))
  :aiResult.value?.routeRecords||searchRouteRecords(aiRoute.value)));
function beginSearch(kind){routeMode.value=kind==='ai'?'ai':'search';}
function acceptSearch(paths,kind,title){searchRoute.value=[...new Set(paths)];searchKind.value=kind;searchTitle.value=title;}
const viewedAt=path=>{const at=viewedFiles.value.find(entry=>entry.path===path)?.at;return Number.isFinite(at)?new Date(at).toLocaleString('ja-JP',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'';};
function closeRouteList(event){if(!routeDetached.value&&!routeElement.value?.contains(event.target))routeListOpen.value=false;}
onMounted(()=>document.addEventListener('pointerdown',closeRouteList));
const hiddenAI=computed(()=>{
  const paths=new Set();
  function walk(node,prefix=''){if(!node)return;for(const [name] of node.f)paths.add(prefix+name);for(const dir of node.d)walk(dir,prefix+dir.n+'/');}
  walk(tree.value);return aiRoute.value.filter(path=>!paths.has(path)).length;
});
const routeSteps=computed(()=>routeNavigationSteps(routeRows.value));
const routeIndex=computed(()=>routeSteps.value.findIndex(row=>row.path===(cursor.value||props.selected||props.current)));
function chooseRoute(value){
  const opening=routeMode.value!==value||!routeListOpen.value;
  routeMode.value=value;routeListOpen.value=opening;
  if(value==='ai')mode.value='ai';else if(value==='view'&&opening)syncViewRoute();
}
function selectRoutePath(path){const match=routeMode.value==='search'&&searchKind.value==='grep'?grepResults.value.find(item=>item.path===path):null;if(match)selectMatch(match);else select({type:'file',path,source:routeMode.value});}
function selectRoutePoint(row){if(row.type==='dir')select({type:'dir',path:row.path});else selectRoutePath(row.path);}
function stepRoute(offset){const index=routeIndex.value<0?(offset>0?0:routeSteps.value.length-1):routeIndex.value+offset;const row=routeSteps.value[index];if(row)selectRoutePoint(row);}
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
const grepResults = shallowRef([]), resultQuery = ref(''), resultCase = ref(false);
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
  emit('select',{type:row.type,path:row.path,...(row.mtime != null ? {mtime:row.mtime} : {}),...(row.size != null ? {size:row.size} : {}),...(row.source ? {source:row.source} : {}),...(row.line ? {line:row.line,column:row.column,query:row.query,caseSensitive:row.caseSensitive,matchMtime:row.matchMtime,matchLength:row.matchLength} : {})});
}
function emitMarks() { emit('marks',{mode:mode.value,since:since.value,paths:mode.value==='ai'?[...aiFiles.value.keys()]:[...matches.value]}); }
function selectMatch(match) { select({type:'file',...match,source:'grep',query:resultQuery.value,caseSensitive:resultCase.value,matchMtime:match.mtime,matchLength:match.length}); }
function clearSearch() { cancelSinceExpansion();generation++; controller?.abort();matches.value=new Set();grepResults.value=[];resultQuery.value='';status.value='';searching.value=false;rootExpanded.value=true; }
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
  updateSinceRoute();expandSinceMatches();
}
function updateSinceRoute(){
  beginSearch('since');const paths=[];
  function walk(node,prefix=''){if(!node)return;for(const [name,,mtime] of node.f)if(since.value!=null&&mtime>=since.value)paths.push(prefix+name);for(const dir of node.d)walk(dir,prefix+dir.n+'/');}
  walk(tree.value);acceptSearch(paths,'since','起点検索');
}
function chooseDate(value) { since.value=value?new Date(value).getTime():null;preset.value='custom';updateSinceRoute();expandSinceMatches(); }
async function grep() {
  clearSearch();expanded.value=new Set();cursor.value='';save();scrollToTop();
  if(!query.value.trim())return;
  beginSearch('grep');
  const run=generation, text=query.value, sensitive=caseSensitive.value;controller=new AbortController();status.value='検索中…';searching.value=true;rootExpanded.value=false;
  try {
    const response=await fetch('/api/grep?'+new URLSearchParams({q:text,case:sensitive?'1':'0'}),{signal:controller.signal});
    if(!response.ok)throw Error(await response.text());const result=await response.json();
    if(run!==generation)return;
    matches.value=new Set(result.paths);
    acceptSearch(result.paths,'grep',text);
    grepResults.value=Array.isArray(result.matches)?result.matches:[];resultQuery.value=text;resultCase.value=sensitive;
    const next=new Set();
    for(const path of result.paths){const parts=path.split('/');for(let i=1;i<parts.length;i++)next.add(parts.slice(0,i).join('/'));}
    expanded.value=next;save();
    status.value=`${result.paths.length}ファイル一致（検索 ${result.checked}・対象外 ${result.skipped}）${result.truncated?' ※一部の結果':''}`;
    if (result.truncated) status.value += ` ${scanWarning(result, '検索')}`;
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
watch(()=>props.root,(value,previous)=>{
  if(previous !== undefined){clearSearch();resetLatest();initialSent=false;void pollLatest();}
  aiResult.value=null;searchRoute.value=[];searchKind.value='';searchTitle.value='';routeMode.value='view';
  routeListOpen.value=false;
},{immediate:true});
watch([routeMode,aiRoute,searchRoute],()=>emit('route',{mode:routeMode.value,paths:routeMode.value==='search'?searchRoute.value:aiRoute.value,records:routeMode.value==='ai'?aiResult.value?.routeRecords:undefined}),{immediate:true});
watch(()=>[props.selected,props.current,props.open],()=>{if(props.open&&!props.navigating)reveal();});
watch(()=>props.startedAt,()=>{mode.value='since';clearSearch();resetLatest();initialSent=false;since.value=props.startedAt;preset.value='start';void pollLatest();});
watch(()=>props.filter,clearSearch);
watch(mode,clearSearch);
watch([mode,since,matches,aiResult],emitMarks,{immediate:true});
onBeforeUnmount(()=>{routeDisposed=true;routeMotion.dispose();routeDocumentCleanup();routeWindow?.close();panelWindow?.close();cancelSinceExpansion();generation++;controller?.abort();clearInterval(latestTimer);latestDisposed=true;latestRun++;latestController?.abort();document.removeEventListener('pointerdown',closeRouteList);});
defineExpose({reveal,focusDetached:()=>panelWindow?.focus()||false,pinForAll});
</script>
<template>
  <div class="explorer-component" data-component="FileExplorer">
    <button v-if="!open||detached" class="explorer-toggle burger-button" aria-label="エクスプローラーを開く" title="エクスプローラー" :aria-expanded="false" @click="detached?panelWindow.focus():emit('update:open',true)"><span class="burger burger-h" aria-hidden="true"><i></i><i></i><i></i></span></button>
    <!-- 軌跡バーはエクスプローラーと同じ扱い。閉じている時は縦三本の正方形ボタン、開くと同じ場所から横に開き、先頭の縦三本で閉じる。 -->
    <button v-if="routeClosed||routeDetached" class="route-restore-toggle burger-button" :class="{'explorer-open':open&&!detached}" aria-label="軌跡バーを開く" title="軌跡バー" :aria-expanded="false" @click="openRoutes"><span class="burger burger-v" aria-hidden="true"><i></i><i></i><i></i></span></button>
    <div ref="routeElement" v-show="!routeClosed" class="explorer-routes" :class="{'explorer-collapsed':!open||(detached&&!preparingAll)}" role="group" aria-label="軌跡表示" @keydown.esc.stop.prevent="routeListOpen=false">
      <div class="route-controls"><button v-if="!allDisplays" class="burger-button route-burger" aria-label="軌跡バーを閉じる" title="軌跡バーを閉じる" @click="closeRoutes"><span class="burger burger-v" aria-hidden="true"><i></i><i></i><i></i></span></button><span class="route-drag-handle" aria-hidden="true"></span>
      <button v-for="[value,label] in [['view','閲覧軌跡'],['search','検索軌跡'],['ai','AiDiy検索軌跡']]" :key="value" class="route-choice" :aria-pressed="routeMode===value" :aria-expanded="routeMode===value&&routeListOpen" aria-controls="route-file-list" @click="chooseRoute(value)">{{ label }}</button>
      <button title="プロジェクトルートへ" @click="select({type:'dir',path:''})">ルート</button><button :aria-label="routeMode==='ai'?'前の関連ファイル':routeMode==='search'?'前の検索ファイル':'前の閲覧ファイル'" :disabled="!routeSteps.length||routeIndex===0" @click="stepRoute(-1)">&lt;</button><button :aria-label="routeMode==='ai'?'次の関連ファイル':routeMode==='search'?'次の検索ファイル':'次の閲覧ファイル'" :disabled="!routeSteps.length||routeIndex===routeSteps.length-1" @click="stepRoute(1)">&gt;</button>
      <button v-if="!allDisplays||!routeDetached" :aria-label="routeDetached?'軌跡バーを本体へ戻す':'軌跡バーをピン留め'" :title="routeDetached?'本体へ戻す':'小さな別ウィンドウで開く'" @click="routeDetached?routeWindow.restore():pinRoutes()">{{ routeDetached?'↙':'📌' }}</button>
      </div>
      <div class="route-reveal" :data-phase="routeMotionState.phase" :style="{height:routeMotionState.height+'px'}">
      <section v-if="routeListOpen" :inert="!routeMotionState.visible" :aria-hidden="!routeMotionState.visible" :style="{visibility:routeMotionState.visible?'visible':'hidden'}" id="route-file-list" class="route-file-list" :aria-label="routeLabel+'のファイル一覧'">
        <p v-if="routeMode==='ai'&&aiResult" class="ai-route-title" :title="aiResult.query">{{ aiResult.title || aiResult.query }}</p>
        <p v-if="routeMode==='search'&&searchTitle" :title="searchTitle">{{ searchTitle }}</p>
        <p class="route-list-heading"><span>{{ routeLabel }} · {{ routePaths.length }}件</span><button v-if="routeMode==='view'" type="button" class="route-list-clear" aria-label="閲覧軌跡をクリア" :disabled="!viewedFiles.length" @click="emit('clear-view-history')">クリア</button></p>
        <p v-if="routeRows.length" class="route-tree-origin">{{ routeMode==='search'?'検索結果（並列の候補）':'記録された出発点と分岐' }}</p>
        <ul v-if="routeRows.length" class="route-tree" :aria-label="routeLabel+'のツリー'"><li v-for="row in routeRows" :key="row.key" :data-route-point="row.point" :data-route-parent="row.parent" :data-route-depth="row.depth" :class="{'route-reference':row.reference}" :style="{'--route-depth':row.depth}"><button :data-route-path="row.path" :aria-current="row.path===selected?'true':undefined" :title="routeMode==='ai'?aiFiles.get(row.path):row.path" @click="selectRoutePoint(row)"><span>{{ row.path || '/' }}{{ row.origin?'（出発元）':row.type==='dir'?'（到着）':'' }}{{ row.reference?' ↩（参照）':'' }}</span><small v-if="routeMode==='ai'">{{ aiFiles.get(row.path) }}</small><small v-else-if="routeMode==='view'">{{ viewedAt(row.path) }}</small></button></li></ul>
        <p v-else>{{ routeMode==='ai'?'AiDiy検索の結果を選ぶと、ここに表示します。':routeMode==='search'?'検索軌跡はありません。検索結果があると、ここに表示します。':'ファイルを開くと、ここに表示します。' }}</p>
      </section>
      </div>
    </div>
    <aside ref="panel" v-show="open" class="explorer-panel" :class="{'ai-search-mode':mode==='ai'}" aria-label="ファイルエクスプローラー">
      <header><button v-if="!allDisplays" class="burger-button explorer-burger" aria-label="エクスプローラーを閉じる" title="エクスプローラーを閉じる" :aria-expanded="true" @click="closeExplorer"><span class="burger burger-h" aria-hidden="true"><i></i><i></i><i></i></span></button><span>エクスプローラー</span><button v-if="!allDisplays||!detached" :aria-label="detached?'本体へ戻す':'エクスプローラーをピン留め'" :title="detached?'本体へ戻す':'別ウィンドウで開く'" @click="detached?panelWindow.restore():pinExplorer()">{{ detached?'↙':'📌' }}</button><button v-show="mode!=='ai'" title="選択位置を表示" @click="cancelSinceExpansion();reveal()">◎</button><button v-show="mode!=='ai'" title="すべて閉じる" @click="cancelSinceExpansion();rootExpanded=true;expanded=new Set();save()">⊟</button></header>
      <p v-if="treeWarning" class="scan-warning" role="status">{{ treeWarning }}</p>
      <section class="explorer-search"><small>表示中: {{ current || tree?.n }}</small>
        <fieldset><legend class="sr-only">検索方法</legend><label><input v-model="mode" type="radio" value="since">起点検索</label><label><input v-model="mode" type="radio" value="grep">grep検索</label><label><input v-model="mode" type="radio" value="ai">AiDiy検索</label></fieldset>
        <div v-if="mode==='since'"><label>起点 <input type="datetime-local" step="1" :value="dateInput" @change="chooseDate($event.target.value)"></label><div class="since-presets"><button v-for="[value,label] in [['start','起動'],['ten','10分'],['hour','1時間'],['today','今日'],['clear','解除']]" :key="value" :aria-pressed="preset===value" @click="choose(value)">{{ label }}</button></div></div>
        <form v-else-if="mode==='grep'" @submit.prevent>
          <label class="grep-query">ファイル内容<input v-model="query" type="search" maxlength="256" placeholder="検索する文字列"></label>
          <label><input v-model="caseSensitive" type="checkbox">大文字・小文字を区別</label>
          <div><button type="button" @click="grep">検索</button><button type="button" @click="query='';clearSearch()">解除</button></div>
          <p role="status">{{ status }}</p>
          <ol v-if="grepResults.length" class="grep-results" aria-label="grep検索の一致箇所"><li v-for="(match,index) in grepResults" :key="`${match.path}:${match.line}:${match.column}:${index}`"><button type="button" :title="`${match.path}:${match.line}:${match.column}`" @click="selectMatch(match)"><span>{{ match.path }}:{{ match.line }}:{{ match.column }}</span><small>{{ match.snippet }}</small></button></li></ol>
        </form>
        <AISearchPanel :key="root" :root="root" v-show="mode==='ai'" @search="beginSearch('ai')" @result="acceptAI" />
        <div v-if="mode==='ai'&&aiResult" class="ai-route-results"><p v-if="hiddenAI">{{ hiddenAI }}件は現在の一覧にありません。フィルターをOFFにするか一覧を更新してください。</p><p :title="aiResult.query">{{ aiResult.title || aiResult.query }} · {{ aiRoute.length }}件</p><ol><li v-for="path in aiRoute" :key="path"><button :title="aiFiles.get(path)" @click="select({type:'file',path})">{{ path }}</button><small>{{ aiFiles.get(path) }}</small></li></ol></div>
      </section>
      <div class="explorer-root" :title="root">
        <button class="chevron" :aria-label="rootExpanded?'ルートフォルダを折りたたむ':'ルートフォルダを展開する'" :aria-expanded="rootExpanded" :disabled="searching" @click="cancelSinceExpansion();rootExpanded=!rootExpanded">{{ rootExpanded?'▾':'▸' }}</button>
        <button class="explorer-root-name" :disabled="searching" @click="select({type:'dir',path:''})"><FileTypeIcon :name="tree?.n" directory :open="rootExpanded" /><span class="file-name">{{ tree?.n }}</span></button>
      </div>
      <ul ref="treeElement" role="tree" tabindex="0" @keydown="key"><TransitionGroup name="explorer-branch" @before-leave="beforeTreeLeave" @after-leave="afterTreeLeave" @leave-cancelled="afterTreeLeave"><li v-for="row in rows" :key="row.path" role="treeitem" :aria-expanded="row.type==='dir'?row.open:undefined" :aria-selected="selected===row.path" :data-path="row.path" :data-entry-type="row.type" :title="mode==='ai'?aiFiles.get(row.path):undefined" :style="{'--depth':row.depth}" :class="{fresh:row.fresh,'plain-folder':row.type==='dir'&&mode!=='ai',selected:selected===row.path,cursor:cursor===row.path}" @click="select(row,true)">
        <button v-if="row.type==='dir'" class="chevron" :aria-label="row.open?'折りたたむ':'展開する'" @click.stop="toggle(row)">{{ row.open?'▾':'▸' }}</button><span v-else class="chevron"></span><FileTypeIcon :name="row.name" :directory="row.type==='dir'" :open="row.open" /><span class="file-name">{{ row.name }}</span><span class="file-meta">{{ row.type==='dir'?(row.fresh?`${mode==='ai'?'関連':'更新'} ${row.fresh}`:''):new Date(row.mtime).toLocaleTimeString('ja-JP',{hour:'2-digit',minute:'2-digit'}) }}</span><span v-if="row.fresh" class="file-mark">●</span>
      </li></TransitionGroup></ul>
      <!-- 最下部: 前回取得以降の更新。次の更新が来るまで維持する。 -->
      <footer class="explorer-footer">
        <p v-if="latestWarning" class="scan-warning" role="status">{{ latestWarning }}</p>
        <small v-if="recentUpdates.length">最終更新 · {{ recentUpdates.length }}件</small>
        <div v-if="recentUpdates.length" class="explorer-latest-list" aria-label="最終更新ファイル一覧">
          <button v-for="file in recentUpdates" :key="file.path" class="explorer-latest" :data-latest-path="file.path" :title="`${file.path} · ${new Date(file.mtime).toLocaleString('ja-JP')}`" @click="select({type:'file',path:file.path,mtime:file.mtime,source:'latest'})"><FileTypeIcon :name="file.name" /><span class="file-name">{{ file.name }}</span><span class="file-meta">{{ latestTime(file) }}</span></button>
        </div>
      </footer>

    </aside>
    <p v-if="pinError" class="app-error" role="alert">{{ pinError }}</p>
  </div>
</template>

<style scoped>
.scan-warning{margin:0;padding:6px 8px;color:#ffe28a;font-size:var(--file-font-size,10px);overflow-wrap:anywhere;flex-shrink:0}
.grep-results{list-style:none;margin:6px 0 0;padding:0;max-height:180px;overflow:auto}
.explorer-panel .grep-results li{display:block;height:auto;padding:0;margin:4px 0}
.grep-results button{display:block;width:100%;text-align:left;overflow-wrap:anywhere}
.grep-results small{display:block;white-space:pre-wrap;color:#bac7da;font-family:var(--mono);margin-top:3px}
</style>


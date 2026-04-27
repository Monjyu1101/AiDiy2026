'use strict';

/* -----------------------------------------------------------------------
   XユーチューブBGM — YouTube IFrame API を使った A/B 自動交互再生プレイヤー
   ・A または B どちらかが再生中
   ・10 分経過 OR 動画終了 → もう片方にランダム動画を読み込み開始
   ・読み込み完了（シーク完了）後にクロスフェード開始
   ・フェード中: 旧側を音量↓・新側を音量↑、同時に視覚的 opacity も連動
   ----------------------------------------------------------------------- */

const VIDEOS = [
  { name: 'J-POPピアノ1990',             id: 'Diz_VHiZLO4' },
  { name: 'アバター',                      id: 'n1g30VVQgS8' },
  { name: 'ジブリソロギター',              id: 'FUqb11I8Mc8' },
  { name: 'ディズニーギター',              id: '5fMzH603jzI' },
  { name: 'ビートルズギター',              id: 'S4aZWW_H2PQ' },
  { name: 'ビートルズピアノ',              id: 'OWdKwn6LMr8' },
  { name: 'モーニングヒーリング',           id: 'AJxMeTUWEq0' },
  { name: 'リチャードクレイダーマンピアノ名曲集', id: 'YUuWYaBIsSI' },
  { name: 'ルパンcafe',                    id: 'UwGtKExkgTs' },
  { name: '君の名は。サントラ',            id: 'twV43MJi_fg' },
];

const PLAY_DURATION_MS  = 10 * 60 * 1000;  // 10 分
const FADE_DURATION_MS  = 4000;             // 4 秒クロスフェード
const FADE_INTERVAL_MS  = 50;              // フェード更新間隔
const MAX_VOLUME        = 80;              // 最大音量

/* ---------- 状態管理 ---------- */
const st = {
  players:      { A: null, B: null },
  ready:        { A: false, B: false },
  seekDone:     { A: false, B: false },
  currentVideo: { A: null,  B: null  },
  activePlayer: 'A',
  isCrossfading: false,
  pendingFade:   false,    // 次プレイヤーの再生開始を待機中
  fadeToPlayer:  null,
  playTimerId:   null,
  progressTimerId: null,
  playStartTime: null,
};

const $ = id => document.getElementById(id);

function rand(n) { return Math.floor(Math.random() * n); }

function getRandomVideo(excludeId) {
  const pool = excludeId ? VIDEOS.filter(v => v.id !== excludeId) : VIDEOS;
  return (pool.length > 0 ? pool : VIDEOS)[rand((pool.length > 0 ? pool : VIDEOS).length)];
}

/* ---------- YouTube IFrame API コールバック ---------- */
window.onYouTubeIframeAPIReady = function () {
  ['A', 'B'].forEach(side => {
    st.players[side] = new YT.Player('player-' + side.toLowerCase(), {
      height: '100%',
      width:  '100%',
      videoId: '',
      playerVars: {
        autoplay: 0,
        controls: 1,
        rel:      0,
        modestbranding: 1,
        enablejsapi: 1,
        origin: window.location.origin,
      },
      events: {
        onReady:       () => onPlayerReady(side),
        onStateChange: e  => onStateChange(e, side),
        onError:       e  => onError(e, side),
      },
    });
  });
};

function onPlayerReady(side) {
  st.ready[side] = true;
  st.players[side].setVolume(side === 'A' ? MAX_VOLUME : 0);
  if (st.ready.A && st.ready.B) {
    startInitialPlayback();
  }
}

function startInitialPlayback() {
  const video = getRandomVideo(null);
  loadVideoOnPlayer('A', video);
  updateNowPlaying('A', video.name);
}

function loadVideoOnPlayer(side, video) {
  st.currentVideo[side] = video;
  st.seekDone[side]     = false;
  st.players[side].loadVideoById({ videoId: video.id, startSeconds: 0 });
}

/* ---------- 状態変化ハンドラ ---------- */
function onStateChange(event, side) {
  const PS = YT.PlayerState;

  if (event.data === PS.PLAYING) {
    if (!st.seekDone[side]) {
      // 初回 PLAYING → ランダム位置にシーク
      st.seekDone[side] = true;
      const dur = st.players[side].getDuration();
      if (dur > 120) {
        const pos = Math.floor(Math.random() * dur * 0.75);
        st.players[side].seekTo(pos, true);
      }
      // シーク後: フェード待ちなら実行、アクティブなら再生タイマー開始
      if (st.pendingFade && side === st.fadeToPlayer) {
        st.pendingFade = false;
        executeFade(st.activePlayer, st.fadeToPlayer);
      } else if (side === st.activePlayer && !st.isCrossfading) {
        startPlayTimer();
      }
    }
  }

  if (event.data === PS.ENDED) {
    if (side === st.activePlayer && !st.isCrossfading) {
      triggerCrossfade('動画終了');
    }
  }
}

/* ---------- クロスフェード起動 ---------- */
function triggerCrossfade(reason) {
  if (st.isCrossfading) return;
  st.isCrossfading = true;
  clearPlayTimer();
  updateStatusText('切り替え中... (' + (reason || '') + ')');

  const next      = st.activePlayer === 'A' ? 'B' : 'A';
  const prevId    = st.currentVideo[st.activePlayer]?.id;
  const video     = getRandomVideo(prevId);

  st.fadeToPlayer  = next;
  st.pendingFade   = true;
  st.players[next].setVolume(0);
  loadVideoOnPlayer(next, video);
  updatePlaylistMark(video.name, 'next');
}

/* ---------- フェード実行 ---------- */
function executeFade(from, to) {
  const fromP    = st.players[from];
  const toP      = st.players[to];
  const fromWrap = $('player-' + from.toLowerCase() + '-wrap');
  const toWrap   = $('player-' + to.toLowerCase() + '-wrap');
  const steps    = Math.ceil(FADE_DURATION_MS / FADE_INTERVAL_MS);
  let   step     = 0;

  const iv = setInterval(() => {
    step++;
    const t    = Math.min(step / steps, 1);
    const tInv = 1 - t;

    // 音量
    toP.setVolume(Math.round(MAX_VOLUME * t));
    fromP.setVolume(Math.round(MAX_VOLUME * tInv));

    // 視覚
    if (toWrap)   toWrap.style.opacity   = t;
    if (fromWrap) fromWrap.style.opacity = tInv;

    if (t >= 1) {
      clearInterval(iv);
      fromP.stopVideo();
      fromP.setVolume(0);
      if (fromWrap) { fromWrap.style.opacity = '1'; fromWrap.className = 'player-box inactive'; }
      if (toWrap)   { toWrap.style.opacity   = '1'; toWrap.className   = 'player-box active';   }

      st.activePlayer   = to;
      st.isCrossfading  = false;
      updateNowPlaying(to, st.currentVideo[to]?.name || '');
      startPlayTimer();
    }
  }, FADE_INTERVAL_MS);
}

/* ---------- 再生タイマー ---------- */
function startPlayTimer() {
  clearPlayTimer();
  st.playStartTime   = Date.now();
  st.playTimerId     = setTimeout(() => triggerCrossfade('10分経過'), PLAY_DURATION_MS);
  st.progressTimerId = setInterval(updateProgress, 1000);
  updateStatusText('再生中');
  updateProgress();
}

function clearPlayTimer() {
  if (st.playTimerId)     { clearTimeout(st.playTimerId);    st.playTimerId     = null; }
  if (st.progressTimerId) { clearInterval(st.progressTimerId); st.progressTimerId = null; }
}

function updateProgress() {
  if (!st.playStartTime) return;
  const elapsed = Date.now() - st.playStartTime;
  const pct  = Math.min(elapsed / PLAY_DURATION_MS * 100, 100);
  const bar  = $('play-progress');
  if (bar) bar.style.width = pct + '%';

  const es = Math.floor(elapsed / 1000);
  const rs = Math.max(0, Math.floor((PLAY_DURATION_MS - elapsed) / 1000));
  const fmt = s => Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
  const elEl = $('time-elapsed');
  const reEl = $('time-remaining');
  if (elEl) elEl.textContent = fmt(es);
  if (reEl) reEl.textContent = '残 ' + fmt(rs);
}

/* ---------- UI 更新 ---------- */
function updateNowPlaying(side, title) {
  const indEl   = $('player-indicator');
  const titleEl = $('current-title');
  if (indEl) {
    indEl.textContent = 'Player ' + side;
    indEl.className   = 'player-badge player-' + side.toLowerCase();
  }
  if (titleEl) titleEl.textContent = title;
  updatePlaylistMark(title, 'active');
}

function updateStatusText(text) {
  const el = $('status-text');
  if (el) el.textContent = text;
}

function updatePlaylistMark(name, cls) {
  document.querySelectorAll('#playlist-list li').forEach(li => {
    li.classList.remove('active', 'next');
    if (li.dataset.name === name) li.classList.add(cls);
  });
}

/* ---------- エラーハンドラ ---------- */
function onError(event, side) {
  console.warn('YouTube player error side=' + side + ' code=' + event.data);
  if (side === st.activePlayer && !st.isCrossfading) {
    setTimeout(() => triggerCrossfade('エラー'), 3000);
  } else if (st.pendingFade && side === st.fadeToPlayer) {
    // 次プレイヤーがエラー → 少し待ってリトライ
    st.pendingFade   = false;
    st.isCrossfading = false;
    setTimeout(() => triggerCrossfade('リトライ'), 3000);
  }
}

/* ---------- プレイリスト構築 ---------- */
function buildPlaylist() {
  const ul = $('playlist-list');
  if (!ul) return;
  VIDEOS.forEach((v, i) => {
    const li = document.createElement('li');
    li.dataset.name = v.name;
    li.innerHTML =
      '<span class="pl-num">' + (i + 1) + '</span>' +
      '<span class="pl-name">' + v.name + '</span>';
    ul.appendChild(li);
  });
}

/* ---------- YouTube API ロード ---------- */
function loadYouTubeAPI() {
  const tag = document.createElement('script');
  tag.src   = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(tag);
}

document.addEventListener('DOMContentLoaded', () => {
  buildPlaylist();
  loadYouTubeAPI();
});

// COPYRIGHT (C) 2014-2026 Mitsuo KONDOU and contributors.
// Licensed under "AiDiy 公開利用ライセンス v1.1". See LICENSE for full terms.
import { createApp } from 'vue';
import TaskTeamPanel from './タスクチームパネル.vue';
import { configureClient } from './api/client';
import '../style.css';
import '../共通表示/会話表示.css';
async function main() {
  const response = await fetch('/development/config');
  if (!response.ok) throw Error('起動設定を取得できません。');
  const config = await response.json();
  configureClient(config.kind, config.taskTeamBase);
  document.title = `AiDiy ${config.kind === 'task' ? 'Task' : 'Team'}`;
  createApp(TaskTeamPanel, { config }).mount('#app');
}
void main().catch(error => { document.getElementById('app').textContent = error.message; });

// fix_vue_rename.js - Apply variable renaming to 4 Vue files
const fs = require('fs');

function r(content, from, to) {
  return content.split(from).join(to);
}

// File 1: Avatar AIファイル.vue
{
  const path = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_avatar/src/components/AIファイル.vue';
  let c = fs.readFileSync(path, 'utf8');

  // A1: defineProps rename
  c = r(c, 'const props = defineProps<{', 'const プロパティ = defineProps<{');
  c = r(c, '  sessionId: string\n', '  セッションID: string\n');
  c = r(c, '  inputConnected: boolean\n', '  入力接続済み: boolean\n');

  // A2: defineEmits rename
  c = r(c, 'const emit = defineEmits<{', 'const 通知 = defineEmits<{');

  // A3: fileSocket let → ref
  c = r(c, 'let fileSocket: AIWebSocket | null = null', 'const 出力WebSocket = ref<AIWebSocket | null>(null)');

  // A4: fileSocket replacements (most specific first)
  c = r(c, 'fileSocket?.isConnected()', '出力WebSocket.value?.isConnected()');
  c = r(c, 'fileSocket?.send(', '出力WebSocket.value?.send(');
  c = r(c, 'fileSocket.onStateChange(', '出力WebSocket.value.onStateChange(');
  c = r(c, 'fileSocket.send(', '出力WebSocket.value.send(');
  c = r(c, 'fileSocket.on(', '出力WebSocket.value.on(');
  c = r(c, 'fileSocket.off(', '出力WebSocket.value.off(');
  c = r(c, 'fileSocket.disconnect()', '出力WebSocket.value.disconnect()');
  c = r(c, 'fileSocket.connect()', '出力WebSocket.value.connect()');
  c = r(c, 'fileSocket.isConnected()', '出力WebSocket.value.isConnected()');
  c = r(c, 'fileSocket = new AIWebSocket(', '出力WebSocket.value = new AIWebSocket(');
  c = r(c, 'fileSocket = null', '出力WebSocket.value = null');
  c = r(c, 'if (fileSocket)', 'if (出力WebSocket.value)');
  c = r(c, 'if (!fileSocket', 'if (!出力WebSocket.value');
  c = r(c, 'fileSocket &&', '出力WebSocket.value &&');
  c = r(c, '!fileSocket ||', '!出力WebSocket.value ||');

  // props replacements
  c = r(c, 'props.sessionId', 'プロパティ.セッションID');
  c = r(c, 'props.active', 'プロパティ.active');
  c = r(c, 'props.inputConnected', 'プロパティ.入力接続済み');

  // emit replacement
  c = r(c, 'emit(', '通知(');

  // Normalize to LF
  c = c.replace(/\r\n/g, '\n');
  fs.writeFileSync(path, c, { encoding: 'utf8' });
  console.log('File 1 (avatar AIファイル.vue) done');
}

// File 2: Web AIファイル.vue
{
  const path = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/AiDiy/compornents/AIファイル.vue';
  let c = fs.readFileSync(path, 'utf8');

  c = r(c, 'wsConnected?: boolean;', '入力接続済み?: boolean;');
  c = r(c, 'プロパティ.wsConnected', 'プロパティ.入力接続済み');

  c = c.replace(/\r\n/g, '\n');
  fs.writeFileSync(path, c, { encoding: 'utf8' });
  console.log('File 2 (web AIファイル.vue) done');
}

// File 3: Avatar AiDiy.vue - only change AIコアファイル component block
{
  const path = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_avatar/src/AiDiy.vue';
  let c = fs.readFileSync(path, 'utf8');

  // Normalize first
  c = c.replace(/\r\n/g, '\n');

  const old3 =
    '      <component\n' +
    '        :is="AIコアファイル"\n' +
    '        ref="ファイルRef"\n' +
    '        :session-id="表示セッションID"\n' +
    '        :active="パネル表示状態.file"\n' +
    '        :input-connected="表示入力接続済み"\n' +
    '        @send-input-payload="ウィンドウから入力ペイロード送信"\n' +
    '      />';
  const new3 =
    '      <component\n' +
    '        :is="AIコアファイル"\n' +
    '        ref="ファイルRef"\n' +
    '        :セッションID="表示セッションID"\n' +
    '        :active="パネル表示状態.file"\n' +
    '        :入力接続済み="表示入力接続済み"\n' +
    '        @send-input-payload="ウィンドウから入力ペイロード送信"\n' +
    '      />';

  if (c.includes(old3)) {
    c = c.replace(old3, new3);
    console.log('File 3 (avatar AiDiy.vue) block replaced');
  } else {
    console.log('File 3 (avatar AiDiy.vue) WARNING: block not found, trying to diagnose...');
    // Try to find AIコアファイル context
    const idx = c.indexOf('AIコアファイル');
    if (idx >= 0) {
      console.log('Found AIコアファイル at index', idx);
      console.log('Context:', JSON.stringify(c.substring(idx - 50, idx + 200)));
    }
  }

  fs.writeFileSync(path, c, { encoding: 'utf8' });
}

// File 4: Web AiDiy.vue - only change :ws-connected in AIコアファイル block
{
  const path = 'D:/OneDrive/_sandbox/AiDiy2026/frontend_web/src/components/AiDiy/AiDiy.vue';
  let c = fs.readFileSync(path, 'utf8');

  c = c.replace(/\r\n/g, '\n');

  const old4 =
    '        <AIコアファイル\n' +
    '          :セッションID="セッションID"\n' +
    '          :active="パネル表示中.file"\n' +
    '          :ws-connected="入力接続済み"\n' +
    '          :ws-client="入力ソケット ?? null"\n' +
    "          @close=\"パネル閉じる('file')\"\n" +
    '        />';
  const new4 =
    '        <AIコアファイル\n' +
    '          :セッションID="セッションID"\n' +
    '          :active="パネル表示中.file"\n' +
    '          :入力接続済み="入力接続済み"\n' +
    '          :ws-client="入力ソケット ?? null"\n' +
    "          @close=\"パネル閉じる('file')\"\n" +
    '        />';

  if (c.includes(old4)) {
    c = c.replace(old4, new4);
    console.log('File 4 (web AiDiy.vue) block replaced');
  } else {
    console.log('File 4 (web AiDiy.vue) WARNING: block not found, diagnosing...');
    const idx = c.indexOf('AIコアファイル');
    if (idx >= 0) {
      console.log('Found AIコアファイル at index', idx);
      console.log('Context:', JSON.stringify(c.substring(idx - 20, idx + 250)));
    }
  }

  fs.writeFileSync(path, c, { encoding: 'utf8' });
}

console.log('All done!');

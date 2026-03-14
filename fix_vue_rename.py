# -*- coding: utf-8 -*-

def process_file1():
    """Avatar AIファイル.vue - Apply all A1-A4 changes"""
    path = r'D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\components\AIファイル.vue'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # A1: defineProps rename
    content = content.replace('const props = defineProps<{', 'const プロパティ = defineProps<{')
    content = content.replace('  sessionId: string\n', '  セッションID: string\n')
    content = content.replace('  inputConnected: boolean\n', '  入力接続済み: boolean\n')

    # A2: defineEmits rename
    content = content.replace('const emit = defineEmits<{', 'const 通知 = defineEmits<{')

    # A3: fileSocket let → ref
    content = content.replace(
        'let fileSocket: AIWebSocket | null = null',
        'const 出力WebSocket = ref<AIWebSocket | null>(null)'
    )

    # A4: fileSocket usage replacements (most specific first)
    content = content.replace('fileSocket?.isConnected()', '出力WebSocket.value?.isConnected()')
    content = content.replace('fileSocket?.send(', '出力WebSocket.value?.send(')
    content = content.replace('fileSocket.onStateChange(', '出力WebSocket.value.onStateChange(')
    content = content.replace('fileSocket.send(', '出力WebSocket.value.send(')
    content = content.replace('fileSocket.on(', '出力WebSocket.value.on(')
    content = content.replace('fileSocket.off(', '出力WebSocket.value.off(')
    content = content.replace('fileSocket.disconnect()', '出力WebSocket.value.disconnect()')
    content = content.replace('fileSocket.connect()', '出力WebSocket.value.connect()')
    content = content.replace('fileSocket.isConnected()', '出力WebSocket.value.isConnected()')
    content = content.replace('fileSocket = new AIWebSocket(', '出力WebSocket.value = new AIWebSocket(')
    content = content.replace('fileSocket = null', '出力WebSocket.value = null')
    content = content.replace('if (fileSocket)', 'if (出力WebSocket.value)')
    content = content.replace('if (!fileSocket', 'if (!出力WebSocket.value')
    content = content.replace('fileSocket &&', '出力WebSocket.value &&')
    content = content.replace('!fileSocket ||', '!出力WebSocket.value ||')

    # props replacements
    content = content.replace('props.sessionId', 'プロパティ.セッションID')
    content = content.replace('props.active', 'プロパティ.active')
    content = content.replace('props.inputConnected', 'プロパティ.入力接続済み')

    # emit replacement
    content = content.replace('emit(', '通知(')

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("File 1 (avatar AIファイル.vue) done")


def process_file2():
    """Web AIファイル.vue - Rename wsConnected prop"""
    path = r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\AiDiy\compornents\AIファイル.vue'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # B1: rename prop in defineProps
    content = content.replace('wsConnected?: boolean;', '入力接続済み?: boolean;')

    # B2: replace usage
    content = content.replace('プロパティ.wsConnected', 'プロパティ.入力接続済み')

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("File 2 (web AIファイル.vue) done")


def process_file3():
    """Avatar AiDiy.vue - Change AIコアファイル component props only"""
    path = r'D:\OneDrive\_sandbox\AiDiy2026\frontend_avatar\src\AiDiy.vue'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_block = (
        '      <component\n'
        '        :is="AIコアファイル"\n'
        '        ref="ファイルRef"\n'
        '        :session-id="表示セッションID"\n'
        '        :active="パネル表示状態.file"\n'
        '        :input-connected="表示入力接続済み"\n'
        '        @send-input-payload="ウィンドウから入力ペイロード送信"\n'
        '      />'
    )
    new_block = (
        '      <component\n'
        '        :is="AIコアファイル"\n'
        '        ref="ファイルRef"\n'
        '        :セッションID="表示セッションID"\n'
        '        :active="パネル表示状態.file"\n'
        '        :入力接続済み="表示入力接続済み"\n'
        '        @send-input-payload="ウィンドウから入力ペイロード送信"\n'
        '      />'
    )

    if old_block in content:
        content = content.replace(old_block, new_block)
        print("File 3 (avatar AiDiy.vue) block replaced")
    else:
        print("File 3 (avatar AiDiy.vue) WARNING: block not found!")

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


def process_file4():
    """Web AiDiy.vue - Change AIコアファイル component :ws-connected only"""
    path = r'D:\OneDrive\_sandbox\AiDiy2026\frontend_web\src\components\AiDiy\AiDiy.vue'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_block = (
        '        <AIコアファイル\n'
        '          :セッションID="セッションID"\n'
        '          :active="パネル表示中.file"\n'
        '          :ws-connected="入力接続済み"\n'
        '          :ws-client="入力ソケット ?? null"\n'
        '          @close="パネル閉じる(\'file\')"\n'
        '        />'
    )
    new_block = (
        '        <AIコアファイル\n'
        '          :セッションID="セッションID"\n'
        '          :active="パネル表示中.file"\n'
        '          :入力接続済み="入力接続済み"\n'
        '          :ws-client="入力ソケット ?? null"\n'
        '          @close="パネル閉じる(\'file\')"\n'
        '        />'
    )

    if old_block in content:
        content = content.replace(old_block, new_block)
        print("File 4 (web AiDiy.vue) block replaced")
    else:
        print("File 4 (web AiDiy.vue) WARNING: block not found!")

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


process_file1()
process_file2()
process_file3()
process_file4()
print("All done!")

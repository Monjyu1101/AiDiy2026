import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const PORT_WEB = 8090
const PORT_CORE = 8091
const PORT_TASKTEAM = 8093
const PORT_TOOLS = 8095
const PORT_APPS = 8098

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: ['monaco-editor', 'mermaid'],
    exclude: ['three', '@pixiv/three-vrm', '@pixiv/three-vrm-animation'],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '127.0.0.1',
    port: PORT_WEB,
    proxy: {
      '/core': {
        target: `http://127.0.0.1:${PORT_CORE}`,
        changeOrigin: true,
        ws: true,  // WebSocketサポートを有効化
      },
      '/apps': {
        target: `http://127.0.0.1:${PORT_APPS}`,
        changeOrigin: true,
        ws: true,  // WebSocketサポートを有効化
      },
      '/mcp': {
        target: `http://127.0.0.1:${PORT_TOOLS}`,
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/mcp/, ''),
      },
      '/task': {
        target: `http://127.0.0.1:${PORT_TASKTEAM}`,
        changeOrigin: true,
      },
      '/team': {
        target: `http://127.0.0.1:${PORT_TASKTEAM}`,
        changeOrigin: true,
      }
    }
  }
})

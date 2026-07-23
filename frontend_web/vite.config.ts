import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: ['monaco-editor'],
    exclude: ['three', '@pixiv/three-vrm', '@pixiv/three-vrm-animation'],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 8090,
    proxy: {
      '/core': {
        target: 'http://127.0.0.1:8091',
        changeOrigin: true,
        ws: true,  // WebSocketサポートを有効化
      },
      '/apps': {
        target: 'http://127.0.0.1:9098',
        changeOrigin: true,
        ws: true,  // WebSocketサポートを有効化
      },
      '/mcp': {
        target: 'http://127.0.0.1:8095',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/mcp/, ''),
      },
      '/task': {
        target: 'http://127.0.0.1:8093',
        changeOrigin: true,
      },
      '/team': {
        target: 'http://127.0.0.1:8094',
        changeOrigin: true,
      }
    }
  }
})

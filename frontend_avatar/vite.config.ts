import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: [
      'monaco-editor',
      'three',
      '@pixiv/three-vrm',
      '@pixiv/three-vrm-animation',
    ],
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 8092,
    strictPort: true,
    proxy: {
      '/core': {
        target: 'http://127.0.0.1:8091',
        changeOrigin: true,
        ws: true,
      },
      '/apps': {
        target: 'http://127.0.0.1:9098',
        changeOrigin: true,
        ws: true,
      },
      '/task': {
        target: 'http://127.0.0.1:8093',
        changeOrigin: true,
      },
    },
  },
})

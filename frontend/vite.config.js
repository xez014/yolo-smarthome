import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 代理后端 API 请求（可选，开发时可直接跨域）
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/snapshots': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

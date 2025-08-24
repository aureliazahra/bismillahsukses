import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Jalankan FastAPI di http://127.0.0.1:8000
const BACKEND = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      // Proxy SEMUA endpoint backend
      '/api': {
        target: BACKEND,
        changeOrigin: true,
        secure: false,
      },
      // Proxy file statis dari FastAPI (mis. /static/target_faces/xxx.jpg)
      '/static': {
        target: BACKEND,
        changeOrigin: true,
        secure: false,
      },
      // Opsional: stream multipart (kalau ada SSE/WS tambahan, tambahkan di sini)
      '/realtime': {
        target: BACKEND,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  preview: {
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true, secure: false },
      '/static': { target: BACKEND, changeOrigin: true, secure: false },
      '/realtime': { target: BACKEND, changeOrigin: true, secure: false },
    },
  },
})

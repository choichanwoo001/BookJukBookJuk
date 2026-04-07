import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 백엔드(npm run api) 기본 포트. 8000은 Windows에서 예약·충돌(WinError 10013)이 잦음.
const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:8001',
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: apiProxy,
  },
  preview: {
    port: 3000,
    host: true,
    proxy: apiProxy,
  },
})

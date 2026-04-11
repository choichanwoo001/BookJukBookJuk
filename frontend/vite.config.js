import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
/** Vite 기본은 frontend/ — 루트 `.env` 한 곳에서 VITE_* 를 읽도록 함 */
const repoRoot = path.resolve(__dirname, '..')

// 백엔드(npm run api) 기본 포트. 8000은 Windows에서 예약·충돌(WinError 10013)이 잦음.
const apiProxy = {
  '/api': {
    target: 'http://127.0.0.1:8001',
    changeOrigin: true,
  },
}

export default defineConfig({
  envDir: repoRoot,
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

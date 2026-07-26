import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 백엔드 CORS가 5173으로 열려 있으므로 포트를 고정합니다.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
})

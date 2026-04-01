import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// REQ-006-01: 프론트엔드는 3000번 포트에서 독립 기동
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
  test: {
    // jsdom 환경에서 React 컴포넌트 테스트 실행
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})

import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// Encaminha as chamadas de /api para o FastAPI durante o desenvolvimento.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: env.API_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: (caminho) => caminho.replace(/^\/api/, ''),
        },
      },
    },
  }
})

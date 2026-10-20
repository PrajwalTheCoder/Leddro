import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const isProd = process.env.NODE_ENV === 'production' || process.env.GITHUB_ACTIONS === 'true';

// https://vite.dev/config/
export default defineConfig({
  base: process.env.BASE_URL || (isProd ? '/Leddro/' : '/'),
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})


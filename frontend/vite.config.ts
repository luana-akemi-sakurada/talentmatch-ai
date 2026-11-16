import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: { proxy: { '/api': process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000' } },
  preview: { proxy: { '/api': process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000' } },
  build: { rollupOptions: { output: { manualChunks: { charts: ['recharts'], react: ['react', 'react-dom', 'react-router-dom'] } } } },
})

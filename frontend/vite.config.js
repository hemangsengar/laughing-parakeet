import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/optimize': 'http://localhost:8000',
      '/progress': 'http://localhost:8000',
      '/download': 'http://localhost:8000',
      '/original': 'http://localhost:8000',
      '/job': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
})

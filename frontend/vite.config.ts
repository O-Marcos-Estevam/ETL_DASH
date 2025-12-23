import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: true,
    port: 4000,
    strictPort: true,
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:4001',
        changeOrigin: true
      },
      '/ws': {
        target: 'http://localhost:4001',
        ws: true,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})

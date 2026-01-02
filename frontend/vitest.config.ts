/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    // Ambiente de teste
    environment: 'jsdom',

    // Setup files
    setupFiles: ['./src/__tests__/setup.ts'],

    // Glob patterns para encontrar testes
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],

    // Excluir node_modules e arquivos de build
    exclude: ['node_modules', 'dist', 'web'],

    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/__tests__/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
    },

    // Globals (describe, it, expect sem import)
    globals: true,

    // CSS handling
    css: false,

    // Reporter
    reporters: ['verbose'],

    // Timeout
    testTimeout: 10000,
  },
})

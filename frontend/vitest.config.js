import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

// Merged config: upstream util tests (tests/**) + LCS component tests
// (src/**/__tests__). The vue() plugin is required for the LCS .vue specs;
// upstream's happy-dom env + setup file are kept so upstream tests stay green.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    root: __dirname,
    setupFiles: ['./tests/setup.js'],
    include: [
      'src/**/__tests__/**/*.{spec,test}.{js,ts}',
      'tests/**/*.test.js',
      'src/**/*.test.js',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      reportsDirectory: './coverage',
      include: [
        'src/components/lcs/**/*.{vue,ts,js}',
        'src/utils/fieldTransforms.js',
        'src/utils/scriptHelpers.js',
        'src/utils/expressions.js',
        'src/utils/renderFieldLayoutDialog.js',
      ],
    },
  },
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ArcoResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ArcoResolver()],
    }),
    Components({
      resolvers: [
        ArcoResolver({
          sideEffect: true
        })
      ]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  optimizeDeps: {
    include: ['monaco-editor']
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api/': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws/': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    },
    historyApiFallback: true
  }
})

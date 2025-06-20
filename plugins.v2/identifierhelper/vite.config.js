import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'identifier-helper',
      filename: 'remoteEntry.js',
      exposes: {
        './IdentifierHelper': './src/App.vue'
      },
      shared: {
        vue: {
          singleton: true
        },
        vuetify: {
          singleton: true
        }
      }
    })
  ],
  server: {
    port: 5174,
    host: '0.0.0.0',
    cors: true
  },
  build: {
    target: 'esnext',
    minify: false,
    cssCodeSplit: false,
    rollupOptions: {
      external: [],
      output: {
        format: 'esm'
      }
    }
  }
})
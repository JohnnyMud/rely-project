import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/patients': 'http://127.0.0.1:8000',
      '/calls': 'http://127.0.0.1:8000',
      '/websocket': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API requests to the backend server
      '/convert': 'http://backend:6201',
      '/progress': 'http://backend:6201',
      '/convert-word-to-markdown': 'http://backend:6201',
      '/convert-markdown-to-word': 'http://backend:6201',
    },
    host: '0.0.0.0', // Allow external access
  },
})

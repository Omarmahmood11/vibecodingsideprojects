import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API calls to the FastAPI backend during dev (no CORS needed).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/recommendations': 'http://localhost:8077',
      '/metadata': 'http://localhost:8077',
      '/health': 'http://localhost:8077',
    },
  },
})

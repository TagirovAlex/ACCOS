import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('node_modules/react-dom') || id.includes('node_modules/react/')) return 'vendor';
          if (id.includes('node_modules/@mui/') || id.includes('node_modules/@emotion/')) return 'mui';
          if (id.includes('node_modules/react-admin') || id.includes('ra-data-simple-rest') || id.includes('ra-language-russian')) return 'ra';
        },
      },
    },
  },
  base: "/admin/",
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
})

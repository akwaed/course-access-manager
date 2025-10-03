import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/tcecontacts/',
  server: {
    port: 3000,
    proxy: {
      '/tcecontacts/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/tcecontacts/, ''),
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: false,
  },
});

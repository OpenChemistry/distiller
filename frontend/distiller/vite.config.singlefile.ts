import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  server: {
    port: 3000,
  },
  build: {
    rollupOptions: {
      external: ['../../templates/index.html.handlebars?raw'],
    },
  },
});

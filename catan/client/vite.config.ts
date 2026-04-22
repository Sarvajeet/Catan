import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite config: dev server proxies socket.io and /api to the Flask backend.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/socket.io": {
        target: "http://localhost:5001",
        ws: true,
      },
      "/api": "http://localhost:5001",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});

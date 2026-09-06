import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Fully offline demo: no external URLs anywhere (no tile servers, fonts,
  // or CDN scripts). All map layers come from the local data bundle.
  server: { port: 5173 },
});

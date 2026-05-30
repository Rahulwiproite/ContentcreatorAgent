import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const BACKEND = process.env.VITE_DEV_BACKEND || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/agent": BACKEND,
      "/auth": BACKEND,
      "/social": BACKEND,
      "/analytics": BACKEND,
      "/trends": BACKEND,
      "/ideas": BACKEND,
      "/healthz": BACKEND,
    },
  },
});

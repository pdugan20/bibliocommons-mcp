/**
 * Workbench Vite config. Roots at `web/` so the dev server serves both
 * the workbench (`/workbench/`) and every bundle entry (`/<name>.html`).
 * The workbench's iframe loads the bundle entry directly from this
 * server, so saving any component HMR-reloads the iframe.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(here, "..");

export default defineConfig({
  root: webRoot,
  plugins: [react()],
  server: {
    port: 5174,
    open: "/workbench/",
  },
});

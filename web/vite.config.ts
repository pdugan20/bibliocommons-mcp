/**
 * Base Vite config. Used implicitly by `scripts/inline_bundles.mjs` when
 * it builds each `web/*.html` entry programmatically. The workbench has
 * its own config at `web/workbench/vite.config.ts` (lands in a later
 * commit).
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "dist",
  },
});

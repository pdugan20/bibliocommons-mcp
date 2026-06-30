// ESLint v9 flat config for the web/ workspace.
//
// Covers the four UI bundles + the workbench: React 19, strict TS,
// hooks rules. Output bundle JS (`dist/`) and the generated Python
// emitter target are excluded.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import prettier from "eslint-config-prettier";

export default [
  {
    ignores: ["dist/**", "node_modules/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      react: reactPlugin,
      "react-hooks": reactHooks,
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        matchMedia: "readonly",
        console: "readonly",
        HTMLIFrameElement: "readonly",
        MessageEvent: "readonly",
        Window: "readonly",
      },
    },
    settings: {
      react: { version: "19" },
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // The new JSX transform makes the in-scope React import
      // unnecessary; mute the legacy lint that still flags it.
      "react/react-in-jsx-scope": "off",
      // Tightening: tolerate unused args that are deliberately
      // underscored so `_ev` style is legal.
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
  // The bundle/cover scripts and Vite config run as Node ESM and
  // reference node globals (incl. the global fetch from Node 18+).
  {
    files: ["scripts/**/*.mjs", "**/vite.config.ts"],
    languageOptions: {
      globals: {
        process: "readonly",
        console: "readonly",
        fetch: "readonly",
      },
    },
  },
  prettier,
];

/**
 * Shared inline style for the outermost <div> of every bundle. Mirrors
 * clickwheel's pattern: hardcoded card chrome (cream-and-grey) rather
 * than chained host-CSS variables, because Claude Desktop's injected
 * `--color-border-*` values are barely-there alpha and we want the
 * visible card edge.
 *
 * Color and weight tokens live in `./palette.ts`.
 */
import type { CSSProperties } from "react";

import {
  CARD_BG_DARK,
  CARD_BG_LIGHT,
  CARD_BORDER_DARK,
  CARD_BORDER_LIGHT,
} from "./palette.js";

export const rootStyle: CSSProperties = {
  fontFamily:
    'var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
  fontSize: 13,
  lineHeight: 1.4,
  color: "var(--color-text-primary, light-dark(#1a1a1a, #f0f0f0))",
  background: `light-dark(${CARD_BG_LIGHT}, ${CARD_BG_DARK})`,
  // Asymmetric padding on purpose: the last row already carries ~10px of
  // its own bottom padding, so the card only needs a little more beneath it
  // (a symmetric 20px read as too much dead space). Horizontal padding is a
  // responsive var (lib/responsive) — tighter on a narrow iOS bubble.
  padding: "16px var(--bc-pad-x, 20px) 8px",
  borderRadius: 12,
  border: `1px solid light-dark(${CARD_BORDER_LIGHT}, ${CARD_BORDER_DARK})`,
  boxSizing: "border-box",
};

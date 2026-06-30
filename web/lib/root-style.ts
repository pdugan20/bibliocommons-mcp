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

// On iOS, Claude wraps the card iframe in its OWN rounded WKWebView
// container. If we also round + border the card, the two masks fight at the
// corners and ours get clipped square (and the border leaves a hairline gap
// against the host mask). So on iOS we go edge-to-edge — no radius, no border
// — and let the host's container be the only thing rounding the corners.
// (Same fix the rewind MCP server uses.) Everywhere else, keep our chrome.
function isIOS(): boolean {
  if (typeof navigator === "undefined") return false;
  const ua = navigator.userAgent;
  return (
    "standalone" in navigator ||
    /iPad|iPhone|iPod/.test(ua) ||
    (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)
  );
}

const ON_IOS = isIOS();

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
  borderRadius: ON_IOS ? 0 : 12,
  border: ON_IOS
    ? "none"
    : `1px solid light-dark(${CARD_BORDER_LIGHT}, ${CARD_BORDER_DARK})`,
  boxSizing: "border-box",
};

// Single-line status states (loading / error). The list rootStyle keeps a
// tight 8px bottom because the last row carries its own padding; a lone
// message has no row, so it needs symmetric breathing room top and bottom.
export const messageRootStyle: CSSProperties = {
  ...rootStyle,
  padding: "16px var(--bc-pad-x, 20px)",
};

/**
 * Color tokens for the bibliocommons-mcp UI bundles.
 *
 * We deliberately hard-code card chrome (`CARD_BG_*`, `CARD_BORDER_*`)
 * rather than chain through host-injected CSS variables. Claude
 * Desktop's `--color-border-*` values are barely-there alpha values
 * that collapse against the host's background; the cream-and-grey
 * card edge is what we want.
 */

export const CARD_BG_LIGHT = "#fcfcfa";
export const CARD_BG_DARK = "#272726";
export const CARD_BORDER_LIGHT = "#d9d9d9";
export const CARD_BORDER_DARK = "#383836";

/** BiblioCommons brand-adjacent accent. Used for status pills and
 * "ready for pickup" indicators. */
export const ACCENT = "#0f6dbf";

/** Status colors for hold + loan states. Darkened from the tailwind-600
 * tier to the 700 tier so 11px white pill text clears WCAG AA (4.5:1) on
 * both card backgrounds — the 600 greens/ambers were ~3.2–3.3:1. */
export const STATUS_READY = "#15803d"; // green — pick it up (white text ≈ 4.9:1)
export const STATUS_QUEUED = "#0f6dbf"; // blue — in queue (white text ≈ 4.6:1)
export const STATUS_DUE_SOON = "#b45309"; // amber — due in <3 days (white text ≈ 4.7:1)
export const STATUS_OVERDUE = "#b91c1c"; // red — past due (white text ≈ 5.9:1)

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

/** Status colors for hold + loan states. */
export const STATUS_READY = "#16a34a"; // green — pick it up
export const STATUS_QUEUED = "#0f6dbf"; // blue — in queue
export const STATUS_DUE_SOON = "#d97706"; // amber — due in <3 days
export const STATUS_OVERDUE = "#dc2626"; // red — past due

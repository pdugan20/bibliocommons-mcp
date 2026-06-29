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

/** Single blue accent for every active status pill — ready, queued, in
 * transit, due, overdue. The reds/greens/ambers were intentionally dropped:
 * the pill text carries the state, so the palette stays calm and mostly
 * monochrome. White pill text on this blue is ≈ 4.6:1 (WCAG AA). */
export const STATUS_ACTIVE = "#0f6dbf";

/** Neutral slate for spent/inactive states (expired, cancelled), paired
 * with the dim + strikethrough treatment. */
export const STATUS_SPENT = "#6b7280";

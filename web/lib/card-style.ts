/**
 * Shared inline styles for the card family (search / holds / loans). The
 * three cards previously each carried their own copy of these; the only
 * intentional per-card difference is the title line-clamp, which is now
 * an explicit `titleStyle(lines)` argument rather than silent drift.
 */
import type { CSSProperties } from "react";

export const rowStyle: CSSProperties = {
  display: "flex",
  // Center the meta block against the cover so short cards (a single
  // ready hold) don't leave the cover hanging in dead space.
  alignItems: "center",
  gap: 12,
  paddingTop: 10,
  paddingBottom: 10,
};

export const firstRowStyle: CSSProperties = {
  ...rowStyle,
  paddingTop: 2,
};

/** iOS-style inset row separator: a hairline that starts at the text's
 * left edge (past the cover + gap) rather than spanning the full width.
 * Rendered as its own element between rows, not as a row border. */
export const rowDividerStyle: CSSProperties = {
  height: 1,
  background: "light-dark(#ececec, #2e2e2e)",
  marginLeft: "calc(var(--bc-cover-w, 64px) + 12px)",
};

export const metaStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  minWidth: 0, // lets long titles wrap/clamp inside the flex row
  flex: 1,
};

export const lineStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.75,
  margin: 0,
  overflowWrap: "anywhere", // defensive: no overflow on a long unbroken token
};

export const pillRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  flexWrap: "wrap",
  marginTop: 3,
  // Pull the row left by the chip's own horizontal padding so the chip's
  // *text* optically aligns with the title above and the meta line below,
  // instead of being indented by the chip's left padding.
  marginLeft: -8,
};

// --- Chip family. Status and format now share one quiet, tonal shape so
// the status reads as part of the same system as the Book/CD badge rather
// than a loud solid pill. Variants differ only in tint.
const chipBase: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: 19,
  padding: "0 8px",
  borderRadius: 5,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.2,
  whiteSpace: "nowrap",
};

/** Active status (ready / queued / in transit / due / overdue) — tonal blue. */
export const statusChipStyle: CSSProperties = {
  ...chipBase,
  background: "light-dark(rgba(15,109,191,0.12), rgba(77,159,232,0.22))",
  color: "light-dark(#0b5da6, #9ccbf0)",
};

/** Spent status (expired / cancelled) — tonal neutral, paired with dim. */
export const spentChipStyle: CSSProperties = {
  ...chipBase,
  background: "light-dark(rgba(0,0,0,0.06), rgba(255,255,255,0.10))",
  color: "light-dark(#6b7280, #a3a3a3)",
};

/** Format badge (eBook / CD / Book / …) — quiet neutral chip. */
export const badgeStyle: CSSProperties = {
  ...chipBase,
  background: "light-dark(rgba(0,0,0,0.06), rgba(255,255,255,0.10))",
  color: "light-dark(#3a3a3a, #cfcfcf)",
};

export function titleStyle(lines: number): CSSProperties {
  return {
    fontSize: 14,
    fontWeight: 600,
    margin: 0,
    display: "-webkit-box",
    WebkitBoxOrient: "vertical" as CSSProperties["WebkitBoxOrient"],
    WebkitLineClamp: lines,
    overflow: "hidden",
  };
}

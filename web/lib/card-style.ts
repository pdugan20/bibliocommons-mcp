/**
 * Shared inline styles for the card family (search / holds / loans). The
 * three cards previously each carried their own copy of these; the only
 * intentional per-card difference is the title line-clamp, which is now
 * an explicit `titleStyle(lines)` argument rather than silent drift.
 */
import type { CSSProperties } from "react";

/** Section heading ("Holds (3)", "Page 1 of 3 · 67 results"). Sits a clear
 * step above the 14px item titles so a screenshot reads top-down. */
export const headingStyle: CSSProperties = {
  margin: 0,
  fontSize: 16,
  fontWeight: 700,
  letterSpacing: -0.1,
};

export const rowStyle: CSSProperties = {
  display: "flex",
  // Center the meta block against the 88px cover so short cards (a single
  // ready hold) don't leave the cover hanging in dead space.
  alignItems: "center",
  gap: 12,
  paddingTop: 10,
  paddingBottom: 10,
  borderTop: "1px solid light-dark(#ececec, #2e2e2e)",
};

export const firstRowStyle: CSSProperties = {
  ...rowStyle,
  borderTop: "none",
  paddingTop: 4,
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
  gap: 8,
  flexWrap: "wrap",
  marginTop: 2,
};

/** Stadium status pill (Ready / queue / due-state). Saturated solid fills
 * are reserved for these — the format badge is a quiet neutral chip. */
export const pillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: 18,
  padding: "0 8px",
  borderRadius: 9,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.2,
  textTransform: "uppercase",
  whiteSpace: "nowrap", // long "due in N days" labels shouldn't wrap/clip
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

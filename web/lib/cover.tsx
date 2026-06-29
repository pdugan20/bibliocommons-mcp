/**
 * Shared cover thumbnail for every card. One place for cover sizing, the
 * fallback treatment, lazy/eager loading, and image decoding.
 *
 * - The box matches the media's real aspect ratio — portrait for books,
 *   square for discs (CD/vinyl) — and `objectFit: cover` fills it, so
 *   nothing letterboxes (grey bars) or crops the wrong way.
 * - We pull the `large` jacket (a full-quality JPG) rather than the
 *   `small`/`medium` 256-colour GIFs: the box renders ~64-88px CSS, i.e.
 *   ~128-176px on a 2x display, so the small thumbnail looked soft.
 * - `eager` (first ~3 rows) loads above-the-fold covers immediately and
 *   hints high priority; the long tail stays lazy.
 * - A hairline border defines the cover edge against the card; when there's
 *   no jacket we draw an intentional book glyph, not a bare grey box.
 * - Width is the responsive `--bc-cover-w` (see lib/responsive); height is
 *   the same for a square cover, or `--bc-cover-h` for a portrait one.
 */
import type { CSSProperties } from "react";

import { isSquareFormat } from "./format.js";
import type { Jacket } from "./jacket.js";

export const COVER_WIDTH = 64;
export const COVER_HEIGHT = 88;
const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";

const baseWrapStyle: CSSProperties = {
  position: "relative",
  flexShrink: 0,
  width: "var(--bc-cover-w, 64px)",
  background: COVER_FALLBACK_BG,
  borderRadius: 4,
  border: "1px solid light-dark(rgba(0,0,0,0.14), rgba(255,255,255,0.14))",
  boxSizing: "border-box",
  overflow: "hidden",
};

const imgStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
  display: "block",
};

const placeholderStyle: CSSProperties = {
  position: "absolute",
  inset: 0,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "light-dark(#b6b2ac, #6b6b6b)",
};

function PlaceholderGlyph() {
  // Lucide "book" — a quiet thematic stand-in for "no cover available".
  return (
    <div style={placeholderStyle} aria-hidden="true">
      <svg
        width="26"
        height="26"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
      </svg>
    </div>
  );
}

export function CoverImage({
  jacket,
  format,
  eager,
}: {
  jacket?: Jacket | null;
  /** Format facet code (BK, MUSIC_CD, …) — decides square vs portrait. */
  format?: string | null;
  /** True for the first few above-the-fold rows. */
  eager?: boolean;
}) {
  // Prefer a library upload, then the high-res JPG, falling back to the
  // smaller GIFs so a partial jacket still renders something.
  const src =
    jacket?.local_url ??
    jacket?.large ??
    jacket?.medium ??
    jacket?.small ??
    null;
  const square = isSquareFormat(format);
  const wrapStyle: CSSProperties = {
    ...baseWrapStyle,
    height: square ? "var(--bc-cover-w, 64px)" : "var(--bc-cover-h, 88px)",
  };
  return (
    <div style={wrapStyle}>
      {src ? (
        <img
          src={src}
          // Decorative: the adjacent <h3> already names the item, so an
          // alt of "Cover of …" would just double-announce — and an empty
          // alt avoids a broken-image label if the host CSP drops the URL.
          alt=""
          style={imgStyle}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          fetchPriority={eager ? "high" : "low"}
        />
      ) : (
        <PlaceholderGlyph />
      )}
    </div>
  );
}

/**
 * Shared cover thumbnail for every card. One place for cover sizing, the
 * fallback treatment, lazy/eager loading, and image decoding — the three
 * cards previously each carried a byte-identical copy of this.
 *
 * - `objectFit: contain` so square CD/DVD/vinyl art letterboxes on the
 *   neutral matte instead of being cropped by the portrait 64x88 box.
 * - `eager` (first ~3 rows) loads above-the-fold covers immediately and
 *   hints high priority; the long tail stays lazy.
 * - When there's no jacket URL we draw an intentional book glyph rather
 *   than a bare grey rectangle that reads as "broken/loading".
 * - Size is driven by `--bc-cover-w/h` (see lib/responsive) so the cover
 *   shrinks on a narrow iOS bubble; `accent` draws a status ring (a
 *   pickup-ready hold reads green, an overdue loan reads red).
 */
import type { CSSProperties } from "react";

import type { Jacket } from "./jacket.js";

export const COVER_WIDTH = 64;
export const COVER_HEIGHT = 88; // ~book aspect; square media letterboxes via objectFit:contain
const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";

const wrapStyle: CSSProperties = {
  position: "relative",
  flexShrink: 0,
  width: "var(--bc-cover-w, 64px)",
  height: "var(--bc-cover-h, 88px)",
  background: COVER_FALLBACK_BG,
  borderRadius: 4,
  overflow: "hidden",
};

const imgStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "contain",
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
  eager,
  accent,
}: {
  jacket?: Jacket | null;
  /** True for the first few above-the-fold rows. */
  eager?: boolean;
  /** Status ring color (e.g. green for ready-for-pickup, red for overdue). */
  accent?: string;
}) {
  const src = jacket?.local_url ?? jacket?.small ?? jacket?.medium ?? null;
  const style = accent
    ? { ...wrapStyle, outline: `2px solid ${accent}`, outlineOffset: 1 }
    : wrapStyle;
  return (
    <div style={style}>
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

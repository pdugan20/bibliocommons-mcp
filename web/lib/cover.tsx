/**
 * Shared cover thumbnail for every card. One place for cover sizing, the
 * fallback treatment, lazy/eager loading, and image decoding.
 *
 * - Fixed width, **natural height**: every cover is the same width and the
 *   height follows the art's real aspect ratio (a square CD stays square, a
 *   portrait book stays portrait, a tall DVD stays tall) — so nothing is
 *   letterboxed or cropped. Matches the BiblioCommons catalog layout.
 * - We pull the `large` jacket (a full-quality JPG) rather than the
 *   `small`/`medium` 256-colour GIFs: the box renders ~64px CSS wide, i.e.
 *   ~128px on a 2x display, so the small thumbnail looked soft.
 * - `eager` (first ~3 rows) loads above-the-fold covers immediately and
 *   hints high priority; the long tail stays lazy.
 * - A faint hairline border defines the edge; with no jacket we draw a
 *   book glyph in a portrait-shaped box.
 * - Width is the responsive `--bc-cover-w` (see lib/responsive).
 */
import { useState, type CSSProperties } from "react";

import { isDiscFormat } from "./format.js";
import type { Jacket } from "./jacket.js";

export const COVER_WIDTH = 64;
const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";

const wrapStyle: CSSProperties = {
  flexShrink: 0,
  width: "var(--bc-cover-w, 64px)",
  borderRadius: 4,
  border: "1px solid light-dark(rgba(0,0,0,0.08), rgba(255,255,255,0.10))",
  boxSizing: "border-box",
  overflow: "hidden",
  background: COVER_FALLBACK_BG,
};

// No jacket: give the box a book-shaped footprint to hold the glyph.
const placeholderWrapStyle: CSSProperties = {
  ...wrapStyle,
  position: "relative",
  aspectRatio: "2 / 3",
};

const imgStyle: CSSProperties = {
  width: "100%",
  height: "auto",
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

function PlaceholderGlyph({ disc }: { disc?: boolean }) {
  // Lucide "disc" for CDs, "book" otherwise — a quiet thematic stand-in
  // for "no cover available" that matches the item's medium.
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
        {disc ? (
          <>
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="2.2" />
          </>
        ) : (
          <>
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </>
        )}
      </svg>
    </div>
  );
}

export function CoverImage({
  jacket,
  eager,
  format,
}: {
  jacket?: Jacket | null;
  /** True for the first few above-the-fold rows. */
  eager?: boolean;
  /** Format facet — picks the placeholder's aspect (square for discs). */
  format?: string | null;
}) {
  // A 404 or CSP-blocked cover loads to zero intrinsic size, which would
  // collapse the box to a hairline; onError swaps in the placeholder.
  const [failed, setFailed] = useState(false);

  // Prefer a library upload, then the high-res JPG, falling back to the
  // smaller GIFs so a partial jacket still renders something.
  const src = failed
    ? null
    : (jacket?.local_url ??
      jacket?.large ??
      jacket?.medium ??
      jacket?.small ??
      null);

  if (!src) {
    // Match the missing cover's footprint + glyph to its format so it
    // doesn't tower over (or shrink beside) the real covers around it.
    const disc = isDiscFormat(format);
    const aspectRatio = disc ? "1 / 1" : "2 / 3";
    return (
      <div style={{ ...placeholderWrapStyle, aspectRatio }}>
        <PlaceholderGlyph disc={disc} />
      </div>
    );
  }

  return (
    <div style={wrapStyle}>
      <img
        src={src}
        // Decorative: the adjacent <h3> already names the item, so an alt
        // of "Cover of …" would just double-announce — and an empty alt
        // avoids a broken-image label if the host CSP drops the URL.
        alt=""
        style={imgStyle}
        loading={eager ? "eager" : "lazy"}
        decoding="async"
        fetchPriority={eager ? "high" : "low"}
        onError={() => setFailed(true)}
      />
    </div>
  );
}

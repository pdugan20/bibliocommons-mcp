/**
 * Format-facet helpers shared by all three cards. The gateway returns
 * codes like `BK` / `EBOOK` / `MUSIC_CD`; we surface a friendly label and
 * decide which formats are square (disc media) vs portrait (book-shaped)
 * so covers can be sized to their real aspect ratio.
 */
export const FORMAT_LABELS: Record<string, string> = {
  BK: "Book",
  EBOOK: "eBook",
  EAUDIOBOOK: "Audiobook",
  AUDIOBOOK_CD: "Audiobook (CD)",
  MUSIC_CD: "CD",
  DVD: "DVD",
  BLU_RAY: "Blu-ray",
  LARGEPRINT: "Large print",
  LP: "Large print",
  MN: "Score",
  MAGAZINE: "Magazine",
  VINYL: "Vinyl",
  STREAMING_VIDEO: "Streaming",
};

export function formatLabel(format?: string | null): string | null {
  if (!format) return null;
  return FORMAT_LABELS[format] ?? format;
}

// Canonical order for the format filter pills, so they read the same across
// cards regardless of the (variable, sort-dependent) order items arrive in.
// Uses the FORMAT_LABELS declaration order; unknown codes sort last.
const FORMAT_ORDER = Object.keys(FORMAT_LABELS);

/** Sort comparator for format codes into their canonical pill order. */
export function compareFormats(a: string, b: string): number {
  const ia = FORMAT_ORDER.indexOf(a);
  const ib = FORMAT_ORDER.indexOf(b);
  return (
    (ia === -1 ? FORMAT_ORDER.length : ia) -
      (ib === -1 ? FORMAT_ORDER.length : ib) || a.localeCompare(b)
  );
}

/** Disc media (square cover art): music + audiobook CDs. Their covers are
 * square, so a multi-line title overshoots the short cover and unbalances
 * the row — callers clamp these titles harder on a narrow viewport. */
export function isDiscFormat(format?: string | null): boolean {
  return format === "MUSIC_CD" || format === "AUDIOBOOK_CD";
}

/** Longer label for the in-row line (vs the short filter-chip label): a
 * plain physical book reads "Physical Book", everything else as usual. */
export function formatLabelLong(format?: string | null): string | null {
  if (format === "BK") return "Physical Book";
  return formatLabel(format);
}

/** Strip a trailing authority qualifier from a creator name —
 * "Mudhoney (Musical group)" -> "Mudhoney" — keeping personal names
 * ("Cross, Charles R.") untouched. */
export function cleanCreator(name?: string | null): string | null {
  if (!name) return null;
  return name.replace(/\s*\([^)]*\)\s*$/, "").trim() || name;
}

// A trailing, redundant format tag we already show on the format line.
const FORMAT_SUFFIX_RE =
  /\s*\((?:CD|DVD|LP|VINYL|BLU-?RAY|AUDIOBOOK|E-?BOOK|E-?AUDIOBOOK)\)\s*$/i;

/** Tidy a catalog title for display: drop a redundant trailing format tag
 * ("Pearl Jam (CD)" -> "Pearl Jam") and title-case an ALL-CAPS multi-word
 * title (a cataloging artifact: "RIOT ACT" -> "Riot Act"). Mixed-case titles
 * and short all-caps tokens (AC/DC, U2) are left untouched. */
export function cleanTitle(title?: string | null): string | null {
  if (!title) return null;
  let t = title.replace(FORMAT_SUFFIX_RE, "").trim();
  if (t.includes(" ") && /[A-Za-z]/.test(t) && t === t.toUpperCase()) {
    t = t
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
  }
  return t || title;
}

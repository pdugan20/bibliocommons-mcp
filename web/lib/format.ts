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

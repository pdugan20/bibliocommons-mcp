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

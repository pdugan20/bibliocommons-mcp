/**
 * One row in a search results list. Cover + title/subtitle + authors
 * + format badge + year. No status pill (catalog data is stateless).
 *
 * Data shape mirrors `bibliocommons_mcp.models.BibSummary`.
 */
import type { CSSProperties } from "react";

import { ACCENT } from "../lib/palette.js";
import type { Jacket } from "./HoldCard.js";

export type BibSummary = {
  bib_id: string;
  title?: string | null;
  subtitle?: string | null;
  authors?: string[] | null;
  format?: string | null;
  year?: string | null;
  call_number?: string | null;
  jacket?: Jacket | null;
};

const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";
const COVER_WIDTH = 64;
const COVER_HEIGHT = 88;

const rowStyle: CSSProperties = {
  display: "flex",
  gap: 12,
  paddingTop: 10,
  paddingBottom: 10,
  borderTop: "1px solid light-dark(#ececec, #2e2e2e)",
};

const firstRowStyle: CSSProperties = {
  ...rowStyle,
  borderTop: "none",
  paddingTop: 4,
};

const coverWrapStyle: CSSProperties = {
  flexShrink: 0,
  width: COVER_WIDTH,
  height: COVER_HEIGHT,
  background: COVER_FALLBACK_BG,
  borderRadius: 4,
  overflow: "hidden",
};

const coverImgStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
  display: "block",
};

const metaStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  minWidth: 0,
  flex: 1,
};

const titleStyle: CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  margin: 0,
  display: "-webkit-box",
  WebkitBoxOrient: "vertical" as CSSProperties["WebkitBoxOrient"],
  WebkitLineClamp: 2,
  overflow: "hidden",
};

const subtitleStyle: CSSProperties = {
  fontSize: 12,
  fontStyle: "italic",
  opacity: 0.7,
  margin: 0,
  display: "-webkit-box",
  WebkitBoxOrient: "vertical" as CSSProperties["WebkitBoxOrient"],
  WebkitLineClamp: 1,
  overflow: "hidden",
};

const lineStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.75,
  margin: 0,
};

const badgeRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  marginTop: 2,
};

const badgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: 18,
  padding: "0 8px",
  borderRadius: 4,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.3,
  background: ACCENT,
  color: "white",
};

// Friendly labels for the format facet codes the gateway returns.
const FORMAT_LABELS: Record<string, string> = {
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
  STREAMING_VIDEO: "Streaming",
};

function formatLabel(format?: string | null): string | null {
  if (!format) return null;
  return FORMAT_LABELS[format] ?? format;
}

function CoverImage({ bib }: { bib: BibSummary }) {
  const src =
    bib.jacket?.local_url ?? bib.jacket?.small ?? bib.jacket?.medium ?? null;
  if (!src) return <div style={coverWrapStyle} aria-hidden="true" />;
  return (
    <div style={coverWrapStyle}>
      <img
        src={src}
        alt={bib.title ? `Cover of ${bib.title}` : ""}
        style={coverImgStyle}
        loading="lazy"
      />
    </div>
  );
}

export function BibCard({
  bib,
  isFirst,
}: {
  bib: BibSummary;
  isFirst?: boolean;
}) {
  const format = formatLabel(bib.format);
  const author = (bib.authors ?? [])[0];

  return (
    <div style={isFirst ? firstRowStyle : rowStyle}>
      <CoverImage bib={bib} />
      <div style={metaStyle}>
        <h3 style={titleStyle}>{bib.title ?? "(untitled)"}</h3>
        {bib.subtitle && <p style={subtitleStyle}>{bib.subtitle}</p>}
        {author && <p style={lineStyle}>by {author}</p>}
        <div style={badgeRowStyle}>
          {format && <span style={badgeStyle}>{format}</span>}
          {bib.year && <span style={lineStyle}>{bib.year}</span>}
          {bib.call_number && <span style={lineStyle}>{bib.call_number}</span>}
        </div>
      </div>
    </div>
  );
}

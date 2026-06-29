/**
 * One row in a search results list. Cover + title/subtitle + authors
 * + format badge + year. No status pill (catalog data is stateless).
 *
 * Data shape mirrors `bibliocommons_mcp.models.BibSummary`.
 */
import type { CSSProperties } from "react";

import {
  firstRowStyle,
  lineStyle,
  metaStyle,
  pillRowStyle,
  rowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import type { Jacket } from "../lib/jacket.js";

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

const BIB_TITLE_STYLE = titleStyle(2);

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

// Quiet neutral chip: format is secondary metadata, so it shouldn't out-
// shout the title. Saturated solid fills are reserved for status pills.
const badgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: 18,
  padding: "0 8px",
  borderRadius: 4,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.2,
  whiteSpace: "nowrap",
  background: "light-dark(rgba(0,0,0,0.06), rgba(255,255,255,0.10))",
  color: "light-dark(#3a3a3a, #cfcfcf)",
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

export function BibCard({ bib, index }: { bib: BibSummary; index: number }) {
  const format = formatLabel(bib.format);
  const author = (bib.authors ?? [])[0];

  return (
    <div style={index === 0 ? firstRowStyle : rowStyle}>
      <CoverImage jacket={bib.jacket} eager={index < 3} />
      <div style={metaStyle}>
        <h3 style={BIB_TITLE_STYLE}>{bib.title ?? "(untitled)"}</h3>
        {bib.subtitle && <p style={subtitleStyle}>{bib.subtitle}</p>}
        {author && <p style={lineStyle}>by {author}</p>}
        <div style={pillRowStyle}>
          {format && <span style={badgeStyle}>{format}</span>}
          {bib.year && <span style={lineStyle}>{bib.year}</span>}
          {bib.call_number && <span style={lineStyle}>{bib.call_number}</span>}
        </div>
      </div>
    </div>
  );
}

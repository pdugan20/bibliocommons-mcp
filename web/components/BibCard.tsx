/**
 * One row in a search results list. Cover + title/subtitle + authors
 * + format badge + year. No status chip (catalog data is stateless).
 *
 * Data shape mirrors `bibliocommons_mcp.models.BibSummary`.
 */
import type { CSSProperties } from "react";

import {
  badgeStyle,
  firstRowStyle,
  lineStyle,
  metaStyle,
  pillRowStyle,
  rowDividerStyle,
  rowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatLabel } from "../lib/format.js";
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

export type SearchResult = {
  page?: number | null;
  pages?: number | null;
  total?: number | null;
  library?: string | null;
  results: BibSummary[];
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

export function BibCard({ bib, index }: { bib: BibSummary; index: number }) {
  const format = formatLabel(bib.format);
  const author = (bib.authors ?? [])[0];

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={index === 0 ? firstRowStyle : rowStyle}>
        <CoverImage jacket={bib.jacket} format={bib.format} eager={index < 3} />
        <div style={metaStyle}>
          <h3 style={BIB_TITLE_STYLE}>{bib.title ?? "(untitled)"}</h3>
          {bib.subtitle && <p style={subtitleStyle}>{bib.subtitle}</p>}
          {author && <p style={lineStyle}>by {author}</p>}
          <div style={pillRowStyle}>
            {format && <span style={badgeStyle}>{format}</span>}
            {bib.year && <span style={lineStyle}>{bib.year}</span>}
            {bib.call_number && (
              <span style={lineStyle}>{bib.call_number}</span>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

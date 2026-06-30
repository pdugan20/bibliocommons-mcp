/**
 * One row in a search results list. Cover + title/subtitle + author +
 * format · year. No status chip (catalog data is stateless).
 *
 * Data shape mirrors `bibliocommons_mcp.models.BibSummary`.
 */
import {
  firstRowStyle,
  lineStyle,
  metaStyle,
  rowDividerStyle,
  rowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { cleanCreator, formatLabelLong } from "../lib/format.js";
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
  more_url?: string | null;
  results: BibSummary[];
};

const BIB_TITLE_STYLE = titleStyle(2);

export function BibCard({ bib, index }: { bib: BibSummary; index: number }) {
  const author = (bib.authors ?? [])[0];
  const formatYear = [formatLabelLong(bib.format), bib.year]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={index === 0 ? firstRowStyle : rowStyle}>
        <CoverImage jacket={bib.jacket} eager={index < 3} />
        <div style={metaStyle}>
          <h3 style={BIB_TITLE_STYLE}>{bib.title ?? "(untitled)"}</h3>
          {author && <p style={lineStyle}>{cleanCreator(author)}</p>}
          {formatYear && <p style={lineStyle}>{formatYear}</p>}
        </div>
      </div>
    </>
  );
}

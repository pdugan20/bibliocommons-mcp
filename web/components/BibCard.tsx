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
  availability_status?: string | null;
  available_copies?: number | null;
  held_copies?: number | null;
  total_copies?: number | null;
};

/** "Available" / "All copies in use", with a holds tally when copies are
 * held. Plain text (no red/green) — the status is the signal, not colour. */
function availabilityText(b: BibSummary): string | null {
  const avail = b.available_copies ?? null;
  const status = b.availability_status ?? null;
  if (avail == null && status == null) return null;
  const base = (avail != null ? avail > 0 : status === "AVAILABLE")
    ? "Available"
    : "All copies in use";
  const held = b.held_copies ?? 0;
  const total = b.total_copies ?? null;
  if (held > 0 && total) {
    const h = `${held} hold${held === 1 ? "" : "s"}`;
    const c = `${total} cop${total === 1 ? "y" : "ies"}`;
    return `${base} · ${h} on ${c}`;
  }
  return base;
}

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
  const availability = availabilityText(bib);

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={index === 0 ? firstRowStyle : rowStyle}>
        <CoverImage jacket={bib.jacket} eager={index < 3} format={bib.format} />
        <div style={metaStyle}>
          <h3 style={BIB_TITLE_STYLE}>{bib.title ?? "(untitled)"}</h3>
          {author && <p style={lineStyle}>{cleanCreator(author)}</p>}
          {formatYear && <p style={lineStyle}>{formatYear}</p>}
          {availability && <p style={lineStyle}>{availability}</p>}
        </div>
      </div>
    </>
  );
}

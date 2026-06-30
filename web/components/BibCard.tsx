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
import { cleanCreator, cleanTitle, formatLabelLong } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";
import { RecordLink } from "../lib/open-link.js";

import type { CSSProperties } from "react";

const COVER_LINK_STYLE: CSSProperties = { display: "block", flexShrink: 0 };

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
  url?: string | null;
};

/** A one-word availability label folded onto the format line. Plain text
 * (no red/green) — the status word is the signal, not colour. The wait-time
 * detail (holds on copies) lives in the dedicated `availability` tool. */
function availabilityLabel(b: BibSummary): string | null {
  const status = b.availability_status ?? null;
  const avail = b.available_copies ?? null;
  if (status === "ON_ORDER") return "On order";
  if (avail != null && avail > 0) return "Available";
  if (status === "AVAILABLE") return "Available";
  if (avail === 0 || status === "UNAVAILABLE") return "All copies in use";
  return null;
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
  // Fold the subtitle into the title ("Kurt Cobain: Forever in Bloom"). Many
  // bibs carry the distinguishing part in the subtitle (a cluster of books
  // titled just "Kurt Cobain"), so combining keeps the bold line unique per
  // result; the 2-line clamp bounds the length.
  const fullTitle =
    [cleanTitle(bib.title), cleanTitle(bib.subtitle)]
      .filter(Boolean)
      .join(": ") || "(untitled)";
  // Format · year · availability on one line so the row stays compact next
  // to a short square CD cover.
  const formatLine = [
    formatLabelLong(bib.format),
    bib.year,
    availabilityLabel(bib),
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={index === 0 ? firstRowStyle : rowStyle}>
        <RecordLink url={bib.url} style={COVER_LINK_STYLE}>
          <CoverImage
            jacket={bib.jacket}
            eager={index < 3}
            format={bib.format}
          />
        </RecordLink>
        <div style={metaStyle}>
          <h3 style={BIB_TITLE_STYLE}>
            <RecordLink url={bib.url}>{fullTitle}</RecordLink>
          </h3>
          {author && <p style={lineStyle}>{cleanCreator(author)}</p>}
          {formatLine && <p style={lineStyle}>{formatLine}</p>}
        </div>
      </div>
    </>
  );
}

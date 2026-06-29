/**
 * The presentational view for each bundle — header + filter + card list +
 * footer — built on CardFrame. Imported by both the real bundle entries
 * (holds/loans/search.tsx, which wrap these in the MCP Apps handshake) and
 * the dev workbench, so what ships and what we design against are the same.
 */
import { BibCard, type SearchResult } from "../components/BibCard.js";
import { HoldCard, type HoldList } from "../components/HoldCard.js";
import { LoanCard, type LoanList } from "../components/LoanCard.js";
import { CardFrame } from "./card-frame.js";

function searchTitle(p: SearchResult): string {
  if (p.total == null) return "Search results";
  if (p.total === 0) return "No results";
  return `${p.total} result${p.total === 1 ? "" : "s"}`;
}

function searchFooterNote(p: SearchResult): string | undefined {
  return p.pages && p.pages > 1
    ? `Page ${p.page ?? 1} of ${p.pages}`
    : undefined;
}

export function HoldsView({ payload }: { payload: HoldList }) {
  return (
    <CardFrame
      library={payload.library}
      title="Your holds"
      items={payload.holds}
      emptyText="No active holds."
      renderItem={(h, i) => <HoldCard key={h.hold_id} hold={h} index={i} />}
      moreUrl={payload.more_url}
      moreLabel="Manage holds"
    />
  );
}

export function LoansView({ payload }: { payload: LoanList }) {
  return (
    <CardFrame
      library={payload.library}
      title="Your checkouts"
      items={payload.loans}
      emptyText="Nothing currently checked out."
      renderItem={(l, i) => <LoanCard key={l.checkout_id} loan={l} index={i} />}
      moreUrl={payload.more_url}
      moreLabel="Manage checkouts"
    />
  );
}

export function SearchView({ payload }: { payload: SearchResult }) {
  return (
    <CardFrame
      library={payload.library}
      title={searchTitle(payload)}
      items={payload.results}
      emptyText="No matches."
      renderItem={(b, i) => <BibCard key={b.bib_id} bib={b} index={i} />}
      footerNote={searchFooterNote(payload)}
      moreUrl={payload.more_url}
      moreLabel="See all results"
    />
  );
}

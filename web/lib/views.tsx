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

// Inline search shows a curated top slice and links out for the rest,
// rather than dumping a full 25-row page into the conversation.
const SEARCH_CARD_LIMIT = 10;

function searchTitle(p: SearchResult): string {
  return p.total === 0 ? "No results" : "Search results";
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
  const total = payload.total ?? payload.results.length;
  const shown = payload.results.slice(0, SEARCH_CARD_LIMIT);
  // Only link out when there's genuinely more than we're showing.
  const hasMore = total > shown.length;
  return (
    <CardFrame
      library={payload.library}
      title={searchTitle(payload)}
      items={shown}
      emptyText="No matches."
      renderItem={(b, i) => <BibCard key={b.bib_id} bib={b} index={i} />}
      moreUrl={hasMore ? payload.more_url : undefined}
      moreLabel={hasMore ? `See all ${total} results` : undefined}
    />
  );
}

/**
 * Dev-only app shells — the heading + card-list markup each bundle entry
 * (holds/loans/search.tsx) wraps its cards in, minus the MCP Apps host
 * plumbing. Shared by the gallery and the scenarios storyboard so they
 * render exactly what ships without re-mounting the real entries (which
 * auto-call createRoot on import).
 */
import { BibCard } from "../components/BibCard.js";
import { HoldCard } from "../components/HoldCard.js";
import { LoanCard } from "../components/LoanCard.js";
import { headingStyle } from "../lib/card-style.js";
import { rootStyle } from "../lib/root-style.js";
import type { HoldList } from "../holds.fixtures.js";
import type { LoanList } from "../loans.fixtures.js";
import type { SearchResult } from "../search.fixtures.js";

const emptyTextStyle = { marginTop: 8, marginBottom: 0, opacity: 0.7 };

export function HoldsShell({ payload }: { payload: HoldList }) {
  if (payload.count === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={headingStyle}>Holds</h2>
        <p style={emptyTextStyle}>No active holds.</p>
      </div>
    );
  }
  return (
    <div style={rootStyle}>
      <h2 style={headingStyle}>Holds ({payload.count})</h2>
      <div style={{ marginTop: 8 }}>
        {payload.holds.map((hold, i) => (
          <HoldCard key={hold.hold_id} hold={hold} index={i} />
        ))}
      </div>
    </div>
  );
}

export function LoansShell({ payload }: { payload: LoanList }) {
  if (payload.count === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={headingStyle}>Checkouts</h2>
        <p style={emptyTextStyle}>Nothing currently checked out.</p>
      </div>
    );
  }
  return (
    <div style={rootStyle}>
      <h2 style={headingStyle}>Checkouts ({payload.count})</h2>
      <div style={{ marginTop: 8 }}>
        {payload.loans.map((loan, i) => (
          <LoanCard key={loan.checkout_id} loan={loan} index={i} />
        ))}
      </div>
    </div>
  );
}

function paginationSummary(payload: SearchResult): string {
  const { total, page, pages } = payload;
  if (total == null) return "Results";
  if (total === 0) return "No results";
  if (pages && pages > 1)
    return `Page ${page ?? 1} of ${pages} · ${total} results`;
  return `${total} result${total === 1 ? "" : "s"}`;
}

export function SearchShell({ payload }: { payload: SearchResult }) {
  if (payload.results.length === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={headingStyle}>Search</h2>
        <p style={emptyTextStyle}>No matches.</p>
      </div>
    );
  }
  return (
    <div style={rootStyle}>
      <h2 style={headingStyle}>{paginationSummary(payload)}</h2>
      <div style={{ marginTop: 8 }}>
        {payload.results.map((bib, i) => (
          <BibCard key={bib.bib_id} bib={bib} index={i} />
        ))}
      </div>
    </div>
  );
}

/**
 * Entry for the search-results bundle. Receives `SearchResult` as
 * structuredContent and renders one `BibCard` per hit, plus a
 * pagination indicator above the list.
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { BibCard, type BibSummary } from "./components/BibCard.js";
import { rootStyle } from "./lib/root-style.js";

type SearchResult = {
  page?: number | null;
  pages?: number | null;
  total?: number | null;
  results: BibSummary[];
};

function paginationSummary(payload: SearchResult): string {
  const total = payload.total;
  const page = payload.page;
  const pages = payload.pages;
  if (total == null) return "Results";
  if (total === 0) return "No results";
  if (pages && pages > 1) {
    return `Page ${page ?? 1} of ${pages} · ${total} results`;
  }
  return `${total} result${total === 1 ? "" : "s"}`;
}

function SearchApp() {
  const [payload, setPayload] = useState<SearchResult | null>(null);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "bibliocommons-mcp-search", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (created) => {
      created.ontoolresult = (result) => {
        const sc = result?.structuredContent as SearchResult | undefined;
        if (sc && Array.isArray(sc.results)) setPayload(sc);
      };
    },
  });

  // See holds.tsx — pass initial host context so theme applies on mount.
  useHostStyles(app, app?.getHostContext());

  if (error) {
    return <div style={rootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={rootStyle}>Waiting for search results…</div>;
  }

  if (payload.results.length === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Search</h2>
        <p style={{ marginTop: 8, marginBottom: 0, opacity: 0.7 }}>
          No matches.
        </p>
      </div>
    );
  }

  return (
    <div style={rootStyle}>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
        {paginationSummary(payload)}
      </h2>
      <div style={{ marginTop: 8 }}>
        {payload.results.map((bib, i) => (
          <BibCard key={bib.bib_id} bib={bib} isFirst={i === 0} />
        ))}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <SearchApp />
  </StrictMode>,
);

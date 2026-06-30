/**
 * Entry for the search-results bundle. Receives `SearchResult` as
 * structuredContent and hands it to SearchView (header + filter + cards).
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { type SearchResult } from "./components/BibCard.js";
import { useLinkOpener } from "./lib/open-link.js";
import { ResponsiveStyles } from "./lib/responsive.js";
import { rootStyle } from "./lib/root-style.js";
import { SearchView } from "./lib/views.js";

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
  useLinkOpener(app);

  if (error) {
    return <div style={rootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={rootStyle}>Waiting for search results…</div>;
  }

  return <SearchView payload={payload} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <SearchApp />
  </StrictMode>,
);

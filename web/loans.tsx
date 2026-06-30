/**
 * Entry for the loans bundle. Receives `LoanList` as structuredContent
 * and hands it to LoansView (header + filter + cards).
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { type LoanList } from "./components/LoanCard.js";
import { useLinkOpener } from "./lib/open-link.js";
import { ResponsiveStyles } from "./lib/responsive.js";
import { messageRootStyle } from "./lib/root-style.js";
import { LoansView } from "./lib/views.js";

function LoansApp() {
  const [payload, setPayload] = useState<LoanList | null>(null);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "bibliocommons-mcp-loans", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (created) => {
      created.ontoolresult = (result) => {
        const sc = result?.structuredContent as LoanList | undefined;
        if (sc && Array.isArray(sc.loans)) setPayload(sc);
      };
    },
  });

  // See holds.tsx — pass initial host context so theme applies on mount.
  useHostStyles(app, app?.getHostContext());
  useLinkOpener(app);

  if (error) {
    return <div style={messageRootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={messageRootStyle}>Waiting for loans…</div>;
  }

  return <LoansView payload={payload} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <LoansApp />
  </StrictMode>,
);

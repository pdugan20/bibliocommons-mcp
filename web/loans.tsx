/**
 * Entry for the loans bundle. Receives `LoanList` as structuredContent
 * and renders one `LoanCard` per checkout.
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { LoanCard, type Loan } from "./components/LoanCard.js";
import { headingStyle } from "./lib/card-style.js";
import { ResponsiveStyles } from "./lib/responsive.js";
import { rootStyle } from "./lib/root-style.js";

type LoanList = {
  count: number;
  loans: Loan[];
};

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

  if (error) {
    return <div style={rootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={rootStyle}>Waiting for loans…</div>;
  }

  if (payload.count === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={headingStyle}>Checkouts</h2>
        <p style={{ marginTop: 8, marginBottom: 0, opacity: 0.7 }}>
          Nothing currently checked out.
        </p>
      </div>
    );
  }

  return (
    <div style={rootStyle}>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
        Checkouts ({payload.count})
      </h2>
      <div style={{ marginTop: 8 }}>
        {payload.loans.map((loan, i) => (
          <LoanCard key={loan.checkout_id} loan={loan} index={i} />
        ))}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <LoansApp />
  </StrictMode>,
);

/**
 * Entry for the holds bundle. Receives `HoldList` as the tool result's
 * structuredContent and renders one `HoldCard` per hold.
 *
 * Wired the same way clickwheel wires its entries: `useApp({ onAppCreated })`
 * to register `ontoolresult` synchronously before `app.connect()` resolves
 * (otherwise the SDK can drop the very first tool-result notification).
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { HoldCard, type Hold } from "./components/HoldCard.js";
import { headingStyle } from "./lib/card-style.js";
import { rootStyle } from "./lib/root-style.js";

type HoldList = {
  count: number;
  holds: Hold[];
};

function HoldsApp() {
  const [payload, setPayload] = useState<HoldList | null>(null);

  const { app, isConnected, error } = useApp({
    appInfo: { name: "bibliocommons-mcp-holds", version: "0.1.0" },
    capabilities: {},
    onAppCreated: (created) => {
      created.ontoolresult = (result) => {
        const sc = result?.structuredContent as HoldList | undefined;
        if (sc && Array.isArray(sc.holds)) setPayload(sc);
      };
    },
  });

  // Pass the initial host context so the host's theme + style vars apply on
  // mount, not just on later host-context-changed notifications. Without the
  // second arg, light-dark() follows the iframe's OS preference instead of
  // the user's Claude appearance (per ext-apps useHostStyles docs).
  useHostStyles(app, app?.getHostContext());

  if (error) {
    return <div style={rootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={rootStyle}>Waiting for holds…</div>;
  }

  if (payload.count === 0) {
    return (
      <div style={rootStyle}>
        <h2 style={headingStyle}>Holds</h2>
        <p style={{ marginTop: 8, marginBottom: 0, opacity: 0.7 }}>
          No active holds.
        </p>
      </div>
    );
  }

  return (
    <div style={rootStyle}>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
        Holds ({payload.count})
      </h2>
      <div style={{ marginTop: 8 }}>
        {payload.holds.map((hold, i) => (
          <HoldCard key={hold.hold_id} hold={hold} index={i} />
        ))}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HoldsApp />
  </StrictMode>,
);

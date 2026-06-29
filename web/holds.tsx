/**
 * Entry for the holds bundle. Receives `HoldList` as the tool result's
 * structuredContent and hands it to HoldsView (header + filter + cards).
 *
 * Wired the same way clickwheel wires its entries: `useApp({ onAppCreated })`
 * to register `ontoolresult` synchronously before `app.connect()` resolves
 * (otherwise the SDK can drop the very first tool-result notification).
 */
import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

import { type HoldList } from "./components/HoldCard.js";
import { ResponsiveStyles } from "./lib/responsive.js";
import { rootStyle } from "./lib/root-style.js";
import { HoldsView } from "./lib/views.js";

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
  // mount, not just on later host-context-changed notifications.
  useHostStyles(app, app?.getHostContext());

  if (error) {
    return <div style={rootStyle}>Error: {error.message}</div>;
  }
  if (!isConnected) return null;
  if (payload === null) {
    return <div style={rootStyle}>Waiting for holds…</div>;
  }

  return <HoldsView payload={payload} />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <HoldsApp />
  </StrictMode>,
);

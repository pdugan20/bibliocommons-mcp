/**
 * Placeholder bundle. Exists so the build chain has one entry to
 * compile — confirms inline_bundles.mjs works end-to-end before the
 * real cards land. Will be deleted in the HoldCard commit.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { rootStyle } from "./lib/root-style.js";

function Placeholder() {
  return (
    <div style={rootStyle}>
      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
        bibliocommons-mcp UI bundle
      </h2>
      <p style={{ marginTop: 8, marginBottom: 0, opacity: 0.7 }}>
        Build chain confirmed working. Real card components ship in the next
        commit.
      </p>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Placeholder />
  </StrictMode>,
);

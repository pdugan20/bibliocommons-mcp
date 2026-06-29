/**
 * Dev-only "product scenarios" storyboard — NOT a shipped bundle.
 *
 * The three flows the cards are designed for, each framed as a Claude
 * conversation (the user's question → the assistant's card response), so
 * the end-to-end product experience can be reviewed/screenshotted in one
 * place. Uses the real card components + the representative "typical"
 * fixture for each flow.
 *
 * Serve via:  cd web && npx vite --port 5176
 * Then open:  http://localhost:5176/workbench/scenarios.html  (?theme=dark)
 */
import {
  StrictMode,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createRoot } from "react-dom/client";

import {
  DEFAULT_HEADER_VARIANT,
  HEADER_VARIANTS,
  HEADER_VARIANT_NOTES,
  HeaderVariantContext,
  type HeaderVariant,
} from "../lib/card-header.js";
import { ResponsiveStyles } from "../lib/responsive.js";
import { fixtures as holdsFixtures } from "../holds.fixtures.js";
import { fixtures as loansFixtures } from "../loans.fixtures.js";
import { fixtures as searchFixtures } from "../search.fixtures.js";
import { HoldsShell, LoansShell, SearchShell } from "./shells.js";

function pick<T extends { name: string }>(arr: T[], name: string): T {
  return arr.find((f) => f.name === name) ?? arr[0];
}

const loansTypical = pick(
  loansFixtures,
  "Mixed urgency (typical)",
).structuredContent;
const holdsTypical = pick(
  holdsFixtures,
  "Mixed queue (typical)",
).structuredContent;
const searchTypical = pick(
  searchFixtures,
  "Mixed format query",
).structuredContent;

type Scenario = { label: string; prompt: string; response: ReactNode };

const SCENARIOS: Scenario[] = [
  {
    label: "Checkouts — what's out & when it's due",
    prompt: "What books do I have checked out, and when are they due back?",
    response: <LoansShell payload={loansTypical} />,
  },
  {
    label: "Holds — how much longer",
    prompt: "How much longer on my holds?",
    response: <HoldsShell payload={holdsTypical} />,
  },
  {
    label: "Search — catalog results",
    prompt: "Search the library catalog for Kurt Cobain — books and CDs.",
    response: <SearchShell payload={searchTypical} />,
  },
];

const theme: "light" | "dark" =
  new URLSearchParams(location.search).get("theme") === "dark"
    ? "dark"
    : "light";

const HOST_BG = theme === "dark" ? "#1f1e1d" : "#ffffff";
const HOST_FG = theme === "dark" ? "#e8e6e3" : "#1a1a1a";

const pageStyle: CSSProperties = {
  colorScheme: theme,
  background: HOST_BG,
  color: HOST_FG,
  minHeight: "100vh",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
};

const columnStyle: CSSProperties = {
  maxWidth: 680,
  margin: "0 auto",
  padding: "32px 24px 64px",
  display: "flex",
  flexDirection: "column",
  gap: 40,
};

const eyebrowStyle: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: 1.2,
  opacity: 0.5,
  marginBottom: 12,
};

// Approximates a Claude user message bubble.
const userBubbleStyle: CSSProperties = {
  alignSelf: "flex-end",
  maxWidth: "85%",
  background: "light-dark(#f0eee6, #34322d)",
  borderRadius: 14,
  padding: "10px 14px",
  fontSize: 15,
  lineHeight: 1.45,
  marginBottom: 16,
};

// The assistant's reply: a little "Claude" label + the rendered card,
// constrained to a realistic in-product width.
const cardWrapStyle: CSSProperties = {
  maxWidth: 460,
};

function Scenario({ label, prompt, response }: Scenario) {
  return (
    <section>
      <div style={eyebrowStyle}>{label}</div>
      <div style={{ display: "flex", flexDirection: "column" }}>
        <div style={userBubbleStyle}>{prompt}</div>
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            opacity: 0.5,
            margin: "0 0 8px 2px",
          }}
        >
          Claude
        </div>
        <div style={cardWrapStyle}>{response}</div>
      </div>
    </section>
  );
}

const switcherStyle: CSSProperties = {
  position: "sticky",
  top: 0,
  zIndex: 10,
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  padding: "10px 0",
  background: HOST_BG,
  borderBottom:
    "1px solid light-dark(rgba(0,0,0,0.08), rgba(255,255,255,0.08))",
};

const switchChip: CSSProperties = {
  appearance: "none",
  fontFamily: "inherit",
  cursor: "pointer",
  border: "1px solid light-dark(#dcdcd7, #3a3a38)",
  background: "transparent",
  color: "inherit",
  borderRadius: 6,
  padding: "4px 10px",
  fontSize: 13,
  fontWeight: 600,
};

const switchActive: CSSProperties = {
  ...switchChip,
  background: "light-dark(#0f6dbf, #2f72ab)",
  color: "#fff",
  borderColor: "transparent",
};

function HeaderSwitcher({
  value,
  onChange,
}: {
  value: HeaderVariant;
  onChange: (v: HeaderVariant) => void;
}) {
  return (
    <div style={switcherStyle}>
      <span
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: 0.6,
          opacity: 0.5,
        }}
      >
        Header
      </span>
      {HEADER_VARIANTS.map((v) => (
        <button
          key={v}
          type="button"
          onClick={() => onChange(v)}
          title={HEADER_VARIANT_NOTES[v]}
          style={v === value ? switchActive : switchChip}
        >
          {v}
        </button>
      ))}
      <span style={{ fontSize: 12, opacity: 0.6 }}>
        {HEADER_VARIANT_NOTES[value]}
      </span>
    </div>
  );
}

function Scenarios() {
  const [variant, setVariant] = useState<HeaderVariant>(DEFAULT_HEADER_VARIANT);
  return (
    <HeaderVariantContext.Provider value={variant}>
      <div style={pageStyle}>
        <div style={columnStyle}>
          <header>
            <h1 style={{ fontSize: 18, fontWeight: 700, margin: "0 0 4px" }}>
              bibliocommons-mcp — product scenarios
            </h1>
            <p style={{ margin: 0, fontSize: 13, opacity: 0.6 }}>
              The three flows the cards are built for, framed as a conversation.
              Switch the header lockup below; append <code>?theme=dark</code>{" "}
              for dark mode.
            </p>
          </header>
          <HeaderSwitcher value={variant} onChange={setVariant} />
          {SCENARIOS.map((s) => (
            <Scenario key={s.label} {...s} />
          ))}
        </div>
      </div>
    </HeaderVariantContext.Provider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <Scenarios />
  </StrictMode>,
);

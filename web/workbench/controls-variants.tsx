/**
 * Dev-only filter-pill + CTA-button style comparison — NOT a shipped bundle.
 * Open: /workbench/controls-variants.html  (?theme=dark)
 */
import { StrictMode, type CSSProperties, type ReactNode } from "react";
import { createRoot } from "react-dom/client";

import { ResponsiveStyles } from "../lib/responsive.js";

const theme: "light" | "dark" =
  new URLSearchParams(location.search).get("theme") === "dark"
    ? "dark"
    : "light";

const OPTS = ["All", "Book", "CD"];
const BLUE = "#0f6dbf";

// ---------- Filter styles ----------
function FilterRow({
  base,
  active,
  wrap,
}: {
  base: CSSProperties;
  active: CSSProperties;
  wrap?: CSSProperties;
}) {
  return (
    <div style={{ display: "inline-flex", gap: 6, ...wrap }}>
      {OPTS.map((o, i) => (
        <button key={o} type="button" style={i === 0 ? active : base}>
          {o}
        </button>
      ))}
    </div>
  );
}

const btnReset: CSSProperties = {
  appearance: "none",
  fontFamily: "inherit",
  cursor: "pointer",
  color: "inherit",
};

const FILTERS: { note: string; node: ReactNode }[] = [
  {
    note: "1. Outlined pills, active solid (current)",
    node: (
      <FilterRow
        base={{
          ...btnReset,
          border: "1px solid light-dark(#dcdcd7, #3a3a38)",
          background: "transparent",
          borderRadius: 999,
          padding: "3px 11px",
          fontSize: 12,
          fontWeight: 500,
        }}
        active={{
          ...btnReset,
          border: "1px solid transparent",
          background: BLUE,
          color: "#fff",
          borderRadius: 999,
          padding: "3px 11px",
          fontSize: 12,
          fontWeight: 600,
        }}
      />
    ),
  },
  {
    note: "2. Segmented control (active = raised card)",
    node: (
      <FilterRow
        wrap={{
          background: "light-dark(rgba(0,0,0,0.05), rgba(255,255,255,0.07))",
          borderRadius: 9,
          padding: 3,
          gap: 2,
        }}
        base={{
          ...btnReset,
          border: "none",
          background: "transparent",
          borderRadius: 6,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
          opacity: 0.7,
        }}
        active={{
          ...btnReset,
          border: "none",
          background: "light-dark(#fff, rgba(255,255,255,0.16))",
          borderRadius: 6,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
          boxShadow: "0 1px 2px rgba(0,0,0,0.12)",
        }}
      />
    ),
  },
  {
    note: "3. Underline tabs",
    node: (
      <FilterRow
        wrap={{ gap: 16 }}
        base={{
          ...btnReset,
          border: "none",
          background: "none",
          padding: "2px 0 5px",
          fontSize: 13,
          fontWeight: 600,
          opacity: 0.55,
          borderBottom: "2px solid transparent",
        }}
        active={{
          ...btnReset,
          border: "none",
          background: "none",
          padding: "2px 0 5px",
          fontSize: 13,
          fontWeight: 700,
          color: BLUE,
          borderBottom: `2px solid ${BLUE}`,
        }}
      />
    ),
  },
  {
    note: "4. Soft tonal (no borders)",
    node: (
      <FilterRow
        base={{
          ...btnReset,
          border: "none",
          background: "light-dark(rgba(0,0,0,0.06), rgba(255,255,255,0.10))",
          borderRadius: 999,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
        }}
        active={{
          ...btnReset,
          border: "none",
          background:
            "light-dark(rgba(15,109,191,0.14), rgba(77,159,232,0.22))",
          color: "light-dark(#0b5da6, #9ccbf0)",
          borderRadius: 999,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
        }}
      />
    ),
  },
];

// ---------- CTA styles ----------
const CTAS: { note: string; node: ReactNode }[] = [
  {
    note: "A. Text link (current)",
    node: (
      <a
        href="#"
        style={{
          color: "light-dark(#0b5da6, #9ccbf0)",
          textDecoration: "none",
          fontWeight: 600,
          fontSize: 13,
        }}
      >
        Manage holds →
      </a>
    ),
  },
  {
    note: "B. Outlined button",
    node: (
      <button
        type="button"
        style={{
          ...btnReset,
          border: "1px solid light-dark(#cdd6df, #3a4654)",
          background: "transparent",
          color: "light-dark(#0b5da6, #9ccbf0)",
          borderRadius: 8,
          padding: "7px 14px",
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        Manage holds
      </button>
    ),
  },
  {
    note: "C. Filled button",
    node: (
      <button
        type="button"
        style={{
          ...btnReset,
          border: "none",
          background: BLUE,
          color: "#fff",
          borderRadius: 8,
          padding: "8px 16px",
          fontSize: 13,
          fontWeight: 600,
        }}
      >
        Manage holds
      </button>
    ),
  },
  {
    note: "D. Soft tonal button",
    node: (
      <button
        type="button"
        style={{
          ...btnReset,
          border: "none",
          background:
            "light-dark(rgba(15,109,191,0.12), rgba(77,159,232,0.22))",
          color: "light-dark(#0b5da6, #9ccbf0)",
          borderRadius: 8,
          padding: "8px 16px",
          fontSize: 13,
          fontWeight: 700,
        }}
      >
        Manage holds →
      </button>
    ),
  },
];

const pageStyle: CSSProperties = {
  colorScheme: theme,
  background: theme === "dark" ? "#1f1e1d" : "#ffffff",
  color: theme === "dark" ? "#e8e6e3" : "#1a1a1a",
  minHeight: "100vh",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
};

const cardBg: CSSProperties = {
  background: "light-dark(#fcfcfa, #272726)",
  border: "1px solid light-dark(#d9d9d9, #383836)",
  borderRadius: 12,
  padding: "16px 20px",
};

function Section({
  title,
  items,
}: {
  title: string;
  items: { note: string; node: ReactNode }[];
}) {
  return (
    <section style={{ marginBottom: 36 }}>
      <h2 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 14px" }}>
        {title}
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {items.map((it) => (
          <div key={it.note}>
            <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>
              {it.note}
            </div>
            <div style={cardBg}>{it.node}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Controls() {
  return (
    <div style={pageStyle}>
      <div
        style={{ maxWidth: 560, margin: "0 auto", padding: "28px 24px 64px" }}
      >
        <h1 style={{ fontSize: 18, fontWeight: 700, margin: "0 0 24px" }}>
          Filter pills &amp; CTA buttons — pick a style
        </h1>
        <Section title="Filter pills" items={FILTERS} />
        <Section title="Footer CTA button" items={CTAS} />
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <Controls />
  </StrictMode>,
);

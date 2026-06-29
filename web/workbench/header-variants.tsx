/**
 * Dev-only header-lockup comparison — NOT a shipped bundle.
 *
 * Six treatments of the "Seattle Public Library" + title lockup (library
 * above vs below, different weights/cases) shown in context above a sample
 * row, so a direction can be picked before it's applied to CardHeader.
 *
 * Open: http://localhost:5176/workbench/header-variants.html  (?theme=dark)
 */
import { StrictMode, type CSSProperties, type ReactNode } from "react";
import { createRoot } from "react-dom/client";

import { HoldCard } from "../components/HoldCard.js";
import { ResponsiveStyles } from "../lib/responsive.js";
import { rootStyle } from "../lib/root-style.js";
import { fixtures as holdsFixtures } from "../holds.fixtures.js";

const sampleHold = holdsFixtures.find(
  (f) => f.name === "Single ready for pickup",
)!.structuredContent.holds[0];

const LIBRARY = "Seattle Public Library";
const TITLE = "Your holds";

const theme: "light" | "dark" =
  new URLSearchParams(location.search).get("theme") === "dark"
    ? "dark"
    : "light";

const lib = (s: CSSProperties) =>
  ({ margin: 0, opacity: 0.5, ...s }) as CSSProperties;
const ttl = (s: CSSProperties) => ({ margin: 0, ...s }) as CSSProperties;

type Variant = { id: string; note: string; header: ReactNode };

const VARIANTS: Variant[] = [
  {
    id: "A",
    note: "Eyebrow above · uppercase 11/600 (current)",
    header: (
      <header>
        <p
          style={lib({
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: 0.4,
            textTransform: "uppercase",
          })}
        >
          {LIBRARY}
        </p>
        <h2 style={ttl({ fontSize: 16, fontWeight: 700, marginTop: 2 })}>
          {TITLE}
        </h2>
      </header>
    ),
  },
  {
    id: "B",
    note: "Title first · library below, small caps muted",
    header: (
      <header>
        <h2 style={ttl({ fontSize: 17, fontWeight: 700 })}>{TITLE}</h2>
        <p
          style={lib({
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: 0.4,
            textTransform: "uppercase",
            marginTop: 3,
          })}
        >
          {LIBRARY}
        </p>
      </header>
    ),
  },
  {
    id: "C",
    note: "Eyebrow above · normal case, regular weight",
    header: (
      <header>
        <p style={lib({ fontSize: 12.5, fontWeight: 500, opacity: 0.55 })}>
          {LIBRARY}
        </p>
        <h2 style={ttl({ fontSize: 17, fontWeight: 700, marginTop: 1 })}>
          {TITLE}
        </h2>
      </header>
    ),
  },
  {
    id: "D",
    note: "Title-dominant · big title, tiny tracked label below",
    header: (
      <header>
        <h2 style={ttl({ fontSize: 19, fontWeight: 800, letterSpacing: -0.3 })}>
          {TITLE}
        </h2>
        <p
          style={lib({
            fontSize: 10.5,
            fontWeight: 600,
            letterSpacing: 0.8,
            textTransform: "uppercase",
            marginTop: 4,
            opacity: 0.45,
          })}
        >
          {LIBRARY}
        </p>
      </header>
    ),
  },
  {
    id: "E",
    note: "Library-forward · bold eyebrow, quieter title",
    header: (
      <header>
        <p
          style={lib({
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 0.3,
            textTransform: "uppercase",
            opacity: 0.7,
          })}
        >
          {LIBRARY}
        </p>
        <h2
          style={ttl({
            fontSize: 14,
            fontWeight: 600,
            marginTop: 3,
            opacity: 0.9,
          })}
        >
          {TITLE}
        </h2>
      </header>
    ),
  },
  {
    id: "F",
    note: "One line · title with library trailing",
    header: (
      <header
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <h2 style={ttl({ fontSize: 17, fontWeight: 700 })}>{TITLE}</h2>
        <span style={lib({ fontSize: 12, fontWeight: 500, opacity: 0.5 })}>
          · {LIBRARY}
        </span>
      </header>
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

function Variants() {
  return (
    <div style={pageStyle}>
      <div
        style={{
          maxWidth: 1040,
          margin: "0 auto",
          padding: "28px 24px 64px",
          display: "grid",
          gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
          gap: 28,
        }}
      >
        <h1
          style={{
            gridColumn: "1 / -1",
            margin: 0,
            fontSize: 18,
            fontWeight: 700,
          }}
        >
          Header lockups — pick a direction
        </h1>
        {VARIANTS.map((v) => (
          <div key={v.id}>
            <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>
              <strong>{v.id}.</strong> {v.note}
            </div>
            <div style={{ ...rootStyle, maxWidth: 440 }}>
              {v.header}
              <div style={{ marginTop: 12 }}>
                <HoldCard hold={sampleHold} index={0} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <Variants />
  </StrictMode>,
);

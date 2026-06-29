/**
 * Dev-only static gallery — NOT a shipped bundle.
 *
 * Lives under web/workbench/ so the bundle build's top-level `web/*.html`
 * glob (web/scripts/inline_bundles.mjs) never picks it up. It imports the
 * real card components + fixtures and reproduces each app shell WITHOUT
 * the MCP Apps host handshake, so every fixture renders directly. Used to
 * eyeball / screenshot all card states in light + dark while polishing.
 *
 * Serve via:  cd web && npx vite --port 5175
 * Then open:  http://localhost:5175/workbench/gallery.html
 */
import { StrictMode, type ReactNode } from "react";
import { createRoot } from "react-dom/client";

import { ResponsiveStyles } from "../lib/responsive.js";
import { fixtures as holdsFixtures } from "../holds.fixtures.js";
import { fixtures as loansFixtures } from "../loans.fixtures.js";
import { fixtures as searchFixtures } from "../search.fixtures.js";
import { HoldsShell, LoansShell, SearchShell } from "./shells.js";

// --- Theme columns: approximate the Claude host conversation backdrop so
// --- the cream/charcoal card chrome reads the way it will in-product.

const CARD_WIDTH = 400;

const HOST_BG: Record<"light" | "dark", string> = {
  light: "#ffffff",
  dark: "#1f1e1d",
};

function ThemeColumn({
  theme,
  children,
}: {
  theme: "light" | "dark";
  children: ReactNode;
}) {
  return (
    <div
      style={{
        colorScheme: theme,
        background: HOST_BG[theme],
        color: theme === "dark" ? "#e8e6e3" : "#1a1a1a",
        padding: 24,
        display: "flex",
        flexDirection: "column",
        gap: 20,
        flex: 1,
        minHeight: "100vh",
      }}
    >
      <div
        style={{
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: 1,
          opacity: 0.5,
        }}
      >
        {theme}
      </div>
      {children}
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ width: CARD_WIDTH, maxWidth: "100%" }}>
      <div style={{ fontSize: 11, opacity: 0.55, marginBottom: 6 }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function Section({
  title,
  themes,
  render,
}: {
  title: string;
  themes: ("light" | "dark")[];
  render: (theme: "light" | "dark") => ReactNode;
}) {
  return (
    <>
      <h1
        id={title.toLowerCase()}
        style={{
          gridColumn: "1 / -1",
          margin: "8px 0 0",
          padding: "8px 24px",
          fontSize: 13,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: 1.5,
          background: "#000",
          color: "#fff",
        }}
      >
        {title}
      </h1>
      {themes.map((t) => (
        <ThemeColumn key={t} theme={t}>
          {render(t)}
        </ThemeColumn>
      ))}
    </>
  );
}

function Gallery() {
  // ?only=holds|loans|search renders a single section so each can be
  // screenshotted at a bounded height. ?theme=light|dark renders a single
  // theme column — handy for screenshotting the narrow (responsive) case
  // at a small window width, where the @media query in lib/responsive fires.
  const params = new URLSearchParams(location.search);
  const only = params.get("only");
  const theme = params.get("theme");
  const themes: ("light" | "dark")[] =
    theme === "light"
      ? ["light"]
      : theme === "dark"
        ? ["dark"]
        : ["light", "dark"];
  const show = (name: string) => !only || only === name;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: themes.length === 1 ? "1fr" : "1fr 1fr",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {show("holds") && (
        <Section
          title="Holds"
          themes={themes}
          render={() => (
            <>
              {holdsFixtures.map((fx) => (
                <Labeled key={fx.name} label={fx.name}>
                  <HoldsShell payload={fx.structuredContent} />
                </Labeled>
              ))}
            </>
          )}
        />
      )}
      {show("loans") && (
        <Section
          title="Checkouts"
          themes={themes}
          render={() => (
            <>
              {loansFixtures.map((fx) => (
                <Labeled key={fx.name} label={fx.name}>
                  <LoansShell payload={fx.structuredContent} />
                </Labeled>
              ))}
            </>
          )}
        />
      )}
      {show("search") && (
        <Section
          title="Search"
          themes={themes}
          render={() => (
            <>
              {searchFixtures.map((fx) => (
                <Labeled key={fx.name} label={fx.name}>
                  <SearchShell payload={fx.structuredContent} />
                </Labeled>
              ))}
            </>
          )}
        />
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ResponsiveStyles />
    <Gallery />
  </StrictMode>,
);

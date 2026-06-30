/**
 * Dev-only row-lockup comparison — NOT a shipped bundle.
 *
 * Several treatments of a single checkout row, to settle (a) how the
 * status reads against the title's left edge — chip vs. text — and (b)
 * which extra fields (author, exact due date, availability) are worth
 * pulling in. Open: /workbench/row-variants.html  (?theme=dark)
 */
import { StrictMode, type CSSProperties, type ReactNode } from "react";
import { createRoot } from "react-dom/client";

import {
  badgeStyle,
  lineStyle,
  metaStyle,
  rowStyle,
  statusChipStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { ResponsiveStyles } from "../lib/responsive.js";
import { rootStyle } from "../lib/root-style.js";

const theme: "light" | "dark" =
  new URLSearchParams(location.search).get("theme") === "dark"
    ? "dark"
    : "light";

const JACKET = {
  small: null,
  medium: null,
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780385471992/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

const ITEM = {
  title: "Come as You Are",
  author: "Azerrad, Michael",
  format: "Audiobook",
  year: "2026",
  due: "Due in 4 days",
  dueExact: "until Jul 3",
  hint: "Not renewable",
};

const TITLE = titleStyle(3);

// Status rendered as plain coloured text (aligns to the title's left edge
// with no chip background overhanging the grid).
const statusTextStyle: CSSProperties = {
  fontSize: 12.5,
  fontWeight: 700,
  color: "light-dark(#0b5da6, #9ccbf0)",
};

function Row({ children }: { children: ReactNode }) {
  return (
    <div style={rowStyle}>
      <CoverImage jacket={JACKET} eager />
      <div style={metaStyle}>{children}</div>
    </div>
  );
}

const pillRow = (extra?: CSSProperties): CSSProperties => ({
  display: "flex",
  alignItems: "center",
  gap: 6,
  flexWrap: "wrap",
  marginTop: 3,
  ...extra,
});

type Variant = { id: string; note: string; render: () => ReactNode };

const VARIANTS: Variant[] = [
  {
    id: "1",
    note: "Chips, background aligned to the title (text sits slightly inset — conventional pill)",
    render: () => (
      <Row>
        <h3 style={TITLE}>{ITEM.title}</h3>
        <div style={pillRow()}>
          <span style={statusChipStyle}>{ITEM.due}</span>
          <span style={badgeStyle}>{ITEM.format}</span>
        </div>
        <p style={lineStyle}>{ITEM.hint}</p>
      </Row>
    ),
  },
  {
    id: "2",
    note: "Status as coloured text (aligns exactly to the title); format stays a chip",
    render: () => (
      <Row>
        <h3 style={TITLE}>{ITEM.title}</h3>
        <div style={pillRow()}>
          <span style={statusTextStyle}>{ITEM.due}</span>
          <span style={badgeStyle}>{ITEM.format}</span>
        </div>
        <p style={lineStyle}>{ITEM.hint}</p>
      </Row>
    ),
  },
  {
    id: "3",
    note: "+ Author line (like the library row); chips below",
    render: () => (
      <Row>
        <h3 style={TITLE}>{ITEM.title}</h3>
        <p style={lineStyle}>by {ITEM.author}</p>
        <div style={pillRow()}>
          <span style={statusChipStyle}>{ITEM.due}</span>
          <span style={badgeStyle}>{ITEM.format}</span>
        </div>
        <p style={lineStyle}>{ITEM.hint}</p>
      </Row>
    ),
  },
  {
    id: "4",
    note: "Richer / labeled: author · format+year · coloured due + exact date",
    render: () => (
      <Row>
        <h3 style={TITLE}>{ITEM.title}</h3>
        <p style={lineStyle}>by {ITEM.author}</p>
        <div style={pillRow()}>
          <span style={badgeStyle}>{ITEM.format}</span>
          <span style={lineStyle}>{ITEM.year}</span>
        </div>
        <p style={{ ...lineStyle, marginTop: 3 }}>
          <span style={{ ...statusTextStyle, fontSize: 12 }}>{ITEM.due}</span>{" "}
          <span style={{ opacity: 0.7 }}>· {ITEM.dueExact}</span>
        </p>
      </Row>
    ),
  },
  {
    id: "5",
    note: "Status-forward: a coloured dot + status on its own line, format chip above",
    render: () => (
      <Row>
        <h3 style={TITLE}>{ITEM.title}</h3>
        <p style={lineStyle}>by {ITEM.author}</p>
        <div style={pillRow()}>
          <span style={badgeStyle}>{ITEM.format}</span>
        </div>
        <p
          style={{
            ...statusTextStyle,
            marginTop: 3,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: 999,
              background: "currentColor",
              display: "inline-block",
            }}
          />
          {ITEM.due} · {ITEM.hint}
        </p>
      </Row>
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
          maxWidth: 560,
          margin: "0 auto",
          padding: "28px 24px 64px",
          display: "flex",
          flexDirection: "column",
          gap: 28,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
          Row lockups — pick a direction
        </h1>
        {VARIANTS.map((v) => (
          <div key={v.id}>
            <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>
              <strong>{v.id}.</strong> {v.note}
            </div>
            <div style={rootStyle}>{v.render()}</div>
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

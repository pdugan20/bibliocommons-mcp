/**
 * Shared frame for a card list: the header, an optional format filter, the
 * rows (or an empty state), and a footer with pagination + a catalog link.
 * Used by holds / checkouts / search so they share one structure. The
 * filter is client-side React state over the already-returned items — no
 * server round-trip — and only appears when the list spans >1 format. The
 * filter-pill and CTA-button styles come from contexts (see lib/controls).
 */
import {
  useContext,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";

import { CardHeader } from "./card-header.js";
import {
  CtaStyleContext,
  FilterStyleContext,
  ctaStyle,
  filterStyles,
} from "./controls.js";
import { compareFormats, formatLabel } from "./format.js";
import { openLink } from "./open-link.js";
import { rootStyle } from "./root-style.js";

const emptyStyle: CSSProperties = {
  // Top margin separates the message from the header (no filter sits between
  // them here); bottom margin keeps it off the footer divider.
  margin: "14px 0 16px",
  fontSize: 13,
  opacity: 0.7,
};

const footerStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  // Sit the divider close under the last row; the CTA's own padding
  // supplies the breathing room below the line.
  marginTop: 6,
  paddingTop: 4,
  borderTop: "1px solid light-dark(#ececec, #2e2e2e)",
  fontSize: 12,
};

const footerNoteStyle: CSSProperties = { opacity: 0.6 };

function FilterBar({
  formats,
  value,
  onChange,
}: {
  formats: string[];
  value: string | null;
  onChange: (v: string | null) => void;
}) {
  const fs = filterStyles(useContext(FilterStyleContext));
  const options: { key: string | null; label: string }[] = [
    { key: null, label: "All" },
    ...formats.map((f) => ({ key: f, label: formatLabel(f) ?? f })),
  ];
  return (
    <div
      style={{ ...fs.wrap, marginTop: 12 }}
      role="tablist"
      aria-label="Filter by format"
    >
      {options.map((o) => {
        const active = o.key === value;
        return (
          <button
            key={o.key ?? "all"}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.key)}
            style={active ? fs.active : fs.base}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

type WithFormat = { format?: string | null };

export function CardFrame<T extends WithFormat>({
  library,
  title,
  items,
  emptyText,
  renderItem,
  footerNote,
  moreUrl,
  moreLabel,
}: {
  library?: string | null;
  title: string;
  items: T[];
  emptyText: string;
  renderItem: (item: T, index: number) => ReactNode;
  /** Small muted note on the left of the footer (e.g. "Page 1 of 3"). */
  footerNote?: string | null;
  /** A single link back to the library catalog. */
  moreUrl?: string | null;
  moreLabel?: string;
}) {
  const [filter, setFilter] = useState<string | null>(null);
  const cta = ctaStyle(useContext(CtaStyleContext));
  const ctaLabel = `${moreLabel ?? "View in catalog"}${cta.arrow ? " →" : ""}`;

  // Distinct format codes present, in a fixed canonical order so the filter
  // pills read the same across cards regardless of item order (which varies
  // with sorting).
  const formats: string[] = [];
  for (const it of items) {
    const f = it.format ?? null;
    if (f && !formats.includes(f)) formats.push(f);
  }
  formats.sort(compareFormats);

  const shown =
    filter == null
      ? items
      : items.filter((it) => (it.format ?? null) === filter);

  const empty =
    items.length === 0
      ? emptyText
      : shown.length === 0
        ? `No ${formatLabel(filter) ?? ""} items.`
        : null;

  return (
    <div style={rootStyle}>
      <CardHeader library={library} title={title} />
      {formats.length > 1 && (
        <FilterBar formats={formats} value={filter} onChange={setFilter} />
      )}
      {empty ? (
        <p style={emptyStyle}>{empty}</p>
      ) : (
        <div style={{ marginTop: formats.length > 1 ? 16 : 14 }}>
          {shown.map((it, i) => renderItem(it, i))}
        </div>
      )}
      {(moreUrl || footerNote) &&
        (cta.full && moreUrl ? (
          <div
            style={{
              marginTop: 14,
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {footerNote && (
              <span style={{ ...footerNoteStyle, textAlign: "center" }}>
                {footerNote}
              </span>
            )}
            <a
              href={moreUrl}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => {
                e.preventDefault();
                openLink(moreUrl);
              }}
              style={cta.style}
            >
              {ctaLabel}
            </a>
          </div>
        ) : (
          <div
            style={{
              ...footerStyle,
              justifyContent: footerNote ? "space-between" : "center",
            }}
          >
            {footerNote && <span style={footerNoteStyle}>{footerNote}</span>}
            {moreUrl && (
              <a
                href={moreUrl}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => {
                  e.preventDefault();
                  openLink(moreUrl);
                }}
                style={{ ...cta.style, whiteSpace: "nowrap" }}
              >
                {ctaLabel}
              </a>
            )}
          </div>
        ))}
    </div>
  );
}

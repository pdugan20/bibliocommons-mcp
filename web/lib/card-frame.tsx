/**
 * Shared frame for a card list: the header, an optional format filter, and
 * the rows (or an empty state). Used by holds / checkouts / search so they
 * share one structure. The filter is client-side React state over the
 * already-returned items — no server round-trip — and only appears when the
 * list actually contains more than one format.
 */
import { useState, type CSSProperties, type ReactNode } from "react";

import { CardHeader } from "./card-header.js";
import { formatLabel } from "./format.js";
import { rootStyle } from "./root-style.js";

const barStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 6,
  marginTop: 12,
};

const filterChipBase: CSSProperties = {
  appearance: "none",
  fontFamily: "inherit",
  border: "1px solid light-dark(#dcdcd7, #3a3a38)",
  background: "transparent",
  color: "inherit",
  borderRadius: 999,
  padding: "3px 11px",
  fontSize: 12,
  fontWeight: 500,
  cursor: "pointer",
};

const filterChipActive: CSSProperties = {
  ...filterChipBase,
  background: "light-dark(#0f6dbf, #2f72ab)",
  color: "#fff",
  borderColor: "transparent",
};

const emptyStyle: CSSProperties = {
  margin: "12px 0 0",
  fontSize: 13,
  opacity: 0.7,
};

function FilterBar({
  formats,
  value,
  onChange,
}: {
  formats: string[];
  value: string | null;
  onChange: (v: string | null) => void;
}) {
  const options: { key: string | null; label: string }[] = [
    { key: null, label: "All" },
    ...formats.map((f) => ({ key: f, label: formatLabel(f) ?? f })),
  ];
  return (
    <div style={barStyle} role="tablist" aria-label="Filter by format">
      {options.map((o) => {
        const active = o.key === value;
        return (
          <button
            key={o.key ?? "all"}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.key)}
            style={active ? filterChipActive : filterChipBase}
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
}: {
  library?: string | null;
  title: string;
  items: T[];
  emptyText: string;
  renderItem: (item: T, index: number) => ReactNode;
}) {
  const [filter, setFilter] = useState<string | null>(null);

  // Distinct format codes present, in first-seen order, for the filter.
  const formats: string[] = [];
  for (const it of items) {
    const f = it.format ?? null;
    if (f && !formats.includes(f)) formats.push(f);
  }

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
        <div style={{ marginTop: 10 }}>
          {shown.map((it, i) => renderItem(it, i))}
        </div>
      )}
    </div>
  );
}

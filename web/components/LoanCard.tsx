/**
 * One row in the loans list. Mirrors HoldCard structurally but the
 * status pill encodes due-date urgency instead of queue position.
 *
 * Data shape mirrors `bibliocommons_mcp.models.Loan`.
 */
import type { CSSProperties } from "react";

import {
  STATUS_DUE_SOON,
  STATUS_OVERDUE,
  STATUS_QUEUED,
} from "../lib/palette.js";
import type { Jacket } from "./HoldCard.js";

export type Loan = {
  checkout_id: string;
  metadata_id?: string | null;
  title?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  due?: string | null;
  call_number?: string | null;
  branch?: string | null;
  jacket?: Jacket | null;
};

const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";
const COVER_WIDTH = 64;
const COVER_HEIGHT = 88;

const rowStyle: CSSProperties = {
  display: "flex",
  gap: 12,
  paddingTop: 10,
  paddingBottom: 10,
  borderTop: "1px solid light-dark(#ececec, #2e2e2e)",
};

const firstRowStyle: CSSProperties = {
  ...rowStyle,
  borderTop: "none",
  paddingTop: 4,
};

const coverWrapStyle: CSSProperties = {
  flexShrink: 0,
  width: COVER_WIDTH,
  height: COVER_HEIGHT,
  background: COVER_FALLBACK_BG,
  borderRadius: 4,
  overflow: "hidden",
};

const coverImgStyle: CSSProperties = {
  width: "100%",
  height: "100%",
  objectFit: "cover",
  display: "block",
};

const metaStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 4,
  minWidth: 0,
  flex: 1,
};

const titleStyle: CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  margin: 0,
  display: "-webkit-box",
  WebkitBoxOrient: "vertical" as CSSProperties["WebkitBoxOrient"],
  WebkitLineClamp: 3,
  overflow: "hidden",
};

const lineStyle: CSSProperties = {
  fontSize: 12,
  opacity: 0.75,
  margin: 0,
};

const pillRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
  marginTop: 2,
};

const pillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  height: 18,
  padding: "0 8px",
  borderRadius: 9,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.2,
  textTransform: "uppercase",
};

type DueLabel = { text: string; color: string; bg: string };

function dueForRender(loan: Loan): DueLabel {
  // Compute due-date urgency relative to "today" (UTC midnight is fine
  // — we're not chasing minute-level accuracy, just bucketing into
  // overdue / due-soon / normal).
  const iso = loan.due;
  if (!iso) {
    return { text: "no due date", color: "white", bg: STATUS_QUEUED };
  }
  const dueDate = new Date(iso + "T00:00:00Z");
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const dayMs = 24 * 60 * 60 * 1000;
  const days = Math.round((dueDate.getTime() - today.getTime()) / dayMs);
  const shortDate = formatShort(iso);

  if (days < 0) {
    return {
      text: `overdue · ${shortDate}`,
      color: "white",
      bg: STATUS_OVERDUE,
    };
  }
  if (days <= 3) {
    return {
      text: `due ${days === 0 ? "today" : days === 1 ? "tomorrow" : `in ${days} days`} · ${shortDate}`,
      color: "white",
      bg: STATUS_DUE_SOON,
    };
  }
  return {
    text: `due ${shortDate}`,
    color: "white",
    bg: STATUS_QUEUED,
  };
}

function formatShort(iso?: string | null): string {
  if (!iso) return "";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  const months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const month = months[Number.parseInt(m[2], 10) - 1] ?? m[2];
  const day = Number.parseInt(m[3], 10);
  return `${month} ${day}`;
}

function CoverImage({ loan }: { loan: Loan }) {
  const src =
    loan.jacket?.local_url ?? loan.jacket?.small ?? loan.jacket?.medium ?? null;
  if (!src) return <div style={coverWrapStyle} aria-hidden="true" />;
  return (
    <div style={coverWrapStyle}>
      <img
        src={src}
        alt={loan.title ? `Cover of ${loan.title}` : ""}
        style={coverImgStyle}
        loading="lazy"
      />
    </div>
  );
}

export function LoanCard({ loan, isFirst }: { loan: Loan; isFirst?: boolean }) {
  const due = dueForRender(loan);
  const material = loan.material_type === "DIGITAL" ? "Digital" : "Physical";

  return (
    <div style={isFirst ? firstRowStyle : rowStyle}>
      <CoverImage loan={loan} />
      <div style={metaStyle}>
        <h3 style={titleStyle}>{loan.title ?? "(untitled)"}</h3>
        <div style={pillRowStyle}>
          <span
            style={{
              ...pillStyle,
              color: due.color,
              background: due.bg,
            }}
          >
            {due.text}
          </span>
          <span style={lineStyle}>{material}</span>
          {loan.branch && <span style={lineStyle}>{loan.branch}</span>}
        </div>
        {loan.call_number && <p style={lineStyle}>{loan.call_number}</p>}
      </div>
    </div>
  );
}

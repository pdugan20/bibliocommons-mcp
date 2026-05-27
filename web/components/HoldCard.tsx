/**
 * One row in the holds list. Cover image on the left, metadata on the
 * right (title, status pill, queue position, pickup branch).
 *
 * Data shape mirrors `bibliocommons_mcp.models.Hold` — keep field
 * names in sync if anything changes server-side.
 */
import type { CSSProperties } from "react";

import { STATUS_OVERDUE, STATUS_QUEUED, STATUS_READY } from "../lib/palette.js";

export type Jacket = {
  small?: string | null;
  medium?: string | null;
  large?: string | null;
  local_url?: string | null;
};

export type Hold = {
  hold_id: string;
  metadata_id?: string | null;
  title?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  status?: string | null;
  position?: number | null;
  pickup_branch?: string | null;
  placed?: string | null;
  expiry?: string | null;
  jacket?: Jacket | null;
};

const COVER_FALLBACK_BG = "light-dark(#e5e3df, #38383a)";
const COVER_WIDTH = 64;
const COVER_HEIGHT = 88; // ~book-cover aspect; CDs are squarer but Syndetics returns book-shaped fallbacks

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
  minWidth: 0, // lets long titles wrap inside flex
  flex: 1,
};

const titleStyle: CSSProperties = {
  fontSize: 14,
  fontWeight: 600,
  margin: 0,
  // Keep titles from blowing out the card vertically — three lines max.
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

type StatusLabel = { text: string; color: string; bg: string };

function statusForRender(hold: Hold): StatusLabel {
  // Status comes from the gateway as snake- / UPPER-cased strings; we
  // surface the friendly label + color pairing here so HoldCard
  // callers don't repeat themselves.
  const raw = hold.status ?? "";
  switch (raw) {
    case "READY_FOR_PICKUP":
      return {
        text: "Ready",
        color: "white",
        bg: STATUS_READY,
      };
    case "EXPIRED":
    case "CANCELLED":
      return {
        text: raw.toLowerCase(),
        color: "white",
        bg: STATUS_OVERDUE,
      };
    case "IN_TRANSIT":
      return {
        text: "In transit",
        color: "white",
        bg: STATUS_QUEUED,
      };
    case "NOT_YET_AVAILABLE":
    default: {
      // Queued: lead with position when we have one; fall back to the
      // raw status if not.
      const text =
        hold.position != null
          ? `#${hold.position} in queue`
          : raw
            ? raw.replace(/_/g, " ").toLowerCase()
            : "queued";
      return { text, color: "white", bg: STATUS_QUEUED };
    }
  }
}

function formatPlaced(iso?: string | null): string | null {
  // Gateway returns YYYY-MM-DD; render as e.g. "May 27" / "Jan 4"
  // without dragging in a date library.
  if (!iso) return null;
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

function CoverImage({ hold }: { hold: Hold }) {
  // Prefer the library's local upload when present, otherwise fall
  // back to Syndetics. small is fine here — we render at 64px wide.
  const src =
    hold.jacket?.local_url ?? hold.jacket?.small ?? hold.jacket?.medium ?? null;
  if (!src) return <div style={coverWrapStyle} aria-hidden="true" />;
  return (
    <div style={coverWrapStyle}>
      <img
        src={src}
        alt={hold.title ? `Cover of ${hold.title}` : ""}
        style={coverImgStyle}
        loading="lazy"
      />
    </div>
  );
}

export function HoldCard({ hold, isFirst }: { hold: Hold; isFirst?: boolean }) {
  const status = statusForRender(hold);
  const placed = formatPlaced(hold.placed);
  const material = hold.material_type === "DIGITAL" ? "Digital" : "Physical";

  return (
    <div style={isFirst ? firstRowStyle : rowStyle}>
      <CoverImage hold={hold} />
      <div style={metaStyle}>
        <h3 style={titleStyle}>{hold.title ?? "(untitled)"}</h3>
        <div style={pillRowStyle}>
          <span
            style={{
              ...pillStyle,
              color: status.color,
              background: status.bg,
            }}
          >
            {status.text}
          </span>
          <span style={lineStyle}>{material}</span>
          {hold.pickup_branch && (
            <span style={lineStyle}>{hold.pickup_branch}</span>
          )}
        </div>
        {placed && <p style={lineStyle}>Placed {placed}</p>}
      </div>
    </div>
  );
}

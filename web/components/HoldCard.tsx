/**
 * One row in the holds list. Cover image on the left, metadata on the
 * right (title, status pill, queue position, pickup branch).
 *
 * Data shape mirrors `bibliocommons_mcp.models.Hold` — keep field
 * names in sync if anything changes server-side.
 */
import {
  firstRowStyle,
  lineStyle,
  metaStyle,
  pillRowStyle,
  pillStyle,
  rowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatMonthDay } from "../lib/date.js";
import type { Jacket } from "../lib/jacket.js";
import { STATUS_OVERDUE, STATUS_QUEUED, STATUS_READY } from "../lib/palette.js";

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

const HOLD_TITLE_STYLE = titleStyle(3);

type StatusLabel = { text: string; color: string; bg: string };

function statusForRender(hold: Hold): StatusLabel {
  // Status comes from the gateway as snake- / UPPER-cased strings; we
  // surface the friendly label + color pairing here so HoldCard
  // callers don't repeat themselves.
  const raw = hold.status ?? "";
  switch (raw) {
    case "READY_FOR_PICKUP":
      return { text: "Ready", color: "white", bg: STATUS_READY };
    case "EXPIRED":
    case "CANCELLED":
      return { text: raw.toLowerCase(), color: "white", bg: STATUS_OVERDUE };
    case "IN_TRANSIT":
      return { text: "In transit", color: "white", bg: STATUS_QUEUED };
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

export function HoldCard({ hold, index }: { hold: Hold; index: number }) {
  const status = statusForRender(hold);
  const placed = formatMonthDay(hold.placed);
  const material = hold.material_type === "DIGITAL" ? "Digital" : "Physical";

  // Status-aware treatment beyond the pill: a ready-for-pickup hold gets a
  // green cover ring (it's the one that needs action); expired/cancelled
  // holds dim and strike through so they read as spent.
  const raw = hold.status ?? "";
  const ring = raw === "READY_FOR_PICKUP" ? STATUS_READY : undefined;
  const spent = raw === "EXPIRED" || raw === "CANCELLED";
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  return (
    <div style={spent ? { ...baseRow, opacity: 0.55 } : baseRow}>
      <CoverImage jacket={hold.jacket} eager={index < 3} accent={ring} />
      <div style={metaStyle}>
        <h3
          style={
            spent
              ? { ...HOLD_TITLE_STYLE, textDecoration: "line-through" }
              : HOLD_TITLE_STYLE
          }
        >
          {hold.title ?? "(untitled)"}
        </h3>
        <div style={pillRowStyle}>
          <span
            style={{ ...pillStyle, color: status.color, background: status.bg }}
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

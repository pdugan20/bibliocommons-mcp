/**
 * One row in the holds list. Cover image on the left, metadata on the
 * right (title, status chip, format, queue position, pickup branch).
 *
 * Data shape mirrors `bibliocommons_mcp.models.Hold` — keep field
 * names in sync if anything changes server-side.
 */
import type { CSSProperties } from "react";

import {
  badgeStyle,
  firstRowStyle,
  lineStyle,
  metaStyle,
  pillRowStyle,
  rowDividerStyle,
  rowStyle,
  spentChipStyle,
  statusChipStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatMonthDay } from "../lib/date.js";
import { formatLabel } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";

export type Hold = {
  hold_id: string;
  metadata_id?: string | null;
  title?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  format?: string | null;
  status?: string | null;
  position?: number | null;
  pickup_branch?: string | null;
  placed?: string | null;
  expiry?: string | null;
  jacket?: Jacket | null;
};

export type HoldList = {
  count: number;
  library?: string | null;
  holds: Hold[];
};

const HOLD_TITLE_STYLE = titleStyle(3);

type StatusLabel = { text: string; chip: CSSProperties };

function statusForRender(hold: Hold): StatusLabel {
  // Status comes from the gateway as snake- / UPPER-cased strings; we
  // surface the friendly label + chip pairing here.
  const raw = hold.status ?? "";
  switch (raw) {
    case "READY_FOR_PICKUP":
      return { text: "Ready", chip: statusChipStyle };
    case "EXPIRED":
      return { text: "Expired", chip: spentChipStyle };
    case "CANCELLED":
      return { text: "Cancelled", chip: spentChipStyle };
    case "IN_TRANSIT":
      return { text: "In transit", chip: statusChipStyle };
    case "NOT_YET_AVAILABLE":
    default: {
      // Queued: lead with position when we have one; fall back to the
      // raw status if not.
      const text =
        hold.position != null
          ? `#${hold.position} in queue`
          : raw
            ? raw.replace(/_/g, " ").toLowerCase()
            : "Queued";
      return { text, chip: statusChipStyle };
    }
  }
}

export function HoldCard({ hold, index }: { hold: Hold; index: number }) {
  const status = statusForRender(hold);
  const placed = formatMonthDay(hold.placed);
  const format = formatLabel(hold.format);
  const spent = hold.status === "EXPIRED" || hold.status === "CANCELLED";
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  // Bottom line: "Placed May 20 · Lake City".
  const meta = [placed ? `Placed ${placed}` : null, hold.pickup_branch]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={spent ? { ...baseRow, opacity: 0.55 } : baseRow}>
        <CoverImage
          jacket={hold.jacket}
          format={hold.format}
          eager={index < 3}
        />
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
            <span style={status.chip}>{status.text}</span>
            {format && <span style={badgeStyle}>{format}</span>}
          </div>
          {meta && <p style={lineStyle}>{meta}</p>}
        </div>
      </div>
    </>
  );
}

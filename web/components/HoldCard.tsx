/**
 * One row in the holds list. Cover image on the left, metadata on the
 * right (title, author, status chip, format, queue depth / pickup branch).
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
  author?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  format?: string | null;
  status?: string | null;
  position?: number | null;
  /** Holdable copies serving the queue — pairs with position. */
  copies?: number | null;
  pickup_branch?: string | null;
  placed?: string | null;
  /** For a ready hold: the last day to collect it. */
  pickup_by?: string | null;
  expiry?: string | null;
  jacket?: Jacket | null;
};

export type HoldList = {
  count: number;
  library?: string | null;
  more_url?: string | null;
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
      // Queued: lead with position, and pair it with the copy count when we
      // have it — position alone ("#35") doesn't convey speed; "#35 · 4
      // copies" does. Fall back to the raw status if there's no position.
      let text: string;
      if (hold.position != null) {
        text =
          hold.copies != null
            ? `#${hold.position} · ${hold.copies} ${hold.copies === 1 ? "copy" : "copies"}`
            : `#${hold.position} in queue`;
      } else {
        text = raw ? raw.replace(/_/g, " ").toLowerCase() : "Queued";
      }
      return { text, chip: statusChipStyle };
    }
  }
}

export function HoldCard({ hold, index }: { hold: Hold; index: number }) {
  const status = statusForRender(hold);
  const format = formatLabel(hold.format);
  const spent = hold.status === "EXPIRED" || hold.status === "CANCELLED";
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  // Bottom line is status-aware: a ready hold leads with its pickup deadline
  // ("Pick up by Jul 6"); everything else shows when it was placed.
  const pickupBy = formatMonthDay(hold.pickup_by);
  const placed = formatMonthDay(hold.placed);
  const primary =
    hold.status === "READY_FOR_PICKUP" && pickupBy
      ? `Pick up by ${pickupBy}`
      : placed
        ? `Placed ${placed}`
        : null;
  const meta = [primary, hold.pickup_branch].filter(Boolean).join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={spent ? { ...baseRow, opacity: 0.55 } : baseRow}>
        <CoverImage jacket={hold.jacket} eager={index < 3} />
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
          {hold.author && <p style={lineStyle}>by {hold.author}</p>}
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

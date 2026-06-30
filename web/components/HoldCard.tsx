/**
 * One row in the holds list. Cover on the left; on the right the title with
 * a right-aligned status chip, then author, format · year, and a
 * status-aware line (pickup deadline for ready holds, else placed date).
 *
 * Data shape mirrors `bibliocommons_mcp.models.Hold` — keep field
 * names in sync if anything changes server-side.
 */
import type { CSSProperties } from "react";

import {
  firstRowStyle,
  lineStyle,
  metaStyle,
  rowDividerStyle,
  rowStyle,
  spentChipStyle,
  statusChipStyle,
  titleRowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatMonthDay } from "../lib/date.js";
import { formatLabelLong } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";

export type Hold = {
  hold_id: string;
  metadata_id?: string | null;
  title?: string | null;
  author?: string | null;
  year?: string | null;
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

const TITLE_STYLE: CSSProperties = { ...titleStyle(3), flex: 1, minWidth: 0 };
const CHIP_RIGHT: CSSProperties = { flexShrink: 0 };

// 1 -> "1st", 2 -> "2nd", 54 -> "54th".
function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return `${n}${s[(v - 20) % 10] ?? s[v] ?? s[0]}`;
}

type StatusLabel = { text: string; chip: CSSProperties };

function statusForRender(hold: Hold): StatusLabel {
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
      // Spell out the wait: "54th in line on 12 copies" conveys speed in a
      // way a bare position never could.
      let text: string;
      if (hold.position != null) {
        const place = `${ordinal(hold.position)} in line`;
        text =
          hold.copies != null
            ? `${place} on ${hold.copies} ${hold.copies === 1 ? "copy" : "copies"}`
            : place;
      } else {
        text = raw ? raw.replace(/_/g, " ").toLowerCase() : "Queued";
      }
      return { text, chip: statusChipStyle };
    }
  }
}

export function HoldCard({ hold, index }: { hold: Hold; index: number }) {
  const status = statusForRender(hold);
  const spent = hold.status === "EXPIRED" || hold.status === "CANCELLED";
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  const formatYear = [formatLabelLong(hold.format), hold.year]
    .filter(Boolean)
    .join(" · ");

  // A ready hold leads with its pickup deadline + location; everything else
  // shows when it was placed.
  const pickupBy = formatMonthDay(hold.pickup_by);
  const placed = formatMonthDay(hold.placed);
  const metaLine =
    hold.status === "READY_FOR_PICKUP" && pickupBy
      ? `Pick up by ${pickupBy}${hold.pickup_branch ? ` at ${hold.pickup_branch}` : ""}`
      : [placed ? `Placed ${placed}` : null, hold.pickup_branch]
          .filter(Boolean)
          .join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={spent ? { ...baseRow, opacity: 0.55 } : baseRow}>
        <CoverImage jacket={hold.jacket} eager={index < 3} />
        <div style={metaStyle}>
          <div style={titleRowStyle}>
            <h3
              style={
                spent
                  ? { ...TITLE_STYLE, textDecoration: "line-through" }
                  : TITLE_STYLE
              }
            >
              {hold.title ?? "(untitled)"}
            </h3>
            <span style={{ ...status.chip, ...CHIP_RIGHT }}>{status.text}</span>
          </div>
          {hold.author && <p style={lineStyle}>{hold.author}</p>}
          {formatYear && <p style={lineStyle}>{formatYear}</p>}
          {metaLine && <p style={lineStyle}>{metaLine}</p>}
        </div>
      </div>
    </>
  );
}

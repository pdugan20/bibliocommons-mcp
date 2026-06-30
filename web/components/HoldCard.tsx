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
  badgeStyle,
  firstRowStyle,
  lineStyle,
  metaStyle,
  rowDividerStyle,
  rowStyle,
  spentChipStyle,
  titleRowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatMonthDay } from "../lib/date.js";
import { cleanCreator, formatLabelLong } from "../lib/format.js";
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
      return { text: "Ready", chip: badgeStyle };
    case "EXPIRED":
      return { text: "Expired", chip: spentChipStyle };
    case "CANCELLED":
      return { text: "Cancelled", chip: spentChipStyle };
    case "IN_TRANSIT":
      return { text: "In transit", chip: badgeStyle };
    case "NOT_YET_AVAILABLE": {
      // Position spelled out as a place in line ("8th in line"); when the
      // gateway omits a position, fall back to a plain "Not available".
      const text =
        hold.position != null
          ? `${ordinal(hold.position)} in line`
          : "Not available";
      return { text, chip: badgeStyle };
    }
    default: {
      // Unknown status: title-case the raw enum so it reads as a label.
      const text = raw
        ? raw.charAt(0) + raw.slice(1).toLowerCase().replace(/_/g, " ")
        : "Queued";
      return { text, chip: badgeStyle };
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
  const metaLine = (
    hold.status === "READY_FOR_PICKUP" && pickupBy
      ? [`Pick up by ${pickupBy}`, hold.pickup_branch]
      : [placed ? `Placed ${placed}` : null, hold.pickup_branch]
  )
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
          {hold.author && <p style={lineStyle}>{cleanCreator(hold.author)}</p>}
          {formatYear && <p style={lineStyle}>{formatYear}</p>}
          {metaLine && <p style={lineStyle}>{metaLine}</p>}
        </div>
      </div>
    </>
  );
}

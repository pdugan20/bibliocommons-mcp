/**
 * One row in the loans list. Mirrors HoldCard: cover, then the title with a
 * right-aligned due chip, author, format · year, and a detail line (branch,
 * call number, renewal hint).
 *
 * Data shape mirrors `bibliocommons_mcp.models.Loan`.
 */
import type { CSSProperties } from "react";

import {
  badgeStyle,
  firstRowStyle,
  lineStyle,
  metaStyle,
  rowDividerStyle,
  rowStyle,
  titleRowStyle,
  titleStyle,
} from "../lib/card-style.js";
import { CoverImage } from "../lib/cover.js";
import { formatMonthDay } from "../lib/date.js";
import { cleanCreator, formatLabelLong } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";

export type Loan = {
  checkout_id: string;
  metadata_id?: string | null;
  title?: string | null;
  author?: string | null;
  year?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  format?: string | null;
  due?: string | null;
  call_number?: string | null;
  branch?: string | null;
  jacket?: Jacket | null;
  actions?: string[];
  times_renewed?: number;
};

export type LoanList = {
  count: number;
  library?: string | null;
  more_url?: string | null;
  loans: Loan[];
};

const TITLE_STYLE: CSSProperties = { ...titleStyle(3), flex: 1, minWidth: 0 };
const CHIP_RIGHT: CSSProperties = { flexShrink: 0 };

function dueText(loan: Loan): string {
  const iso = loan.due;
  if (!iso) return "No due date";
  const dueDate = new Date(iso + "T00:00:00Z");
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const dayMs = 24 * 60 * 60 * 1000;
  const days = Math.round((dueDate.getTime() - today.getTime()) / dayMs);

  // Relative phrasings carry the timing on their own — only the far-future
  // case needs the explicit date.
  if (days < 0) return "Overdue";
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  if (days <= 3) return `Due in ${days} days`;
  return `Due ${formatMonthDay(iso) ?? ""}`;
}

function renewalHint(loan: Loan): string | null {
  const actions = loan.actions ?? [];
  // Just whether it's renewable — the renewal count (times_renewed) is
  // more detail than a "can I keep this longer?" glance needs.
  if (actions.includes("renew")) return "Renewable";
  if (actions.includes("checkIn")) return "Return only";
  return null;
}

export function LoanCard({ loan, index }: { loan: Loan; index: number }) {
  const hint = renewalHint(loan);
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  const formatYear = [formatLabelLong(loan.format), loan.year]
    .filter(Boolean)
    .join(" · ");

  // No call number: it's shelf-finding jargon, and its cutter just repeats
  // the author already shown above (e.g. "… CROSS" for "Cross, Charles R.")
  // — useless for an item you already hold. The line is branch · renewal.
  const meta = [loan.branch, hint].filter(Boolean).join(" · ");

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={baseRow}>
        <CoverImage jacket={loan.jacket} eager={index < 3} />
        <div style={metaStyle}>
          <div style={titleRowStyle}>
            <h3 style={TITLE_STYLE}>{loan.title ?? "(untitled)"}</h3>
            <span style={{ ...badgeStyle, ...CHIP_RIGHT }}>
              {dueText(loan)}
            </span>
          </div>
          {loan.author && <p style={lineStyle}>{cleanCreator(loan.author)}</p>}
          {formatYear && <p style={lineStyle}>{formatYear}</p>}
          {meta && <p style={lineStyle}>{meta}</p>}
        </div>
      </div>
    </>
  );
}

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
import { cleanCreator, formatLabelLong, isDiscFormat } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";
import { RecordLink } from "../lib/open-link.js";

const COVER_LINK_STYLE: CSSProperties = { display: "block", flexShrink: 0 };

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
  url?: string | null;
};

export type LoanList = {
  count: number;
  library?: string | null;
  more_url?: string | null;
  loans: Loan[];
};

const TITLE_STYLE: CSSProperties = { ...titleStyle(2), flex: 1, minWidth: 0 };
// CD titles clamp to one line on a narrow viewport (var flips to 1 via a
// media query) so the title doesn't overshoot the short square cover.
const TITLE_STYLE_CD: CSSProperties = {
  ...titleStyle("var(--bc-cd-title-lines, 2)"),
  flex: 1,
  minWidth: 0,
};
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
  if (actions.includes("checkIn")) return "Not renewable";
  return null;
}

export function LoanCard({ loan, index }: { loan: Loan; index: number }) {
  const hint = renewalHint(loan);
  const baseRow = index === 0 ? firstRowStyle : rowStyle;

  const formatYear = [formatLabelLong(loan.format), loan.year]
    .filter(Boolean)
    .join(" · ");

  // Just the renewal state. No branch (a checkout returns to any branch, so
  // its owning branch is noise) and no call number (shelf-finding jargon for
  // an item you already hold).
  const meta = hint ?? "";

  return (
    <>
      {index > 0 && <div style={rowDividerStyle} />}
      <div style={baseRow}>
        <RecordLink url={loan.url} style={COVER_LINK_STYLE}>
          <CoverImage
            jacket={loan.jacket}
            eager={index < 3}
            format={loan.format}
          />
        </RecordLink>
        <div style={metaStyle}>
          <div style={titleRowStyle}>
            <h3
              style={isDiscFormat(loan.format) ? TITLE_STYLE_CD : TITLE_STYLE}
            >
              <RecordLink url={loan.url}>
                {loan.title ?? "(untitled)"}
              </RecordLink>
            </h3>
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

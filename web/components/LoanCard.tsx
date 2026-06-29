/**
 * One row in the loans list. Mirrors HoldCard structurally but the
 * status pill encodes due-date urgency instead of queue position.
 *
 * Data shape mirrors `bibliocommons_mcp.models.Loan`.
 */
import {
  badgeStyle,
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
import { formatLabel } from "../lib/format.js";
import type { Jacket } from "../lib/jacket.js";
import { STATUS_ACTIVE } from "../lib/palette.js";

export type Loan = {
  checkout_id: string;
  metadata_id?: string | null;
  title?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  format?: string | null;
  due?: string | null;
  call_number?: string | null;
  branch?: string | null;
  jacket?: Jacket | null;
  actions?: string[];
  times_renewed?: number;
};

const LOAN_TITLE_STYLE = titleStyle(3);

function dueText(loan: Loan): string {
  // Bucket into overdue / due-soon / normal relative to "today" (UTC
  // midnight is fine — we're not chasing minute-level accuracy). The pill
  // color is a single blue now; the text carries the urgency.
  const iso = loan.due;
  if (!iso) return "no due date";
  const dueDate = new Date(iso + "T00:00:00Z");
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const dayMs = 24 * 60 * 60 * 1000;
  const days = Math.round((dueDate.getTime() - today.getTime()) / dayMs);
  const shortDate = formatMonthDay(iso) ?? "";

  if (days < 0) return `overdue · ${shortDate}`;
  if (days <= 3) {
    const when =
      days === 0 ? "today" : days === 1 ? "tomorrow" : `in ${days} days`;
    return `due ${when} · ${shortDate}`;
  }
  return `due ${shortDate}`;
}

function renewalHint(loan: Loan): string | null {
  const actions = loan.actions ?? [];
  if (actions.includes("renew")) {
    const n = loan.times_renewed ?? 0;
    if (n > 0) return `Renewable · ${n}× renewed`;
    return "Renewable";
  }
  // The format badge already conveys digital, so don't repeat it here.
  if (actions.includes("checkIn")) return "Return only";
  return null;
}

export function LoanCard({ loan, index }: { loan: Loan; index: number }) {
  const format = formatLabel(loan.format);
  const material = loan.material_type === "DIGITAL" ? "Digital" : "Physical";
  const hint = renewalHint(loan);

  return (
    <div style={index === 0 ? firstRowStyle : rowStyle}>
      <CoverImage jacket={loan.jacket} format={loan.format} eager={index < 3} />
      <div style={metaStyle}>
        <h3 style={LOAN_TITLE_STYLE}>{loan.title ?? "(untitled)"}</h3>
        <div style={pillRowStyle}>
          <span
            style={{ ...pillStyle, color: "white", background: STATUS_ACTIVE }}
          >
            {dueText(loan)}
          </span>
          {format ? (
            <span style={badgeStyle}>{format}</span>
          ) : (
            <span style={lineStyle}>{material}</span>
          )}
          {loan.branch && <span style={lineStyle}>{loan.branch}</span>}
        </div>
        {(loan.call_number || hint) && (
          <p style={lineStyle}>
            {loan.call_number ?? ""}
            {loan.call_number && hint ? " · " : ""}
            {hint ?? ""}
          </p>
        )}
      </div>
    </div>
  );
}

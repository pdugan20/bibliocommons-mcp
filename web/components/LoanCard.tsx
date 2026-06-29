/**
 * One row in the loans list. Mirrors HoldCard structurally but the
 * status pill encodes due-date urgency instead of queue position.
 *
 * Data shape mirrors `bibliocommons_mcp.models.Loan`.
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
import {
  STATUS_DUE_SOON,
  STATUS_OVERDUE,
  STATUS_QUEUED,
} from "../lib/palette.js";

export type Loan = {
  checkout_id: string;
  metadata_id?: string | null;
  title?: string | null;
  material_type?: "PHYSICAL" | "DIGITAL" | null;
  due?: string | null;
  call_number?: string | null;
  branch?: string | null;
  jacket?: Jacket | null;
  actions?: string[];
  times_renewed?: number;
};

const LOAN_TITLE_STYLE = titleStyle(3);

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
  const shortDate = formatMonthDay(iso) ?? "";

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
  return { text: `due ${shortDate}`, color: "white", bg: STATUS_QUEUED };
}

function renewalHint(loan: Loan): string | null {
  const actions = loan.actions ?? [];
  if (actions.includes("renew")) {
    const n = loan.times_renewed ?? 0;
    if (n > 0) return `Renewable · ${n}× renewed`;
    return "Renewable";
  }
  // "Digital" already shows in the pill row, so don't repeat it here.
  if (actions.includes("checkIn")) return "Return only";
  return null;
}

export function LoanCard({ loan, index }: { loan: Loan; index: number }) {
  const due = dueForRender(loan);
  const material = loan.material_type === "DIGITAL" ? "Digital" : "Physical";
  const hint = renewalHint(loan);

  return (
    <div style={index === 0 ? firstRowStyle : rowStyle}>
      <CoverImage jacket={loan.jacket} eager={index < 3} />
      <div style={metaStyle}>
        <h3 style={LOAN_TITLE_STYLE}>{loan.title ?? "(untitled)"}</h3>
        <div style={pillRowStyle}>
          <span style={{ ...pillStyle, color: due.color, background: due.bg }}>
            {due.text}
          </span>
          <span style={lineStyle}>{material}</span>
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

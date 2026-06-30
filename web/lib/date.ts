/**
 * Format a gateway YYYY-MM-DD string as "May 27" / "Jan 4" without pulling
 * in a date library. Shared by HoldCard ("Placed …") and LoanCard (due
 * dates), which each had their own copy.
 */
const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export function formatMonthDay(iso?: string | null): string | null {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  const month = MONTHS[Number.parseInt(m[2], 10) - 1] ?? m[2];
  const day = Number.parseInt(m[3], 10);
  return `${month} ${day}`;
}

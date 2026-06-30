/**
 * Cover-art URLs as the BC gateway returns them (briefInfo.jacket). Shared
 * across BibSummary / Hold / Loan so the three cards and their fixtures
 * agree on one shape. Mirrors `bibliocommons_mcp.models.Jacket`.
 */
export type Jacket = {
  small?: string | null;
  medium?: string | null;
  large?: string | null;
  local_url?: string | null;
};

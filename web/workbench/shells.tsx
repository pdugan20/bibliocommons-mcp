/**
 * Dev-only re-export. The app shells used to live here; they're now the
 * shared HoldsView/LoansView/SearchView in lib/views (used by both the
 * real bundle entries and the workbench), so the gallery and scenarios
 * pages import them under their old names from here.
 */
export {
  HoldsView as HoldsShell,
  LoansView as LoansShell,
  SearchView as SearchShell,
} from "../lib/views.js";

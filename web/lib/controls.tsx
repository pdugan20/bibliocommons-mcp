/**
 * Switchable filter-pill and footer-CTA styles. Like the header lockup,
 * the exact treatment is still being chosen, so the candidates live here
 * behind contexts the dev workbench can flip; CardFrame reads them.
 */
import { createContext, type CSSProperties } from "react";

const BLUE = "#0f6dbf";
const LINK = "light-dark(#0b5da6, #9ccbf0)";
const reset: CSSProperties = {
  appearance: "none",
  fontFamily: "inherit",
  cursor: "pointer",
  color: "inherit",
};

// ---------- Filter pills ----------
export type FilterStyleId = "outlined" | "segmented" | "underline" | "tonal";
export const FILTER_STYLE_IDS: FilterStyleId[] = [
  "outlined",
  "segmented",
  "underline",
  "tonal",
];
export const FILTER_STYLE_NOTES: Record<FilterStyleId, string> = {
  outlined: "Outlined",
  segmented: "Segmented",
  underline: "Underline",
  tonal: "Tonal",
};
export const DEFAULT_FILTER_STYLE: FilterStyleId = "outlined";
export const FilterStyleContext =
  createContext<FilterStyleId>(DEFAULT_FILTER_STYLE);

export function filterStyles(id: FilterStyleId): {
  wrap: CSSProperties;
  base: CSSProperties;
  active: CSSProperties;
} {
  switch (id) {
    case "segmented":
      return {
        wrap: {
          display: "inline-flex",
          background: "light-dark(rgba(0,0,0,0.05), rgba(255,255,255,0.07))",
          borderRadius: 9,
          padding: 3,
          gap: 2,
        },
        base: {
          ...reset,
          border: "none",
          background: "transparent",
          borderRadius: 6,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
          opacity: 0.7,
        },
        active: {
          ...reset,
          border: "none",
          background: "light-dark(#fff, rgba(255,255,255,0.16))",
          borderRadius: 6,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
          boxShadow: "0 1px 2px rgba(0,0,0,0.12)",
        },
      };
    case "underline":
      return {
        wrap: { display: "flex", gap: 16, flexWrap: "wrap" },
        base: {
          ...reset,
          border: "none",
          background: "none",
          padding: "2px 0 5px",
          fontSize: 13,
          fontWeight: 600,
          opacity: 0.55,
          borderBottom: "2px solid transparent",
        },
        active: {
          ...reset,
          border: "none",
          background: "none",
          padding: "2px 0 5px",
          fontSize: 13,
          fontWeight: 700,
          color: BLUE,
          borderBottom: `2px solid ${BLUE}`,
        },
      };
    case "tonal":
      return {
        wrap: { display: "flex", gap: 6, flexWrap: "wrap" },
        base: {
          ...reset,
          border: "none",
          background: "light-dark(rgba(0,0,0,0.06), rgba(255,255,255,0.10))",
          borderRadius: 999,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
        },
        active: {
          ...reset,
          border: "none",
          background:
            "light-dark(rgba(15,109,191,0.14), rgba(77,159,232,0.22))",
          color: "light-dark(#0b5da6, #9ccbf0)",
          borderRadius: 999,
          padding: "4px 12px",
          fontSize: 12,
          fontWeight: 600,
        },
      };
    case "outlined":
    default:
      return {
        wrap: { display: "flex", gap: 6, flexWrap: "wrap" },
        base: {
          ...reset,
          border: "1px solid light-dark(#dcdcd7, #3a3a38)",
          background: "transparent",
          borderRadius: 999,
          padding: "3px 11px",
          fontSize: 12,
          fontWeight: 500,
        },
        active: {
          ...reset,
          border: "1px solid transparent",
          background: BLUE,
          color: "#fff",
          borderRadius: 999,
          padding: "3px 11px",
          fontSize: 12,
          fontWeight: 600,
        },
      };
  }
}

// ---------- Footer CTA ----------
export type CtaStyleId =
  | "link"
  | "outlined"
  | "filled"
  | "tonal"
  | "fullFilled"
  | "fullOutlined"
  | "fullTonal";
export const CTA_STYLE_IDS: CtaStyleId[] = [
  "link",
  "outlined",
  "filled",
  "tonal",
  "fullFilled",
  "fullOutlined",
  "fullTonal",
];
export const CTA_STYLE_NOTES: Record<CtaStyleId, string> = {
  link: "Link",
  outlined: "Outlined",
  filled: "Filled",
  tonal: "Tonal",
  fullFilled: "Full filled",
  fullOutlined: "Full outlined",
  fullTonal: "Full tonal",
};
export const DEFAULT_CTA_STYLE: CtaStyleId = "link";
export const CtaStyleContext = createContext<CtaStyleId>(DEFAULT_CTA_STYLE);

const fullBase: CSSProperties = {
  display: "block",
  textAlign: "center",
  width: "100%",
  boxSizing: "border-box",
  borderRadius: 8,
  textDecoration: "none",
};

export function ctaStyle(id: CtaStyleId): {
  style: CSSProperties;
  arrow: boolean;
  /** Full-width: render under the content with no top divider. */
  full?: boolean;
} {
  switch (id) {
    case "fullFilled":
      return {
        style: {
          ...fullBase,
          border: "none",
          background: BLUE,
          color: "#fff",
          padding: "11px 16px",
          fontWeight: 600,
        },
        arrow: false,
        full: true,
      };
    case "fullOutlined":
      return {
        style: {
          ...fullBase,
          border: "1px solid light-dark(#cdd6df, #3a4654)",
          background: "transparent",
          color: LINK,
          padding: "10px 16px",
          fontWeight: 600,
        },
        arrow: false,
        full: true,
      };
    case "fullTonal":
      return {
        style: {
          ...fullBase,
          border: "none",
          background:
            "light-dark(rgba(15,109,191,0.12), rgba(77,159,232,0.22))",
          color: LINK,
          padding: "11px 16px",
          fontWeight: 700,
        },
        arrow: true,
        full: true,
      };
    case "outlined":
      return {
        style: {
          border: "1px solid light-dark(#cdd6df, #3a4654)",
          background: "transparent",
          color: LINK,
          borderRadius: 8,
          padding: "7px 14px",
          fontWeight: 600,
          textDecoration: "none",
        },
        arrow: false,
      };
    case "filled":
      return {
        style: {
          border: "none",
          background: BLUE,
          color: "#fff",
          borderRadius: 8,
          padding: "8px 16px",
          fontWeight: 600,
          textDecoration: "none",
        },
        arrow: false,
      };
    case "tonal":
      return {
        style: {
          border: "none",
          background:
            "light-dark(rgba(15,109,191,0.12), rgba(77,159,232,0.22))",
          color: LINK,
          borderRadius: 8,
          padding: "8px 16px",
          fontWeight: 700,
          textDecoration: "none",
        },
        arrow: true,
      };
    case "link":
    default:
      return {
        style: { color: LINK, textDecoration: "none", fontWeight: 600 },
        arrow: true,
      };
  }
}

/**
 * Consistent card header: a library-name + title lockup. The exact
 * typographic treatment is still being chosen, so the six candidate
 * lockups live here behind a context the dev workbench can switch; the
 * shipped default is whatever DEFAULT_HEADER_VARIANT points at.
 */
import { createContext, useContext, type CSSProperties } from "react";

export type HeaderVariant = "A" | "B" | "C" | "D" | "E" | "F" | "G";

export const HEADER_VARIANTS: HeaderVariant[] = [
  "A",
  "B",
  "C",
  "D",
  "E",
  "F",
  "G",
];

export const HEADER_VARIANT_NOTES: Record<HeaderVariant, string> = {
  A: "Uppercase eyebrow above (current)",
  B: "Title first, library below",
  C: "Quiet eyebrow above (normal case)",
  D: "Title-dominant",
  E: "Library-forward",
  F: "One line",
  G: "One line, library right-aligned",
};

export const DEFAULT_HEADER_VARIANT: HeaderVariant = "C";

export const HeaderVariantContext = createContext<HeaderVariant>(
  DEFAULT_HEADER_VARIANT,
);

const lib = (s: CSSProperties): CSSProperties => ({
  margin: 0,
  opacity: 0.5,
  ...s,
});
const ttl = (s: CSSProperties): CSSProperties => ({ margin: 0, ...s });

export function HeaderLockup({
  variant,
  library,
  title,
}: {
  variant: HeaderVariant;
  library?: string | null;
  title: string;
}) {
  if (!library) {
    return (
      <header>
        <h2 style={ttl({ fontSize: 16, fontWeight: 700 })}>{title}</h2>
      </header>
    );
  }

  switch (variant) {
    case "B":
      return (
        <header>
          <h2 style={ttl({ fontSize: 17, fontWeight: 700 })}>{title}</h2>
          <p
            style={lib({
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: 0.4,
              textTransform: "uppercase",
              marginTop: 3,
            })}
          >
            {library}
          </p>
        </header>
      );
    case "C":
      return (
        <header>
          <p style={lib({ fontSize: 12.5, fontWeight: 500, opacity: 0.55 })}>
            {library}
          </p>
          <h2 style={ttl({ fontSize: 17, fontWeight: 700, marginTop: 1 })}>
            {title}
          </h2>
        </header>
      );
    case "D":
      return (
        <header>
          <h2
            style={ttl({ fontSize: 19, fontWeight: 800, letterSpacing: -0.3 })}
          >
            {title}
          </h2>
          <p
            style={lib({
              fontSize: 10.5,
              fontWeight: 600,
              letterSpacing: 0.8,
              textTransform: "uppercase",
              marginTop: 4,
              opacity: 0.45,
            })}
          >
            {library}
          </p>
        </header>
      );
    case "E":
      return (
        <header>
          <p
            style={lib({
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: 0.3,
              textTransform: "uppercase",
              opacity: 0.7,
            })}
          >
            {library}
          </p>
          <h2
            style={ttl({
              fontSize: 14,
              fontWeight: 600,
              marginTop: 3,
              opacity: 0.9,
            })}
          >
            {title}
          </h2>
        </header>
      );
    case "F":
      return (
        <header
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          <h2 style={ttl({ fontSize: 17, fontWeight: 700 })}>{title}</h2>
          <span style={lib({ fontSize: 12, fontWeight: 500, opacity: 0.5 })}>
            · {library}
          </span>
        </header>
      );
    case "G":
      return (
        <header
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
            gap: 8,
          }}
        >
          <h2 style={ttl({ fontSize: 17, fontWeight: 700 })}>{title}</h2>
          <span style={lib({ fontSize: 12, fontWeight: 500, opacity: 0.5 })}>
            {library}
          </span>
        </header>
      );
    case "A":
    default:
      return (
        <header>
          <p
            style={lib({
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: 0.4,
              textTransform: "uppercase",
            })}
          >
            {library}
          </p>
          <h2 style={ttl({ fontSize: 16, fontWeight: 700, marginTop: 2 })}>
            {title}
          </h2>
        </header>
      );
  }
}

export function CardHeader({
  library,
  title,
}: {
  library?: string | null;
  title: string;
}) {
  const variant = useContext(HeaderVariantContext);
  return <HeaderLockup variant={variant} library={library} title={title} />;
}

/**
 * Consistent card header: a muted library-name eyebrow over a title, used
 * by all three cards so "Your holds", "Your checkouts", and the search
 * result summary read as one family (instead of the old "Holds (3)").
 */
import type { CSSProperties } from "react";

const eyebrowStyle: CSSProperties = {
  margin: 0,
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: 0.4,
  textTransform: "uppercase",
  opacity: 0.5,
};

const titleStyle: CSSProperties = {
  margin: "2px 0 0",
  fontSize: 16,
  fontWeight: 700,
  letterSpacing: -0.1,
};

export function CardHeader({
  library,
  title,
}: {
  library?: string | null;
  title: string;
}) {
  return (
    <header>
      {library && <p style={eyebrowStyle}>{library}</p>}
      <h2 style={titleStyle}>{title}</h2>
    </header>
  );
}

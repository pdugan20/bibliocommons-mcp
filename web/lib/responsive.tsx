/**
 * Responsive design tokens for the cards, as CSS custom properties driven
 * by a media query. The cards are otherwise styled with inline styles
 * (which can't hold `@media`), so we render one <style> tag that sets the
 * vars and shrinks them on a narrow viewport — and the inline styles read
 * `var(--bc-…)`. In-product the bundle's iframe viewport width *is* the
 * card width, so `max-width: 360px` fires on a narrow iOS chat bubble; the
 * workbench's 320px "iPhone" preset exercises the same path.
 *
 * Render <ResponsiveStyles /> once per app (and once in the gallery).
 */
export function ResponsiveStyles() {
  return (
    <style>
      {[
        ":root{--bc-pad-x:20px;--bc-cover-w:64px;--bc-cover-h:88px}",
        "@media (max-width:360px){:root{--bc-pad-x:14px;--bc-cover-w:54px;--bc-cover-h:74px}}",
      ].join("")}
    </style>
  );
}

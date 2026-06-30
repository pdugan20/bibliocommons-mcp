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
        ":root{--bc-pad-x:20px;--bc-cover-w:64px;--bc-cover-h:88px;--bc-cd-title-lines:2}",
        "@media (max-width:360px){:root{--bc-pad-x:14px;--bc-cover-w:54px;--bc-cover-h:74px}}",
        // Square CD covers are short, so cap their (only) title to one line
        // on a narrow viewport so it doesn't tower over the cover. 400px to
        // also catch the 380px "Mobile" preset, not just the 320px iPhone.
        "@media (max-width:400px){:root{--bc-cd-title-lines:1}}",
      ].join("")}
    </style>
  );
}

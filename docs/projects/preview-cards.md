# Project: Preview cards (inline UI bundles)

## Goal

When the user asks "show me my holds" or "what's available?", the MCP client renders an inline card per item — cover art + title + author + status — instead of (or alongside) the JSON. Like the iPod-capacity widget clickwheel ships, or the album/article cards rewind ships.

## Why

Library content is visual. Cover art is the difference between scanning a list and recognizing an item at a glance. The MCP Apps extension (`io.modelcontextprotocol/ui`) is the right mechanism, and BiblioCommons already gives us the images.

## What the BC API gives us

`briefInfo.jacket` is structured and consistent across libraries:

```json
{
  "type": "SYNDETICS",
  "small": "https://secure.syndetics.com/index.aspx?isbn=.../SC.GIF&client=sepup&type=xw12&oclc=&upc=...",
  "medium": "https://secure.syndetics.com/index.aspx?isbn=.../MC.GIF&...",
  "large": "https://secure.syndetics.com/index.aspx?isbn=.../LC.JPG&...",
  "local_url": null
}
```

`local_url` is sometimes populated when the library has uploaded its own cover. Per-library `client=` query param identifies the calling system.

That means we already have everything for `BibSummary` / `Hold` / `Loan` cards.

## Approach

This is the largest of the project briefs — split into three milestones.

### Milestone 1 — wire jacket URLs into models (~30m)

1. Add `jacket: Jacket | None` field to `BibSummary` and to `Hold` / `Loan` where bib data is denormalised in.
2. Extract during model construction in `server.py`.
3. Smoke-test that VCR cassettes include the field correctly.

This alone is useful: even without a UI bundle, MCP clients that can render markdown will show the image inline via `![title](url)` if the agent decides to.

### Milestone 2 — workbench scaffolding (~2–3h)

Mirror the clickwheel pattern:

- `web/` directory at the repo root with Vite + a small UI framework (React, Preact, or vanilla — see open question).
- `web/components/` with one component per card type: `HoldCard`, `LoanCard`, `BibCard`, `BranchCard`.
- `web/scripts/inline_bundles.mjs` — Vite build → emits `src/bibliocommons_mcp/_ui_bundles.py` (auto-generated, ruff-excluded, gitignored from format but committed so `pip install` works without a Node toolchain).
- `Makefile`: `make build-web` runs the Vite build.
- CI job `web-bundle` rebuilds and fails if the committed bundle drifts (like clickwheel's check).
- Set up `npm run dev` for local component iteration.

This is the **workbench** — a self-contained dev environment for iterating on cards without restarting the MCP server.

### Milestone 3 — MCP Apps wiring (~2h)

- `src/bibliocommons_mcp/ui.py`: register the `io.modelcontextprotocol/ui` extension. Mirror clickwheel's `enable_mcp_apps(mcp)` pattern.
- `src/bibliocommons_mcp/ui_resources.py`: register `ui://` resources for each card type.
- Annotate tools with `meta=ui_tool_meta(...)`. Concrete first pass:
  - `list_holds` → `ui://bibliocommons-mcp/holds.html`
  - `list_loans` → `ui://bibliocommons-mcp/loans.html`
  - `search` → `ui://bibliocommons-mcp/search-results.html`
  - `availability` → `ui://bibliocommons-mcp/availability.html`

- Test in Claude Desktop (the client with the best MCP Apps support today).

### Milestone 4 — polish + responsive (optional, ~1–2h)

- Tap-to-expand: click a card to see full bib metadata.
- Status-aware visual treatment: pickup-ready holds get a green ring, expired holds get strikethrough.
- Mobile-friendly layout (Claude Desktop on iOS).

## Effort

**~6–8h total** for milestones 1–3 (the visible feature). Milestone 4 is optional polish.

Cost is front-loaded — the workbench is reusable for every future card design.

## Open questions

- **Framework choice.** Clickwheel uses React + Vite. Rewind likely the same. We could go simpler — vanilla JS / Lit / Preact — since cards are stateless. Lean **vanilla + small Vite config** for v1; if the cards grow stateful (filtering, sorting, expanding), upgrade to Preact.
- **Bundle size.** Clickwheel's `_ui_bundles.py` is ~1.7MB inlined. Our cards are simpler; aim for <500KB total.
- **Image performance.** Syndetics URLs hotlink directly — fine for one or two cards, but a "20 holds" view could be slow if all images load eagerly. Lazy-load past the first 3.
- **Self-test for the workbench.** Clickwheel's CI checks bundle freshness via git diff; we'd want the same. What's the minimum unit test for "card renders with the data shape we expect"?
- **Client fallback.** Clients without MCP Apps support get text-only — that's already what we have. No regression.

## Dependencies / blockers

- A working `web/` workbench is a significant scope expansion. Decide whether the project wants to take on a Node toolchain before starting.
- Milestone 1 is independent and can ship without 2–4 (people who like the JSON shape get a `jacket` URL they can use however).

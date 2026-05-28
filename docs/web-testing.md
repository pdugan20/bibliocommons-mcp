# Web bundle test plan

How to manually verify the React UI bundles (`web/holds.tsx`, `loans.tsx`,
`search.tsx`) and the workbench that drives them. Covers local
iteration, CI guarantees, and the production end-to-end path through a
UI-capable MCP host.

Run this top-to-bottom after any change under `web/` that isn't a
trivial style tweak. The whole thing takes 10–15 minutes.

## 0. Preconditions

```bash
node --version   # must be 22 (matches web/.nvmrc)
cd web && npm ci  # exact lockfile install
```

## 1. Workbench boots and lists all bundles

```bash
make dev-web
```

Expected:

- Vite prints `Local: http://localhost:5174/workbench/` and opens
  that URL automatically.
- Sidebar shows three bundles in this order: **Holds**, **Checkouts**,
  **Search results**.
- Header shows two toggle groups: **Viewport** (Mobile / Tablet /
  Desktop, default Desktop) and **Theme** (Light / Dark, defaulting
  to the OS preference).
- The currently-selected bundle's first fixture is rendered in the
  main iframe within ~1s.
- Status footer in the sidebar reads `status: pushed-result`.

Fail conditions: Vite errors on launch; bundles missing from the
sidebar; status stuck on `mounting` or `awaiting-initialize` (means
the postMessage handshake broke — open the browser DevTools console
and look for `[workbench]` debug log lines to see which step stalled).

## 2. Per-bundle fixture coverage

For each bundle, click each fixture in the sidebar and verify it
renders the documented shape. The fixture's `name` is what's visible
in the sidebar; the `description` (if present) explains what the
visual should look like.

### Holds bundle

| Fixture                       | What to verify                                                                                  |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `Mixed queue (typical)`       | 4 cards, mix of ready/queued/in-transit/expired statuses, all status pills colored correctly    |
| `Empty (no holds)`            | Single "No holds" empty state, no broken layout                                                 |
| `Single ready for pickup`     | One card, green "READY" pill, branch name shown                                                 |
| `Long title without jacket`   | 3-line clamp on the title kicks in; placeholder cover background shows where the image would be |
| `In transit to pickup branch` | Blue "IN TRANSIT" pill, position field hidden (it's not relevant in this state)                 |

### Checkouts bundle

| Fixture                                     | What to verify                                                                                             |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `Mixed urgency (typical)`                   | 3 cards: one red overdue pill, one amber due-soon pill, one blue normal pill. Date math relative to today. |
| `Empty (no loans)`                          | Empty state renders cleanly                                                                                |
| `Due today`                                 | Pill reads "due today · {Mon Day}" in amber                                                                |
| `Physical with branch + call number`        | Branch code + call number both visible, no "Renewable" hint (this fixture predates the actions field)      |
| `Renewable physical (already renewed once)` | Hint line reads "Renewable · 1× renewed"                                                                   |

### Search results bundle

| Fixture                        | What to verify                                                                                                     |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `Mixed format query (typical)` | Pagination summary at top ("Page 1 of N · M results"). Format badges (Book / eBook / CD / Audiobook) on each card. |
| `Empty (no results)`           | "No results" empty state                                                                                           |
| `Single result`                | One card with full metadata; pagination summary still shown but degenerate                                         |
| `Page N of M`                  | Summary correctly shows mid-pagination state                                                                       |
| `No covers (all fallback)`     | Placeholder cover background on every card; layout unaffected                                                      |

## 3. Cross-cutting toggles

With any bundle + fixture loaded:

1. Click **Viewport: Mobile**. The iframe's max-width snaps to 380px.
   Card layout should remain readable — title clamps tighter, cover
   stays at fixed size, branch/call-number lines wrap if needed.
2. Click **Viewport: Tablet** → 600px. **Desktop** → 720px.
3. Toggle **Theme: Dark**. Background, text, and pill colors should
   all flip (CSS `light-dark()` driven). Status pills stay legible
   in both modes (the green/amber/red/blue should be visible against
   the dark card background).
4. Toggle back to **Light**.

The iframe should not remount between toggles — verify by watching
the sidebar status: it should stay at `pushed-result`. (A remount
would briefly flicker through `mounting` → `awaiting-initialize` →
`initialized` → `pushed-result`.)

## 4. HMR

With the workbench running:

1. Open `web/components/HoldCard.tsx` in your editor.
2. Change a visible style — e.g. set `STATUS_QUEUED` in
   `web/lib/palette.ts` to a different hex.
3. Save. The iframe in the workbench should reload within ~1s with
   the new color applied. Sidebar status should briefly show
   `mounting` then return to `pushed-result`.
4. Revert the change.

Fail condition: needing to manually click "reload iframe" or restart
Vite to see the change. That indicates the dev server lost HMR or the
Vite config is misrouting modules.

## 5. MCP Apps handshake (postMessage simulation)

The workbench plays the host side of the `io.modelcontextprotocol/ui`
protocol. Verify each step of the handshake fires in order:

1. Open the browser DevTools console. Filter for `[workbench]`.
2. Click "reload iframe" in the sidebar.
3. Expected log sequence:
   - `[workbench] ← ui/initialize` (the bundle requests host context)
   - `[workbench] ← ui/notifications/initialized` (bundle confirms
     it's ready for tool results)
   - `[workbench] → tool-result <fixture name> {…}` (workbench
     pushes the fixture's structuredContent into the bundle)
4. Sidebar status should end at `pushed-result`.
5. Click a different fixture in the sidebar. A new
   `[workbench] → tool-result` log line should appear immediately —
   no remount, no second `ui/initialize`.
6. Toggle theme. A `[workbench]` line should fire with
   `ui/notifications/host-context-changed` and the bundle's colors
   should update.

Fail condition: any of these messages missing, or status stuck on
`awaiting-initialize` (the bundle never sent `initialized`, which
means the `useApp` hook in the entry file isn't wiring `onAppCreated`
correctly).

## 6. CI bundle-freshness guarantee

The `web-bundles` CI job rebuilds the bundles and diffs
`src/bibliocommons_mcp/_ui_bundles.py`. Verify locally:

```bash
make build-web
git diff src/bibliocommons_mcp/_ui_bundles.py
```

Expected: **no diff** on a clean working tree. If there's a diff, the
committed `_ui_bundles.py` is stale — commit the regenerated file.

Force-test the check (optional):

```bash
# Edit web/components/HoldCard.tsx — change any visible string.
# Don't run make build-web. Push to a branch and open a PR.
# CI should fail the `Web bundle freshness` job with the diff.
```

## 7. Production end-to-end (UI-capable host)

This is the only check that proves the bundle actually renders in a
real client; everything above runs against the workbench's fixture
simulator.

### MCP Inspector path (fastest)

```bash
npx @modelcontextprotocol/inspector bibliocommons-mcp
```

In the Inspector:

1. Connect; verify the server lists 13 tools including the four
   UI-annotated ones (`search`, `list_holds`, `ready_for_pickup`,
   `list_loans`).
2. Verify the server lists three resources under `ui://`:
   `ui://bibliocommons-mcp/holds`, `.../loans`, `.../search`.
3. Call `list_holds()`. The result panel should render the
   structuredContent JSON AND mount the holds bundle inline.
4. Repeat for `list_loans()` and `search(query="grunge")`.

### Claude Desktop path (real-world)

```bash
claude mcp add bibliocommons bibliocommons-mcp --scope user
# restart Claude Desktop
```

Then ask:

> Show my current holds.

Expected: Claude calls `list_holds()` and the response renders as
inline cards (cover + title + status pill), not as raw JSON.

Fail conditions:

- Cards render as JSON text → the host isn't reading the
  `io.modelcontextprotocol/ui` meta. Check `_meta` on the tool
  definition via the Inspector.
- Cards mount but covers don't load → CSP is blocking Syndetics.
  Check the iframe DevTools (Inspector exposes them; Claude
  Desktop hides them) for `Content-Security-Policy` violations.
- Cards mount but data is empty → `structuredContent` schema
  mismatch between the tool's return type and what the bundle's
  fixtures assume. The bundle's `useApp` hook will console-error
  in dev.

## What's intentionally not tested

- **Pixel diffs across themes/viewports.** No screenshot infra.
  Visual regressions are caught by hand during step 2.
- **A11y audit.** The cards use semantic HTML (`<h3>` for titles,
  `alt` text on covers), but no full WCAG pass. Worth doing before
  declaring v1.0.
- **Performance with 50+ items.** Fixtures cap at ~5 items per
  bundle. A real user with 30 holds might hit lazy-load issues with
  Syndetics — not a regression vs. v0.2 (which rendered nothing at
  all), but worth profiling if anyone complains.
- **Failure rendering.** No fixture yet for "tool returned but the
  shape is malformed." The bundles fall back to a minimal "no data"
  state in that case; visual confirmation is on hold until we have
  a real failure to design against.

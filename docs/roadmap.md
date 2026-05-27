# Roadmap

What's planned, what's deliberately deferred, and what's a maybe. None of these dates are hard — this is "what I'd build next if I sat down for an afternoon."

## v1.1 — fill in digital + suspend

- **Digital queue holds.** `place_digital_hold(bib_id)` — currently the gateway 500s on a partial body shape. The blocker is a `format` enum field in `materialParams`. We have the full `DigitalFormatType` enum from a Jackson type-mismatch probe (see [`format-codes.md`](format-codes.md)) but haven't captured a successful real-browser POST for the join-waitlist path. One DevTools network capture from someone with an unavailable digital item on an SPL account would close this.
- **Suspend / unsuspend holds.** The actions array on existing holds includes `suspend`, but the endpoint shape isn't probed yet. Should be a sibling of `cancel_hold` (likely PUT or PATCH on `/holds/{id}`).
- **Pickup-branch update on existing holds.** Bundle code references `UPDATE_PICKUP_LOCATION` — useful when you want to change pickup mid-queue.

## v1.2 — Loans

- **Renew loans.** Distinct endpoint, untested. Most-asked-for missing feature once people start using this in earnest.
- **Mark "ready for pickup" notifications.** The holds list exposes status transitions — surface them as a tool that filters.

## v2.x — bigger swings

- **Multi-library mode.** Today, one MCP server instance speaks to one library. Multi-card households would benefit from a `library` argument on each tool, with config defining the default. Trade-off: per-library session caching gets more complex.
- **Better recommendations.** The catalog response includes `recommendations` and `userContent` entities we ignore. A `recommend(bib_id)` tool that cross-references your loans/holds with similar items would be a natural fit for AI clients.
- **Search-only mode (no credentials).** Most read-only catalog endpoints work unauthenticated. A `read_only` config flag would let users explore a library's catalog without giving the server a PIN. (Searches the same way the public catalog UI does.)

## Explicit non-goals

- **Account creation / sign-up flows.** This server assumes you already have a card.
- **Library staff features.** No catalog editing, item creation, etc.
- **Caching layer.** Branch lists are cached in-memory per process; everything else is live. No SQLite, no Redis. If you need persistence, run two instances behind a thin cache yourself.
- **GUI.** It's MCP. Use a client.

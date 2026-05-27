# Project: Ready-for-pickup tool

## Goal

Surface holds that have arrived at the user's pickup branch as a dedicated MCP tool, so the agent can answer "what's waiting for me at the library" without filtering `list_holds` client-side.

## Why

The current `list_holds` returns everything — pending queue positions, ready-for-pickup, expired. Users almost always want the subset that has arrived. Filtering server-side is one less thing the model has to figure out.

It's also a low-risk way to bake **status-aware tools** into the design, which v1.2's renew + suspend work will rely on.

## Approach

1. **Data is already there.** `list_holds` returns `status` strings; `"READY_FOR_PICKUP"` is the value we want. We're just filtering.

2. **Two design choices** — pick one:
   - **a)** Add `status_filter: list[str] | None = None` to `list_holds`. Single tool, more flexible. Best if other status filters become common (`NOT_YET_AVAILABLE`, `IN_TRANSIT`, etc.).
   - **b)** New tool `ready_for_pickup() -> HoldList`. Two tools, but the name reads naturally in an agent prompt.

   Lean **b** — it surfaces in the tools list as a discoverable verb. Composes with `list_holds` for the general case.

3. **Add an `expires_at` field** to the `Hold` model if not already there — pickup-ready holds have a short window (typically 7–10 days) before they go back into circulation.

4. **Surface arrival date** if available in the BC response (`statusChangedDate` or similar). Spike to confirm shape.

5. **Server instructions** — add a one-liner: "use `ready_for_pickup()` when the user asks 'what's at the library waiting for me?' or similar."

## Effort

~45m. Mostly tool wiring + a model field addition + 2–3 unit tests with mocked holds.

## Open questions

- Does the BC response actually populate a pickup-expiry / status-changed date, or do we synthesize it from `holdsPosition == 0` + the user's branch policy (typically 7 days)?
- Does the `IN_TRANSIT` status warrant its own surfacing (between "ordered from another branch" and "ready"), or is it noise?

## Dependencies / blockers

None. Can ship anytime.

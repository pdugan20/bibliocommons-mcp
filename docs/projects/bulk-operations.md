# Project: Bulk hold operations

> **Status: shipped** in the v0.4.0 "collapse mutation tools to
> list-accepting only" refactor. Both halves landed, and the design
> question below resolved toward **one list-accepting tool each** (not
> separate singular/plural tools):
>
> - **Cancel** — `cancel_hold(holds: list[HoldRef], dry_run=False)`,
>   single native bulk `DELETE`; `dry_run` previews. Partial failures
>   surface in `BulkCancelHoldsResult`.
> - **Place (physical)** — `place_hold(bib_ids: list[str],
pickup_branch=None, delay_seconds=1.0) -> BulkPlaceHoldResult`; N
>   sequential POSTs with the polite delay baked in as a parameter.
> - **Place (digital queue)** — `place_digital_hold(bib_ids: list[str],
delay_seconds=1.0)` joins Libby waitlists, same shape.
>
> See `src/bibliocommons_mcp/server.py`. The only deferred piece is
> richer renewal-style error classification, tracked in
> [`renew-loans.md`](renew-loans.md).

## Goal

Expose bulk cancel and bulk place-hold as first-class MCP tools (or arguments on the existing tools), so the agent can do "cancel all my holds at the central branch" or "place a hold on these five CDs" in one call.

## Why

Cancel-bulk is already the gateway's native shape — we just expose it single-item. Place-bulk is N gateway calls but the MCP-side ergonomics matter: an agent doing five sequential `place_hold` calls is slow and easy to interrupt.

## Approach

### Cancel (the easy half)

The gateway's `DELETE /holds` already accepts arrays:

```http
DELETE /v2/libraries/{lib}/holds?locale=en-US
{
  "accountId": <int>,
  "metadataIds": ["S30C...", "S30C..."],
  "holdIds": ["H1", "H2"],
  "errorMessageLocale": "en-US"
}
```

`Client.cancel_holds(...)` already takes a list internally. The MCP tool just needs to accept lists:

1. Change `cancel_hold(hold_id, bib_id)` → `cancel_hold(hold_id, bib_id)` and `cancel_holds(holds: list[tuple[str, str]])`. Or accept either shape on one tool.
2. Decide on partial-failure semantics — gateway returns a `failures` map keyed by hold id. Reflect that in `CancelHoldResult`.
3. `dry_run` already exists on the single-item path; extend to bulk so "cancel everything ready-for-pickup that I won't make it to the library for" is safe to plan first.

**Effort: ~45m.**

### Place (the harder half)

No gateway batch endpoint — bulk means N sequential POSTs. Considerations:

1. **Failure modes get messy.** Some succeed, some fail with 409 (already on holds), some fail with 500 (gateway hiccup). Need a clear partial-success result type:

   ```python
   class BulkPlaceHoldResult(BaseModel):
       placed: list[PlaceHoldResult]
       failed: dict[str, str]  # bib_id → reason
   ```

2. **Rate limiting matters more.** Five rapid POSTs is plausible. Twenty might trip something on BC's side. Default to a small per-call delay; document as opt-out.

3. **Same pickup branch for all?** Most natural API: single `pickup_branch` argument applied to every bib. Per-bib branches add complexity for marginal value.

4. **Server instructions update** — guide the model toward bulk when the user has a list, single when one item.

**Effort: ~1.5h** with thoughtful error handling + tests.

## Open questions

- Should `cancel_hold` and `cancel_holds` be one tool with a union-typed argument, or two tools? Lean **two tools** — discoverability matters, and the model picks the right one from the action verb.
- For bulk place: do we expose the per-call delay as a tool parameter, or just bake in a sensible default?
- Is "cancel everything not yet available" worth its own helper, or trust the agent to call `list_holds` → filter → `cancel_holds`?

## Dependencies / blockers

- Cancel-bulk: nothing.
- Place-bulk: best after [renew-loans](renew-loans.md) ships, since the partial-failure result type pattern carries over.

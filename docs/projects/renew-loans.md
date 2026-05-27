# Project: Renew loans

## Goal

A `renew_loan(checkout_id)` MCP tool that extends the due date on a physical or digital checkout the user currently has out.

## Why

Most-requested missing feature once anyone uses this tool in earnest. The user is going to ask "renew everything that's due this week" the first time they have something due they're not done with.

## Approach

1. **Spike the endpoint.** Browser DevTools capture: log into SPL, click "Renew" on any current loan, capture the resulting POST/PUT. Likely shape:

   ```http
   PUT|POST https://gateway.bibliocommons.com/v2/libraries/{lib}/checkouts/{checkout_id}/renew?locale=en-US
   {
     "accountId": <int>,
     "errorMessageLocale": "en-US"
   }
   ```

   The `errorMessageLocale` quirk almost certainly applies here too (see `architecture.md`).

2. **Probe error cases.** What does the gateway return for:
   - "max renewals reached"
   - "someone else has a hold so renewal is blocked"
   - "not yet renewable" (some libraries only allow renewal in the last 3 days)

   These should become typed `BCError` classifications or a structured `RenewLoanResult` model.

3. **Add to `Client`** — `client.renew_loan(checkout_id) -> dict`.

4. **Add `renew_loan` MCP tool** with `MUTATION` annotation. Return type:

   ```python
   class RenewLoanResult(BaseModel):
       success: bool
       new_due_date: str | None
       renewals_remaining: int | None
       reason: str | None  # populated when success=False
   ```

5. **Bulk variant** — `renew_loans(checkout_ids: list[str]) -> dict[str, RenewLoanResult]`. The gateway might support this natively; otherwise N×1 calls.

6. **Server instructions update** — add a line under "Common workflows" so the model knows when to suggest it ("when something's due back soon and not finished, ask if user wants to renew before nudging them to return it").

## Effort

~2h end-to-end if the browser capture is clean. Most of the time is in the typed error cases — there are at least 3–4 distinct rejection reasons to distinguish.

## Open questions

- Is the renewal endpoint a `PUT` to a per-checkout URL, or a `POST` to a bulk-shaped URL? Spike will answer.
- For DIGITAL items (OverDrive), do renewals work the same way, or do they go through a separate Libby-side flow? Spike against an active e-book loan.
- Does the response include the new due date directly, or only a success flag (forcing a follow-up `list_loans`)?
- Does the gateway distinguish "blocked by hold queue" cleanly enough that we can surface a useful message?

## Dependencies / blockers

- Active loans on the user's account for the spike (read-only probing isn't enough — we need to capture a real renewal POST).
- Decision on whether the bulk variant is v1.2 or split into v1.3.

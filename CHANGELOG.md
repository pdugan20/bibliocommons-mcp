# Changelog

## [1.0.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.3.0...v1.0.0) (2026-05-28)


### ⚠ BREAKING CHANGES

* All mutation tools now accept lists. Callers using `place_hold(bib_id="X")` must update to `place_hold(bib_ids=["X"])`. Singular variants (place_hold, cancel_hold, renew_loan, check_in_loan, borrow_digital, place_digital_hold) and their result types (CancelHoldResult, CheckInLoanResult, RenewLoanResult) are removed in favor of the new list-accepting forms. Triggers v0.4.0 via release-please.

### Code Refactoring

* collapse mutation tools to list-accepting only ([bcb8a79](https://github.com/pdugan20/bibliocommons-mcp/commit/bcb8a793e3e1536ba4426dd42038ec3653f4d50e))

## [0.3.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.2.0...v0.3.0) (2026-05-28)


### Features

* add place_holds bulk tool ([4cf4537](https://github.com/pdugan20/bibliocommons-mcp/commit/4cf45372c10f6f43daa28f08a88e1433cdfbb8de))
* add ready_for_pickup, cancel_holds, and jacket cover URLs ([f3e2460](https://github.com/pdugan20/bibliocommons-mcp/commit/f3e2460e3918f9a8afe99f8f1b9747927534462d))
* **check-in:** return digital checkouts early via check_in_loan(s) ([7ac9e47](https://github.com/pdugan20/bibliocommons-mcp/commit/7ac9e471a06af8a90cfc147b62ef65eff875931c))
* **holds:** place_digital_hold for Libby waitlist ([fa5e526](https://github.com/pdugan20/bibliocommons-mcp/commit/fa5e52683d9c45f9c681930b20985ee0361bffe1))
* **renew:** add renew_loan + renew_loans tools ([ac52ff2](https://github.com/pdugan20/bibliocommons-mcp/commit/ac52ff257a4e55bb30d9129673e4233dca1dcffa))
* scaffold web/ workbench (build chain end-to-end) ([db31558](https://github.com/pdugan20/bibliocommons-mcp/commit/db31558e137467be855048e1c441b72beab3560a))
* **ui:** wire MCP Apps bundles + add CI freshness check ([923ede7](https://github.com/pdugan20/bibliocommons-mcp/commit/923ede7ddab86fa8f069dd68e5f123557cdb02f1))
* **web:** BibCard component + search bundle ([540f512](https://github.com/pdugan20/bibliocommons-mcp/commit/540f51263cb21dff36f234dbbea6e42bd4c937c4))
* **web:** HoldCard component + holds bundle ([29d01bb](https://github.com/pdugan20/bibliocommons-mcp/commit/29d01bba5e6458833586e0fc801fd3ac753cda21))
* **web:** LoanCard component + loans bundle ([c8ded52](https://github.com/pdugan20/bibliocommons-mcp/commit/c8ded528e264a3fc36c7f9c1ae0429717e539510))
* **web:** workbench for local card iteration ([9100c8e](https://github.com/pdugan20/bibliocommons-mcp/commit/9100c8ebfecef9ba45bad4c9465129dfc7924b2f))


### Bug Fixes

* drop description from schema snapshot (cross-Python drift) ([cac23fa](https://github.com/pdugan20/bibliocommons-mcp/commit/cac23fae4fdbadb3992dd5adc9185df000ce721b))
* normalize tool descriptions in schema snapshot ([d88304e](https://github.com/pdugan20/bibliocommons-mcp/commit/d88304ecd4ff3877675a2c82e19936eee15bdbbe))


### Documentation

* add docs/projects briefs + expand roadmap inventory ([433d115](https://github.com/pdugan20/bibliocommons-mcp/commit/433d1153cac4e20bc0bfeb316781e4128f38d58d))
* add place_holds to readme tools table ([322ff3f](https://github.com/pdugan20/bibliocommons-mcp/commit/322ff3f457c678fff3f86d8de568bed9c8aa4274))
* README + project docs + workbench test plan ([5d5be53](https://github.com/pdugan20/bibliocommons-mcp/commit/5d5be530491c7e89aacbd03c23d62bf140f547cd))

## [0.2.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.1.0...v0.2.0) (2026-05-27)


### Features

* add bibliocommons-mcp init wizard ([86397db](https://github.com/pdugan20/bibliocommons-mcp/commit/86397db0d2fa173d08d50edd552ee0ee5072454f))
* add dry_run flag to cancel_hold ([94c85cd](https://github.com/pdugan20/bibliocommons-mcp/commit/94c85cd25a8cb6a3a446ed280d94b8892b912737))
* pydantic response models + tool annotations + server instructions ([2b39ffc](https://github.com/pdugan20/bibliocommons-mcp/commit/2b39ffcc328e872640aebe0ca3c364d86fd633e2))


### Documentation

* add badges, SECURITY.md, issue + PR templates ([6a83895](https://github.com/pdugan20/bibliocommons-mcp/commit/6a83895ebaff844985b25a6006a7f8cab36a629b))
* polish readme + add roadmap + troubleshooting ([6d95b8a](https://github.com/pdugan20/bibliocommons-mcp/commit/6d95b8ab7e84cc875c7c6225bb880007d5898cf3))
* restructure README + add docs/ topic pages ([8f6dea9](https://github.com/pdugan20/bibliocommons-mcp/commit/8f6dea9607f4def93e4e704a146bde904b06b66b))
* tighten readme + known-libraries pass ([feadc2e](https://github.com/pdugan20/bibliocommons-mcp/commit/feadc2e3b7c41f1c4079d8020504a156d78af176))

## Changelog

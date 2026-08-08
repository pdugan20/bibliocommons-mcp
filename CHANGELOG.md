# Changelog

## [0.6.2](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.6.1...v0.6.2) (2026-07-28)


### Bug Fixes

* support MCP 2026-07-28 ([22ed821](https://github.com/pdugan20/bibliocommons-mcp/commit/22ed821aa61198a16334a1c2c50b53c22dcd1f62))

## [0.6.1](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.6.0...v0.6.1) (2026-07-24)


### Bug Fixes

* **auth:** support Chicago multi-domain SSO ([#58](https://github.com/pdugan20/bibliocommons-mcp/issues/58)) ([38a396e](https://github.com/pdugan20/bibliocommons-mcp/commit/38a396ea3ad4429618497978c2b79a61b5f40dba))
* **deps:** bridge Vite security updates on v6 ([#57](https://github.com/pdugan20/bibliocommons-mcp/issues/57)) ([9503a34](https://github.com/pdugan20/bibliocommons-mcp/commit/9503a34dd5d0e3e581cc84d523a55f56c4493fbc))
* **preview-cards:** stable format-filter pill order ([#43](https://github.com/pdugan20/bibliocommons-mcp/issues/43)) ([c5ca1ca](https://github.com/pdugan20/bibliocommons-mcp/commit/c5ca1cabf0f1f96364c29ef2258ba05f1662053b))

## [0.6.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.5.0...v0.6.0) (2026-07-01)


### Features

* **preview-cards:** enrich holds/loans/search cards, clickable links, due-sorted checkouts ([#37](https://github.com/pdugan20/bibliocommons-mcp/issues/37)) ([1bac840](https://github.com/pdugan20/bibliocommons-mcp/commit/1bac8402d763cf7df342863d6b48f1a38fa7d59b))
* **preview-cards:** sanitize catalog titles for display ([#41](https://github.com/pdugan20/bibliocommons-mcp/issues/41)) ([7257215](https://github.com/pdugan20/bibliocommons-mcp/commit/7257215830cbfc50a5c9780c17f940a0cd1ae93c))
* **search:** fold subtitle into the title for context ([#40](https://github.com/pdugan20/bibliocommons-mcp/issues/40)) ([7974d33](https://github.com/pdugan20/bibliocommons-mcp/commit/7974d3329fa8ee1c8db59a9dcd4acebb48f93087))


### Bug Fixes

* **holds:** show the ready deadline from expiryDate ([#42](https://github.com/pdugan20/bibliocommons-mcp/issues/42)) ([ea9202f](https://github.com/pdugan20/bibliocommons-mcp/commit/ea9202f04ef3f5ffc707224c8daeb74ed896aabb))
* **http:** transparent favicon everywhere; drop apple-touch icon ([#32](https://github.com/pdugan20/bibliocommons-mcp/issues/32)) ([fda6e03](https://github.com/pdugan20/bibliocommons-mcp/commit/fda6e03b22a2f5feb5a3ff96a6f3e835759e11a8))
* make the served favicon square ([#34](https://github.com/pdugan20/bibliocommons-mcp/issues/34)) ([f9f63b7](https://github.com/pdugan20/bibliocommons-mcp/commit/f9f63b71af08bde2ed50e1396e0fa4d546358122))
* **preview-cards:** mobile polish — iOS corners, tap-highlight, lighter cover border ([#39](https://github.com/pdugan20/bibliocommons-mcp/issues/39)) ([eebe515](https://github.com/pdugan20/bibliocommons-mcp/commit/eebe515b4233e1efbf02049eb7880ed3898e100a))
* use an opaque square favicon source ([#33](https://github.com/pdugan20/bibliocommons-mcp/issues/33)) ([4091929](https://github.com/pdugan20/bibliocommons-mcp/commit/40919296ea34fd2d31d243bf3916873d7f957a76))


### Documentation

* house-style review pass (IA, voice, icons, brand) ([#27](https://github.com/pdugan20/bibliocommons-mcp/issues/27)) ([21d0669](https://github.com/pdugan20/bibliocommons-mcp/commit/21d0669942c2c1ddc50fb332221534fd46d9cfe3))
* **projects:** correct v1.2 briefs to shipped status ([#26](https://github.com/pdugan20/bibliocommons-mcp/issues/26)) ([44b5e99](https://github.com/pdugan20/bibliocommons-mcp/commit/44b5e999af452bcfdd140049fe2d803a01752bfd))
* **projects:** reconcile briefs to v0.5.0 state ([#24](https://github.com/pdugan20/bibliocommons-mcp/issues/24)) ([cf3f28e](https://github.com/pdugan20/bibliocommons-mcp/commit/cf3f28eb19171de65898614df8fcb5bb389ee46a))

## [0.5.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.4.0...v0.5.0) (2026-05-30)


### Features

* **auth:** account settings page for per-user library credentials ([#9](https://github.com/pdugan20/bibliocommons-mcp/issues/9)) ([d528a9c](https://github.com/pdugan20/bibliocommons-mcp/commit/d528a9c8c5dd7bad8cfe07633aa1ddc52a285754))
* **auth:** gate single-user mode to allow-listed owner subjects ([#18](https://github.com/pdugan20/bibliocommons-mcp/issues/18)) ([4ef064c](https://github.com/pdugan20/bibliocommons-mcp/commit/4ef064c692ea134fe205d512712c6803cdc1a732))
* **auth:** multi-user WorkOS OAuth Resource Server + per-user routing ([#8](https://github.com/pdugan20/bibliocommons-mcp/issues/8)) ([dd9eb6a](https://github.com/pdugan20/bibliocommons-mcp/commit/dd9eb6abf45463ce4572bdd461efe8ff3b1d8230))
* **http:** add getbiblio favicon assets + svg/apple-touch routes ([#17](https://github.com/pdugan20/bibliocommons-mcp/issues/17)) ([3b58341](https://github.com/pdugan20/bibliocommons-mcp/commit/3b58341a51a014d29bc98b910c9f400fdb7a367b))
* **http:** remote-MCP Milestone 1 — Streamable HTTP + read-only catalog mode ([#5](https://github.com/pdugan20/bibliocommons-mcp/issues/5)) ([5c6ef93](https://github.com/pdugan20/bibliocommons-mcp/commit/5c6ef930b718413b241ef9f9b098489b062ffcfd))
* **http:** single-user mode + /favicon.ico and landing routes ([#14](https://github.com/pdugan20/bibliocommons-mcp/issues/14)) ([9214783](https://github.com/pdugan20/bibliocommons-mcp/commit/9214783b9c329bc34a3e43afdf010fc248d7947a))


### Bug Fixes

* **deploy:** auto_start_machines = true so a stopped Fly machine self-heals ([#13](https://github.com/pdugan20/bibliocommons-mcp/issues/13)) ([188e531](https://github.com/pdugan20/bibliocommons-mcp/commit/188e531a0e741e585903dba80423743796b55af3))
* **http:** allow the deployed Host for Streamable HTTP; Fly region sjc ([#12](https://github.com/pdugan20/bibliocommons-mcp/issues/12)) ([93ef1f0](https://github.com/pdugan20/bibliocommons-mcp/commit/93ef1f09def12e07ee7ac12c05115028f09df18f))
* **ui:** allow OverDrive CDN so Libby/digital covers render ([#23](https://github.com/pdugan20/bibliocommons-mcp/issues/23)) ([4447a1e](https://github.com/pdugan20/bibliocommons-mcp/commit/4447a1e127226b62779d2eb7e9209d830f508cde))
* **ui:** match the shipping MCP Apps wire format so cards actually render ([#21](https://github.com/pdugan20/bibliocommons-mcp/issues/21)) ([186dcba](https://github.com/pdugan20/bibliocommons-mcp/commit/186dcbaa81f9e6ca05bf1b150c54abe22a1476a9))


### Performance Improvements

* **auth:** bound per-user client cache with idle-TTL + LRU, plus M3 audit ([#10](https://github.com/pdugan20/bibliocommons-mcp/issues/10)) ([fad7e2a](https://github.com/pdugan20/bibliocommons-mcp/commit/fad7e2a3f27be2b550df696f3cb979f6a5cd4285))


### Documentation

* **docs-site:** add Mintlify docs site with generated reference and anti-drift CI ([#19](https://github.com/pdugan20/bibliocommons-mcp/issues/19)) ([8ba173e](https://github.com/pdugan20/bibliocommons-mcp/commit/8ba173eb0ecda01545721e6797af0bb65f02a091))
* **docs-site:** pause Phase 3 (Mintlify 1-site-per-account); document setup steps ([#20](https://github.com/pdugan20/bibliocommons-mcp/issues/20)) ([d5f274a](https://github.com/pdugan20/bibliocommons-mcp/commit/d5f274aa87bcb44cf34cf5cec03a31df3182e8f1))
* **preview-cards:** record the rendering fix; reopen milestone 4 as active ([#22](https://github.com/pdugan20/bibliocommons-mcp/issues/22)) ([e3ea18b](https://github.com/pdugan20/bibliocommons-mcp/commit/e3ea18b9832846dd9ae8233202a5517d0cdbfdba))
* **projects:** reconcile follow-ups to live state; close out shipped/N-A items ([#16](https://github.com/pdugan20/bibliocommons-mcp/issues/16)) ([6b1bcc4](https://github.com/pdugan20/bibliocommons-mcp/commit/6b1bcc483947f0d5fbdfaa04b9d2a701aa8f94b8))

## [0.4.0](https://github.com/pdugan20/bibliocommons-mcp/compare/v0.3.0...v0.4.0) (2026-05-28)


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

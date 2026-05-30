# Docs site — deferred / out of scope

Explicitly parked, with the reason. Not silent omissions.

- **Separate marketing site (Astro `www`).** rewind has one because rewind.rest
  is a product; bibliocommons-mcp is an OSS tool, so the Mintlify intro page is
  the landing. Revisit only if `getbiblio.app` ever becomes a marketed service.
- **Legal pages (Terms/Privacy/DPA).** Needed for a hosted multi-user service
  handling other people's data; not for an OSS tool / single-user instance.
  Revisit with multi-user.
- **API playground / OpenAPI.** No REST API — the interface is MCP tools, which
  the generated tool reference + `llms.txt` already cover.
- **Custom-domain Mintlify paid tier.** `docs.getbiblio.app` on the free OSS
  tier is sufficient; the $-tier features (custom auth, etc.) aren't needed.
- **Multi-user as the headline.** Documented as an "advanced" subsection only,
  pending the BiblioCommons/SPL ToS question. Promote later if it clears.
- **Versioned docs.** Single current version is fine until the tool surface
  changes enough to need it.

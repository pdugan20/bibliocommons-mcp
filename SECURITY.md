# Security Policy

## Supported Versions

Only the latest minor release on PyPI is supported. Older versions are not patched.

## Reporting a Vulnerability

If you discover a security issue, **do not open a public GitHub issue**. Instead, use one of these private channels:

- [GitHub Security Advisories](https://github.com/pdugan20/bibliocommons-mcp/security/advisories/new) (preferred — lets us coordinate a fix and disclosure)
- Email: <dugan.pat@gmail.com>

I'll acknowledge within 7 days. Coordinated disclosure preferred; please give a reasonable window before going public.

## What counts as a security issue

This tool handles library card credentials and session cookies. Particular interest:

- Credentials, PINs, or auth tokens leaking via logs, cassettes, or error messages
- Bypasses of the credential-leak pre-commit hook
- VCR cassette sanitization missing a sensitive field
- The MCP server returning credentials in tool responses (it shouldn't)
- Anything that lets a third party act on a user's library account

For BiblioCommons / library-system bugs themselves, please report to the library or to BiblioCommons directly — those aren't in scope for this project.

# MCP client setup

bibliocommons-mcp speaks the MCP wire protocol over stdio. Any client that supports stdio MCP servers can use it. After installing the package (`pipx install bibliocommons-mcp`), the `bibliocommons-mcp` console script is on your `$PATH`.

The server reads its config from `~/.config/bibliocommons-mcp/config.toml` (or environment variables — see [`configuration.md`](configuration.md)). That's the same regardless of client.

## Claude Code

```bash
claude mcp add bibliocommons bibliocommons-mcp --scope user
```

Then restart the session. `--scope user` makes it available across all your projects; drop the flag to add it only in the current directory.

## Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent on your OS:

```json
{
  "mcpServers": {
    "bibliocommons": {
      "command": "bibliocommons-mcp"
    }
  }
}
```

Restart Claude Desktop. You should see "bibliocommons" appear in the tools menu.

If `bibliocommons-mcp` isn't on Claude Desktop's `$PATH`, use the absolute path from `which bibliocommons-mcp`:

```json
{
  "mcpServers": {
    "bibliocommons": {
      "command": "/Users/you/.local/bin/bibliocommons-mcp"
    }
  }
}
```

## Cursor / Continue / Cline / Zed

All of these support stdio MCP servers. The configuration shape varies but the gist is the same:

- **Command**: `bibliocommons-mcp`
- **Args**: none
- **Env**: optional — set `BIBLIOCOMMONS_LIBRARY` / `BIBLIOCOMMONS_CARD` / `BIBLIOCOMMONS_PIN` here if you prefer env config over `config.toml`

Check your client's MCP docs for the exact JSON / TOML field names.

## Debugging

If a client says the server failed to start, run it directly to see the error:

```bash
bibliocommons-mcp
```

It expects to speak MCP framing over stdio, so it'll appear to hang — that's correct. Ctrl-C out. If you see a config error before that, the loader couldn't find your `library` / `card` / `pin`.

For more output, set `BIBLIOCOMMONS_MCP_LOG_LEVEL=DEBUG` in the client's env (or your shell). Logs go to stderr; the client typically surfaces them in its UI somewhere.

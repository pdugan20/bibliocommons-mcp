# Container image for the remote / Streamable-HTTP deployment (Cloud Run,
# Fly, etc.). Local stdio usage (Claude Code / Desktop) does NOT need this —
# see docs/projects/remote-mcp-mobile.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Belt-and-suspenders: select HTTP transport even if a platform
    # overrides CMD with just the bare entrypoint.
    BIBLIOCOMMONS_MCP_TRANSPORT=http

WORKDIR /app

# Build inputs: pyproject (with the file-based version source) + README
# (declared as the project readme) + the package source.
COPY pyproject.toml README.md ./
COPY src ./src
# Install the package and create the non-root user in one layer.
RUN pip install . \
  && useradd --create-home --uid 10001 app
USER 10001

# Cloud Run / Fly inject $PORT; _run_http() honors it (default 8000).
EXPOSE 8000

# Liveness via the credential-free /healthz route. (Cloud Run uses its own
# probes and ignores this; it helps for Docker/Fly/local.)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import os,sys,urllib.request; p=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/healthz', timeout=2).status==200 else 1)"]

CMD ["bibliocommons-mcp", "serve", "--http"]

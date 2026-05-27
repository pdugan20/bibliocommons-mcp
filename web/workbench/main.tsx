/**
 * Local design workbench for bibliocommons-mcp UI bundles.
 *
 * Mounts the production bundle's HTML entry inside an iframe and plays
 * the host side of the MCP Apps protocol against it: responds to
 * `ui/initialize` with a stub host context, then pushes a fake
 * `ui/notifications/tool-result` carrying the selected fixture's
 * structuredContent. Same connect/handshake/render path the real
 * Claude Desktop host uses — just with fixture data instead of a
 * real tool call.
 *
 * Iterate on components in `web/components/`, save, Vite HMR
 * re-mounts the bundle.
 *
 * Sequencing: the SDK only accepts tool-result notifications after it
 * has sent `ui/notifications/initialized`. Wait for that before
 * flushing the first fixture; after that, switching fixtures pushes
 * immediately. "Reload iframe" remounts and restarts the handshake.
 */
import {
  StrictMode,
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { createRoot } from "react-dom/client";

import { bundles, type Bundle } from "./registry.js";
import type { Fixture } from "../holds.fixtures.js";

// Spec revision the workbench negotiates with bundles. Matches the
// version `@modelcontextprotocol/ext-apps` ships against in
// web/package.json.
const PROTOCOL_VERSION = "2026-01-26";

function buildHostResponse(theme: "light" | "dark") {
  return {
    protocolVersion: PROTOCOL_VERSION,
    hostInfo: { name: "bibliocommons-mcp-workbench", version: "0.1.0" },
    hostCapabilities: {
      openLinks: {},
      logging: {},
      sandbox: {},
    },
    hostContext: {
      theme,
      platform: "desktop",
      locale: navigator.language,
    },
  };
}

type Status =
  | "mounting"
  | "awaiting-initialize"
  | "initialized"
  | "pushed-result";

type Viewport = "mobile" | "tablet" | "desktop";
type Theme = "light" | "dark";

const VIEWPORT_WIDTHS: Record<Viewport, number> = {
  mobile: 380,
  tablet: 600,
  desktop: 720,
};

function ToggleGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: string; label: string }[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span
        style={{
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: 0.4,
          opacity: 0.6,
        }}
      >
        {label}
      </span>
      <div
        style={{
          display: "inline-flex",
          background: "light-dark(rgba(0,0,0,0.04), rgba(255,255,255,0.06))",
          borderRadius: 6,
          padding: 2,
        }}
      >
        {options.map((o) => {
          const active = o.value === value;
          return (
            <button
              key={o.value}
              onClick={() => onChange(o.value)}
              type="button"
              aria-pressed={active}
              style={{
                padding: "4px 10px",
                fontSize: 12,
                fontWeight: 500,
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                background: active
                  ? "light-dark(#fff, rgba(255,255,255,0.12))"
                  : "transparent",
                color: "inherit",
                boxShadow: active ? "0 1px 2px rgba(0,0,0,0.08)" : undefined,
              }}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

const asideStyle: CSSProperties = {
  padding: "16px 12px",
  borderRight: "1px solid light-dark(#e0e0e0, #2e2e2e)",
  overflowY: "auto",
  fontSize: 13,
};

function Workbench() {
  const [bundle, setBundle] = useState<Bundle>(bundles[0]);
  const [fixture, setFixture] = useState<Fixture>(bundles[0].fixtures[0]);
  const [reloadKey, setReloadKey] = useState(0);
  const [status, setStatus] = useState<Status>("mounting");
  const [viewport, setViewport] = useState<Viewport>("desktop");
  const [theme, setTheme] = useState<Theme>(
    matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );

  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  // Apply theme to the workbench chrome (host doc).
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  // Latest theme in a ref so the message handler (registered once
  // with [] deps for stability) reads the current value on every
  // ui/initialize round-trip.
  const themeRef = useRef(theme);
  themeRef.current = theme;

  // Broadcast theme changes to the iframe so the bundle's useHostStyles
  // re-applies colors live.
  useEffect(() => {
    const target = iframeRef.current?.contentWindow;
    if (!target || !initializedRef.current) return;
    target.postMessage(
      {
        jsonrpc: "2.0",
        method: "ui/notifications/host-context-changed",
        params: { theme },
      },
      "*",
    );
  }, [theme]);

  // Keep the *latest* fixture in a ref so the listener and the
  // post-init send both push the right one regardless of effect-
  // ordering races.
  const fixtureRef = useRef(fixture);
  fixtureRef.current = fixture;

  // Per-iframe-instance gate. Resets whenever the iframe remounts
  // (bundle change, reloadKey bump) so the next ui/initialize round-
  // trip re-triggers a tool-result push.
  const initializedRef = useRef(false);

  const sendToolResult = useCallback((target: Window, fx: Fixture) => {
    const message = {
      jsonrpc: "2.0",
      method: "ui/notifications/tool-result",
      params: {
        content: [{ type: "text", text: fx.description ?? fx.name }],
        structuredContent: fx.structuredContent,
      },
    };
    console.debug("[workbench] → tool-result", fx.name, message.params);
    target.postMessage(message, "*");
    setStatus("pushed-result");
  }, []);

  useEffect(() => {
    function onMessage(ev: MessageEvent) {
      const msg = ev.data;
      const target = iframeRef.current?.contentWindow;
      if (!msg || msg.jsonrpc !== "2.0" || !target) return;
      // Vite HMR posts on the same window; filter to messages from the
      // iframe we're hosting.
      if (ev.source !== target) return;

      if (msg.method === "ui/initialize" && msg.id != null) {
        console.debug("[workbench] ← ui/initialize", msg.params);
        target.postMessage(
          {
            jsonrpc: "2.0",
            id: msg.id,
            result: buildHostResponse(themeRef.current),
          },
          "*",
        );
        setStatus("awaiting-initialize");
        return;
      }
      if (msg.method === "ui/notifications/initialized") {
        console.debug("[workbench] ← ui/notifications/initialized");
        initializedRef.current = true;
        setStatus("initialized");
        sendToolResult(target, fixtureRef.current);
        return;
      }
      if (msg.method?.startsWith("ui/")) {
        console.debug("[workbench] ←", msg.method, msg.params);
      }
    }
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [sendToolResult]);

  // Iframe remount: clear initialized state so the next handshake
  // re-pushes a fresh tool-result.
  useEffect(() => {
    initializedRef.current = false;
    setStatus("mounting");
  }, [bundle, reloadKey]);

  // Fixture change without iframe remount: if already initialized,
  // push the new tool-result immediately.
  useEffect(() => {
    if (!initializedRef.current) return;
    const target = iframeRef.current?.contentWindow;
    if (target) sendToolResult(target, fixture);
  }, [fixture, sendToolResult]);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "260px 1fr",
        height: "100vh",
        gap: 0,
      }}
    >
      <aside style={asideStyle}>
        <h1 style={{ fontSize: 14, margin: "0 0 12px" }}>
          bibliocommons-mcp workbench
        </h1>
        {bundles.map((b) => (
          <div key={b.slug} style={{ marginBottom: 16 }}>
            <button
              onClick={() => {
                setBundle(b);
                setFixture(b.fixtures[0]);
              }}
              style={{
                background: bundle.slug === b.slug ? "#3b82f6" : "transparent",
                color: bundle.slug === b.slug ? "#fff" : "inherit",
                border: "1px solid light-dark(#d4d4d4, #3a3a3a)",
                borderRadius: 4,
                padding: "6px 10px",
                width: "100%",
                textAlign: "left",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {b.label}
            </button>
            {bundle.slug === b.slug && (
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: "8px 0 0 8px",
                }}
              >
                {b.fixtures.map((fx) => (
                  <li key={fx.name}>
                    <button
                      onClick={() => setFixture(fx)}
                      style={{
                        background: "transparent",
                        border: "none",
                        padding: "4px 0",
                        cursor: "pointer",
                        textAlign: "left",
                        color: fixture.name === fx.name ? "#3b82f6" : "inherit",
                        fontWeight: fixture.name === fx.name ? 600 : 400,
                        fontSize: 12,
                      }}
                    >
                      {fx.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
        <button
          onClick={() => setReloadKey((k) => k + 1)}
          style={{
            marginTop: 8,
            padding: "4px 8px",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          reload iframe
        </button>
        <div
          style={{
            marginTop: 16,
            fontSize: 11,
            opacity: 0.7,
            fontFamily: "ui-monospace, monospace",
          }}
        >
          status: {status}
        </div>
      </aside>
      <main
        style={{
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <header
          style={{
            display: "flex",
            gap: 16,
            alignItems: "center",
            padding: "12px 24px",
            borderBottom:
              "1px solid light-dark(rgba(0,0,0,0.08), rgba(255,255,255,0.08))",
            fontSize: 12,
          }}
        >
          <ToggleGroup
            label="Viewport"
            options={[
              { value: "mobile", label: "Mobile" },
              { value: "tablet", label: "Tablet" },
              { value: "desktop", label: "Desktop" },
            ]}
            value={viewport}
            onChange={(v) => setViewport(v as Viewport)}
          />
          <ToggleGroup
            label="Theme"
            options={[
              { value: "light", label: "Light" },
              { value: "dark", label: "Dark" },
            ]}
            value={theme}
            onChange={(v) => setTheme(v as Theme)}
          />
        </header>
        <div
          style={{
            padding: 24,
            overflow: "auto",
            flex: 1,
          }}
        >
          <iframe
            key={`${bundle.slug}-${reloadKey}`}
            ref={iframeRef}
            src={bundle.entryUrl}
            title={bundle.label}
            style={{
              display: "block",
              width: "100%",
              maxWidth: VIEWPORT_WIDTHS[viewport],
              minHeight: 280,
              border: "none",
              background: "transparent",
              transition: "max-width 200ms ease",
            }}
          />
          <details
            style={{
              marginTop: 16,
              fontSize: 12,
              opacity: 0.7,
              maxWidth: VIEWPORT_WIDTHS[viewport],
            }}
          >
            <summary>fixture payload</summary>
            <pre style={{ fontSize: 11, lineHeight: 1.4 }}>
              {JSON.stringify(fixture.structuredContent, null, 2)}
            </pre>
          </details>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Workbench />
  </StrictMode>,
);

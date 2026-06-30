/**
 * Opening catalog links from inside an MCP App. The view is a sandboxed
 * iframe with no popup permission, so a plain `<a target="_blank">` can't
 * reliably open a tab; the spec route is `app.openLink({url})` → host
 * (`ui/open-link`) → the host opens it. Entries register the app's opener
 * via `useLinkOpener`; cards wrap content in `<RecordLink>`. Outside a real
 * host (the dev workbench/gallery), we fall back to `window.open`.
 */
import { useEffect, type CSSProperties, type ReactNode } from "react";

type AppLike = { openLink: (params: { url: string }) => Promise<unknown> };

let opener: ((url: string) => void) | null = null;

function fallbackOpen(url: string): void {
  window.open(url, "_blank", "noopener,noreferrer");
}

export function openLink(url: string): void {
  if (opener) opener(url);
  else fallbackOpen(url);
}

/** Register the connected app as the link opener (with a window.open
 * fallback if the host rejects or doesn't support `ui/open-link`). */
export function useLinkOpener(app: AppLike | null | undefined): void {
  useEffect(() => {
    if (!app) return;
    opener = (url) => {
      void app.openLink({ url }).catch(() => fallbackOpen(url));
    };
    return () => {
      opener = null;
    };
  }, [app]);
}

const linkStyle: CSSProperties = {
  color: "inherit",
  textDecoration: "none",
  cursor: "pointer",
};

/** Wrap content in a click-to-open catalog-record link. With no url it's a
 * passthrough, so callers don't need their own conditional. */
export function RecordLink({
  url,
  style,
  children,
}: {
  url?: string | null;
  style?: CSSProperties;
  children: ReactNode;
}) {
  if (!url) return <>{children}</>;
  return (
    <a
      href={url}
      onClick={(e) => {
        e.preventDefault();
        openLink(url);
      }}
      style={{ ...linkStyle, ...style }}
    >
      {children}
    </a>
  );
}

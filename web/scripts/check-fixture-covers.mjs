#!/usr/bin/env node
/**
 * Fetch every cover URL referenced in web/*.fixtures.ts and fail if any
 * returns a Syndetics "no cover" sentinel (an ~86-byte 1x1 GIF/JPEG)
 * instead of real art.
 *
 * A resolving URL is NOT proof of a real cover — Syndetics 200s with a tiny
 * placeholder for an ISBN/UPC it doesn't have, so a fixture can silently
 * render a broken box in a product screenshot. Run this before cutting a
 * release (it hits the network, so it's a manual/optional check, not part
 * of the offline CI gate):
 *
 *   cd web && npm run check:covers
 *
 * Note: a real cover is verified by SIZE here, not content — a URL can
 * still resolve to the *wrong* book at full size. Always eyeball new covers
 * in the workbench gallery too.
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const webDir = dirname(dirname(fileURLToPath(import.meta.url)));
const MIN_BYTES = 300; // sentinel is ~86 bytes; real covers are >2 KB

const urls = new Set();
for (const f of readdirSync(webDir).filter((n) => n.endsWith(".fixtures.ts"))) {
  const txt = readFileSync(join(webDir, f), "utf8");
  for (const m of txt.matchAll(/https?:\/\/[^"'`\s]+/g)) urls.add(m[0]);
}

if (!urls.size) {
  console.error("No cover URLs found in web/*.fixtures.ts");
  process.exit(1);
}

const results = await Promise.all(
  [...urls].map(async (url) => {
    try {
      const res = await fetch(url, { redirect: "follow" });
      const bytes = (await res.arrayBuffer()).byteLength;
      return {
        url,
        status: res.status,
        bytes,
        ok: res.ok && bytes >= MIN_BYTES,
      };
    } catch (err) {
      return { url, status: "ERR", bytes: 0, ok: false, err: String(err) };
    }
  }),
);

results.sort((a, b) => a.bytes - b.bytes);
for (const r of results) {
  const tag = r.ok ? "ok " : "BAD";
  console.log(`${tag}  ${String(r.bytes).padStart(7)}b  ${r.status}  ${r.url}`);
}

const bad = results.filter((r) => !r.ok);
console.log(
  `\n${urls.size} cover URLs checked, ${bad.length} bad (< ${MIN_BYTES} bytes or non-200).`,
);
process.exit(bad.length ? 1 : 0);

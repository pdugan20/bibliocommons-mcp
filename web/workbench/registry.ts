/**
 * Bundle registry. One entry per `web/<name>.tsx` bundle so the
 * workbench sidebar lists it and can mount it with its fixtures.
 *
 * `entryUrl` is what the workbench's iframe `src` points at. In dev,
 * Vite serves `web/<name>.html` directly from the parent root — the
 * workbench config's `root` is the `web/` parent so these paths
 * resolve.
 */
import { fixtures as holdsFixtures, type Fixture } from "../holds.fixtures.js";
import { fixtures as loansFixtures } from "../loans.fixtures.js";
import { fixtures as searchFixtures } from "../search.fixtures.js";

export type Bundle = {
  /** Slug shown in the sidebar and used as the iframe key. */
  slug: string;
  /** Human-readable label. */
  label: string;
  /** Path Vite serves the bundle's HTML entry from (relative to web/). */
  entryUrl: string;
  /** Available fixtures the workbench can post into the iframe. */
  fixtures: Fixture[];
};

// Cast across the per-bundle Fixture types: they all share the same
// shape (name + description + structuredContent), they just carry
// different structuredContent payloads. The workbench treats them
// uniformly.
export const bundles: Bundle[] = [
  {
    slug: "holds",
    label: "Holds",
    entryUrl: "/holds.html",
    fixtures: holdsFixtures as unknown as Fixture[],
  },
  {
    slug: "loans",
    label: "Checkouts",
    entryUrl: "/loans.html",
    fixtures: loansFixtures as unknown as Fixture[],
  },
  {
    slug: "search",
    label: "Search results",
    entryUrl: "/search.html",
    fixtures: searchFixtures as unknown as Fixture[],
  },
];

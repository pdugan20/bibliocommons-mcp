/**
 * Fixtures for the holds bundle. Each is a plausible HoldList payload
 * the holds tool could return. The workbench iterates these so we can
 * see every state without standing up real gateway data.
 *
 * Shape mirrors `bibliocommons_mcp.models.HoldList` exactly — keep in
 * sync if the server-side model changes.
 */
import type { Hold } from "./components/HoldCard.js";

export type HoldList = {
  count: number;
  holds: Hold[];
};

export type Fixture = {
  name: string;
  description?: string;
  structuredContent: HoldList;
};

const COVER_PLASTIC_ETERNITY = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=/SC.GIF&client=sepup&type=xw12&upc=098787129021",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=/MC.GIF&client=sepup&type=xw12&upc=098787129021",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=/LC.JPG&client=sepup&type=xw12&upc=098787129021",
  local_url: null,
};

const COVER_IN_UTERO = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=/SC.GIF&client=sepup&type=xw12&upc=720642472927",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=/MC.GIF&client=sepup&type=xw12&upc=720642472927",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=/LC.JPG&client=sepup&type=xw12&upc=720642472927",
  local_url: null,
};

const COVER_HEAVIER = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

// OverDrive (Libby) digital cover. Comes from a different CDN than the
// Syndetics jacket — exercises the `*.od-cdn.com` CSP allow-list entry in
// ui.py (PR #23), which otherwise has no fixture coverage. Real URL pulled
// from the cassettes; OverDrive serves one image, so all three sizes reuse it.
const COVER_OVERDRIVE_DIGITAL =
  "https://img1.od-cdn.com/ImageType-100/1523-1/%7BF100E9B4-8CF4-4525-916F-FDE4A77586A4%7DImg100.jpg";
const COVER_OD = {
  small: COVER_OVERDRIVE_DIGITAL,
  medium: COVER_OVERDRIVE_DIGITAL,
  large: COVER_OVERDRIVE_DIGITAL,
  local_url: null,
};

export const fixtures: Fixture[] = [
  {
    name: "Mixed queue (typical)",
    description:
      "Two physical holds (one queued, one ready) plus a digital hold deep in the OverDrive queue.",
    structuredContent: {
      count: 3,
      holds: [
        {
          hold_id: "71992850",
          metadata_id: "S30C3453854",
          title: "Heavier Than Heaven",
          material_type: "PHYSICAL",
          status: "READY_FOR_PICKUP",
          position: null,
          pickup_branch: "LCY",
          placed: "2026-05-20",
          expiry: "2027-03-03",
          jacket: COVER_HEAVIER,
        },
        {
          hold_id: "71992829",
          metadata_id: "S30C3857930",
          title: "Plastic Eternity",
          material_type: "PHYSICAL",
          status: "NOT_YET_AVAILABLE",
          position: 1,
          pickup_branch: "LCY",
          placed: "2026-05-27",
          expiry: "2027-03-03",
          jacket: COVER_PLASTIC_ETERNITY,
        },
        {
          hold_id: "A81AE857-2EEF-49B2-930F-8AE7114F6A7B",
          metadata_id: "S30C4144014",
          // Real OverDrive title whose cover lives on od-cdn — the single
          // fixture that proves the *.od-cdn.com CSP allow-list entry renders.
          title: "Splotch",
          material_type: "DIGITAL",
          status: "NOT_YET_AVAILABLE",
          position: 8,
          pickup_branch: null,
          placed: "2026-05-23",
          expiry: null,
          jacket: COVER_OD,
        },
      ],
    },
  },
  {
    name: "Empty (no holds)",
    structuredContent: {
      count: 0,
      holds: [],
    },
  },
  {
    name: "Single ready for pickup",
    description:
      "Just one card, ready at Lake City — the most common workflow trigger.",
    structuredContent: {
      count: 1,
      holds: [
        {
          hold_id: "71992850",
          metadata_id: "S30C3453854",
          title: "Heavier Than Heaven",
          material_type: "PHYSICAL",
          status: "READY_FOR_PICKUP",
          position: null,
          pickup_branch: "LCY",
          placed: "2026-05-20",
          expiry: "2027-03-03",
          jacket: COVER_HEAVIER,
        },
      ],
    },
  },
  {
    name: "Long title without jacket",
    description:
      "Edge case: very long title and no cover-art URL. Title should wrap at 3 lines max; cover area shows the neutral placeholder.",
    structuredContent: {
      count: 1,
      holds: [
        {
          hold_id: "X1",
          metadata_id: "S30CXXXX",
          title:
            "A Compendium of Quite Excessively Long Titles That Editors Once Thought Would Sell Books And Which Cataloguers Are Now Forced To Reckon With",
          material_type: "PHYSICAL",
          status: "NOT_YET_AVAILABLE",
          position: 17,
          pickup_branch: "LCY",
          placed: "2026-04-15",
          expiry: "2027-02-12",
          jacket: null,
        },
      ],
    },
  },
  {
    name: "In transit",
    description: "Hold has been pulled at another branch and is on its way.",
    structuredContent: {
      count: 1,
      holds: [
        {
          hold_id: "T1",
          metadata_id: "S30C2936752",
          title: "In utero",
          material_type: "PHYSICAL",
          status: "IN_TRANSIT",
          position: null,
          pickup_branch: "LCY",
          placed: "2026-05-25",
          expiry: "2027-03-01",
          jacket: COVER_IN_UTERO,
        },
      ],
    },
  },
  {
    name: "Expired hold",
    description:
      "Edge case: the only state that renders the red pill. Hold sat ready and was never picked up.",
    structuredContent: {
      count: 1,
      holds: [
        {
          hold_id: "E1",
          metadata_id: "S30C3453854",
          title: "Heavier Than Heaven",
          material_type: "PHYSICAL",
          status: "EXPIRED",
          position: null,
          pickup_branch: "LCY",
          placed: "2026-03-01",
          expiry: "2026-04-12",
          jacket: COVER_HEAVIER,
        },
      ],
    },
  },
  {
    name: "Queued without position",
    description:
      "NOT_YET_AVAILABLE with no queue position — exercises the 'queued' fallback label (no '#N in queue').",
    structuredContent: {
      count: 1,
      holds: [
        {
          hold_id: "Q1",
          metadata_id: "S30C3857930",
          title: "Plastic Eternity",
          material_type: "PHYSICAL",
          status: "NOT_YET_AVAILABLE",
          position: null,
          pickup_branch: "LCY",
          placed: "2026-06-01",
          expiry: "2027-03-03",
          jacket: COVER_PLASTIC_ETERNITY,
        },
      ],
    },
  },
];

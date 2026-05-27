/**
 * Fixtures for the search bundle. Each is a plausible SearchResult
 * payload the search tool could return.
 */
import type { BibSummary } from "./components/BibCard.js";

export type SearchResult = {
  page?: number | null;
  pages?: number | null;
  total?: number | null;
  results: BibSummary[];
};

export type Fixture = {
  name: string;
  description?: string;
  structuredContent: SearchResult;
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

const COVER_HEAVIER = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

const COVER_SING_BACKWARDS = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9781529104202/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9781529104202/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9781529104202/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

export const fixtures: Fixture[] = [
  {
    name: "Mixed format query",
    description:
      "'kurt cobain' query — book, audiobook, and CD all in the first page.",
    structuredContent: {
      page: 1,
      pages: 3,
      total: 67,
      results: [
        {
          bib_id: "S30C3453854",
          title: "Heavier Than Heaven",
          subtitle: "A Biography of Kurt Cobain",
          authors: ["Cross, Charles R."],
          format: "BK",
          year: "2019",
          call_number: "B COBAIN, K. CROSS",
          jacket: COVER_HEAVIER,
        },
        {
          bib_id: "S30C3637382",
          title: "Sing Backwards and Weep",
          subtitle: "A Memoir",
          authors: ["Lanegan, Mark"],
          format: "BK",
          year: "2020",
          call_number: "B LANEGAN, M. LANEGAN",
          jacket: COVER_SING_BACKWARDS,
        },
        {
          bib_id: "S30C3857930",
          title: "Plastic Eternity",
          subtitle: null,
          authors: ["Mudhoney (Musical group)"],
          format: "MUSIC_CD",
          year: "2023",
          call_number: "CD 782.42166 M884P",
          jacket: COVER_PLASTIC_ETERNITY,
        },
      ],
    },
  },
  {
    name: "Empty (no results)",
    structuredContent: {
      page: 1,
      pages: 0,
      total: 0,
      results: [],
    },
  },
  {
    name: "Single result",
    structuredContent: {
      page: 1,
      pages: 1,
      total: 1,
      results: [
        {
          bib_id: "S30C3857930",
          title: "Plastic Eternity",
          subtitle: null,
          authors: ["Mudhoney (Musical group)"],
          format: "MUSIC_CD",
          year: "2023",
          call_number: "CD 782.42166 M884P",
          jacket: COVER_PLASTIC_ETERNITY,
        },
      ],
    },
  },
  {
    name: "Page 2 of 5",
    description:
      "Pagination indicator should read 'Page 2 of 5 (108 results)'.",
    structuredContent: {
      page: 2,
      pages: 5,
      total: 108,
      results: [
        {
          bib_id: "S30C2585948",
          title: "Sweet Oblivion",
          subtitle: null,
          authors: ["Screaming Trees (Musical group)"],
          format: "MUSIC_CD",
          year: "1992",
          call_number: "CD 782.42166 S433Sw",
          jacket: null,
        },
      ],
    },
  },
  {
    name: "No covers",
    description:
      "Search hits with no jacket URLs — every cover area shows the neutral placeholder.",
    structuredContent: {
      page: 1,
      pages: 1,
      total: 2,
      results: [
        {
          bib_id: "S30CX1",
          title: "Untitled rare press",
          subtitle: null,
          authors: ["Various Artists"],
          format: "MUSIC_CD",
          year: "1998",
          call_number: "CD 782.42166 V299",
          jacket: null,
        },
        {
          bib_id: "S30CX2",
          title: "Field recordings, vol. 3",
          subtitle: "Pacific Northwest, 1991-1994",
          authors: ["Anonymous"],
          format: "BK",
          year: "2010",
          call_number: "F 781.65 A615",
          jacket: null,
        },
      ],
    },
  },
];

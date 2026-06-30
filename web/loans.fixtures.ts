/**
 * Fixtures for the loans bundle. Each is a plausible LoanList payload
 * the loans tool could return. Workbench iterates these to render
 * every due-state without standing up real gateway data.
 */
import { type LoanList } from "./components/LoanCard.js";

export type Fixture = {
  name: string;
  description?: string;
  structuredContent: LoanList;
};

// "Today" for fixture purposes — kept as a constant so due-date math
// in LoanCard renders consistently across workbench reloads. The
// gateway uses YYYY-MM-DD ISO strings; we follow suit.
const TODAY = new Date();
TODAY.setUTCHours(0, 0, 0, 0);

function isoOffset(days: number): string {
  const d = new Date(TODAY);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

const COVER_HEAVIER = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780786884025/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

const COVER_EVERYBODY = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780307464446/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780307464446/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780307464446/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

const COVER_SINGULARITY = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780670033843/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780670033843/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780670033843/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

const COVER_COME_AS_YOU_ARE = {
  small:
    "https://secure.syndetics.com/index.aspx?isbn=9780385471992/SC.GIF&client=sepup&type=xw12",
  medium:
    "https://secure.syndetics.com/index.aspx?isbn=9780385471992/MC.GIF&client=sepup&type=xw12",
  large:
    "https://secure.syndetics.com/index.aspx?isbn=9780385471992/LC.JPG&client=sepup&type=xw12",
  local_url: null,
};

export const fixtures: Fixture[] = [
  {
    name: "Mixed urgency (typical)",
    description:
      "An overdue ebook, an ebook due tomorrow, and an audiobook due in two weeks — all OverDrive.",
    structuredContent: {
      count: 3,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "1052952601",
          metadata_id: "S30C2815026",
          title: "Everybody Loves Our Town",
          author: "Yarm, Mark",
          year: "2011",
          material_type: "DIGITAL",
          format: "EBOOK",
          due: isoOffset(-2),
          call_number: "EBOOK OVERDRIVE",
          branch: null,
          jacket: COVER_EVERYBODY,
          actions: ["checkIn", "updateFormat"],
          times_renewed: 0,
        },
        {
          checkout_id: "1477017860",
          metadata_id: "S30C2636037",
          title: "The Singularity Is Near",
          author: "Kurzweil, Ray",
          year: "2005",
          material_type: "DIGITAL",
          format: "EBOOK",
          due: isoOffset(1),
          call_number: "EBOOK OVERDRIVE",
          branch: null,
          jacket: COVER_SINGULARITY,
          actions: ["checkIn", "updateFormat"],
          times_renewed: 0,
        },
        {
          checkout_id: "1559494087",
          metadata_id: "S30C3452840",
          title: "Come as You Are",
          author: "Azerrad, Michael",
          year: "1993",
          material_type: "DIGITAL",
          format: "EAUDIOBOOK",
          due: isoOffset(14),
          call_number: "EAUDIO OVERDRIVE",
          branch: null,
          jacket: COVER_COME_AS_YOU_ARE,
          actions: ["checkIn", "updateFormat"],
          times_renewed: 0,
        },
      ],
    },
  },
  {
    name: "Empty (no loans)",
    structuredContent: {
      count: 0,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [],
    },
  },
  {
    name: "Due today",
    description: "Single loan with due == today; pill should read 'due today'.",
    structuredContent: {
      count: 1,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "TODAY",
          metadata_id: "S30C9",
          title: "Everybody Loves Our Town",
          author: "Yarm, Mark",
          year: "2011",
          material_type: "DIGITAL",
          format: "EBOOK",
          due: isoOffset(0),
          call_number: "EBOOK OVERDRIVE",
          branch: null,
          jacket: COVER_EVERYBODY,
        },
      ],
    },
  },
  {
    name: "Physical book with branch + call number",
    description:
      "Physical book checked out at Lake City — shows the Book badge, branch code, and call number.",
    structuredContent: {
      count: 1,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "PHYS",
          metadata_id: "S30C9",
          title: "Heavier Than Heaven",
          author: "Cross, Charles R.",
          year: "2019",
          material_type: "PHYSICAL",
          format: "BK",
          due: isoOffset(10),
          call_number: "B COBAIN, K. CROSS",
          branch: "Lake City",
          jacket: COVER_HEAVIER,
          actions: ["renew", "updateFormat"],
          times_renewed: 1,
        },
      ],
    },
  },
  {
    name: "Renewable physical (already renewed once)",
    description:
      "Physical loan with `actions: ['renew', ...]` and `times_renewed: 1` — card surfaces 'Renewable · 1× renewed'.",
    structuredContent: {
      count: 1,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "-3399081509618396918",
          metadata_id: "S30C3680329",
          title: "A Garden to Save the Birds",
          author: "McClure, Wendy",
          year: "2021",
          material_type: "PHYSICAL",
          format: "BK",
          due: isoOffset(20),
          call_number: "E MCCLURE",
          branch: "Lake City",
          jacket: null,
          actions: ["renew", "updateFormat"],
          times_renewed: 1,
        },
      ],
    },
  },
  {
    name: "Renewable (not yet renewed)",
    description:
      "Physical loan with `actions: ['renew']` and `times_renewed: 0` — hint reads plain 'Renewable' (no '· N× renewed').",
    structuredContent: {
      count: 1,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "REN0",
          metadata_id: "S30C3453854",
          title: "Heavier Than Heaven",
          author: "Cross, Charles R.",
          year: "2019",
          material_type: "PHYSICAL",
          format: "BK",
          due: isoOffset(12),
          call_number: "B COBAIN, K. CROSS",
          branch: "Lake City",
          jacket: COVER_HEAVIER,
          actions: ["renew", "updateFormat"],
          times_renewed: 0,
        },
      ],
    },
  },
  {
    name: "Due in 2 days (mid bucket)",
    description:
      "Exercises the 'due in N days' branch between today/tomorrow and the normal >3-day case.",
    structuredContent: {
      count: 1,
      library: "Seattle Public Library",
      more_url: "https://seattle.bibliocommons.com/checkedout",
      loans: [
        {
          checkout_id: "DUE2",
          metadata_id: "S30C2636037",
          title: "The Singularity Is Near",
          author: "Kurzweil, Ray",
          year: "2005",
          material_type: "DIGITAL",
          format: "EBOOK",
          due: isoOffset(2),
          call_number: "EBOOK OVERDRIVE",
          branch: null,
          jacket: COVER_SINGULARITY,
          actions: ["checkIn", "updateFormat"],
          times_renewed: 0,
        },
      ],
    },
  },
];

# Format codes

The `format` parameter of `search` (and `default_format` in config) accepts BiblioCommons' internal facet codes. These are stable across libraries — the SaaS uses the same vocabulary everywhere.

## Common values

| Code              | Meaning                        |
| ----------------- | ------------------------------ |
| `BK`              | Book                           |
| `EBOOK`           | Ebook                          |
| `EAUDIOBOOK`      | E-audiobook                    |
| `AUDIOBOOK_CD`    | Audiobook on CD                |
| `MUSIC_CD`        | Music CD                       |
| `DVD`             | DVD                            |
| `BLU_RAY`         | Blu-ray                        |
| `LARGEPRINT`      | Large print book               |
| `MN`              | Music notation / printed score |
| `MAGAZINE`        | Magazine / periodical          |
| `STREAMING_VIDEO` | Streaming video                |

## Discovering more

A search response includes the format facet itself, with counts per format that matched the query. To enumerate every format your library supports for a given query, search with no `format` filter and inspect `catalogSearch.fields` in the gateway response:

```python
data = client.search("anything", page=1)
formats = data["catalogSearch"]["fields"]  # list with id="FORMAT" and a fieldFilters array
```

Or simpler — search broadly via `list_branches` first, then call `search` without a format, and look at the unique `briefInfo.format` values in the results.

## The full `DigitalFormatType` enum (for the curious)

When we probed the gateway's digital-hold endpoint with an obviously-bad enum value, the Java backend leaked its full enum:

```
MAGAZINE_READ, OVERDRIVE_WMA_AUDIOBOOK, MUSIC, OVERDRIVE_MP3_AUDIOBOOK,
DISNEY_ONLINE_BOOK, ACOUSTIK, OPEN_PDF_EBOOK, KINDLE, OVERDRIVE_MEDIA_DO,
OVERDRIVE_LISTEN, ADOBE_PDF_EBOOK, ADOBE_EPUB_EBOOK, VIDEO, MMM_EBOOK,
STREAMING_VIDEO, OVERDRIVE_READ, UNSUPPORTED_FORMAT, BLIO, OPEN_EPUB_EBOOK
```

Those are the values you'd pass as `materialParams.format` when placing a digital hold (which we don't yet do — see [`architecture.md`](architecture.md)). They map to underlying provider integrations (Kindle, OverDrive Read, Adobe Digital Editions, etc.), not to the search-facet codes above.

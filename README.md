# Comics-SourceHub

A small, data-driven source catalogue for an Android manga/comics reader.

**Important:** this repository stores source metadata and health-probe results. It does not magically add parsers to an app. A source marked `kotatsu_redo` requires the matching Kotatsu-Redo parser library (or a compatible port) in the Android app. Mihon/Keiyoushi extension code is not directly compatible with Kotatsu's parser API.

## Contents

- `sources/*.json` — regular manga/manhwa/manhua/webtoon/comics catalogues.
- `sources/official.json` — official publishing platforms.
- `sources/special/*.json` — separately tracked GetComics and ReadComicsOnline sources.
- `health/status.json` — generated website reachability observations.
- `schema/source.schema.json` — JSON Schema for source records.
- `scripts/validate_catalog.py` — validates catalogue structure and duplicate IDs.
- `scripts/health_check.py` — performs a lightweight HTTP reachability probe.
- `.github/workflows/source-health.yml` — runs validation and health checks every six hours.

## Add this catalogue to your app

Raw catalogue URL pattern:

```text
https://raw.githubusercontent.com/OWNER/REPO/main/sources/manga.json
```

Replace `OWNER/REPO` with your GitHub account and repository name. The app should download the JSON, parse the records, and map each `parser.sourceId` to a parser that is actually bundled or ported into the app. Do not treat a successful catalogue download as proof that a source can read chapters.

## Source status meanings

The health checker checks only whether the website host responds to a lightweight HTTP request. It does **not** test search, manga details, chapter lists, or page images.

- `reachable` — the host returned a 2xx/3xx response.
- `blocked` — the host returned a common bot/auth/rate-limit response (401/403/407/429/503).
- `http_error` — the host responded with another HTTP error.
- `unreachable` — DNS, TLS, timeout, or connection failure.

A 403 is not automatically a dead website. Cloudflare and other anti-bot systems can block scripted probes while the site works in a normal browser. The health report is only a triage signal.

## Current seeded sources

The initial list is deliberately small and includes entries with parser implementations in the Kotatsu-Redo parser repository. `parserChecked` means the parser source file and parser ID were found upstream; it does **not** mean a live end-to-end read test passed today.

The two requested special sources are kept separate:

- **GetComics:** a downloadable comic archive catalogue, not a conventional chapter reader. Its linked API is unofficial and should be treated as experimental.
- **ReadComicsOnline.ru:** has a Kotatsu parser implementation, but may encounter Cloudflare/HTTP 403 restrictions. It is not classified as dead solely because automated requests are blocked.

## Update source records

1. Add or edit records in the relevant JSON file.
2. Keep every `id` unique across all source files, including `sources/special/`.
3. Run `python scripts/validate_catalog.py`.
4. Run `python scripts/health_check.py` (Python 3.10+; standard library only).
5. Commit and push the changes.

## Android integration guidance

See [`docs/ANDROID_INTEGRATION.md`](docs/ANDROID_INTEGRATION.md). This scaffold does not contain your app's existing source runtime, so no app files are overwritten here.

## License and content

This is metadata and integration scaffolding. Each third-party parser/library and each content website has its own license and terms. Review those before copying or redistributing parser code. Prefer official APIs and legally authorized sources where available.

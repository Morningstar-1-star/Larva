#!/usr/bin/env python3
"""Lightweight HTTP reachability checks; never equates HTTP 403 with a dead site."""
from __future__ import annotations

import concurrent.futures
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources"
OUTPUT = ROOT / "health" / "status.json"
TIMEOUT_SECONDS = 15
MAX_WORKERS = 6
BLOCKED_CODES = {401, 403, 407, 429, 503}
USER_AGENT = "Comics-SourceHub-HealthCheck/1.0 (+https://github.com/)"


def load_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(SOURCE_DIR.rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for item in doc.get("sources", []):
            if isinstance(item, dict) and "siteUrl" in item:
                records.append(item)
    return records


def check_one(source: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    url = source["siteUrl"]
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Range": "bytes=0-2047",
        },
        method="GET",
    )
    status: int | None = None
    final_url = url
    note = None
    result = "unreachable"
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            final_url = response.geturl()
            response.read(2048)
            result = "reachable" if 200 <= status < 400 else ("blocked" if status in BLOCKED_CODES else "http_error")
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = exc.geturl() or url
        result = "blocked" if status in BLOCKED_CODES else "http_error"
        note = "HTTP response received; a block/error response does not prove the site is dead."
        try:
            exc.close()
        except Exception:
            pass
    except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError, OSError) as exc:
        note = f"{type(exc).__name__}: {str(exc)[:240]}"
    except Exception as exc:  # Keep one unusual host from aborting the whole run.
        note = f"{type(exc).__name__}: {str(exc)[:240]}"

    return {
        "id": source["id"],
        "name": source.get("name", source["id"]),
        "siteUrl": url,
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "result": result,
        "httpStatus": status,
        "finalUrl": final_url,
        "elapsedMs": round((time.monotonic() - started) * 1000),
        "note": note,
    }


def main() -> int:
    records = load_records()
    # Deduplicate canonical source IDs because category indexes may refer to the same source.
    unique: dict[str, dict[str, Any]] = {}
    for item in records:
        unique[item["id"]] = item
    records = list(unique.values())

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(check_one, item) for item in records]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda x: x["id"])

    counts: dict[str, int] = {}
    for item in results:
        counts[item["result"]] = counts.get(item["result"], 0) + 1

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "HTTP host reachability only; not parser validation",
        "summary": counts,
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Checked {len(results)} unique website host(s): " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

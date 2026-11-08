#!/usr/bin/env python3
"""Validate SourceHub JSON catalogues using only the Python standard library."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
REQUIRED = {"id", "name", "siteUrl", "language", "contentTypes", "sourceKind", "integration", "parser"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def main() -> int:
    errors = 0
    canonical_ids: dict[str, str] = {}
    references: list[tuple[str, str, str]] = []
    files = sorted(SOURCE_DIR.rglob("*.json"))
    if not files:
        fail("No source JSON files found.")
        return 1

    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            errors += 1
            continue

        if not isinstance(doc, dict) or doc.get("schemaVersion") != 1 or not isinstance(doc.get("sources"), list):
            fail(f"{path.relative_to(ROOT)}: expected schemaVersion=1 and a sources array")
            errors += 1
            continue

        for index, item in enumerate(doc["sources"]):
            where = f"{path.relative_to(ROOT)} sources[{index}]"
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                fail(f"{where}: expected a source/reference object with an id")
                errors += 1
                continue
            source_id = item["id"]
            if not ID_RE.fullmatch(source_id):
                fail(f"{where}: invalid id {source_id!r}")
                errors += 1
                continue
            if "refFile" in item:
                if not item.get("refId"):
                    fail(f"{where}: reference entry needs refId")
                    errors += 1
                else:
                    references.append((source_id, item["refFile"], item["refId"]))
                continue

            if source_id in canonical_ids:
                fail(f"{where}: duplicate full source id {source_id!r}; first declared in {canonical_ids[source_id]}")
                errors += 1
            else:
                canonical_ids[source_id] = str(path.relative_to(ROOT))

            missing = REQUIRED - item.keys()
            if missing:
                fail(f"{where}: missing fields: {', '.join(sorted(missing))}")
                errors += 1
                continue
            parsed = urlparse(str(item["siteUrl"]))
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"{where}: siteUrl must be an HTTPS URL")
                errors += 1
            if not isinstance(item["language"], list) or not item["language"]:
                fail(f"{where}: language must be a non-empty array")
                errors += 1
            if not isinstance(item["contentTypes"], list) or not item["contentTypes"]:
                fail(f"{where}: contentTypes must be a non-empty array")
                errors += 1
            parser = item.get("parser")
            if parser is not None:
                for key in ("sourceId", "repo", "filePath", "parserChecked"):
                    if key not in parser:
                        fail(f"{where}: parser is missing {key}")
                        errors += 1

    for source_id, ref_file, ref_id in references:
        target_path = (SOURCE_DIR / ref_file).resolve()
        try:
            target_path.relative_to(SOURCE_DIR.resolve())
        except ValueError:
            fail(f"reference {source_id!r}: refFile escapes sources directory")
            errors += 1
            continue
        if not target_path.is_file():
            fail(f"reference {source_id!r}: missing target file {ref_file!r}")
            errors += 1
            continue
        try:
            target_doc = json.loads(target_path.read_text(encoding="utf-8"))
            target_ids = {entry.get("id") for entry in target_doc.get("sources", []) if isinstance(entry, dict) and "siteUrl" in entry}
            if ref_id not in target_ids or source_id != ref_id:
                fail(f"reference {source_id!r}: {ref_file!r} does not contain canonical source {ref_id!r}")
                errors += 1
        except Exception as exc:
            fail(f"reference {source_id!r}: could not validate target {ref_file!r}: {exc}")
            errors += 1

    if errors:
        print(f"Validation failed: {errors} error(s) across {len(files)} file(s).")
        return 1
    print(f"Validation passed: {len(files)} catalogue file(s), {len(canonical_ids)} unique source ID(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

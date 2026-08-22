from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _extract_inputs(raw_inputs: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_inputs, list):
        return []

    inputs: list[dict[str, Any]] = []
    for item in raw_inputs:
        if not isinstance(item, dict):
            continue

        input_entry: dict[str, Any] = {}
        for key in (
            "name",
            "label",
            "type",
            "optional",
            "condition",
            "extensions",
            "format",
        ):
            if key in item:
                input_entry[key] = item[key]

        if "name" in input_entry:
            inputs.append(input_entry)

    return inputs


def _extract_outputs(raw_outputs: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_outputs, list):
        return []

    outputs: list[dict[str, Any]] = []
    for item in raw_outputs:
        if not isinstance(item, dict):
            continue

        output_entry: dict[str, Any] = {}
        for key in (
            "name",
            "label",
            "type",
            "format",
            "default_format",
            "discovered_formats",
            "extensions",
        ):
            if key in item:
                output_entry[key] = item[key]

        if "name" in output_entry:
            outputs.append(output_entry)

    return outputs


def _extract_categories(record: dict[str, Any]) -> list[str]:
    categories = record.get("categories")
    if isinstance(categories, list):
        return [str(item) for item in categories if isinstance(item, str) and item]

    enrichment = record.get("enrichment")
    if isinstance(enrichment, dict):
        domains = enrichment.get("scientific_domains")
        if isinstance(domains, list):
            return [str(item) for item in domains if isinstance(item, str) and item]

    return []


def build_metadata(input_path: Path, output_path: Path) -> tuple[int, int, int, int]:
    processed = 0
    stored = 0
    parse_errors = 0
    skipped = 0

    metadata: dict[str, dict[str, Any]] = {}

    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                skipped += 1
                continue

            processed += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                continue

            if not isinstance(record, dict):
                skipped += 1
                continue

            tool_id = record.get("tool_id")
            if not isinstance(tool_id, str) or not tool_id:
                skipped += 1
                continue

            metadata[tool_id] = {
                "tool_id": tool_id,
                "name": record.get("name", ""),
                "description": record.get("description", ""),
                "categories": _extract_categories(record),
                "inputs": _extract_inputs(record.get("inputs")),
                "outputs": _extract_outputs(record.get("outputs")),
            }
            stored += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    return processed, stored, skipped, parse_errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build compact deterministic tool metadata for validation."
    )
    parser.add_argument(
        "--input",
        default="data/tools_enriched.jsonl",
        help="Path to tools_enriched.jsonl",
    )
    parser.add_argument(
        "--output",
        default="outputs/tool_metadata.json",
        help="Path to output metadata JSON",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    input_path = (root / args.input).resolve()
    output_path = (root / args.output).resolve()

    processed, stored, skipped, parse_errors = build_metadata(input_path, output_path)

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Processed records: {processed}")
    print(f"Stored tools: {stored}")
    print(f"Skipped records: {skipped}")
    print(f"Parse errors: {parse_errors}")


if __name__ == "__main__":
    main()

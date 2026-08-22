from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import CheckStatus, ValidationError


class ToolMetadataStore:
    def __init__(self, metadata_path: str | Path):
        self.metadata_path = Path(metadata_path)
        payload = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("tool metadata must be a JSON object keyed by tool_id")
        self._tools: dict[str, dict[str, Any]] = {
            str(tool_id): tool for tool_id, tool in payload.items() if isinstance(tool, dict)
        }

    def has_tool(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def get_tool(self, tool_id: str) -> dict[str, Any] | None:
        return self._tools.get(tool_id)

    def get_input_names(self, tool_id: str) -> set[str]:
        tool = self.get_tool(tool_id) or {}
        return {
            str(item.get("name"))
            for item in tool.get("inputs", [])
            if isinstance(item, dict) and item.get("name")
        }

    def get_output_names(self, tool_id: str) -> set[str]:
        tool = self.get_tool(tool_id) or {}
        return {
            str(item.get("name"))
            for item in tool.get("outputs", [])
            if isinstance(item, dict) and item.get("name")
        }

    def get_required_unconditioned_inputs(self, tool_id: str) -> set[str]:
        tool = self.get_tool(tool_id) or {}
        required: set[str] = set()
        for item in tool.get("inputs", []):
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            if not isinstance(name, str) or not name:
                continue

            optional = bool(item.get("optional", False))
            condition = item.get("condition")
            has_condition = isinstance(condition, str) and condition.strip() != ""

            # Phase-1 rule: only unconditioned non-optional params are hard required.
            if (not optional) and (not has_condition):
                required.add(name)

        return required

    def get_output_formats(self, tool_id: str, output_name: str) -> set[str]:
        tool = self.get_tool(tool_id) or {}
        formats: set[str] = set()

        for item in tool.get("outputs", []):
            if not isinstance(item, dict):
                continue
            if item.get("name") != output_name:
                continue

            for key in ("format", "default_format"):
                value = item.get(key)
                if isinstance(value, str) and value:
                    formats.add(value)

            discovered = item.get("discovered_formats")
            if isinstance(discovered, list):
                formats.update(str(fmt) for fmt in discovered if isinstance(fmt, str) and fmt)

        return formats

    def get_input_formats(self, tool_id: str, input_name: str) -> set[str]:
        tool = self.get_tool(tool_id) or {}
        formats: set[str] = set()

        for item in tool.get("inputs", []):
            if not isinstance(item, dict):
                continue
            if item.get("name") != input_name:
                continue

            extensions = item.get("extensions")
            if isinstance(extensions, list):
                formats.update(str(ext) for ext in extensions if isinstance(ext, str) and ext)

            value = item.get("format")
            if isinstance(value, str) and value:
                formats.add(value)

        return formats


def _extract_named_fields(value: Any) -> set[str]:
    if isinstance(value, list):
        names: set[str] = set()
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                names.add(item["name"])
            elif isinstance(item, str):
                names.add(item)
        return names

    if isinstance(value, dict):
        return {str(key) for key in value.keys()}

    return set()


def validate_tools_exist(
    nodes: list[dict[str, Any]],
    metadata: ToolMetadataStore,
) -> tuple[CheckStatus, list[ValidationError]]:
    errors: list[ValidationError] = []
    for node in nodes:
        node_id = str(node.get("id", ""))
        tool_id = node.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id:
            continue

        if not metadata.has_tool(tool_id):
            errors.append(
                ValidationError(
                    type="UNKNOWN_TOOL",
                    tool_id=tool_id,
                    node_id=node_id or None,
                    message="Tool does not exist in the tool metadata.",
                )
            )

    if errors:
        return "FAIL", errors
    return "PASS", errors


def validate_node_inputs(
    nodes: list[dict[str, Any]],
    metadata: ToolMetadataStore,
) -> tuple[CheckStatus, list[ValidationError]]:
    errors: list[ValidationError] = []
    unknown_seen = False

    for node in nodes:
        node_id = str(node.get("id", ""))
        tool_id = node.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id or not metadata.has_tool(tool_id):
            continue

        known_inputs = metadata.get_input_names(tool_id)
        required_inputs = metadata.get_required_unconditioned_inputs(tool_id)

        if "inputs" not in node:
            if required_inputs:
                unknown_seen = True
            continue

        provided_inputs = _extract_named_fields(node.get("inputs"))

        invalid_inputs = sorted(provided_inputs - known_inputs)
        for input_name in invalid_inputs:
            errors.append(
                ValidationError(
                    type="INVALID_INPUT_PARAMETER",
                    tool_id=tool_id,
                    node_id=node_id or None,
                    message=f"Input parameter '{input_name}' is not defined for this tool.",
                )
            )

        missing_required = sorted(required_inputs - provided_inputs)
        for input_name in missing_required:
            errors.append(
                ValidationError(
                    type="MISSING_REQUIRED_INPUT",
                    tool_id=tool_id,
                    node_id=node_id or None,
                    message=f"Required input '{input_name}' is missing.",
                )
            )

    if errors:
        return "FAIL", errors
    if unknown_seen:
        return "UNKNOWN", errors
    return "PASS", errors


def validate_node_outputs(
    nodes: list[dict[str, Any]],
    metadata: ToolMetadataStore,
) -> tuple[CheckStatus, list[ValidationError]]:
    errors: list[ValidationError] = []
    unknown_seen = False

    for node in nodes:
        node_id = str(node.get("id", ""))
        tool_id = node.get("tool_id")
        if not isinstance(tool_id, str) or not tool_id or not metadata.has_tool(tool_id):
            continue

        if "outputs" not in node:
            unknown_seen = True
            continue

        known_outputs = metadata.get_output_names(tool_id)
        provided_outputs = _extract_named_fields(node.get("outputs"))
        invalid_outputs = sorted(provided_outputs - known_outputs)

        for output_name in invalid_outputs:
            errors.append(
                ValidationError(
                    type="UNKNOWN_OUTPUT",
                    tool_id=tool_id,
                    node_id=node_id or None,
                    message=f"Output '{output_name}' is not defined for this tool.",
                )
            )

    if errors:
        return "FAIL", errors
    if unknown_seen:
        return "UNKNOWN", errors
    return "PASS", errors

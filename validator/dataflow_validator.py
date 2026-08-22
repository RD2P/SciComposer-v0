from __future__ import annotations

from typing import Any

from .schemas import CheckStatus, ValidationError
from .tool_validator import ToolMetadataStore


def _are_formats_compatible(output_formats: set[str], input_formats: set[str]) -> CheckStatus:
    if not output_formats or not input_formats:
        return "UNKNOWN"

    if output_formats.intersection(input_formats):
        return "PASS"

    return "FAIL"


def validate_data_flow(
    nodes_by_id: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    metadata: ToolMetadataStore,
) -> tuple[CheckStatus, list[ValidationError]]:
    errors: list[ValidationError] = []
    unknown_seen = False

    for edge_index, edge in enumerate(edges):
        source_id = edge.get("from")
        target_id = edge.get("to")

        if not isinstance(source_id, str) or source_id not in nodes_by_id:
            errors.append(
                ValidationError(
                    type="NONEXISTENT_CONNECTION_SOURCE",
                    node_id=source_id if isinstance(source_id, str) else None,
                    edge_index=edge_index,
                    message="Connection source node does not exist.",
                )
            )
            continue

        if not isinstance(target_id, str) or target_id not in nodes_by_id:
            errors.append(
                ValidationError(
                    type="NONEXISTENT_CONNECTION_TARGET",
                    node_id=target_id if isinstance(target_id, str) else None,
                    edge_index=edge_index,
                    message="Connection target node does not exist.",
                )
            )
            continue

        source = nodes_by_id[source_id]
        target = nodes_by_id[target_id]
        source_tool = source.get("tool_id")
        target_tool = target.get("tool_id")

        if not isinstance(source_tool, str) or not metadata.has_tool(source_tool):
            continue
        if not isinstance(target_tool, str) or not metadata.has_tool(target_tool):
            continue

        source_output = edge.get("from_output")
        target_input = edge.get("to_input")

        if not isinstance(source_output, str) or not isinstance(target_input, str):
            unknown_seen = True
            continue

        source_outputs = metadata.get_output_names(source_tool)
        if source_output not in source_outputs:
            errors.append(
                ValidationError(
                    type="UNKNOWN_OUTPUT",
                    tool_id=source_tool,
                    node_id=source_id,
                    edge_index=edge_index,
                    message=f"Output '{source_output}' does not exist on source tool.",
                )
            )
            continue

        target_inputs = metadata.get_input_names(target_tool)
        if target_input not in target_inputs:
            errors.append(
                ValidationError(
                    type="UNKNOWN_INPUT",
                    tool_id=target_tool,
                    node_id=target_id,
                    edge_index=edge_index,
                    message=f"Input '{target_input}' does not exist on target tool.",
                )
            )
            continue

        output_formats = metadata.get_output_formats(source_tool, source_output)
        input_formats = metadata.get_input_formats(target_tool, target_input)

        compatibility = _are_formats_compatible(output_formats, input_formats)
        if compatibility == "UNKNOWN":
            unknown_seen = True
            continue
        if compatibility == "FAIL":
            errors.append(
                ValidationError(
                    type="DATA_TYPE_MISMATCH",
                    edge_index=edge_index,
                    message=(
                        f"Data type mismatch between {source_id}.{source_output} and "
                        f"{target_id}.{target_input}."
                    ),
                    details={
                        "source_formats": sorted(output_formats),
                        "target_formats": sorted(input_formats),
                    },
                )
            )

    if errors:
        return "FAIL", errors
    if unknown_seen:
        return "UNKNOWN", errors
    return "PASS", errors

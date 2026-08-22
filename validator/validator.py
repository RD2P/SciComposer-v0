from __future__ import annotations

from pathlib import Path
from typing import Any

from .dataflow_validator import validate_data_flow
from .schemas import CheckStatus, ValidationError, ValidationReport
from .tool_validator import (
    ToolMetadataStore,
    validate_node_inputs,
    validate_node_outputs,
    validate_tools_exist,
)


class DeterministicWorkflowValidator:
    def __init__(self, metadata_path: str | Path | None = None):
        root = Path(__file__).resolve().parent.parent
        resolved_path = Path(metadata_path) if metadata_path else root / "data" / "tool_metadata.json"
        self.metadata = ToolMetadataStore(resolved_path)

    def validate(self, workflow_graph: dict[str, Any]) -> dict[str, Any]:
        checks: dict[str, CheckStatus] = {
            "schema": "UNKNOWN",
            "tools_exist": "UNKNOWN",
            "inputs_valid": "UNKNOWN",
            "outputs_valid": "UNKNOWN",
            "data_flow_valid": "UNKNOWN",
        }
        errors: list[ValidationError] = []

        schema_status, schema_errors, nodes, edges, nodes_by_id = self._validate_schema(workflow_graph)
        checks["schema"] = schema_status
        errors.extend(schema_errors)

        tools_status, tools_errors = validate_tools_exist(nodes, self.metadata)
        checks["tools_exist"] = tools_status
        errors.extend(tools_errors)

        inputs_status, input_errors = validate_node_inputs(nodes, self.metadata)
        checks["inputs_valid"] = inputs_status
        errors.extend(input_errors)

        outputs_status, output_errors = validate_node_outputs(nodes, self.metadata)
        checks["outputs_valid"] = outputs_status
        errors.extend(output_errors)

        flow_status, flow_errors = validate_data_flow(nodes_by_id, edges, self.metadata)
        checks["data_flow_valid"] = flow_status
        errors.extend(flow_errors)

        valid = all(status != "FAIL" for status in checks.values())
        return ValidationReport(valid=valid, errors=errors, checks=checks).to_dict()

    def _validate_schema(
        self, workflow_graph: dict[str, Any]
    ) -> tuple[CheckStatus, list[ValidationError], list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
        errors: list[ValidationError] = []

        if not isinstance(workflow_graph, dict):
            errors.append(
                ValidationError(
                    type="INVALID_WORKFLOW",
                    message="Workflow graph must be a JSON object.",
                )
            )
            return "FAIL", errors, [], [], {}

        raw_nodes = workflow_graph.get("nodes", [])
        raw_edges = workflow_graph.get("edges", [])

        if not isinstance(raw_nodes, list):
            errors.append(
                ValidationError(
                    type="INVALID_SCHEMA",
                    message="Workflow 'nodes' must be a list.",
                )
            )
            raw_nodes = []

        if not isinstance(raw_edges, list):
            errors.append(
                ValidationError(
                    type="INVALID_SCHEMA",
                    message="Workflow 'edges' must be a list.",
                )
            )
            raw_edges = []

        nodes: list[dict[str, Any]] = []
        node_ids: set[str] = set()
        nodes_by_id: dict[str, dict[str, Any]] = {}

        for index, node in enumerate(raw_nodes):
            if not isinstance(node, dict):
                errors.append(
                    ValidationError(
                        type="INVALID_NODE",
                        message=f"Node at index {index} must be an object.",
                    )
                )
                continue

            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                errors.append(
                    ValidationError(
                        type="MISSING_NODE_ID",
                        message=f"Node at index {index} is missing a valid 'id'.",
                    )
                )
                continue

            if node_id in node_ids:
                errors.append(
                    ValidationError(
                        type="DUPLICATE_NODE_ID",
                        node_id=node_id,
                        message=f"Duplicate node id '{node_id}'.",
                    )
                )
                continue

            tool_id = node.get("tool_id")
            if not isinstance(tool_id, str) or not tool_id:
                errors.append(
                    ValidationError(
                        type="MISSING_TOOL_ID",
                        node_id=node_id,
                        message=f"Node '{node_id}' is missing a valid 'tool_id'.",
                    )
                )

            node_ids.add(node_id)
            nodes.append(node)
            nodes_by_id[node_id] = node

        edges: list[dict[str, Any]] = []
        for edge_index, edge in enumerate(raw_edges):
            if not isinstance(edge, dict):
                errors.append(
                    ValidationError(
                        type="INVALID_EDGE",
                        edge_index=edge_index,
                        message="Edge must be an object with 'from' and 'to'.",
                    )
                )
                continue

            source = edge.get("from")
            target = edge.get("to")
            if not isinstance(source, str) or not source or not isinstance(target, str) or not target:
                errors.append(
                    ValidationError(
                        type="INVALID_EDGE",
                        edge_index=edge_index,
                        message="Edge must include non-empty string 'from' and 'to' fields.",
                    )
                )
                continue

            if source not in node_ids or target not in node_ids:
                errors.append(
                    ValidationError(
                        type="UNKNOWN_NODE_REFERENCE",
                        edge_index=edge_index,
                        message="Edge references a node that does not exist.",
                    )
                )

            edges.append(edge)

        if self._has_cycle(node_ids=node_ids, edges=edges):
            errors.append(
                ValidationError(
                    type="GRAPH_HAS_CYCLE",
                    message="Workflow graph contains a cycle and must be a DAG.",
                )
            )

        status: CheckStatus = "FAIL" if errors else "PASS"
        return status, errors, nodes, edges, nodes_by_id

    @staticmethod
    def _has_cycle(node_ids: set[str], edges: list[dict[str, Any]]) -> bool:
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in edges:
            source = edge.get("from")
            target = edge.get("to")
            if isinstance(source, str) and isinstance(target, str) and source in adjacency:
                adjacency[source].append(target)

        temp: set[str] = set()
        perm: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in perm:
                return False
            if node_id in temp:
                return True

            temp.add(node_id)
            for neighbor in adjacency.get(node_id, []):
                if neighbor in adjacency and visit(neighbor):
                    return True
            temp.remove(node_id)
            perm.add(node_id)
            return False

        for node_id in adjacency:
            if visit(node_id):
                return True

        return False

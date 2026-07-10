from __future__ import annotations

from typing import Any


class ValidatorAgent:
    def validate(
        self,
        workflow_graph: dict[str, Any],
        workflow_spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        nodes = workflow_graph.get("nodes", [])
        edges = workflow_graph.get("edges", [])

        issues: list[str] = []

        if not nodes:
            issues.append("Workflow graph has no nodes.")

        node_tools = {node.get("tool") for node in nodes if isinstance(node, dict)}
        if not edges and len(nodes) > 1:
            issues.append("Workflow graph has no edges.")

        for left, right in edges:
            if left not in node_tools:
                issues.append(f"Unknown source tool in edge: {left}")
            if right not in node_tools:
                issues.append(f"Unknown target tool in edge: {right}")

        valid = len(issues) == 0

        return {
            "valid": valid,
            "issues": issues,
            "summary": "Workflow is valid." if valid else "Workflow has validation issues.",
            "workflow_spec": workflow_spec or {},
            "corrected_workflow": workflow_graph,
        }
from __future__ import annotations

from typing import Any


class BuilderAgent:
    def build(
        self,
        candidate_tools: list[dict[str, Any]],
        workflow_examples: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        nodes = []
        seen = set()

        for item in candidate_tools:
            tool_name = item.get("tool", "")
            if tool_name and tool_name not in seen:
                seen.add(tool_name)
                nodes.append(
                    {
                        "stage": item.get("stage", ""),
                        "tool": tool_name,
                        "tool_id": item.get("tool_id", tool_name.lower()),
                    }
                )

        edges: list[tuple[str, str]] = []
        for left, right in zip(nodes, nodes[1:]):
            edges.append((left["tool"], right["tool"]))

        return {
            "nodes": nodes,
            "edges": edges,
            "examples_used": [wf.get("name", "") for wf in (workflow_examples or [])],
        }
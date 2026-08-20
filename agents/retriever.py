from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from utils.model_loader import load_embedding_model


@dataclass(frozen=True)
class GalaxyTool:
    tool_id: str
    name: str
    description: str = ""
    inputs: list[str] | None = None
    outputs: list[str] | None = None
    tags: list[str] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "GalaxyTool":
        return GalaxyTool(
            tool_id=data.get("tool_id", data.get("name", "")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            tags=data.get("tags", []),
        )


class RetrieverAgent:
    def __init__(
        self,
        tools_index_path: str | Path | None = None,
        tools_metadata_path: str | Path | None = None,
        workflows_index_path: str | Path | None = None,
        workflows_metadata_path: str | Path | None = None,
        model: Any | None = None,
        model_name: str | None = None,
    ) -> None:
        data_dir = Path(__file__).resolve().parent.parent / "data"
        self._tools = self._load_bundle(
            Path(tools_index_path) if tools_index_path else data_dir / "tools.faiss",
            Path(tools_metadata_path)
            if tools_metadata_path
            else data_dir / "tools_index_metadata.json",
        )
        self._workflows = self._load_bundle(
            Path(workflows_index_path)
            if workflows_index_path
            else data_dir / "workflows.faiss",
            Path(workflows_metadata_path)
            if workflows_metadata_path
            else data_dir / "workflows_index_metadata.json",
        )

        if self._tools["model"] != self._workflows["model"]:
            raise ValueError("Tool and workflow indexes use different embedding models")
        if self._tools["dimension"] != self._workflows["dimension"]:
            raise ValueError("Tool and workflow indexes use different dimensions")

        expected_model = self._tools["model"]
        if model_name is not None and model_name != expected_model:
            raise ValueError(
                f"Requested model {model_name!r} does not match index model {expected_model!r}"
            )
        self.model = model or load_embedding_model(expected_model=expected_model)

    @staticmethod
    def _load_bundle(
        index_path: Path,
        metadata_path: Path,
    ) -> dict[str, Any]:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        index = faiss.read_index(str(index_path))
        dimension = int(metadata["dimension"])
        if index.d != dimension:
            raise ValueError(
                f"Index dimension {index.d} does not match metadata dimension {dimension}"
            )

        records = metadata.get("tools", metadata.get("workflows", []))
        by_index = {int(record["index"]): record for record in records}
        return {
            "index": index,
            "model": metadata["model"],
            "dimension": dimension,
            "records": by_index,
        }

    def _search(self, bundle: dict[str, Any], query: str, top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []
        query_vector = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )
        query_vector = np.asarray(query_vector, dtype=np.float32)
        scores, indexes = bundle["index"].search(
            query_vector, min(top_k, bundle["index"].ntotal)
        )

        results = []
        for score, index in zip(scores[0], indexes[0]):
            record = bundle["records"].get(int(index))
            if record is not None:
                results.append({**record, "score": float(score)})
        return results

    def retrieve_tools(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self._search(self._tools, query, top_k)

    def retrieve_workflows(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self._search(self._workflows, query, top_k)

    def retrieve(self, workflow_spec: dict[str, Any]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for stage in workflow_spec.get("stages", []):
            stage_name = stage.get("name", "") if isinstance(stage, dict) else str(stage)
            description = stage.get("description", "") if isinstance(stage, dict) else ""
            query = f"{workflow_spec.get('goal', '')}. {stage_name}: {description}"
            for tool in self.retrieve_tools(query):
                results.append({**tool, "stage": stage_name, "tool": tool.get("name", "")})
        return sorted(results, key=lambda result: result["score"], reverse=True)

    def retrieve_plan_tools(
        self, workflow_spec: dict[str, Any], top_k: int = 3
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        best_by_tool: dict[str, dict[str, Any]] = {}
        for result in self.retrieve(workflow_spec):
            tool_key = result.get("tool_id", result.get("name", ""))
            if tool_key not in best_by_tool or result["score"] > best_by_tool[tool_key]["score"]:
                best_by_tool[tool_key] = result
        return sorted(
            best_by_tool.values(), key=lambda result: result["score"], reverse=True
        )[:top_k]
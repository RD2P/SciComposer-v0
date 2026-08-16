from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    def __init__(self, tools_path: str | Path | None = None) -> None:
        self.tools_path = Path(tools_path) if tools_path else None
        self.tools = self._load_tools()

    def _load_tools(self) -> list[GalaxyTool]:
        if not self.tools_path or not self.tools_path.exists():
            return self._default_tools()

        if self.tools_path.is_file():
            raw = json.loads(self.tools_path.read_text(encoding="utf-8"))
            return [GalaxyTool.from_dict(item) for item in raw]

        return self._default_tools()

    def _default_tools(self) -> list[GalaxyTool]:
        return [
            GalaxyTool(
                tool_id="fastqc",
                name="FastQC",
                description="Quality control for raw sequencing reads",
                inputs=["fastq"],
                outputs=["qc_report"],
                tags=["rna-seq", "qc", "fastq"],
            ),
            GalaxyTool(
                tool_id="trimmomatic",
                name="Trimmomatic",
                description="Read trimming and adapter removal",
                inputs=["fastq"],
                outputs=["trimmed_fastq"],
                tags=["rna-seq", "preprocessing", "fastq"],
            ),
            GalaxyTool(
                tool_id="hisat2",
                name="HISAT2",
                description="Spliced alignment for RNA-seq reads",
                inputs=["fastq", "reference_genome"],
                outputs=["bam"],
                tags=["rna-seq", "alignment"],
            ),
            GalaxyTool(
                tool_id="featurecounts",
                name="FeatureCounts",
                description="Count reads overlapping genomic features",
                inputs=["bam", "annotation"],
                outputs=["count_table"],
                tags=["rna-seq", "quantification"],
            ),
            GalaxyTool(
                tool_id="deseq2",
                name="DESeq2",
                description="Differential expression analysis",
                inputs=["count_table"],
                outputs=["differential_expression_table"],
                tags=["rna-seq", "expression"],
            ),
            GalaxyTool(
                tool_id="volcano_plot",
                name="Volcano Plot",
                description="Create differential expression visualization",
                inputs=["differential_expression_table"],
                outputs=["plot"],
                tags=["rna-seq", "reporting", "visualization"],
            ),
        ]

    def retrieve(self, workflow_spec: dict[str, Any]) -> list[dict[str, Any]]:
        stages = workflow_spec.get("stages", [])

        results: list[dict[str, Any]] = []
        for stage in stages:
            matches = [
                tool
                for tool in self.tools
                if stage in (tool.tags or [])
            ]
            if not matches:
                matches = self.tools[:1]
            for tool in matches[:3]:
                results.append(
                    {
                        "stage": stage,
                        "tool_id": tool.tool_id,
                        "tool": tool.name,
                        "description": tool.description,
                    }
                )
        return results
"""Transform repository analysis and graph data into a project summary."""

from app.schemas.repositories import (
    ArchitectureGraph,
    RepositoryAnalyzeResponse,
    RepositorySummary,
)


class RepositorySummaryService:
    """Build frontend-ready counts from already-produced backend metadata."""

    def build_summary(
        self,
        analysis: RepositoryAnalyzeResponse,
        graph: ArchitectureGraph,
    ) -> RepositorySummary:
        """Return direct analysis and graph counts without new inference."""
        return RepositorySummary(
            total_java_files=analysis.total_java_files,
            parsed_successfully=analysis.parsed_successfully,
            parse_failures=analysis.parse_failures,
            class_count=len(analysis.classes),
            controller_count=len(analysis.controllers),
            service_count=len(analysis.services),
            repository_count=len(analysis.repositories),
            endpoint_count=len(analysis.endpoints),
            dependency_count=len(analysis.dependencies),
            graph_node_count=len(graph.nodes),
            graph_edge_count=len(graph.edges),
        )

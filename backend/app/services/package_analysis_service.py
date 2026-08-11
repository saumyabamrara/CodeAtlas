"""Transform repository analysis metadata into package-level architecture."""

from collections import Counter
from collections.abc import Iterable
from typing import Protocol

from app.schemas.repositories import (
    PackageAnalysisResponse,
    PackageDependencyMetadata,
    PackageMetadata,
    RepositoryAnalyzeResponse,
)
from app.services.architecture_graph_service import ArchitectureGraphService
from app.services.source_scope_service import SourceScope


class _ScopedPackageMetadata(Protocol):
    package_name: str
    scope: SourceScope


class PackageAnalysisService:
    """Build package counts and production package dependencies."""

    def __init__(self, graph_service: ArchitectureGraphService) -> None:
        self._graph_service = graph_service

    def build_package_analysis(
        self,
        analysis: RepositoryAnalyzeResponse,
    ) -> PackageAnalysisResponse:
        """Derive package metadata from one completed repository analysis."""
        package_names = {
            metadata.package_name
            for collection in (
                analysis.classes,
                analysis.controllers,
                analysis.services,
                analysis.repositories,
            )
            for metadata in collection
        }
        packages = [
            PackageMetadata(
                package_name=package_name,
                production_class_count=self._count_scoped(
                    analysis.classes, package_name, "production"
                ),
                test_class_count=self._count_scoped(
                    analysis.classes, package_name, "test"
                ),
                production_controller_count=self._count_scoped(
                    analysis.controllers, package_name, "production"
                ),
                test_controller_count=self._count_scoped(
                    analysis.controllers, package_name, "test"
                ),
                production_service_count=self._count_scoped(
                    analysis.services, package_name, "production"
                ),
                test_service_count=self._count_scoped(
                    analysis.services, package_name, "test"
                ),
                production_repository_count=self._count_scoped(
                    analysis.repositories, package_name, "production"
                ),
                test_repository_count=self._count_scoped(
                    analysis.repositories, package_name, "test"
                ),
            )
            for package_name in sorted(package_names)
        ]

        graph = self._graph_service.build_graph(analysis)
        packages_by_node_id = {node.id: node.package_name for node in graph.nodes}
        dependency_counts = Counter(
            (packages_by_node_id[edge.source], packages_by_node_id[edge.target])
            for edge in graph.edges
            if packages_by_node_id[edge.source] != packages_by_node_id[edge.target]
        )
        dependencies = [
            PackageDependencyMetadata(
                source_package=source_package,
                target_package=target_package,
                dependency_count=dependency_count,
            )
            for (source_package, target_package), dependency_count in sorted(
                dependency_counts.items()
            )
        ]
        return PackageAnalysisResponse(packages=packages, dependencies=dependencies)

    @staticmethod
    def _count_scoped(
        collection: Iterable[_ScopedPackageMetadata],
        package_name: str,
        scope: SourceScope,
    ) -> int:
        return sum(
            metadata.package_name == package_name and metadata.scope == scope
            for metadata in collection
        )

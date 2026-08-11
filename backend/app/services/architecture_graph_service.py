"""Transform repository analysis metadata into an architecture graph."""

from collections import defaultdict

from app.schemas.repositories import (
    ArchitectureGraph,
    GraphEdge,
    GraphNode,
    RepositoryAnalyzeResponse,
)

_DEPENDS_ON = "DEPENDS_ON"
_ROLE_PRIORITY = {
    "class": 0,
    "repository": 1,
    "service": 2,
    "controller": 3,
}


class ArchitectureGraphService:
    """Build a canonical class-level graph from completed analysis metadata."""

    def build_graph(self, analysis: RepositoryAnalyzeResponse) -> ArchitectureGraph:
        """Return graph nodes and resolved dependency edges without re-analyzing files."""
        roles = self._class_roles(analysis)
        nodes_by_id: dict[str, GraphNode] = {}
        for metadata in analysis.classes:
            if metadata.scope != "production":
                continue
            node_id = self._node_id(
                metadata.package_name,
                metadata.qualified_class_name,
            )
            nodes_by_id.setdefault(
                node_id,
                GraphNode(
                    id=node_id,
                    label=metadata.class_name,
                    node_type=roles.get(node_id, "class"),
                    file_path=metadata.file_path,
                    package_name=metadata.package_name,
                    qualified_class_name=metadata.qualified_class_name,
                ),
            )
        node_ids_by_simple_name: dict[str, list[str]] = defaultdict(list)
        for node in nodes_by_id.values():
            node_ids_by_simple_name[node.label].append(node.id)

        edge_keys: set[tuple[str, str, str]] = set()
        for dependency in analysis.dependencies:
            if dependency.source_scope != "production":
                continue
            source_id = self._node_id(
                dependency.package_name,
                dependency.source_qualified_class_name,
            )
            if source_id not in nodes_by_id:
                continue
            target_name = self._declared_simple_type(dependency.target_type)
            target_ids = node_ids_by_simple_name.get(target_name, [])
            if len(target_ids) != 1:
                continue
            edge_keys.add((source_id, target_ids[0], _DEPENDS_ON))

        return ArchitectureGraph(
            nodes=list(nodes_by_id.values()),
            edges=[
                GraphEdge(source=source, target=target, edge_type=edge_type)
                for source, target, edge_type in sorted(edge_keys)
            ],
        )

    @staticmethod
    def _class_roles(analysis: RepositoryAnalyzeResponse) -> dict[str, str]:
        roles: dict[str, str] = {}
        role_collections = (
            ("repository", analysis.repositories),
            ("service", analysis.services),
            ("controller", analysis.controllers),
        )
        for role, collection in role_collections:
            for metadata in collection:
                node_id = ArchitectureGraphService._node_id(
                    metadata.package_name,
                    metadata.qualified_class_name,
                )
                current_role = roles.get(node_id, "class")
                if _ROLE_PRIORITY[role] > _ROLE_PRIORITY[current_role]:
                    roles[node_id] = role
        return roles

    @staticmethod
    def _node_id(package_name: str, qualified_class_name: str) -> str:
        if package_name == "":
            return qualified_class_name
        return f"{package_name}.{qualified_class_name}"

    @staticmethod
    def _declared_simple_type(target_type: str) -> str:
        without_generics = target_type.split("<", maxsplit=1)[0].strip()
        return without_generics.rsplit(".", maxsplit=1)[-1]

export interface RepositoryAnalyzeRequest {
  local_path: string;
}

export interface RepositorySummary {
  total_java_files: number;
  parsed_successfully: number;
  parse_failures: number;
  class_count: number;
  controller_count: number;
  service_count: number;
  repository_count: number;
  endpoint_count: number;
  dependency_count: number;
  graph_node_count: number;
  graph_edge_count: number;
  production_java_files: number;
  test_java_files: number;
  production_class_count: number;
  test_class_count: number;
  production_dependency_count: number;
  test_dependency_count: number;
}

export interface PackageMetadata {
  package_name: string;
  production_class_count: number;
  test_class_count: number;
  production_controller_count: number;
  test_controller_count: number;
  production_service_count: number;
  test_service_count: number;
  production_repository_count: number;
  test_repository_count: number;
}

export interface PackageDependencyMetadata {
  source_package: string;
  target_package: string;
  dependency_count: number;
}

export interface PackageAnalysisResponse {
  packages: PackageMetadata[];
  dependencies: PackageDependencyMetadata[];
}

export type GraphNodeType = 'class' | 'controller' | 'service' | 'repository';

export interface GraphNode {
  id: string;
  label: string;
  node_type: GraphNodeType;
  file_path: string;
  package_name: string;
  qualified_class_name: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  edge_type: 'DEPENDS_ON';
}

export interface ArchitectureGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ComponentMetadata {
  class_name: string;
  package_name: string;
  qualified_class_name: string;
  scope: 'production' | 'test';
}

export interface RepositoryAnalysis {
  controllers: ComponentMetadata[];
  repositories: ComponentMetadata[];
}

export interface DashboardAnalysis {
  summary: RepositorySummary;
  packageAnalysis: PackageAnalysisResponse;
  repositoryAnalysis: RepositoryAnalysis;
  architectureGraph: ArchitectureGraphResponse;
}

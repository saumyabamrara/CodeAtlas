import type {
  DashboardAnalysis,
  RepositoryAnalyzeRequest,
  UnifiedRepositoryAnalysisResponse,
} from '../types/api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
);
const ANALYSIS_ERROR =
  'Could not analyze this repository. Make sure the CodeAtlas backend is running and the repository path is valid.';
const GRAPH_ERROR = 'Architecture graph could not be loaded.';

async function readError(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json();
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      const detail = (payload as { detail: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
    }
  } catch {
    // Use the friendly fallback below when the backend did not return JSON.
  }
  return ANALYSIS_ERROR;
}

async function post<T>(
  path: string,
  request: RepositoryAnalyzeRequest,
  errorFallback?: string,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(errorFallback ?? ANALYSIS_ERROR);
  }

  if (!response.ok) {
    const message = await readError(response);
    throw new Error(errorFallback ?? message);
  }
  return (await response.json()) as T;
}

export async function analyzeRepository(localPath: string): Promise<DashboardAnalysis> {
  const request: RepositoryAnalyzeRequest = { local_path: localPath };
  const response = await post<UnifiedRepositoryAnalysisResponse>(
    '/repositories/analyze-all',
    request,
  );

  if (
    typeof response.summary.total_java_files !== 'number' ||
    !Array.isArray(response.packages.packages) ||
    !Array.isArray(response.analysis.controllers) ||
    !Array.isArray(response.analysis.repositories)
  ) {
    throw new Error('The backend returned an unexpected analysis response.');
  }
  if (!Array.isArray(response.graph.nodes) || !Array.isArray(response.graph.edges)) {
    throw new Error(GRAPH_ERROR);
  }

  return {
    summary: response.summary,
    packageAnalysis: response.packages,
    repositoryAnalysis: response.analysis,
    architectureGraph: response.graph,
  };
}

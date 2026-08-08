import { useState } from 'react';

type CloneResponse = {
  repository_name: string;
  local_path: string;
  default_branch: string;
  clone_timestamp: string;
};

type InspectResponse = {
  repository_name: string;
  primary_language: string;
  build_tool: string;
  java_file_count: number;
  has_src_main_java: boolean;
  has_pom_xml: boolean;
  has_gradle_build: boolean;
  is_spring_boot: boolean;
  application_class: string | null;
  detection_reason: string;
};

type AnalyzeResponse = {
  total_java_files: number;
  parsed_successfully: number;
  parse_failures: number;
};

type ControllerMetadata = {
  class_name: string;
  package_name: string;
  fully_qualified_name: string;
  controller_type: string;
};

type ControllersResponse = {
  controller_count: number;
  controllers: ControllerMetadata[];
};

type AnalysisResult = {
  repositoryName: string;
  primaryLanguage: string;
  buildTool: string;
  javaFileCount: number;
  springBootStatus: string;
  parsedSuccessfully: number;
  parseFailures: number;
  controllerCount: number;
  controllerNames: string[];
  detectionReason: string;
};

async function getErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload === 'string') {
      return payload;
    }
    if (payload && typeof payload === 'object') {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
      if (detail && typeof detail === 'object') {
        const message = (detail as { message?: unknown }).message;
        if (typeof message === 'string') {
          return message;
        }
      }
    }
  } catch {
    // Ignore JSON parse issues and fall back to the generic error.
  }
  return fallback;
}

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [status, setStatus] = useState('Awaiting repository URL');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const canAnalyze = repositoryUrl.trim().length > 0;

  const handleAnalyze = async () => {
    if (!canAnalyze) {
      setStatus('Enter a GitHub repository URL to continue.');
      setErrorMessage('No repository URL provided.');
      setAnalysisResult(null);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setAnalysisResult(null);
    setStatus('Cloning repository...');

    try {
      const cloneResponse = await fetch('http://localhost:8000/repositories/clone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repository_url: repositoryUrl.trim() }),
      });

      if (!cloneResponse.ok) {
        throw new Error(await getErrorMessage(cloneResponse, 'Repository cloning failed.'));
      }

      const cloneData = (await cloneResponse.json()) as CloneResponse;
      setStatus('Inspecting repository...');

      const inspectResponse = await fetch('http://localhost:8000/repositories/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ local_path: cloneData.local_path }),
      });

      if (!inspectResponse.ok) {
        throw new Error(await getErrorMessage(inspectResponse, 'Repository inspection failed.'));
      }

      const inspectData = (await inspectResponse.json()) as InspectResponse;
      setStatus('Analyzing Java files...');

      const analyzeResponse = await fetch('http://localhost:8000/repositories/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ local_path: cloneData.local_path }),
      });

      if (!analyzeResponse.ok) {
        throw new Error(await getErrorMessage(analyzeResponse, 'Repository analysis failed.'));
      }

      const analyzeData = (await analyzeResponse.json()) as AnalyzeResponse;
      setStatus('Extracting controllers...');

      const controllersResponse = await fetch('http://localhost:8000/repositories/controllers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ local_path: cloneData.local_path }),
      });

      if (!controllersResponse.ok) {
        throw new Error(await getErrorMessage(controllersResponse, 'Controller extraction failed.'));
      }

      const controllersData = (await controllersResponse.json()) as ControllersResponse;
      setAnalysisResult({
        repositoryName: inspectData.repository_name,
        primaryLanguage: inspectData.primary_language,
        buildTool: inspectData.build_tool,
        javaFileCount: inspectData.java_file_count,
        springBootStatus: inspectData.is_spring_boot ? 'Yes' : 'No',
        parsedSuccessfully: analyzeData.parsed_successfully,
        parseFailures: analyzeData.parse_failures,
        controllerCount: controllersData.controller_count,
        controllerNames: controllersData.controllers.map((controller) => controller.class_name),
        detectionReason: inspectData.detection_reason,
      });
      setStatus('Analysis complete.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unexpected error occurred.';
      setErrorMessage(message);
      setStatus('Analysis failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="hero-panel">
        <div>
          <p className="eyebrow">Developer tools</p>
          <h1>CodeAtlas</h1>
          <p className="hero-copy">
            Inspect GitHub repositories and surface architecture insights with a focused
            engineering workflow.
          </p>
        </div>
      </header>

      <main className="workspace-panel">
        <section className="card">
          <label className="input-label" htmlFor="repository-url">
            GitHub repository URL
          </label>
          <div className="input-row">
            <input
              id="repository-url"
              type="url"
              value={repositoryUrl}
              onChange={(event) => setRepositoryUrl(event.target.value)}
              placeholder="https://github.com/owner/repository"
            />
            <button type="button" onClick={handleAnalyze} disabled={!canAnalyze || isLoading}>
              {isLoading ? 'Analyzing…' : 'Analyze Repository'}
            </button>
          </div>

          <div className="status-area" aria-live="polite">
            <div className="status-pill">{isLoading ? 'Loading' : 'Ready'}</div>
            <p>{status}</p>
          </div>
        </section>

        <section className="card results-card">
          <div className="results-header">
            <h2>Analysis results</h2>
            <span className="results-badge">Live</span>
          </div>
          {errorMessage ? <div className="error-panel">{errorMessage}</div> : null}
          {analysisResult ? (
            <div className="result-grid">
              <div className="result-item">
                <span>Repository name</span>
                <strong>{analysisResult.repositoryName}</strong>
              </div>
              <div className="result-item">
                <span>Primary language</span>
                <strong>{analysisResult.primaryLanguage}</strong>
              </div>
              <div className="result-item">
                <span>Build tool</span>
                <strong>{analysisResult.buildTool}</strong>
              </div>
              <div className="result-item">
                <span>Java file count</span>
                <strong>{analysisResult.javaFileCount}</strong>
              </div>
              <div className="result-item">
                <span>Spring Boot</span>
                <strong>{analysisResult.springBootStatus}</strong>
              </div>
              <div className="result-item">
                <span>Parsed successfully</span>
                <strong>{analysisResult.parsedSuccessfully}</strong>
              </div>
              <div className="result-item">
                <span>Parse failures</span>
                <strong>{analysisResult.parseFailures}</strong>
              </div>
              <div className="result-item">
                <span>Controller count</span>
                <strong>{analysisResult.controllerCount}</strong>
              </div>
              <div className="result-item full-width">
                <span>Controller names</span>
                {analysisResult.controllerNames.length > 0 ? (
                  <ul className="controller-list">
                    {analysisResult.controllerNames.map((name) => (
                      <li key={name}>{name}</li>
                    ))}
                  </ul>
                ) : (
                  <strong>No controllers detected.</strong>
                )}
              </div>
              <div className="result-item full-width">
                <span>Detection details</span>
                <strong>{analysisResult.detectionReason}</strong>
              </div>
            </div>
          ) : (
            <p>Enter a GitHub repository URL and click Analyze Repository to inspect the backend response.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;

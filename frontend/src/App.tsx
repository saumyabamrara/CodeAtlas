import { useState } from 'react';

function App() {
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [status, setStatus] = useState('Awaiting repository URL');
  const [isLoading, setIsLoading] = useState(false);
  const [resultMessage, setResultMessage] = useState('No analysis run yet.');

  const canAnalyze = repositoryUrl.trim().length > 0;

  const handleAnalyze = () => {
    if (!canAnalyze) {
      setStatus('Enter a GitHub repository URL to continue.');
      setResultMessage('No repository URL provided.');
      return;
    }

    setIsLoading(true);
    setStatus('Preparing analysis request...');
    setResultMessage('Your repository URL is queued for the next integration step.');

    window.setTimeout(() => {
      setIsLoading(false);
      setStatus('Frontend foundation ready. Backend wiring pending.');
      setResultMessage('Analysis results will appear here once the integration is live.');
    }, 1200);
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
            <span className="results-badge">Coming next</span>
          </div>
          <p>{resultMessage}</p>
        </section>
      </main>
    </div>
  );
}

export default App;

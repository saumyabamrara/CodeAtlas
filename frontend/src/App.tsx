import { useState } from 'react';

import { ArchitectureGraph } from './components/ArchitectureGraph';
import { ArchitectureAssistant } from './components/ArchitectureAssistant';
import { ComponentList } from './components/ComponentList';
import { PackageTable } from './components/PackageTable';
import { RepositoryInput } from './components/RepositoryInput';
import { SourceBreakdown } from './components/SourceBreakdown';
import { StatCard } from './components/StatCard';
import { analyzeRepository } from './services/api';
import type { DashboardAnalysis } from './types/api';

const GENERIC_ERROR =
  'Could not analyze this repository. Make sure the CodeAtlas backend is running and the repository path is valid.';

function App() {
  const [activeView, setActiveView] = useState<'overview' | 'graph'>('overview');
  const [repositoryPath, setRepositoryPath] = useState('');
  const [result, setResult] = useState<DashboardAnalysis | null>(null);
  const [analyzedPath, setAnalyzedPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const handleAnalyze = async () => {
    const localPath = repositoryPath.trim();
    if (!localPath) {
      setError('Enter a local repository path before starting analysis.');
      setResult(null);
      return;
    }

    setLoading(true);
    setAssistantOpen(false);
    setError(null);
    setResult(null);
    try {
      const analysis = await analyzeRepository(localPath);
      setResult(analysis);
      setAnalyzedPath(localPath);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : GENERIC_ERROR);
    } finally {
      setLoading(false);
    }
  };

  const summary = result?.summary;

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="CodeAtlas home">
          <span className="brand-mark">CA</span>
          <span>CODEATLAS</span>
        </a>
        <span className="header-status"><span /> Backend-powered analysis</span>
      </header>

      <main>
        <section className="hero">
          <p className="eyebrow">Java repository architecture analyzer</p>
          <h1>Turn a Java codebase into an architecture overview.</h1>
          <p className="hero-copy">
            Analyze classes, Spring components, endpoints, dependencies, and package
            structure from one local repository path.
          </p>
        </section>

        <section className="analysis-console" aria-label="Repository analysis">
          <div className="console-titlebar">
            <span className="terminal-dot red" />
            <span className="terminal-dot amber" />
            <span className="terminal-dot green" />
            <code>codeatlas / analyze</code>
          </div>
          <RepositoryInput
            value={repositoryPath}
            loading={loading}
            onChange={setRepositoryPath}
            onSubmit={handleAnalyze}
          />
          {loading ? (
            <div className="loading-state" role="status" aria-live="polite">
              <span className="loading-spinner" />
              <div>
                <strong>Analyzing repository architecture...</strong>
                <p>Parsing Java metadata and assembling architecture views.</p>
              </div>
            </div>
          ) : null}
          {error ? <div className="error-panel" role="alert">{error}</div> : null}
        </section>

        <div
          className={
            result
              ? `analysis-layout${assistantOpen ? ' assistant-open' : ''}`
              : ''
          }
        >
        <div className="analysis-content">
        <div className="analysis-navigation">
        <nav className="view-tabs" aria-label="Analysis views">
          <button
            type="button"
            className={activeView === 'overview' ? 'active' : ''}
            onClick={() => setActiveView('overview')}
          >
            Overview
          </button>
          <button
            type="button"
            className={activeView === 'graph' ? 'active' : ''}
            onClick={() => setActiveView('graph')}
          >
            Architecture Graph
          </button>
        </nav>
        {result ? (
          <button
            type="button"
            className={`assistant-toggle${assistantOpen ? ' active' : ''}`}
            onClick={() => setAssistantOpen((open) => !open)}
            aria-expanded={assistantOpen}
            aria-controls="architecture-assistant"
          >
            <span>AI</span>
            {assistantOpen ? 'Hide AI' : 'Ask AI'}
          </button>
        ) : null}
        </div>

        {activeView === 'overview' && !result && !loading && !error ? (
          <section className="empty-state">
            <span className="empty-icon">{`{ }`}</span>
            <h2>Your architecture overview starts here</h2>
            <p>
              Enter a repository path above. CodeAtlas will send it to the backend and
              present the existing static-analysis results in this dashboard.
            </p>
          </section>
        ) : null}

        {activeView === 'overview' && result && summary ? (
          <div className="dashboard" aria-live="polite">
            <section className="dashboard-intro">
              <div>
                <p className="section-kicker">Analysis complete</p>
                <h2>Repository overview</h2>
                <code title={analyzedPath}>{analyzedPath}</code>
              </div>
              <div className="parse-health">
                <span className={summary.parse_failures ? 'warning' : 'healthy'} />
                {summary.parsed_successfully}/{summary.total_java_files} files parsed
              </div>
            </section>

            <section className="stat-grid" aria-label="Repository statistics">
              <StatCard label="Java files" value={summary.total_java_files} detail={`${summary.parse_failures} parse failures`} />
              <StatCard label="Classes" value={summary.class_count} />
              <StatCard label="Controllers" value={summary.controller_count} />
              <StatCard label="Services" value={summary.service_count} />
              <StatCard label="Repositories" value={summary.repository_count} />
              <StatCard label="Endpoints" value={summary.endpoint_count} />
              <StatCard label="Dependencies" value={summary.dependency_count} detail={`${summary.graph_edge_count} resolved graph edges`} />
              <StatCard label="Packages" value={result.packageAnalysis.packages.length} detail={`${result.packageAnalysis.dependencies.length} package relationships`} />
            </section>

            <SourceBreakdown summary={summary} />
            <PackageTable packages={result.packageAnalysis.packages} />

            <div className="component-grid" aria-label="Detected components">
              <ComponentList
                eyebrow="Spring web"
                title="Controllers"
                items={result.repositoryAnalysis.controllers}
                emptyMessage="No Spring controllers were detected."
              />
              <ComponentList
                eyebrow="Persistence"
                title="Repositories"
                items={result.repositoryAnalysis.repositories}
                emptyMessage="No Spring repositories were detected."
              />
            </div>
          </div>
        ) : null}

        {activeView === 'graph' && result ? (
          <div className="graph-view">
            <ArchitectureGraph graph={result.architectureGraph} />
          </div>
        ) : null}

        {activeView === 'graph' && !result && !loading ? (
          <section className="empty-state graph-prompt">
            <span className="empty-icon">{`< >`}</span>
            <h2>Analyze a repository to explore its architecture.</h2>
            <p>The production class dependency graph will appear here.</p>
          </section>
        ) : null}
        </div>
        {result ? (
          <div id="architecture-assistant" className="assistant-sidebar-slot">
            <ArchitectureAssistant
              context={result.unifiedContext}
              onClose={() => setAssistantOpen(false)}
            />
          </div>
        ) : null}
        </div>
      </main>

      <footer>
        <span>CodeAtlas</span>
        <span>Static architecture analysis for Java repositories</span>
      </footer>
    </div>
  );
}

export default App;

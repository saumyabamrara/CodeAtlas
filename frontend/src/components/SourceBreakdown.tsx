import type { RepositorySummary } from '../types/api';

interface SourceBreakdownProps {
  summary: RepositorySummary;
}

export function SourceBreakdown({ summary }: SourceBreakdownProps) {
  return (
    <section className="panel" aria-labelledby="source-breakdown-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Source scope</p>
          <h2 id="source-breakdown-title">Production and test breakdown</h2>
        </div>
      </div>
      <div className="scope-grid">
        <article className="scope-card production-scope">
          <div className="scope-title">
            <span className="scope-dot" />
            <h3>Production</h3>
          </div>
          <dl>
            <div><dt>Java files</dt><dd>{summary.production_java_files}</dd></div>
            <div><dt>Classes</dt><dd>{summary.production_class_count}</dd></div>
            <div><dt>Dependencies</dt><dd>{summary.production_dependency_count}</dd></div>
          </dl>
        </article>
        <article className="scope-card test-scope">
          <div className="scope-title">
            <span className="scope-dot" />
            <h3>Test</h3>
          </div>
          <dl>
            <div><dt>Java files</dt><dd>{summary.test_java_files}</dd></div>
            <div><dt>Classes</dt><dd>{summary.test_class_count}</dd></div>
            <div><dt>Dependencies</dt><dd>{summary.test_dependency_count}</dd></div>
          </dl>
        </article>
      </div>
    </section>
  );
}

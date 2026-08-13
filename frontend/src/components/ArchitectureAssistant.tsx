import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { askArchitecture } from '../services/api';
import type { UnifiedRepositoryAnalysisResponse } from '../types/api';

const EXAMPLE_QUESTIONS = [
  'Explain the architecture of this repository.',
  'Which repositories are used by controllers?',
  'Why are there no services in this repository?',
];

interface ArchitectureAssistantProps {
  context: UnifiedRepositoryAnalysisResponse;
}

export function ArchitectureAssistant({ context }: ArchitectureAssistantProps) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [model, setModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    setLoading(true);
    setError(null);
    setAnswer(null);
    setModel(null);
    try {
      const response = await askArchitecture({
        question: trimmedQuestion,
        context,
      });
      setAnswer(response.answer);
      setModel(response.model);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'The architecture assistant could not answer right now.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel assistant-panel" aria-labelledby="assistant-title">
      <div className="section-heading assistant-heading">
        <div>
          <p className="section-kicker">Grounded AI</p>
          <h2 id="assistant-title">Architecture Assistant</h2>
        </div>
        <span className="count-badge">Uses current analysis</span>
      </div>

      <p className="assistant-copy">
        Ask one question about the analyzed repository. Answers use CodeAtlas metadata,
        not direct access to your source files.
      </p>

      <div className="example-questions" aria-label="Example questions">
        {EXAMPLE_QUESTIONS.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => setQuestion(example)}
            disabled={loading}
          >
            {example}
          </button>
        ))}
      </div>

      <form
        className="assistant-form"
        onSubmit={(event) => {
          event.preventDefault();
          void submitQuestion();
        }}
      >
        <label htmlFor="architecture-question">Question</label>
        <div className="assistant-input-row">
          <input
            id="architecture-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What does OwnerController depend on?"
            maxLength={1000}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'Asking...' : 'Ask AI'}
          </button>
        </div>
      </form>

      {loading ? (
        <div className="assistant-status" role="status">
          <span className="loading-spinner" />
          Generating a grounded architecture answer...
        </div>
      ) : null}
      {error ? <div className="assistant-error" role="alert">{error}</div> : null}
      {answer ? (
        <div className="assistant-answer" aria-live="polite">
          <div className="assistant-answer-heading">
            <strong>Answer</strong>
            {model ? <code>{model}</code> : null}
          </div>
          <div className="assistant-answer-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
          </div>
        </div>
      ) : null}
    </section>
  );
}

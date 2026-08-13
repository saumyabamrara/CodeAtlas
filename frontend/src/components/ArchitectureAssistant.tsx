import { useEffect, useRef, useState } from 'react';
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
  onClose: () => void;
}

interface TranscriptEntry {
  id: number;
  question: string;
  answer?: string;
  model?: string;
  error?: string;
  pending: boolean;
}

export function ArchitectureAssistant({ context, onClose }: ArchitectureAssistantProps) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const nextMessageId = useRef(0);
  const transcript = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcript.current?.scrollTo({
      top: transcript.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  const submitQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    const messageId = nextMessageId.current++;
    setQuestion('');
    setLoading(true);
    setMessages((current) => [
      ...current,
      { id: messageId, question: trimmedQuestion, pending: true },
    ]);

    try {
      const response = await askArchitecture({
        question: trimmedQuestion,
        context,
      });
      setMessages((current) =>
        current.map((message) =>
          message.id === messageId
            ? {
                ...message,
                answer: response.answer,
                model: response.model,
                pending: false,
              }
            : message,
        ),
      );
    } catch (requestError) {
      setMessages((current) =>
        current.map((message) =>
          message.id === messageId
            ? {
                ...message,
                error:
                  requestError instanceof Error
                    ? requestError.message
                    : 'The architecture assistant could not answer right now.',
                pending: false,
              }
            : message,
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="panel assistant-panel" aria-labelledby="assistant-title">
      <div className="assistant-header">
        <div>
          <p className="section-kicker">Grounded AI</p>
          <h2 id="assistant-title">Architecture Assistant</h2>
        </div>
        <button
          className="assistant-close"
          type="button"
          onClick={onClose}
          aria-label="Close Architecture Assistant"
        >
          ×
        </button>
      </div>

      <p className="assistant-copy">
        Ask about this repository. Previous answers stay here for this analysis.
      </p>

      <div className="assistant-transcript" aria-live="polite" ref={transcript}>
        {messages.length === 0 ? (
          <div className="assistant-welcome">
            <strong>Start with an example</strong>
            <p>Answers use CodeAtlas metadata, not direct source-file access.</p>
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
          </div>
        ) : null}

        {messages.map((message) => (
          <article className="assistant-exchange" key={message.id}>
            <div className="assistant-question">
              <span>You</span>
              <p>{message.question}</p>
            </div>

            {message.pending ? (
              <div className="assistant-thinking" role="status">
                <span className="loading-spinner" />
                Reading the architecture metadata...
              </div>
            ) : null}

            {message.error ? (
              <div className="assistant-error" role="alert">{message.error}</div>
            ) : null}

            {message.answer ? (
              <div className="assistant-answer">
                <div className="assistant-answer-heading">
                  <strong>CodeAtlas AI</strong>
                  {message.model ? <code>{message.model}</code> : null}
                </div>
                <div className="assistant-answer-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.answer}
                  </ReactMarkdown>
                </div>
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <form
        className="assistant-form"
        onSubmit={(event) => {
          event.preventDefault();
          void submitQuestion();
        }}
      >
        <label htmlFor="architecture-question">Ask a question</label>
        <textarea
          id="architecture-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              void submitQuestion();
            }
          }}
          placeholder="What does OwnerController depend on?"
          maxLength={1000}
          rows={3}
          disabled={loading}
        />
        <div className="assistant-form-footer">
          <span>Enter to send · Shift+Enter for a new line</span>
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'Asking...' : 'Ask AI'}
          </button>
        </div>
      </form>
    </aside>
  );
}

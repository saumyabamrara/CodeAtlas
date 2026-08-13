interface RepositoryInputProps {
  value: string;
  activity: 'cloning' | 'analyzing' | null;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function RepositoryInput({
  value,
  activity,
  onChange,
  onSubmit,
}: RepositoryInputProps) {
  return (
    <form
      className="repository-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label htmlFor="repository-path">Repository source</label>
      <div className="repository-input-row">
        <input
          id="repository-path"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="https://github.com/spring-projects/spring-petclinic"
          autoComplete="off"
          spellCheck={false}
          aria-describedby="repository-path-help"
        />
        <button type="submit" disabled={activity !== null}>
          {activity === 'cloning'
            ? 'Cloning...'
            : activity === 'analyzing'
              ? 'Analyzing...'
              : 'Analyze Repository'}
        </button>
      </div>
      <p id="repository-path-help" className="field-help">
        Paste a public HTTPS GitHub URL or a local path available to the backend.
      </p>
    </form>
  );
}

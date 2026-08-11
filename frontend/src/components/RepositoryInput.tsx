interface RepositoryInputProps {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function RepositoryInput({
  value,
  loading,
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
      <label htmlFor="repository-path">Repository path</label>
      <div className="repository-input-row">
        <input
          id="repository-path"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="E:\Project\CodeAtlas\backend\workspace\spring-petclinic"
          autoComplete="off"
          spellCheck={false}
          aria-describedby="repository-path-help"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze Repository'}
        </button>
      </div>
      <p id="repository-path-help" className="field-help">
        Enter a local path available to the CodeAtlas backend.
      </p>
    </form>
  );
}

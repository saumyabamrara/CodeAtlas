interface StatCardProps {
  label: string;
  value: number;
  detail?: string;
}

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <article className="stat-card">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
      {detail ? <small>{detail}</small> : null}
    </article>
  );
}

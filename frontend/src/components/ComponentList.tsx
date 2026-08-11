import type { ComponentMetadata } from '../types/api';

interface ComponentListProps {
  title: string;
  eyebrow: string;
  items: ComponentMetadata[];
  emptyMessage: string;
}

export function ComponentList({
  title,
  eyebrow,
  items,
  emptyMessage,
}: ComponentListProps) {
  return (
    <section className="panel component-panel">
      <div className="section-heading compact-heading">
        <div>
          <p className="section-kicker">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
        <span className="count-badge">{items.length}</span>
      </div>
      {items.length ? (
        <ul className="component-list">
          {items.map((item) => (
            <li key={`${item.package_name}.${item.qualified_class_name}`}>
              <div>
                <strong>{item.class_name}</strong>
                <code>{item.package_name}</code>
              </div>
              <span className={`scope-tag ${item.scope}`}>{item.scope}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-copy">{emptyMessage}</p>
      )}
    </section>
  );
}

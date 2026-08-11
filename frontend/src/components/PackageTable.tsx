import type { PackageMetadata } from '../types/api';

interface PackageTableProps {
  packages: PackageMetadata[];
}

export function PackageTable({ packages }: PackageTableProps) {
  return (
    <section className="panel table-panel" aria-labelledby="packages-title">
      <div className="section-heading">
        <div>
          <p className="section-kicker">Structure</p>
          <h2 id="packages-title">Packages</h2>
        </div>
        <span className="count-badge">{packages.length} detected</span>
      </div>
      {packages.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Package</th>
                <th>Production classes</th>
                <th>Test classes</th>
                <th>Components</th>
              </tr>
            </thead>
            <tbody>
              {packages.map((item) => {
                const componentCount =
                  item.production_controller_count +
                  item.production_service_count +
                  item.production_repository_count;
                return (
                  <tr key={item.package_name}>
                    <td><code>{item.package_name || '(default package)'}</code></td>
                    <td>{item.production_class_count}</td>
                    <td>{item.test_class_count}</td>
                    <td>{componentCount}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="empty-copy">No Java packages were detected.</p>
      )}
    </section>
  );
}

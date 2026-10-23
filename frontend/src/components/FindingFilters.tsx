import { Link, useSearchParams } from 'react-router-dom';
import { Button } from './ui/Primitives';
export function FindingFilters({
  domains,
}: {
  domains: { id: string; hostname: string }[];
}) {
  const [params, setParams] = useSearchParams();
  return (
    <form
      className="finding-filters"
      aria-label="Filter findings"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        const next = new URLSearchParams();
        for (const [key, value] of form.entries())
          if (String(value) && value !== 'all') next.set(key, String(value));
        if (params.get('scan_id')) next.set('scan_id', params.get('scan_id')!);
        setParams(next);
      }}
    >
      <label>
        Status
        <select name="status" defaultValue={params.get('status') ?? 'all'}>
          <option value="all">All statuses</option>
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
        </select>
      </label>
      <label>
        Priority
        <select name="severity" defaultValue={params.get('severity') ?? 'all'}>
          <option value="all">All priorities</option>
          {['high', 'medium', 'low', 'info'].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>
      <label>
        Domain
        <select name="domain_id" defaultValue={params.get('domain_id') ?? ''}>
          <option value="">All owned domains</option>
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.hostname}
            </option>
          ))}
        </select>
      </label>
      <label>
        Category
        <select name="category" defaultValue={params.get('category') ?? 'all'}>
          <option value="all">All categories</option>
          {['tls', 'https', 'http_headers', 'dns_email'].map((v) => (
            <option key={v} value={v}>
              {v.replaceAll('_', ' ')}
            </option>
          ))}
        </select>
      </label>
      <label>
        Evidence freshness
        <select
          name="freshness"
          defaultValue={params.get('freshness') ?? 'all'}
        >
          <option value="all">All evidence</option>
          <option value="stale">Stale</option>
          <option value="not_rechecked">Not rechecked</option>
        </select>
      </label>
      <label>
        Sort
        <select name="sort" defaultValue={params.get('sort') ?? 'priority'}>
          <option value="priority">Priority order</option>
          <option value="newest">Newest issue evidence</option>
          <option value="oldest">First detected</option>
          <option value="domain">Domain name</option>
        </select>
      </label>
      <Button type="submit">Apply filters</Button>
      <Link to="/app/findings">Reset filters</Link>
    </form>
  );
}

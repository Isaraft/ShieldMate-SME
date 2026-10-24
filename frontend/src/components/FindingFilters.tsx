import { T, tr } from '../i18n';
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
      aria-label={tr('Filter findings')}
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
        <T text={'Status'} />
        <select name="status" defaultValue={params.get('status') ?? 'all'}>
          <option value="all">
            <T text={'All statuses'} />
          </option>
          <option value="open">
            <T text={'Open'} />
          </option>
          <option value="resolved">
            <T text={'Resolved'} />
          </option>
        </select>
      </label>
      <label>
        <T text={'Priority '} />
        <select name="severity" defaultValue={params.get('severity') ?? 'all'}>
          <option value="all">
            <T text={'All priorities'} />
          </option>
          {['high', 'medium', 'low', 'info'].map((v) => (
            <option key={tr(v)} value={tr(v)}>
              {tr(v)}
            </option>
          ))}
        </select>
      </label>
      <label>
        <T text={'Domain'} />
        <select name="domain_id" defaultValue={params.get('domain_id') ?? ''}>
          <option value="">
            <T text={'All owned domains'} />
          </option>
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.hostname}
            </option>
          ))}
        </select>
      </label>
      <label>
        <T text={'Category'} />
        <select name="category" defaultValue={params.get('category') ?? 'all'}>
          <option value="all">
            <T text={'All categories'} />
          </option>
          {['tls', 'https', 'http_headers', 'dns_email'].map((v) => (
            <option key={tr(v)} value={tr(v)}>
              {tr(v)}
            </option>
          ))}
        </select>
      </label>
      <label>
        <T text={'Evidence freshness'} />
        <select
          name="freshness"
          defaultValue={params.get('freshness') ?? 'all'}
        >
          <option value="all">
            <T text={'All evidence'} />
          </option>
          <option value="stale">
            <T text={'Stale'} />
          </option>
          <option value="not_rechecked">
            <T text={'Not rechecked'} />
          </option>
        </select>
      </label>
      <label>
        <T text={'Sort'} />
        <select name="sort" defaultValue={params.get('sort') ?? 'priority'}>
          <option value="priority">
            <T text={'Priority order'} />
          </option>
          <option value="newest">
            <T text={'Newest issue evidence'} />
          </option>
          <option value="oldest">
            <T text={'First detected'} />
          </option>
          <option value="domain">
            <T text={'Domain name'} />
          </option>
        </select>
      </label>
      <Button type="submit">
        <T text={'Apply filters'} />
      </Button>
      <Link to="/app/findings">
        <T text={'Reset filters'} />
      </Link>
    </form>
  );
}

import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../authApi';
import {
  Alert,
  Badge,
  Button,
  EmptyState,
  Field,
  LoadingState,
} from '../components/ui/Primitives';

type Asset = {
  scan_available: boolean;
  id: string;
  canonical_fqdn: string;
  status: string;
  created_at: number;
  authorization_attested_at: number;
  authorization_policy_version: string;
  challenge_generation: number;
  challenge_issued_at: number;
  challenge_expires_at: number;
  verified_at: number | null;
  verification_valid_until: number | null;
  record_hostname: string;
  record_value: string;
  last_verification_error_code: string | null;
};
const messages: Record<string, string> = {
  verified: 'Domain control verified. This is not a security assessment.',
  not_found:
    'The exact TXT record was not found. Check the name and value, allow DNS caches to update, then retry.',
  temporarily_unavailable:
    'DNS could not be checked right now. No new verification was granted. Retry later.',
  challenge_expired:
    'This challenge has expired. Generate a new challenge and replace the old TXT value.',
};
function date(value: number | null) {
  return value
    ? new Date(value * 1000).toLocaleString(undefined, {
        timeZoneName: 'short',
      })
    : 'Not verified';
}
export function Assets() {
  const [assets, setAssets] = useState<Asset[]>();
  const [selected, setSelected] = useState<string>();
  const [fqdn, setFqdn] = useState('');
  const [consent, setConsent] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState('');
  const [copy, setCopy] = useState('');
  const [remove, setRemove] = useState<Asset>();
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const navigate = useNavigate();
  const active = assets?.find((a) => a.id === selected);
  function fail(e: unknown) {
    if (e instanceof ApiError && e.status === 401)
      navigate('/login', { replace: true });
    else
      setError(
        e instanceof Error
          ? e.message
          : 'Connection unavailable. Please retry.',
      );
  }
  useEffect(() => {
    let alive = true;
    api<Asset[]>('/domains')
      .then((rows) => {
        if (alive) setAssets(rows);
      })
      .catch((e) => {
        if (alive) {
          if (e instanceof ApiError && e.status === 401)
            navigate('/login', { replace: true });
          else setError('Unable to load domains. Retry.');
        }
      });
    return () => {
      alive = false;
    };
  }, [navigate]);
  async function refresh() {
    setAssets(await api<Asset[]>('/domains'));
  }
  async function action(path: string, method = 'POST') {
    setPending(true);
    setError('');
    setFeedback('');
    try {
      const result = await api<Asset | { code: string; domain: Asset }>(
        path,
        method,
      );
      await refresh();
      if ('code' in result)
        setFeedback(messages[result.code] ?? 'Domain updated.');
      else
        setFeedback(
          'New challenge generated. Previous verification was revoked; replace the old TXT value.',
        );
    } catch (e) {
      fail(e);
    } finally {
      setPending(false);
    }
  }
  async function copyValue(value: string, label: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopy(`${label} copied.`);
    } catch {
      setCopy('Clipboard unavailable. Select and copy the full value below.');
    }
  }
  return (
    <section className="assets-page">
      <p className="eyebrow">Company workspace / Authorized assets</p>
      <h1>Assets</h1>
      <p>
        Add only domains you control or have written authorization to assess.
        DNS proof confirms control at a specific name and time; it does not
        authorize every host or service behind it.
      </p>
      <Alert title="Limited checks, exact domain only">
        ShieldMate Starter performs limited external configuration checks. It
        does not guarantee security or detect all vulnerabilities.
      </Alert>
      {error && (
        <Alert title="Unable to complete request" tone="error">
          {error}
        </Alert>
      )}
      {assets === undefined ? (
        <>
          {!error && <LoadingState label="Loading your domains…" />}
          {error && (
            <Button
              onClick={async () => {
                try {
                  await refresh();
                  setError('');
                } catch (e) {
                  fail(e);
                }
              }}
            >
              Retry loading domains
            </Button>
          )}
        </>
      ) : (
        <>
          <form
            className="asset-enrollment"
            onSubmit={async (event) => {
              event.preventDefault();
              setError('');
              setFeedback('');
              if (!consent || /[^a-zA-Z0-9.-]/.test(fqdn)) {
                setError(
                  'Enter a domain only, without whitespace, URL, path or port, and acknowledge authorization. Use ASCII or Punycode.',
                );
                return;
              }
              setPending(true);
              try {
                const row = await api<Asset>('/domains', 'POST', {
                  fqdn,
                  authorization_acknowledged: consent,
                });
                await refresh();
                setSelected(row.id);
                setFqdn('');
                setConsent(false);
                setFeedback(
                  'Domain added. Publish the TXT record below, then verify ownership.',
                );
                window.setTimeout(() => heading.current?.focus(), 0);
              } catch (e) {
                fail(e);
              } finally {
                setPending(false);
              }
            }}
          >
            <h2>Add an authorized domain</h2>
            <Field
              label="Domain name"
              help="Domain only, such as shop.example.com. ASCII or valid Punycode; no URL or whitespace."
              required
              maxLength={254}
              autoComplete="off"
              value={fqdn}
              onChange={(e) => setFqdn(e.target.value)}
            />
            <label className="authorization-choice">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                required
              />{' '}
              <span>
                I control this domain or have written permission to request
                ShieldMate’s limited external checks. I understand DNS control
                does not prove authorization for every underlying service.
              </span>
            </label>
            <Button type="submit" pending={pending}>
              Add domain
            </Button>
          </form>
          {assets.length === 0 ? (
            <EmptyState title="Your domain list starts here.">
              <p>
                Enroll a domain and publish its unique TXT challenge. Nothing
                becomes verified until the server finds a valid matching record.
              </p>
            </EmptyState>
          ) : (
            <div className="asset-list" aria-label="Your domains">
              {assets.map((asset) => (
                <article key={asset.id}>
                  <div>
                    <h2>{asset.canonical_fqdn}</h2>
                    <Badge
                      tone={asset.status === 'verified' ? 'success' : 'neutral'}
                    >
                      {asset.status}
                    </Badge>
                    <p>Added {date(asset.created_at)}</p>
                    <p>
                      Verification valid until:{' '}
                      {date(asset.verification_valid_until)}
                    </p>
                  </div>
                  <div className="asset-scan-actions">
                    <Button
                      pending={pending}
                      disabled={!asset.scan_available}
                      onClick={async () => {
                        setPending(true);
                        setError('');
                        try {
                          const run = await api<{ id: string }>(
                            `/domains/${asset.id}/scans`,
                            'POST',
                          );
                          navigate(`/app/assets/${asset.id}/scans/${run.id}`);
                        } catch (e) {
                          fail(e);
                        } finally {
                          setPending(false);
                        }
                      }}
                    >
                      Run security checks
                    </Button>
                    {!asset.scan_available && (
                      <p className="field-help">
                        {asset.status === 'stale'
                          ? 'DNS proof is stale. Generate a new challenge and verify again.'
                          : asset.status === 'expired'
                            ? 'The DNS challenge expired. Generate a new challenge and verify ownership.'
                            : asset.status === 'verified'
                              ? 'Recorded scan authorization is missing or no longer valid.'
                              : 'Ownership is not verified. Publish the TXT challenge and verify ownership.'}
                      </p>
                    )}
                    <Link
                      className="button button-quiet"
                      to={`/app/assets/${asset.id}/scans`}
                    >
                      Scan history for {asset.canonical_fqdn}
                    </Link>
                  </div>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setSelected(asset.id);
                      setFeedback('');
                      setCopy('');
                    }}
                  >
                    DNS instructions for {asset.canonical_fqdn}
                  </Button>
                </article>
              ))}
            </div>
          )}
        </>
      )}
      {feedback && <Alert title="Verification update">{feedback}</Alert>}
      {active && (
        <section className="dns-instructions" aria-labelledby="dns-title">
          <h2 id="dns-title" ref={heading} tabIndex={-1}>
            DNS TXT instructions: {active.canonical_fqdn}
          </h2>
          <Badge tone={active.status === 'verified' ? 'success' : 'neutral'}>
            {active.status}
          </Badge>
          <p>
            Record type: <strong>TXT</strong>
          </p>
          <p>
            Issued {date(active.challenge_issued_at)} · Generation{' '}
            {active.challenge_generation}
          </p>
          <p>Challenge expires {date(active.challenge_expires_at)}</p>
          <p>Domain control verified at: {date(active.verified_at)}</p>
          <p>
            Verification freshness ends: {date(active.verification_valid_until)}
          </p>
          <dl>
            <dt>Full record hostname</dt>
            <dd>
              <code>{active.record_hostname}</code>
              <Button
                variant="quiet"
                onClick={() => copyValue(active.record_hostname, 'Hostname')}
              >
                Copy hostname
              </Button>
            </dd>
            <dt>Exact TXT value</dt>
            <dd>
              <code>{active.record_value}</code>
              <Button
                variant="quiet"
                onClick={() => copyValue(active.record_value, 'TXT value')}
              >
                Copy TXT value
              </Button>
            </dd>
          </dl>
          <p role="status">{copy}</p>
          <p>
            Your DNS provider may append the selected zone automatically. In the
            zone for this exact domain the relative name is{' '}
            <code>_shieldmate-challenge</code>. For a subdomain asset in its
            parent zone, include that subdomain in the relative name. Check the
            resulting full hostname to avoid duplicating the zone. Create a
            separate TXT record; do not edit SPF or DMARC.
          </p>
          <p>
            DNS caching can delay visibility. No propagation time is guaranteed.
            TXT challenges are public DNS data, never account credentials.
          </p>
          {active.status === 'stale' && (
            <Alert title="Verification is stale" tone="warning">
              Generate a new challenge, publish it and verify again. Freshness
              is separate from the challenge expiry.
            </Alert>
          )}
          <div className="button-row">
            <Button
              pending={pending}
              onClick={() => action(`/domains/${active.id}/verification/check`)}
            >
              Verify ownership
            </Button>
            <Button
              variant="secondary"
              disabled={pending}
              onClick={() =>
                action(`/domains/${active.id}/verification/request`)
              }
            >
              Generate new challenge
            </Button>

            <Button
              variant="quiet"
              disabled={pending}
              onClick={() => {
                setRemove(active);
                dialog.current?.showModal();
              }}
            >
              Remove domain
            </Button>
          </div>
          <p className="field-help">
            Generating a new challenge immediately revokes previous verification
            and invalidates the old TXT value. You can delete obsolete records
            from your DNS provider yourself.
          </p>
        </section>
      )}
      <dialog
        ref={dialog}
        className="confirm-dialog"
        aria-labelledby="remove-title"
        onClose={() => setRemove(undefined)}
      >
        <h2 id="remove-title">Remove domain?</h2>
        <p>
          Remove {remove?.canonical_fqdn} from this workspace and revoke its
          verification. Derived findings and their history are also removed.
          This cannot be undone and does not remove records at your DNS
          provider.
        </p>
        <div className="button-row">
          <Button variant="secondary" onClick={() => dialog.current?.close()}>
            Cancel
          </Button>
          <Button
            pending={pending}
            onClick={async () => {
              if (!remove) return;
              setPending(true);
              try {
                await api(`/domains/${remove.id}`, 'DELETE');
                await refresh();
                setSelected(undefined);
                setFeedback('Domain removed.');
                dialog.current?.close();
              } catch (e) {
                fail(e);
              } finally {
                setPending(false);
              }
            }}
          >
            Confirm removal
          </Button>
        </div>
      </dialog>
    </section>
  );
}

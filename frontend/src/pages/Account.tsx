import { useEffect, useState } from 'react';
import {
  Link,
  Navigate,
  Outlet,
  useNavigate,
  useOutletContext,
  useSearchParams,
} from 'react-router-dom';
import { api, ApiError, type Identity, type Organization } from '../authApi';
import {
  Alert,
  Button,
  Field,
  LoadingState,
} from '../components/ui/Primitives';

export function AccountForm({ register = false }: { register?: boolean }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [params] = useSearchParams();
  const created = params.has('created');
  return (
    <section className="account-page">
      <p className="eyebrow">ShieldMate SME / Account</p>
      <h1>{register ? 'Create account' : 'Sign in'}</h1>
      <p>
        {register
          ? 'Start with your account. Create your company workspace after signing in.'
          : 'Continue to your company workspace.'}
      </p>
      {created && (
        <Alert title="Account created" tone="success">
          Sign in with your new account.
        </Alert>
      )}
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          setPending(true);
          setError('');
          try {
            await api(register ? '/auth/register' : '/auth/login', 'POST', {
              email,
              password,
            });
            setPassword('');
            if (register) {
              navigate('/login?created=1');
            } else {
              navigate('/app', { replace: true });
            }
          } catch (e) {
            setError(
              e instanceof Error ? e.message : 'Unable to connect. Retry.',
            );
          } finally {
            setPending(false);
          }
        }}
      >
        <Field
          label="Email address"
          help="Use your own email address."
          type="email"
          autoComplete="email"
          required
          maxLength={254}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Field
          label="Password"
          help="12–128 characters. Passphrases and Unicode are supported."
          type="password"
          autoComplete={register ? 'new-password' : 'current-password'}
          required
          minLength={12}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && (
          <Alert title="Unable to continue" tone="error">
            {error}
          </Alert>
        )}
        <Button type="submit" pending={pending}>
          {register ? 'Create account' : 'Sign in'}
        </Button>
      </form>
      <Link to={register ? '/login' : '/register'}>
        {register ? 'Already have an account? Sign in' : 'Create an account'}
      </Link>
      {!register && (
        <p className="field-help">
          Email verification and password reset are not available yet.
        </p>
      )}
    </section>
  );
}

export function PrivateWorkspace() {
  const [identity, setIdentity] = useState<Identity | null>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    api<Identity>('/auth/me')
      .then((user) => {
        if (active) setIdentity(user);
      })
      .catch((e) => {
        if (active) {
          if (e instanceof ApiError && e.status === 401) setIdentity(null);
          else setError('Unable to load your account. Please retry.');
        }
      });
    const refresh = () => setAttempt((n) => n + 1);
    window.addEventListener('focus', refresh);
    const interval = window.setInterval(refresh, 60000);
    return () => {
      active = false;
      window.removeEventListener('focus', refresh);
      window.clearInterval(interval);
    };
  }, [attempt]);
  if (error)
    return (
      <section className="account-page">
        <Alert title="Connection unavailable" tone="error">
          {error}
        </Alert>
        <Button
          onClick={() => {
            setError('');
            setAttempt((n) => n + 1);
          }}
        >
          Retry
        </Button>
      </section>
    );
  if (identity === undefined)
    return (
      <div className="account-page">
        <LoadingState label="Checking your session…" />
      </div>
    );
  if (identity === null) return <Navigate to="/login" replace />;
  return (
    <div>
      <div className="preview-banner">
        <strong>{identity.organization?.name ?? 'Your account'}</strong>
        <span>{identity.email}</span>
        <Link to="/app/settings">Organization settings</Link>
        <Button
          variant="quiet"
          onClick={async () => {
            try {
              await api('/auth/logout', 'POST');
              navigate('/login', { replace: true });
            } catch (e) {
              if (e instanceof ApiError && e.status === 401)
                navigate('/login', { replace: true });
              else setError('Unable to sign out. Retry.');
            }
          }}
        >
          Sign out
        </Button>
      </div>
      {identity.organization ? (
        <>
          <nav className="private-nav" aria-label="Workspace navigation">
            <Link to="/app">Overview</Link>
            <Link to="/app/assets">Assets</Link>
            <Link to="/app/findings">Findings</Link>
            <Link to="/app/tasks">Action plan</Link>
            <Link to="/app/reports">Reports</Link>
            <Link to="/app/settings">Settings</Link>
          </nav>
          <Outlet
            key={`${identity.id}:${identity.organization.id}`}
            context={{ identity, refresh: () => setAttempt((n) => n + 1) }}
          />
        </>
      ) : (
        <OrganizationForm onSaved={() => setAttempt((n) => n + 1)} />
      )}
    </div>
  );
}

export function OrganizationForm({
  organization,
  onSaved,
}: {
  organization?: Organization;
  onSaved: () => void;
}) {
  const [name, setName] = useState(organization?.name ?? '');
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  return (
    <section className="account-page">
      <p className="eyebrow">Company workspace</p>
      <h1>
        {organization ? 'Organization settings' : 'Create your workspace'}
      </h1>
      <p>
        {organization
          ? 'Update your company display name.'
          : 'One company workspace per account. Choose the name your team uses.'}
      </p>
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          setPending(true);
          setError('');
          setMessage('');
          try {
            await api(
              '/organizations' + (organization ? '/current' : ''),
              organization ? 'PATCH' : 'POST',
              { name },
            );
            setMessage('Workspace saved.');
            onSaved();
          } catch (e) {
            if (e instanceof ApiError && e.status === 401)
              navigate('/login', { replace: true });
            else
              setError(
                e instanceof Error ? e.message : 'Unable to connect. Retry.',
              );
          } finally {
            setPending(false);
          }
        }}
      >
        <Field
          label="Company name"
          help="1–120 characters. You can rename it later."
          required
          maxLength={120}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {error && (
          <Alert title="Unable to save" tone="error">
            {error}
          </Alert>
        )}
        {message && (
          <Alert title="Saved" tone="success">
            {message}
          </Alert>
        )}
        <Button type="submit" pending={pending}>
          {organization ? 'Save company name' : 'Create workspace'}
        </Button>
      </form>
    </section>
  );
}

export function OrganizationSettings() {
  const { identity, refresh } = useOutletContext<{
    identity: Identity;
    refresh: () => void;
  }>();
  return (
    <OrganizationForm
      organization={identity.organization ?? undefined}
      onSaved={refresh}
    />
  );
}
export function PrivatePlanned({ title }: { title: string }) {
  return (
    <section className="account-page">
      <p className="eyebrow">Company workspace / Planned</p>
      <h1>{title}</h1>
      <Alert title="Coming in a later phase">
        This feature is not available yet. Reports are planned for Phase 07.
        Existing assets, findings and remediation tasks remain available.
      </Alert>
      <Button disabled>Unavailable</Button>
    </section>
  );
}

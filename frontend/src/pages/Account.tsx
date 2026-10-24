import { onSessionChange } from '../sessionEvents';
import { T, tr } from '../i18n';
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
      <p className="eyebrow">
        <T text={'ShieldMate SME / Account'} />
      </p>
      <h1>
        <T text={register ? 'Create account' : 'Sign in'} />
      </h1>
      <p>
        <T
          text={
            register
              ? 'Start with your account. Create your company workspace after signing in.'
              : 'Continue to your company workspace.'
          }
        />
      </p>
      {created && (
        <Alert title={tr('Account created')} tone="success">
          <T text={'Sign in with your new account.'} />
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
          label={tr('Email address')}
          help={tr('Use your own email address.')}
          type="email"
          autoComplete="email"
          required
          maxLength={254}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Field
          label={tr('Password')}
          help={tr('12–128 characters. Passphrases and Unicode are supported.')}
          type="password"
          autoComplete={register ? 'new-password' : 'current-password'}
          required
          minLength={12}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && (
          <Alert title={tr('Unable to continue')} tone="error">
            {tr(error)}
          </Alert>
        )}
        <Button type="submit" pending={pending}>
          <T text={register ? 'Create account' : 'Sign in'} />
        </Button>
      </form>
      <Link to={register ? '/login' : '/register'}>
        <T
          text={
            register ? 'Already have an account? Sign in' : 'Create an account'
          }
        />
      </Link>
      {!register && (
        <p className="field-help">
          <T
            text={
              'Email verification and password reset are not available yet.'
            }
          />
        </p>
      )}
    </section>
  );
}

export function PrivateWorkspace() {
  const [identity, setIdentity] = useState<Identity | null>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [checking, setChecking] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    api<Identity>('/auth/me')
      .then((user) => {
        if (active) {
          setIdentity(user);
          setChecking(document.hidden);
          setError('');
        }
      })
      .catch((e) => {
        if (active) {
          if (e instanceof ApiError && e.status === 401) setIdentity(null);
          else setError('Unable to load your account. Please retry.');
        }
      });
    const refresh = () => {
      setChecking(true);
      setAttempt((n) => n + 1);
    };
    const changed = () => {
      setIdentity(undefined);
      setError('');
      refresh();
    };
    const unsubscribe = onSessionChange(changed);
    const visibility = () => {
      if (document.hidden) setChecking(true);
      else refresh();
    };
    const restored = (event: PageTransitionEvent) => {
      if (event.persisted) refresh();
    };
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('pageshow', restored);
    window.addEventListener('focus', refresh);
    const interval = window.setInterval(refresh, 60000);
    return () => {
      active = false;
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', visibility);
      window.removeEventListener('pageshow', restored);
      unsubscribe();
      window.clearInterval(interval);
    };
  }, [attempt]);
  if (error)
    return (
      <section className="account-page">
        <Alert title={tr('Connection unavailable')} tone="error">
          {tr(error)}
        </Alert>
        <Button
          onClick={() => {
            setError('');
            setAttempt((n) => n + 1);
          }}
        >
          <T text={'Retry'} />
        </Button>
      </section>
    );
  if (identity === undefined)
    return (
      <div className="account-page">
        <LoadingState label={tr('Checking your session…')} />
      </div>
    );
  if (identity === null) return <Navigate to="/login" replace />;
  return (
    <div>
      {checking && (
        <div className="account-page">
          <LoadingState label={tr('Checking your session…')} />
        </div>
      )}
      <div hidden={checking}>
        <div className="preview-banner">
          <strong>{identity.organization?.name ?? tr('Your account')}</strong>
          <span>{identity.email}</span>
          <Link to="/app/settings">
            <T text={'Organization settings'} />
          </Link>
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
            <T text={'Sign out'} />
          </Button>
        </div>
        {identity.organization ? (
          <>
            <nav
              className="private-nav"
              aria-label={tr('Workspace navigation')}
            >
              <Link to="/app">
                <T text={'Overview'} />
              </Link>
              <Link to="/app/assets">
                <T text={'Assets'} />
              </Link>
              <Link to="/app/findings">
                <T text={'Findings'} />
              </Link>
              <Link to="/app/tasks">
                <T text={'Action plan'} />
              </Link>
              <Link to="/app/reports">
                <T text={'Reports'} />
              </Link>
              <Link to="/app/settings">
                <T text={'Settings'} />
              </Link>
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
      <p className="eyebrow">
        <T text={'Company workspace'} />
      </p>
      <h1>
        <T
          text={
            organization ? 'Organization settings' : 'Create your workspace'
          }
        />
      </h1>
      <p>
        <T
          text={
            organization
              ? 'Update your company display name.'
              : 'One company workspace per account. Choose the name your team uses.'
          }
        />
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
          label={tr('Company name')}
          help={tr('1–120 characters. You can rename it later.')}
          required
          maxLength={120}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {error && (
          <Alert title={tr('Unable to save')} tone="error">
            {tr(error)}
          </Alert>
        )}
        {message && (
          <Alert title={tr('Saved')} tone="success">
            {tr(message)}
          </Alert>
        )}
        <Button type="submit" pending={pending}>
          <T text={organization ? 'Save company name' : 'Create workspace'} />
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
      <p className="eyebrow">
        <T text={'Company workspace / Planned'} />
      </p>
      <h1>{title}</h1>
      <Alert title={tr('Coming in a later phase')}>
        <T
          text={
            'This feature is not available yet. This area is planned for a later phase. Existing assets, findings and remediation tasks remain available.'
          }
        />
      </Alert>
      <Button disabled>
        <T text={'Unavailable'} />
      </Button>
    </section>
  );
}

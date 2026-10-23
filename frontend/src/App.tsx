import { useEffect, useRef } from 'react';
import {
  Link,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';
import { PlannedState } from './components/PlannedState';
import { ServiceStatus } from './components/ServiceStatus';

const workspaceRoutes = [
  {
    path: '/app',
    title: 'Overview',
    phase: 'Phase 06',
    description:
      'Priorities will appear here once authorized checks and the finding engine are implemented.',
  },
  {
    path: '/app/assets',
    title: 'Assets',
    phase: 'Phase 03',
    description:
      'Domain ownership verification will be required before any external checks become available.',
  },
  {
    path: '/app/findings',
    title: 'Findings',
    phase: 'Phase 05',
    description:
      'Evidence-backed findings and recommended actions will be available after the checking and prioritization phases.',
  },
  {
    path: '/app/tasks',
    title: 'Action plan',
    phase: 'Phase 06',
    description:
      'Remediation tasks, owner labels and progress tracking are planned. There are no saved tasks yet.',
  },
  {
    path: '/app/reports',
    title: 'Reports',
    phase: 'Phase 07',
    description:
      'Management PDF reports will use stored evidence. Report generation is not available yet.',
  },
];

function Shell() {
  const { pathname } = useLocation();
  const previousPath = useRef(pathname);
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    const title = workspaceRoutes.find(
      (route) => route.path === pathname,
    )?.title;
    document.title = `${title ?? 'Foundation'} · ShieldMate SME`;
    if (previousPath.current !== pathname) {
      main.current?.focus();
      previousPath.current = pathname;
    }
  }, [pathname]);

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <Link className="wordmark" to="/" aria-label="ShieldMate SME home">
          SHIELDMATE<span>SME / STARTER</span>
        </Link>
        <nav aria-label="Main navigation">
          <NavLink to="/" end>
            Foundation
          </NavLink>
          <NavLink to="/app">Workspace preview</NavLink>
        </nav>
        <span className="phase-label">Phase 00</span>
      </header>
      <div className="phase-notice">
        Foundation preview · Authentication, external scanning, reports and paid
        subscriptions are not implemented.
      </div>
      <main id="main" ref={main} tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="site-footer">
        <strong>Clarity before action.</strong>
        <p>
          Planned scope: limited external configuration checks. ShieldMate
          Starter will not guarantee security or detect all vulnerabilities.
        </p>
      </footer>
    </div>
  );
}

function Welcome() {
  return (
    <div className="welcome">
      <section className="welcome-title" aria-labelledby="page-title">
        <p className="eyebrow">ShieldMate SME Starter</p>
        <h1 id="page-title">
          Know what <br />
          to fix first.
        </h1>
        <p className="welcome-caption">
          A foundation for clearer security decisions.
        </p>
      </section>
      <div className="welcome-detail">
        <p className="eyebrow">The starting point</p>
        <h2>Built for the next step.</h2>
        <p className="prose">
          ShieldMate is being developed for Kazakhstan’s small businesses. This
          first build establishes navigation and a local service connection.
          Product workflows come later.
        </p>
        <Link className="primary-link" to="/app">
          View workspace preview <span aria-hidden="true">↗</span>
        </Link>
        <p className="text-sm">Preview only. No account or domain required.</p>
        <div className="planned-access">
          <button disabled aria-describedby="account-note">
            Create workspace
          </button>
          <p id="account-note" className="text-sm">
            Planned for Phase 02. Accounts are not available yet.
          </p>
        </div>
        <ServiceStatus />
      </div>
    </div>
  );
}

function WorkspaceLayout() {
  return (
    <div className="workspace-layout">
      <aside className="workspace-nav">
        <p className="eyebrow">Workspace preview</p>
        <nav aria-label="Workspace navigation">
          {workspaceRoutes.map((route) => (
            <NavLink key={route.path} to={route.path} end>
              {route.title}
              <span>Planned</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <Outlet />
    </div>
  );
}

function NotFound() {
  return (
    <section className="not-found">
      <p className="eyebrow">404 / Page not found</p>
      <h1>This path ends here.</h1>
      <p>The page you requested does not exist.</p>
      <Link className="primary-link" to="/">
        Return to foundation
      </Link>
    </section>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Welcome />} />
        <Route element={<WorkspaceLayout />}>
          {workspaceRoutes.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={
                <PlannedState title={route.title} phase={route.phase}>
                  <p>{route.description}</p>
                </PlannedState>
              }
            />
          ))}
        </Route>
        <Route
          path="/login"
          element={
            <PlannedState title="Sign in" phase="Phase 02">
              <p>
                Authentication is not implemented. Do not enter credentials into
                this preview.
              </p>
            </PlannedState>
          }
        />
        <Route
          path="/register"
          element={
            <PlannedState title="Create workspace" phase="Phase 02">
              <p>Registration and organization setup are not implemented.</p>
            </PlannedState>
          }
        />
        <Route
          path="/demo"
          element={
            <PlannedState title="Sample Demo" phase="Phase 07">
              <p>
                The isolated, clearly labeled sample workspace is planned. No
                sample security results are available in Phase 00.
              </p>
            </PlannedState>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

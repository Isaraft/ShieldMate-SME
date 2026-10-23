import { useEffect, useRef } from 'react';
import {
  Link,
  Navigate,
  Outlet,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';
import { Header, Footer } from './components/SiteChrome';
import { PlannedState } from './components/PlannedState';
import { Landing } from './pages/Landing';
import { WorkspaceLayout, WorkspacePage } from './pages/Workspace';
import { workspaceRoutes } from './pages/workspaceRoutes';
import {
  AccountForm,
  PrivateWorkspace,
  OrganizationSettings,
  PrivateOverview,
  PrivatePlanned,
} from './pages/Account';
import { UiKit } from './pages/UiKit';

const titles: Record<string, string> = {
  '/': 'Know what to fix first',
  '/login': 'Sign in',
  '/register': 'Create account',
  '/demo': 'Sample Demo — planned',
  '/preview/ui-kit': 'UI foundation',
  '/app/settings': 'Organization settings',
  ...Object.fromEntries(
    workspaceRoutes.flatMap((route) => [
      [route.path, route.title],
      [route.path.replace('/app', '/preview'), `${route.title} — preview`],
    ]),
  ),
};

function Shell() {
  const { pathname, hash, key } = useLocation();
  const previousKey = useRef(key);
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    document.title = `${titles[pathname] ?? 'Page not found'} · ShieldMate SME`;
    if (hash) {
      const target = document.getElementById(hash.slice(1));
      target?.scrollIntoView?.();
      target?.focus({ preventScroll: true });
    } else if (previousKey.current !== key) {
      main.current?.focus();
      window.scrollTo?.(0, 0);
    }
    previousKey.current = key;
  }, [pathname, hash, key]);
  return (
    <div className="site-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main" ref={main} tabIndex={-1}>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

function NotFound() {
  return (
    <section className="not-found page-pad">
      <p className="eyebrow">404 / Page not found</p>
      <span className="error-number" aria-hidden="true">
        404
      </span>
      <h1>This path ends here.</h1>
      <p>
        The page you requested does not exist. There’s a clearer route back.
      </p>
      <Link className="button button-primary" to="/">
        Return to home <span aria-hidden="true">↗</span>
      </Link>
    </section>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Landing />} />
        <Route element={<WorkspaceLayout />}>
          {workspaceRoutes.map((route) => (
            <Route
              key={route.path}
              path={route.path.replace('/app', '/preview')}
              element={<WorkspacePage route={route} />}
            />
          ))}
          <Route path="/preview/ui-kit" element={<UiKit />} />
        </Route>
        <Route
          path="/app/ui-kit"
          element={<Navigate to="/preview/ui-kit" replace />}
        />
        <Route path="/login" element={<AccountForm />} />
        <Route path="/register" element={<AccountForm register />} />
        <Route element={<PrivateWorkspace />}>
          <Route path="/app" element={<PrivateOverview />} />
          {workspaceRoutes
            .filter((route) => route.path !== '/app')
            .map((route) => (
              <Route
                key={route.path}
                path={route.path}
                element={<PrivatePlanned title={route.title} />}
              />
            ))}
          <Route path="/app/settings" element={<OrganizationSettings />} />
        </Route>
        <Route
          path="/demo"
          element={
            <PlannedState title="Sample Demo" phase="Phase 07">
              <p>
                The isolated, clearly labeled sample workspace is planned. No
                sample security results are available in Phase 01.
              </p>
            </PlannedState>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

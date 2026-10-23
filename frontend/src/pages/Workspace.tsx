import { Link, NavLink, Outlet } from 'react-router-dom';
import { ServiceStatus } from '../components/ServiceStatus';
import { Alert, Badge, Button, EmptyState } from '../components/ui/Primitives';
import { Table } from '../components/ui/Table';
import { workspaceRoutes } from './workspaceRoutes';
type WorkspaceRoute = (typeof workspaceRoutes)[number];
export function WorkspaceLayout() {
  return (
    <div className="workspace">
      <div className="preview-banner">
        <strong>Interface preview</strong>
        <span>
          Live features are under development. No account or workspace data.
        </span>
      </div>
      <div className="workspace-layout">
        <aside className="workspace-nav">
          <p className="eyebrow">Starter / Preview</p>
          <nav aria-label="Workspace navigation">
            {workspaceRoutes.map((route, index) => (
              <NavLink
                key={route.path}
                to={route.path.replace('/app', '/preview')}
                end
              >
                <span className="nav-index" aria-hidden="true">
                  0{index + 1}
                </span>
                {route.title}
                <span className="nav-planned">Planned</span>
              </NavLink>
            ))}
          </nav>
          <div className="workspace-nav-bottom">
            <Link to="/preview/ui-kit">
              UI foundation <span aria-hidden="true">↗</span>
            </Link>
            <p>
              Built for clearer decisions. <br />
              Product workflows come later.
            </p>
          </div>
        </aside>
        <div className="workspace-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
export function WorkspacePage({ route }: { route: WorkspaceRoute }) {
  return (
    <section className="workspace-page" aria-labelledby="page-title">
      <div className="workspace-page-heading">
        <div>
          <p className="eyebrow">Workspace / {route.title}</p>
          <h1 id="page-title">{route.title}</h1>
        </div>
        <Button disabled aria-describedby="availability">
          {route.action}
        </Button>
      </div>
      <div className="availability-row">
        <Badge>{route.phase}</Badge>
        <p id="availability">Coming in a later phase</p>
      </div>
      <EmptyState title={route.empty}>
        <p>{route.description}</p>
        <p>No workspace data is collected or stored in this preview.</p>
      </EmptyState>
      {route.path === '/app/findings' ? (
        <Table<{ id: string }>
          caption="Findings structure — no results available"
          columns={[
            { key: 'finding', title: 'Finding', render: (row) => row.id },
            { key: 'priority', title: 'Priority', render: () => '' },
            { key: 'evidence', title: 'Evidence', render: () => '' },
          ]}
          rows={[]}
          rowKey={(row) => row.id}
          empty="No checks have run. An empty table is not evidence of a secure domain."
        />
      ) : (
        <Alert title="Permission comes first">
          <p>
            Future checks will require proof that you control the domain. This
            preview cannot initiate external requests to a domain.
          </p>
        </Alert>
      )}
      <div className="workspace-bottom">
        <Link className="text-link" to="/#how-it-works">
          Read the intended workflow <span aria-hidden="true">↗</span>
        </Link>
        <ServiceStatus />
      </div>
    </section>
  );
}

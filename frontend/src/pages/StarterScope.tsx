import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/Primitives';
export function StarterScope() {
  return (
    <section
      id="scope"
      tabIndex={-1}
      className="scope-section page-pad anchor-section"
      aria-labelledby="scope-title"
    >
      <div className="section-index">
        <span>04 / Product scope</span>
        <span>Clear boundaries. Honest expectations.</span>
      </div>
      <h2 id="scope-title" className="display-heading">
        Start focused. <br />
        Build from evidence.
      </h2>
      <div className="scope-grid">
        <div className="starter-scope">
          <div className="scope-heading">
            <h3>Starter</h3>
            <Badge>In development</Badge>
          </div>
          <p>The intended first release.</p>
          <ul>
            <li>Owned-domain onboarding with DNS proof</li>
            <li>Limited DNS, TLS and HTTP observations</li>
            <li>Prioritized findings with supporting evidence</li>
            <li>Practical actions and management reporting</li>
          </ul>
          <div className="planned-access">
            <Link className="button button-primary" to="/register">
              Create account
            </Link>
            <p id="account-note">
              Create an account, then set up your company workspace.
            </p>
          </div>
        </div>
        <div className="future-scope">
          <div className="scope-heading">
            <h3>Beyond Starter</h3>
            <Badge>Future concepts</Badge>
          </div>
          <p>Possible Plus capabilities. Outside this MVP.</p>
          <ul>
            <li>Phishing awareness</li>
            <li>Third-party integrations</li>
            <li>Expert review</li>
          </ul>
          <p className="future-note">
            No subscription or checkout is available. Pricing and these future
            capabilities are not confirmed.
          </p>
        </div>
      </div>
      <div className="scope-questions">
        <details>
          <summary>What can these checks actually tell me?</summary>
          <p>
            They can record specific external configuration observations, such
            as DNS records, certificate validity and the presence of selected
            HTTP headers. They cannot establish that an entire business or
            website is secure.
          </p>
        </details>
        <details>
          <summary>Can I run a check today?</summary>
          <p>
            No. This release contains the public website and interface
            foundation. Domain ownership verification and the bounded checking
            service will be built in later phases.
          </p>
        </details>
        <details>
          <summary>Is this a managed security service?</summary>
          <p>
            No. ShieldMate Starter is a focused risk-to-action product in
            development. It is not a SOC, SIEM, EDR or penetration-testing
            service.
          </p>
        </details>
      </div>
    </section>
  );
}

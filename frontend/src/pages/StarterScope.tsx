import { T } from '../i18n';
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
        <span>
          <T text={'04 / Product scope'} />
        </span>
        <span>
          <T text={'Clear boundaries. Honest expectations.'} />
        </span>
      </div>
      <h2 id="scope-title" className="display-heading">
        <T text={'Start focused. '} />
        <br />
        <T text={'Build from evidence.'} />
      </h2>
      <div className="scope-grid">
        <div className="starter-scope">
          <div className="scope-heading">
            <h3>
              <T text={'Starter'} />
            </h3>
            <Badge>
              <T text={'In development'} />
            </Badge>
          </div>
          <p>
            <T text={'The intended first release.'} />
          </p>
          <ul>
            <li>
              <T text={'Owned-domain onboarding with DNS proof'} />
            </li>
            <li>
              <T text={'Limited DNS, TLS and HTTP observations'} />
            </li>
            <li>
              <T text={'Prioritized findings with supporting evidence'} />
            </li>
            <li>
              <T text={'Practical actions and management reporting'} />
            </li>
          </ul>
          <div className="planned-access">
            <Link className="button button-primary" to="/register">
              <T text={'Create account'} />
            </Link>
            <p id="account-note">
              <T
                text={'Create an account, then set up your company workspace.'}
              />
            </p>
          </div>
        </div>
        <div className="future-scope">
          <div className="scope-heading">
            <h3>
              <T text={'Beyond Starter'} />
            </h3>
            <Badge>
              <T text={'Future concepts'} />
            </Badge>
          </div>
          <p>
            <T text={'Possible Plus capabilities. Outside this MVP.'} />
          </p>
          <ul>
            <li>
              <T text={'Phishing awareness'} />
            </li>
            <li>
              <T text={'Third-party integrations'} />
            </li>
            <li>
              <T text={'Expert review'} />
            </li>
          </ul>
          <p className="future-note">
            <T
              text={
                'No subscription or checkout is available. Pricing and these future capabilities are not confirmed.'
              }
            />
          </p>
        </div>
      </div>
      <div className="scope-questions">
        <details>
          <summary>
            <T text={'What can these checks actually tell me?'} />
          </summary>
          <p>
            <T
              text={
                'They can record specific external configuration observations, such as DNS records, certificate validity and the presence of selected HTTP headers. They cannot establish that an entire business or website is secure.'
              }
            />
          </p>
        </details>
        <details>
          <summary>
            <T text={'Can I run a check today?'} />
          </summary>
          <p>
            <T
              text={
                'Yes. Create a workspace, prove ownership of an authorized domain by DNS TXT, then run its bounded checks. The sample demo needs no real domain.'
              }
            />
          </p>
        </details>
        <details>
          <summary>
            <T text={'Is this a managed security service?'} />
          </summary>
          <p>
            <T
              text={
                'No. ShieldMate Starter is a focused risk-to-action product in development. It is not a SOC, SIEM, EDR or penetration-testing service.'
              }
            />
          </p>
        </details>
      </div>
    </section>
  );
}

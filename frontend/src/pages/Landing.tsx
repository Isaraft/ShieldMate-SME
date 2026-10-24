import { T, tr } from '../i18n';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/Primitives';
import { LandingHero } from './LandingHero';
import { StarterScope } from './StarterScope';
const steps = [
  [
    'Verify an owned domain',
    'Prove control with a DNS TXT record before any checks can run. Permission comes first.',
    'Ownership → DNS TXT',
  ],
  [
    'Observe the essentials',
    'Read bounded DNS configuration, TLS certificate details and HTTP response headers.',
    'DNS / TLS / HTTP',
  ],
  [
    'Understand the priority',
    'Connect each observation to its evidence, business relevance and a suggested next action.',
    'Evidence → context',
  ],
  [
    'Make the next move',
    'Assign actions, track follow-up and prepare a concise management report from stored evidence.',
    'Action → follow-through',
  ],
];
export function Landing() {
  return (
    <>
      <LandingHero />
      <section
        id="product"
        tabIndex={-1}
        className="product-section page-pad anchor-section"
        aria-labelledby="product-title"
      >
        <div className="section-index">
          <span>
            <T text={'01 / The problem'} />
          </span>
          <span>
            <T text={'From information to a decision'} />
          </span>
        </div>
        <div className="product-grid">
          <h2 id="product-title" className="display-heading">
            <T text="landing.product.lead" />{' '}
            <span className="text-red">
              <T text="landing.product.accent" />
            </span>
          </h2>
          <div className="product-detail">
            <p className="lead">
              <T
                text={
                  'A certificate warning. A DNS setting. Another report in your inbox.'
                }
              />
            </p>
            <p>
              <T
                text={
                  'When one person looks after the website, the laptops and everything in between, security work competes with keeping the business running.'
                }
              />
            </p>
            <p>
              <T
                text={
                  'ShieldMate’s aim is simple: give owners a clear next decision and give IT the evidence behind it.'
                }
              />
            </p>
            <div className="perspective">
              <div>
                <span className="eyebrow">
                  <T text={'For the business owner'} />
                </span>
                <h3>
                  <T text={'Understand the impact.'} />
                </h3>
                <p>
                  <T text={'What deserves attention, and why?'} />
                </p>
              </div>
              <div>
                <span className="eyebrow">
                  <T text={'For the IT generalist'} />
                </span>
                <h3>
                  <T text={'Follow the evidence.'} />
                </h3>
                <p>
                  <T text={'What was observed, and what can I change?'} />
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section
        id="how-it-works"
        tabIndex={-1}
        className="workflow-section page-pad anchor-section"
        aria-labelledby="workflow-title"
      >
        <div className="section-index">
          <span>
            <T text={'02 / How it is intended to work'} />
          </span>
          <Badge>
            <T text={'Planned Starter workflow'} />
          </Badge>
        </div>
        <div className="section-intro">
          <h2 id="workflow-title" className="display-heading">
            <T text="landing.workflow.title" />
          </h2>
          <p>
            <T text={'landing.workflow.description'} />
          </p>
        </div>
        <ol className="workflow-list">
          {steps.map(([title, description, detail], index) => (
            <li key={title}>
              <span className="step-number" aria-hidden="true">
                0{index + 1}
              </span>
              <div>
                <h3>{tr(title)}</h3>
                <p>{tr(description)}</p>
              </div>
              <span className="step-detail">{tr(detail)}</span>
            </li>
          ))}
        </ol>
        <p className="scope-note">
          <T
            text={
              'A bounded configuration review. Not a penetration test, continuous monitoring or a guarantee of security.'
            }
          />
        </p>
      </section>
      <section
        id="who-its-for"
        tabIndex={-1}
        className="audience-section page-pad anchor-section"
        aria-labelledby="audience-title"
      >
        <div className="section-index">
          <span>
            <T text={'03 / Who it’s for'} />
          </span>
          <span>
            <T text={'Kazakhstan first'} />
          </span>
        </div>
        <div className="audience-grid">
          <div>
            <h2 id="audience-title" className="display-heading">
              <T text="landing.audience.title" />
            </h2>
            <p>
              <T
                text={
                  'Designed with businesses of roughly 10–100 employees in mind. Digitally dependent. Short on time. Without a dedicated security team.'
                }
              />
            </p>
            <p className="audience-caption">
              <T
                text={
                  'Your size shouldn’t decide whether security makes sense.'
                }
              />
            </p>
          </div>
          <ul className="audience-list">
            <li>
              <span>01</span>
              <div>
                <h3>
                  <T text={'E-commerce'} />
                </h3>
                <p>
                  <T
                    text={
                      'Your storefront is your business. Make sense of the configuration behind it.'
                    }
                  />
                </p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <h3>
                  <T text={'Accounting & outsourcing'} />
                </h3>
                <p>
                  <T
                    text={
                      'Client relationships depend on trust. Give everyday IT decisions a clearer basis.'
                    }
                  />
                </p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <h3>
                  <T text={'Private clinics'} />
                </h3>
                <p>
                  <T
                    text={
                      'A practical starting point for your public website, without implying a clinical systems or compliance assessment.'
                    }
                  />
                </p>
              </div>
            </li>
          </ul>
        </div>
      </section>
      <StarterScope />
      <section
        className="closing-section page-pad"
        aria-labelledby="closing-title"
      >
        <p className="eyebrow">
          <T text={'Take a look at what’s taking shape'} />
        </p>
        <div>
          <h2 id="closing-title" className="display-heading">
            <T text="landing.closing.title" />
          </h2>
          <div className="closing-action">
            <p>
              <T text={'Explore the interface foundation. '} />
              <br />
              <T text={'No account. No scan. No invented results.'} />
            </p>
            <Link className="button button-light" to="/preview">
              <T text={'Explore workspace preview '} />
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

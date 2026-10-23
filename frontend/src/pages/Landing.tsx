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
          <span>01 / The problem</span>
          <span>From information to a decision</span>
        </div>
        <div className="product-grid">
          <h2 id="product-title" className="display-heading">
            More signals. <br />
            <span className="text-red">
              Still no <br />
              clear priority.
            </span>
          </h2>
          <div className="product-detail">
            <p className="lead">
              A certificate warning. A DNS setting. Another report in your
              inbox.
            </p>
            <p>
              When one person looks after the website, the laptops and
              everything in between, security work competes with keeping the
              business running.
            </p>
            <p>
              ShieldMate’s aim is simple: give owners a clear next decision and
              give IT the evidence behind it.
            </p>
            <div className="perspective">
              <div>
                <span className="eyebrow">For the business owner</span>
                <h3>Understand the impact.</h3>
                <p>What deserves attention, and why?</p>
              </div>
              <div>
                <span className="eyebrow">For the IT generalist</span>
                <h3>Follow the evidence.</h3>
                <p>What was observed, and what can I change?</p>
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
          <span>02 / How it is intended to work</span>
          <Badge>Planned Starter workflow</Badge>
        </div>
        <div className="section-intro">
          <h2 id="workflow-title" className="display-heading">
            Less guesswork. <br />A clearer next step.
          </h2>
          <p>
            Four connected steps, built around a domain you control. This
            workflow is in development and is not available yet.
          </p>
        </div>
        <ol className="workflow-list">
          {steps.map(([title, description, detail], index) => (
            <li key={title}>
              <span className="step-number" aria-hidden="true">
                0{index + 1}
              </span>
              <div>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
              <span className="step-detail">{detail}</span>
            </li>
          ))}
        </ol>
        <p className="scope-note">
          A bounded configuration review. Not a penetration test, continuous
          monitoring or a guarantee of security.
        </p>
      </section>
      <section
        id="who-its-for"
        tabIndex={-1}
        className="audience-section page-pad anchor-section"
        aria-labelledby="audience-title"
      >
        <div className="section-index">
          <span>03 / Who it’s for</span>
          <span>Kazakhstan first</span>
        </div>
        <div className="audience-grid">
          <div>
            <h2 id="audience-title" className="display-heading">
              Small team. <br />
              Real stakes.
            </h2>
            <p>
              Designed with businesses of roughly 10–100 employees in mind.
              Digitally dependent. Short on time. Without a dedicated security
              team.
            </p>
            <p className="audience-caption">
              Your size shouldn’t decide whether security makes sense.
            </p>
          </div>
          <ul className="audience-list">
            <li>
              <span>01</span>
              <div>
                <h3>E-commerce</h3>
                <p>
                  Your storefront is your business. Make sense of the
                  configuration behind it.
                </p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <h3>Accounting & outsourcing</h3>
                <p>
                  Client relationships depend on trust. Give everyday IT
                  decisions a clearer basis.
                </p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <h3>Private clinics</h3>
                <p>
                  A practical starting point for your public website, without
                  implying a clinical systems or compliance assessment.
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
        <p className="eyebrow">Take a look at what’s taking shape</p>
        <div>
          <h2 id="closing-title" className="display-heading">
            Clarity <br />
            before action.
          </h2>
          <div className="closing-action">
            <p>
              Explore the interface foundation. <br />
              No account. No scan. No invented results.
            </p>
            <Link className="button button-light" to="/preview">
              Explore workspace preview <span aria-hidden="true">↗</span>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

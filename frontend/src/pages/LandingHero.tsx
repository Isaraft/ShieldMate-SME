import { Link } from 'react-router-dom';
export function LandingHero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-topline">
        <span className="eyebrow">Security clarity for small teams</span>
        <span className="launch-label">
          <span aria-hidden="true">●</span> Pre-launch / In development
        </span>
      </div>
      <div className="hero-main">
        <div className="hero-message">
          <h1 id="hero-title">
            Know what <br />
            to fix <span>first.</span>
          </h1>
          <div className="hero-copy">
            <span className="hero-rule" aria-hidden="true" />
            <p>
              Your business runs online. Security decisions shouldn’t slow it
              down.
            </p>
          </div>
        </div>
        <aside
          className="signal-diagram"
          aria-label="Product concept: turn configuration signals into an informed next action"
        >
          <p className="eyebrow">The idea behind ShieldMate</p>
          <div className="signal-input">
            <span>DNS</span>
            <span>TLS</span>
            <span>HTTP</span>
          </div>
          <div className="signal-path" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div className="signal-context">
            <span className="eyebrow">Add the context</span>
            <p>
              What it means. <br />
              Why it matters.
            </p>
          </div>
          <div className="signal-arrow" aria-hidden="true">
            ↓
          </div>
          <div className="signal-output">
            <span>Your next action</span>
            <span aria-hidden="true">↗</span>
          </div>
          <p className="diagram-note">
            Intended workflow. No checks are running.
          </p>
        </aside>
      </div>
      <div className="hero-bottom">
        <p>
          ShieldMate is being developed to turn limited external configuration
          checks into prioritized actions for Kazakhstan’s small businesses.
        </p>
        <div className="hero-actions">
          <Link className="button button-light" to="/#how-it-works">
            See how it works <span aria-hidden="true">↓</span>
          </Link>
          <Link className="text-link" to="/preview">
            View interface preview <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

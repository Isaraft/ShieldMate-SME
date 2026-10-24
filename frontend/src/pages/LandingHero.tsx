import { T, tr } from '../i18n';
import { Link } from 'react-router-dom';
export function LandingHero() {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero-topline">
        <span className="eyebrow">
          <T text={'Security clarity for small teams'} />
        </span>
        <span className="launch-label">
          <span aria-hidden="true">●</span>
          <T text={' Pre-launch / In development'} />
        </span>
      </div>
      <div className="hero-main">
        <div className="hero-message">
          <h1 id="hero-title">
            <T text={'Know what '} />
            <br />
            <T text={'to fix '} />
            <span>
              <T text={'first.'} />
            </span>
          </h1>
          <div className="hero-copy">
            <span className="hero-rule" aria-hidden="true" />
            <p>
              <T
                text={
                  'Your business runs online. Security decisions shouldn’t slow it down.'
                }
              />
            </p>
          </div>
        </div>
        <aside
          className="signal-diagram"
          aria-label={tr(
            'Product concept: turn configuration signals into an informed next action',
          )}
        >
          <p className="eyebrow">
            <T text={'The idea behind ShieldMate'} />
          </p>
          <div className="signal-input">
            <span>
              <T text={'DNS'} />
            </span>
            <span>
              <T text={'TLS'} />
            </span>
            <span>
              <T text={'HTTP'} />
            </span>
          </div>
          <div className="signal-path" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div className="signal-context">
            <span className="eyebrow">
              <T text={'Add the context'} />
            </span>
            <p>
              <T text={'What it means. '} />
              <br />
              <T text={'Why it matters.'} />
            </p>
          </div>
          <div className="signal-arrow" aria-hidden="true">
            ↓
          </div>
          <div className="signal-output">
            <span>
              <T text={'Your next action'} />
            </span>
            <span aria-hidden="true">↗</span>
          </div>
          <p className="diagram-note">
            <T text={'Intended workflow. No checks are running.'} />
          </p>
        </aside>
      </div>
      <div className="hero-bottom">
        <p>
          <T
            text={
              'ShieldMate is being developed to turn limited external configuration checks into prioritized actions for Kazakhstan’s small businesses.'
            }
          />
        </p>
        <div className="hero-actions">
          <Link className="button button-light" to="/#how-it-works">
            <T text={'See how it works '} />
            <span aria-hidden="true">↓</span>
          </Link>
          <Link className="text-link" to="/preview">
            <T text={'View interface preview '} />
            <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

import { LanguageSwitch, T, tr } from '../i18n';
import { useEffect, useRef, useState } from 'react';
import { api, type Identity } from '../authApi';
import { Link, useLocation } from 'react-router-dom';
const links = [
  ['product', 'Product'],
  ['how-it-works', 'How it works'],
  ['who-its-for', 'Who it’s for'],
  ['scope', 'Scope'],
];

export function Wordmark() {
  return (
    <Link className="wordmark" to="/" aria-label={tr('ShieldMate SME home')}>
      <span className="brand-mark" aria-hidden="true">
        ↗
      </span>
      <T text={'SHIELDMATE'} />{' '}
      <span className="wordmark-suffix">
        <T text={'SME'} />
      </span>
    </Link>
  );
}
export function Header() {
  const { pathname } = useLocation();
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => {
    let active = true;
    if (pathname.startsWith('/demo')) {
      return;
    }
    api<Identity>('/auth/me')
      .then((value) => {
        if (active) setSignedIn(Boolean(value.id));
      })
      .catch(() => {
        if (active) setSignedIn(false);
      });
    return () => {
      active = false;
    };
  }, [pathname]);
  const showSignedIn = !pathname.startsWith('/demo') && signedIn;
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  return (
    <header
      className="site-header"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && open) {
          setOpen(false);
          toggle.current?.focus();
        }
      }}
    >
      <div onClick={() => setOpen(false)}>
        <Wordmark />
      </div>
      <button
        ref={toggle}
        className="menu-toggle button button-secondary"
        aria-expanded={open}
        aria-controls="header-nav"
        onClick={() => setOpen(!open)}
      >
        <T text={open ? 'Close menu' : 'Menu'} />{' '}
        <span aria-hidden="true">
          <T text={open ? '−' : '+'} />
        </span>
      </button>
      <LanguageSwitch />
      <nav
        id="header-nav"
        className={`header-nav ${open ? 'is-open' : ''}`}
        aria-label={tr('Main navigation')}
        onClick={() => setOpen(false)}
      >
        {links.map(([id, label]) => (
          <Link key={id} to={`/#${id}`}>
            {tr(label)}
          </Link>
        ))}
        <Link to={showSignedIn ? '/app' : '/login'}>
          <T text={showSignedIn ? 'My workspace' : 'Sign in'} />
        </Link>
        <Link to="/demo">
          <T text={'Sample Demo'} />
        </Link>
        <Link className="header-preview" to="/preview">
          <T text={'Workspace preview '} />
          <span aria-hidden="true">↗</span>
        </Link>
      </nav>
    </header>
  );
}
export function Footer() {
  return (
    <footer className="site-footer page-pad">
      <div className="footer-top">
        <Wordmark />
        <span className="eyebrow">
          <T text={'Kazakhstan first. Small teams in mind.'} />
        </span>
      </div>
      <div className="footer-bottom">
        <p>
          <T text={'Pre-launch / Starter in development. '} />
          <br />
          <T
            text={
              'Limited external checks cannot guarantee security or detect every vulnerability. Current ownership verification is required before checks.'
            }
          />
        </p>
        <nav aria-label={tr('Footer navigation')}>
          <Link to="/#scope">
            <T text={'Product scope'} />
          </Link>
          <Link to="/preview">
            <T text={'Interface preview'} />
          </Link>
          <Link to="/preview/ui-kit">
            <T text={'UI foundation '} />
          </Link>
        </nav>
        <a className="back-top" href="#main">
          <T text={'Back to top ↑'} />
        </a>
      </div>
    </footer>
  );
}

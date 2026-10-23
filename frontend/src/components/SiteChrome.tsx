import { useRef, useState } from 'react';
import { Link } from 'react-router-dom';
const links = [
  ['product', 'Product'],
  ['how-it-works', 'How it works'],
  ['who-its-for', 'Who it’s for'],
  ['scope', 'Scope'],
];

export function Wordmark() {
  return (
    <Link className="wordmark" to="/" aria-label="ShieldMate SME home">
      <span className="brand-mark" aria-hidden="true">
        ↗
      </span>
      SHIELDMATE<span className="wordmark-suffix">SME</span>
    </Link>
  );
}
export function Header() {
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
        {open ? 'Close menu' : 'Menu'}{' '}
        <span aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      <nav
        id="header-nav"
        className={`header-nav ${open ? 'is-open' : ''}`}
        aria-label="Main navigation"
        onClick={() => setOpen(false)}
      >
        {links.map(([id, label]) => (
          <Link key={id} to={`/#${id}`}>
            {label}
          </Link>
        ))}
        <Link className="header-preview" to="/app">
          Workspace preview <span aria-hidden="true">↗</span>
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
        <span className="eyebrow">Kazakhstan first. Small teams in mind.</span>
      </div>
      <div className="footer-bottom">
        <p>
          Pre-launch / Starter in development. <br />
          Limited external checks cannot guarantee security or detect every
          vulnerability. Ownership verification will be required.
        </p>
        <nav aria-label="Footer navigation">
          <Link to="/#scope">Product scope</Link>
          <Link to="/app">Interface preview</Link>
          <Link to="/app/ui-kit">UI foundation</Link>
        </nav>
        <a className="back-top" href="#main">
          Back to top ↑
        </a>
      </div>
    </footer>
  );
}

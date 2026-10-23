# SHIELDMATE SME — CODEX IMPLEMENTATION PROMPT
## PHASE 01: Brand Identity, Landing Page & Product UI Kit

You are continuing an existing, working repository after Phase 00. Act as a senior frontend engineer, experienced product designer, accessibility-minded UI engineer, and security-conscious maintainer. Implement actual code, not a design proposal.

## 0. Non-negotiable preparation

1. Locate the **existing ShieldMate repository** created in Phase 00. Work in that repository; do not create a second project, replace the scaffold, or copy files into an unrelated working directory.
2. Read `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, and the three images under `docs/design-references/` completely. Also read the current README, package manifests, existing routes/components/styles, and relevant tests.
3. Inspect `git status`, the current commit, project scripts, and existing architecture. Preserve all Phase 00 work, design tokens, backend routes, Docker setup, locks, and tests. Verify the baseline before making changes and report any pre-existing failures separately.
4. This request **authorizes PHASE 01 ONLY**. Do not begin authentication, organization CRUD, domain verification, security scanning, risk scoring, remediation workflows, payments, PDF generation, or deployment.
5. Ask questions only if a missing detail truly blocks implementation. Otherwise make reversible choices, briefly state them, and proceed.

## 1. Product and objective

Product: **ShieldMate SME**, a pre-launch, Kazakhstan-first B2B cybersecurity risk-to-action SaaS concept for digitally dependent small/medium companies (approximately 10–100 employees), especially e-commerce firms without a dedicated security team.

The long-term user journey is: register -> create workspace -> verify an owned domain -> run limited authorized DNS/TLS/HTTP checks -> understand prioritized findings -> take remediation actions -> export management report. **That workflow is not implemented yet.** Phase 01 builds the memorable public-facing experience and a reusable, accessible product UI foundation, with honest representations of future functionality.

The main customer value is **knowing what to fix first**, rather than receiving another enormous scanner report. Explain risk in business language while preserving technical credibility. Do not position ShieldMate as a SIEM, SOC, EDR, pentesting service, or a guarantee of security.

## 2. Art direction: BURGUNDY + RED (NOT PINK)

Review the three user-provided slide images for visual art direction ONLY. They communicate oversized condensed type, assertive editorial hierarchy, bold dark fields, controlled asymmetry, and high contrast. Do **not** recreate any slide layout, slide text, presenter credits, boxes, graphics, or page composition in the website.

Design direction: **Modern editorial / disciplined brutalism meets credible cybersecurity SaaS**. It should feel fearless, distinctive, precise, intentional, and designed by a skilled human—not like an AI-generated template. The marketing site can be expressive; the future security workspace must be restrained and legible.

Brand color system (existing tokens are the starting point; refine only when necessary for accessibility):
- Deep burgundy: `#570711`
- Dark burgundy / wine: `#321015`
- Crimson red: `#98121F`
- Strong accent RED: `#CF2431`
- Warm neutral canvas: `#F7F0EA`
- Light raised surface: `#FFF9F5`
- Neutral border: `#D9C7C3`

**This is a BURGUNDY–RED brand.** Pale ivory/warm-neutral colors exist for contrast only; do not reinterpret this brief as burgundy-pink. No blue, cyan, teal, purple neon, glassmorphism, cyber glow, rainbow gradients, or generic dark dashboard aesthetics. Choose meaningful semantic colors for warning/success/error, and never communicate severity by color alone. Check contrast against WCAG AA, particularly red buttons/text on dark backgrounds.

Typography: choose **at most two** deliberate, properly licensed/open-source font families, such as Anton for expressive display type and IBM Plex Sans for UI/body. Use stable fallbacks. A bold condensed display typeface should define the character, but never sacrifice legibility on small screens or in tables. Use a clear type scale, sensible paragraph measure (~60–75 characters), purposeful whitespace, a coherent 4/8px spacing rhythm, and crisp rather than excessively rounded elements.

Avoid these AI-site cliches:
- Generic centered hero + two bright buttons + three identical feature cards.
- Endless identical cards with shadows, icon-in-circle feature lists, stock photos, invented customer logos, emojis-as-icons, lorem ipsum, fabricated testimonials/metrics.
- Overdone gradients, random animations, giant numbers without sources, buzzwords like “revolutionary”, “seamless”, “next-gen”, “AI-powered” without actual functionality.
- Copying the attached presentation as if it were a website wireframe.

Add restrained, purposeful transitions (~150–300ms); support `prefers-reduced-motion`. Include coherent hover, focus-visible, active, disabled, pending/loading, empty, error, and success states where applicable.

**Before editing UI code**, write a 3–4 sentence art-direction statement and a concise implementation plan. Then follow that plan, unless code inspection reveals a reason to adjust it.

## 3. Required public website (/)

Deliver an original, highly polished, mobile-first landing page using the existing React/TypeScript/Tailwind setup and existing routing convention. This is not a static screenshot: navigation, internal links, responsive menu, and available CTA interactions must work.

Provide these sections in a purposeful editorial composition (use varied scale and rhythm; order can be adapted for design quality):

A. **Global navigation**
- Custom ShieldMate wordmark built from typography or simple scalable vector artwork (do not invent an official certification/seal).
- Functional anchor or route navigation to Product, How it works, Who it is for, and Scope.
- Working mobile navigation: correct expanded state, escape/focus behavior, close after navigation, accessible labels.
- A clearly labeled workspace-preview link. Registration is not implemented, so don't present “Sign up” as a working action.

B. **Hero**
- Distinctive, asymmetric composition with bold, oversized condensed headline and strong burgundy/red blocks.
- Core message in the spirit of **“Know what to fix first.”**
- Tight, credible subcopy: ShieldMate is being developed to translate limited external configuration checks into prioritized actions for small teams.
- A primary **working** CTA: “See how it works” (scroll or jump to a real section).
- A secondary **working** CTA: “View interface preview” (navigate to a clearly labeled preview route).
- Clearly visible pre-launch/MVP status without making the whole layout apologetic.

C. **Customer problem / value**
- Explain fragmented signals, limited security staff/time, and lack of clear priorities in a concrete voice.
- Differentiate executive clarity from technical evidence without claiming either is shipped.
- Use original diagrams, editorial typography, borders, grids, or CSS/SVG accents rather than random stock imagery.

D. **How ShieldMate is intended to work**
- Four truthful steps: Verify an owned domain -> Run limited, safe external checks -> Receive understandable prioritized findings -> Track actions and progress.
- Label as the intended Starter MVP workflow, not already available functionality.
- Make DNS/TLS/HTTP examples precise: limited configuration observations, not comprehensive vulnerability detection.

E. **Who it is for**
- Target Kazakhstan SMEs with ~10–100 employees, especially e-commerce, accounting/outsourcing, and private clinics. Avoid fabricated adoption figures or customer stories.

F. **Starter scope vs future capabilities**
- Clearly describe intended Starter capabilities: owned-domain onboarding, limited DNS/TLS/HTTP observations, prioritized actions, simple management reporting.
- Distinguish future Plus concepts (phishing awareness, integrations, expert review) as **planned/not part of this MVP**.
- Do not imply payment checkout, subscription activation, or verified pricing. The ₸50,000/month figure in Assignment 4 is a hypothesis, not an offered or validated plan; omit it from public pricing unless conspicuously labeled as an unvalidated proposal.

G. **Honest closing CTA and footer**
- Meaningful CTA to the workspace preview and/or how-it-works section.
- Product identity, navigation, pre-launch label, and concise safety disclaimer.
- Do not invent company registration details, public contact addresses, legal certifications, privacy claims, or real customer traction.

Use original, concise, natural English website copy. “Cybersecurity-as-a-subscription” may appear as positioning, but avoid claiming a subscription/billing system is live. No placeholder links (`href="#"`) without a corresponding target, and no buttons that appear functional but do nothing.

## 4. Product preview / app shell (NO fictional live data)

Build/refine the existing Phase 00 application layout and planned routes while preserving existing route names where practical. It should clearly share the new brand system but optimize for dense, trustworthy product information rather than giant marketing headings.

- Responsive desktop sidebar and compact mobile navigation/header.
- Navigation destinations for Overview, Assets, Findings, Action Plan, Reports and any already defined route.
- All not-yet-implemented destinations must show intentional, accessible **empty / coming-in-later-phase** views instead of pretending to work. Include an explicit “Interface preview — live features are under development” label.
- Do **not** render invented security scores, scan timestamps, vulnerability counts, risk trends, organization names presented as real customers, progress bars suggesting real measurements, or fake backend-connected activity.
- Use meaningful skeleton/loading, empty, permission/error, disabled and informational UI patterns where appropriate; demo data belongs to Phase 07, not Phase 01.
- Preview routes must not accidentally hit future scan/auth endpoints or expose mock API results as genuine.
- Preserve the FastAPI health endpoint and existing backend/database foundation; no backend business-feature work in this phase.
- Build a proper 404 for unknown routes, with a functional recovery link.

## 5. Reusable UI foundation

Create a small, cohesive, typed design-system component layer **only where it will actually be reused**. Prefer existing components when correct; avoid installing a heavy UI framework or building a premature universal component library.

Include appropriate variants and meaningful tests for:
- Button and link styles (primary, secondary, quiet, disabled, loading if needed).
- Input, label, help and validation/error feedback.
- Status/severity badge combining text with visual treatment (never color alone).
- Alert/notification or inline feedback.
- Empty state and simple loading/skeleton state.
- Responsive table/list patterns suitable for future findings (no fabricated records).
- Accessible dialog/modal pattern only if needed by a real Phase 01 interaction; otherwise leave it for the phase that needs it, rather than implementing unused complexity.

Keep public and workspace styles coordinated using centralized semantic tokens (not scattered hex literals). Document final tokens, fonts, typography hierarchy, spacing, responsive behavior, component variants, and practical do/don't examples in `docs/design-system.md`.

## 6. Engineering, quality, security and SEO

- Keep existing architecture, file organization, package manager, formatting style, locked dependencies and Docker workflow. Prefer small reusable components and semantic markup over huge single-file JSX.
- Use proper links for navigation, real button semantics for actions, correct heading hierarchy, keyboard focus visibility, form associations, ARIA only where necessary, `alt` for meaningful images, and accessible mobile navigation. Avoid `dangerouslySetInnerHTML` and unsanitized user content.
- Responsive and visually intentional at **360, 768, 1280 and 1920 CSS px**. No unintended horizontal scrolling or clipped typography. Verify long text wrapping and small-screen navigation.
- Honor reduced motion and respect system color/contrast preferences where practical; do not let dark/light variants drift from brand identity.
- Maintain appropriate frontend security practices. Do not introduce hardcoded secrets, unsafe HTML injections, unnecessary external runtime scripts, localStorage auth assumptions, or permissive API changes.
- Metadata: meaningful title and description, favicon or small original vector mark, Open Graph basics, logical semantic headings, sitemap/robots where appropriate to this Vite SPA. Do not fabricate a production domain for canonical links. Explain SPA-specific SEO limitations rather than pretending SSR exists. Don't publish an imaginary social share image.
- Minimize third-party dependencies. If fonts/assets are added, use legitimate licenses and a deliberate loading strategy. Do not embed the slide screenshots directly into the UI.
- No external deployment, purchases, domain registration, emails, user recruitment, git push or automated scans.

## 7. Verification (required; execute rather than merely describe)

1. First reproduce the Phase 00 baseline tests and build. Report actual output and any pre-existing issue.
2. After implementation, run existing frontend tests, lint, format checks, TypeScript typecheck, production build, and backend regression tests. If Docker startup is available, confirm it still works and `/api/v1/health` remains healthy.
3. Add or update tests for: landing page rendering/semantics; working in-page navigation and CTA destinations; mobile navigation behavior; clear preview labels and no fake statistics; 404 recovery; component disabled/focus/error states; and any new logic.
4. If browser automation or browser preview is available, **actually inspect** 360/768/1280/1920 screenshots, keyboard navigation, mobile menu and layout overflow. Record what you inspected and fix observed defects. If unavailable, say NOT TESTED and provide concise manual verification instructions instead of fabricating results.
5. Validate WCAG AA text/button contrast and reduced-motion behavior using available checks or documented manual calculations.
6. Run dependency audit if toolchain supports it, report only what was actually tested, and avoid unrelated package upgrades.
7. Check the git diff for accidental changes and confirm the full user journey has not been implied as functional ahead of its phase.

## 8. Definition of done — PHASE 01 ONLY

Phase 01 is complete when:
- [ ] Landing page is an original high-quality, bold **burgundy + RED** editorial design, not pink or blue.
- [ ] All supplied design reference images informed the art direction, but no slide layout was copied.
- [ ] Responsive layout works at 360, 768, 1280 and 1920 CSS px.
- [ ] Navigation and currently enabled CTAs have real destinations/behavior.
- [ ] Preview app shell is coherent, accessible, and unmistakably marked as a preview, with NO invented live security metrics.
- [ ] Honest Starter and future Plus scope is clearly distinguished.
- [ ] A concise reusable UI layer and `docs/design-system.md` exist.
- [ ] 404, empty and disabled states are polished and functional.
- [ ] Current tests/lint/typecheck/build pass, no backend regression, and actual QA evidence is reported.
- [ ] Auth, domain verification, scans, findings, tasks, reports, and deployment **have not started**.

## 9. Completion report (use this exact structure)

**Phase:** 01 — Brand Identity, Landing Page & Product UI Kit

**Art direction:** 3–4 sentences explaining the actual design choices.

**Files changed:** concise file-path list grouped by purpose.

**Implemented:** exact working behavior.

**Explicitly not implemented:** functions reserved for later phases, including nonworking CTAs intentionally disabled/marked.

**Commands executed & actual results:** tests, lint, typecheck, build, Docker/health, audit; counts and failures, not generic "passed" without evidence.

**Visual/accessibility QA:** viewport-by-viewport result, keyboard/focus, reduced motion and color contrast; distinguish verified from not tested.

**Security and regressions:** what was checked and any residual risk.

**Phase 01 acceptance checklist:** PASS / FAIL / NOT TESTED against each item above.

**Run instructions:** exact local commands and URLs.

**Open issues / manual actions:** precise and honest.

**Git status and commit:** state what changed; do not push. Commit only if consistent with existing repo workflow, and report hash if committed.

**Next phase:** PHASE 02 NOT STARTED — await explicit user approval.

Implement the phase now. Do not stop at a plan or output pseudocode.

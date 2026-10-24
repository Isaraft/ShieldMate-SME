# SHIELDMATE SME — PHASE 07.1
## Production-Quality UI Polish, Professional PDF Report Redesign, and Native EN/RU/KK Localization

**Execution instruction:** This is an IMPLEMENTATION task, not a proposal or design-only exercise. Implement, test, visually review and commit the completed work. Do not start Phase 08, push to a remote, deploy publicly, or modify production data.

**Project context**
- Product: ShieldMate SME — Kazakhstan-first, small-business-focused security risk-to-action platform.
- Completed foundation: Phases 00–07, most recent local `main` commit: `8f295fa` (verify actual HEAD and repository state before changing anything).
- Current capabilities: auth/organization isolation, authorized domain enrollment and DNS TXT proof, bounded DNS/TLS/HTTP checks, evidence-backed findings and Top 3 priorities, dashboard/tasks, PDF reports, public synthetic demo, EN/RU language switching.
- Existing brand: **BOLD BURGUNDY + RED**, editorial/brutalist typography for public marketing, more restrained ergonomic UI inside workspace. Warm light neutrals are contrast colors; **this is NOT a pink-themed product**. No stock-image templates or generic blue/neon cybersecurity styling.
- The user identified real visual and language defects. The attached screenshots under `docs/qa-references/` are visual BUG EVIDENCE, not design mocks. Examine both before coding.

### Required start sequence
1. Inspect the repository, current `git status`, `AGENTS.md`, `SHIELDMATE_MVP_SPEC.md`, `PHASES.md`, the design system, Phases 06/07 implementation and tests, i18n dictionaries and components, report renderer, and `docs/phase-07-results.md` if present.
2. Open and inspect both bug screenshots:
   - `docs/qa-references/hero-overlap.png` — hero headline / red FIRST accent composition.
   - `docs/qa-references/russian-steps-alignment.png` — Russian numbered steps; numbers are visually too high instead of vertically centered within their rows.
3. Run and record the existing test/build baseline before modifications. Preserve all already-working security and product behavior. Do not reset or silently discard user changes. If the current working tree is not clean, inspect and preserve changes.
4. In 3–5 sentences, state the refined design/typographic direction and a short diagnostic of the observed defects. Then implement all requirements below, not only a plan.

---

## A. Fix the homepage headline and responsive composition

**Observed defect:** In the supplied English screenshot, the oversized 'KNOW WHAT / TO FIX FIRST.' composition is visually broken: the red `FIRST.` treatment intrudes into the neighboring headline content. It gives the impression that part of the headline, particularly `WHAT`, is masked/overlapped. Also inspect the right-side panel/header for clipped content at the screenshot width; determine whether it is genuine page overflow or a cropped screenshot before claiming a defect.

**Implement**
- Rebuild the headline using a deliberate, stable typographic layout; eliminate accidental overlap caused by absolute positioning, negative margins, mismatched line heights, excessive transforms or fixed widths.
- Preserve the dramatic Anton/condensed editorial feel and the intentional highlighted red `FIRST.` accent. Intentional graphic overlap is allowed **only if legibility is unequivocally preserved**, including all target locales and all screen sizes.
- Prefer a responsive CSS grid/flex/intrinsic composition using actual text measurements / content-driven sizing. `clamp()` may be useful, but is not a substitute for testing.
- No hidden or clipped letters, overlap between siblings, cropped nav labels, off-screen callouts, unexpected horizontal scroll, text covered by decorative pseudo-elements, or hero controls outside the viewport.
- Ensure the hero works with English, idiomatic Russian and idiomatic Kazakh copy. Do NOT require translations to match English word counts or insert unnatural sentences to force a visual layout.
- For different locales, allow intentional responsive line breaks and separately composed highlighted phrases where linguistically necessary. Do not assemble sentences by concatenating independent fragments whose grammar breaks across locales.
- Check mobile navigation, desktop header, CTA hierarchy, sidebar/callouts, and page scroll widths. Apply component-level fixes, not globally shrinking all font sizes.
- Maintain reduced-motion support, good keyboard focus, and no content movement on locale switch beyond necessary reflow.

## B. Fix numbered-step vertical alignment and typography

**Observed defect:** In the provided Russian screenshot, numbers `01`, `02`, `03`, `04` sit too close to their row's top divider; corresponding titles/descriptions vary in height and row centering is visually inconsistent.

**Implement**
- Center the number **vertically relative to its complete step row**, not merely relative to the title or first line; respect rows with longer translations and two- or three-line descriptions.
- Use semantically suitable list markup or equivalent accessible structure; grid with `align-items: center` or a full-row flex alignment is preferred over per-item hardcoded top offsets.
- Maintain visible baseline rhythm, consistent gutters, dividers, row padding, numeral size and column width.
- Make sure number/title/body do not collide on 360px screens. Responsive stacking is fine if designed intentionally.
- Repeat the same inspection for any other numbered sections and connected UI lists throughout landing, demo and workspace.

## C. Full UI design and multilingual layout audit

Audit every significant user-facing route and interaction, **not just the screenshots**. Include as applicable:
- Landing sections, header, mobile menu, hero, navigation, FAQ and footer
- Auth forms and validation errors, organization onboarding/settings
- `/app` dashboard, assets and ownership verification, scan controls/results/history
- Findings details, risk priorities, remediation task list/details, reports/history/downloads
- `/demo`, empty/loading/error/disabled states, 404, responsive tables, language switcher

For EN, RU, KK:
- Inspect headings, badges, buttons, tables, modals, notification text, long URLs/domains, form labels, helper texts, captions, date strings, number formatting and error messages.
- Correct clipped/wrapped labels, displaced buttons, uneven spacing, overflowing dropdowns, fixed-height elements that cannot accommodate translation, and misaligned cards/columns.
- Prefer intrinsic height, min/max content rules, `min-width: 0`, deliberate wrapping, and responsive grid decisions. Never just set `overflow: hidden` to conceal broken text.
- Ensure font families support Latin and Cyrillic including Kazakh-specific glyphs; avoid unexpected fallback font differences causing width or line-height jumps. Use up to two intentional families and licensed assets only.
- Preserve consistent brand tokens rather than scattered overrides or patch-on-patch media queries.
- Recheck WCAG AA contrast, keyboard and focus, zoom at 200%, reduced motion, visible hover/pressed/disabled states, mobile touch targets, and optional high-contrast mode where practical.

## D. Real, editorial-quality English/Russian/Kazakh localization

### D1. Add a proper third locale: **Kazakh — Қазақша (`kk`)**
- Use standard locale identifier **`kk`** (do not confuse with country code `kz`); keep `en` and `ru` working.
- Native names in selector: `English`, `Русский`, `Қазақша`. Ensure selector fits mobile and is keyboard/screen-reader accessible. Persist user choice without auth disruption or cross-user leakage; switching should preserve form state and current route when feasible.
- Expand the established i18n architecture: meaningful keys with clear context, no repeated hardcoded literals, no fragmented string concatenation or brittle positional placeholders.
- Translate every actual in-scope string, including landing copy, consent, scan statuses, security terminology, validation errors, action labels, account screens, demo disclaimers, reports and footer/legal copy. Handle backend-provided statuses with locale-based presentation mapping; do NOT translate protocol names/domain values/technical evidence that must remain exact.
- Locale-aware date/time/number formatting, including Kazakhstan context where appropriate, while preserving canonical backend values. Never transform raw security evidence (DNS, domain names, hashes, URLs, timestamps) into fake or ambiguous localized values.
- Update metadata (`html[lang]`, page title/description where the app supports it), language preference, PDF API locale validation, test fixtures and documentation. Backwards compatibility: existing EN/RU users and saved preferences must continue working; specify fallback for unknown locale values.

### D2. Rewrite Russian as natural product language

Do a complete human-style editorial pass rather than literal word substitution. Existing RU text has instances of awkward, robotic or overly literal translation. Improve fluency, agreement, case, punctuation, commands and cybersecurity terminology. Avoid nonsense literal translations of terms such as `findings`, `posture`, `scan`, `coverage`, `risk-to-action`, `owner`, `remediation` or `verified`.

Use concise, precise, professional Russian appropriate for a Kazakhstan business owner and an IT generalist. Where a cybersecurity term is genuinely industry-standard in English (DNS, SPF, DMARC, TLS, HTTP, CVE, API), retain that term and provide a natural explanation if needed.

### D3. Write idiomatic Kazakh, not Russian grammar with substituted words

Use correct Kazakh syntax, natural terminology and punctuation; favor clear language understandable to Kazakhstan SME decision-makers. Correctly support characters: Ә ә, Ғ ғ, Қ қ, Ң ң, Ө ө, Ұ ұ, Ү ү, Һ һ, І і. Avoid mixing Russian word forms or leaving English marketing placeholders except genuine technical abbreviations and product names.

Examples of **terminology direction** (translate consistently and use context, not copy these blindly):
- Domain ownership verification: `Доменге иелік етуді растау`
- Security report: `Қауіпсіздік туралы есеп`
- Recommended actions: `Ұсынылатын әрекеттер`
- Risk level: `Тәуекел деңгейі`
- Scan history: `Тексеру тарихы`
- Remediation tasks: `Осалдықтарды жою тапсырмалары` (adapt when the issue is a misconfiguration rather than an actual vulnerability)
- Incomplete assessment: `Тексеру толық аяқталмады`

Provide a small `docs/localization-style-guide.md` explaining language tone and 15–25 canonical terms across EN/RU/KK, distinguishing `finding` from proven `vulnerability` and `task completed` from `risk resolved`. Run automated missing-key and interpolation-key parity checks for all three locales. If native review is unavailable, **do not claim native-language certification**; mark it for manual review, but still produce the best complete translation you can.

## E. Rebuild the PDF report into a professional, readable deliverable

The current Phase 07 PDF reportedly looks crooked/unprofessional. **Inspect real generated EN/RU PDFs and their rendered pages before redesigning.** Do not guess based solely on source. Examine `docs/evidence/phase-07/` or generate new local fixture PDFs. If you cannot read an original output, state that plainly and proceed from the renderer + a new reproducible output.

### E1. Information architecture

Keep existing *evidence-backed* semantics and nonfabrication safeguards, but redesign the presentation. A suggested report outline:
1. **Report identity / first page:** ShieldMate SME wordmark; `External Security Configuration Assessment` (localized naturally); organization; authorized assessment scope; generation date/time/timezone; report ID; clear `Limited external assessment` label, not an implied penetration-test certification.
2. **Executive summary:** short plain-language narrative based on actual evidence; coverage status (complete/partial/inconclusive), inspected asset count, findings by severity if supported, Top 3 priorities if they exist. Empty means empty, not invented.
3. **Scope & methodology:** authorized domain list, time windows, DNS/TLS/HTTP check types, scope limitations, excluded controls, no pentest claim, uncertainty/failed checks.
4. **Prioritized findings:** compact overview grouped/ordered by authoritative Phase 05 ranking. Severity, asset, status, reason and link/reference identifiers. Do not invent CVSS/CVE.
5. **Finding detail:** readable title, impact, actual evidence, affected asset, remediation, verification guidance, last observation, confidence/uncertainty. Separate machine evidence from business explanation.
6. **Action plan:** existing task records/status/owner labels where available; human completion must NOT equal technical risk resolution.
7. **Methodology / definitions and footnotes:** explain observation gaps and terms. Include DEMO / LOCAL QA markings when applicable.

Do not force blank sections; build graceful empty/inconclusive states. The PDF should be useful for managers and credible to a security practitioner, without claiming more than the scanner measures.

### E2. Print-oriented design rules

- A4 portrait, intentional margins and a consistent typography grid; consider shorter-page sections where appropriate. Avoid giant empty gaps, overstuffed pages, randomly broken paragraphs, strange indenting and unstable spacing.
- Brand expression through **deep burgundy, clear red accents and restrained warm neutral backgrounds**. Body text should be dark, highly legible and comfortably sized; avoid pink body text, giant decorative banners on every page or red-on-burgundy low-contrast labels.
- Strong hierarchy: title > section > finding title > body > labels; concise tables, consistent borders and spacing; clean header/footer with page number, organization (when safe), report ID and confidentiality/context marking.
- Header/footer areas may not collide with content. Table headers repeat when a table spans pages. Do not split a finding heading from its first detail/evidence block; minimize widows/orphans and one-line continuation pages.
- Wrap long hostnames, URLs, SHA-style values, evidence snippets, domain lists and localized strings safely. Never silently truncate critical evidence or overflow boxes. For unusually long technical values, use controlled wrapping or dedicated evidence formatting.
- Distinguish severity with **text labels + color**, not color alone. Color must be meaningful and printable in grayscale.
- Keep icons/vector shapes deliberate and minimal. No template-like KPI card explosion, no meaningless charts. Use metrics only if they are grounded in stored evidence and correctly labeled with coverage constraints.
- Keep consistent line heights, padding, baseline rhythm and pagination on multi-page reports, including PDFs with dozens of findings.
- Embedded, redistributable font(s) must cover English, Russian and all Kazakh glyphs. Check embedding/rendering with license compliance; **do not supply/share font files outside the repository through this response**. Avoid accidental fallback or missing-glyph boxes.
- Validate semantic visual hierarchy and PDF text extractability. PDF/UA certification is not required; do not claim it unless independently established.
- Continue to mark every synthetic DEMO page conspicuously as `DEMO — SYNTHETIC DATA` (localized where appropriate while retaining an unambiguous DEMO marker). LOCAL QA fixture exports must also be visibly labeled as test evidence; never disguise them as real company results.

### E3. Report data/security invariants

- Preserve the existing organization-scoped, authorized, immutable snapshot / PDF persistence and downloads; do not weaken access, CSRF, Origin or IDOR protection.
- Reports must use persisted authoritative findings, priority ordering, timestamps, task statuses and coverage; re-use existing services instead of creating a parallel risk calculation.
- Preserve current report history and bytes. **Never modify old immutable report records** when improving the template. New template version applies only to newly generated exports, with documented compatibility.
- No network access from PDF renderer, arbitrary URL fetching, template injection, unsanitized markup, executable content, unsafe filesystem paths, or tenant data exposure.
- Handle font/rendering failures transactionally and with bounded resources/time/memory/page counts where reasonable. Errors must not leave corrupt downloadable reports.
- If local database changes are truly required, justify and apply additive Alembic migrations; otherwise do not add migrations for aesthetic work.

## F. Tests, browser inspection and rigorous visual QA

Do not equate green unit tests with visual correctness. Add **reproducible screenshot-based inspections and overflow assertions**.

### F1. Browser matrix

- Viewports: **360, 390, 768, 1024, 1280, 1440 and 1920px**, with viewport zoom/text scaling edge cases where available.
- Locales: **en, ru, kk** on all major user-facing routes and key modals/forms.
- Must directly reproduce and fix the two attached screenshot defects. Capture **before/after** screenshots at matching or close dimensions: approximately **1247×827** for hero and **1082×679** for numbered Russian steps, plus mobile screenshots.
- Test long translations, long organization names, domain labels, critical/high-priority finding names, unverified-domain states, empty organization data, and a fully populated local-only QA fixture.
- Explicit assertions: no unintended horizontal scroll; no overlaps/clipping of text; numbered steps vertically centered; menu/CTA reachable; no runtime console errors; language switch stable; visible translated focus/errors.
- Accessibility: keyboard-only navigation, focus restoration, labels, aria/live error announcements, reduced-motion, contrast, and axe. Distinguish automated checks from manual screen reader testing.
- If the browser tool supports screenshots and image inspection, **actually inspect the rendered PNGs**. If it does not, record that limitation and do not claim full visual verification.

### F2. PDF quality gate

Generate and visually inspect a **minimum of six new PDFs**: EN/RU/KK for both (a) short/empty/partial coverage and (b) complex multi-page fixture with long strings. Also export DEMO PDFs in all three languages and inspect DEMO label on **every page**; these may be part of the six if coverage is adequate, otherwise add more.

Verify on the output PDFs:
- No page-area overflow, no clipped glyphs or missing Kazakh Cyrillic characters.
- No overlapping headings/body/table rows/headers/footers.
- Predictable page breaks, repeated table headings, sensible finding grouping, and readable density.
- Metadata/locale/date/scope are honest, and the PDF text can be extracted.
- Owner organization and history access remains protected; demo isolation still passes.
- Where practical, use programmatic PDF text and bounding-box inspection **plus human visual review of rendered PDF pages**. Unit tests alone are insufficient.

### F3. Regression checks

Run and document actual results (do not invent them):
- `npm test --prefix frontend`, ESLint, TypeScript, formatter, production build and `npm run i18n:check --prefix frontend` (adapt exact commands if repository differs).
- Backend `.venv/bin/pytest -q`, Ruff, mypy, migrations/schema drift, PDF renderer tests.
- `npm audit`, `pip-audit`, Docker compose build/start/health, restart persistence and Git diff checks.
- Re-test authentication/session/CSRF, domain proof, scan safety/SSRF defenses, tenant isolation, findings, tasks, report history, and demo isolation.

## G. Deliverables and completion criteria

1. Improved responsive homepage without the hero `WHAT/FIRST` overlap, same strong visual identity.
2. Correct vertically centered step numerals for variable-height text.
3. Comprehensive layout/spacing/wrapping fixes on all important routes in EN/RU/KK.
4. Idiomatic corrected Russian; complete appropriate Kazakh locale (including all visible statuses/messages).
5. PDF export UI supports EN, RU and KK naturally. PDFs have redesigned, professional typography, usable multi-page pagination and properly displayed Kazakh glyphs.
6. Existing auth, scan, risk prioritization, tasks, PDF snapshots and demo security invariants preserved.
7. Automatic localization parity and layout regression checks plus stored screenshot evidence, including before/after of reported defects.
8. Rendered PDF QA evidence and an honest list of what was visually inspected (including exact page counts).
9. Updated docs: `docs/localization-style-guide.md`, design/report decisions and `docs/phase-07-1-results.md`, including any manual steps and unsupported browsers.
10. Run checks, fix actual failures and leave a clean working tree. Make **one focused local commit** with a meaningful message; no push or deployment.

### Required final report format
- Current branch/starting commit/final commit/status.
- Root causes identified for hero overlap, step alignment and poor PDF layout, with what changed.
- Complete list of affected routes and principal code locations.
- EN/RU/KK localization coverage and sample copy changes; native review caveat if applicable.
- PDF sample outputs with paths, number of pages and actual rendering QA performed.
- Exact tests and checks with numerical outcomes, and known NOT TESTED items.
- Before/after screenshots and screenshot coverage by locale/device.
- Security/regression findings and open blockers.
- Phase 07.1 acceptance gates PASS/FAIL/NOT TESTED; do not mark unverified items PASS.
- Local startup instructions.

**STOP at Phase 07.1. Do NOT begin Phase 08. Do not push, deploy or assert production readiness.**
